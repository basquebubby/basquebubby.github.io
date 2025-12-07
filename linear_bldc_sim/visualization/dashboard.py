"""
Visualization Dashboard for Linear BLDC Simulation

Creates comprehensive plots of simulation results
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from typing import Dict


class SimulationDashboard:
    """Creates visualization dashboard for simulation results"""

    def __init__(self, figsize=(16, 12)):
        """Initialize dashboard

        Args:
            figsize: Figure size (width, height) in inches
        """
        self.figsize = figsize

    def plot_system_state(self, history: Dict):
        """Plot system state dashboard

        Args:
            history: Simulation history dictionary
        """
        fig = plt.figure(figsize=self.figsize)
        gs = GridSpec(4, 2, figure=fig, hspace=0.3, wspace=0.3)

        time = history['time']

        # 1. Position
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(time, history['position'], 'b-', linewidth=2, label='Actual')
        if 'position_setpoint' in history:
            ax1.plot(time, history['position_setpoint'], 'r--', linewidth=1, label='Setpoint')
        ax1.set_ylabel('Position (mm)', fontsize=11, fontweight='bold')
        ax1.set_xlabel('Time (s)', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.legend(fontsize=9)
        ax1.set_title('Position vs Time', fontsize=12, fontweight='bold')

        # 2. Velocity
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(time, history['velocity'], 'g-', linewidth=2)
        ax2.set_ylabel('Velocity (m/s)', fontsize=11, fontweight='bold')
        ax2.set_xlabel('Time (s)', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Velocity vs Time', fontsize=12, fontweight='bold')

        # 3. Force
        ax3 = fig.add_subplot(gs[1, 0])
        ax3.plot(time, history['force_em'], 'b-', linewidth=2, label='EM Force')
        ax3.plot(time, history['force_total'], 'r--', linewidth=1, label='Total (w/ cogging)')
        ax3.set_ylabel('Force (N)', fontsize=11, fontweight='bold')
        ax3.set_xlabel('Time (s)', fontsize=10)
        ax3.grid(True, alpha=0.3)
        ax3.legend(fontsize=9)
        ax3.set_title('Force vs Time', fontsize=12, fontweight='bold')

        # 4. Phase Currents
        ax4 = fig.add_subplot(gs[1, 1])
        ax4.plot(time, history['current_A'], 'r-', linewidth=1, alpha=0.7, label='Phase A')
        ax4.plot(time, history['current_B'], 'g-', linewidth=1, alpha=0.7, label='Phase B')
        ax4.plot(time, history['current_C'], 'b-', linewidth=1, alpha=0.7, label='Phase C')
        ax4.set_ylabel('Current (A)', fontsize=11, fontweight='bold')
        ax4.set_xlabel('Time (s)', fontsize=10)
        ax4.grid(True, alpha=0.3)
        ax4.legend(fontsize=9)
        ax4.set_title('Phase Currents vs Time', fontsize=12, fontweight='bold')

        # 5. Temperatures
        ax5 = fig.add_subplot(gs[2, 0])
        ax5.plot(time, history['temp_coils'], 'r-', linewidth=2, label='Coils')
        ax5.plot(time, history['temp_magnets'], 'b-', linewidth=2, label='Magnets')
        ax5.plot(time, history['temp_housing'], 'g-', linewidth=2, label='Housing')
        ax5.axhline(y=155, color='r', linestyle='--', linewidth=1, alpha=0.5, label='Coil Limit')
        ax5.axhline(y=80, color='b', linestyle='--', linewidth=1, alpha=0.5, label='Magnet Limit')
        ax5.set_ylabel('Temperature (°C)', fontsize=11, fontweight='bold')
        ax5.set_xlabel('Time (s)', fontsize=10)
        ax5.grid(True, alpha=0.3)
        ax5.legend(fontsize=9)
        ax5.set_title('Thermal State', fontsize=12, fontweight='bold')

        # 6. Power Loss
        ax6 = fig.add_subplot(gs[2, 1])
        ax6.plot(time, history['power_loss'], 'r-', linewidth=2)
        ax6.set_ylabel('Power Loss (W)', fontsize=11, fontweight='bold')
        ax6.set_xlabel('Time (s)', fontsize=10)
        ax6.grid(True, alpha=0.3)
        ax6.set_title('Total Power Loss', fontsize=12, fontweight='bold')

        # 7. Position Error (if available)
        if 'position_error' in history:
            ax7 = fig.add_subplot(gs[3, 0])
            ax7.plot(time, history['position_error'], 'r-', linewidth=2)
            ax7.set_ylabel('Position Error (mm)', fontsize=11, fontweight='bold')
            ax7.set_xlabel('Time (s)', fontsize=10)
            ax7.grid(True, alpha=0.3)
            ax7.set_title('Position Tracking Error', fontsize=12, fontweight='bold')

        # 8. Acceleration
        ax8 = fig.add_subplot(gs[3, 1])
        ax8.plot(time, history['acceleration'], 'purple', linewidth=2)
        ax8.set_ylabel('Acceleration (m/s²)', fontsize=11, fontweight='bold')
        ax8.set_xlabel('Time (s)', fontsize=10)
        ax8.grid(True, alpha=0.3)
        ax8.set_title('Acceleration vs Time', fontsize=12, fontweight='bold')

        plt.suptitle('Linear BLDC Actuator - System State Dashboard', fontsize=14, fontweight='bold')

        return fig

    def plot_electromagnetic(self, em_model, position_range=None):
        """Plot electromagnetic characteristics

        Args:
            em_model: Electromagnetic model instance
            position_range: Range of positions to evaluate (meters)
        """
        if position_range is None:
            position_range = np.linspace(0, em_model.stroke, 100)

        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        # 1. Cogging force profile
        cogging_forces = [em_model.get_cogging_force(pos) for pos in position_range]
        axes[0, 0].plot(position_range * 1000, cogging_forces, 'b-', linewidth=2)
        axes[0, 0].set_xlabel('Position (mm)', fontsize=10)
        axes[0, 0].set_ylabel('Cogging Force (N)', fontsize=10)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].set_title('Cogging Force vs Position', fontsize=11, fontweight='bold')

        # 2. Force vs current at middle position
        mid_position = em_model.stroke / 2
        current_range = np.linspace(-30, 30, 100)
        forces = em_model.get_force_vs_current_curve(mid_position, current_range)
        axes[0, 1].plot(current_range, forces, 'r-', linewidth=2)
        axes[0, 1].axhline(y=365, color='g', linestyle='--', label='Continuous (365 N)')
        axes[0, 1].axhline(y=876, color='orange', linestyle='--', label='Peak (876 N)')
        axes[0, 1].set_xlabel('Current (A)', fontsize=10)
        axes[0, 1].set_ylabel('Force (N)', fontsize=10)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].legend(fontsize=9)
        axes[0, 1].set_title('Force vs Current (at mid-stroke)', fontsize=11, fontweight='bold')

        # 3. Magnetic field distribution
        z_positions, flux_densities = em_model.get_field_distribution(mid_position, num_points=200)
        axes[1, 0].plot(z_positions * 1000, flux_densities, 'b-', linewidth=2)
        axes[1, 0].axhline(y=0, color='k', linestyle='-', linewidth=0.5)
        axes[1, 0].set_xlabel('Axial Position (mm)', fontsize=10)
        axes[1, 0].set_ylabel('Flux Density (T)', fontsize=10)
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_title('Magnetic Field Distribution', fontsize=11, fontweight='bold')

        # 4. Commutation signals
        positions = np.linspace(0, em_model.pole_pitch * 2, 200)  # Two pole pitches
        signals_A = []
        signals_B = []
        signals_C = []
        for pos in positions:
            signals = em_model.get_commutation_signals(pos)
            signals_A.append(signals[0])
            signals_B.append(signals[1])
            signals_C.append(signals[2])

        axes[1, 1].plot(positions * 1000, signals_A, 'r-', linewidth=2, label='Phase A')
        axes[1, 1].plot(positions * 1000, signals_B, 'g-', linewidth=2, label='Phase B')
        axes[1, 1].plot(positions * 1000, signals_C, 'b-', linewidth=2, label='Phase C')
        axes[1, 1].set_xlabel('Position (mm)', fontsize=10)
        axes[1, 1].set_ylabel('Commutation Signal', fontsize=10)
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].legend(fontsize=9)
        axes[1, 1].set_title('Commutation Signals (2 pole pitches)', fontsize=11, fontweight='bold')

        plt.suptitle('Electromagnetic Characteristics', fontsize=14, fontweight='bold')
        plt.tight_layout()

        return fig

    def plot_thermal_analysis(self, history: Dict):
        """Plot detailed thermal analysis

        Args:
            history: Simulation history dictionary
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        time = history['time']

        # 1. All temperatures
        axes[0, 0].plot(time, history['temp_coils'], 'r-', linewidth=2, label='Coils')
        axes[0, 0].plot(time, history['temp_magnets'], 'b-', linewidth=2, label='Magnets')
        axes[0, 0].plot(time, history['temp_housing'], 'g-', linewidth=2, label='Housing')
        axes[0, 0].axhline(y=155, color='r', linestyle='--', alpha=0.5)
        axes[0, 0].axhline(y=80, color='b', linestyle='--', alpha=0.5)
        axes[0, 0].set_xlabel('Time (s)', fontsize=10)
        axes[0, 0].set_ylabel('Temperature (°C)', fontsize=10)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend(fontsize=9)
        axes[0, 0].set_title('Temperature Rise', fontsize=11, fontweight='bold')

        # 2. Power loss breakdown (would need to log individual losses)
        axes[0, 1].plot(time, history['power_loss'], 'r-', linewidth=2)
        axes[0, 1].set_xlabel('Time (s)', fontsize=10)
        axes[0, 1].set_ylabel('Total Power Loss (W)', fontsize=10)
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].set_title('Total Heat Generation', fontsize=11, fontweight='bold')

        # 3. Temperature vs current (scatter plot)
        axes[1, 0].scatter(history['current_total'], history['temp_coils'],
                          alpha=0.3, c=time, cmap='viridis', s=10)
        axes[1, 0].set_xlabel('Current (A)', fontsize=10)
        axes[1, 0].set_ylabel('Coil Temperature (°C)', fontsize=10)
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].set_title('Coil Temp vs Current', fontsize=11, fontweight='bold')
        cbar = plt.colorbar(axes[1, 0].collections[0], ax=axes[1, 0])
        cbar.set_label('Time (s)', fontsize=9)

        # 4. Thermal time constant analysis
        # Find where temperature reaches 63.2% of final value
        if len(history['temp_coils']) > 0:
            T_final = history['temp_coils'][-1]
            T_initial = history['temp_coils'][0]
            T_63 = T_initial + 0.632 * (T_final - T_initial)

            axes[1, 1].plot(time, history['temp_coils'], 'r-', linewidth=2)
            axes[1, 1].axhline(y=T_63, color='b', linestyle='--', label=f'63.2% = {T_63:.1f}°C')
            axes[1, 1].set_xlabel('Time (s)', fontsize=10)
            axes[1, 1].set_ylabel('Coil Temperature (°C)', fontsize=10)
            axes[1, 1].grid(True, alpha=0.3)
            axes[1, 1].legend(fontsize=9)
            axes[1, 1].set_title('Thermal Time Constant', fontsize=11, fontweight='bold')

        plt.suptitle('Thermal Analysis', fontsize=14, fontweight='bold')
        plt.tight_layout()

        return fig

    def plot_control_performance(self, history: Dict):
        """Plot control system performance

        Args:
            history: Simulation history dictionary
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))

        time = history['time']

        # 1. Position tracking
        axes[0, 0].plot(time, history['position'], 'b-', linewidth=2, label='Actual')
        if 'position_setpoint' in history:
            axes[0, 0].plot(time, history['position_setpoint'], 'r--',
                           linewidth=1, label='Setpoint')
        axes[0, 0].set_xlabel('Time (s)', fontsize=10)
        axes[0, 0].set_ylabel('Position (mm)', fontsize=10)
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].legend(fontsize=9)
        axes[0, 0].set_title('Position Tracking', fontsize=11, fontweight='bold')

        # 2. Position error
        if 'position_error' in history:
            axes[0, 1].plot(time, history['position_error'], 'r-', linewidth=2)
            axes[0, 1].set_xlabel('Time (s)', fontsize=10)
            axes[0, 1].set_ylabel('Position Error (mm)', fontsize=10)
            axes[0, 1].grid(True, alpha=0.3)
            axes[0, 1].set_title('Tracking Error', fontsize=11, fontweight='bold')

        # 3. Control effort (current)
        axes[1, 0].plot(time, history['current_total'], 'g-', linewidth=2)
        axes[1, 0].axhline(y=12.5, color='orange', linestyle='--', label='Continuous (12.5 A)')
        axes[1, 0].axhline(y=30, color='r', linestyle='--', label='Peak (30 A)')
        axes[1, 0].set_xlabel('Time (s)', fontsize=10)
        axes[1, 0].set_ylabel('Total Current (A)', fontsize=10)
        axes[1, 0].grid(True, alpha=0.3)
        axes[1, 0].legend(fontsize=9)
        axes[1, 0].set_title('Control Effort (Current)', fontsize=11, fontweight='bold')

        # 4. Velocity
        axes[1, 1].plot(time, history['velocity'], 'purple', linewidth=2)
        axes[1, 1].set_xlabel('Time (s)', fontsize=10)
        axes[1, 1].set_ylabel('Velocity (m/s)', fontsize=10)
        axes[1, 1].grid(True, alpha=0.3)
        axes[1, 1].set_title('Velocity Profile', fontsize=11, fontweight='bold')

        plt.suptitle('Control Performance', fontsize=14, fontweight='bold')
        plt.tight_layout()

        return fig


def plot_all_dashboards(simulation, history: Dict = None):
    """Create all dashboard plots

    Args:
        simulation: Simulation instance
        history: History dictionary (uses simulation history if None)

    Returns:
        List of figures
    """
    if history is None:
        history = simulation.get_history()

    dashboard = SimulationDashboard()

    figures = []

    # System state dashboard
    print("Creating system state dashboard...")
    fig1 = dashboard.plot_system_state(history)
    figures.append(fig1)

    # Electromagnetic characteristics
    print("Creating electromagnetic plots...")
    fig2 = dashboard.plot_electromagnetic(simulation.electromagnetic)
    figures.append(fig2)

    # Thermal analysis
    print("Creating thermal analysis...")
    fig3 = dashboard.plot_thermal_analysis(history)
    figures.append(fig3)

    # Control performance
    print("Creating control performance plots...")
    fig4 = dashboard.plot_control_performance(history)
    figures.append(fig4)

    return figures
