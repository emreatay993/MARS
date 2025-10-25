"""
Main window for the MARS: Modal Analysis Response Solver application.

Provides the main application window with menu bar, navigator, and tab widgets
for solver and display functionality.
"""

from PyQt5.QtCore import Qt, QDir, pyqtSlot
from PyQt5.QtGui import QPalette, QColor
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
from ui.styles.style_constants import (
    MENU_BAR_STYLE, NAVIGATOR_TITLE_STYLE, TREE_VIEW_STYLE, TAB_STYLE
)


class ApplicationController(QMainWindow):
    """
    Main application controller for MARS.

    Coordinates tabs, signal connections between components, and application-level
    state and navigation.
    """
    
    def __init__(self):
        """Initialize the application controller."""
        super().__init__()

        # Set window background color (matching legacy)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(230, 230, 230))  # Light gray background
        self.setPalette(palette)

        # Handlers
        self.plotting_handler = PlottingHandler()

        # Window configuration
        self.setWindowTitle('MARS: Modal Analysis Response Solver - v1.0.0 (Modular)')
        self.setGeometry(40, 40, 600, 800)
        
        # Create UI components (order matters - navigator before menu bar)
        self._create_tabs()
        self._create_navigator()
        self._create_menu_bar()
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
        self.solver_tab.animation_precomputation_failed.connect(
            self._on_animation_precomputation_failed
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

    @pyqtSlot(str)
    def _on_animation_precomputation_failed(self, message: str):
        """Show failure message for animation precomputation and reset UI controls."""
        try:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Animation Cancelled", message)
            # Enable play button on display tab if available
            if hasattr(self.display_tab, 'play_button'):
                self.display_tab.play_button.setEnabled(True)
        except Exception:
            pass

    @pyqtSlot(bool)
    def open_advanced_settings(self, checked=False):
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
