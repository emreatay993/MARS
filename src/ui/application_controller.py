"""
Main window for the MSUP Smart Solver application.

This module provides the main application window with menu bar, navigator,
and tab widgets for solver and display functionality.
"""

from PyQt5.QtCore import Qt, QDir
from PyQt5.QtWidgets import (
    QAction, QDockWidget, QFileSystemModel,
    QMainWindow, QMenuBar, QMessageBox, QTabWidget, QTreeView
)

from ui.solver_tab import SolverTab
from ui.display_tab import DisplayTab
from ui.widgets.dialogs import AdvancedSettingsDialog
from ui.handlers.plotting_handler import PlottingHandler
from ui.handlers.settings_handler import SettingsHandler
from ui.handlers.navigator_handler import NavigatorHandler


class ApplicationController(QMainWindow):
    """
    Main application controller for MSUP Smart Solver.

    This class serves as the central coordinator for the entire application,
    managing tabs, signal connections between components, and application-level
    state and navigation.
    """
    
    def __init__(self):
        """Initialize the application controller."""
        super().__init__()

        # Handlers
        self.plotting_handler = PlottingHandler()

        # Window configuration
        self.setWindowTitle('MSUP Smart Solver - v2.0.0 (Modular)')
        self.setGeometry(40, 40, 600, 800)
        
        # Create UI components (order matters - navigator before menu bar)
        self._create_tabs()
        self._create_navigator()
        self._create_menu_bar()
        self._connect_signals()
    
    def _create_menu_bar(self):
        """Create the menu bar with File, View, and Settings menus."""
        menu_bar_style = """
            QMenuBar {
                background-color: #ffffff;
                color: #000000;
                padding: 2px;
                font-family: Arial;
                font-size: 12px;
            }
            QMenuBar::item {
                background-color: #ffffff;
                color: #000000;
                padding: 2px 5px;
                margin: 0px;
            }
            QMenuBar::item:selected {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
            QMenu {
                background-color: #ffffff;
                color: #000000;
                padding: 2px;
                border: 1px solid #d0d0d0;
            }
            QMenu::item {
                background-color: transparent;
                padding: 2px 10px;
            }
            QMenu::item:selected {
                background-color: #e0e0e0;
                border-radius: 2px;
            }
        """
        
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.menu_bar.setStyleSheet(menu_bar_style)
        
        # File menu
        file_menu = self.menu_bar.addMenu("File")
        select_dir_action = QAction("Select Project Directory", self)
        select_dir_action.triggered.connect(
            lambda: self.navigator_handler.select_project_directory(self)
        )
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

        # Create handler and connect the signal to the handler
        self.navigator_handler = NavigatorHandler(self.file_model, self.tree_view, self.solver_tab)
        self.tree_view.doubleClicked.connect(self.navigator_handler.open_navigator_file)
    
    def _apply_navigator_styles(self):
        """Apply styles to navigator components."""
        navigator_title_style = """
            QDockWidget::title {
                background-color: #e7f0fd;
                color: black;
                font-weight: bold;
                font-size: 9px;
                padding-top: 2px;
                padding-bottom: 2px;
                padding-left: 8px;
                padding-right: 8px;
                border-bottom: 2px solid #5b9bd5;
            }
        """
        
        tree_view_style = """
            QTreeView {
                font-size: 7.5pt;
                background-color: #ffffff;
                alternate-background-color: #f5f5f5;
                border: none;
            }
            QTreeView::item:hover {
                background-color: #d0e4ff;
            }
            QTreeView::item:selected {
                background-color: #5b9bd5;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #e7f0fd;
                padding: 3px;
                border: none;
                font-weight: bold;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 8px;
            }
            QScrollBar::handle:vertical {
                background: #5b9bd5;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """
        
        self.navigator_dock.setStyleSheet(navigator_title_style)
        self.tree_view.setStyleSheet(tree_view_style)
    
    def _create_tabs(self):
        """Create main tab widget with solver and display tabs."""
        tab_style = """
            QTabBar::tab {
                background-color: #d6e4f5;
                color: #666666;
                border: 1px solid #5b9bd5;
                padding: 3px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                margin: 2px;
                font-size: 8pt;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background-color: #e7f0fd;
                color: #000000;
                border: 3px solid #5b9bd5;
            }
            QTabBar::tab:hover {
                background-color: #cce4ff;
            }
        """
        
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(tab_style)
        
        # Create tabs
        self.solver_tab = SolverTab()
        self.display_tab = DisplayTab()

        self.display_tab.set_plotting_handler(self.plotting_handler) #TODO: Add this plotting handler method inside Display tab
        
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
            self.solver_tab.request_time_point_calculation
        )
        self.display_tab.animation_precomputation_requested.connect(
            self.solver_tab.request_animation_precomputation
        )

    def open_advanced_settings(self):
        """Open advanced settings dialog."""
        dialog = AdvancedSettingsDialog(self)
        if dialog.exec_() == AdvancedSettingsDialog.Accepted:
            settings = dialog.get_settings()
            self.settings_handler.apply_advanced_settings(settings)
            QMessageBox.information(
                self, "Settings Applied",
                "New advanced settings have been applied.\n"
                "They will be used for the next solve operation."
            )
    
    def closeEvent(self, event):
        """Clean up temporary files on application close."""
        self.plotting_handler.cleanup_temp_files()
        event.accept()

