"""
Commutation Controller for Linear BLDC Motor

Handles phase switching and PWM voltage generation
"""

import numpy as np


class CommutationController:
    """Controls phase voltages based on position and desired current/force"""

    def __init__(self, specs: dict, pwm_frequency: float = 20000):
        """Initialize commutation controller

        Args:
            specs: Motor specifications
            pwm_frequency: PWM switching frequency in Hz
        """
        self.specs = specs
        self.pwm_frequency = pwm_frequency
        self.pwm_period = 1.0 / pwm_frequency

        self.voltage_bus = specs['voltage']
        self.current_limit = specs['current_peak']

        # Commutation mode
        self.mode = 'sinusoidal'  # 'sinusoidal' or 'trapezoidal'

    def calc_phase_voltages(self, position: float, current_command: np.ndarray,
                            actual_currents: np.ndarray, em_model) -> np.ndarray:
        """Calculate phase voltages to achieve desired currents

        Uses simple PI current control in each phase

        Args:
            position: Position in meters
            current_command: Desired current in each phase [I_A, I_B, I_C]
            actual_currents: Measured current in each phase
            em_model: Electromagnetic model (for back-EMF)

        Returns:
            Phase voltages [V_A, V_B, V_C]
        """
        # Simple proportional control: V = V_bus × (I_desired / I_max)
        # More sophisticated: V = R×I + back_EMF + L×dI/dt (feedforward)

        # Current error
        current_error = current_command - actual_currents

        # Proportional gain (simple)
        Kp_current = 5.0

        # Voltage command from current error
        voltage_ff = current_error * Kp_current

        # Limit to bus voltage
        voltages = np.clip(voltage_ff, -self.voltage_bus, self.voltage_bus)

        return voltages

    def current_to_phase_commands(self, position: float, total_current: float) -> np.ndarray:
        """Convert total motor current to three-phase current commands

        Uses commutation signals to distribute current among phases

        Args:
            position: Position in meters
            total_current: Total motor current (scalar)

        Returns:
            Three-phase current commands [I_A, I_B, I_C]
        """
        # Get commutation signals from electromagnetic model
        pole_pitch = self.specs['pole_pitch'] / 1000.0  # m
        electrical_angle = (position / pole_pitch) * 2 * np.pi

        if self.mode == 'sinusoidal':
            # Sinusoidal commutation (smooth, low torque ripple)
            signal_A = np.sin(electrical_angle)
            signal_B = np.sin(electrical_angle - 2 * np.pi / 3)
            signal_C = np.sin(electrical_angle - 4 * np.pi / 3)
        else:  # 'trapezoidal'
            # Trapezoidal commutation (6-step, higher torque ripple)
            signal_A = self._trapezoidal_wave(electrical_angle)
            signal_B = self._trapezoidal_wave(electrical_angle - 2 * np.pi / 3)
            signal_C = self._trapezoidal_wave(electrical_angle - 4 * np.pi / 3)

        # Distribute current according to commutation signals
        # For sinusoidal commutation, the peak phase current equals the desired current
        # and the effective torque-producing current is sqrt(3/2) times smaller
        phase_currents = total_current * np.array([signal_A, signal_B, signal_C])

        # Limit individual phase currents
        phase_currents = np.clip(phase_currents, -self.current_limit, self.current_limit)

        return phase_currents

    def _trapezoidal_wave(self, angle: float) -> float:
        """Generate trapezoidal wave for 6-step commutation

        Args:
            angle: Electrical angle in radians

        Returns:
            Value between -1 and 1
        """
        # Normalize angle to 0-2π
        angle = angle % (2 * np.pi)

        # 6 sectors, each 60° (π/3 radians)
        if angle < np.pi / 3:
            return 1.0
        elif angle < 2 * np.pi / 3:
            return 1.0 - 6 * (angle - np.pi / 3) / np.pi
        elif angle < 4 * np.pi / 3:
            return -1.0
        elif angle < 5 * np.pi / 3:
            return -1.0 + 6 * (angle - 4 * np.pi / 3) / np.pi
        else:
            return 1.0

    def set_mode(self, mode: str):
        """Set commutation mode

        Args:
            mode: 'sinusoidal' or 'trapezoidal'
        """
        if mode in ['sinusoidal', 'trapezoidal']:
            self.mode = mode
        else:
            raise ValueError(f"Invalid commutation mode: {mode}")

    def __repr__(self):
        return f"CommutationController(mode={self.mode}, PWM={self.pwm_frequency / 1000:.1f} kHz)"
