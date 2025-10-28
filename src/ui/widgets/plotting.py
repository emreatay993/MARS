"""
Plotting widgets for MARS (Modal Analysis Response Solver).

Contains matplotlib- and plotly-based widgets for displaying analysis results.
"""

import numpy as np
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QKeySequence, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QShortcut, QSizePolicy,
    QSplitter, QTableView, QVBoxLayout, QWidget, QHeaderView
)
from PyQt5.QtWebEngineWidgets import QWebEngineView

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.ticker import MaxNLocator

import plotly.graph_objects as go
from plotly_resampler import FigureResampler


class MatplotlibWidget(QWidget):
    """
    Widget for displaying matplotlib plots with an interactive data table.
    
    Features:
    - Matplotlib canvas with navigation toolbar
    - Interactive legend (click to hide/show traces)
    - Hover annotations for data points
    - Side-by-side data table
    - Clipboard copy support (Ctrl+C)
    - Auto-resizing splitter
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Attributes for interactivity
        self.ax = None
        self.annot = None
        self.plotted_lines = []
        self.legend_map = {}  # Used to map legend items to plot lines
        
        # Matplotlib canvas on the left
        self.figure = plt.Figure(tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.updateGeometry()
        
        # Add the Navigation Toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # Data table on the right
        self.table = QTableView(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Time [s]", "Value"])
        self.table.setModel(self.model)
        
        # Ctrl+C to copy the selected block
        copy_sc = QShortcut(QKeySequence.Copy, self.table)
        copy_sc.activated.connect(self.copy_selection)
        
        # Split view
        self.splitter = QSplitter(Qt.Horizontal, self)
        
        # Create a container for plot and toolbar
        plot_container = QWidget()
        plot_layout = QVBoxLayout(plot_container)
        plot_layout.setContentsMargins(0, 0, 0, 0)
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        self.splitter.addWidget(plot_container)
        self.splitter.addWidget(self.table)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
        
        # Connect events
        self.canvas.mpl_connect("motion_notify_event", self.hover)
        self.canvas.mpl_connect('pick_event', self.on_legend_pick)
    
    def showEvent(self, event):
        """Called when the widget is shown."""
        super().showEvent(event)
        QTimer.singleShot(50, self.adjust_splitter_size)
    
    def resizeEvent(self, event):
        """Called when the widget is resized."""
        super().resizeEvent(event)
        self.adjust_splitter_size()
    
    def adjust_splitter_size(self):
        """Calculates and sets optimal table width."""
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        v_scrollbar = self.table.verticalScrollBar()
        scrollbar_width = v_scrollbar.width() if v_scrollbar.isVisible() else 0
        
        required_width = (header.length() +
                         self.table.verticalHeader().width() +
                         self.table.frameWidth() * 2 +
                         scrollbar_width)
        
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        total_width = self.splitter.width()
        plot_width = max(450, total_width - required_width)
        new_table_width = total_width - plot_width
        
        self.splitter.setSizes([int(plot_width), int(new_table_width)])
    
    def hover(self, event):
        """Show annotation when hovering over a data point."""
        if not event.inaxes or self.ax is None or self.annot is None:
            return
        
        visible = self.annot.get_visible()
        
        for line in self.plotted_lines:
            cont, ind = line.contains(event)
            if cont:
                pos = line.get_xydata()[ind["ind"][0]]
                x_coord, y_coord = pos[0], pos[1]
                
                self.annot.xy = (x_coord, y_coord)
                self.annot.set_text(f"Time: {x_coord:.4f}\\nValue: {y_coord:.4f}")
                
                if not visible:
                    self.annot.set_visible(True)
                    self.canvas.draw_idle()
                return
        
        if visible:
            self.annot.set_visible(False)
            self.canvas.draw_idle()
    
    def on_legend_pick(self, event):
        """Toggle line visibility when legend is clicked."""
        artist = event.artist
        if artist in self.legend_map:
            original_line = self.legend_map[artist]
            is_visible = not original_line.get_visible()
            original_line.set_visible(is_visible)
            
            for leg_artist, line in self.legend_map.items():
                if line == original_line:
                    leg_artist.set_alpha(1.0 if is_visible else 0.2)
            
            # Rescale Y-axis to fit visible data
            min_y, max_y = np.inf, -np.inf
            any_line_visible = False
            for line in self.plotted_lines:
                if line.get_visible():
                    any_line_visible = True
                    y_data = line.get_ydata()
                    if len(y_data) > 0:
                        min_y = min(min_y, np.min(y_data))
                        max_y = max(max_y, np.max(y_data))
            
            if any_line_visible and self.ax:
                if np.isclose(min_y, max_y):
                    margin = 1.0
                    self.ax.set_ylim(min_y - margin, max_y + margin)
                else:
                    margin = (max_y - min_y) * 0.05
                    self.ax.set_ylim(min_y - margin, max_y + margin)
            
            self.canvas.draw()
    
    def update_plot(self, x, y, node_id=None,
                   is_max_principal_stress=False,
                   is_min_principal_stress=False,
                   is_von_mises=False,
                   is_deformation=False,
                   is_velocity=False,
                   is_acceleration=False,
                   plasticity_overlay=None):
        """Update the plot and table with new data."""
        # Reset state
        self.figure.clear()
        self.plotted_lines.clear()
        self.legend_map.clear()
        
        self.ax = self.figure.add_subplot(1, 1, 1)
        
        # Define plotting styles
        styles = {
            'Magnitude': {'color': 'black', 'linestyle': '-', 'linewidth': 2},
            'X': {'color': 'red', 'linestyle': '--', 'linewidth': 1},
            'Y': {'color': 'green', 'linestyle': '--', 'linewidth': 1},
            'Z': {'color': 'blue', 'linestyle': '--', 'linewidth': 1},
        }
        
        self.model.clear()
        textstr = ""
        
        # Handle dict data (multi-component)
        if isinstance(y, dict):
            if is_velocity:
                prefix, units = "Velocity", "(mm/s)"
            elif is_acceleration:
                prefix, units = "Acceleration", "(mm/s²)"
            else:
                prefix, units = "Deformation", "(mm)"
            
            self.ax.set_title(f"{prefix} (Node ID: {node_id})", fontsize=8)
            self.ax.set_ylabel(f"{prefix} {units}", fontsize=8)
            self.model.setHorizontalHeaderLabels(
                ["Time [s]", f"Mag {units}", f"X {units}", f"Y {units}", f"Z {units}"])
            
            for component, data in y.items():
                style = styles.get(component, {})
                line, = self.ax.plot(x, data, label=f'{prefix} ({component})', **style)
                self.plotted_lines.append(line)
            
            for i in range(len(x)):
                items = [
                    QStandardItem(f"{x[i]:.5f}"),
                    QStandardItem(f"{y['Magnitude'][i]:.5f}"),
                    QStandardItem(f"{y['X'][i]:.5f}"),
                    QStandardItem(f"{y['Y'][i]:.5f}"),
                    QStandardItem(f"{y['Z'][i]:.5f}")
                ]
                self.model.appendRow(items)
            
            max_y_value = np.max(y['Magnitude'])
            time_of_max = x[np.argmax(y['Magnitude'])]
            textstr = f'Max Magnitude: {max_y_value:.4f}\nTime of Max: {time_of_max:.5f} s'
        
        # Handle array data (single component)
        else:
            if is_min_principal_stress:
                self.model.setHorizontalHeaderLabels(["Time [s]", r'$\sigma_3$ [MPa]'])
                for xi, yi in zip(x, y):
                    self.model.appendRow([QStandardItem(f"{xi:.5f}"), QStandardItem(f"{yi:.5f}")])

                line, = self.ax.plot(x, y, label=r'$\sigma_3$', color='green')
                self.plotted_lines.append(line)
                self.ax.set_title(f"Min Principal Stress (Node ID: {node_id})" if node_id else "Min Principal Stress", fontsize=8)
                self.ax.set_ylabel(r'$\sigma_3$ [MPa]', fontsize=8)
                min_y_value = np.min(y)
                time_of_min = x[np.argmin(y)]
                textstr = f'Min Magnitude: {min_y_value:.4f}\nTime of Min: {time_of_min:.5f} s'
            else:
                title, label, color = "Stress", "Value", 'blue'
                if is_max_principal_stress:
                    title, label, color = "Max Principal Stress", r'$\sigma_1$', 'red'
                elif is_von_mises:
                    title, label, color = "Von Mises Stress", r'$\sigma_{VM}$', 'blue'
                
                headers = ["Time [s]", f"{label} [MPa]"]
                if plasticity_overlay and 'corrected_vm' in plasticity_overlay:
                    corrected = np.asarray(plasticity_overlay['corrected_vm'], dtype=float)
                    strain = np.asarray(plasticity_overlay.get('plastic_strain', []), dtype=float)

                    elastic_line, = self.ax.plot(x, y, label=f"{label} (Elastic)", color=color)
                    corrected_line, = self.ax.plot(x, corrected, label=f"{label} (Corrected)", color='orange')
                    self.plotted_lines.extend([elastic_line, corrected_line])

                    headers.append("Corrected [MPa]")
                    if strain.size == corrected.size:
                        headers.append("Plastic Strain")

                    self.model.setHorizontalHeaderLabels(headers)
                    for idx, xi in enumerate(x):
                        row_items = [
                            QStandardItem(f"{xi:.5f}"),
                            QStandardItem(f"{y[idx]:.5f}"),
                            QStandardItem(f"{corrected[idx]:.5f}")
                        ]
                        if strain.size == corrected.size:
                            row_items.append(QStandardItem(f"{strain[idx]:.6e}"))
                        self.model.appendRow(row_items)

                    if corrected.size > 0 and np.any(np.isfinite(corrected)):
                        max_corr = np.nanmax(corrected)
                        time_of_max = x[np.nanargmax(corrected)]
                        textstr = f'Max Corrected: {max_corr:.4f}\nTime of Max: {time_of_max:.5f} s'
                else:
                    line, = self.ax.plot(x, y, label=label, color=color)
                    self.plotted_lines.append(line)
                    self.model.setHorizontalHeaderLabels(headers)
                    for xi, yi in zip(x, y):
                        self.model.appendRow([QStandardItem(f"{xi:.5f}"), QStandardItem(f"{yi:.5f}")])

                    if len(y) > 0 and np.any(y):
                        max_y_value = np.max(y)
                        time_of_max = x[np.argmax(y)]
                        textstr = f'Max Magnitude: {max_y_value:.4f}\nTime of Max: {time_of_max:.5f} s'

                self.ax.set_title(f"{title} (Node ID: {node_id})" if node_id else title, fontsize=8)
                self.ax.set_ylabel(f'{label} [MPa]', fontsize=8)

                # Optional diagnostics overlay (Δεp, εp) on secondary axis
                if plasticity_overlay and plasticity_overlay.get('show_diagnostics'):
                    eps = np.asarray(plasticity_overlay.get('plastic_strain', []), dtype=float)
                    deps = np.asarray(plasticity_overlay.get('delta_plastic_strain', []), dtype=float)
                    if eps.size == len(x) or deps.size == len(x):
                        ax2 = self.ax.twinx()
                        ax2.grid(False)
                        if eps.size == len(x):
                            line_eps, = ax2.plot(x, eps, label='εp (cumulative)', color='purple', linestyle='--', linewidth=1)
                            self.plotted_lines.append(line_eps)
                        if deps.size == len(x):
                            line_deps, = ax2.plot(x, deps, label='Δεp (per step)', color='brown', linestyle=':', linewidth=1)
                            self.plotted_lines.append(line_deps)
                        ax2.set_ylabel('Plastic Strain', fontsize=8)
        
        # Apply common styling
        self.ax.set_xlabel('Time [seconds]', fontsize=8)
        self.ax.set_xlim(np.min(x), np.max(x))
        self.ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
        self.ax.grid(True, which='both', linestyle='-', linewidth=0.5)
        self.ax.minorticks_on()
        self.ax.tick_params(axis='both', which='major', labelsize=8)
        
        # Create interactive legend
        handles, labels = self.ax.get_legend_handles_labels()
        if handles:
            leg = self.ax.legend(handles, labels, fontsize=7, loc='upper right')
            for legline, legtext, origline in zip(leg.get_lines(), leg.get_texts(), self.plotted_lines):
                legline.set_picker(True)
                legline.set_pickradius(5)
                self.legend_map[legline] = origline
                legtext.set_picker(True)
                self.legend_map[legtext] = origline
        
        # Add annotation
        if textstr:
            self.ax.text(0.05, 0.95, textstr, transform=self.ax.transAxes, fontsize=8,
                        verticalalignment='top', horizontalalignment='left',
                        bbox=dict(facecolor='white', alpha=0.5, boxstyle='round,pad=0.2'))
        
        # Finalize
        self.table.resizeColumnsToContents()
        self.canvas.draw()
        QTimer.singleShot(0, self.adjust_splitter_size)
    
    @pyqtSlot()
    def copy_selection(self):
        """Copy selected cells to clipboard as TSV."""
        sel = self.table.selectedIndexes()
        if not sel:
            return
        
        rows = sorted(idx.row() for idx in sel)
        cols = sorted(idx.column() for idx in sel)
        r0, r1 = rows[0], rows[-1]
        c0, c1 = cols[0], cols[-1]
        
        headers = [self.model.headerData(c, Qt.Horizontal) for c in range(c0, c1 + 1)]
        lines = ['\\t'.join(headers)]
        
        for r in range(r0, r1 + 1):
            row_data = []
            for c in range(c0, c1 + 1):
                text = self.model.index(r, c).data() or ""
                row_data.append(text)
            lines.append('\\t'.join(row_data))
        
        QApplication.clipboard().setText('\\n'.join(lines))
    
    def clear_plot(self):
        """Clear the plot and table."""
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.set_title("Time History (No Data)", fontsize=8)
        ax.set_xlabel('Time [seconds]', fontsize=8)
        ax.set_ylabel('Value', fontsize=8)
        ax.grid(True, which='both', linestyle='-', linewidth=0.5)
        ax.minorticks_on()
        ax.tick_params(axis='both', which='major', labelsize=8)
        self.canvas.draw()
        
        self.model.removeRows(0, self.model.rowCount())
        self.model.setHorizontalHeaderLabels(["Time [s]", "Value"])
        self.table.resizeColumnsToContents()
        QTimer.singleShot(0, self.adjust_splitter_size)


class PlotlyWidget(QWidget):
    """
    Simple widget for displaying Plotly plots in a web view.
    
    Used for displaying modal coordinates over time.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.web_view = QWebEngineView(self)
        layout = QVBoxLayout()
        layout.addWidget(self.web_view)
        self.setLayout(layout)
        
        # Store last used data for refresh
        self.last_time_values = None
        self.last_modal_coord = None
    
    def update_plot(self, time_values, modal_coord):
        """Update the plot with modal coordinate data."""
        self.last_time_values = time_values
        self.last_modal_coord = modal_coord
        
        fig = go.Figure()
        num_modes = modal_coord.shape[0]
        for i in range(num_modes):
            fig.add_trace(go.Scattergl(
                x=time_values,
                y=modal_coord[i, :],
                mode='lines',
                name=f'Mode {i + 1}',
                opacity=0.7
            ))
        
        fig.update_layout(
            xaxis_title="Time [s]",
            yaxis_title="Modal Coordinate Value",
            template="plotly_white",
            font=dict(size=7),
            margin=dict(l=40, r=40, t=10, b=0),
            legend=dict(font=dict(size=7))
        )
        
        # Wrap in FigureResampler for dynamic resampling
        resampler_fig = FigureResampler(fig, default_n_shown_samples=1000)
        
        # Display
        main_win = self.window()
        main_win.plotting_handler.load_fig_to_webview(resampler_fig, self.web_view)
    
    def clear_plot(self):
        """Clear the plot."""
        self.web_view.setHtml("")
        self.last_time_values = None
        self.last_modal_coord = None


class PlotlyMaxWidget(QWidget):
    """
    Widget for displaying Plotly plots with a data table.
    
    Features:
    - Plotly web view for interactive plots
    - Side-by-side data table
    - Clipboard copy support (Ctrl+C)
    - Auto-resizing splitter
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Plotly web view
        self.web_view = QWebEngineView(self)
        
        # Data table
        self.table = QTableView(self)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        self.model = QStandardItemModel(self)
        self.model.setHorizontalHeaderLabels(["Time [s]", "Data Value"])
        self.table.setModel(self.model)
        
        # Ctrl+C shortcut
        copy_sc = QShortcut(QKeySequence.Copy, self.table)
        copy_sc.activated.connect(self.copy_selection)
        
        # Splitter
        self.splitter = QSplitter(Qt.Horizontal, self)
        self.splitter.addWidget(self.web_view)
        self.splitter.addWidget(self.table)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        self.setLayout(layout)
    
    def showEvent(self, event):
        """Called when widget is shown."""
        super().showEvent(event)
        QTimer.singleShot(50, self.adjust_splitter_size)
    
    def resizeEvent(self, event):
        """Called when widget is resized."""
        super().resizeEvent(event)
        self.adjust_splitter_size()
    
    def adjust_splitter_size(self):
        """Calculate and set optimal table width."""
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        
        v_scrollbar = self.table.verticalScrollBar()
        scrollbar_width = v_scrollbar.width() if v_scrollbar.isVisible() else 0
        
        required_width = (header.length() +
                         self.table.verticalHeader().width() +
                         self.table.frameWidth() * 2 +
                         scrollbar_width)
        
        header.setSectionResizeMode(QHeaderView.Interactive)
        
        total_width = self.splitter.width()
        plot_width = max(450, total_width - required_width)
        
        self.splitter.setSizes([int(plot_width), int(total_width - plot_width)])
    
    def update_plot(self, time_values, traces=None):
        """
        Update plot with multiple data traces.
        
        Args:
            time_values: Array of time values.
            traces: List of dicts with 'name' and 'data' keys.
        """
        if traces is None:
            traces = []
        
        # Build figure
        fig = go.Figure()
        for trace_info in traces:
            fig.add_trace(go.Scattergl(
                x=time_values,
                y=trace_info['data'],
                mode='lines',
                name=trace_info['name']
            ))
        
        fig.update_layout(
            xaxis_title="Time [s]",
            yaxis_title="Value",
            template="plotly_white",
            font=dict(size=7),
            margin=dict(l=40, r=40, t=10, b=0),
            legend=dict(font=dict(size=7))
        )
        
        # Wrap in resampler
        resfig = FigureResampler(fig, default_n_shown_samples=50000)
        
        # Display
        main_win = self.window()
        main_win.plotting_handler.load_fig_to_webview(resfig, self.web_view)
        
        # Populate table
        headers = ["Time [s]"] + [trace['name'] for trace in traces]
        self.model.setHorizontalHeaderLabels(headers)
        self.model.removeRows(0, self.model.rowCount())
        
        for i, t in enumerate(time_values):
            row_items = [QStandardItem(f"{t:.5f}")]
            for trace in traces:
                row_items.append(QStandardItem(f"{trace['data'][i]:.6f}"))
            self.model.appendRow(row_items)
        
        # Finalize
        self.table.resizeColumnsToContents()
        QTimer.singleShot(0, self.adjust_splitter_size)
    
    @pyqtSlot()
    def copy_selection(self):
        """Copy selected cells to clipboard as TSV."""
        sel = self.table.selectedIndexes()
        if not sel:
            return
        
        rows = sorted(idx.row() for idx in sel)
        cols = sorted(idx.column() for idx in sel)
        r0, r1 = rows[0], rows[-1]
        c0, c1 = cols[0], cols[-1]
        
        headers = [self.model.headerData(c, Qt.Horizontal) for c in range(c0, c1 + 1)]
        lines = ['\\t'.join(headers)]
        
        for r in range(r0, r1 + 1):
            row_data = []
            for c in range(c0, c1 + 1):
                idx = self.model.index(r, c)
                text = idx.data() or ""
                row_data.append(text)
            lines.append('\\t'.join(row_data))
        
        QApplication.clipboard().setText('\\n'.join(lines))
    
    def clear_plot(self):
        """Clear the plot and table."""
        self.web_view.setHtml("")
        self.model.removeRows(0, self.model.rowCount())
        self.model.setHorizontalHeaderLabels(["Time [s]", "Data Value"])
