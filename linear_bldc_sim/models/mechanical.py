"""
Mechanical Dynamics Model for Linear BLDC Actuator

Includes:
- Newton's laws of motion (F = ma)
- Friction (Coulomb + viscous)
- External load forces
- Position limits and end stops
- Collision detection
"""

import numpy as np


class MechanicalModel:
    """Models mechanical dynamics of the moving shaft and attached load"""

    def __init__(self, specs: dict, mechanical_params: dict, constants: dict):
        self.specs = specs
        self.params = mechanical_params
        self.constants = constants

        # Mass
        self.mass = specs['total_mass']  # kg

        # Position limits
        self.stroke = specs['stroke'] / 1000.0  # Convert to meters
        self.min_position = 0.0
        self.max_position = self.stroke

        # Friction parameters
        self.coulomb_friction = mechanical_params['coulomb_friction']  # N
        self.viscous_friction = mechanical_params['viscous_friction']  # N·s/m

        # End stop parameters
        self.end_stop_stiffness = mechanical_params['end_stop_stiffness']  # N/m
        self.end_stop_damping = mechanical_params['end_stop_damping']  # N·s/m

        # State variables
        self.position = 0.0  # meters
        self.velocity = 0.0  # m/s
        self.acceleration = 0.0  # m/s²

        # External forces
        self.load_force = 0.0  # N (external load, positive = resisting motion)
        self.gravity_force = 0.0  # N (can be set for vertical orientation)

        # Limits
        self.max_velocity = specs['max_velocity']  # m/s
        self.max_acceleration = 100.0  # m/s² (reasonable limit)

        # Impact detection
        self.at_end_stop = False

    def set_load_force(self, force: float):
        """Set external load force

        Args:
            force: Load force in Newtons (positive = resisting motion in positive direction)
        """
        self.load_force = force

    def set_gravity_orientation(self, angle_deg: float):
        """Set gravity component based on motor orientation

        Args:
            angle_deg: Angle from horizontal in degrees
                      0° = horizontal (no gravity effect)
                      90° = vertical upward motion
                      -90° = vertical downward motion
        """
        angle_rad = np.deg2rad(angle_deg)
        self.gravity_force = self.mass * self.constants['g'] * np.sin(angle_rad)

    def calc_friction_force(self, velocity: float) -> float:
        """Calculate friction force

        Friction = Coulomb (constant) + Viscous (velocity-dependent)

        Args:
            velocity: Velocity in m/s

        Returns:
            Friction force in Newtons (always opposes motion)
        """
        # Coulomb friction (sign depends on direction)
        if abs(velocity) < 1e-6:  # Near zero velocity
            coulomb = 0.0  # Static friction handled separately if needed
        else:
            coulomb = self.coulomb_friction * np.sign(velocity)

        # Viscous friction (proportional to velocity)
        viscous = self.viscous_friction * velocity

        # Total friction opposes motion
        friction = coulomb + viscous

        return friction

    def calc_end_stop_force(self, position: float, velocity: float) -> float:
        """Calculate force from end stops (spring-damper at limits)

        Args:
            position: Position in meters
            velocity: Velocity in m/s

        Returns:
            End stop force in Newtons
        """
        force = 0.0

        # Check lower limit
        if position < self.min_position:
            penetration = self.min_position - position
            force = self.end_stop_stiffness * penetration - self.end_stop_damping * velocity
            self.at_end_stop = True
        # Check upper limit
        elif position > self.max_position:
            penetration = position - self.max_position
            force = -self.end_stop_stiffness * penetration - self.end_stop_damping * velocity
            self.at_end_stop = True
        else:
            self.at_end_stop = False

        return force

    def update(self, electromagnetic_force: float, dt: float):
        """Update mechanical state using Newton's laws

        F_net = m × a
        F_net = F_em - F_friction - F_load - F_gravity + F_endstop

        Args:
            electromagnetic_force: Force from motor in Newtons
            dt: Time step in seconds
        """
        # Calculate all forces
        friction_force = self.calc_friction_force(self.velocity)
        end_stop_force = self.calc_end_stop_force(self.position, self.velocity)

        # Net force (force balance)
        F_net = (electromagnetic_force
                 - friction_force
                 - self.load_force
                 - self.gravity_force
                 + end_stop_force)

        # Acceleration from Newton's second law
        self.acceleration = F_net / self.mass

        # Limit acceleration (physical constraint)
        if abs(self.acceleration) > self.max_acceleration:
            self.acceleration = np.sign(self.acceleration) * self.max_acceleration

        # Integrate acceleration to get velocity (Euler integration)
        self.velocity += self.acceleration * dt

        # Limit velocity
        if abs(self.velocity) > self.max_velocity:
            self.velocity = np.sign(self.velocity) * self.max_velocity

        # Integrate velocity to get position
        self.position += self.velocity * dt

        # Hard limits on position (backup to end stop forces)
        if self.position < self.min_position:
            self.position = self.min_position
            if self.velocity < 0:
                self.velocity = 0  # Stop at limit
        elif self.position > self.max_position:
            self.position = self.max_position
            if self.velocity > 0:
                self.velocity = 0  # Stop at limit

    def get_kinetic_energy(self) -> float:
        """Calculate kinetic energy

        Returns:
            Kinetic energy in Joules
        """
        return 0.5 * self.mass * self.velocity ** 2

    def get_potential_energy(self) -> float:
        """Calculate gravitational potential energy

        Returns:
            Potential energy in Joules
        """
        return self.mass * self.constants['g'] * self.position * np.sin(
            np.arcsin(self.gravity_force / (self.mass * self.constants['g'])) if self.mass * self.constants[
                'g'] > 0 else 0
        )

    def reset(self, position: float = 0.0, velocity: float = 0.0):
        """Reset to initial conditions

        Args:
            position: Initial position in meters
            velocity: Initial velocity in m/s
        """
        self.position = np.clip(position, self.min_position, self.max_position)
        self.velocity = velocity
        self.acceleration = 0.0
        self.at_end_stop = False

    def __repr__(self):
        return (f"MechanicalModel(pos={self.position * 1000:.2f} mm, "
                f"vel={self.velocity:.3f} m/s, "
                f"acc={self.acceleration:.2f} m/s², "
                f"mass={self.mass:.2f} kg)")
