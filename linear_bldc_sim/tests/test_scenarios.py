"""
Test Scenarios for Linear BLDC Simulation

Includes:
1. Step response
2. Frequency response
3. Force testing
4. Thermal runaway
5. Trajectory tracking
6. Cogging force measurement
7. Efficiency test
"""

import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, Tuple
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation import LinearBLDCSimulation
from visualization.dashboard import plot_all_dashboards


class TestScenarios:
    """Collection of test scenarios for the linear BLDC actuator"""

    def __init__(self, simulation: LinearBLDCSimulation = None):
        """Initialize test scenarios

        Args:
            simulation: Simulation instance (creates new if None)
        """
        self.sim = simulation if simulation is not None else LinearBLDCSimulation()

    def test_step_response(self, target_position: float = 100.0,
                           Kp: float = 100, Ki: float = 10, Kd: float = 5,
                           duration: float = 1.0) -> Dict:
        """Test step response

        Args:
            target_position: Target position in mm
            Kp: Proportional gain
            Ki: Integral gain
            Kd: Derivative gain
            duration: Test duration in seconds

        Returns:
            Results dictionary with metrics
        """
        print(f"\n{'=' * 60}")
        print("TEST 1: STEP RESPONSE")
        print(f"{'=' * 60}")
        print(f"Target: {target_position} mm")
        print(f"PID Gains: Kp={Kp}, Ki={Ki}, Kd={Kd}")

        # Reset and configure
        self.sim.reset()
        self.sim.set_position_gains(Kp=Kp, Ki=Ki, Kd=Kd)
        self.sim.command_position(target_position)

        # Run simulation
        history = self.sim.run(duration=duration, dt=1e-4)

        # Calculate metrics
        pos = np.array(history['position'])
        time = np.array(history['time'])
        setpoint = target_position

        # Settling time (2% criterion)
        tolerance = 0.02 * setpoint
        settled = np.where(np.abs(pos - setpoint) < tolerance)[0]
        settling_time = time[settled[0]] if len(settled) > 0 else None

        # Overshoot
        overshoot = (np.max(pos) - setpoint) / setpoint * 100 if setpoint > 0 else 0

        # Steady-state error
        ss_error = np.mean(pos[-100:]) - setpoint if len(pos) > 100 else pos[-1] - setpoint

        # Rise time (10% to 90%)
        p10 = 0.1 * setpoint
        p90 = 0.9 * setpoint
        t10_idx = np.where(pos >= p10)[0]
        t90_idx = np.where(pos >= p90)[0]
        rise_time = (time[t90_idx[0]] - time[t10_idx[0]]) if len(t10_idx) > 0 and len(t90_idx) > 0 else None

        results = {
            'settling_time': settling_time,
            'overshoot': overshoot,
            'steady_state_error': ss_error,
            'rise_time': rise_time,
            'history': history,
        }

        print(f"\nResults:")
        print(f"  Rise Time: {rise_time * 1000:.1f} ms" if rise_time else "  Rise Time: N/A")
        print(f"  Settling Time: {settling_time * 1000:.1f} ms" if settling_time else "  Settling Time: N/A")
        print(f"  Overshoot: {overshoot:.1f}%")
        print(f"  Steady-State Error: {ss_error:.3f} mm")

        return results

    def test_force_output(self, test_currents: np.ndarray = None,
                         duration: float = 0.5) -> Dict:
        """Test force vs current relationship

        Args:
            test_currents: Array of currents to test (uses default if None)
            duration: Duration for each test point

        Returns:
            Results dictionary
        """
        print(f"\n{'=' * 60}")
        print("TEST 3: FORCE OUTPUT")
        print(f"{'=' * 60}")

        if test_currents is None:
            test_currents = np.array([5, 10, 12.5, 15, 20, 25, 30])

        forces_measured = []
        forces_predicted = []

        for current in test_currents:
            print(f"\nTesting current: {current} A")

            # Reset and command force
            self.sim.reset()
            predicted_force = current * self.sim.specs['force_constant']
            self.sim.command_force(predicted_force)

            # Run briefly to settle
            history = self.sim.run(duration=duration, dt=1e-4)

            # Measure average force in steady state
            measured_force = np.mean(history['force_em'][-100:])
            forces_measured.append(measured_force)
            forces_predicted.append(predicted_force)

            print(f"  Predicted: {predicted_force:.1f} N")
            print(f"  Measured: {measured_force:.1f} N")
            print(f"  Error: {(measured_force - predicted_force) / predicted_force * 100:.1f}%")

        results = {
            'currents': test_currents,
            'forces_measured': np.array(forces_measured),
            'forces_predicted': np.array(forces_predicted),
            'force_constant_measured': np.mean(forces_measured / test_currents),
        }

        Kf_measured = results['force_constant_measured']
        Kf_spec = self.sim.specs['force_constant']
        print(f"\nForce Constant:")
        print(f"  Specified: {Kf_spec:.2f} N/A")
        print(f"  Measured: {Kf_measured:.2f} N/A")
        print(f"  Error: {(Kf_measured - Kf_spec) / Kf_spec * 100:.1f}%")

        return results

    def test_thermal_runaway(self, current: float = 12.5, duration: float = 100.0,
                            h_conv: float = 10.0) -> Dict:
        """Test thermal behavior under continuous load

        Args:
            current: Continuous current in Amps
            duration: Test duration in seconds
            h_conv: Convection coefficient (W/m²K)

        Returns:
            Results dictionary
        """
        print(f"\n{'=' * 60}")
        print("TEST 4: THERMAL RUNAWAY")
        print(f"{'=' * 60}")
        print(f"Continuous Current: {current} A")
        print(f"Duration: {duration} s")
        print(f"Convection: {h_conv} W/(m²·K)")

        # Reset and configure
        self.sim.reset()
        self.sim.set_cooling(h_conv)

        # Hold position with constant current
        force = current * self.sim.specs['force_constant']
        self.sim.command_force(force)

        # Run simulation
        history = self.sim.run(duration=duration, dt=1e-3)

        # Check thermal limits
        max_temp_coils = np.max(history['temp_coils'])
        max_temp_magnets = np.max(history['temp_magnets'])
        final_temp_coils = history['temp_coils'][-1]

        # Time to thermal limits
        coil_limit = 155.0
        magnet_limit = 80.0

        over_coil_limit = np.where(np.array(history['temp_coils']) > coil_limit)[0]
        over_magnet_limit = np.where(np.array(history['temp_magnets']) > magnet_limit)[0]

        time_to_coil_limit = history['time'][over_coil_limit[0]] if len(over_coil_limit) > 0 else None
        time_to_magnet_limit = history['time'][over_magnet_limit[0]] if len(over_magnet_limit) > 0 else None

        results = {
            'max_temp_coils': max_temp_coils,
            'max_temp_magnets': max_temp_magnets,
            'final_temp_coils': final_temp_coils,
            'time_to_coil_limit': time_to_coil_limit,
            'time_to_magnet_limit': time_to_magnet_limit,
            'history': history,
        }

        print(f"\nResults:")
        print(f"  Max Coil Temp: {max_temp_coils:.1f} °C")
        print(f"  Max Magnet Temp: {max_temp_magnets:.1f} °C")
        print(f"  Final Coil Temp: {final_temp_coils:.1f} °C")
        if time_to_coil_limit:
            print(f"  ⚠️ Coil limit reached at {time_to_coil_limit:.1f} s")
        if time_to_magnet_limit:
            print(f"  ⚠️ Magnet limit reached at {time_to_magnet_limit:.1f} s")

        return results

    def test_cogging_force(self) -> Dict:
        """Measure cogging force (detent force with zero current)

        Returns:
            Results dictionary
        """
        print(f"\n{'=' * 60}")
        print("TEST 6: COGGING FORCE")
        print(f"{'=' * 60}")

        positions = np.linspace(0, self.sim.specs['stroke'], 100)
        cogging_forces = []

        for pos in positions:
            force = self.sim.electromagnetic.get_cogging_force(pos / 1000.0)  # Convert to m
            cogging_forces.append(force)

        cogging_forces = np.array(cogging_forces)
        max_cogging = np.max(np.abs(cogging_forces))
        rms_cogging = np.sqrt(np.mean(cogging_forces ** 2))

        results = {
            'positions': positions,
            'cogging_forces': cogging_forces,
            'max_cogging': max_cogging,
            'rms_cogging': rms_cogging,
        }

        print(f"\nResults:")
        print(f"  Max Cogging Force: {max_cogging:.2f} N")
        print(f"  RMS Cogging Force: {rms_cogging:.2f} N")
        print(f"  As % of continuous force: {max_cogging / self.sim.specs['force_continuous'] * 100:.1f}%")

        return results

    def test_efficiency(self, velocities: np.ndarray = None,
                       load_force: float = 100.0) -> Dict:
        """Test efficiency at various speeds

        Args:
            velocities: Array of velocities to test (m/s)
            load_force: Load force in Newtons

        Returns:
            Results dictionary
        """
        print(f"\n{'=' * 60}")
        print("TEST 7: EFFICIENCY")
        print(f"{'=' * 60}")
        print(f"Load Force: {load_force} N")

        if velocities is None:
            velocities = np.array([0.1, 0.3, 0.5, 0.7, 1.0, 1.2, 1.5])

        efficiencies = []
        power_in_list = []
        power_out_list = []

        for velocity in velocities:
            print(f"\nTesting velocity: {velocity} m/s")

            # Reset and set load
            self.sim.reset()
            self.sim.set_load_force(load_force)
            self.sim.command_velocity(velocity)

            # Run to steady state
            history = self.sim.run(duration=2.0, dt=1e-4)

            # Calculate power in steady state
            vel_actual = np.mean(history['velocity'][-100:])
            current = np.mean(history['current_total'][-100:])
            voltage = self.sim.specs['voltage']

            power_in = voltage * current  # Electrical power in
            power_out = load_force * vel_actual  # Mechanical power out
            efficiency = (power_out / power_in * 100) if power_in > 0 else 0

            efficiencies.append(efficiency)
            power_in_list.append(power_in)
            power_out_list.append(power_out)

            print(f"  Power In: {power_in:.1f} W")
            print(f"  Power Out: {power_out:.1f} W")
            print(f"  Efficiency: {efficiency:.1f}%")

        results = {
            'velocities': velocities,
            'efficiencies': np.array(efficiencies),
            'power_in': np.array(power_in_list),
            'power_out': np.array(power_out_list),
            'peak_efficiency': np.max(efficiencies),
        }

        print(f"\nPeak Efficiency: {results['peak_efficiency']:.1f}%")

        return results

    def run_all_tests(self) -> Dict:
        """Run all test scenarios

        Returns:
            Dictionary with all test results
        """
        print("\n" + "=" * 60)
        print("RUNNING ALL TEST SCENARIOS")
        print("=" * 60)

        results = {}

        # Test 1: Step Response
        results['step_response'] = self.test_step_response()

        # Test 3: Force Output
        results['force_output'] = self.test_force_output()

        # Test 4: Thermal Runaway
        results['thermal'] = self.test_thermal_runaway(duration=50.0)

        # Test 6: Cogging Force
        results['cogging'] = self.test_cogging_force()

        # Test 7: Efficiency
        results['efficiency'] = self.test_efficiency()

        print("\n" + "=" * 60)
        print("ALL TESTS COMPLETE")
        print("=" * 60)

        return results


def run_validation_tests():
    """Run validation tests and compare to specifications"""
    print("\n" + "=" * 70)
    print("LINEAR BLDC ACTUATOR - VALIDATION TESTS")
    print("=" * 70)

    sim = LinearBLDCSimulation()
    tests = TestScenarios(sim)

    # Run all tests
    results = tests.run_all_tests()

    # Validation summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    # Force constant
    Kf_spec = sim.specs['force_constant']
    Kf_meas = results['force_output']['force_constant_measured']
    Kf_error = abs(Kf_meas - Kf_spec) / Kf_spec * 100
    Kf_pass = Kf_error < 5.0

    print(f"\n1. Force Constant:")
    print(f"   Specified: {Kf_spec:.2f} N/A")
    print(f"   Measured: {Kf_meas:.2f} N/A")
    print(f"   Error: {Kf_error:.1f}%")
    print(f"   Status: {'✓ PASS' if Kf_pass else '✗ FAIL'} (tolerance: ±5%)")

    # Step response
    settling = results['step_response']['settling_time']
    overshoot = results['step_response']['overshoot']
    print(f"\n2. Step Response:")
    print(f"   Settling Time: {settling * 1000:.1f} ms" if settling else "   Settling Time: N/A")
    print(f"   Overshoot: {overshoot:.1f}%")
    print(f"   Status: {'✓ ACCEPTABLE' if overshoot < 20 else '⚠ HIGH OVERSHOOT'}")

    # Thermal
    max_temp = results['thermal']['max_temp_coils']
    thermal_safe = max_temp < 155.0
    print(f"\n3. Thermal Performance:")
    print(f"   Max Coil Temp @ 12.5A continuous: {max_temp:.1f} °C")
    print(f"   Status: {'✓ SAFE' if thermal_safe else '⚠ OVER TEMP'}")

    # Cogging
    max_cogging = results['cogging']['max_cogging']
    cogging_acceptable = max_cogging < 20.0
    print(f"\n4. Cogging Force:")
    print(f"   Max Cogging: {max_cogging:.2f} N")
    print(f"   Status: {'✓ ACCEPTABLE' if cogging_acceptable else '⚠ HIGH'} (target: <20 N)")

    # Efficiency
    peak_eff = results['efficiency']['peak_efficiency']
    print(f"\n5. Efficiency:")
    print(f"   Peak Efficiency: {peak_eff:.1f}%")
    print(f"   Status: ✓ MEASURED")

    print("\n" + "=" * 70)

    return results


if __name__ == '__main__':
    # Run validation tests
    results = run_validation_tests()

    # Generate plots
    print("\nGenerating plots...")

    # Plot step response
    if 'step_response' in results and 'history' in results['step_response']:
        sim = LinearBLDCSimulation()
        from visualization.dashboard import SimulationDashboard

        dashboard = SimulationDashboard()
        fig = dashboard.plot_control_performance(results['step_response']['history'])
        plt.savefig('step_response.png', dpi=150, bbox_inches='tight')
        print("  Saved: step_response.png")

    print("\nValidation complete!")
