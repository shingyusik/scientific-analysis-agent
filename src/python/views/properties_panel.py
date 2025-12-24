from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QGroupBox, 
                               QFormLayout, QHBoxLayout, QLabel, QPushButton,
                               QSlider, QSpinBox, QComboBox, QCheckBox,
                               QDoubleSpinBox, QColorDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional, List, Tuple, TYPE_CHECKING
from models.pipeline_item import PipelineItem
from views.common_widgets import ScientificDoubleSpinBox
from views.vtk_widget import DEFAULT_LEGEND_SETTINGS

if TYPE_CHECKING:
    from services.vtk_render_service import VTKRenderService


class PropertiesPanel(QWidget):
    """Panel for displaying and editing item properties."""
    
    apply_filter_requested = Signal(str)  # item_id
    opacity_changed = Signal(str, float)  # item_id, value
    point_size_changed = Signal(str, float)  # item_id, value
    line_width_changed = Signal(str, float)  # item_id, value
    gaussian_scale_changed = Signal(str, float)  # item_id, value
    color_by_changed = Signal(str, str, str, str)  # item_id, array_name, array_type, component
    filter_params_changed = Signal(str, dict)  # item_id, params (general purpose)
    legend_settings_changed = Signal(dict)  # legend settings dictionary
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: Optional[PipelineItem] = None
        self._current_style: str = "Surface"
        self._data_arrays: List[Tuple[str, str]] = []
        self._parent_bounds: Optional[Tuple[float, ...]] = None
        self._render_service: Optional["VTKRenderService"] = None
        self._filter_widget: Optional[QWidget] = None
        self._legend_settings: dict = DEFAULT_LEGEND_SETTINGS.copy()
        
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        
        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setAlignment(Qt.AlignTop)
        
        self._scroll.setWidget(self._content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._scroll)
    
    def set_render_service(self, render_service: "VTKRenderService") -> None:
        """Set the render service for creating filter widgets."""
        self._render_service = render_service
    
    def set_item(self, item: Optional[PipelineItem], style: str = "Surface",
                 data_arrays: List[Tuple[str, str]] = None, 
                 current_array: str = None, scalar_visible: bool = False,
                 parent_bounds: Tuple[float, ...] = None) -> None:
        """Set the current item to display properties for."""
        self._current_item = item
        self._current_style = style
        self._data_arrays = data_arrays or []
        self._parent_bounds = parent_bounds
        self._rebuild_ui(current_array, scalar_visible)
    
    def _clear_layout(self) -> None:
        """Clear all widgets from the layout."""
        while self._layout.count():
            child = self._layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
    
    def _rebuild_ui(self, current_array: str = None, scalar_visible: bool = False) -> None:
        """Rebuild the properties UI for current item."""
        self._clear_layout()
        self._filter_widget = None
        
        if not self._current_item:
            self._layout.addWidget(QLabel("No item selected."))
            return
        
        item = self._current_item
        
        if not item.actor:
            self._layout.addWidget(QLabel("No styling properties available for this source."))
            return
        
        if "filter" in item.item_type:
            self._add_apply_button()
        
        if self._data_arrays:
            self._add_color_by_section(current_array, scalar_visible)
        
        self._add_styling_section()
        
        if self._data_arrays:
            legend_enabled = scalar_visible and item.visible
            self._add_legend_section(legend_enabled)
        
        if "filter" in item.item_type:
            self._add_filter_params_section(item)
        
        self._layout.addStretch()
    
    def _add_filter_params_section(self, item: PipelineItem) -> None:
        """Add filter parameters section using the filter registry."""
        import filters
        
        filter_class = filters.get_filter(item.item_type)
        if not filter_class or not self._render_service:
            return
        
        filter_instance = filter_class(self._render_service)
        
        def on_params_changed(item_id: str, params: dict):
            self.filter_params_changed.emit(item_id, params)
        
        widget = filter_instance.create_params_widget(
            self._content, item, self._parent_bounds, on_params_changed
        )
        
        if widget:
            self._filter_widget = widget
            self._layout.addWidget(widget)
    
    def _add_color_by_section(self, current_array: str, scalar_visible: bool) -> None:
        """Add color by dropdown with vector component selection."""
        group = QGroupBox("Color By")
        layout = QHBoxLayout(group)
        
        main_combo = QComboBox()
        main_combo.addItem("Solid Color", ("__SolidColor__", None, None))
        
        component_combo = QComboBox()
        component_combo.addItem("Magnitude", "Magnitude")
        component_combo.setEnabled(False)
        
        current_main_idx = 0
        current_component = None
        
        VALID_COMPONENTS = {"Magnitude", "X", "Y", "Z"}
        
        if scalar_visible and current_array:
            for idx, (name, type_, num_components) in enumerate(self._data_arrays):
                if num_components > 1:
                    if name == current_array:
                        current_main_idx = idx + 1
                        current_component = "Magnitude"
                        break
                    prefix = f"{name}_"
                    if current_array.startswith(prefix):
                        suffix = current_array[len(prefix):]
                        if suffix in VALID_COMPONENTS:
                            current_main_idx = idx + 1
                            current_component = suffix
                            break
        
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
                target_component = component_to_select if component_to_select else current_component
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
                update_component_combo(idx, current_component)
            else:
                update_component_combo(idx)
            on_selection_changed()
        
        def on_selection_changed():
            if not self._current_item:
                return
            main_data = main_combo.itemData(main_combo.currentIndex())
            if main_data[0] == "__SolidColor__":
                self.color_by_changed.emit(self._current_item.id, "__SolidColor__", "POINT", "")
            else:
                name, type_, num_components = main_data
                if num_components and num_components > 1:
                    component = component_combo.itemData(component_combo.currentIndex())
                    self.color_by_changed.emit(self._current_item.id, name, type_, component)
                else:
                    self.color_by_changed.emit(self._current_item.id, name, type_, "")
        
        main_combo.currentIndexChanged.connect(on_main_combo_changed)
        component_combo.currentIndexChanged.connect(on_selection_changed)
        
        update_component_combo(current_main_idx, current_component)
        
        layout.addWidget(main_combo)
        layout.addWidget(component_combo)
        self._layout.addWidget(group)
    
    def _add_apply_button(self) -> None:
        """Add apply button for filters."""
        btn = QPushButton("Apply")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2c3e50;
                color: white;
                font-weight: bold;
                padding: 10px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #34495e; }
            QPushButton:pressed { background-color: #1a252f; }
        """)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(self._on_apply_clicked)
        self._layout.addWidget(btn)
    
    def _on_apply_clicked(self) -> None:
        """Handle apply button click."""
        if self._current_item:
            self.apply_filter_requested.emit(self._current_item.id)
    
    def _add_styling_section(self) -> None:
        """Add styling controls section."""
        group = QGroupBox(f"Styling: {self._current_style}")
        layout = QFormLayout(group)
        
        self._add_opacity_control(layout)
        
        if self._current_style == "Points":
            self._add_point_size_control(layout)
        elif self._current_style in ["Wireframe", "Surface With Edges"]:
            self._add_line_width_control(layout)
        elif self._current_style == "Point Gaussian":
            self._add_gaussian_scale_control(layout)
        
        self._layout.addWidget(group)
    
    def _add_opacity_control(self, layout: QFormLayout) -> None:
        """Add opacity slider and spinbox."""
        if not self._current_item or not self._current_item.actor:
            return
        
        current_opacity = int(self._current_item.actor.GetProperty().GetOpacity() * 100)
        
        row = QHBoxLayout()
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(current_opacity)
        
        spin = QSpinBox()
        spin.setRange(0, 100)
        spin.setSuffix("%")
        spin.setValue(current_opacity)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(50)
        
        def update_opacity(val):
            slider.blockSignals(True)
            spin.blockSignals(True)
            slider.setValue(val)
            spin.setValue(val)
            slider.blockSignals(False)
            spin.blockSignals(False)
            if self._current_item:
                self.opacity_changed.emit(self._current_item.id, val / 100.0)
        
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
        
        row = QHBoxLayout()
        spin = ScientificDoubleSpinBox()
        spin.setValue(current_size)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(50)
        
        def update_size(val):
            if self._current_item:
                self.point_size_changed.emit(self._current_item.id, val)
        
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
        
        row = QHBoxLayout()
        spin = ScientificDoubleSpinBox()
        spin.setValue(current_width)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(50)
        
        def update_width(val):
            if self._current_item:
                self.line_width_changed.emit(self._current_item.id, val)
        
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
        
        row = QHBoxLayout()
        spin = ScientificDoubleSpinBox()
        spin.setValue(current_scale)
        
        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(50)
        
        def update_scale(val):
            if self._current_item:
                self.gaussian_scale_changed.emit(self._current_item.id, val)
        
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
        
        self._layout.addWidget(group)
    
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
        self.legend_settings_changed.emit(self._legend_settings.copy())
    
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
        
        self.legend_settings_changed.emit(self._legend_settings.copy())
