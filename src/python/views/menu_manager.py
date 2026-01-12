"""
Menu bar manager for the main window.

Extracts menu bar setup logic from MainWindow to reduce class size
and improve maintainability.
"""

from typing import TYPE_CHECKING, Callable, List, Tuple
from PySide6.QtWidgets import QMainWindow, QMenu
from PySide6.QtGui import QAction

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel


class MenuBarManager:
    """Manages menu bar setup and actions for the main window."""
    
    def __init__(
        self,
        main_window: QMainWindow,
        pipeline_vm: "PipelineViewModel",
        on_load_file: Callable[[], None],
        on_apply_filter: Callable[[str], None],
        create_tab: Callable[[str, str], None],
    ):
        """
        Initialize the menu bar manager.
        
        Args:
            main_window: Parent main window
            pipeline_vm: Pipeline ViewModel for filter menu population
            on_load_file: Callback for file loading
            on_apply_filter: Callback for filter application (takes filter_type)
            create_tab: Callback for tab creation (takes tab_type, tab_name)
        """
        self._main_window = main_window
        self._pipeline_vm = pipeline_vm
        self._on_load_file = on_load_file
        self._on_apply_filter = on_apply_filter
        self._create_tab = create_tab
    
    def setup(self) -> None:
        """Setup the complete menu bar."""
        menu_bar = self._main_window.menuBar()
        
        # File menu
        self._setup_file_menu(menu_bar)
        
        # Filters menu
        filters_menu = menu_bar.addMenu("Filters")
        self._populate_filters_menu(filters_menu)
        
        # View menu
        self._setup_view_menu(menu_bar)
    
    def _setup_file_menu(self, menu_bar) -> None:
        """Setup the File menu."""
        file_menu = menu_bar.addMenu("File")
        
        load_action = QAction("Load Data...", self._main_window)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_file)
        file_menu.addAction(load_action)
        
        exit_action = QAction("Exit", self._main_window)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self._main_window.close)
        file_menu.addAction(exit_action)
    
    def _populate_filters_menu(self, menu: QMenu) -> None:
        """Populate filters menu from registry."""
        for filter_type, display_name in self._pipeline_vm.get_available_filters():
            action = QAction(display_name, self._main_window)
            action.triggered.connect(
                lambda checked=False, ft=filter_type: self._on_apply_filter(ft)
            )
            menu.addAction(action)
    
    def _setup_view_menu(self, menu_bar) -> None:
        """Setup the View menu for creating tabs."""
        view_menu = menu_bar.addMenu("View")
        
        new_3d_tab_action = QAction("New 3D View Tab", self._main_window)
        new_3d_tab_action.triggered.connect(
            lambda: self._create_tab("vtk", "3D View")
        )
        view_menu.addAction(new_3d_tab_action)
        
        new_table_tab_action = QAction("New Table View Tab", self._main_window)
        new_table_tab_action.triggered.connect(
            lambda: self._create_tab("table", "Table")
        )
        view_menu.addAction(new_table_tab_action)
        
        new_graph_tab_action = QAction("New Graph View Tab", self._main_window)
        new_graph_tab_action.triggered.connect(
            lambda: self._create_tab("graph", "Graph")
        )
        view_menu.addAction(new_graph_tab_action)
