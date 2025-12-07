"""
Main Control System for Linear BLDC Actuator

Combines PID control with commutation to provide:
- Position control
- Velocity control
- Force/Current control
"""

import numpy as np
from .pid import PIDController
from .commutation import CommutationController


class ControlSystem:
    """Main controller for the linear BLDC actuator"""

    def __init__(self, specs: dict, control_params: dict):
        """Initialize control system

        Args:
            specs: Motor specifications
            control_params: Control parameters (PID gains, etc.)
        """
        self.specs = specs
        self.params = control_params

        # Control mode
        self.mode = 'position'  # 'position', 'velocity', 'current', or 'force'

        # Setpoints
        self.position_setpoint = 0.0  # meters
        self.velocity_setpoint = 0.0  # m/s
        self.current_setpoint = 0.0  # Amps (total motor current)
        self.force_setpoint = 0.0  # Newtons

        # PID controllers for each mode
        self.position_pid = PIDController(
            Kp=control_params['position_control']['Kp'],
            Ki=control_params['position_control']['Ki'],
            Kd=control_params['position_control']['Kd'],
            output_limit=specs['max_velocity']
        )

        self.velocity_pid = PIDController(
            Kp=control_params['velocity_control']['Kp'],
            Ki=control_params['velocity_control']['Ki'],
            Kd=control_params['velocity_control']['Kd'],
            output_limit=specs['force_peak'] / specs['force_constant']  # Max current
        )

        self.current_pid = PIDController(
            Kp=control_params['current_control']['Kp'],
            Ki=control_params['current_control']['Ki'],
            Kd=control_params['current_control']['Kd'],
            output_limit=specs['voltage']
        )

        # Commutation controller
        self.commutation = CommutationController(specs, control_params['pwm_frequency'])

        # Current limits
        self.current_limit = specs['current_peak']
        self.current_continuous = specs['current_continuous']

    def update(self, position: float, velocity: float, actual_currents: np.ndarray,
               em_model, dt: float) -> np.ndarray:
        """Update control system and return voltage commands

        Args:
            position: Current position in meters
            velocity: Current velocity in m/s
            actual_currents: Actual phase currents [I_A, I_B, I_C]
            em_model: Electromagnetic model (for back-EMF calculation)
            dt: Time step in seconds

        Returns:
            Phase voltage commands [V_A, V_B, V_C]
        """
        # Cascade control structure:
        # Position → Velocity → Current → Voltage

        if self.mode == 'position':
            # Position control → desired velocity
            desired_velocity = self.position_pid.update(self.position_setpoint, position, dt)

            # Velocity control → desired current
            desired_current = self.velocity_pid.update(desired_velocity, velocity, dt)

        elif self.mode == 'velocity':
            # Velocity control → desired current
            desired_current = self.velocity_pid.update(self.velocity_setpoint, velocity, dt)

        elif self.mode == 'current':
            # Direct current command
            desired_current = self.current_setpoint

        elif self.mode == 'force':
            # Force → current (using force constant)
            desired_current = self.force_setpoint / self.specs['force_constant']

        else:
            raise ValueError(f"Invalid control mode: {self.mode}")

        # Limit current
        desired_current = np.clip(desired_current, -self.current_limit, self.current_limit)

        # Convert total current to three-phase current commands
        phase_current_commands = self.commutation.current_to_phase_commands(position, desired_current)

        # Current control → voltage commands
        voltage_commands = self.commutation.calc_phase_voltages(
            position, phase_current_commands, actual_currents, em_model
        )

        return voltage_commands

    def set_mode(self, mode: str):
        """Set control mode

        Args:
            mode: 'position', 'velocity', 'current', or 'force'
        """
        if mode in ['position', 'velocity', 'current', 'force']:
            self.mode = mode
            # Reset PID integrators when switching modes
            self.position_pid.reset()
            self.velocity_pid.reset()
            self.current_pid.reset()
        else:
            raise ValueError(f"Invalid control mode: {mode}")

    def set_position_setpoint(self, position: float):
        """Set position setpoint

        Args:
            position: Desired position in meters
        """
        # Clip to stroke limits
        position = np.clip(position, 0, self.specs['stroke'] / 1000.0)
        self.position_setpoint = position

    def set_velocity_setpoint(self, velocity: float):
        """Set velocity setpoint

        Args:
            velocity: Desired velocity in m/s
        """
        # Clip to max velocity
        velocity = np.clip(velocity, -self.specs['max_velocity'], self.specs['max_velocity'])
        self.velocity_setpoint = velocity

    def set_current_setpoint(self, current: float):
        """Set current setpoint

        Args:
            current: Desired current in Amps
        """
        # Clip to current limit
        current = np.clip(current, -self.current_limit, self.current_limit)
        self.current_setpoint = current

    def set_force_setpoint(self, force: float):
        """Set force setpoint

        Args:
            force: Desired force in Newtons
        """
        # Clip to peak force
        force = np.clip(force, -self.specs['force_peak'], self.specs['force_peak'])
        self.force_setpoint = force

    def set_position_gains(self, Kp: float = None, Ki: float = None, Kd: float = None):
        """Set position PID gains

        Args:
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
        """
        self.position_pid.set_gains(Kp, Ki, Kd)

    def set_velocity_gains(self, Kp: float = None, Ki: float = None, Kd: float = None):
        """Set velocity PID gains

        Args:
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
        """
        self.velocity_pid.set_gains(Kp, Ki, Kd)

    def command_position(self, position: float):
        """Command position (convenience method)

        Args:
            position: Desired position in mm
        """
        self.set_mode('position')
        self.set_position_setpoint(position / 1000.0)  # Convert mm to m

    def command_velocity(self, velocity: float):
        """Command velocity (convenience method)

        Args:
            velocity: Desired velocity in m/s
        """
        self.set_mode('velocity')
        self.set_velocity_setpoint(velocity)

    def command_force(self, force: float):
        """Command force (convenience method)

        Args:
            force: Desired force in Newtons
        """
        self.set_mode('force')
        self.set_force_setpoint(force)

    def reset(self):
        """Reset all controllers"""
        self.position_pid.reset()
        self.velocity_pid.reset()
        self.current_pid.reset()

    def get_control_effort(self) -> float:
        """Get current control effort (commanded current)

        Returns:
            Control effort in Amps
        """
        if self.mode == 'position':
            return self.velocity_pid.last_p_term / self.specs['force_constant']
        elif self.mode == 'velocity':
            return self.velocity_setpoint
        elif self.mode == 'current':
            return self.current_setpoint
        elif self.mode == 'force':
            return self.force_setpoint / self.specs['force_constant']

    def __repr__(self):
        return f"ControlSystem(mode={self.mode}, setpoint={getattr(self, self.mode + '_setpoint')})"
