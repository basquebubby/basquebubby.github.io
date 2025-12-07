"""
Position Sensor Model

Simulates linear encoder with realistic noise and quantization
"""

import numpy as np


class PositionSensor:
    """Simulates a linear encoder with noise and quantization"""

    def __init__(self, resolution: float = 1e-6, noise_std: float = 0.1e-6):
        """Initialize position sensor

        Args:
            resolution: Encoder resolution in meters (default: 1 μm)
            noise_std: Standard deviation of measurement noise in meters
        """
        self.resolution = resolution
        self.noise_std = noise_std

        # State
        self.last_position = 0.0
        self.last_time = 0.0

    def measure_position(self, true_position: float, add_noise: bool = True) -> float:
        """Measure position with quantization and noise

        Args:
            true_position: Actual position in meters
            add_noise: Whether to add measurement noise

        Returns:
            Measured position in meters
        """
        # Quantize to encoder resolution
        quantized = np.round(true_position / self.resolution) * self.resolution

        # Add noise
        if add_noise:
            noise = np.random.normal(0, self.noise_std)
            measured = quantized + noise
        else:
            measured = quantized

        self.last_position = measured
        return measured

    def measure_velocity(self, true_position: float, current_time: float,
                        add_noise: bool = True) -> float:
        """Calculate velocity from position measurements

        Args:
            true_position: Actual position in meters
            current_time: Current time in seconds
            add_noise: Whether to add measurement noise

        Returns:
            Estimated velocity in m/s
        """
        # Measure position
        measured_position = self.measure_position(true_position, add_noise)

        # Calculate velocity
        dt = current_time - self.last_time
        if dt > 0 and self.last_time > 0:
            velocity = (measured_position - self.last_position) / dt
        else:
            velocity = 0.0

        # Update state
        self.last_position = measured_position
        self.last_time = current_time

        return velocity

    def reset(self):
        """Reset sensor state"""
        self.last_position = 0.0
        self.last_time = 0.0

    def __repr__(self):
        return f"PositionSensor(resolution={self.resolution * 1e6:.2f} μm)"
