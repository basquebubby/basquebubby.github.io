"""
PID Controller Implementation

Provides position, velocity, and current control modes
"""

import numpy as np


class PIDController:
    """PID controller with anti-windup and output limiting"""

    def __init__(self, Kp: float = 1.0, Ki: float = 0.0, Kd: float = 0.0,
                 output_limit: float = None, integral_limit: float = None):
        """Initialize PID controller

        Args:
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
            output_limit: Maximum absolute output value
            integral_limit: Maximum absolute integral term
        """
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd

        self.output_limit = output_limit
        self.integral_limit = integral_limit

        # State variables
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_measurement = None

        # For debugging/analysis
        self.last_p_term = 0.0
        self.last_i_term = 0.0
        self.last_d_term = 0.0

    def update(self, setpoint: float, measurement: float, dt: float) -> float:
        """Update PID controller

        Args:
            setpoint: Desired value
            measurement: Actual measured value
            dt: Time step in seconds

        Returns:
            Control output
        """
        # Error
        error = setpoint - measurement

        # Proportional term
        p_term = self.Kp * error

        # Integral term
        self.integral += error * dt
        if self.integral_limit is not None:
            self.integral = np.clip(self.integral, -self.integral_limit, self.integral_limit)
        i_term = self.Ki * self.integral

        # Derivative term (use derivative of measurement to avoid spikes from setpoint changes)
        if self.previous_measurement is not None:
            derivative = -(measurement - self.previous_measurement) / dt
        else:
            derivative = 0.0
        d_term = self.Kd * derivative

        # Total output
        output = p_term + i_term + d_term

        # Apply output limits
        if self.output_limit is not None:
            output = np.clip(output, -self.output_limit, self.output_limit)

            # Anti-windup: don't integrate if output is saturated
            if abs(output) >= self.output_limit and np.sign(error) == np.sign(self.integral):
                self.integral -= error * dt  # Undo the integration

        # Save for next iteration
        self.previous_error = error
        self.previous_measurement = measurement

        # Save terms for debugging
        self.last_p_term = p_term
        self.last_i_term = i_term
        self.last_d_term = d_term

        return output

    def reset(self):
        """Reset controller state"""
        self.integral = 0.0
        self.previous_error = 0.0
        self.previous_measurement = None
        self.last_p_term = 0.0
        self.last_i_term = 0.0
        self.last_d_term = 0.0

    def set_gains(self, Kp: float = None, Ki: float = None, Kd: float = None):
        """Update PID gains

        Args:
            Kp: Proportional gain (optional)
            Ki: Integral gain (optional)
            Kd: Derivative gain (optional)
        """
        if Kp is not None:
            self.Kp = Kp
        if Ki is not None:
            self.Ki = Ki
        if Kd is not None:
            self.Kd = Kd

    def get_terms(self) -> dict:
        """Get individual PID terms for analysis

        Returns:
            Dictionary with P, I, D terms
        """
        return {
            'P': self.last_p_term,
            'I': self.last_i_term,
            'D': self.last_d_term,
        }

    def __repr__(self):
        return f"PIDController(Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd})"
