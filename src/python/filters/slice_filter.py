from typing import Any, Tuple, Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
from PySide6.QtCore import Signal, Qt
from filters.filter_base import FilterBase
from models.pipeline_item import PipelineItem
from models.filter_params import SliceParams
from views.common_widgets import ScientificDoubleSpinBox, OffsetListWidget
import numpy as np


class SliceFilter(FilterBase):
    """Slice filter implementation."""
    
    def __init__(self, render_service):
        super().__init__(render_service)
        self._params_widget: Optional[QWidget] = None
        self._offset_widget: Optional[OffsetListWidget] = None
    
    @property
    def filter_type(self) -> str:
        return "slice_filter"
    
    @property
    def display_name(self) -> str:
        return "Slice"
    
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        """Apply slice filter."""
        slice_params = SliceParams.from_dict(params)
        return self._render_service.apply_slice(
            data,
            slice_params.origin,
            slice_params.normal,
            slice_params.offsets
        )
    
    def create_default_params(self) -> dict:
        """Create default slice parameters."""
        return SliceParams().to_dict()
    
    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None) -> Optional[QWidget]:
        """Create slice filter parameters widget."""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        params = SliceParams.from_dict(item.filter_params if item else self.create_default_params())
        
        group = QGroupBox("Filter Parameters")
        form_layout = QFormLayout(group)
        
        show_plane_cb = QCheckBox("Show Plane")
        show_plane_cb.setChecked(params.show_preview)
        show_plane_cb.toggled.connect(lambda v: self._on_preview_changed(v, item))
        form_layout.addRow("", show_plane_cb)
        
        origin_row = QHBoxLayout()
        origin_row.addWidget(QLabel("Origin:"))
        origin_spins = []
        for i, label in enumerate(["X", "Y", "Z"]):
            spin = ScientificDoubleSpinBox()
            spin.setFixedWidth(100)
            spin.setValue(params.origin[i])
            spin.valueChanged.connect(lambda v, idx=i: self._on_origin_changed(idx, v, item))
            origin_row.addWidget(QLabel(label))
            origin_row.addWidget(spin)
            origin_spins.append(spin)
        
        origin_reset_btn = QPushButton("Reset")
        origin_reset_btn.setFixedWidth(50)
        origin_reset_btn.clicked.connect(lambda: self._reset_origin(origin_spins, item))
        origin_row.addWidget(origin_reset_btn)
        origin_row.addStretch()
        form_layout.addRow(origin_row)
        
        normal_row = QHBoxLayout()
        normal_row.addWidget(QLabel("Normal:"))
        normal_spins = []
        for i, label in enumerate(["X", "Y", "Z"]):
            spin = ScientificDoubleSpinBox()
            spin.setFixedWidth(100)
            spin.setRange(-1, 1)
            spin.setValue(params.normal[i])
            spin.valueChanged.connect(lambda v, idx=i: self._on_normal_changed(idx, v, item))
            normal_row.addWidget(QLabel(label))
            normal_row.addWidget(spin)
            normal_spins.append(spin)
        
        normal_reset_btn = QPushButton("Reset")
        normal_reset_btn.setFixedWidth(50)
        normal_reset_btn.clicked.connect(lambda: self._reset_normal(normal_spins, item))
        normal_row.addWidget(normal_reset_btn)
        normal_row.addStretch()
        form_layout.addRow(normal_row)
        
        layout.addWidget(group)
        
        offset_group = QGroupBox("Slice Offsets")
        offset_layout = QVBoxLayout(offset_group)
        
        self._offset_widget = OffsetListWidget()
        self._offset_widget.set_offsets(params.offsets)
        
        if parent_bounds:
            normal_np = np.array(params.normal)
            normal_len = np.linalg.norm(normal_np)
            if normal_len > 0:
                normal_np = normal_np / normal_len
            
            bounds = parent_bounds
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
            self._offset_widget.set_value_range(min_proj, max_proj)
        
        self._offset_widget.offsets_changed.connect(lambda offsets: self._on_offsets_changed(offsets, item))
        offset_layout.addWidget(self._offset_widget)
        
        layout.addWidget(offset_group)
        
        self._params_widget = widget
        return widget
    
    def get_params_changed_signal(self, widget: QWidget) -> Optional[Signal]:
        """Get the offsets changed signal."""
        if self._offset_widget:
            return self._offset_widget.offsets_changed
        return None
    
    def _on_origin_changed(self, index: int, value: float, item: Optional[PipelineItem]) -> None:
        """Handle origin parameter change."""
        if not item:
            return
        params = SliceParams.from_dict(item.filter_params)
        params.origin[index] = value
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _on_normal_changed(self, index: int, value: float, item: Optional[PipelineItem]) -> None:
        """Handle normal parameter change."""
        if not item:
            return
        params = SliceParams.from_dict(item.filter_params)
        params.normal[index] = value
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _on_offsets_changed(self, offsets: List[float], item: Optional[PipelineItem]) -> None:
        """Handle offsets change."""
        if not item:
            return
        params = SliceParams.from_dict(item.filter_params)
        params.offsets = offsets
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _on_preview_changed(self, visible: bool, item: Optional[PipelineItem]) -> None:
        """Handle preview toggle."""
        if not item:
            return
        params = SliceParams.from_dict(item.filter_params)
        params.show_preview = visible
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _reset_origin(self, spins: List[ScientificDoubleSpinBox], item: Optional[PipelineItem]) -> None:
        """Reset origin values."""
        if not item:
            return
        for i, spin in enumerate(spins):
            spin.blockSignals(True)
            spin.setValue(0.0)
            spin.blockSignals(False)
            self._on_origin_changed(i, 0.0, item)
    
    def _reset_normal(self, spins: List[ScientificDoubleSpinBox], item: Optional[PipelineItem]) -> None:
        """Reset normal values."""
        if not item:
            return
        default_values = [1.0, 0.0, 0.0]
        for i, spin in enumerate(spins):
            spin.blockSignals(True)
            spin.setValue(default_values[i])
            spin.blockSignals(False)
            self._on_normal_changed(i, default_values[i], item)
    
    def _emit_params_changed(self, item: PipelineItem) -> None:
        """Emit parameters changed signal."""
        params = SliceParams.from_dict(item.filter_params)
        if hasattr(self, '_params_changed_signal') and self._params_changed_signal:
            self._params_changed_signal.emit(
                item.id, params.origin, params.normal, params.offsets, params.show_preview
            )

