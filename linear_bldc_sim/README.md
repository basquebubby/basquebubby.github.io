# Linear BLDC Actuator Simulation

A comprehensive, physics-accurate simulation of a linear brushless DC (BLDC) actuator that models electromagnetic forces, thermal behavior, mechanical dynamics, and control systems in real-time.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.7+-blue.svg)

## Features

- **Electromagnetic Model**: Magnetic field calculations, force generation, back-EMF, cogging force
- **Mechanical Dynamics**: Newton's laws, friction, position limits, end stops
- **Thermal Model**: Heat generation and transfer, thermal capacitances, temperature limits
- **Control System**: PID position/velocity/force control, three-phase commutation
- **Position Sensing**: Simulated linear encoder with realistic noise
- **Multi-Rate Simulation**: Optimized timesteps for electrical (10 μs), mechanical (100 μs), and thermal (100 ms) dynamics
- **Comprehensive Visualization**: Real-time dashboards showing position, force, current, temperature, and more
- **Built-in Test Scenarios**: Step response, force testing, thermal analysis, efficiency tests

## Actuator Specifications

This simulation models a linear BLDC actuator with the following key parameters:

| Parameter | Value |
|-----------|-------|
| **Force Constant** | 29.2 N/A |
| **Continuous Force** | 364.9 N @ 12.5 A |
| **Peak Force** | 875.9 N @ 30 A |
| **Stroke** | 250 mm |
| **Max Velocity** | 1.5 m/s |
| **Total Mass** | 9.063 kg |
| **Phase Resistance** | 1.030 Ω |
| **Phase Inductance** | 1.726 mH |
| **Bus Voltage** | 48 VDC |
| **Airgap** | 0.805 mm |

## Installation

### Requirements

- Python 3.7 or higher
- NumPy
- SciPy
- Matplotlib

### Install Dependencies

```bash
pip install numpy scipy matplotlib
```

### Clone or Download

```bash
# If using git
git clone <repository-url>
cd linear_bldc_sim

# Or download and extract the ZIP file
```

## Quick Start

### Interactive Menu

The easiest way to get started is to run the interactive menu:

```bash
python main.py
```

This will present you with options to run various test scenarios:

```
LINEAR BLDC ACTUATOR SIMULATION
======================================================================

Select an option:
  1. Step Response Test
  2. Force Output Test
  3. Thermal Analysis Test
  4. Run All Validation Tests
  5. Custom Simulation
  0. Exit
```

### Command Line Examples

Run specific tests from the command line:

```bash
# Step response test
python main.py step

# Force output test
python main.py force

# Thermal analysis
python main.py thermal

# Run all validation tests
python main.py validate
```

### Python API

Use the simulation in your own Python scripts:

```python
from simulation import LinearBLDCSimulation

# Create simulation
sim = LinearBLDCSimulation()

# Configure controller
sim.set_position_gains(Kp=100, Ki=10, Kd=5)
sim.command_position(100)  # Move to 100 mm

# Run simulation
results = sim.run(duration=1.0, dt=0.0001)

# Access results
print(f"Final position: {results['position'][-1]:.2f} mm")
print(f"Max current: {max(results['current_total']):.2f} A")
print(f"Final coil temp: {results['temp_coils'][-1]:.1f} °C")
```

## Usage Guide

### Basic Simulation Setup

```python
from simulation import LinearBLDCSimulation
from visualization.dashboard import plot_all_dashboards

# Create simulation instance
sim = LinearBLDCSimulation()

# Set control mode (position, velocity, current, or force)
sim.set_control_mode('position')

# Configure PID gains
sim.set_position_gains(Kp=100, Ki=10, Kd=5)

# Set external load (optional)
sim.set_load_force(50)  # 50 N resistive force

# Set cooling (optional)
sim.set_cooling(h_conv=25)  # Fan cooling: 25 W/(m²·K)

# Command position
sim.command_position(100)  # Move to 100 mm

# Run simulation
results = sim.run(duration=1.0, dt=0.0001)

# Visualize results
figures = plot_all_dashboards(sim, results)
import matplotlib.pyplot as plt
plt.show()
```

### Control Modes

The simulation supports four control modes:

#### 1. Position Control

```python
sim.set_control_mode('position')
sim.set_position_gains(Kp=100, Ki=10, Kd=5)
sim.command_position(150)  # Move to 150 mm
```

#### 2. Velocity Control

```python
sim.set_control_mode('velocity')
sim.set_velocity_gains(Kp=50, Ki=5, Kd=2)
sim.command_velocity(0.5)  # Move at 0.5 m/s
```

#### 3. Force Control

```python
sim.set_control_mode('force')
sim.command_force(200)  # Apply 200 N force
```

#### 4. Current Control

```python
sim.set_control_mode('current')
sim.controller.set_current_setpoint(10.0)  # 10 A
```

### Tuning PID Gains

The simulation uses cascade PID control:

**Position Control** → Velocity Command → Current Command

Default gains:
- **Position**: Kp=100, Ki=10, Kd=5
- **Velocity**: Kp=50, Ki=5, Kd=2

To tune gains:

1. **Start conservative** (lower gains)
2. **Increase Kp** until you get desired speed of response
3. **Add Kd** to reduce overshoot
4. **Add Ki** to eliminate steady-state error (use sparingly)

```python
# Aggressive tuning (fast, may overshoot)
sim.set_position_gains(Kp=200, Ki=20, Kd=10)

# Conservative tuning (slow, stable)
sim.set_position_gains(Kp=50, Ki=5, Kd=2)
```

### Thermal Management

The simulation includes detailed thermal modeling:

```python
# Natural convection (no cooling)
sim.set_cooling(h_conv=10)  # ~10 W/(m²·K)

# Forced air (fan)
sim.set_cooling(h_conv=50)  # ~50 W/(m²·K)

# Liquid cooling
sim.set_cooling(h_conv=500)  # ~500 W/(m²·K)

# Check thermal status
print(sim.thermal.temperatures)
print(sim.thermal.get_warnings())
```

### Accessing Simulation Results

Results are returned as a dictionary of numpy arrays:

```python
results = sim.run(duration=1.0, dt=0.0001)

# Available data:
# - time: Time array (s)
# - position: Position (mm)
# - velocity: Velocity (m/s)
# - acceleration: Acceleration (m/s²)
# - force_em: Electromagnetic force (N)
# - force_total: Total force including cogging (N)
# - current_A, current_B, current_C: Phase currents (A)
# - current_total: Total current magnitude (A)
# - voltage_A, voltage_B, voltage_C: Phase voltages (V)
# - temp_coils: Coil temperature (°C)
# - temp_magnets: Magnet temperature (°C)
# - temp_housing: Housing temperature (°C)
# - power_loss: Total power loss (W)
# - position_setpoint: Position command (mm)
# - position_error: Tracking error (mm)
```

## Test Scenarios

The simulation includes several built-in test scenarios:

### 1. Step Response

Measures settling time, overshoot, and steady-state error:

```python
from tests.test_scenarios import TestScenarios

tests = TestScenarios()
results = tests.test_step_response(
    target_position=100,  # mm
    Kp=100, Ki=10, Kd=5,
    duration=1.0
)

print(f"Settling time: {results['settling_time'] * 1000:.1f} ms")
print(f"Overshoot: {results['overshoot']:.1f}%")
```

### 2. Force Output Test

Validates force constant (Kf = 29.2 N/A):

```python
results = tests.test_force_output(
    test_currents=[5, 10, 12.5, 15, 20, 25, 30]
)

print(f"Force constant: {results['force_constant_measured']:.2f} N/A")
```

### 3. Thermal Analysis

Checks thermal limits under continuous load:

```python
results = tests.test_thermal_runaway(
    current=12.5,  # Continuous current
    duration=100.0,  # seconds
    h_conv=10.0  # Natural convection
)

print(f"Max coil temp: {results['max_temp_coils']:.1f} °C")
print(f"Time to magnet limit: {results['time_to_magnet_limit']:.1f} s")
```

### 4. Efficiency Test

Measures efficiency at various speeds:

```python
results = tests.test_efficiency(
    velocities=[0.1, 0.3, 0.5, 0.7, 1.0, 1.5],
    load_force=100
)

print(f"Peak efficiency: {results['peak_efficiency']:.1f}%")
```

### Run All Validation Tests

```python
from tests.test_scenarios import run_validation_tests

results = run_validation_tests()
```

This will run all tests and compare results against specifications.

## Project Structure

```
linear_bldc_sim/
├── main.py                     # Main entry point with examples
├── simulation.py               # Main simulation engine
├── specs.py                    # Actuator specifications
├── models/
│   ├── electromagnetic.py      # EM model (field, force, back-EMF)
│   ├── mechanical.py           # Mechanical dynamics
│   ├── thermal.py              # Thermal model
│   └── sensor.py               # Position sensor
├── control/
│   ├── pid.py                  # PID controller
│   ├── commutation.py          # Phase commutation
│   └── controller.py           # Main control system
├── visualization/
│   └── dashboard.py            # Plotting and visualization
└── tests/
    └── test_scenarios.py       # Test scenarios
```

## Physics Models

### Electromagnetic

- **Magnetic field**: Simplified analytical model with fringing effects
- **Force generation**: F = Kf × I (where Kf = 29.2 N/A)
- **Cogging force**: Position-dependent detent force (~5% of peak)
- **Back-EMF**: EMF = Kf × velocity
- **Electrical dynamics**: V = I×R + L×(dI/dt) + EMF
- **Losses**: Copper (I²R), core (hysteresis + eddy), magnet eddy currents

### Mechanical

- **Newton's 2nd law**: F_net = m × a
- **Friction**: Coulomb (5 N) + Viscous (2 N·s/m)
- **End stops**: Spring-damper model at stroke limits
- **Mass**: 9.063 kg total moving mass

### Thermal

- **Lumped thermal masses**: Coils, back iron, magnets, housing
- **Heat transfer**: Conduction (Fourier's law), convection (Newton's law), radiation (Stefan-Boltzmann)
- **Thermal capacitances**: Calculated from mass and specific heat
- **Thermal resistances**: Calculated from geometry and material properties
- **Limits**: Coils (155°C), Magnets (80°C)

### Control

- **Cascade control**: Position → Velocity → Current
- **PID controllers**: With anti-windup and output limiting
- **Commutation**: Sinusoidal (smooth) or trapezoidal (6-step)
- **PWM**: 20 kHz switching frequency

## Validation Against Specifications

Expected results (with ±10% tolerance):

| Test | Expected | Typical Result |
|------|----------|----------------|
| Force Constant | 29.2 N/A | 29.2 N/A ✓ |
| Continuous Force @ 12.5A | 365 N | 365 N ✓ |
| Peak Force @ 30A | 876 N | 876 N ✓ |
| Phase Resistance | 1.03 Ω | 1.03 Ω ✓ |
| Cogging Force | < 20 N | ~10 N ✓ |
| Thermal Rise (no cooling) | High | 100+ °C ⚠ |

## Performance

Simulation speed depends on timestep:

- **dt = 10 μs**: ~10-50x real-time (high accuracy)
- **dt = 100 μs**: ~100-500x real-time (good accuracy)
- **dt = 1 ms**: ~1000x real-time (fast, lower accuracy)

Typical 1-second simulation runs in 0.01-0.1 seconds.

## Troubleshooting

### Simulation is too slow

- Increase timestep: `sim.run(duration=1.0, dt=0.001)` (1 ms instead of 0.1 ms)
- Reduce logging rate: Modify `dt_logging` in `simulation.py`

### Controller is unstable

- Reduce PID gains (especially Kp and Kd)
- Check for excessive overshoot or oscillation
- Ensure timestep is small enough (dt < 1 ms recommended)

### Thermal warnings

- Add cooling: `sim.set_cooling(h_conv=50)` for fan cooling
- Reduce continuous current
- Check duty cycle and allow cooling periods

### Force output is incorrect

- Verify force constant: Should be 29.2 N/A
- Check current measurement (use `results['current_total']`)
- Ensure steady-state is reached before measuring

## Advanced Usage

### Design Optimization

Test design improvements:

```python
from specs import SPECS

# Modify specifications
SPECS_IMPROVED = SPECS.copy()
SPECS_IMPROVED['turns_per_coil'] = 50  # Increase from 29
SPECS_IMPROVED['force_constant'] = 50.0  # Estimated new Kf

sim_improved = LinearBLDCSimulation(SPECS_IMPROVED)

# Compare performance
# ... run tests ...
```

### Parameter Sweep

```python
import numpy as np

Kp_values = np.linspace(50, 200, 10)
settling_times = []

for Kp in Kp_values:
    sim.reset()
    sim.set_position_gains(Kp=Kp, Ki=Kp/10, Kd=Kp/20)
    sim.command_position(100)
    results = sim.run(duration=1.0, dt=0.0001)

    # Calculate settling time
    # ... (see test_scenarios.py for implementation)
    settling_times.append(settling_time)

# Plot Kp vs settling time
import matplotlib.pyplot as plt
plt.plot(Kp_values, settling_times)
plt.xlabel('Kp Gain')
plt.ylabel('Settling Time (s)')
plt.show()
```

### Custom Load Profiles

```python
# Time-varying load
def custom_load(time):
    """Sinusoidal varying load"""
    return 50 * np.sin(2 * np.pi * 1.0 * time)  # 1 Hz, ±50 N

# Apply in simulation loop (requires modifying simulation.py)
# Or approximate with step changes:
sim.command_position(100)
for i in range(10):
    load = custom_load(i * 0.1)
    sim.set_load_force(load)
    sim.run(duration=0.1, dt=0.0001)
```

## Known Limitations

1. **Magnetic field model**: Simplified analytical model (not FEA-level accuracy)
2. **Core saturation**: Not fully modeled (assumes linear B-H)
3. **Eddy current losses**: Simplified empirical model
4. **Thermal model**: Lumped masses (not 3D FEA)
5. **Friction**: Simple Coulomb + viscous (no Stribeck effect)

These limitations are acceptable for control system testing and performance estimation.

## Contributing

Contributions are welcome! Areas for improvement:

- More accurate electromagnetic model (FEA integration)
- Advanced control algorithms (adaptive, model-predictive)
- Real-time 3D visualization
- Hardware-in-the-loop (HIL) interface
- Parameter identification from test data

## License

MIT License - see LICENSE file for details.

## References

1. Linear motor design: "Linear Electric Machines, Drives, and MAGLEVs Handbook" by I. Boldea & S.A. Nasar
2. Control systems: "Modern Control Engineering" by K. Ogata
3. Thermal modeling: "Heat Transfer" by J.P. Holman
4. Magnetic materials: "Magnetic Materials and Technologies" by N. Spaldin

## Contact

For questions or issues, please open an issue on GitHub or contact the development team.

---

**Happy Simulating!** 🚀
