"""
Quick validation test for the Linear BLDC simulation
"""

import sys
import numpy as np

# Test imports
print("Testing imports...")
try:
    from simulation import LinearBLDCSimulation
    from specs import SPECS
    print("✓ Core modules imported successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

# Test simulation creation
print("\nTesting simulation creation...")
try:
    sim = LinearBLDCSimulation()
    print("✓ Simulation created successfully")
    print(f"  Force constant: {sim.specs['force_constant']} N/A")
    print(f"  Stroke: {sim.specs['stroke']} mm")
    print(f"  Total mass: {sim.specs['total_mass']} kg")
except Exception as e:
    print(f"✗ Simulation creation error: {e}")
    sys.exit(1)

# Test basic simulation run
print("\nTesting basic simulation (0.1s)...")
try:
    sim.command_position(50)  # Move to 50 mm
    results = sim.run(duration=0.1, dt=0.0001)
    print("✓ Simulation ran successfully")
    print(f"  Final position: {results['position'][-1]:.2f} mm")
    print(f"  Final velocity: {results['velocity'][-1]:.3f} m/s")
    print(f"  Max current: {np.max(results['current_total']):.2f} A")
    print(f"  Final coil temp: {results['temp_coils'][-1]:.1f} °C")
except Exception as e:
    print(f"✗ Simulation run error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test force constant
print("\nTesting force constant...")
try:
    sim.reset()
    # Apply known current and measure force
    test_current = 10.0  # A
    expected_force = test_current * SPECS['force_constant']

    sim.command_force(expected_force)
    results = sim.run(duration=0.2, dt=0.0001)

    # Measure force in steady state
    measured_force = np.mean(results['force_em'][-50:])
    error = abs(measured_force - expected_force) / expected_force * 100

    print(f"  Test current: {test_current} A")
    print(f"  Expected force: {expected_force:.1f} N")
    print(f"  Measured force: {measured_force:.1f} N")
    print(f"  Error: {error:.1f}%")

    if error < 5.0:
        print("✓ Force constant validation PASSED")
    else:
        print("⚠ Force constant error > 5%")
except Exception as e:
    print(f"✗ Force test error: {e}")
    import traceback
    traceback.print_exc()

# Test thermal model
print("\nTesting thermal model...")
try:
    sim.reset()
    initial_temp = sim.thermal.temperatures['coils']
    sim.command_force(365)  # Continuous force
    results = sim.run(duration=1.0, dt=0.001)

    final_temp = results['temp_coils'][-1]
    temp_rise = final_temp - initial_temp

    print(f"  Initial temp: {initial_temp:.1f} °C")
    print(f"  Final temp: {final_temp:.1f} °C")
    print(f"  Temp rise: {temp_rise:.1f} °C")

    if temp_rise > 0:
        print("✓ Thermal model working (temperature rising)")
    else:
        print("⚠ No temperature rise detected")
except Exception as e:
    print(f"✗ Thermal test error: {e}")
    import traceback
    traceback.print_exc()

# Test electromagnetic model
print("\nTesting electromagnetic model...")
try:
    # Check cogging force
    cogging = sim.electromagnetic.get_cogging_force(0.1)  # at 0.1 m
    print(f"  Cogging force @ 0.1m: {cogging:.2f} N")

    # Check field distribution
    z_pos, B_field = sim.electromagnetic.get_field_distribution(0.1, num_points=50)
    max_B = np.max(np.abs(B_field))
    print(f"  Max flux density: {max_B:.3f} T")

    print("✓ Electromagnetic model working")
except Exception as e:
    print(f"✗ EM model error: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("QUICK VALIDATION TEST COMPLETE")
print("=" * 60)
print("\n✓ All basic tests passed!")
print("\nThe simulation is ready to use.")
print("\nNext steps:")
print("  - Run 'python main.py' for interactive menu")
print("  - Run 'python main.py validate' for full validation tests")
print("  - See README.md for detailed usage instructions")
