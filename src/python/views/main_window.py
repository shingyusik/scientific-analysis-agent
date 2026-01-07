from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit,
                               QMenu, QToolButton, QFileDialog, QMessageBox, QToolBar,
                               QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox, QLabel)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from utils.logger import get_logger

from views.vtk_widget import VTKWidget
from views.pipeline_browser import PipelineBrowserWidget
from views.properties_panel import PropertiesPanel
from views.chat_panel import ChatPanel
from views.time_animation_widget import TimeAnimationWidget
from views.tabbed_view_widget import TabbedViewWidget
from views.table_view_widget import TableViewWidget
from views.graph_view_widget import GraphViewWidget
from viewmodels.pipeline_viewmodel import PipelineViewModel
from viewmodels.vtk_viewmodel import VTKViewModel
from viewmodels.chat_viewmodel import ChatViewModel
from viewmodels.time_series_manager import TimeSeriesManager
from viewmodels.table_viewmodel import TableViewModel
from viewmodels.graph_viewmodel import GraphViewModel
from models.properties_context import PropertiesPanelContext
from models.tab_types import TabType
from utils.app_context import set_time_series_manager
import filters


class ScalarRangeDialog(QDialog):
    """Dialog for setting custom scalar range."""
    
    def __init__(self, parent=None, current_min: float = 0.0, current_max: float = 1.0):
        super().__init__(parent)
        self.setWindowTitle("Custom Scalar Range")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setRange(-1e10, 1e10)
        self.min_spinbox.setValue(current_min)
        self.min_spinbox.setDecimals(6)
        self.min_spinbox.setSingleStep(0.1)
        
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setRange(-1e10, 1e10)
        self.max_spinbox.setValue(current_max)
        self.max_spinbox.setDecimals(6)
        self.max_spinbox.setSingleStep(0.1)
        
        layout.addRow("Minimum value:", self.min_spinbox)
        layout.addRow("Maximum value:", self.max_spinbox)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def get_values(self):
        """Get the entered min and max values."""
        return self.min_spinbox.value(), self.max_spinbox.value()


class CameraViewDialog(QDialog):
    """Dialog for manual camera adjustment."""
    
    def __init__(self, parent=None, initial_state: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Camera View Settings")
        self.setModal(False)  # Allow live updates if we want, but let's stick to Apply/OK for now
        
        layout = QFormLayout(self)
        
        self.pos_x = self._create_spinbox(initial_state.get("position", [0, 0, 0])[0])
        self.pos_y = self._create_spinbox(initial_state.get("position", [0, 0, 0])[1])
        self.pos_z = self._create_spinbox(initial_state.get("position", [0, 0, 0])[2])
        
        self.focal_x = self._create_spinbox(initial_state.get("focal_point", [0, 0, 0])[0])
        self.focal_y = self._create_spinbox(initial_state.get("focal_point", [0, 0, 0])[1])
        self.focal_z = self._create_spinbox(initial_state.get("focal_point", [0, 0, 0])[2])
        
        self.up_x = self._create_spinbox(initial_state.get("view_up", [0, 0, 1])[0])
        self.up_y = self._create_spinbox(initial_state.get("view_up", [0, 0, 1])[1])
        self.up_z = self._create_spinbox(initial_state.get("view_up", [0, 0, 1])[2])
        
        self.zoom = self._create_spinbox(initial_state.get("zoom", 30))
        
        layout.addRow("Position X:", self.pos_x)
        layout.addRow("Position Y:", self.pos_y)
        layout.addRow("Position Z:", self.pos_z)
        layout.addRow(QLabel("")) # Spacer
        layout.addRow("Focal Point X:", self.focal_x)
        layout.addRow("Focal Point Y:", self.focal_y)
        layout.addRow("Focal Point Z:", self.focal_z)
        layout.addRow(QLabel("")) # Spacer
        layout.addRow("View Up X:", self.up_x)
        layout.addRow("View Up Y:", self.up_y)
        layout.addRow("View Up Z:", self.up_z)
        layout.addRow(QLabel("")) # Spacer
        layout.addRow("Zoom / Angle:", self.zoom)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Apply).clicked.connect(self.apply_clicked)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.apply_requested = None # Placeholder for callback
        
    def _create_spinbox(self, value):
        sb = QDoubleSpinBox()
        sb.setRange(-1e10, 1e10)
        sb.setValue(value)
        sb.setDecimals(4)
        sb.setSingleStep(0.1)
        return sb
        
    def get_state(self):
        return {
            "position": [self.pos_x.value(), self.pos_y.value(), self.pos_z.value()],
            "focal_point": [self.focal_x.value(), self.focal_y.value(), self.focal_z.value()],
            "view_up": [self.up_x.value(), self.up_y.value(), self.up_z.value()],
            "zoom": self.zoom.value()
        }
        
    def apply_clicked(self):
        if self.apply_requested:
            self.apply_requested(self.get_state())


class MainWindow(QMainWindow):
    """Main application window - orchestrates views and viewmodels."""
    
    def __init__(self, pipeline_vm: PipelineViewModel, vtk_vm: VTKViewModel, chat_vm: ChatViewModel):
        super().__init__()
        self._pipeline_vm = pipeline_vm
        self._vtk_vm = vtk_vm
        self._chat_vm = chat_vm
        self._time_manager = TimeSeriesManager(self)
        
        # Initialize logger
        self.logger = get_logger("MainWindow")
        
        # New: Tab tracking for tab-aware visualization
        self._active_tab_id: Optional[str] = None
        self._active_tab_type: TabType = TabType.VTK
        self._tab_item_mapping: Dict[str, str] = {}  # {tab_id: item_id}
        
        
        # Register TimeSeriesManager in app context for agent tool access
        set_time_series_manager(self._time_manager)
        
        # NOW initialize the agent after all context is registered
        self._chat_vm.initialize_agent()
        
        
        self.setWindowTitle("Scientific Analysis Agent")
        self.resize(1400, 900)
        
        self._setup_menu_bar()
        self._setup_toolbar()
        self._setup_main_layout()
        self._connect_signals()
        self._initialize()
    
    def _setup_menu_bar(self) -> None:
        """Setup the menu bar."""
        menu_bar = self.menuBar()
        
        file_menu = menu_bar.addMenu("File")
        
        load_action = QAction("Load Data...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._on_load_file)
        file_menu.addAction(load_action)
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        filters_menu = menu_bar.addMenu("Filters")
        self._populate_filters_menu(filters_menu)
        
        # View menu for creating tabs
        view_menu = menu_bar.addMenu("View")
        
        new_3d_tab_action = QAction("New 3D View Tab", self)
        new_3d_tab_action.triggered.connect(lambda: self._create_tab_from_menu("vtk", "3D View"))
        view_menu.addAction(new_3d_tab_action)
        
        new_table_tab_action = QAction("New Table View Tab", self)
        new_table_tab_action.triggered.connect(lambda: self._create_tab_from_menu("table", "Table"))
        view_menu.addAction(new_table_tab_action)
        
        new_graph_tab_action = QAction("New Graph View Tab", self)
        new_graph_tab_action.triggered.connect(lambda: self._create_tab_from_menu("graph", "Graph"))
        view_menu.addAction(new_graph_tab_action)
    
    def _populate_filters_menu(self, menu: QMenu) -> None:
        """Populate filters menu from registry."""
        for filter_type, display_name in self._pipeline_vm.get_available_filters():
            action = QAction(display_name, self)
            action.triggered.connect(
                lambda checked=False, ft=filter_type: self._on_apply_filter(ft)
            )
            menu.addAction(action)
    
    def _setup_toolbar(self) -> None:
        """Setup the toolbar."""
        self._toolbar = self.addToolBar("View Controls")
        toolbar = self._toolbar
        
        action_camera = toolbar.addAction("Camera View")
        action_camera.triggered.connect(self._on_camera_view)
        
        action_reset = toolbar.addAction("Home (Reset)")
        action_reset.triggered.connect(self._vtk_vm.reset_camera)
        
        toolbar.addSeparator()
        
        action_xy = toolbar.addAction("XY Plane")
        action_xy.triggered.connect(lambda: self._vtk_vm.set_view_plane("xy"))
        
        action_yz = toolbar.addAction("YZ Plane")
        action_yz.triggered.connect(lambda: self._vtk_vm.set_view_plane("yz"))
        
        action_xz = toolbar.addAction("XZ Plane")
        action_xz.triggered.connect(lambda: self._vtk_vm.set_view_plane("xz"))
        
        toolbar.addSeparator()
        
        action_fit_range = toolbar.addAction("Fit Range")
        action_fit_range.triggered.connect(self._on_fit_range)
        
        action_custom_range = toolbar.addAction("Custom Range")
        action_custom_range.triggered.connect(self._on_custom_range)
        
        toolbar.addSeparator()
        
        self._setup_background_menu(toolbar)
        self._setup_representation_menu(toolbar)
        
        self._setup_time_animation_toolbar()
    
    def _setup_background_menu(self, toolbar) -> None:
        """Setup background color dropdown."""
        bg_btn = QToolButton()
        bg_btn.setText("Background")
        bg_btn.setPopupMode(QToolButton.InstantPopup)
        bg_btn.setStyleSheet(
            "QToolButton { padding-right: 15px; } "
            "QToolButton::menu-indicator { subcontrol-origin: padding; subcontrol-position: center right; }"
        )
        
        bg_menu = QMenu(self)
        for name, c1, c2 in self._vtk_vm.BACKGROUND_PRESETS:
            action = bg_menu.addAction(name)
            action.triggered.connect(
                lambda checked=False, col1=c1, col2=c2: self._vtk_vm.set_background(col1, col2)
            )
        
        bg_btn.setMenu(bg_menu)
        toolbar.addWidget(bg_btn)
    
    def _setup_representation_menu(self, toolbar) -> None:
        """Setup representation style dropdown."""
        rep_btn = QToolButton()
        rep_btn.setText("Representation")
        rep_btn.setPopupMode(QToolButton.InstantPopup)
        rep_btn.setStyleSheet(
            "QToolButton { padding-right: 15px; } "
            "QToolButton::menu-indicator { subcontrol-origin: padding; subcontrol-position: center right; }"
        )
        
        rep_menu = QMenu(self)
        for style in self._vtk_vm.REPRESENTATION_STYLES:
            action = rep_menu.addAction(style)
            action.triggered.connect(
                lambda checked=False, s=style: self._on_representation_changed(s)
            )
        
        rep_btn.setMenu(rep_menu)
        toolbar.addWidget(rep_btn)
    
    def _setup_time_animation_toolbar(self) -> None:
        """Setup time animation toolbar."""
        time_toolbar = self.addToolBar("Time Animation")
        
        self._time_animation_widget = TimeAnimationWidget(self._time_manager)
        time_toolbar.addWidget(self._time_animation_widget)
    
    def _setup_main_layout(self) -> None:
        """Setup the main layout with splitters."""
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)
        
        left_sidebar = QSplitter(Qt.Vertical)
        
        self._pipeline_browser = PipelineBrowserWidget()
        left_sidebar.addWidget(self._pipeline_browser)
        
        self._details_tabs = QTabWidget()
        
        self._properties_panel = PropertiesPanel()
        self._properties_panel.set_render_service(self._pipeline_vm.render_service)
        self._details_tabs.addTab(self._properties_panel, "Properties")
        
        self._info_page = QTextEdit()
        self._info_page.setReadOnly(True)
        self._details_tabs.addTab(self._info_page, "Information")
        
        left_sidebar.addWidget(self._details_tabs)
        left_sidebar.setStretchFactor(0, 1)
        left_sidebar.setStretchFactor(1, 1)
        
        main_splitter.addWidget(left_sidebar)
        
        # Create tabbed view widget for center panel
        self._tabbed_view = TabbedViewWidget()
        
        # Create initial VTK render view tab (pinned by default)
        self._vtk_widget = VTKWidget()
        self._default_vtk_tab_id = self._tabbed_view.add_tab_with_id(
            self._vtk_widget, "vtk", "3D View", pinned=True
        )
        
        # Initialize active tab state
        self._active_tab_id = self._default_vtk_tab_id
        self._active_tab_type = "vtk"
        
        main_splitter.addWidget(self._tabbed_view)
        
        self._chat_panel = ChatPanel()
        main_splitter.addWidget(self._chat_panel)
        
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 5)
        main_splitter.setStretchFactor(2, 2)
        main_splitter.setSizes([350, 750, 300])
    
    
    def _connect_signals(self) -> None:
        """Connect viewmodel signals to UI slots."""
        self._pipeline_vm.item_added.connect(self._on_item_added)
        self._pipeline_vm.item_removed.connect(self._on_item_removed)
        self._pipeline_vm.item_updated.connect(self._on_item_updated)
        self._pipeline_vm.selection_changed.connect(self._on_selection_changed)
        self._pipeline_vm.time_series_loaded.connect(self._on_time_series_loaded)
        
        self._pipeline_browser.item_selected.connect(self._on_browser_selection)
        self._pipeline_browser.item_visibility_changed.connect(self._on_visibility_changed)
        self._pipeline_browser.item_delete_requested.connect(self._on_delete_requested)
        
        self._properties_panel.apply_filter_requested.connect(self._pipeline_vm.commit_filter)
        self._properties_panel.delete_requested.connect(self._on_delete_requested)
        self._properties_panel.opacity_changed.connect(self._on_opacity_changed)
        self._properties_panel.point_size_changed.connect(self._pipeline_vm.set_point_size)
        self._properties_panel.line_width_changed.connect(self._pipeline_vm.set_line_width)
        self._properties_panel.gaussian_scale_changed.connect(self._pipeline_vm.set_gaussian_scale)
        self._properties_panel.color_by_changed.connect(self._on_color_by_changed)
        self._properties_panel.filter_params_changed.connect(self._on_filter_params_changed)
        self._properties_panel.legend_settings_changed.connect(self._vtk_vm.set_legend_settings)
        
        self._chat_panel.message_sent.connect(self._chat_vm.send_user_message)
        self._chat_panel.new_conversation_requested.connect(self._chat_vm.start_new_conversation)
        self._chat_panel.cancel_requested.connect(self._chat_vm.stop_generation)
        self._chat_vm.message_added.connect(
            lambda msg: self._chat_panel.append_message(msg.sender, msg.content)
        )
        
        # AI started/finished handlers
        self._chat_vm.streaming_started.connect(self._disable_ui_interaction)
        self._chat_vm.streaming_finished.connect(self._enable_ui_interaction)
        
        # Chat panel streaming connections
        self._chat_vm.streaming_started.connect(self._chat_panel.start_streaming)
        self._chat_vm.streaming_token.connect(self._chat_panel.update_streaming)
        self._chat_vm.streaming_finished.connect(self._chat_panel.finish_streaming)
        self._chat_vm.tool_activity.connect(self._chat_panel.add_tool_activity)
        self._chat_vm.input_requested.connect(
            lambda desc, fields: self._chat_panel.show_input_form(desc, fields, self._chat_vm)
        )
        self._chat_vm.render_requested.connect(self._vtk_widget.render)
        self._chat_vm.conversation_cleared.connect(self._chat_panel.clear_display)
        
        self._vtk_vm.actor_added.connect(self._vtk_widget.add_actor)
        self._vtk_vm.actor_removed.connect(self._vtk_widget.remove_actor)
        self._vtk_vm.actor_visibility_changed.connect(self._vtk_widget.set_actor_visibility)
        self._vtk_vm.clear_scene_requested.connect(self._pipeline_vm.clear_all_items)
        self._vtk_vm.clear_scene_requested.connect(self._vtk_widget.clear_scene)
        self._vtk_vm.background_changed.connect(self._vtk_widget.set_background)
        self._vtk_vm.camera_reset_requested.connect(self._vtk_widget.reset_camera)
        self._vtk_vm.view_plane_requested.connect(self._vtk_widget.set_view_plane)
        self._vtk_vm.plane_preview_requested.connect(self._vtk_widget.update_plane_preview)
        self._vtk_vm.plane_preview_hide_requested.connect(self._vtk_widget.hide_plane_preview)
        self._vtk_vm.camera_query_requested.connect(
            lambda: self._vtk_vm.notify_camera_state(self._vtk_widget.get_camera_state())
        )
        self._vtk_vm.camera_apply_requested.connect(self._vtk_widget.apply_camera_state)
        self._vtk_vm.scalar_bar_update_requested.connect(self._vtk_widget.update_scalar_bar)
        self._vtk_vm.scalar_bar_hide_requested.connect(self._vtk_widget.hide_scalar_bar)
        self._vtk_vm.legend_settings_changed.connect(self._vtk_widget.apply_legend_settings)
        
        # Tabbed view connections
        self._tabbed_view.tab_created.connect(self._on_tab_created)
        self._tabbed_view.tab_closed.connect(self._on_tab_closed)
        self._tabbed_view.currentChanged.connect(self._on_tab_changed)
        
        # Tab management signals from PipelineViewModel (for LLM tools)
        self._pipeline_vm.vtk_view_requested.connect(self._handle_vtk_view_request)
        self._pipeline_vm.table_view_requested.connect(self._handle_table_view_request)
        self._pipeline_vm.graph_view_requested.connect(self._handle_graph_view_request)
        self._pipeline_vm.tab_close_requested.connect(self._handle_tab_close_request)
        self._pipeline_vm.tab_pin_requested.connect(self._handle_tab_pin_request)
        
        self._time_manager.time_changed.connect(self._on_time_step_changed)
    
    def _disable_ui_interaction(self) -> None:
        """Disable UI elements when AI starts responding."""
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication
        
        try:
            # Set busy cursor
            QApplication.setOverrideCursor(Qt.WaitCursor)
            
            # Disable ALL main interaction areas explicitely
            self._tabbed_view.setEnabled(False)
            if hasattr(self._tabbed_view, "tabBar"):
                 self._tabbed_view.tabBar().setEnabled(False)

            if hasattr(self, "_toolbar") and self._toolbar:
                self._toolbar.setEnabled(False)
                
            if hasattr(self, "_pipeline_browser") and self._pipeline_browser:
                self._pipeline_browser.setEnabled(False)
                
            if hasattr(self, "_properties_panel") and self._properties_panel:
                self._properties_panel.setEnabled(False)
                
            if hasattr(self, "_details_tabs") and self._details_tabs:
                self._details_tabs.setEnabled(False)
                
            # Disable menu bar
            if self.menuBar():
                self.menuBar().setEnabled(False)
            
            # Force update
            QApplication.processEvents()
            self.logger.info("UI disabled successfully")
        except Exception as e:
            self.logger.error(f"Error disabling UI: {e}", exc_info=True)
    
    def _enable_ui_interaction(self) -> None:
        """Re-enable UI elements when AI finishes responding."""
        from PySide6.QtCore import QTimer
        
        # Small delay to ensure no flickering
        QTimer.singleShot(100, self._perform_ui_reenable)

    def _perform_ui_reenable(self) -> None:
        from PySide6.QtWidgets import QApplication
        
        try:
            # Re-enable all elements
            if hasattr(self, "_tabbed_view"):
                self._tabbed_view.setEnabled(True)
                if hasattr(self._tabbed_view, "tabBar"):
                    self._tabbed_view.tabBar().setEnabled(True)
            
            if hasattr(self, "_toolbar") and self._toolbar:
                self._toolbar.setEnabled(True)
                
            if hasattr(self, "_pipeline_browser") and self._pipeline_browser:
                self._pipeline_browser.setEnabled(True)
                
            if hasattr(self, "_properties_panel") and self._properties_panel:
                self._properties_panel.setEnabled(True)

            if hasattr(self, "_details_tabs") and self._details_tabs:
                self._details_tabs.setEnabled(True)
                
            # Re-enable menu bar
            if self.menuBar():
                self.menuBar().setEnabled(True)
            
            # Restore cursor (safely loop to clear all overrides if any)
            while QApplication.overrideCursor() is not None:
                QApplication.restoreOverrideCursor()
            
            QApplication.processEvents()
            self.logger.info("UI re-enabled successfully")
        except Exception as e:
            self.logger.error(f"Error in _on_ai_finished: {e}", exc_info=True)
    
    def _initialize(self) -> None:
        """Initialize the application state."""
        self._vtk_vm.clear_scene()
        item = self._pipeline_vm.create_cone_source()
        self._vtk_vm.add_actor(item.actor)
        self._vtk_vm.reset_camera()
    
    def _on_load_file(self) -> None:
        """Handle file load action."""
        file_names, _ = QFileDialog.getOpenFileNames(
            self, "Load Data", "", "VTK Files (*.vtu *.vti *.vtk)"
        )
        if not file_names:
            return
        
        if len(file_names) > 1:
            item = self._pipeline_vm.load_time_series(file_names)
        else:
            item = self._pipeline_vm.load_file(file_names[0])
        
        if item:
            self._vtk_vm.add_actor(item.actor)
            self._vtk_vm.reset_camera()
            self._pipeline_vm.select_item(item.id)
    
    def _on_apply_filter(self, filter_type: str) -> None:
        """Handle filter application from menu."""
        selected = self._pipeline_vm.selected_item
        if not selected:
            QMessageBox.warning(self, "Warning", "Please select a source in Pipeline Browser.")
            return
        
        item = self._pipeline_vm.apply_filter(filter_type, selected.id)
        if item:
            self._vtk_vm.add_actor(item.actor)
            self._vtk_vm.request_render()
            self._pipeline_vm.select_item(item.id)
    
    def _on_representation_changed(self, style: str) -> None:
        """Handle representation style change."""
        selected = self._pipeline_vm.selected_item
        if selected:
            self._pipeline_vm.set_representation(selected.id, style)
            self._update_properties_panel(selected)
            self._vtk_vm.request_render()
    
    def _on_item_added(self, item) -> None:
        """Handle item added to pipeline."""
        self._pipeline_browser.add_item(item)
        if item.actor:
            self._vtk_vm.add_actor(item.actor)
            self._vtk_vm.request_render()
    
    def _on_item_removed(self, item_id: str) -> None:
        """Handle item removed from pipeline."""
        item = self._pipeline_vm.items.get(item_id)
        if item and item.actor:
            self._vtk_vm.remove_actor(item.actor)
        self._pipeline_browser.remove_item(item_id)
        self._vtk_vm.hide_plane_preview()
    
    def _on_item_updated(self, item) -> None:
        """Handle item update."""
        self._pipeline_browser.update_item(item)
        if item == self._pipeline_vm.selected_item:
            self._update_properties_panel(item)
        self._vtk_vm.request_render()
    
    def _on_selection_changed(self, item) -> None:
        """Handle selection change."""
        if item:
            self._pipeline_browser.select_item(item.id)
            self._info_page.setPlainText(item.get_info_string())
            self._update_time_animation_widget(item)
            
            # Map item to active tab
            if self._active_tab_id:
                self._tab_item_mapping[self._active_tab_id] = item.id
            
            # Update active tab display
            if self._active_tab_type == TabType.VTK:
                self._update_properties_panel(item)
            elif self._active_tab_type == TabType.TABLE:
                self._update_table_tab(item)
            elif self._active_tab_type == TabType.GRAPH:
                self._update_graph_tab(item)
        else:
            self._clear_active_tab_display()
            self._info_page.setPlainText("")
            self._time_manager.set_item(None)
            self._time_animation_widget.reset()
    
    def _on_browser_selection(self, item_id: str) -> None:
        """Handle browser selection."""
        self._pipeline_vm.select_item(item_id if item_id else None)
    
    def _on_visibility_changed(self, item_id: str, visible: bool) -> None:
        """Handle visibility toggle."""
        self._pipeline_vm.set_visibility(item_id, visible)
        
        # Update visibility in all relevant tabs or just active?
        # User requested "pipeline의 가시화 버튼으로 열려있는 탭의 가시화가 조작됐음 좋겠어"
        # This means all tabs displaying this item should update.
        
        # 1. Update VTK actors (standard behavior)
        item = self._pipeline_vm.items.get(item_id)
        if item and item.actor:
            self._vtk_vm.set_actor_visibility(item.actor, visible)
            
        # 2. Update Table/Graph tabs displaying this item
        for tab_id, display_item_id in self._tab_item_mapping.items():
            if display_item_id == item_id:
                widget = self._tabbed_view.get_tab_widget_by_id(tab_id)
                if hasattr(widget, "set_data_visibility"):
                    widget.set_data_visibility(visible)

    
    def _on_delete_requested(self, item_id: str) -> None:
        """Handle delete request."""
        item = self._pipeline_vm.items.get(item_id)
        if item and item.actor:
            self._vtk_vm.remove_actor(item.actor)
        self._pipeline_vm.delete_item(item_id)
        self._vtk_vm.hide_plane_preview()
    
    def _on_opacity_changed(self, item_id: str, value: float) -> None:
        """Handle opacity change."""
        self._pipeline_vm.set_opacity(item_id, value)
        self._vtk_vm.request_render()
    
    def _on_color_by_changed(self, item_id: str, array_name: str, array_type: str, component: str = '') -> None:
        """Handle color by change."""
        self._pipeline_vm.set_color_by(item_id, array_name, array_type, component)
        
        item = self._pipeline_vm.items.get(item_id)
        if item and item.actor and item.visible:
            if array_name == "__SolidColor__":
                self._vtk_vm.hide_scalar_bar()
            else:
                self._vtk_vm.update_scalar_bar(item.actor)
        
        self._vtk_vm.request_render()
    
    def _on_filter_params_changed(self, item_id: str, params: dict) -> None:
        """Handle general filter parameter change."""
        self._pipeline_vm.update_filter_params(item_id, params)
        
        item = self._pipeline_vm.items.get(item_id)
        if item and "filter" in item.item_type:
            self._update_plane_preview_visibility(item)
    
    
    def _update_properties_panel(self, item) -> None:
        """Update properties panel for item."""
        if not item:
            self._properties_panel.set_item(None)
            self._vtk_vm.hide_scalar_bar()
            self._vtk_vm.hide_plane_preview()
            return
        
        ctx = PropertiesPanelContext.from_item(item, self._vtk_vm)
        
        parent_bounds = None
        if "filter" in item.item_type:
            parent = self._pipeline_vm.get_parent_item(item.id)
            if parent and parent.vtk_data:
                parent_bounds = parent.vtk_data.GetBounds()
        
        # Determine viewmodel based on active tab
        viewmodel = None
        widget = self._tabbed_view.get_active_tab_widget()
        if widget and hasattr(widget, "viewmodel"):
            viewmodel = widget.viewmodel
            
        self._properties_panel.set_item(
            item, ctx.style, ctx.data_arrays, ctx.current_array, ctx.current_component,
            ctx.scalar_visible, parent_bounds, viewmodel
        )

        
        self._update_scalar_bar_visibility(item, ctx.scalar_visible)
        self._update_plane_preview_visibility(item)
    
    def _update_scalar_bar_visibility(self, item, scalar_visible: bool) -> None:
        """Update scalar bar based on item state."""
        if item.actor and scalar_visible and item.visible:
            self._vtk_vm.update_scalar_bar(item.actor)
        else:
            self._vtk_vm.hide_scalar_bar()
    
    def _update_plane_preview_visibility(self, item) -> None:
        """Update plane preview based on filter's plane preview params."""
        if "filter" not in item.item_type:
            self._vtk_vm.hide_plane_preview()
            return
        
        filter_instance = self._pipeline_vm.get_filter(item.item_type)
        if not filter_instance:
            self._vtk_vm.hide_plane_preview()
            return
        
        preview_params = filter_instance.get_plane_preview_params(item.filter_params)
        if not preview_params:
            self._vtk_vm.hide_plane_preview()
            return
        
        origin, normal, show_preview = preview_params
        parent = self._pipeline_vm.get_parent_item(item.id)
        
        if show_preview and parent and parent.vtk_data:
            bounds = parent.vtk_data.GetBounds()
            self._vtk_vm.show_plane_preview(origin, normal, bounds)
        else:
            self._vtk_vm.hide_plane_preview()
    
    def _on_fit_range(self) -> None:
        """Handle fit range button click."""
        selected = self._pipeline_vm.selected_item
        if not selected or not selected.actor:
            QMessageBox.warning(self, "Warning", "Please select an item with scalar data.")
            return
        
        if self._vtk_vm.fit_scalar_range(selected.actor):
            self._vtk_vm.update_scalar_bar(selected.actor)
            self._vtk_vm.request_render()
        else:
            QMessageBox.warning(self, "Warning", "No scalar data found for selected item.")
    
    def _on_custom_range(self) -> None:
        """Handle custom range button click."""
        selected = self._pipeline_vm.selected_item
        if not selected or not selected.actor:
            QMessageBox.warning(self, "Warning", "Please select an item with scalar data.")
            return
        
        mapper = selected.actor.GetMapper()
        if not mapper or not mapper.GetScalarVisibility():
            QMessageBox.warning(self, "Warning", "Selected item has no scalar data.")
            return
        
        current_range = mapper.GetScalarRange()
        
        dialog = ScalarRangeDialog(self, current_range[0], current_range[1])
        if dialog.exec() == QDialog.Accepted:
            min_val, max_val = dialog.get_values()
            
            if min_val >= max_val:
                QMessageBox.critical(self, "Error", "Minimum must be less than maximum.")
                return
            
            if not self._vtk_vm.set_custom_scalar_range(selected.actor, min_val, max_val):
                QMessageBox.critical(self, "Error", "Failed to set custom scalar range.")
            else:
                self._vtk_vm.update_scalar_bar(selected.actor)
                self._vtk_vm.request_render()
    
    def _on_camera_view(self) -> None:
        """Handle camera view button click."""
        # Query current state
        state = self._vtk_widget.get_camera_state()
        
        dialog = CameraViewDialog(self, state)
        dialog.apply_requested = lambda s: self._vtk_vm.apply_camera_state(s)
        
        if dialog.exec() == QDialog.Accepted:
            self._vtk_vm.apply_camera_state(dialog.get_state())
    
    def _on_time_series_loaded(self, item) -> None:
        """Handle time series loaded."""
        self._time_manager.set_item(item)
        self._time_animation_widget.update_for_item(
            item.is_time_series,
            item.max_time_index,
            item.current_time_index
        )
    
    def _on_time_step_changed(self, item_id: str, time_index: int) -> None:
        """Handle time step change from time manager."""
        self._pipeline_vm.update_time_step(item_id, time_index)
        self._vtk_vm.request_render()
        
        item = self._pipeline_vm.items.get(item_id)
        if item:
            self._info_page.setPlainText(item.get_info_string())
    
    def _update_time_animation_widget(self, item) -> None:
        """Update time animation widget for selected item."""
        if item and item.is_time_series:
            self._time_manager.set_item(item)
            self._time_animation_widget.update_for_item(
                True,
                item.max_time_index,
                item.current_time_index
            )
        else:
            self._time_manager.set_item(None)
            self._time_animation_widget.update_for_item(False, 0, 0)
    
    def _on_ai_started(self) -> None:
        """Handle AI starting to process/reflect."""
        self._set_ui_enabled(False)
    
    def _on_ai_finished(self) -> None:
        """Handle AI finishing processing."""
        self._set_ui_enabled(True)
    
    def _set_ui_enabled(self, enabled: bool) -> None:
        """Enable or disable overall UI components."""
        self.menuBar().setEnabled(enabled)
        
        # Disable all toolbars
        for toolbar in self.findChildren(QToolBar):
            toolbar.setEnabled(enabled)
            
        self._pipeline_browser.setEnabled(enabled)
        self._details_tabs.setEnabled(enabled)
        self._chat_panel.set_input_enabled(enabled)
        self._vtk_widget.set_interaction_enabled(enabled)
    
    def _on_tab_created(self, tab_id: str, tab_type: str, tab_name: str) -> None:
        """Handle new tab creation request."""
        self.logger.info(f"Creating new tab: type={tab_type}, name={tab_name}, id={tab_id}")
        
        widget = None
        
        if tab_type == "vtk":
            # Create new VTK widget
            widget = VTKWidget()
            # Connect to VTK viewmodel
            self._vtk_vm.render_requested.connect(widget.render)
            self._vtk_vm.actor_added.connect(widget.add_actor)
            self._vtk_vm.actor_removed.connect(widget.remove_actor)
            self._vtk_vm.actor_visibility_changed.connect(widget.set_actor_visibility)
            self._vtk_vm.clear_scene_requested.connect(widget.clear_scene)
            self._vtk_vm.background_changed.connect(widget.set_background)
            self._vtk_vm.camera_reset_requested.connect(widget.reset_camera)
            self._vtk_vm.view_plane_requested.connect(widget.set_view_plane)
            self._vtk_vm.plane_preview_requested.connect(widget.update_plane_preview)
            self._vtk_vm.plane_preview_hide_requested.connect(widget.hide_plane_preview)
            self._vtk_vm.camera_apply_requested.connect(widget.apply_camera_state)
            self._vtk_vm.scalar_bar_update_requested.connect(widget.update_scalar_bar)
            self._vtk_vm.scalar_bar_hide_requested.connect(widget.hide_scalar_bar)
            self._vtk_vm.legend_settings_changed.connect(widget.apply_legend_settings)
            self._chat_vm.render_requested.connect(widget.render)
            
            # Add existing pipeline actors to the new VTK widget
            for item in self._pipeline_vm.items.values():
                if item.actor and item.visible:
                    widget.add_actor(item.actor)
            widget.reset_camera()
            widget.render()
            
        elif tab_type == "table":
            # Create table viewmodel and widget
            table_vm = TableViewModel()
            widget = TableViewWidget(table_vm)
            
        elif tab_type == "graph":
            # Create graph viewmodel and widget
            graph_vm = GraphViewModel()
            widget = GraphViewWidget(graph_vm)
        
        if widget:
            # Add tab to tabbed view (will use tab_id from request)
            actual_tab_id = self._tabbed_view.add_tab_with_id(widget, tab_type, tab_name, pinned=False)
            # Switch to new tab
            index = self._tabbed_view.indexOf(widget)
            self._tabbed_view.setCurrentIndex(index)
            
            # Register tab in PipelineViewModel
            self._pipeline_vm.register_tab(actual_tab_id, tab_name, tab_type, pinned=False)
            
            self.logger.info(f"Tab created successfully: {actual_tab_id}")
        else:
            self.logger.error(f"Failed to create tab of type: {tab_type}")
    
    def _on_tab_closed(self, tab_id: str) -> None:
        """Handle tab closure and clean up resources."""
        self.logger.info(f"Tab closed: {tab_id}")
        
        # Get widget before cleanup to disconnect signals
        widget = self._tabbed_view.get_tab_widget_by_id(tab_id)
        if widget and hasattr(widget, 'render'):  # Likely a VTKWidget
            try:
                self._vtk_vm.render_requested.disconnect(widget.render)
                self._vtk_vm.actor_added.disconnect(widget.add_actor)
                self._vtk_vm.actor_removed.disconnect(widget.remove_actor)
                self._vtk_vm.actor_visibility_changed.disconnect(widget.set_actor_visibility)
                self._vtk_vm.clear_scene_requested.disconnect(widget.clear_scene)
                self._vtk_vm.background_changed.disconnect(widget.set_background)
                self._vtk_vm.camera_reset_requested.disconnect(widget.reset_camera)
                self._vtk_vm.view_plane_requested.disconnect(widget.set_view_plane)
                self._vtk_vm.plane_preview_requested.disconnect(widget.update_plane_preview)
                self._vtk_vm.plane_preview_hide_requested.disconnect(widget.hide_plane_preview)
                self._vtk_vm.camera_apply_requested.disconnect(widget.apply_camera_state)
                self._vtk_vm.scalar_bar_update_requested.disconnect(widget.update_scalar_bar)
                self._vtk_vm.scalar_bar_hide_requested.disconnect(widget.hide_scalar_bar)
                self._vtk_vm.legend_settings_changed.disconnect(widget.apply_legend_settings)
                self.logger.info(f"Disconnected all pipeline signals for VTK tab: {tab_id}")
            except (RuntimeError, TypeError) as e:
                # Signal might not be connected or already disconnected
                self.logger.debug(f"Signal disconnection info for {tab_id}: {e}")
        
        # Cleanup mapping
        if tab_id in self._tab_item_mapping:
            del self._tab_item_mapping[tab_id]
        
        # Unregister from PipelineViewModel
        self._pipeline_vm.unregister_tab(tab_id)

    
    def _create_tab_from_menu(self, tab_type: str, default_name: str) -> None:
        """Create a new tab from menu action."""
        # Generate unique tab name
        existing_tabs = self._tabbed_view.get_all_tabs()
        count = sum(1 for meta in existing_tabs.values() if meta['type'] == tab_type)
        tab_name = f"{default_name} {count + 1}" if count > 0 else default_name
        
        # Generate tab ID
        tab_id = f"tab_{self._tabbed_view._next_tab_id}"
        
        # Trigger tab creation
        self._on_tab_created(tab_id, tab_type, tab_name)
    
    def _get_validated_tab_widget(self, expected_type: TabType):
        """Get active tab widget if it matches expected type, else None."""
        if not self._active_tab_id:
            return None
        widget = self._tabbed_view.get_active_tab_widget()
        if not widget or self._active_tab_type != expected_type:
            return None
        return widget
    
    def _update_table_tab(self, item) -> None:
        """Update active table tab with item data."""
        widget = self._get_validated_tab_widget(TabType.TABLE)
        if not widget:
            return
        
        # Load all arrays from the item
        success = widget.viewmodel.set_data_source(item.id, "POINT")
        if not success:
            widget.clear_data()
        
    def _update_graph_tab(self, item) -> None:
        """Update active graph tab with item data."""
        widget = self._get_validated_tab_widget(TabType.GRAPH)
        if not widget:
            return
            
        data_arrays = item.get_data_arrays()
        if not data_arrays:
            widget.clear_data()
            return
            
        y_array, array_type, _ = data_arrays[0]
        x_array = "__Index__"
        widget.viewmodel.set_data_source(item.id, x_array, y_array, array_type)

    def _clear_active_tab_display(self) -> None:
        """Clear the display of the current active tab."""
        if self._active_tab_type == TabType.VTK:
            self._properties_panel.set_item(None)
            self._vtk_vm.hide_scalar_bar()
            self._vtk_vm.hide_plane_preview()
        elif self._active_tab_type in (TabType.TABLE, TabType.GRAPH):
            widget = self._tabbed_view.get_active_tab_widget()
            if widget:
                widget.clear_data()

    def _on_tab_changed(self, index: int) -> None:
        """Handle active tab change."""
        if index < 0:
            self._active_tab_id = None
            self._active_tab_type = TabType.VTK
            return
            
        widget = self._tabbed_view.widget(index)
        metadata = self._tabbed_view.get_metadata_by_widget(widget)
        
        if metadata:
            self._active_tab_id = metadata['id']
            self._active_tab_type = metadata['type']
            self.logger.info(f"Active tab changed: {self._active_tab_id} ({self._active_tab_type})")
            
            # Update overall UI for current tab
            self._update_for_active_tab()
    
    def _update_for_active_tab(self) -> None:
        """Update overall UI state based on active tab type."""
        # Update Properties Panel mode
        if hasattr(self, "_properties_panel"):
            self._properties_panel.set_tab_type(self._active_tab_type)
            
        # If we have a selected item, ensure it's displayed in the current tab
        selected_item = self._pipeline_vm.selected_item
        if selected_item:
            # Re-trigger selection change logic to update the current tab's specific view
            self._on_selection_changed(selected_item)
        else:
            self._clear_active_tab_display()

    # ==================== Tab Management Handlers (From PipelineVM signals) ====================
    
    def _handle_vtk_view_request(self, tab_name: str) -> None:
        """Handle VTK render view creation request from PipelineViewModel."""
        from views.vtk_widget import VTKWidget
        
        # Create VTK widget
        widget = VTKWidget()
        
        # Connect VTK VM signals
        self._vtk_vm.render_requested.connect(widget.render)
        self._vtk_vm.camera_reset_requested.connect(widget.reset_camera)
        self._vtk_vm.plane_preview_requested.connect(widget.update_plane_preview)
        self._vtk_vm.plane_preview_hide_requested.connect(widget.hide_plane_preview)
        self._vtk_vm.camera_apply_requested.connect(widget.apply_camera_state)
        self._vtk_vm.scalar_bar_update_requested.connect(widget.update_scalar_bar)
        self._vtk_vm.scalar_bar_hide_requested.connect(widget.hide_scalar_bar)
        self._vtk_vm.legend_settings_changed.connect(widget.apply_legend_settings)
        self._chat_vm.render_requested.connect(widget.render)
        
        # Add existing pipeline actors
        for item in self._pipeline_vm.items.values():
            if item.actor and item.visible:
                widget.add_actor(item.actor)
        widget.reset_camera()
        widget.render()
        
        # Add to tabbed view
        tab_id = self._tabbed_view.add_tab_with_id(widget, "vtk", tab_name, pinned=False)
        
        # Register tab
        self._pipeline_vm.register_tab(tab_id, tab_name, "vtk", pinned=False)
        
        # Switch to new tab
        index = self._tabbed_view.indexOf(widget)
        self._tabbed_view.setCurrentIndex(index)
        
        self.logger.info(f"VTK view created via signal: {tab_id}")
    
    def _handle_table_view_request(self, item_id: str, tab_name: str, array_type: str) -> None:
        """Handle table view creation request from PipelineViewModel."""
        from viewmodels.table_viewmodel import TableViewModel
        from views.table_view_widget import TableViewWidget
        
        table_vm = TableViewModel()
        success = table_vm.set_data_source(item_id, array_type)
        
        if not success:
            self.logger.error(f"Failed to create table view for item '{item_id}'")
            return
        
        widget = TableViewWidget(table_vm)
        tab_id = self._tabbed_view.add_tab_with_id(widget, "table", tab_name, pinned=False)
        
        # Register tab
        self._pipeline_vm.register_tab(tab_id, tab_name, "table", pinned=False)
        
        # Switch to new tab
        index = self._tabbed_view.indexOf(widget)
        self._tabbed_view.setCurrentIndex(index)
        
        self.logger.info(f"Table view created via signal: {tab_id}")
    
    def _handle_graph_view_request(self, graph_type: str, item_id: str, y_array: str,
                                    x_array: str, tab_name: str, array_type: str) -> None:
        """Handle graph view creation request from PipelineViewModel."""
        from viewmodels.graph_viewmodel import GraphViewModel
        from views.graph_view_widget import GraphViewWidget
        
        graph_vm = GraphViewModel()
        graph_vm.set_graph_type(graph_type)
        success = graph_vm.set_data_source(item_id, x_array, y_array, array_type)
        
        if not success:
            self.logger.error(f"Failed to create graph view: data not found")
            return
        
        widget = GraphViewWidget(graph_vm)
        tab_id = self._tabbed_view.add_tab_with_id(widget, "graph", tab_name, pinned=False)
        
        # Register tab
        self._pipeline_vm.register_tab(tab_id, tab_name, "graph", pinned=False)
        
        # Switch to new tab
        index = self._tabbed_view.indexOf(widget)
        self._tabbed_view.setCurrentIndex(index)
        
        self.logger.info(f"Graph view created via signal: {tab_id}")
    
    def _handle_tab_close_request(self, tab_id: str) -> None:
        """Handle tab close request from PipelineViewModel."""
        metadata = self._tabbed_view.get_tab_metadata(tab_id)
        if not metadata:
            self.logger.warning(f"Tab not found: {tab_id}")
            return
        
        if metadata.get('pinned', False):
            self.logger.warning(f"Cannot close pinned tab: {tab_id}")
            return
        
        self._tabbed_view.close_tab_by_id(tab_id)
        self.logger.info(f"Tab closed via signal: {tab_id}")
    
    def _handle_tab_pin_request(self, tab_id: str, pinned: bool) -> None:
        """Handle tab pin/unpin request from PipelineViewModel."""
        success = self._tabbed_view.set_tab_pinned(tab_id, pinned)
        if success:
            action = "pinned" if pinned else "unpinned"
            self.logger.info(f"Tab {action} via signal: {tab_id}")
        else:
            self.logger.warning(f"Failed to modify pin status for tab: {tab_id}")
