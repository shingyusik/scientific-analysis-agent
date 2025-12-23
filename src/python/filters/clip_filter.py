from typing import Any, Tuple, Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Signal
from filters.filter_base import FilterBase
from models.pipeline_item import PipelineItem
from views.common_widgets import ScientificDoubleSpinBox


class ClipParams:
    """Parameters for clip filter."""
    
    def __init__(self, origin=None, normal=None):
        self.origin = origin or [0.0, 0.0, 0.0]
        self.normal = normal or [1.0, 0.0, 0.0]
    
    def to_dict(self) -> dict:
        return {
            "origin": self.origin.copy(),
            "normal": self.normal.copy(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ClipParams":
        return cls(
            origin=data.get("origin", [0.0, 0.0, 0.0]),
            normal=data.get("normal", [1.0, 0.0, 0.0]),
        )


class ClipFilter(FilterBase):
    """Clip filter implementation - example of how easy it is to add a new filter."""
    
    @property
    def filter_type(self) -> str:
        return "clip_filter"
    
    @property
    def display_name(self) -> str:
        return "Clip"
    
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        """Apply clip filter."""
        import vtk
        clip_params = ClipParams.from_dict(params)
        
        plane = vtk.vtkPlane()
        plane.SetOrigin(clip_params.origin)
        plane.SetNormal(clip_params.normal)
        
        clipper = vtk.vtkClipDataSet()
        clipper.SetInputData(data)
        clipper.SetClipFunction(plane)
        clipper.Update()
        
        clipped_data = clipper.GetOutput()
        
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(clipped_data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 1, 1)
        
        return actor, clipped_data
    
    def create_default_params(self) -> dict:
        """Create default clip parameters."""
        return ClipParams().to_dict()
    
    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None) -> Optional[QWidget]:
        """Create clip filter parameters widget."""
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        params = ClipParams.from_dict(item.filter_params if item else self.create_default_params())
        
        group = QGroupBox("Filter Parameters")
        form_layout = QFormLayout(group)
        
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
        return widget
    
    def _on_origin_changed(self, index: int, value: float, item: Optional[PipelineItem]) -> None:
        """Handle origin parameter change."""
        if not item:
            return
        params = ClipParams.from_dict(item.filter_params)
        params.origin[index] = value
        item.filter_params = params.to_dict()
    
    def _on_normal_changed(self, index: int, value: float, item: Optional[PipelineItem]) -> None:
        """Handle normal parameter change."""
        if not item:
            return
        params = ClipParams.from_dict(item.filter_params)
        params.normal[index] = value
        item.filter_params = params.to_dict()
    
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

