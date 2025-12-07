"""
Electromagnetic Model for Linear BLDC Actuator

Includes:
- Magnetic field calculation from permanent magnets
- Force generation (Lorentz force)
- Back-EMF calculation
- Electrical dynamics (V = IR + L·dI/dt + back-EMF)
- Cogging force
- Position-dependent inductance
"""

import numpy as np
from typing import Tuple


class ElectromagneticModel:
    """Models electromagnetic behavior of the linear BLDC motor"""

    def __init__(self, specs: dict, materials: dict, constants: dict):
        self.specs = specs
        self.materials = materials
        self.constants = constants

        # Extract key parameters
        self.num_phases = specs['num_phases']
        self.num_magnets = specs['num_magnets']
        self.pole_pairs = specs['pole_pairs']
        self.pole_pitch = specs['pole_pitch'] / 1000.0  # Convert to meters
        self.stroke = specs['stroke'] / 1000.0  # Convert to meters

        # Electrical parameters
        self.R_phase = specs['phase_resistance']  # Ohms
        self.L_phase = specs['phase_inductance'] / 1000.0  # Convert mH to H
        self.voltage = specs['voltage']

        # Force constant (N/A)
        self.Kf = specs['force_constant']

        # Magnet parameters
        self.Br = specs['magnet_remanence']  # Tesla
        self.airgap = specs['airgap'] / 1000.0  # Convert to meters

        # State variables
        self.phase_currents = np.zeros(3)  # A, B, C phase currents
        self.back_emf = np.zeros(3)  # Back-EMF in each phase

        # Pre-calculate cogging force lookup table
        self._build_cogging_table()

    def _build_cogging_table(self):
        """Build lookup table for cogging force vs position"""
        # Cogging force is due to magnetic attraction between magnets and steel slots
        # It varies periodically with position at the slot pitch

        positions = np.linspace(0, self.stroke, 1000)
        self.cogging_positions = positions

        # Cogging force amplitude (estimate: ~5% of peak force)
        cogging_amplitude = 0.05 * self.specs['force_peak']

        # Cogging frequency: related to slot/pole interaction
        # For 12 coils and 8 magnets, LCM = 24, so 24 cycles over stroke
        num_cogging_cycles = 24

        # Create cogging force profile (combination of harmonics)
        self.cogging_forces = np.zeros_like(positions)
        for harmonic in [1, 2, 3]:
            phase = np.random.uniform(0, 2 * np.pi)  # Random phase
            amplitude = cogging_amplitude / harmonic  # Decreasing harmonics
            self.cogging_forces += amplitude * np.sin(
                2 * np.pi * num_cogging_cycles * harmonic * positions / self.stroke + phase
            )

    def get_cogging_force(self, position: float) -> float:
        """Get cogging force at given position

        Args:
            position: Position in meters

        Returns:
            Cogging force in Newtons (resistive force)
        """
        # Interpolate from lookup table
        if position < 0:
            position = 0
        elif position > self.stroke:
            position = self.stroke

        return np.interp(position, self.cogging_positions, self.cogging_forces)

    def get_commutation_signals(self, position: float) -> np.ndarray:
        """Get three-phase commutation signals (0 to 1) based on position

        For a linear motor, the commutation is based on electrical position.
        Electrical position = mechanical position / pole pitch

        Returns trapezoidal commutation (6-step approximation)

        Args:
            position: Position in meters

        Returns:
            Array of 3 commutation signals for phases A, B, C (range 0 to 1)
        """
        # Calculate electrical angle (radians)
        electrical_position = (position / self.pole_pitch) * 2 * np.pi

        # Three-phase signals, 120° apart
        # Using sinusoidal commutation (could also use trapezoidal)
        signal_A = np.sin(electrical_position)
        signal_B = np.sin(electrical_position - 2 * np.pi / 3)
        signal_C = np.sin(electrical_position - 4 * np.pi / 3)

        # Normalize to 0-1 range for force calculation
        # (negative values mean force in opposite direction)
        signals = np.array([signal_A, signal_B, signal_C])

        return signals

    def calc_back_emf(self, velocity: float, position: float) -> np.ndarray:
        """Calculate back-EMF in each phase

        Back-EMF = velocity × force_constant × commutation_signal

        Args:
            velocity: Velocity in m/s
            position: Position in meters

        Returns:
            Array of 3 back-EMF values for phases A, B, C (Volts)
        """
        commutation_signals = self.get_commutation_signals(position)
        back_emf = velocity * self.Kf * commutation_signals

        self.back_emf = back_emf
        return back_emf

    def calc_airgap_flux_density(self, position: float) -> float:
        """Calculate average airgap flux density at given position

        Simplified model: uses magnet remanence with fringing factor

        Args:
            position: Position in meters

        Returns:
            Flux density in Tesla
        """
        # Fringing factor (accounts for flux spreading in airgap)
        magnet_thickness = self.specs['magnet_thickness'] / 1000.0  # m
        fringing_factor = magnet_thickness / (magnet_thickness + self.airgap)

        # Airgap flux density
        B_airgap = self.Br * fringing_factor

        return B_airgap

    def calc_electromagnetic_force(self, position: float, phase_currents: np.ndarray = None) -> float:
        """Calculate electromagnetic force (thrust) from phase currents

        Uses simplified model: F = Kf × I_total
        where I_total is the vector sum of phase currents weighted by commutation

        Args:
            position: Position in meters
            phase_currents: Array of 3 phase currents [I_A, I_B, I_C]

        Returns:
            Force in Newtons (positive = forward direction)
        """
        if phase_currents is None:
            phase_currents = self.phase_currents

        # Get commutation signals
        commutation_signals = self.get_commutation_signals(position)

        # Calculate total current in the direction of motion
        # This is the dot product of current and commutation vectors
        I_effective = np.dot(phase_currents, commutation_signals)

        # For three-phase sinusoidal commutation:
        # The sum of sin²(θ) + sin²(θ-120°) + sin²(θ-240°) = 3/2
        # So we need to scale by 2/3 to get the correct force constant
        # This makes F = Kf × I_rms (where I_rms is the commanded current)
        force = self.Kf * I_effective * (2.0 / 3.0)

        return force

    def update_currents(self, voltage_commands: np.ndarray, back_emf: np.ndarray, dt: float) -> np.ndarray:
        """Update phase currents based on voltage commands and back-EMF

        Electrical dynamics: V = I×R + L×(dI/dt) + back_EMF
        Rearranged: dI/dt = (V - I×R - back_EMF) / L

        Args:
            voltage_commands: Array of 3 voltage commands for phases A, B, C
            back_emf: Array of 3 back-EMF values
            dt: Time step in seconds

        Returns:
            Updated phase currents
        """
        # Calculate current derivative
        dI_dt = (voltage_commands - self.phase_currents * self.R_phase - back_emf) / self.L_phase

        # Integrate (simple Euler method)
        self.phase_currents += dI_dt * dt

        return self.phase_currents

    def get_copper_loss(self) -> float:
        """Calculate copper losses (I²R) in all phases

        Returns:
            Power loss in Watts
        """
        # Sum of I²R for all three phases
        loss = np.sum(self.phase_currents ** 2) * self.R_phase
        return loss

    def get_core_loss(self, velocity: float) -> float:
        """Calculate core losses (hysteresis + eddy currents) in back iron

        Simplified model: P_core ∝ f^1.5 × B^2
        where f is electrical frequency and B is flux density

        Args:
            velocity: Velocity in m/s

        Returns:
            Power loss in Watts
        """
        # Electrical frequency
        f_elec = abs(velocity) / self.pole_pitch  # Hz

        # Average flux density in core
        B_core = self.Br * 0.8  # Approximate

        # Core loss coefficient (empirical)
        k_core = self.materials['steel_1018']['core_loss_coefficient']

        # Calculate loss
        loss = k_core * (f_elec ** 1.5) * (B_core ** 2)

        return loss

    def get_magnet_eddy_loss(self, velocity: float) -> float:
        """Calculate eddy current losses in permanent magnets

        These can be significant at high speeds with PWM drive

        Args:
            velocity: Velocity in m/s

        Returns:
            Power loss in Watts
        """
        # Simplified model: proportional to velocity squared
        # (eddy losses ∝ frequency²)
        f_elec = abs(velocity) / self.pole_pitch

        # Empirical coefficient (much smaller than core loss)
        k_eddy = 0.0001

        loss = k_eddy * (f_elec ** 2)

        return loss

    def get_total_losses(self, velocity: float) -> float:
        """Get total electromagnetic losses

        Args:
            velocity: Velocity in m/s

        Returns:
            Total power loss in Watts
        """
        copper_loss = self.get_copper_loss()
        core_loss = self.get_core_loss(velocity)
        magnet_loss = self.get_magnet_eddy_loss(velocity)

        return copper_loss + core_loss + magnet_loss

    def get_field_distribution(self, position: float, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """Get magnetic field distribution along the length of the motor

        Args:
            position: Current rotor position in meters
            num_points: Number of points to calculate

        Returns:
            Tuple of (positions, flux_densities) arrays
        """
        # Create position array along motor length
        z_positions = np.linspace(0, self.specs['back_iron_length'] / 1000.0, num_points)

        # Calculate flux density at each point
        flux_densities = np.zeros(num_points)

        for i, z in enumerate(z_positions):
            # Distance from each magnet center
            magnet_centers = np.linspace(
                self.specs['magnet_length'] / 2000.0,  # First magnet center
                self.specs['back_iron_length'] / 1000.0 - self.specs['magnet_length'] / 2000.0,
                self.num_magnets
            )

            # Sum contribution from all magnets
            B_total = 0
            for j, mag_center in enumerate(magnet_centers):
                distance = abs(z - mag_center)

                # Gaussian-like decay from magnet center
                sigma = self.specs['magnet_length'] / 2000.0  # Spread
                B_contribution = self.Br * np.exp(-0.5 * (distance / sigma) ** 2)

                # Alternate polarity (N-S-N-S...)
                polarity = 1 if j % 2 == 0 else -1
                B_total += polarity * B_contribution

            flux_densities[i] = B_total

        return z_positions, flux_densities

    def get_force_vs_current_curve(self, position: float, current_range: np.ndarray) -> np.ndarray:
        """Get force vs current curve at a given position

        Args:
            position: Position in meters
            current_range: Array of current values to evaluate

        Returns:
            Array of force values
        """
        forces = np.zeros_like(current_range)

        # Get commutation signals at this position
        comm_signals = self.get_commutation_signals(position)

        for i, current in enumerate(current_range):
            # Apply current to all phases with proper commutation
            phase_currents = current * comm_signals
            forces[i] = self.calc_electromagnetic_force(position, phase_currents)

        return forces

    def __repr__(self):
        return (f"ElectromagneticModel(Kf={self.Kf} N/A, "
                f"R={self.R_phase} Ω, L={self.L_phase * 1000} mH, "
                f"I=[{self.phase_currents[0]:.2f}, {self.phase_currents[1]:.2f}, {self.phase_currents[2]:.2f}] A)")
