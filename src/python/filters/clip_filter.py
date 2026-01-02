from dataclasses import dataclass, field
from typing import Any, Tuple, Optional, List
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox
from PySide6.QtCore import Signal
from filters.filter_base import FilterBase
from models.pipeline_item import PipelineItem
from views.common_widgets import ScientificDoubleSpinBox
from utils.logger import get_logger, log_execution

logger = get_logger("FilterOps")


@dataclass
class ClipParams:
    """Parameters for clip filter."""
    
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    normal: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    show_preview: bool = True
    
    def to_dict(self) -> dict:
        return {
            "origin": self.origin.copy(),
            "normal": self.normal.copy(),
            "show_preview": self.show_preview,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ClipParams":
        return cls(
            origin=data.get("origin", [0.0, 0.0, 0.0]),
            normal=data.get("normal", [1.0, 0.0, 0.0]),
            show_preview=data.get("show_preview", True),
        )


class ClipFilter(FilterBase):
    """Clip filter implementation - example of how easy it is to add a new filter."""
    
    @property
    def apply_immediately(self) -> bool:
        return False
    
    @property
    def filter_type(self) -> str:
        return "clip_filter"
    
    @property
    def display_name(self) -> str:
        return "Clip"
    
    @property
    def params_class(self) -> type:
        return ClipParams
    
    @log_execution(start_msg="Clip Filter Calculation Started", end_msg="Clip Filter Calculation Finished")
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
    
    def get_plane_preview_params(self, params: dict) -> Optional[Tuple[List[float], List[float], bool]]:
        """Get plane preview parameters."""
        clip_params = ClipParams.from_dict(params)
        return (clip_params.origin, clip_params.normal, clip_params.show_preview)
    
    def create_default_params(self) -> dict:
        """Create default clip parameters."""
        return ClipParams().to_dict()
    
    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None,
                            on_params_changed: Optional[callable] = None) -> Optional[QWidget]:
        """Create clip filter parameters widget."""
        self._on_params_changed_callback = on_params_changed
        
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        params = ClipParams.from_dict(item.filter_params if item else self.create_default_params())
        
        group = QGroupBox("Filter Parameters")
        form_layout = QFormLayout(group)
        
        show_plane_cb = QCheckBox("Show Plane")
        show_plane_cb.setChecked(params.show_preview)
        show_plane_cb.toggled.connect(lambda v: self._on_show_preview_changed(v, item))
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
        return widget
    
    def _on_origin_changed(self, index: int, value: float, item: Optional[PipelineItem]) -> None:
        """Handle origin parameter change."""
        if not item:
            return
        params = ClipParams.from_dict(item.filter_params)
        params.origin[index] = value
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _on_normal_changed(self, index: int, value: float, item: Optional[PipelineItem]) -> None:
        """Handle normal parameter change."""
        if not item:
            return
        params = ClipParams.from_dict(item.filter_params)
        params.normal[index] = value
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
    
    def _on_show_preview_changed(self, value: bool, item: Optional[PipelineItem]) -> None:
        """Handle show preview toggle."""
        if not item:
            return
        params = ClipParams.from_dict(item.filter_params)
        params.show_preview = value
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _emit_params_changed(self, item: PipelineItem) -> None:
        """Emit parameters changed via callback."""
        if hasattr(self, '_on_params_changed_callback') and self._on_params_changed_callback:
            self._on_params_changed_callback(item.id, item.filter_params)

