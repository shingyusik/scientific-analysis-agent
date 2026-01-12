"""
Toolbar manager for the main window.

Extracts toolbar setup logic from MainWindow to reduce class size
and improve maintainability.
"""

from typing import TYPE_CHECKING, Callable, Any
from PySide6.QtWidgets import QMainWindow, QMenu, QToolButton, QToolBar

if TYPE_CHECKING:
    from viewmodels.vtk_viewmodel import VTKViewModel
    from viewmodels.pipeline_viewmodel import PipelineViewModel


# Toolbar dropdown button style
DROPDOWN_BUTTON_STYLE = (
    "QToolButton { padding-right: 15px; } "
    "QToolButton::menu-indicator { subcontrol-origin: padding; subcontrol-position: center right; }"
)


class ToolbarManager:
    """Manages toolbar setup and actions for the main window."""
    
    def __init__(
        self,
        main_window: QMainWindow,
        vtk_vm: "VTKViewModel",
        pipeline_vm: "PipelineViewModel",
        on_camera_view: Callable[[], None],
        on_fit_range: Callable[[], None],
        on_custom_range: Callable[[], None],
    ):
        """
        Initialize the toolbar manager.
        
        Args:
            main_window: Parent main window
            vtk_vm: VTK ViewModel for view controls
            pipeline_vm: Pipeline ViewModel for item operations
            on_camera_view: Callback for camera view dialog
            on_fit_range: Callback for fit scalar range
            on_custom_range: Callback for custom scalar range dialog
        """
        self._main_window = main_window
        self._vtk_vm = vtk_vm
        self._pipeline_vm = pipeline_vm
        self._on_camera_view = on_camera_view
        self._on_fit_range = on_fit_range
        self._on_custom_range = on_custom_range
        
        self._toolbar: QToolBar = None
        self._background_btn: QToolButton = None
        self._representation_btn: QToolButton = None
    
    def setup(self) -> QToolBar:
        """Setup the main toolbar and return it."""
        self._toolbar = self._main_window.addToolBar("View Controls")
        toolbar = self._toolbar
        
        # Camera controls
        action_camera = toolbar.addAction("Camera View")
        action_camera.triggered.connect(self._on_camera_view)
        
        action_reset = toolbar.addAction("Home (Reset)")
        action_reset.triggered.connect(self._vtk_vm.reset_camera)
        
        toolbar.addSeparator()
        
        # View plane controls
        action_xy = toolbar.addAction("XY Plane")
        action_xy.triggered.connect(lambda: self._vtk_vm.set_view_plane("xy"))
        
        action_yz = toolbar.addAction("YZ Plane")
        action_yz.triggered.connect(lambda: self._vtk_vm.set_view_plane("yz"))
        
        action_xz = toolbar.addAction("XZ Plane")
        action_xz.triggered.connect(lambda: self._vtk_vm.set_view_plane("xz"))
        
        toolbar.addSeparator()
        
        # Scalar range controls
        action_fit_range = toolbar.addAction("Fit Range")
        action_fit_range.triggered.connect(self._on_fit_range)
        
        action_custom_range = toolbar.addAction("Custom Range")
        action_custom_range.triggered.connect(self._on_custom_range)
        
        toolbar.addSeparator()
        
        # Dropdown menus
        self._setup_background_menu(toolbar)
        self._setup_representation_menu(toolbar)
        
        return toolbar
    
    def _setup_background_menu(self, toolbar: QToolBar) -> None:
        """Setup background color dropdown."""
        self._background_btn = QToolButton()
        self._background_btn.setText("Background")
        self._background_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._background_btn.setStyleSheet(DROPDOWN_BUTTON_STYLE)
        
        bg_menu = QMenu(self._main_window)
        for name, c1, c2 in self._vtk_vm.BACKGROUND_PRESETS:
            action = bg_menu.addAction(name)
            action.triggered.connect(
                lambda checked=False, n=name: self._vtk_vm.set_background_preset(n)
            )
        
        self._background_btn.setMenu(bg_menu)
        toolbar.addWidget(self._background_btn)
        
        # Sync with ViewModel
        self._vtk_vm.background_preset_changed.connect(self._on_background_changed)
        
        # Initialize
        current_name = self._vtk_vm._current_background[0]
        self._background_btn.setText(current_name)
    
    def _on_background_changed(self, name: str) -> None:
        """Handle background preset change."""
        if self._background_btn:
            self._background_btn.setText(name)
    
    def _setup_representation_menu(self, toolbar: QToolBar) -> None:
        """Setup representation style dropdown."""
        self._representation_btn = QToolButton()
        self._representation_btn.setText("Representation")
        self._representation_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._representation_btn.setStyleSheet(DROPDOWN_BUTTON_STYLE)
        
        rep_menu = QMenu(self._main_window)
        for style in self._vtk_vm.REPRESENTATION_STYLES:
            action = rep_menu.addAction(style)
            action.triggered.connect(
                lambda checked=False, s=style: self._set_selected_item_representation(s)
            )
        
        self._representation_btn.setMenu(rep_menu)
        toolbar.addWidget(self._representation_btn)
        
        # Sync with ViewModel (Item based sync)
        self._pipeline_vm.item_style_changed.connect(self._on_item_style_changed)
        self._pipeline_vm.selection_changed.connect(self._on_item_selected)
    
    def _set_selected_item_representation(self, style: str) -> None:
        """Set representation for selected item via Toolbar."""
        selected = self._pipeline_vm.selected_item
        if selected:
            self._pipeline_vm.set_representation(selected.id, style)
            self._vtk_vm.request_render()
    
    def _on_item_style_changed(self, item_id: str, style: str) -> None:
        """Handle item representation change."""
        selected = self._pipeline_vm.selected_item
        if selected and selected.id == item_id:
            if self._representation_btn:
                self._representation_btn.setText(style)
    
    def _on_item_selected(self, item: Any) -> None:
        """Update toolbar when selection changes."""
        if item and self._representation_btn:
            style = self._vtk_vm.get_representation_style(item.actor)
            self._representation_btn.setText(style)
    
    @property
    def toolbar(self) -> QToolBar:
        """Get the main toolbar."""
        return self._toolbar
    
    @property
    def representation_button(self) -> QToolButton:
        """Get the representation button for external updates."""
        return self._representation_btn
