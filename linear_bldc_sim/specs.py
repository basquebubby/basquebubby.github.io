"""
Linear BLDC Actuator Specifications
All values from the complete actuator design
"""

import numpy as np

SPECS = {
    # Housing
    'housing_od': 80.0,  # mm
    'housing_id': 73.99,  # mm
    'housing_length': 300.0,  # mm
    'housing_material': 'aluminum_6061',

    # Back Iron (magnetic flux return path)
    'back_iron_od': 72.99,  # mm
    'back_iron_id': 66.98,  # mm
    'back_iron_length': 250.0,  # mm
    'back_iron_material': 'steel_1018',

    # Stator Coils
    'num_coils': 12,
    'num_phases': 3,
    'coils_per_phase': 4,
    'coil_od': 65.98,  # mm
    'coil_id': 63.98,  # mm
    'coil_length': 20.83,  # mm
    'turns_per_coil': 29,
    'wire_diameter': 0.701,  # mm
    'coil_resistance': 0.257,  # ohms per coil
    'phase_resistance': 1.030,  # ohms per phase
    'phase_inductance': 1.726,  # mH per phase (CORRECTED - was listed as H in prompt but should be mH)
    'copper_mass': 0.248,  # kg

    # Permanent Magnets
    'num_magnets': 8,
    'magnet_od': 62.37,  # mm
    'magnet_id': 38.45,  # mm
    'magnet_thickness': 11.96,  # mm (radial)
    'magnet_length': 48.38,  # mm (axial)
    'magnet_material': 'NdFeB_N42',
    'magnet_remanence': 1.32,  # Tesla
    'magnet_coercivity': -915000,  # A/m
    'magnet_mass': 5.499,  # kg

    # Shaft
    'shaft_diameter': 20.29,  # mm
    'shaft_length': 360.0,  # mm
    'shaft_material': 'steel_4140',
    'shaft_mass': 0.888,  # kg

    # Critical Airgap
    'airgap': 0.805,  # mm CRITICAL

    # Electrical
    'voltage': 48.0,  # VDC
    'current_continuous': 12.5,  # A
    'current_peak': 30.0,  # A

    # Performance
    'force_constant': 29.2,  # N/A
    'force_continuous': 364.9,  # N
    'force_peak': 875.9,  # N
    'max_velocity': 1.5,  # m/s
    'stroke': 250.0,  # mm

    # Total Mass
    'total_mass': 9.063,  # kg

    # Pole arrangement (alternating N-S)
    'pole_pairs': 4,
    'pole_pitch': 31.25,  # mm (electrical wavelength)

    # Derived parameters
    'coil_pitch': None,  # Will be calculated
    'electrical_frequency': None,  # Depends on velocity
}

# Calculate derived parameters
SPECS['coil_pitch'] = SPECS['back_iron_length'] / SPECS['num_coils']  # ~20.83 mm

def get_electrical_frequency(velocity_m_s):
    """Calculate electrical frequency from velocity

    Args:
        velocity_m_s: Velocity in m/s

    Returns:
        Electrical frequency in Hz
    """
    pole_pitch_m = SPECS['pole_pitch'] / 1000.0  # Convert to meters
    return velocity_m_s / pole_pitch_m


# Material properties for thermal and magnetic analysis
MATERIALS = {
    'aluminum_6061': {
        'density': 2700,  # kg/m³
        'specific_heat': 896,  # J/(kg·K)
        'thermal_conductivity': 167,  # W/(m·K)
        'emissivity': 0.1,  # Polished
    },
    'steel_1018': {
        'density': 7870,  # kg/m³
        'specific_heat': 486,  # J/(kg·K)
        'thermal_conductivity': 51.9,  # W/(m·K)
        'relative_permeability': 200,  # Typical for mild steel
        'saturation_flux_density': 2.0,  # Tesla
        'core_loss_coefficient': 0.001,  # Simplified
    },
    'steel_4140': {
        'density': 7850,  # kg/m³
        'specific_heat': 475,  # J/(kg·K)
        'thermal_conductivity': 42.6,  # W/(m·K)
    },
    'NdFeB_N42': {
        'density': 7500,  # kg/m³
        'specific_heat': 502,  # J/(kg·K)
        'thermal_conductivity': 9.0,  # W/(m·K)
        'remanence': 1.32,  # Tesla
        'coercivity': -915000,  # A/m
        'max_temp': 80,  # °C (demagnetization limit)
        'temp_coefficient': -0.11,  # %/°C for Br
    },
    'copper': {
        'density': 8960,  # kg/m³
        'specific_heat': 385,  # J/(kg·K)
        'thermal_conductivity': 401,  # W/(m·K)
        'resistivity_20C': 1.68e-8,  # Ω·m
        'temp_coefficient': 0.00393,  # 1/°C
    },
}

# Control parameters (default values, can be tuned)
CONTROL_PARAMS = {
    'position_control': {
        'Kp': 100.0,
        'Ki': 10.0,
        'Kd': 5.0,
    },
    'velocity_control': {
        'Kp': 50.0,
        'Ki': 5.0,
        'Kd': 2.0,
    },
    'current_control': {
        'Kp': 10.0,
        'Ki': 100.0,
        'Kd': 0.0,
    },
    'pwm_frequency': 20000,  # Hz
    'control_frequency': 1000,  # Hz (1 ms loop time)
}

# Physical constants
CONSTANTS = {
    'mu_0': 4 * np.pi * 1e-7,  # Permeability of free space (H/m)
    'g': 9.81,  # Gravitational acceleration (m/s²)
    'ambient_temp': 25.0,  # °C
    'stefan_boltzmann': 5.67e-8,  # W/(m²·K⁴)
}

# Thermal limits
THERMAL_LIMITS = {
    'coil_max_temp': 155.0,  # °C (Class F insulation)
    'magnet_max_temp': 80.0,  # °C (N42 demagnetization)
    'housing_max_temp': 100.0,  # °C (safety limit)
}

# Friction and mechanical parameters
MECHANICAL_PARAMS = {
    'coulomb_friction': 5.0,  # N (static friction force)
    'viscous_friction': 2.0,  # N·s/m (damping coefficient)
    'bearing_stiffness': 1e6,  # N/m
    'end_stop_stiffness': 1e7,  # N/m (for impact simulation)
    'end_stop_damping': 1000,  # N·s/m
}

if __name__ == '__main__':
    print("Linear BLDC Actuator Specifications")
    print("=" * 50)
    print(f"Force Constant: {SPECS['force_constant']} N/A")
    print(f"Continuous Force @ {SPECS['current_continuous']}A: {SPECS['force_continuous']} N")
    print(f"Peak Force @ {SPECS['current_peak']}A: {SPECS['force_peak']} N")
    print(f"Total Mass: {SPECS['total_mass']} kg")
    print(f"Stroke: {SPECS['stroke']} mm")
    print(f"Phase Resistance: {SPECS['phase_resistance']} Ω")
    print(f"Phase Inductance: {SPECS['phase_inductance']} mH")
    print(f"Airgap: {SPECS['airgap']} mm")
