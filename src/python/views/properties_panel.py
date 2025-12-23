from PySide6.QtWidgets import (QWidget, QVBoxLayout, QScrollArea, QGroupBox, 
                               QFormLayout, QHBoxLayout, QLabel, QPushButton,
                               QDoubleSpinBox, QSlider, QSpinBox, QCheckBox, QComboBox)
from PySide6.QtCore import Qt, Signal
from typing import Optional, Any, List, Tuple
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


class PropertiesPanel(QWidget):
    """Panel for displaying and editing item properties."""
    
    apply_filter_requested = Signal(str)  # item_id
    opacity_changed = Signal(str, float)  # item_id, value
    point_size_changed = Signal(str, float)  # item_id, value
    line_width_changed = Signal(str, float)  # item_id, value
    gaussian_scale_changed = Signal(str, float)  # item_id, value
    color_by_changed = Signal(str, str, str)  # item_id, array_name, array_type
    slice_params_changed = Signal(str, list, list, bool)  # item_id, origin, normal, show_preview
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: Optional[PipelineItem] = None
        self._current_style: str = "Surface"
        self._data_arrays: List[Tuple[str, str]] = []
        
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
                 current_array: str = None, scalar_visible: bool = False) -> None:
        """Set the current item to display properties for."""
        self._current_item = item
        self._current_style = style
        self._data_arrays = data_arrays or []
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
        """Add color by dropdown."""
        group = QGroupBox("Color By")
        layout = QVBoxLayout(group)
        
        combo = QComboBox()
        combo.addItem("Solid Color", "__SolidColor__")
        
        current_idx = 0
        for idx, (name, type_) in enumerate(self._data_arrays):
            combo.addItem(f"{name} ({type_})", (name, type_))
            if scalar_visible and name == current_array:
                current_idx = idx + 1
        
        combo.setCurrentIndex(current_idx)
        combo.currentIndexChanged.connect(lambda idx: self._on_color_change(combo, idx))
        
        layout.addWidget(combo)
        self._layout.addWidget(group)
    
    def _on_color_change(self, combo: QComboBox, idx: int) -> None:
        """Handle color by selection change."""
        if not self._current_item:
            return
        data = combo.itemData(idx)
        if data == "__SolidColor__":
            self.color_by_changed.emit(self._current_item.id, "__SolidColor__", "POINT")
        else:
            name, type_ = data
            self.color_by_changed.emit(self._current_item.id, name, type_)
    
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
        
        origin_spins = []
        for i, label in enumerate(["Origin X", "Origin Y", "Origin Z"]):
            spin = ScientificDoubleSpinBox()
            spin.setValue(params.origin[i])
            spin.valueChanged.connect(lambda v, idx=i: self._on_slice_param_changed('origin', idx, v))
            layout.addRow(label, spin)
            origin_spins.append(spin)
        
        show_plane_cb = QCheckBox("Show Plane")
        show_plane_cb.setChecked(params.show_preview)
        show_plane_cb.toggled.connect(lambda v: self._on_slice_preview_toggled(v))
        layout.addRow("", show_plane_cb)
        
        for i, label in enumerate(["Normal X", "Normal Y", "Normal Z"]):
            spin = ScientificDoubleSpinBox()
            spin.setRange(-1, 1)
            spin.setValue(params.normal[i])
            spin.valueChanged.connect(lambda v, idx=i: self._on_slice_param_changed('normal', idx, v))
            layout.addRow(label, spin)
        
        self._layout.addWidget(group)
    
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
            self._current_item.id, params.origin, params.normal, params.show_preview
        )
    
    def _on_slice_preview_toggled(self, visible: bool) -> None:
        """Handle slice preview toggle."""
        if not self._current_item:
            return
        
        params = SliceParams.from_dict(self._current_item.filter_params)
        params.show_preview = visible
        self._current_item.filter_params = params.to_dict()
        
        self.slice_params_changed.emit(
            self._current_item.id, params.origin, params.normal, params.show_preview
        )

