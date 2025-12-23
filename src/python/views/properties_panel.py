from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QGroupBox, 
                               QFormLayout, QHBoxLayout, QLabel, QPushButton,
                               QDoubleSpinBox, QSlider, QSpinBox, QCheckBox, QComboBox,
                               QDialog, QDialogButtonBox, QListWidget, QListWidgetItem,
                               QAbstractItemView)
from PySide6.QtCore import Qt, Signal
from typing import Optional, Any, List, Tuple
import numpy as np
from models.pipeline_item import PipelineItem
from models.filter_params import SliceParams


class ScientificDoubleSpinBox(QDoubleSpinBox):
    """SpinBox optimized for scientific values."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDecimals(15)
        self.setRange(-1e30, 1e30)
        self.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
    
    def textFromValue(self, value):
        return format(value, '.10g')


class GenerateSeriesDialog(QDialog):
    """Dialog for generating a series of offset values."""
    
    def __init__(self, min_val: float = -1.0, max_val: float = 1.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Number Series")
        self.setMinimumWidth(400)
        
        self._min_val = min_val
        self._max_val = max_val
        self._result: List[float] = []
        
        layout = QVBoxLayout(self)
        
        range_group = QGroupBox("Range")
        range_layout = QHBoxLayout(range_group)
        
        self._min_spin = ScientificDoubleSpinBox()
        self._min_spin.setValue(min_val)
        self._min_spin.valueChanged.connect(self._update_preview)
        
        range_layout.addWidget(self._min_spin)
        range_layout.addWidget(QLabel("-"))
        
        self._max_spin = ScientificDoubleSpinBox()
        self._max_spin.setValue(max_val)
        self._max_spin.valueChanged.connect(self._update_preview)
        range_layout.addWidget(self._max_spin)
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(30)
        refresh_btn.setToolTip("Reset to data range")
        refresh_btn.clicked.connect(self._reset_range)
        range_layout.addWidget(refresh_btn)
        
        layout.addWidget(range_group)
        
        type_layout = QFormLayout()
        self._type_combo = QComboBox()
        self._type_combo.addItem("Linear")
        self._type_combo.currentIndexChanged.connect(self._update_preview)
        type_layout.addRow("Type:", self._type_combo)
        
        self._samples_spin = QSpinBox()
        self._samples_spin.setRange(2, 1000)
        self._samples_spin.setValue(10)
        self._samples_spin.valueChanged.connect(self._update_preview)
        type_layout.addRow("Number of Samples:", self._samples_spin)
        layout.addLayout(type_layout)
        
        self._preview_label = QLabel()
        self._preview_label.setWordWrap(True)
        self._preview_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self._preview_label)
        
        layout.addStretch()
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Generate")
        button_box.accepted.connect(self._on_generate)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self._update_preview()
    
    def _reset_range(self) -> None:
        """Reset range to initial data range."""
        self._min_spin.setValue(self._min_val)
        self._max_spin.setValue(self._max_val)
    
    def _generate_series(self) -> List[float]:
        """Generate the series based on current settings."""
        min_v = self._min_spin.value()
        max_v = self._max_spin.value()
        n = self._samples_spin.value()
        
        if self._type_combo.currentText() == "Linear":
            return list(np.linspace(min_v, max_v, n))
        return [min_v]
    
    def _update_preview(self) -> None:
        """Update the preview label."""
        series = self._generate_series()
        formatted = [format(v, '.6g') for v in series]
        if len(formatted) > 8:
            preview_text = ", ".join(formatted[:4]) + ", ..., " + ", ".join(formatted[-2:])
        else:
            preview_text = ", ".join(formatted)
        self._preview_label.setText(f"Sample series: {preview_text}")
    
    def _on_generate(self) -> None:
        """Handle generate button click."""
        self._result = self._generate_series()
        self.accept()
    
    def get_result(self) -> List[float]:
        """Get the generated series."""
        return self._result


class OffsetListWidget(QWidget):
    """Widget for managing a list of offset values."""
    
    offsets_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value_range: Tuple[float, float] = (-1.0, 1.0)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        range_label_layout = QHBoxLayout()
        self._range_label = QLabel("Value Range: [-1.0, 1.0]")
        range_label_layout.addWidget(self._range_label)
        range_label_layout.addStretch()
        layout.addLayout(range_label_layout)
        
        list_layout = QHBoxLayout()
        
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list_widget.setMinimumHeight(150)
        self._list_widget.setMaximumHeight(200)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_layout.addWidget(self._list_widget)
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(30, 30)
        add_btn.setToolTip("Add new offset value")
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setToolTip("Remove selected offset")
        remove_btn.clicked.connect(self._on_remove)
        btn_layout.addWidget(remove_btn)
        
        series_btn = QPushButton("⋯")
        series_btn.setFixedSize(30, 30)
        series_btn.setToolTip("Generate number series")
        series_btn.clicked.connect(self._on_generate_series)
        btn_layout.addWidget(series_btn)
        
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(30, 30)
        clear_btn.setToolTip("Clear all offsets")
        clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(clear_btn)
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setToolTip("Refresh value range")
        refresh_btn.clicked.connect(self._on_refresh_range)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        layout.addLayout(list_layout)
        
        self._add_item(0.0)
    
    def set_value_range(self, min_val: float, max_val: float) -> None:
        """Set the valid value range for offsets."""
        self._value_range = (min_val, max_val)
        self._range_label.setText(f"Value Range: [{format(min_val, '.7g')}, {format(max_val, '.7g')}]")
    
    def set_offsets(self, offsets: List[float]) -> None:
        """Set the offset values."""
        self._list_widget.clear()
        for offset in offsets:
            self._add_item(offset)
    
    def get_offsets(self) -> List[float]:
        """Get current offset values."""
        offsets = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            offsets.append(item.data(Qt.UserRole))
        return offsets
    
    def _add_item(self, value: float) -> None:
        """Add a new offset item."""
        item = QListWidgetItem(format(value, '.15g'))
        item.setData(Qt.UserRole, value)
        self._list_widget.addItem(item)
    
    def _on_add(self) -> None:
        """Add a new offset value at 0."""
        self._add_item(0.0)
        self._emit_change()
    
    def _on_remove(self) -> None:
        """Remove selected offset."""
        current = self._list_widget.currentRow()
        if current >= 0 and self._list_widget.count() > 1:
            self._list_widget.takeItem(current)
            self._emit_change()
    
    def _on_generate_series(self) -> None:
        """Open generate series dialog."""
        dialog = GenerateSeriesDialog(self._value_range[0], self._value_range[1], self)
        if dialog.exec() == QDialog.Accepted:
            series = dialog.get_result()
            self._list_widget.clear()
            for value in series:
                self._add_item(value)
            self._emit_change()
    
    def _on_clear(self) -> None:
        """Clear all offsets and add default 0."""
        self._list_widget.clear()
        self._add_item(0.0)
        self._emit_change()
    
    def _on_refresh_range(self) -> None:
        """Request range refresh (parent should handle this)."""
        pass
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click to edit value."""
        from PySide6.QtWidgets import QInputDialog
        current_value = item.data(Qt.UserRole)
        new_value, ok = QInputDialog.getDouble(
            self, "Edit Offset", "Offset value:",
            current_value, -1e30, 1e30, 10
        )
        if ok:
            item.setText(format(new_value, '.15g'))
            item.setData(Qt.UserRole, new_value)
            self._emit_change()
    
    def _emit_change(self) -> None:
        """Emit offsets changed signal."""
        self.offsets_changed.emit(self.get_offsets())


class PropertiesPanel(QWidget):
    """Panel for displaying and editing item properties."""
    
    apply_filter_requested = Signal(str)  # item_id
    opacity_changed = Signal(str, float)  # item_id, value
    point_size_changed = Signal(str, float)  # item_id, value
    line_width_changed = Signal(str, float)  # item_id, value
    gaussian_scale_changed = Signal(str, float)  # item_id, value
    color_by_changed = Signal(str, str, str, str)  # item_id, array_name, array_type, component
    slice_params_changed = Signal(str, list, list, list, bool)  # item_id, origin, normal, offsets, show_preview
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: Optional[PipelineItem] = None
        self._current_style: str = "Surface"
        self._data_arrays: List[Tuple[str, str]] = []
        self._parent_bounds: Optional[Tuple[float, ...]] = None
        self._offset_list_widget: Optional[OffsetListWidget] = None
        
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        
        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setAlignment(Qt.AlignTop)
        
        self._scroll.setWidget(self._content)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self._scroll)
    
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
        
        if item.item_type == "slice_filter":
            self._add_slice_params_section()
        
        self._layout.addStretch()
    
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
    
    def _add_slice_params_section(self) -> None:
        """Add slice filter parameters section."""
        if not self._current_item:
            return
        
        params = SliceParams.from_dict(self._current_item.filter_params)
        
        group = QGroupBox("Filter Parameters")
        layout = QFormLayout(group)
        
        show_plane_cb = QCheckBox("Show Plane")
        show_plane_cb.setChecked(params.show_preview)
        show_plane_cb.toggled.connect(lambda v: self._on_slice_preview_toggled(v))
        layout.addRow("", show_plane_cb)
        
        origin_row = QHBoxLayout()
        origin_row.addWidget(QLabel("Origin:"))
        origin_spins = []
        for i, label in enumerate(["X", "Y", "Z"]):
            spin = ScientificDoubleSpinBox()
            spin.setFixedWidth(100)
            spin.setValue(params.origin[i])
            spin.valueChanged.connect(lambda v, idx=i: self._on_slice_param_changed('origin', idx, v))
            origin_row.addWidget(QLabel(label))
            origin_row.addWidget(spin)
            origin_spins.append(spin)
        
        origin_reset_btn = QPushButton("Reset")
        origin_reset_btn.setFixedWidth(50)
        origin_reset_btn.clicked.connect(lambda: self._reset_origin(origin_spins))
        origin_row.addWidget(origin_reset_btn)
        origin_row.addStretch()
        layout.addRow(origin_row)
        
        normal_row = QHBoxLayout()
        normal_row.addWidget(QLabel("Normal:"))
        normal_spins = []
        for i, label in enumerate(["X", "Y", "Z"]):
            spin = ScientificDoubleSpinBox()
            spin.setFixedWidth(100)
            spin.setRange(-1, 1)
            spin.setValue(params.normal[i])
            spin.valueChanged.connect(lambda v, idx=i: self._on_slice_param_changed('normal', idx, v))
            normal_row.addWidget(QLabel(label))
            normal_row.addWidget(spin)
            normal_spins.append(spin)
        
        normal_reset_btn = QPushButton("Reset")
        normal_reset_btn.setFixedWidth(50)
        normal_reset_btn.clicked.connect(lambda: self._reset_normal(normal_spins))
        normal_row.addWidget(normal_reset_btn)
        normal_row.addStretch()
        layout.addRow(normal_row)
        
        self._layout.addWidget(group)
        
        offset_group = QGroupBox("Slice Offsets")
        offset_layout = QVBoxLayout(offset_group)
        
        self._offset_list_widget = OffsetListWidget()
        self._offset_list_widget.set_offsets(params.offsets)
        
        if self._parent_bounds:
            normal_np = np.array(params.normal)
            normal_len = np.linalg.norm(normal_np)
            if normal_len > 0:
                normal_np = normal_np / normal_len
            
            bounds = self._parent_bounds
            corners = [
                [bounds[0], bounds[2], bounds[4]],
                [bounds[1], bounds[2], bounds[4]],
                [bounds[0], bounds[3], bounds[4]],
                [bounds[1], bounds[3], bounds[4]],
                [bounds[0], bounds[2], bounds[5]],
                [bounds[1], bounds[2], bounds[5]],
                [bounds[0], bounds[3], bounds[5]],
                [bounds[1], bounds[3], bounds[5]],
            ]
            origin_np = np.array(params.origin)
            projections = [np.dot(np.array(c) - origin_np, normal_np) for c in corners]
            min_proj = min(projections)
            max_proj = max(projections)
            self._offset_list_widget.set_value_range(min_proj, max_proj)
        
        self._offset_list_widget.offsets_changed.connect(self._on_offsets_changed)
        offset_layout.addWidget(self._offset_list_widget)
        
        self._layout.addWidget(offset_group)
    
    def _on_slice_param_changed(self, param_type: str, index: int, value: float) -> None:
        """Handle slice parameter change."""
        if not self._current_item:
            return
        
        params = SliceParams.from_dict(self._current_item.filter_params)
        
        if param_type == 'origin':
            params.origin[index] = value
        else:
            params.normal[index] = value
        
        self._current_item.filter_params = params.to_dict()
        self.slice_params_changed.emit(
            self._current_item.id, params.origin, params.normal, params.offsets, params.show_preview
        )
    
    def _on_slice_preview_toggled(self, visible: bool) -> None:
        """Handle slice preview toggle."""
        if not self._current_item:
            return
        
        params = SliceParams.from_dict(self._current_item.filter_params)
        params.show_preview = visible
        self._current_item.filter_params = params.to_dict()
        
        self.slice_params_changed.emit(
            self._current_item.id, params.origin, params.normal, params.offsets, params.show_preview
        )
    
    def _on_offsets_changed(self, offsets: List[float]) -> None:
        """Handle offset list change."""
        if not self._current_item:
            return
        
        params = SliceParams.from_dict(self._current_item.filter_params)
        params.offsets = offsets
        self._current_item.filter_params = params.to_dict()
        
        self.slice_params_changed.emit(
            self._current_item.id, params.origin, params.normal, params.offsets, params.show_preview
        )
    
    def _reset_origin(self, spins: List[ScientificDoubleSpinBox]) -> None:
        """Reset origin values to [0.0, 0.0, 0.0]."""
        if not self._current_item:
            return
        
        for i, spin in enumerate(spins):
            spin.blockSignals(True)
            spin.setValue(0.0)
            spin.blockSignals(False)
            self._on_slice_param_changed('origin', i, 0.0)
    
    def _reset_normal(self, spins: List[ScientificDoubleSpinBox]) -> None:
        """Reset normal values to [1.0, 0.0, 0.0]."""
        if not self._current_item:
            return
        
        default_values = [1.0, 0.0, 0.0]
        for i, spin in enumerate(spins):
            spin.blockSignals(True)
            spin.setValue(default_values[i])
            spin.blockSignals(False)
            self._on_slice_param_changed('normal', i, default_values[i])

