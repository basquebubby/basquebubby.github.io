"""
Main entry point for Linear BLDC Simulation

Simple interface for running simulations and visualizations
"""

import numpy as np
import matplotlib.pyplot as plt
from simulation import LinearBLDCSimulation
from visualization.dashboard import plot_all_dashboards
from tests.test_scenarios import TestScenarios, run_validation_tests


def example_step_response():
    """Example: Step response test"""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Step Response (0 → 100mm)")
    print("=" * 60)

    # Create simulation
    sim = LinearBLDCSimulation()

    # Configure controller
    sim.set_position_gains(Kp=100, Ki=10, Kd=5)
    sim.command_position(100)  # Command 100 mm

    # Run simulation
    results = sim.run(duration=1.0, dt=0.0001)

    # Print status
    print("\nFinal Status:")
    print(sim.get_status())

    # Plot results
    print("\nGenerating plots...")
    figures = plot_all_dashboards(sim, results)

    plt.show()

    return sim, results


def example_force_test():
    """Example: Constant force output"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Force Test (365N continuous)")
    print("=" * 60)

    # Create simulation
    sim = LinearBLDCSimulation()

    # Apply external load
    sim.set_load_force(100)  # 100 N opposing force

    # Command continuous force
    sim.command_force(365)  # 365 N

    # Run simulation
    results = sim.run(duration=2.0, dt=0.0001)

    # Print status
    print("\nFinal Status:")
    print(sim.get_status())

    # Calculate average force
    avg_force = np.mean(results['force_em'][-100:])
    print(f"\nAverage Force (steady state): {avg_force:.1f} N")
    print(f"Error: {(avg_force - 365) / 365 * 100:.1f}%")

    # Plot results
    print("\nGenerating plots...")
    figures = plot_all_dashboards(sim, results)

    plt.show()

    return sim, results


def example_thermal_test():
    """Example: Thermal analysis under continuous load"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Thermal Analysis (12.5A continuous, 60s)")
    print("=" * 60)

    # Create simulation
    sim = LinearBLDCSimulation()

    # Set cooling (natural convection)
    sim.set_cooling(h_conv=10.0)  # W/(m²·K)

    # Command continuous current
    current = 12.5  # A
    force = current * sim.specs['force_constant']
    sim.command_force(force)

    # Run simulation
    print("\nRunning thermal simulation (this may take a moment)...")
    results = sim.run(duration=60.0, dt=0.001)

    # Print status
    print("\nFinal Status:")
    print(sim.get_status())

    # Thermal summary
    print(f"\nThermal Summary:")
    print(f"  Coil Temp: {sim.thermal.temperatures['coils']:.1f} °C")
    print(f"  Magnet Temp: {sim.thermal.temperatures['magnets']:.1f} °C")
    print(f"  Housing Temp: {sim.thermal.temperatures['housing']:.1f} °C")
    print(f"  Total Heat: {sim.thermal.get_total_heat_generation():.1f} W")

    # Plot results
    print("\nGenerating plots...")
    figures = plot_all_dashboards(sim, results)

    plt.show()

    return sim, results


def example_custom_simulation():
    """Example: Custom simulation setup"""
    print("\n" + "=" * 60)
    print("EXAMPLE: Custom Simulation")
    print("=" * 60)

    # Create simulation
    sim = LinearBLDCSimulation()

    # Custom configuration
    sim.set_position_gains(Kp=150, Ki=15, Kd=8)
    sim.set_load_force(50)  # 50 N external load
    sim.set_cooling(h_conv=25)  # Add fan cooling

    # Run a sequence of moves
    print("\nRunning sequence of moves...")

    # Move 1: Go to 50mm
    sim.command_position(50)
    sim.run(duration=0.5, dt=0.0001)

    # Move 2: Go to 150mm
    sim.command_position(150)
    sim.run(duration=0.5, dt=0.0001)

    # Move 3: Go back to 100mm
    sim.command_position(100)
    sim.run(duration=0.5, dt=0.0001)

    # Get results
    results = sim.get_history()

    # Print status
    print("\nFinal Status:")
    print(sim.get_status())

    # Plot results
    print("\nGenerating plots...")
    figures = plot_all_dashboards(sim, results)

    plt.show()

    return sim, results


def run_all_examples():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("LINEAR BLDC ACTUATOR SIMULATION - EXAMPLES")
    print("=" * 70)

    examples = [
        ("Step Response", example_step_response),
        ("Force Test", example_force_test),
        ("Thermal Test", example_thermal_test),
    ]

    for name, func in examples:
        print(f"\n\nRunning example: {name}")
        print("-" * 70)
        try:
            func()
        except KeyboardInterrupt:
            print("\nExample interrupted by user")
            break
        except Exception as e:
            print(f"\nError in example: {e}")
            import traceback
            traceback.print_exc()

        plt.close('all')  # Close figures between examples

    print("\n" + "=" * 70)
    print("All examples complete!")
    print("=" * 70)


def interactive_menu():
    """Interactive menu for running simulations"""
    while True:
        print("\n" + "=" * 70)
        print("LINEAR BLDC ACTUATOR SIMULATION")
        print("=" * 70)
        print("\nSelect an option:")
        print("  1. Step Response Test")
        print("  2. Force Output Test")
        print("  3. Thermal Analysis Test")
        print("  4. Run All Validation Tests")
        print("  5. Custom Simulation")
        print("  0. Exit")
        print("-" * 70)

        try:
            choice = input("\nEnter choice (0-5): ").strip()

            if choice == '0':
                print("\nExiting...")
                break
            elif choice == '1':
                example_step_response()
            elif choice == '2':
                example_force_test()
            elif choice == '3':
                example_thermal_test()
            elif choice == '4':
                run_validation_tests()
            elif choice == '5':
                example_custom_simulation()
            else:
                print("\nInvalid choice. Please try again.")

        except KeyboardInterrupt:
            print("\n\nInterrupted by user. Exiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1:
        # Command line mode
        cmd = sys.argv[1].lower()

        if cmd == 'step':
            example_step_response()
        elif cmd == 'force':
            example_force_test()
        elif cmd == 'thermal':
            example_thermal_test()
        elif cmd == 'validate':
            run_validation_tests()
        elif cmd == 'all':
            run_all_examples()
        else:
            print(f"Unknown command: {cmd}")
            print("\nUsage: python main.py [step|force|thermal|validate|all]")
            sys.exit(1)
    else:
        # Interactive menu
        interactive_menu()
