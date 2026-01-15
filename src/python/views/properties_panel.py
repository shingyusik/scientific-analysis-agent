from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QGroupBox, 
                               QFormLayout, QHBoxLayout, QLabel, QPushButton,
                               QSlider, QSpinBox, QComboBox, QCheckBox,
                               QDoubleSpinBox, QColorDialog, QStackedWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional, List, Tuple, TYPE_CHECKING
from models.pipeline_item import PipelineItem
from views.common_widgets import ScientificDoubleSpinBox
from utils.constants import DEFAULT_LEGEND_SETTINGS, RESET_BUTTON_WIDTH, SPINBOX_WIDTH
from views.table_properties_widget import TablePropertiesWidget
from views.graph_properties_widget import GraphPropertiesWidget
from models.tab_types import TabType

if TYPE_CHECKING:
    from services.vtk_render_service import VTKRenderService


class PropertiesPanel(QWidget):
    """Panel for displaying and editing item properties."""
    
    apply_filter_requested = Signal(str)  # item_id
    delete_requested = Signal(str)  # item_id
    opacity_changed = Signal(str, float)  # item_id, value
    point_size_changed = Signal(str, float)  # item_id, value
    line_width_changed = Signal(str, float)  # item_id, value
    gaussian_scale_changed = Signal(str, float)  # item_id, value
    representation_style_changed = Signal(str, str)  # item_id, style
    color_by_changed = Signal(str, str, str, str)  # item_id, array_name, array_type, component
    filter_params_changed = Signal(str, dict)  # item_id, params (general purpose)
    legend_settings_changed = Signal(dict)  # legend settings dictionary
    custom_range_requested = Signal()  # Request custom range dialog
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: Optional[PipelineItem] = None
        self._current_style: str = "Surface"
        self._data_arrays: List[Tuple[str, str]] = []
        self._parent_bounds: Optional[Tuple[float, ...]] = None
        self._render_service: Optional["VTKRenderService"] = None
        self._filter_widget: Optional[QWidget] = None
        self._legend_settings: dict = DEFAULT_LEGEND_SETTINGS.copy()
        self._pending_changes = {}  # Store pending changes for batch apply
        
        self._active_tab_type: TabType = TabType.VTK  # Default
        
        # Signal connection tracking
        self._camera_signal_connected = False
        self._bg_combo_ref = None  # Reference to track background combo connection
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Action buttons (Always visible)
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(4, 4, 4, 4)
        btn_row.setSpacing(4)
        
        self._apply_btn = QPushButton("Apply")
        self._apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover:enabled { background-color: #34495e; }
            QPushButton:pressed:enabled { background-color: #1a252f; }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """)
        self._apply_btn.setCursor(Qt.PointingHandCursor)
        self._apply_btn.clicked.connect(self._on_apply_clicked)
        self._apply_btn.setEnabled(False)
        btn_row.addWidget(self._apply_btn)
        
        self._delete_btn = QPushButton("Delete")
        self._delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover:enabled { background-color: #e74c3c; }
            QPushButton:pressed:enabled { background-color: #a93226; }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """)
        self._delete_btn.setCursor(Qt.PointingHandCursor)
        self._delete_btn.clicked.connect(self._on_delete_clicked)
        self._delete_btn.setEnabled(False)
        btn_row.addWidget(self._delete_btn)
        
        main_layout.addLayout(btn_row)
        
        # Stacked widget for different property types
        self._stacked_widget = QStackedWidget()
        
        # 1. VTK Properties (Scroll Area)
        self._vtk_scroll = QScrollArea()
        self._vtk_scroll.setWidgetResizable(True)
        self._vtk_content = QWidget()
        self._vtk_layout = QVBoxLayout(self._vtk_content)
        self._vtk_layout.setAlignment(Qt.AlignTop)
        self._vtk_scroll.setWidget(self._vtk_content)
        self._stacked_widget.addWidget(self._vtk_scroll) # Index 0
        
        # 2. Table Properties
        self._table_props = TablePropertiesWidget()
        self._table_props_scroll = QScrollArea()
        self._table_props_scroll.setWidgetResizable(True)
        self._table_props_scroll.setWidget(self._table_props)
        self._stacked_widget.addWidget(self._table_props_scroll) # Index 1
        
        # 3. Graph Properties
        self._graph_props = GraphPropertiesWidget()
        self._graph_props.graph_updated.connect(lambda: self._apply_btn.setEnabled(True))
        self._graph_props_scroll = QScrollArea()
        self._graph_props_scroll.setWidgetResizable(True)
        self._graph_props_scroll.setWidget(self._graph_props)
        self._stacked_widget.addWidget(self._graph_props_scroll) # Index 2
        
        main_layout.addWidget(self._stacked_widget)
    
    def set_render_service(self, render_service: "VTKRenderService") -> None:
        """Set the render service for creating filter widgets."""
        self._render_service = render_service
    
    def set_tab_type(self, tab_type: TabType) -> None:
        """Switch the property interface based on tab type."""
        self._active_tab_type = tab_type
        if tab_type == TabType.VTK:
            self._stacked_widget.setCurrentIndex(0)
        elif tab_type == TabType.TABLE:
            self._stacked_widget.setCurrentIndex(1)
        elif tab_type == TabType.GRAPH:
            self._stacked_widget.setCurrentIndex(2)
            
    def set_item(self, item: Optional[PipelineItem], style: str = "Surface",
                 data_arrays: List[Tuple[str, str]] = None, 
                 current_array: str = None, current_component: str = None,
                 scalar_visible: bool = False,
                 parent_bounds: Tuple[float, ...] = None,
                 viewmodel = None) -> None:
        """Set the current item and update the active property interface."""
        self._current_item = item
        self._current_style = style
        self._data_arrays = data_arrays or []
        self._parent_bounds = parent_bounds
        
        # Reset pending changes on item switch
        self._pending_changes = {}
        
        # Update universal buttons
        self._delete_btn.setEnabled(item is not None)
        
        # Apply button: enable for filters that haven't been applied yet (apply_immediately=False)
        should_enable_apply = False
        if item and "filter" in item.item_type:
            import filters
            filter_class = filters.get_filter(item.item_type)
            if filter_class and self._render_service:
                filter_instance = filter_class(self._render_service)
                # If filter doesn't apply immediately and vtk_data is same as parent's data,
                # it means the filter hasn't been applied yet
                if not filter_instance.apply_immediately:
                    should_enable_apply = True
        self._apply_btn.setEnabled(should_enable_apply)
        
        if self._active_tab_type == TabType.VTK:
             # Store ViewModel reference for VTK properties
             self._vtk_vm_ref = viewmodel
        else:
             self._vtk_vm_ref = None
        
        if self._active_tab_type == TabType.VTK:
            self._rebuild_vtk_ui(current_array, current_component, scalar_visible)
        elif self._active_tab_type == TabType.TABLE:
            self._table_props.set_item(item, viewmodel)
        elif self._active_tab_type == TabType.GRAPH:
            self._graph_props.set_item(item, viewmodel)
    
    def _clear_vtk_layout(self) -> None:
        """Clear all widgets from the VTK layout."""
        # Disconnect signals BEFORE deleting widgets to prevent RuntimeError
        if self._camera_signal_connected and hasattr(self, '_vtk_vm_ref') and self._vtk_vm_ref:
            try:
                self._vtk_vm_ref.camera_state_changed.disconnect(self._update_camera_inputs)
            except (TypeError, RuntimeError):
                pass
            self._camera_signal_connected = False
        
        # Disconnect background combo signal
        if self._bg_combo_ref is not None and hasattr(self, '_vtk_vm_ref') and self._vtk_vm_ref:
            try:
                # Check if the Qt object is still valid before disconnect
                self._bg_combo_ref.objectName()  # This will raise RuntimeError if deleted
                self._vtk_vm_ref.background_preset_changed.disconnect(self._bg_combo_ref.setCurrentText)
            except (TypeError, RuntimeError):
                pass
            self._bg_combo_ref = None
        
        # Clear spinbox references to prevent access after deletion
        self._cam_pos_spins = []
        self._cam_focal_spins = []
        self._cam_up_spins = []
        self._cam_zoom_spin = None
        
        while self._vtk_layout.count():
            child = self._vtk_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _rebuild_vtk_ui(self, current_array: str = None, current_component: str = None, 
                    scalar_visible: bool = False) -> None:
        """Rebuild the VTK properties UI."""
        self._clear_vtk_layout()
        self._filter_widget = None
        
        if not self._current_item:
            self._vtk_layout.addWidget(QLabel("No item selected."))
            return
        
        item = self._current_item
        
        # For filters without actor yet (apply_immediately=False), show filter params first
        if "filter" in item.item_type:
            self._add_filter_params_section(item)
        
        if not item.actor:
            if "filter" not in item.item_type:
                self._vtk_layout.addWidget(QLabel("No 3D styling available for this source."))
            self._vtk_layout.addStretch()
            return
        
        if self._data_arrays:
            self._add_coloring_and_range_section(current_array, current_component, scalar_visible)
        
        self._add_view_controls_section()
        self._add_styling_section()
        
        if self._data_arrays:
            legend_enabled = scalar_visible and item.visible
            self._add_legend_section(legend_enabled)
        
        self._vtk_layout.addStretch()
        
    def _add_view_controls_section(self) -> None:
        """Add global view controls (Camera, Env)."""
        group = QGroupBox("View Controls")
        layout = QFormLayout(group)
        
        if not self._current_item or not hasattr(self, '_vtk_vm_ref') or not self._vtk_vm_ref:
            pass

        # Camera Controls (Detailed)
        # Position
        pos_row = QHBoxLayout()
        self._cam_pos_spins = [ScientificDoubleSpinBox() for _ in range(3)]
        for spin in self._cam_pos_spins:
            spin.setRange(-1e9, 1e9)
            pos_row.addWidget(spin)
        layout.addRow("Camera Pos:", pos_row)

        # Focal Point
        focal_row = QHBoxLayout()
        self._cam_focal_spins = [ScientificDoubleSpinBox() for _ in range(3)]
        for spin in self._cam_focal_spins:
            spin.setRange(-1e9, 1e9)
            focal_row.addWidget(spin)
        layout.addRow("Focal Point:", focal_row)

        # View Up
        up_row = QHBoxLayout()
        self._cam_up_spins = [ScientificDoubleSpinBox() for _ in range(3)]
        for spin in self._cam_up_spins:
            spin.setRange(-1.0, 1.0)
            spin.setSingleStep(0.1)
            up_row.addWidget(spin)
        layout.addRow("View Up:", up_row)
        
        # Zoom (Angle?) - VTK usually uses different params for zoom. 
        # But 'set_camera_view' tool uses 'zoom' factor. 
        # Let's check get_camera_state returns. It returns pos, focal, up, zoom.
        # So we add a Zoom spinbox.
        zoom_row = QHBoxLayout()
        self._cam_zoom_spin = ScientificDoubleSpinBox()
        self._cam_zoom_spin.setRange(0.001, 1000.0) # Zoom factor
        self._cam_zoom_spin.setValue(1.0)
        zoom_row.addWidget(self._cam_zoom_spin)
        layout.addRow("Zoom:", zoom_row)

        # Connect signals
        # Connect signals
        if self._vtk_vm_ref:
             # Update inputs from ViewModel state change (no disconnect needed here, done in _clear_vtk_layout)
            self._vtk_vm_ref.camera_state_changed.connect(self._update_camera_inputs)
            self._camera_signal_connected = True
            
            # Queue changes
            def queue_camera_change():
                state = {
                    "position": [s.value() for s in self._cam_pos_spins],
                    "focal_point": [s.value() for s in self._cam_focal_spins],
                    "view_up": [s.value() for s in self._cam_up_spins],
                    "zoom": self._cam_zoom_spin.value()
                }
                self._pending_changes["camera"] = state
                self._apply_btn.setEnabled(True)

            for spin in self._cam_pos_spins + self._cam_focal_spins + self._cam_up_spins + [self._cam_zoom_spin]:
                spin.valueChanged.connect(lambda: queue_camera_change())

            # Initial Query
            self._vtk_vm_ref.request_camera_query()

        # Background
        if self._vtk_vm_ref:
            bg_combo = QComboBox()
            bg_combo.addItems([p[0] for p in self._vtk_vm_ref.BACKGROUND_PRESETS])
            # Set current
            current_bg = self._vtk_vm_ref._current_background[0]
            bg_combo.setCurrentText(current_bg)
            
            bg_combo.currentTextChanged.connect(lambda t: [
                self._pending_changes.update({"background": t}),
                self._apply_btn.setEnabled(True)
            ])
            # Store reference and connect (disconnect done in _clear_vtk_layout)
            self._bg_combo_ref = bg_combo
            self._vtk_vm_ref.background_preset_changed.connect(bg_combo.setCurrentText)
            
            layout.addRow("Background:", bg_combo)
            
        self._vtk_layout.addWidget(group)
        
    def _update_camera_inputs(self, state: dict) -> None:
        """Update camera inputs from state dictionary."""
        # Safety check: ensure widgets exist
        if not hasattr(self, '_cam_pos_spins') or not self._cam_pos_spins:
            return
            
        # Block signals to prevent feedback loop
        all_spins = self._cam_pos_spins + self._cam_focal_spins + self._cam_up_spins + [self._cam_zoom_spin]
        
        # Check if C++ objects are still valid
        for spin in all_spins:
            try:
                # Accessing any property will raise RuntimeError if deleted
                spin.objectName()
            except RuntimeError:
                return

        for spin in all_spins:
            spin.blockSignals(True)
            
        try:
            if "position" in state:
                for i, val in enumerate(state["position"]):
                    self._cam_pos_spins[i].setValue(val)
            if "focal_point" in state:
                for i, val in enumerate(state["focal_point"]):
                    self._cam_focal_spins[i].setValue(val)
            if "view_up" in state:
                for i, val in enumerate(state["view_up"]):
                    self._cam_up_spins[i].setValue(val)
            if "zoom" in state:
                self._cam_zoom_spin.setValue(state["zoom"])
        finally:
            for spin in all_spins:
                try:
                    spin.blockSignals(False)
                except RuntimeError:
                    pass
    
    def _add_filter_params_section(self, item: PipelineItem) -> None:
        """Add filter parameters section using the filter registry."""
        import filters
        
        filter_class = filters.get_filter(item.item_type)
        if not filter_class or not self._render_service:
            return
        
        filter_instance = filter_class(self._render_service)
        
        def on_params_changed(item_id: str, params: dict):
            self._pending_changes["filter_params"] = (item_id, params)
            self._apply_btn.setEnabled(True)
        
        widget = filter_instance.create_params_widget(
            self._vtk_content, item, self._parent_bounds, on_params_changed
        )
        
        if widget:
            self._filter_widget = widget
            self._vtk_layout.addWidget(widget)
    
    def _add_coloring_and_range_section(self, current_array: str, current_component: str, 
                               scalar_visible: bool) -> None:
        """Add coloring and range controls."""
        group = QGroupBox("Coloring & Range")
        layout = QVBoxLayout(group)
        
        self._add_coloring_controls(layout, current_array, current_component, scalar_visible)
        self._add_range_controls(layout)
        
        self._vtk_layout.addWidget(group)

    def _add_coloring_controls(self, layout: QVBoxLayout, current_array: str, 
                             current_component: str, scalar_visible: bool) -> None:
        """Add coloring controls (Color By, Component)."""
        color_row = QHBoxLayout()
        main_combo = QComboBox()
        main_combo.addItem("Solid Color", ("__SolidColor__", None, None))
        
        component_combo = QComboBox()
        component_combo.addItem("Magnitude", "Magnitude")
        component_combo.setEnabled(False)
        
        current_main_idx = 0
        saved_component = current_component if current_component else "Magnitude"
        
        for idx, (name, type_, num_components) in enumerate(self._data_arrays):
            if num_components > 1:
                main_combo.addItem(f"{name} ({type_})", (name, type_, num_components))
            else:
                main_combo.addItem(f"{name} ({type_})", (name, type_, None))
            
            if scalar_visible and name == current_array:
                current_main_idx = idx + 1
        
        main_combo.setCurrentIndex(current_main_idx)
        
        def update_component_combo(idx: int, component_to_select: str = None):
            component_combo.blockSignals(True)
            data = main_combo.itemData(idx)
            if data and data[0] == "__SolidColor__":
                component_combo.clear()
                component_combo.addItem("Magnitude", "Magnitude")
                component_combo.setEnabled(False)
            elif data and data[2] and data[2] > 1:
                component_combo.clear()
                component_combo.addItem("Magnitude", "Magnitude")
                component_combo.addItem("X", "X")
                component_combo.addItem("Y", "Y")
                if data[2] >= 3:
                    component_combo.addItem("Z", "Z")
                component_combo.setEnabled(True)
                
                component_idx = 0
                target_component = component_to_select if component_to_select else saved_component
                if target_component:
                    for i in range(component_combo.count()):
                        if component_combo.itemData(i) == target_component:
                            component_idx = i
                            break
                component_combo.setCurrentIndex(component_idx)
            else:
                component_combo.clear()
                component_combo.addItem("Magnitude", "Magnitude")
                component_combo.setEnabled(False)
            component_combo.blockSignals(False)
        
        def on_main_combo_changed():
            idx = main_combo.currentIndex()
            data = main_combo.itemData(idx)
            if data and data[2] and data[2] > 1:
                update_component_combo(idx, saved_component)
            else:
                update_component_combo(idx)
            on_selection_changed()
        
        def on_selection_changed():
            if not self._current_item:
                return
            main_data = main_combo.itemData(main_combo.currentIndex())
            
            self._pending_changes["color_by"] = None # Reset
            
            if main_data[0] == "__SolidColor__":
                self._pending_changes["color_by"] = (self._current_item.id, "__SolidColor__", "POINT", "")
            else:
                name, type_, num_components = main_data
                if num_components and num_components > 1:
                    component = component_combo.itemData(component_combo.currentIndex())
                    self._pending_changes["color_by"] = (self._current_item.id, name, type_, component)
                else:
                    self._pending_changes["color_by"] = (self._current_item.id, name, type_, "")
            
            self._apply_btn.setEnabled(True)
        
        main_combo.currentIndexChanged.connect(on_main_combo_changed)
        component_combo.currentIndexChanged.connect(on_selection_changed)
        
        update_component_combo(current_main_idx, saved_component)
        
        color_row.addWidget(main_combo)
        color_row.addWidget(component_combo)
        layout.addLayout(color_row)

    def _add_range_controls(self, layout: QVBoxLayout) -> None:
        """Add range controls (Fit Range, Custom Range)."""
        range_layout = QFormLayout()
        
        # Fit Range Button
        btn_fit = QPushButton("Fit Range")
        def on_fit_clicked():
            if self._vtk_vm_ref and self._current_item and self._current_item.actor:
                rng = self._vtk_vm_ref.get_data_scalar_range(self._current_item.actor)
                if rng:
                    # Update spinboxes, which triggers valueChanged -> pending_changes
                    self._range_min_spin.setValue(rng[0])
                    self._range_max_spin.setValue(rng[1])
        btn_fit.clicked.connect(on_fit_clicked)
        range_layout.addRow("", btn_fit)
        
        # Custom Range Min/Max
        custom_range_row = QHBoxLayout()
        self._range_min_spin = ScientificDoubleSpinBox()
        self._range_min_spin.setRange(-1e30, 1e30)
        self._range_max_spin = ScientificDoubleSpinBox()
        self._range_max_spin.setRange(-1e30, 1e30)
        
        # Get current range from actor if available
        if self._current_item and self._current_item.actor:
            mapper = self._current_item.actor.GetMapper()
            if mapper:
                current_range = mapper.GetScalarRange()
                self._range_min_spin.setValue(current_range[0])
                self._range_max_spin.setValue(current_range[1])
        
        def on_custom_range_changed():
            self._pending_changes["custom_range"] = (
                self._range_min_spin.value(),
                self._range_max_spin.value()
            )
            self._apply_btn.setEnabled(True)
        
        self._range_min_spin.valueChanged.connect(on_custom_range_changed)
        self._range_max_spin.valueChanged.connect(on_custom_range_changed)
        
        custom_range_row.addWidget(QLabel("Min:"))
        custom_range_row.addWidget(self._range_min_spin)
        custom_range_row.addWidget(QLabel("Max:"))
        custom_range_row.addWidget(self._range_max_spin)
        range_layout.addRow("Custom Range:", custom_range_row)
        
        layout.addLayout(range_layout)
    
    def _on_apply_clicked(self) -> None:
        """Handle apply button click."""
        if not self._current_item:
            return
            
        if self._active_tab_type == TabType.VTK:
            if not self._vtk_vm_ref:
                return
                
            changes = self._pending_changes
            
            # Apply Filter Parameters
            if "filter_params" in changes:
                item_id, params = changes["filter_params"]
                self.filter_params_changed.emit(item_id, params)
            
            # Trigger Filter Commit (if filter)
            if "filter" in self._current_item.item_type:
                self.apply_filter_requested.emit(self._current_item.id)
            
            # Camera
            if "camera" in changes:
                self._vtk_vm_ref.apply_camera_state(changes["camera"])
            
            # Background
            if "background" in changes:
                self._vtk_vm_ref.set_background_preset(changes["background"])
                
            # Representation (per-item, not global)
            if "representation" in changes:
                self.representation_style_changed.emit(self._current_item.id, changes["representation"])
                
            # Color By
            if "color_by" in changes and changes["color_by"]:
                item_id, name, type_, component = changes["color_by"]
                self.color_by_changed.emit(item_id, name, type_, component)
            
            # Opacity
            if "opacity" in changes:
                self.opacity_changed.emit(self._current_item.id, changes["opacity"])
                
            # Point Size
            if "point_size" in changes:
                self.point_size_changed.emit(self._current_item.id, changes["point_size"])
                
            # Line Width
            if "line_width" in changes:
                self.line_width_changed.emit(self._current_item.id, changes["line_width"])
                
            # Gaussian Scale
            if "gaussian_scale" in changes:
                self.gaussian_scale_changed.emit(self._current_item.id, changes["gaussian_scale"])
                
            # Legend
            if "legend" in changes:
                self.legend_settings_changed.emit(changes["legend"])
            
            # Custom Scalar Range
            if "custom_range" in changes:
                min_val, max_val = changes["custom_range"]
                if self._current_item and self._current_item.actor:
                    self._vtk_vm_ref.set_custom_scalar_range(
                        self._current_item.actor, min_val, max_val
                    )
                    self._vtk_vm_ref.update_scalar_bar(self._current_item.actor)
                    self._vtk_vm_ref.request_render()
            
            self._pending_changes = {}
            self._apply_btn.setEnabled(False)
            
        elif self._active_tab_type == TabType.GRAPH:
            # Delegate to graph widget
            self._graph_props.apply_changes()
        elif self._active_tab_type == TabType.TABLE:
            pass
    
    def update_representation_indicator(self, style: str) -> None:
        """Update representation combobox without triggering signals."""
        idx = self._rep_combo.findText(style)
        if idx >= 0:
            self._rep_combo.blockSignals(True)
            self._rep_combo.setCurrentIndex(idx)
            self._rep_combo.blockSignals(False)
    
    def update_representation_style(self, style: str) -> None:
        """Update representation style and rebuild VTK UI to show appropriate controls.
        
        This method should be called when the representation style changes externally
        (e.g., from toolbar or programmatically) to ensure the Properties Panel
        displays the correct controls for the new representation style.
        """
        if self._active_tab_type != TabType.VTK:
            return
            
        # Update internal state
        self._current_style = style
        
        # Rebuild VTK UI to show appropriate controls for the new style
        if self._current_item and self._current_item.actor:
            # Get current coloring state to preserve it
            current_array = None
            current_component = None
            scalar_visible = False
            
            if self._current_item.actor:
                mapper = self._current_item.actor.GetMapper()
                if mapper and mapper.GetScalarVisibility():
                    scalar_visible = True
                    # Try to get current array name from mapper
                    if hasattr(mapper, 'GetArrayName'):
                        current_array = mapper.GetArrayName()
            
            # Rebuild the UI
            self._rebuild_vtk_ui(current_array, current_component, scalar_visible)
            
    def _on_delete_clicked(self) -> None:
        """Handle delete button click."""
        if self._current_item:
            self.delete_requested.emit(self._current_item.id)
    
    def _add_styling_section(self) -> None:
        """Add styling controls section."""
        group = QGroupBox("Styling")
        layout = QFormLayout(group)
        
        # 1. Opacity control (First)
        self._add_opacity_control(layout)
        
        # 2. Representation control (Second)
        if self._vtk_vm_ref:
            self._rep_combo = QComboBox()
            self._rep_combo.addItems(self._vtk_vm_ref.REPRESENTATION_STYLES)
            # Set current representation from _current_style
            self._rep_combo.setCurrentText(self._current_style)
            
            # Trigger UI update immediately, but defer application to Apply button
            def on_rep_changed(style):
                # 1. Update internal UI state immediately to show relevant controls
                self.update_representation_style(style)
                
                # 2. Queue the change for application
                self._pending_changes["representation"] = style
                self._apply_btn.setEnabled(True)
            
            self._rep_combo.currentTextChanged.connect(on_rep_changed)
            
            layout.addRow("Representation:", self._rep_combo)
        
        # 3. Style-specific controls (Last)
        if self._current_style == "Points":
            self._add_point_size_control(layout)
        elif self._current_style in ["Wireframe", "Surface With Edges"]:
            self._add_line_width_control(layout)
        elif self._current_style == "Point Gaussian":
            self._add_gaussian_scale_control(layout)
        
        self._vtk_layout.addWidget(group)
    
    def _add_opacity_control(self, layout: QFormLayout) -> None:
        """Add opacity slider and spinbox."""
        if not self._current_item or not self._current_item.actor:
            return
        
        current_opacity = int(self._current_item.actor.GetProperty().GetOpacity() * 100)
        if "opacity" in self._pending_changes:
            current_opacity = int(self._pending_changes["opacity"] * 100)
        
        row = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(current_opacity)
        
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setSuffix("%")
        spin.setValue(current_opacity)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(RESET_BUTTON_WIDTH)
        
        def update_opacity(val):
            slider.blockSignals(True)
            spin.blockSignals(True)
            slider.setValue(val)
            spin.setValue(val)
            slider.blockSignals(False)
            spin.blockSignals(False)
            self._pending_changes["opacity"] = val / 100.0
            self._apply_btn.setEnabled(True)
        
        slider.valueChanged.connect(update_opacity)
        spin.valueChanged.connect(update_opacity)
        reset_btn.clicked.connect(lambda: update_opacity(100))
        
        row.addWidget(slider)
        row.addWidget(spin)
        row.addWidget(reset_btn)
        layout.addRow("Opacity:", row)
    
    def _add_point_size_control(self, layout: QFormLayout) -> None:
        """Add point size control."""
        if not self._current_item or not self._current_item.actor:
            return
        
        current_size = self._current_item.actor.GetProperty().GetPointSize()
        if "point_size" in self._pending_changes:
            current_size = self._pending_changes["point_size"]
        
        row = QHBoxLayout()
        spin = ScientificDoubleSpinBox()
        spin.setValue(current_size)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(RESET_BUTTON_WIDTH)
        
        def update_size(val):
            self._pending_changes["point_size"] = val
            self._apply_btn.setEnabled(True)
        
        spin.valueChanged.connect(update_size)
        reset_btn.clicked.connect(lambda: [spin.setValue(3.0), update_size(3.0)])
        
        row.addWidget(spin)
        row.addWidget(reset_btn)
        layout.addRow("Point Size:", row)
    
    def _add_line_width_control(self, layout: QFormLayout) -> None:
        """Add line width control."""
        if not self._current_item or not self._current_item.actor:
            return
        
        current_width = self._current_item.actor.GetProperty().GetLineWidth()
        if "line_width" in self._pending_changes:
            current_width = self._pending_changes["line_width"]
        
        row = QHBoxLayout()
        spin = ScientificDoubleSpinBox()
        spin.setValue(current_width)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(RESET_BUTTON_WIDTH)
        
        def update_width(val):
            self._pending_changes["line_width"] = val
            self._apply_btn.setEnabled(True)
        
        spin.valueChanged.connect(update_width)
        reset_btn.clicked.connect(lambda: [spin.setValue(1.0), update_width(1.0)])
        
        row.addWidget(spin)
        row.addWidget(reset_btn)
        layout.addRow("Line Width:", row)
    
    def _add_gaussian_scale_control(self, layout: QFormLayout) -> None:
        """Add gaussian scale control."""
        if not self._current_item or not self._current_item.actor:
            return
        
        mapper = self._current_item.actor.GetMapper()
        current_scale = mapper.GetScaleFactor() if hasattr(mapper, "GetScaleFactor") else 0.05
        if "gaussian_scale" in self._pending_changes:
            current_scale = self._pending_changes["gaussian_scale"]
        
        row = QHBoxLayout()
        spin = ScientificDoubleSpinBox()
        spin.setValue(current_scale)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(RESET_BUTTON_WIDTH)
        
        def update_scale(val):
            self._pending_changes["gaussian_scale"] = val
            self._apply_btn.setEnabled(True)
        
        spin.valueChanged.connect(update_scale)
        reset_btn.clicked.connect(lambda: [spin.setValue(0.05), update_scale(0.05)])
        
        row.addWidget(spin)
        row.addWidget(reset_btn)
        layout.addRow("Sphere Radius:", row)
    
    def _add_legend_section(self, enabled: bool = True) -> None:
        """Add legend (scalar bar) settings section."""
        group = QGroupBox("Legend Settings")
        group.setEnabled(enabled)
        layout = QFormLayout(group)
        
        settings = self._legend_settings
        defaults = DEFAULT_LEGEND_SETTINGS
        
        font_size_row = QHBoxLayout()
        font_size_spin = QSpinBox()
        font_size_spin.setRange(8, 72)
        font_size_spin.setValue(settings["font_size"])
        font_size_spin.valueChanged.connect(lambda v: self._on_legend_setting_changed("font_size", v))
        font_size_reset = QPushButton("Reset")
        font_size_reset.setFixedWidth(50)
        font_size_reset.clicked.connect(lambda: [font_size_spin.setValue(defaults["font_size"])])
        font_size_row.addWidget(font_size_spin)
        font_size_row.addWidget(font_size_reset)
        layout.addRow("Font Size:", font_size_row)
        
        color_row = QHBoxLayout()
        self._font_color_btn = QPushButton()
        self._update_color_button_style(settings["font_color"])
        self._font_color_btn.setFixedSize(60, 25)
        self._font_color_btn.clicked.connect(self._on_font_color_clicked)
        color_reset = QPushButton("Reset")
        color_reset.setFixedWidth(50)
        color_reset.clicked.connect(lambda: self._reset_font_color())
        color_row.addWidget(self._font_color_btn)
        color_row.addWidget(color_reset)
        color_row.addStretch()
        layout.addRow("Font Color:", color_row)
        
        bold_row = QHBoxLayout()
        bold_check = QCheckBox()
        bold_check.setChecked(settings["bold"])
        bold_check.checkStateChanged.connect(lambda s: self._on_legend_setting_changed("bold", s == Qt.CheckState.Checked))
        bold_reset = QPushButton("Reset")
        bold_reset.setFixedWidth(50)
        bold_reset.clicked.connect(lambda: bold_check.setChecked(defaults["bold"]))
        bold_row.addWidget(bold_check)
        bold_row.addWidget(bold_reset)
        bold_row.addStretch()
        layout.addRow("Bold:", bold_row)
        
        italic_row = QHBoxLayout()
        italic_check = QCheckBox()
        italic_check.setChecked(settings["italic"])
        italic_check.checkStateChanged.connect(lambda s: self._on_legend_setting_changed("italic", s == Qt.CheckState.Checked))
        italic_reset = QPushButton("Reset")
        italic_reset.setFixedWidth(50)
        italic_reset.clicked.connect(lambda: italic_check.setChecked(defaults["italic"]))
        italic_row.addWidget(italic_check)
        italic_row.addWidget(italic_reset)
        italic_row.addStretch()
        layout.addRow("Italic:", italic_row)
        
        pos_x_row = QHBoxLayout()
        self._pos_x_spin = QDoubleSpinBox()
        self._pos_x_spin.setSingleStep(0.05)
        self._pos_x_spin.setDecimals(2)
        self._pos_x_spin.setValue(settings["position_x"])
        pos_x_reset = QPushButton("Reset")
        pos_x_reset.setFixedWidth(50)
        pos_x_reset.clicked.connect(lambda: self._pos_x_spin.setValue(defaults["position_x"]))
        pos_x_row.addWidget(self._pos_x_spin)
        pos_x_row.addWidget(pos_x_reset)
        layout.addRow("Position X:", pos_x_row)
        
        pos_y_row = QHBoxLayout()
        self._pos_y_spin = QDoubleSpinBox()
        self._pos_y_spin.setSingleStep(0.05)
        self._pos_y_spin.setDecimals(2)
        self._pos_y_spin.setValue(settings["position_y"])
        pos_y_reset = QPushButton("Reset")
        pos_y_reset.setFixedWidth(50)
        pos_y_reset.clicked.connect(lambda: self._pos_y_spin.setValue(defaults["position_y"]))
        pos_y_row.addWidget(self._pos_y_spin)
        pos_y_row.addWidget(pos_y_reset)
        layout.addRow("Position Y:", pos_y_row)
        
        width_row = QHBoxLayout()
        self._width_spin = QDoubleSpinBox()
        self._width_spin.setRange(0.01, 0.5)
        self._width_spin.setSingleStep(0.01)
        self._width_spin.setDecimals(2)
        self._width_spin.setValue(settings["width"])
        width_reset = QPushButton("Reset")
        width_reset.setFixedWidth(50)
        width_reset.clicked.connect(lambda: self._width_spin.setValue(defaults["width"]))
        width_row.addWidget(self._width_spin)
        width_row.addWidget(width_reset)
        layout.addRow("Width:", width_row)
        
        height_row = QHBoxLayout()
        self._height_spin = QDoubleSpinBox()
        self._height_spin.setRange(0.1, 0.9)
        self._height_spin.setSingleStep(0.05)
        self._height_spin.setDecimals(2)
        self._height_spin.setValue(settings["height"])
        height_reset = QPushButton("Reset")
        height_reset.setFixedWidth(50)
        height_reset.clicked.connect(lambda: self._height_spin.setValue(defaults["height"]))
        height_row.addWidget(self._height_spin)
        height_row.addWidget(height_reset)
        layout.addRow("Height:", height_row)
        
        self._update_legend_spinbox_ranges()
        
        self._pos_x_spin.valueChanged.connect(self._on_legend_pos_size_changed)
        self._pos_y_spin.valueChanged.connect(self._on_legend_pos_size_changed)
        self._width_spin.valueChanged.connect(self._on_legend_pos_size_changed)
        self._height_spin.valueChanged.connect(self._on_legend_pos_size_changed)
        
        self._vtk_layout.addWidget(group)
    
    def _reset_font_color(self) -> None:
        """Reset font color to default."""
        default_color = DEFAULT_LEGEND_SETTINGS["font_color"]
        self._update_color_button_style(default_color)
        self._on_legend_setting_changed("font_color", default_color)
    
    def _update_color_button_style(self, color: Tuple[float, float, float]) -> None:
        """Update the color button background to reflect the current color."""
        r, g, b = int(color[0] * 255), int(color[1] * 255), int(color[2] * 255)
        self._font_color_btn.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); border: 1px solid #555;"
        )
    
    def _on_font_color_clicked(self) -> None:
        """Handle font color button click."""
        current = self._legend_settings["font_color"]
        initial = QColor(int(current[0] * 255), int(current[1] * 255), int(current[2] * 255))
        color = QColorDialog.getColor(initial, self, "Select Font Color")
        if color.isValid():
            new_color = (color.redF(), color.greenF(), color.blueF())
            self._update_color_button_style(new_color)
            self._on_legend_setting_changed("font_color", new_color)
    
    def _on_legend_setting_changed(self, key: str, value) -> None:
        """Handle legend setting change."""
        self._legend_settings[key] = value
        self._pending_changes["legend"] = self._legend_settings.copy()
        self._apply_btn.setEnabled(True)
    
    def _update_legend_spinbox_ranges(self) -> None:
        """Update position/size spinbox ranges to prevent legend overflow."""
        width = self._width_spin.value()
        height = self._height_spin.value()
        pos_x = self._pos_x_spin.value()
        pos_y = self._pos_y_spin.value()
        
        self._pos_x_spin.blockSignals(True)
        self._pos_y_spin.blockSignals(True)
        self._width_spin.blockSignals(True)
        self._height_spin.blockSignals(True)
        
        self._pos_x_spin.setRange(0.0, max(0.01, 1.0 - width))
        self._pos_y_spin.setRange(0.0, max(0.01, 1.0 - height))
        
        if pos_x > 1.0 - width:
            self._pos_x_spin.setValue(max(0.0, 1.0 - width))
        if pos_y > 1.0 - height:
            self._pos_y_spin.setValue(max(0.0, 1.0 - height))
        
        self._pos_x_spin.blockSignals(False)
        self._pos_y_spin.blockSignals(False)
        self._width_spin.blockSignals(False)
        self._height_spin.blockSignals(False)
    
    def _on_legend_pos_size_changed(self) -> None:
        """Handle position/size spinbox value change."""
        self._update_legend_spinbox_ranges()
        
        self._legend_settings["position_x"] = self._pos_x_spin.value()
        self._legend_settings["position_y"] = self._pos_y_spin.value()
        self._legend_settings["width"] = self._width_spin.value()
        self._legend_settings["height"] = self._height_spin.value()
        
        self._pending_changes["legend"] = self._legend_settings.copy()
        self._apply_btn.setEnabled(True)
