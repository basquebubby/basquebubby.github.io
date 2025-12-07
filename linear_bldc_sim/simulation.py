"""
Main Linear BLDC Simulation Engine

Integrates all models:
- Electromagnetic
- Mechanical
- Thermal
- Control
- Sensors
"""

import numpy as np
from typing import Dict, List, Tuple
import time as pytime

from models.electromagnetic import ElectromagneticModel
from models.mechanical import MechanicalModel
from models.thermal import ThermalModel
from models.sensor import PositionSensor
from control.controller import ControlSystem
from specs import SPECS, MATERIALS, CONSTANTS, CONTROL_PARAMS, THERMAL_LIMITS, MECHANICAL_PARAMS


class LinearBLDCSimulation:
    """Main simulation class for the linear BLDC actuator"""

    def __init__(self, specs: dict = None):
        """Initialize simulation

        Args:
            specs: Motor specifications (uses default if None)
        """
        if specs is None:
            specs = SPECS

        self.specs = specs

        # Initialize all subsystems
        self.electromagnetic = ElectromagneticModel(specs, MATERIALS, CONSTANTS)
        self.mechanical = MechanicalModel(specs, MECHANICAL_PARAMS, CONSTANTS)
        self.thermal = ThermalModel(specs, MATERIALS, CONSTANTS, THERMAL_LIMITS)
        self.sensor = PositionSensor(resolution=1e-6, noise_std=0.1e-6)
        self.controller = ControlSystem(specs, CONTROL_PARAMS)

        # Simulation state
        self.time = 0.0
        self.running = False

        # Data logging
        self.history = {
            'time': [],
            'position': [],
            'velocity': [],
            'acceleration': [],
            'force_em': [],
            'force_total': [],
            'current_A': [],
            'current_B': [],
            'current_C': [],
            'current_total': [],
            'voltage_A': [],
            'voltage_B': [],
            'voltage_C': [],
            'temp_coils': [],
            'temp_magnets': [],
            'temp_housing': [],
            'power_loss': [],
            'position_setpoint': [],
            'position_error': [],
        }

        # Multi-rate time steps
        self.dt_electrical = 10e-6  # 10 μs (for electrical dynamics)
        self.dt_mechanical = 100e-6  # 100 μs (for mechanical dynamics)
        self.dt_thermal = 100e-3  # 100 ms (for thermal dynamics)
        self.dt_control = 1e-3  # 1 ms (control loop)
        self.dt_logging = 1e-3  # 1 ms (data logging)

        # Subcycle counters
        self.electrical_steps = 0
        self.mechanical_steps = 0
        self.thermal_steps = 0
        self.control_steps = 0
        self.logging_steps = 0

    def step(self, dt: float):
        """Execute single simulation timestep

        Args:
            dt: Master time step in seconds (typically 10 μs for electrical)
        """
        # 1. Get current state
        position = self.mechanical.position
        velocity = self.mechanical.velocity

        # 2. Calculate back-EMF
        back_emf = self.electromagnetic.calc_back_emf(velocity, position)

        # 3. Control update (at control rate)
        if self.time >= self.control_steps * self.dt_control:
            voltage_commands = self.controller.update(
                position, velocity,
                self.electromagnetic.phase_currents,
                self.electromagnetic,
                self.dt_control
            )
            self.control_steps += 1
        else:
            # Hold previous voltage command
            voltage_commands = getattr(self, '_last_voltage_commands',
                                      np.zeros(3))
        self._last_voltage_commands = voltage_commands

        # 4. Electrical dynamics (update phase currents)
        self.electromagnetic.update_currents(voltage_commands, back_emf, dt)

        # 5. Calculate electromagnetic force
        force_em = self.electromagnetic.calc_electromagnetic_force(
            position, self.electromagnetic.phase_currents
        )

        # Add cogging force
        force_cogging = self.electromagnetic.get_cogging_force(position)
        force_total = force_em + force_cogging

        # 6. Mechanical update (at mechanical rate)
        if self.time >= self.mechanical_steps * self.dt_mechanical:
            self.mechanical.update(force_total, self.dt_mechanical)
            self.mechanical_steps += 1

        # 7. Thermal update (at thermal rate)
        if self.time >= self.thermal_steps * self.dt_thermal:
            copper_loss = self.electromagnetic.get_copper_loss()
            core_loss = self.electromagnetic.get_core_loss(velocity)
            magnet_loss = self.electromagnetic.get_magnet_eddy_loss(velocity)

            self.thermal.update_heat_generation(copper_loss, core_loss, magnet_loss)
            self.thermal.update(self.dt_thermal)
            self.thermal_steps += 1

        # 8. Data logging (at logging rate)
        if self.time >= self.logging_steps * self.dt_logging:
            self._log_data(force_em, force_total)
            self.logging_steps += 1

        # Update simulation time
        self.time += dt

    def _log_data(self, force_em: float, force_total: float):
        """Log simulation data for plotting

        Args:
            force_em: Electromagnetic force
            force_total: Total force including cogging
        """
        self.history['time'].append(self.time)
        self.history['position'].append(self.mechanical.position * 1000)  # Convert to mm
        self.history['velocity'].append(self.mechanical.velocity)
        self.history['acceleration'].append(self.mechanical.acceleration)
        self.history['force_em'].append(force_em)
        self.history['force_total'].append(force_total)
        self.history['current_A'].append(self.electromagnetic.phase_currents[0])
        self.history['current_B'].append(self.electromagnetic.phase_currents[1])
        self.history['current_C'].append(self.electromagnetic.phase_currents[2])
        self.history['current_total'].append(np.linalg.norm(self.electromagnetic.phase_currents))
        self.history['voltage_A'].append(self._last_voltage_commands[0]
                                        if hasattr(self, '_last_voltage_commands') else 0)
        self.history['voltage_B'].append(self._last_voltage_commands[1]
                                        if hasattr(self, '_last_voltage_commands') else 0)
        self.history['voltage_C'].append(self._last_voltage_commands[2]
                                        if hasattr(self, '_last_voltage_commands') else 0)
        self.history['temp_coils'].append(self.thermal.temperatures['coils'])
        self.history['temp_magnets'].append(self.thermal.temperatures['magnets'])
        self.history['temp_housing'].append(self.thermal.temperatures['housing'])
        self.history['power_loss'].append(self.thermal.get_total_heat_generation())

        # Control system data
        if self.controller.mode == 'position':
            self.history['position_setpoint'].append(self.controller.position_setpoint * 1000)  # mm
            self.history['position_error'].append(
                (self.controller.position_setpoint - self.mechanical.position) * 1000  # mm
            )
        else:
            self.history['position_setpoint'].append(self.mechanical.position * 1000)
            self.history['position_error'].append(0)

    def run(self, duration: float, dt: float = None, realtime: bool = False) -> Dict:
        """Run simulation for specified duration

        Args:
            duration: Simulation duration in seconds
            dt: Time step (uses electrical dt if None)
            realtime: If True, run at real-time speed (for visualization)

        Returns:
            Dictionary of recorded data
        """
        if dt is None:
            dt = self.dt_electrical

        num_steps = int(duration / dt)
        self.running = True

        print(f"Running simulation for {duration} s ({num_steps} steps, dt={dt * 1e6:.1f} μs)...")

        start_time = pytime.time()
        last_print_time = start_time

        for i in range(num_steps):
            if not self.running:
                break

            self.step(dt)

            # Print progress
            if pytime.time() - last_print_time > 1.0:
                progress = (i + 1) / num_steps * 100
                print(f"Progress: {progress:.1f}% (t={self.time:.3f} s)")
                last_print_time = pytime.time()

            # Real-time mode
            if realtime:
                elapsed = pytime.time() - start_time
                if elapsed < self.time:
                    pytime.sleep(self.time - elapsed)

        elapsed = pytime.time() - start_time
        speed_factor = duration / elapsed if elapsed > 0 else 0
        print(f"Simulation complete! Ran {speed_factor:.1f}x real-time ({elapsed:.2f} s elapsed)")

        return self.get_history()

    def get_history(self) -> Dict:
        """Get recorded simulation data

        Returns:
            Dictionary of numpy arrays
        """
        return {key: np.array(values) for key, values in self.history.items()}

    def reset(self):
        """Reset simulation to initial state"""
        self.time = 0.0
        self.mechanical.reset()
        self.thermal.reset()
        self.sensor.reset()
        self.controller.reset()
        self.electromagnetic.phase_currents = np.zeros(3)

        # Reset counters
        self.electrical_steps = 0
        self.mechanical_steps = 0
        self.thermal_steps = 0
        self.control_steps = 0
        self.logging_steps = 0

        # Clear history
        for key in self.history:
            self.history[key] = []

    def stop(self):
        """Stop simulation"""
        self.running = False

    # Convenience methods for setting up tests

    def set_load_force(self, force: float):
        """Set external load force

        Args:
            force: Load force in Newtons
        """
        self.mechanical.set_load_force(force)

    def command_position(self, position: float):
        """Command position

        Args:
            position: Desired position in mm
        """
        self.controller.command_position(position)

    def command_velocity(self, velocity: float):
        """Command velocity

        Args:
            velocity: Desired velocity in m/s
        """
        self.controller.command_velocity(velocity)

    def command_force(self, force: float):
        """Command force

        Args:
            force: Desired force in Newtons
        """
        self.controller.command_force(force)

    def set_control_mode(self, mode: str):
        """Set control mode

        Args:
            mode: 'position', 'velocity', 'current', or 'force'
        """
        self.controller.set_mode(mode)

    def set_position_gains(self, Kp: float = None, Ki: float = None, Kd: float = None):
        """Set position PID gains"""
        self.controller.set_position_gains(Kp, Ki, Kd)

    def set_velocity_gains(self, Kp: float = None, Ki: float = None, Kd: float = None):
        """Set velocity PID gains"""
        self.controller.set_velocity_gains(Kp, Ki, Kd)

    def set_cooling(self, h_conv: float):
        """Set convection coefficient (for modeling cooling)

        Args:
            h_conv: Convection coefficient in W/(m²·K)
        """
        self.thermal.set_convection_coefficient(h_conv)

    def get_status(self) -> str:
        """Get current simulation status

        Returns:
            Status string
        """
        status = f"Time: {self.time:.3f} s\n"
        status += f"Position: {self.mechanical.position * 1000:.2f} mm\n"
        status += f"Velocity: {self.mechanical.velocity:.3f} m/s\n"
        status += f"Force: {self.electromagnetic.calc_electromagnetic_force(self.mechanical.position):.1f} N\n"
        status += f"Current: {np.linalg.norm(self.electromagnetic.phase_currents):.2f} A\n"
        status += f"Temp (coils): {self.thermal.temperatures['coils']:.1f} °C\n"
        status += f"Temp (magnets): {self.thermal.temperatures['magnets']:.1f} °C\n"

        # Warnings
        warnings = self.thermal.get_warnings()
        if any(warnings.values()):
            status += "\n⚠️ WARNINGS:\n"
            if warnings['coils_over_temp']:
                status += "  - Coils over temperature!\n"
            if warnings['magnets_over_temp']:
                status += "  - Magnets over temperature!\n"
            if warnings['housing_over_temp']:
                status += "  - Housing over temperature!\n"

        return status

    def __repr__(self):
        return (f"LinearBLDCSimulation(t={self.time:.3f} s, "
                f"pos={self.mechanical.position * 1000:.1f} mm, "
                f"mode={self.controller.mode})")
