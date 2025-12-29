from PySide6.QtWidgets import (QMainWindow, QSplitter, QTabWidget, QTextEdit,
                               QMenu, QToolButton, QFileDialog, QMessageBox, QToolBar,
                               QDialog, QDialogButtonBox, QFormLayout, QDoubleSpinBox)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt

from views.vtk_widget import VTKWidget
from views.pipeline_browser import PipelineBrowserWidget
from views.properties_panel import PropertiesPanel
from views.chat_panel import ChatPanel
from views.time_animation_widget import TimeAnimationWidget
from viewmodels.pipeline_viewmodel import PipelineViewModel
from viewmodels.vtk_viewmodel import VTKViewModel
from viewmodels.chat_viewmodel import ChatViewModel
from viewmodels.time_series_manager import TimeSeriesManager
from models.properties_context import PropertiesPanelContext
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


class MainWindow(QMainWindow):
    """Main application window - orchestrates views and viewmodels."""
    
    def __init__(self, pipeline_vm: PipelineViewModel, vtk_vm: VTKViewModel, chat_vm: ChatViewModel):
        super().__init__()
        self._pipeline_vm = pipeline_vm
        self._vtk_vm = vtk_vm
        self._chat_vm = chat_vm
        self._time_manager = TimeSeriesManager(self)
        
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
        toolbar = self.addToolBar("View Controls")
        
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
        
        self._vtk_widget = VTKWidget()
        main_splitter.addWidget(self._vtk_widget)
        
        self._chat_panel = ChatPanel()
        main_splitter.addWidget(self._chat_panel)
        
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 5)
        main_splitter.setStretchFactor(2, 2)
        main_splitter.setSizes([350, 750, 300])
    
    def _connect_signals(self) -> None:
        """Connect all signals between views and viewmodels."""
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
        self._chat_vm.message_added.connect(
            lambda msg: self._chat_panel.append_message(msg.sender, msg.content)
        )
        self._chat_vm.streaming_started.connect(self._chat_panel.start_streaming)
        self._chat_vm.streaming_token.connect(self._chat_panel.update_streaming)
        self._chat_vm.streaming_finished.connect(self._chat_panel.finish_streaming)
        self._chat_vm.tool_activity.connect(self._chat_panel.add_tool_activity)
        self._chat_vm.render_requested.connect(self._vtk_widget.render)
        self._chat_vm.conversation_cleared.connect(self._chat_panel.clear_display)
        
        self._chat_vm.streaming_started.connect(self._on_ai_started)
        self._chat_vm.streaming_finished.connect(self._on_ai_finished)
        
        self._vtk_vm.render_requested.connect(self._vtk_widget.render)
        self._vtk_vm.actor_added.connect(self._vtk_widget.add_actor)
        self._vtk_vm.actor_removed.connect(self._vtk_widget.remove_actor)
        self._vtk_vm.actor_visibility_changed.connect(self._vtk_widget.set_actor_visibility)
        self._vtk_vm.clear_scene_requested.connect(self._vtk_widget.clear_scene)
        self._vtk_vm.background_changed.connect(self._vtk_widget.set_background)
        self._vtk_vm.camera_reset_requested.connect(self._vtk_widget.reset_camera)
        self._vtk_vm.view_plane_requested.connect(self._vtk_widget.set_view_plane)
        self._vtk_vm.plane_preview_requested.connect(self._vtk_widget.update_plane_preview)
        self._vtk_vm.plane_preview_hide_requested.connect(self._vtk_widget.hide_plane_preview)
        self._vtk_vm.scalar_bar_update_requested.connect(self._vtk_widget.update_scalar_bar)
        self._vtk_vm.scalar_bar_hide_requested.connect(self._vtk_widget.hide_scalar_bar)
        self._vtk_vm.legend_settings_changed.connect(self._vtk_widget.apply_legend_settings)
        
        self._time_manager.time_changed.connect(self._on_time_step_changed)
    
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
            self._update_properties_panel(item)
            self._info_page.setPlainText(item.get_info_string())
            self._update_time_animation_widget(item)
        else:
            self._properties_panel.set_item(None)
            self._info_page.setPlainText("")
            self._vtk_vm.hide_plane_preview()
            self._vtk_vm.hide_scalar_bar()
            self._time_manager.set_item(None)
            self._time_animation_widget.reset()
    
    def _on_browser_selection(self, item_id: str) -> None:
        """Handle browser selection."""
        self._pipeline_vm.select_item(item_id if item_id else None)
    
    def _on_visibility_changed(self, item_id: str, visible: bool) -> None:
        """Handle visibility toggle."""
        self._pipeline_vm.set_visibility(item_id, visible)
        item = self._pipeline_vm.items.get(item_id)
        if item and item.actor:
            self._vtk_vm.set_actor_visibility(item.actor, visible)
    
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
        
        self._properties_panel.set_item(
            item, ctx.style, ctx.data_arrays, ctx.current_array, ctx.current_component,
            ctx.scalar_visible, parent_bounds
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
