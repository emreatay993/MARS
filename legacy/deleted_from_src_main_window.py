"""
Main window for the MARS GUI.

This module provides the main application window with menu bar, navigator,
and tab widgets for solver and display functionality.
"""

import os
import subprocess
import traceback
from tempfile import NamedTemporaryFile

import numpy as np
import torch
import plotly.io as pio

from PyQt5.QtCore import Qt, QDir, QUrl
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import (
    QAction, QDockWidget, QFileDialog, QFileSystemModel,
    QMainWindow, QMenuBar, QMessageBox, QTabWidget, QTreeView
)

from ui.solver_tab import SolverTab
from ui.display_tab import DisplayTab
from ui.widgets.dialogs import AdvancedSettingsDialog
from ui.styles.style_constants import (
    MENU_BAR_STYLE, NAVIGATOR_TITLE_STYLE, TREE_VIEW_STYLE, TAB_STYLE
)
import solver.engine as solver_engine


class MainWindow(QMainWindow):
    """
    Main application window for MARS.
    
    This class manages the overall application window including menu bar,
    file navigator, and main tab widgets.
    """
    
    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        # Set window background color (matching legacy)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(230, 230, 230))  # Light gray background
        self.setPalette(palette)
        
        # State
        self.temp_files = []
        self.project_directory = None
        
        # Window configuration
        self.setWindowTitle('MARS: Modal Analysis Response Solver - v1.0.0')
        self.setGeometry(40, 40, 600, 800)
        
        # Create UI components (order matters - navigator before menu bar)
        self._create_navigator()
        self._create_menu_bar()
        self._create_tabs()
        self._connect_signals()
    
    def _create_menu_bar(self):
        """Create the menu bar with File, View, and Settings menus."""
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        # Apply menu bar styles (white background, matching legacy)
        self.menu_bar.setStyleSheet(MENU_BAR_STYLE)
        
        # File menu
        file_menu = self.menu_bar.addMenu("File")
        select_dir_action = QAction("Select Project Directory", self)
        select_dir_action.triggered.connect(self.select_project_directory)
        file_menu.addAction(select_dir_action)
        
        # View menu
        view_menu = self.menu_bar.addMenu("View")
        toggle_navigator_action = self.navigator_dock.toggleViewAction()
        toggle_navigator_action.setText("Navigator")
        view_menu.addAction(toggle_navigator_action)
        
        # Settings menu
        settings_menu = self.menu_bar.addMenu("Settings")
        advanced_settings_action = QAction("Advanced", self)
        advanced_settings_action.triggered.connect(self.open_advanced_settings)
        settings_menu.addAction(advanced_settings_action)
    
    def _create_navigator(self):
        """Create file navigator dock widget."""
        self.navigator_dock = QDockWidget("Navigator", self)
        self.navigator_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.navigator_dock.setFeatures(
            QDockWidget.DockWidgetClosable | QDockWidget.DockWidgetMovable
        )
        
        # File system model
        self.file_model = QFileSystemModel()
        self.file_model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)
        self.file_model.setNameFilters(["*.csv", "*.mcf", "*.txt"])
        self.file_model.setNameFilterDisables(False)
        
        # Tree view
        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.doubleClicked.connect(self.open_navigator_file)
        self.tree_view.setHeaderHidden(False)
        self.tree_view.setMinimumWidth(240)
        self.tree_view.setSortingEnabled(True)
        
        # Hide unwanted columns
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnWidth(0, 250)
        self.tree_view.header().setSectionResizeMode(
            0, self.tree_view.header().ResizeToContents
        )
        
        # Apply styles
        self._apply_navigator_styles()
        
        # Enable drag and drop
        self.tree_view.setDragEnabled(True)
        self.tree_view.setAcceptDrops(True)
        self.tree_view.setDropIndicatorShown(True)
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setDragDropMode(QTreeView.DragDrop)
        
        # Set widget
        self.navigator_dock.setWidget(self.tree_view)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.navigator_dock)
    
    def _apply_navigator_styles(self):
        """Apply styles to navigator components (matching legacy approach)."""
        # Apply blue navigator title and tree view styles
        self.navigator_dock.setStyleSheet(NAVIGATOR_TITLE_STYLE)
        self.tree_view.setStyleSheet(TREE_VIEW_STYLE)
    
    def _create_tabs(self):
        """Create main tab widget with solver and display tabs."""
        self.tab_widget = QTabWidget()
        # Apply tab styles (matching legacy approach)
        self.tab_widget.setStyleSheet(TAB_STYLE)
        
        # Create tabs
        self.solver_tab = SolverTab()
        self.display_tab = DisplayTab()
        self.display_tab.main_window = self
        
        self.tab_widget.addTab(self.solver_tab, "Main Window")
        self.tab_widget.addTab(self.display_tab, "Display")
        
        self.setCentralWidget(self.tab_widget)
    
    def _connect_signals(self):
        """Connect signals between tabs."""
        # Connect solver tab to display tab
        self.solver_tab.initial_data_loaded.connect(
            self.display_tab._setup_initial_view
        )
        self.solver_tab.time_point_result_ready.connect(
            self.display_tab.update_view_with_results
        )
        self.solver_tab.animation_data_ready.connect(
            self.display_tab.on_animation_data_ready
        )
        
        # Connect display tab to solver tab
        self.display_tab.node_picked_signal.connect(
            self.solver_tab.handle_node_selection
        )
        self.display_tab.time_point_update_requested.connect(
            self._handle_time_point_request
        )
        self.display_tab.animation_precomputation_requested.connect(
            self._handle_animation_request
        )
    
    def _handle_time_point_request(self, selected_time, options):
        """
        Handle time point calculation request from display tab.

        Forward the request to solver tab for computation.
        """
        self.solver_tab.request_time_point_calculation(selected_time, options)
    
    def _handle_animation_request(self, params):
        """
        Handle animation precomputation request from display tab.

        Forward the request to solver tab for computation.
        """
        self.solver_tab.request_animation_precomputation(params)
    
    def select_project_directory(self):
        """Open dialog to select project directory."""
        dir_path = QFileDialog.getExistingDirectory(
            self, "Select Project Directory"
        )
        if dir_path:
            self.project_directory = dir_path
            print(f"Project directory selected: {self.project_directory}")
            
            # Update solver tab's project directory
            self.solver_tab.project_directory = self.project_directory
            
            # Update navigator
            self.file_model.setRootPath(self.project_directory)
            self.tree_view.setRootIndex(
                self.file_model.index(self.project_directory)
            )
    
    def open_navigator_file(self, index):
        """Open file from navigator in default application."""
        if self.file_model.isDir(index):
            return
        
        file_path = self.file_model.filePath(index)
        
        try:
            subprocess.run(['cmd', '/c', 'start', '/max', '', file_path], shell=True)
        except Exception as e:
            print(f"Error opening file '{file_path}': {e}")
    
    def load_fig_to_webview(self, fig, web_view):
        """Load Plotly figure into web view widget."""
        try:
            # Handle FigureResampler if passed
            plotly_fig = fig.figure if hasattr(fig, 'figure') else fig
            
            html_content = pio.to_html(
                plotly_fig,
                full_html=True,
                include_plotlyjs=True,
                config={'responsive': True}
            )
            
            with NamedTemporaryFile(
                mode='w', suffix='.html', delete=False, encoding='utf-8'
            ) as tmp_file:
                tmp_file.write(html_content)
                file_path = tmp_file.name
                self.temp_files.append(file_path)
            
            web_view.setUrl(QUrl.fromLocalFile(file_path))
            web_view.show()
            
        except Exception as e:
            print(f"Error loading figure to webview: {e}")
            traceback.print_exc()
            error_html = (
                f"<html><body><h1>Error loading plot</h1>"
                f"<pre>{e}</pre><pre>{traceback.format_exc()}</pre></body></html>"
            )
            try:
                web_view.setHtml(error_html)
            except Exception:
                pass
    
    def open_advanced_settings(self):
        """Open advanced settings dialog."""
        dialog = AdvancedSettingsDialog(self)
        if dialog.exec_() == AdvancedSettingsDialog.Accepted:
            settings = dialog.get_settings()
            self._apply_advanced_settings(settings)
            QMessageBox.information(
                self, "Settings Applied",
                "New advanced settings have been applied.\n"
                "They will be used for the next solve operation."
            )
    
    def _apply_advanced_settings(self, settings):
        """Apply advanced settings to solver engine."""
        # Update global settings in solver engine
        solver_engine.RAM_PERCENT = settings["ram_percent"]
        solver_engine.DEFAULT_PRECISION = settings["precision"]
        solver_engine.IS_GPU_ACCELERATION_ENABLED = settings["gpu_acceleration"]
        
        # Update derived precision variables
        if solver_engine.DEFAULT_PRECISION == 'Single':
            solver_engine.NP_DTYPE = np.float32
            solver_engine.TORCH_DTYPE = torch.float32
            solver_engine.RESULT_DTYPE = 'float32'
        elif solver_engine.DEFAULT_PRECISION == 'Double':
            solver_engine.NP_DTYPE = np.float64
            solver_engine.TORCH_DTYPE = torch.float64
            solver_engine.RESULT_DTYPE = 'float64'
        
        print("\n--- Advanced settings updated ---")
        print(f"  RAM Allocation: {solver_engine.RAM_PERCENT * 100:.0f}%")
        print(f"  Solver Precision: {solver_engine.DEFAULT_PRECISION}")
        print(f"  GPU Acceleration: "
              f"{'Enabled' if solver_engine.IS_GPU_ACCELERATION_ENABLED else 'Disabled'}")
        print("---------------------------------")
    
    def closeEvent(self, event):
        """Clean up temporary files on application close."""
        self._cleanup_temp_files()
        event.accept()
    
    def _cleanup_temp_files(self):
        """Remove temporary files created during session."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Error removing temp file {temp_file}: {e}")
        self.temp_files.clear()

