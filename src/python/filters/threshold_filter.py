from dataclasses import dataclass, field
from typing import Any, Tuple, Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Signal
from filters.filter_base import FilterBase
from models.pipeline_item import PipelineItem
from views.common_widgets import ScientificDoubleSpinBox
import vtk
from utils.logger import get_logger, log_execution
from utils.tool_registry import expose_filter_tool
from utils.constants import RESET_BUTTON_WIDTH, SPINBOX_WIDTH

logger = get_logger("ThresholdFilter")

@dataclass
class ThresholdParams:
    """Parameters for threshold filter."""
    array_name: str = ""
    component: int = 0
    lower_bound: float = 0.0
    upper_bound: float = 1.0
    method: str = "between"  # "between", "above", "below"
    attribute_type: str = "POINT"  # "POINT", "CELL"

    def to_dict(self) -> dict:
        return {
            "array_name": self.array_name,
            "component": self.component,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "method": self.method,
            "attribute_type": self.attribute_type,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ThresholdParams":
        return cls(
            array_name=data.get("array_name", ""),
            component=data.get("component", 0),
            lower_bound=data.get("lower_bound", 0.0),
            upper_bound=data.get("upper_bound", 1.0),
            method=data.get("method", "between"),
            attribute_type=data.get("attribute_type", "POINT"),
        )

class ThresholdFilter(FilterBase):
    """Threshold filter - filters data by scalar value or vector component range."""

    @property
    def apply_immediately(self) -> bool:
        return False

    @property
    def filter_type(self) -> str:
        return "threshold_filter"

    @property
    def display_name(self) -> str:
        return "Threshold"

    @property
    def params_class(self) -> type:
        return ThresholdParams

    @expose_filter_tool(
        name="apply_threshold_filter",
        description=(
            "Filters data by a scalar value range. Can also filter by individual components of vector fields.\n"
            "Parameters:\n"
            "- 'array_name': Name of the scalar or vector field to filter by.\n"
            "- 'component': Index of the component for vector fields (0=X, 1=Y, 2=Z). Use 0 for scalars.\n"
            "- 'lower_bound': Threshold value for 'below' method (keeps values <= this).\n"
            "- 'upper_bound': Threshold value for 'above' method (keeps values >= this). Also used as max for 'between'.\n"
            "- 'method': One of 'between', 'above', 'below'.\n"
            "- 'attribute_type': Either 'POINT' or 'CELL' data."
        ),
        params_model=ThresholdParams,
        update_description=(
            "Updates the parameters of an existing Threshold filter.\n"
            "Parameters:\n"
            "- 'array_name': Change the scalar or vector field to filter by.\n"
            "- 'component': Update the component index for vector fields.\n"
            "- 'lower_bound': Update the threshold for 'below' method.\n"
            "- 'upper_bound': Update the threshold for 'above' method.\n"
            "- 'method': Change the filtering method ('between', 'above', 'below').\n"
            "- 'item_id': The ID of the threshold filter item to update. REQUIRED."
        )
    )
    @log_execution(start_msg="Threshold Filter Calculation Started", end_msg="Threshold Filter Calculation Finished")
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        """Apply threshold filter using vtkThreshold."""
        p = ThresholdParams.from_dict(params)
        
        if not p.array_name:
            logger.warning("No array name specified for threshold filter")
            return None, data

        threshold = vtk.vtkThreshold()
        threshold.SetInputData(data)
        
        # Set attribute type and active array
        if p.attribute_type == "POINT":
            field_assoc = vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS
            data.GetPointData().SetActiveScalars(p.array_name)
        else:
            field_assoc = vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS
            data.GetCellData().SetActiveScalars(p.array_name)
            
        threshold.SetInputArrayToProcess(0, 0, 0, field_assoc, p.array_name)
        
        # Set component selection
        threshold.SetSelectedComponent(p.component)
        
        # Use more inclusive thresholding (cell is kept if ANY point satisfies condition)
        threshold.SetAllScalars(0)
        
        # In VTK 9.0+, vtkThreshold changed its API
        if hasattr(threshold, 'SetThresholdFunction'):
            if p.method == "between":
                threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)
                threshold.SetLowerThreshold(p.lower_bound)
                threshold.SetUpperThreshold(p.upper_bound)
            elif p.method == "above":
                # "above X" means values >= X. User enters X in upper_bound field.
                threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_UPPER)
                threshold.SetUpperThreshold(p.upper_bound)
            elif p.method == "below":
                # "below X" means values <= X. User enters X in lower_bound field.
                threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_LOWER)
                threshold.SetLowerThreshold(p.lower_bound)
        else:
            # Fallback for older VTK versions
            if p.method == "between":
                threshold.ThresholdBetween(p.lower_bound, p.upper_bound)
            elif p.method == "above":
                threshold.ThresholdByUpper(p.upper_bound)
            elif p.method == "below":
                threshold.ThresholdByLower(p.lower_bound)

        threshold.Update()
        output_data = threshold.GetOutput()
        
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(output_data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        return actor, output_data

    def create_default_params(self) -> dict:
        return ThresholdParams().to_dict()

    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None,
                            on_params_changed: Optional[callable] = None) -> Optional[QWidget]:
        """Create threshold filter parameters widget."""
        self._on_params_changed_callback = on_params_changed
        self._current_item = item
        
        params = ThresholdParams.from_dict(item.filter_params if item else self.create_default_params())
        
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Threshold Parameters")
        form_layout = QFormLayout(group)
        
        # Array selection
        self._array_combo = QComboBox()
        arrays = self._get_available_arrays(item)
        
        # If no array_name set but arrays available, use first one
        if arrays and not params.array_name:
            params.array_name = arrays[0][1]
            # Also update item's filter_params
            if item:
                item.filter_params["array_name"] = params.array_name
                # Set attribute_type based on first array
                params.attribute_type = "POINT" if arrays[0][0] == vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS else "CELL"
                item.filter_params["attribute_type"] = params.attribute_type
        
        for _, name, _ in arrays:
            self._array_combo.addItem(name)
        
        if params.array_name:
            self._array_combo.setCurrentText(params.array_name)
        
        self._array_combo.currentTextChanged.connect(lambda v: self._on_array_changed(v, item))
        form_layout.addRow("Array:", self._array_combo)
        
        # Component selection (ComboBox instead of radio buttons)
        self._comp_combo = QComboBox()
        self._update_component_ui(params.array_name, params.component, item)
        self._comp_combo.currentIndexChanged.connect(lambda idx: self._on_component_changed(idx, True, item))
        form_layout.addRow("Component:", self._comp_combo)
        
        # Method selection
        self._method_combo = QComboBox()
        self._method_combo.addItems(["between", "above", "below"])
        self._method_combo.setCurrentText(params.method)
        self._method_combo.currentTextChanged.connect(lambda v: self._on_method_changed(v, item))
        form_layout.addRow("Method:", self._method_combo)
        
        # Bounds selection
        self._lower_spin = ScientificDoubleSpinBox()
        self._lower_spin.setValue(params.lower_bound)
        self._lower_spin.valueChanged.connect(lambda v: self._on_bound_changed("lower", v, item))
        form_layout.addRow("Lower Bound:", self._lower_spin)
        
        self._upper_spin = ScientificDoubleSpinBox()
        self._upper_spin.setValue(params.upper_bound)
        self._upper_spin.valueChanged.connect(lambda v: self._on_bound_changed("upper", v, item))
        form_layout.addRow("Upper Bound:", self._upper_spin)
        
        # Update bound spinbox states based on initial method
        self._update_bound_states(params.method)
        
        layout.addWidget(group)
        return widget

    def _get_available_arrays(self, item: Optional[PipelineItem]) -> List[Tuple[int, str, int]]:
        """Get (type, name, components) of available point and cell arrays."""
        if not item or not item.parent_id:
            return []
            
        from utils.app_context import get_pipeline_viewmodel
        vm = get_pipeline_viewmodel()
        parent_item = vm.items.get(item.parent_id)
        if not parent_item or not parent_item.vtk_data:
            return []
            
        data = parent_item.vtk_data
        arrays = []
        
        # Point data
        pd = data.GetPointData()
        for i in range(pd.GetNumberOfArrays()):
            arr = pd.GetArray(i)
            arrays.append((vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS, arr.GetName(), arr.GetNumberOfComponents()))
            
        # Cell data
        cd = data.GetCellData()
        for i in range(cd.GetNumberOfArrays()):
            arr = cd.GetArray(i)
            arrays.append((vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, arr.GetName(), arr.GetNumberOfComponents()))
            
        return arrays

    def _update_component_ui(self, array_name: str, current_comp: int, item: Optional[PipelineItem]):
        """Update component combobox based on selected array."""
        self._comp_combo.blockSignals(True)
        self._comp_combo.clear()
        
        arrays = self._get_available_arrays(item)
        comp_count = 1
        for _, name, comps in arrays:
            if name == array_name:
                comp_count = comps
                break
        
        if comp_count > 1:
            labels = ["X", "Y", "Z"] if comp_count == 3 else [str(i) for i in range(comp_count)]
            for label in labels:
                self._comp_combo.addItem(label)
            self._comp_combo.setCurrentIndex(current_comp if current_comp < comp_count else 0)
            self._comp_combo.setEnabled(True)
        else:
            self._comp_combo.addItem("N/A")
            self._comp_combo.setEnabled(False)
        
        self._comp_combo.blockSignals(False)
    
    def _update_bound_states(self, method: str):
        """Update bound spinbox enabled states based on method."""
        if method == "between":
            self._lower_spin.setEnabled(True)
            self._upper_spin.setEnabled(True)
        elif method == "above":
            # "above X" means values > X, user enters X in Upper Bound
            self._lower_spin.setEnabled(False)
            self._upper_spin.setEnabled(True)
        elif method == "below":
            # "below X" means values < X, user enters X in Lower Bound
            self._lower_spin.setEnabled(True)
            self._upper_spin.setEnabled(False)

    def _on_array_changed(self, name: str, item: Optional[PipelineItem]):
        if not item: return
        p = ThresholdParams.from_dict(item.filter_params)
        p.array_name = name
        p.component = 0 # Reset to first component
        
        # Update attribute type based on array
        arrays = self._get_available_arrays(item)
        for attr_type_enum, arr_name, _ in arrays:
            if arr_name == name:
                p.attribute_type = "POINT" if attr_type_enum == vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS else "CELL"
                break
                
        item.filter_params = p.to_dict()
        self._update_component_ui(name, 0, item)
        self._emit_params_changed(item)

    def _on_component_changed(self, index: int, checked: bool, item: Optional[PipelineItem]):
        if not item or not checked: return
        p = ThresholdParams.from_dict(item.filter_params)
        p.component = index
        item.filter_params = p.to_dict()
        self._emit_params_changed(item)

    def _on_method_changed(self, method: str, item: Optional[PipelineItem]):
        if not item: return
        p = ThresholdParams.from_dict(item.filter_params)
        p.method = method
        item.filter_params = p.to_dict()
        # Update bound spinbox enabled states
        self._update_bound_states(method)
        self._emit_params_changed(item)

    def _on_bound_changed(self, limit: str, value: float, item: Optional[PipelineItem]):
        if not item: return
        p = ThresholdParams.from_dict(item.filter_params)
        if limit == "lower":
            p.lower_bound = value
        else:
            p.upper_bound = value
        item.filter_params = p.to_dict()
        self._emit_params_changed(item)

    def _emit_params_changed(self, item: PipelineItem):
        if hasattr(self, '_on_params_changed_callback') and self._on_params_changed_callback:
            self._on_params_changed_callback(item.id, item.filter_params)
