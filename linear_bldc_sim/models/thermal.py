"""
Thermal Model for Linear BLDC Actuator

Includes:
- Heat generation (copper loss, core loss, eddy currents)
- Heat transfer (conduction, convection, radiation)
- Thermal capacitance of components
- Temperature limits and warnings
"""

import numpy as np
from typing import Dict


class ThermalModel:
    """Models thermal behavior using lumped thermal masses"""

    def __init__(self, specs: dict, materials: dict, constants: dict, thermal_limits: dict):
        self.specs = specs
        self.materials = materials
        self.constants = constants
        self.limits = thermal_limits

        # Thermal nodes (lumped masses)
        self.temperatures = {
            'coils': constants['ambient_temp'],  # °C
            'back_iron': constants['ambient_temp'],
            'magnets': constants['ambient_temp'],
            'housing': constants['ambient_temp'],
            'ambient': constants['ambient_temp'],
        }

        # Calculate thermal capacitances (J/K)
        self._calc_thermal_capacitances()

        # Calculate thermal resistances (K/W)
        self._calc_thermal_resistances()

        # Heat generation tracking
        self.heat_generated = {
            'copper_loss': 0.0,
            'core_loss': 0.0,
            'magnet_loss': 0.0,
        }

        # Warning flags
        self.warnings = {
            'coils_over_temp': False,
            'magnets_over_temp': False,
            'housing_over_temp': False,
        }

    def _calc_thermal_capacitances(self):
        """Calculate thermal capacitance (C = m × c_p) for each component"""

        # Coils (copper)
        copper_mass = self.specs['copper_mass']  # kg
        copper_cp = self.materials['copper']['specific_heat']  # J/(kg·K)
        C_coils = copper_mass * copper_cp

        # Back iron (steel)
        # Volume = π/4 × (OD² - ID²) × Length
        back_iron_od = self.specs['back_iron_od'] / 1000.0  # m
        back_iron_id = self.specs['back_iron_id'] / 1000.0  # m
        back_iron_length = self.specs['back_iron_length'] / 1000.0  # m
        back_iron_volume = np.pi / 4 * (back_iron_od ** 2 - back_iron_id ** 2) * back_iron_length
        back_iron_mass = back_iron_volume * self.materials['steel_1018']['density']
        back_iron_cp = self.materials['steel_1018']['specific_heat']
        C_back_iron = back_iron_mass * back_iron_cp

        # Magnets
        magnet_mass = self.specs['magnet_mass']  # kg
        magnet_cp = self.materials['NdFeB_N42']['specific_heat']  # J/(kg·K)
        C_magnets = magnet_mass * magnet_cp

        # Housing (aluminum)
        housing_od = self.specs['housing_od'] / 1000.0  # m
        housing_id = self.specs['housing_id'] / 1000.0  # m
        housing_length = self.specs['housing_length'] / 1000.0  # m
        housing_volume = np.pi / 4 * (housing_od ** 2 - housing_id ** 2) * housing_length
        housing_mass = housing_volume * self.materials['aluminum_6061']['density']
        housing_cp = self.materials['aluminum_6061']['specific_heat']
        C_housing = housing_mass * housing_cp

        self.thermal_capacitances = {
            'coils': C_coils,
            'back_iron': C_back_iron,
            'magnets': C_magnets,
            'housing': C_housing,
        }

    def _calc_thermal_resistances(self):
        """Calculate thermal resistances (K/W) between components

        R_thermal = L / (k × A)
        where L = length, k = thermal conductivity, A = area
        """

        # Conduction resistance: Coils → Back Iron
        # Approximate radial conduction through thin coil layer
        coil_thickness = (self.specs['coil_od'] - self.specs['coil_id']) / 2000.0  # m
        coil_length = self.specs['num_coils'] * self.specs['coil_length'] / 1000.0  # m
        coil_diameter = (self.specs['coil_od'] + self.specs['coil_id']) / 2000.0  # m
        coil_area = np.pi * coil_diameter * coil_length
        R_coil_to_iron = coil_thickness / (
                    self.materials['copper']['thermal_conductivity'] * coil_area * 0.5)  # *0.5 for poor contact

        # Conduction resistance: Back Iron → Housing
        iron_thickness = (self.specs['back_iron_od'] - self.specs['back_iron_id']) / 2000.0  # m
        iron_length = self.specs['back_iron_length'] / 1000.0  # m
        iron_diameter = (self.specs['back_iron_od'] + self.specs['back_iron_id']) / 2000.0  # m
        iron_area = np.pi * iron_diameter * iron_length
        R_iron_to_housing = iron_thickness / (self.materials['steel_1018']['thermal_conductivity'] * iron_area)

        # Conduction resistance: Magnets → Back Iron (through airgap)
        # This is primarily an air gap resistance
        airgap = self.specs['airgap'] / 1000.0  # m
        magnet_area = self.specs['num_magnets'] * (self.specs['magnet_length'] / 1000.0) * np.pi * (
                    self.specs['magnet_od'] / 1000.0)
        k_air = 0.026  # W/(m·K) for air
        R_magnet_to_iron = airgap / (k_air * magnet_area)

        # Convection resistance: Housing → Ambient
        # R_conv = 1 / (h × A)
        housing_od = self.specs['housing_od'] / 1000.0  # m
        housing_length = self.specs['housing_length'] / 1000.0  # m
        housing_surface_area = np.pi * housing_od * housing_length + 2 * np.pi / 4 * housing_od ** 2  # Cylinder + ends

        # Convection coefficient (W/(m²·K))
        # Natural convection for vertical cylinder: h ≈ 5-10 W/(m²·K)
        # With forced cooling (fan): h ≈ 25-100 W/(m²·K)
        self.h_conv = 10.0  # Natural convection (conservative)
        R_housing_to_ambient = 1 / (self.h_conv * housing_surface_area)

        # Radiation resistance (parallel with convection)
        # R_rad = 1 / (ε × σ × A × (T_hot² + T_cold²) × (T_hot + T_cold))
        # This is temperature-dependent, so we'll calculate it during update
        # For now, use approximate value at 50°C average
        epsilon = self.materials['aluminum_6061']['emissivity']
        sigma = self.constants['stefan_boltzmann']
        T_avg = 273.15 + 50  # K
        T_amb = 273.15 + self.constants['ambient_temp']  # K
        R_radiation = 1 / (epsilon * sigma * housing_surface_area * (T_avg ** 2 + T_amb ** 2) * (T_avg + T_amb))

        # Parallel combination of convection and radiation
        R_housing_to_ambient_total = 1 / (1 / R_housing_to_ambient + 1 / R_radiation)

        self.thermal_resistances = {
            'coil_to_iron': R_coil_to_iron,
            'iron_to_housing': R_iron_to_housing,
            'magnet_to_iron': R_magnet_to_iron,
            'housing_to_ambient': R_housing_to_ambient_total,
        }

        # Store surface area for radiation updates
        self.housing_surface_area = housing_surface_area

    def set_convection_coefficient(self, h: float):
        """Set convection coefficient (for modeling cooling)

        Args:
            h: Convection coefficient in W/(m²·K)
               Natural convection: 5-10
               Forced air (fan): 25-100
               Liquid cooling: 500-10000
        """
        self.h_conv = h
        # Recalculate housing-to-ambient resistance
        R_conv = 1 / (h * self.housing_surface_area)

        # Update with radiation (parallel)
        epsilon = self.materials['aluminum_6061']['emissivity']
        sigma = self.constants['stefan_boltzmann']
        T_housing = 273.15 + self.temperatures['housing']
        T_amb = 273.15 + self.temperatures['ambient']
        R_rad = 1 / (epsilon * sigma * self.housing_surface_area *
                     (T_housing ** 2 + T_amb ** 2) * (T_housing + T_amb))

        self.thermal_resistances['housing_to_ambient'] = 1 / (1 / R_conv + 1 / R_rad)

    def update_heat_generation(self, copper_loss: float, core_loss: float, magnet_loss: float):
        """Update heat generation sources

        Args:
            copper_loss: Copper loss in Watts
            core_loss: Core loss in Watts
            magnet_loss: Magnet eddy current loss in Watts
        """
        self.heat_generated['copper_loss'] = copper_loss
        self.heat_generated['core_loss'] = core_loss
        self.heat_generated['magnet_loss'] = magnet_loss

    def update(self, dt: float):
        """Update temperatures using thermal network

        Heat flow: Q = (T_hot - T_cold) / R_thermal
        Temperature change: dT/dt = Q / C_thermal

        Args:
            dt: Time step in seconds
        """
        # Current temperatures
        T_coils = self.temperatures['coils']
        T_iron = self.temperatures['back_iron']
        T_magnets = self.temperatures['magnets']
        T_housing = self.temperatures['housing']
        T_ambient = self.temperatures['ambient']

        # Heat flows (Watts)
        Q_coil_to_iron = (T_coils - T_iron) / self.thermal_resistances['coil_to_iron']
        Q_iron_to_housing = (T_iron - T_housing) / self.thermal_resistances['iron_to_housing']
        Q_magnet_to_iron = (T_magnets - T_iron) / self.thermal_resistances['magnet_to_iron']
        Q_housing_to_ambient = (T_housing - T_ambient) / self.thermal_resistances['housing_to_ambient']

        # Heat generation (Watts)
        Q_gen_coils = self.heat_generated['copper_loss']
        Q_gen_iron = self.heat_generated['core_loss']
        Q_gen_magnets = self.heat_generated['magnet_loss']

        # Temperature changes (K/s)
        dT_coils_dt = (Q_gen_coils - Q_coil_to_iron) / self.thermal_capacitances['coils']
        dT_iron_dt = (Q_gen_iron + Q_coil_to_iron + Q_magnet_to_iron - Q_iron_to_housing) / \
                     self.thermal_capacitances['back_iron']
        dT_magnets_dt = (Q_gen_magnets - Q_magnet_to_iron) / self.thermal_capacitances['magnets']
        dT_housing_dt = (Q_iron_to_housing - Q_housing_to_ambient) / self.thermal_capacitances['housing']

        # Limit temperature change rate for stability (max 100 K/s)
        max_dT_dt = 100.0  # K/s
        dT_coils_dt = np.clip(dT_coils_dt, -max_dT_dt, max_dT_dt)
        dT_iron_dt = np.clip(dT_iron_dt, -max_dT_dt, max_dT_dt)
        dT_magnets_dt = np.clip(dT_magnets_dt, -max_dT_dt, max_dT_dt)
        dT_housing_dt = np.clip(dT_housing_dt, -max_dT_dt, max_dT_dt)

        # Update temperatures (Euler integration)
        self.temperatures['coils'] += dT_coils_dt * dt
        self.temperatures['back_iron'] += dT_iron_dt * dt
        self.temperatures['magnets'] += dT_magnets_dt * dt
        self.temperatures['housing'] += dT_housing_dt * dt

        # Check for NaN or unreasonable temperatures
        for key in ['coils', 'back_iron', 'magnets', 'housing']:
            if not np.isfinite(self.temperatures[key]):
                print(f"Warning: Non-finite temperature in {key}, resetting to ambient")
                self.temperatures[key] = self.temperatures['ambient']
            # Physical limits (absolute zero to very hot)
            self.temperatures[key] = np.clip(self.temperatures[key], -273, 1000)

        # Check warnings
        self._check_thermal_limits()

        # Update radiation resistance (temperature-dependent)
        self._update_radiation_resistance()

    def _update_radiation_resistance(self):
        """Update radiation resistance based on current temperatures"""
        epsilon = self.materials['aluminum_6061']['emissivity']
        sigma = self.constants['stefan_boltzmann']
        T_housing = 273.15 + self.temperatures['housing']  # K
        T_amb = 273.15 + self.temperatures['ambient']  # K

        R_rad = 1 / (epsilon * sigma * self.housing_surface_area *
                     (T_housing ** 2 + T_amb ** 2) * (T_housing + T_amb))

        R_conv = 1 / (self.h_conv * self.housing_surface_area)

        # Parallel combination
        self.thermal_resistances['housing_to_ambient'] = 1 / (1 / R_conv + 1 / R_rad)

    def _check_thermal_limits(self):
        """Check if any components exceed temperature limits"""
        self.warnings['coils_over_temp'] = self.temperatures['coils'] > self.limits['coil_max_temp']
        self.warnings['magnets_over_temp'] = self.temperatures['magnets'] > self.limits['magnet_max_temp']
        self.warnings['housing_over_temp'] = self.temperatures['housing'] > self.limits['housing_max_temp']

    def get_warnings(self) -> Dict[str, bool]:
        """Get thermal warning flags

        Returns:
            Dictionary of warning flags
        """
        return self.warnings.copy()

    def get_max_temperature(self) -> float:
        """Get maximum temperature in the system

        Returns:
            Maximum temperature in °C
        """
        return max(self.temperatures['coils'],
                   self.temperatures['back_iron'],
                   self.temperatures['magnets'],
                   self.temperatures['housing'])

    def get_total_heat_generation(self) -> float:
        """Get total heat generation rate

        Returns:
            Total heat in Watts
        """
        return sum(self.heat_generated.values())

    def reset(self, ambient_temp: float = None):
        """Reset all temperatures to ambient

        Args:
            ambient_temp: Ambient temperature in °C (optional)
        """
        if ambient_temp is not None:
            self.temperatures['ambient'] = ambient_temp

        for key in self.temperatures:
            if key != 'ambient':
                self.temperatures[key] = self.temperatures['ambient']

        for key in self.warnings:
            self.warnings[key] = False

    def __repr__(self):
        return (f"ThermalModel(T_coils={self.temperatures['coils']:.1f}°C, "
                f"T_magnets={self.temperatures['magnets']:.1f}°C, "
                f"T_housing={self.temperatures['housing']:.1f}°C, "
                f"Q_total={self.get_total_heat_generation():.1f}W)")
