from dataclasses import dataclass, field
from typing import Any, Tuple, Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QHBoxLayout, 
    QLabel, QPushButton, QLineEdit, QComboBox, QGridLayout
)
from PySide6.QtCore import Signal
from filters.filter_base import FilterBase
from models.pipeline_item import PipelineItem
import vtk
from utils.logger import get_logger, log_execution
from utils.tool_registry import expose_filter_tool
from utils.app_context import get_pipeline_viewmodel

logger = get_logger("CalculatorFilter")


@dataclass
class CalculatorParams:
    """Parameters for calculator filter."""
    
    expression: str = ""
    result_array_name: str = "Result"
    attribute_type: str = "POINT"  # "POINT" or "CELL"
    
    def to_dict(self) -> dict:
        return {
            "expression": self.expression,
            "result_array_name": self.result_array_name,
            "attribute_type": self.attribute_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "CalculatorParams":
        return cls(
            expression=data.get("expression", ""),
            result_array_name=data.get("result_array_name", "Result"),
            attribute_type=data.get("attribute_type", "POINT"),
        )


# Function buttons configuration at module level for automatic description generation
_FUNCTION_BUTTONS = [
    # Row 1
    [("Clear", "CLEAR"), ("(", "("), (")", ")"), ("iHat", "iHat"), ("jHat", "jHat"), ("kHat", "kHat")],
    # Row 2
    [("sin", "sin("), ("cos", "cos("), ("tan", "tan("), ("abs", "abs("), ("sqrt", "sqrt("), ("+", "+")],
    # Row 3
    [("asin", "asin("), ("acos", "acos("), ("atan", "atan("), ("ceil", "ceil("), ("floor", "floor("), ("-", "-")],
    # Row 4
    [("sinh", "sinh("), ("cosh", "cosh("), ("tanh", "tanh("), ("x^y", "^"), ("exp", "exp("), ("*", "*")],
    # Row 5
    [("dot", "dot("), ("mag", "mag("), ("norm", "norm("), ("ln", "ln("), ("log10", "log10("), ("/", "/")],
]

# Auto-generate supported functions list from _FUNCTION_BUTTONS
_EXCLUDED = {"Clear", "(", ")", "+", "-", "*", "/", "x^y"}
_SUPPORTED_FUNCTIONS = ", ".join([
    btn[0] for row in _FUNCTION_BUTTONS for btn in row if btn[0] not in _EXCLUDED
])
_OPERATORS = "+, -, *, /, ^, (, )"

_TOOL_DESCRIPTION = (
    "Applies a Calculator filter to create a derived variable using a mathematical expression.\n"
    "Parameters:\n"
    "- 'expression': Mathematical expression.\n"
    "- 'result_array_name': Name for the new array (default: 'Result').\n"
    "- 'attribute_type': 'POINT' or 'CELL' data (default: 'POINT').\n"
    "- 'item_id': ID of the object to apply (optional if an item is selected).\n"
    f"Supported functions: {_SUPPORTED_FUNCTIONS}.\n"
    f"Supported operators: {_OPERATORS}.\n"
    "Expression examples:\n"
    "- 'Temp * 2': Multiply scalar by constant.\n"
    "- 'Pressure + 100': Add constant to scalar.\n"
    "- 'mag(Velocity)': Vector magnitude.\n"
    "- 'dot(Velocity, iHat)': Extract X component of vector.\n"
    "- 'dot(Velocity, jHat)': Extract Y component of vector.\n"
    "- 'sqrt(U^2 + V^2)': Compute magnitude from components.\n"
    "- 'ln(Temp) / log10(Pressure)': Logarithm operations.\n"
    "Returns the ID of the new calculator item."
)

_UPDATE_DESCRIPTION = (
    "Updates the parameters of an existing Calculator filter.\n"
    "Parameters:\n"
    "- 'expression': New mathematical expression.\n"
    "- 'result_array_name': New name for the result array.\n"
    "- 'attribute_type': 'POINT' or 'CELL'.\n"
    "- 'item_id': The ID of the calculator filter item to update. REQUIRED.\n"
    f"Supported functions: {_SUPPORTED_FUNCTIONS}.\n"
    f"Supported operators: {_OPERATORS}.\n"
    "Expression examples:\n"
    "- 'Temp * 2': Multiply scalar by constant.\n"
    "- 'mag(Velocity)': Vector magnitude.\n"
    "- 'dot(Velocity, iHat)': Extract X component of vector."
)


class CalculatorFilter(FilterBase):
    """Calculator filter - creates derived variables using mathematical expressions."""
    
    # Reference module-level constants
    FUNCTION_BUTTONS = _FUNCTION_BUTTONS
    
    def __init__(self, render_service):
        super().__init__(render_service)
        self._params_widget: Optional[QWidget] = None
        self._expression_edit: Optional[QLineEdit] = None
        self._scalar_combo: Optional[QComboBox] = None
        self._vector_combo: Optional[QComboBox] = None
    
    @property
    def apply_immediately(self) -> bool:
        return False
    
    @property
    def filter_type(self) -> str:
        return "calculator_filter"
    
    @property
    def display_name(self) -> str:
        return "Calculator"
    
    @property
    def params_class(self) -> type:
        return CalculatorParams
    
    @staticmethod
    def _format_calculator_result(result_item, params: dict, target_item) -> str:
        """Custom result formatter for Calculator filter."""
        result_name = params.get("result_array_name", "Result")
        attr_type = params.get("attribute_type", "POINT")
        expression = params.get("expression", "")
        
        if not result_item.vtk_data:
            return f"Error: Calculator failed - no output data."
        
        # Get the result array
        if attr_type == "CELL":
            arr = result_item.vtk_data.GetCellData().GetArray(result_name)
        else:
            arr = result_item.vtk_data.GetPointData().GetArray(result_name)
        
        if arr:
            count = arr.GetNumberOfTuples()
            return (
                f"Successfully applied Calculator to '{target_item.name}'.\n"
                f"Expression: '{expression}'\n"
                f"Created array '{result_name}' with {count} values.\n"
                f"New item: '{result_item.name}' (id: {result_item.id})"
            )
        else:
            return (
                f"Error: Calculator expression failed.\n"
                f"Expression: '{expression}'\n"
                f"Array '{result_name}' was not created.\n"
                f"Check if variable names in the expression exist in the data."
            )
    
    @expose_filter_tool(
        name="apply_calculator_filter",
        description=_TOOL_DESCRIPTION,
        params_model=CalculatorParams,
        update_description=_UPDATE_DESCRIPTION,
        result_formatter=_format_calculator_result.__func__  # Pass the function, not the staticmethod
    )
    @log_execution(start_msg="Calculator Filter Started", end_msg="Calculator Filter Finished")
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        """Apply calculator filter using vtkArrayCalculator."""
        calc_params = CalculatorParams.from_dict(params)
        expression = calc_params.expression
        result_name = calc_params.result_array_name
        attr_type = calc_params.attribute_type
        
        if not expression.strip():
            logger.warning("Empty expression provided")
            # Return original data with no changes
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputData(data)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            return actor, data
        
        calculator = vtk.vtkArrayCalculator()
        calculator.SetInputData(data)
        
        # Set attribute type
        if attr_type == "CELL":
            calculator.SetAttributeTypeToCellData()
            data_attrs = data.GetCellData()
        else:
            calculator.SetAttributeTypeToPointData()
            data_attrs = data.GetPointData()
        
        # Register all available arrays
        for i in range(data_attrs.GetNumberOfArrays()):
            arr = data_attrs.GetArray(i)
            if arr:
                name = arr.GetName()
                num_components = arr.GetNumberOfComponents()
                if num_components == 1:
                    calculator.AddScalarArrayName(name)
                elif num_components == 3:
                    calculator.AddVectorArrayName(name)
                else:
                    # For other component counts, add as scalar
                    calculator.AddScalarArrayName(name)
        
        # Set expression and result name
        calculator.SetFunction(expression)
        calculator.SetResultArrayName(result_name)
        
        try:
            calculator.Update()
            output = calculator.GetOutput()
            
            # Check if result was created
            if attr_type == "CELL":
                result_arr = output.GetCellData().GetArray(result_name)
            else:
                result_arr = output.GetPointData().GetArray(result_name)
            
            if result_arr is None:
                logger.error(f"Calculator failed to create result array '{result_name}'")
        except Exception as e:
            logger.error(f"Calculator error: {e}")
            output = data
        
        # Create mapper and actor
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(output)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        return actor, output
    
    def create_default_params(self) -> dict:
        """Create default calculator parameters."""
        return CalculatorParams().to_dict()
    
    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None,
                            on_params_changed: Optional[callable] = None) -> Optional[QWidget]:
        """Create calculator filter parameters widget."""
        self._on_params_changed_callback = on_params_changed
        
        widget = QWidget(parent)
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        params = CalculatorParams.from_dict(item.filter_params if item else self.create_default_params())
        
        group = QGroupBox("Filter Parameters")
        main_layout = QVBoxLayout(group)
        
        # Expression input
        expr_layout = QHBoxLayout()
        expr_layout.addWidget(QLabel("Expression:"))
        self._expression_edit = QLineEdit()
        self._expression_edit.setText(params.expression)
        self._expression_edit.setPlaceholderText("e.g., Temp * 2, mag(Velocity)")
        self._expression_edit.textChanged.connect(lambda t: self._on_expression_changed(t, item))
        expr_layout.addWidget(self._expression_edit)
        main_layout.addLayout(expr_layout)
        
        # Result name and attribute type
        form_layout = QFormLayout()
        
        result_edit = QLineEdit()
        result_edit.setText(params.result_array_name)
        result_edit.textChanged.connect(lambda t: self._on_result_name_changed(t, item))
        form_layout.addRow("Result Name:", result_edit)
        
        attr_combo = QComboBox()
        attr_combo.addItems(["Point Data", "Cell Data"])
        attr_combo.setCurrentIndex(0 if params.attribute_type == "POINT" else 1)
        attr_combo.currentIndexChanged.connect(lambda i: self._on_attr_type_changed(i, item))
        form_layout.addRow("Attribute:", attr_combo)
        
        main_layout.addLayout(form_layout)
        
        # Variable insertion section
        var_group = QGroupBox("Insert Variable")
        var_layout = QVBoxLayout(var_group)
        
        # Get available arrays from parent item
        scalars, vectors = self._get_available_arrays(item)
        
        # Scalar dropdown
        scalar_row = QHBoxLayout()
        scalar_row.addWidget(QLabel("Scalars:"))
        self._scalar_combo = QComboBox()
        self._scalar_combo.addItem("Select Scalar...")
        self._scalar_combo.addItems(scalars)
        scalar_row.addWidget(self._scalar_combo)
        scalar_insert_btn = QPushButton("Insert")
        scalar_insert_btn.clicked.connect(self._insert_scalar)
        scalar_row.addWidget(scalar_insert_btn)
        var_layout.addLayout(scalar_row)
        
        # Vector dropdown with component buttons
        vector_row = QHBoxLayout()
        vector_row.addWidget(QLabel("Vectors:"))
        self._vector_combo = QComboBox()
        self._vector_combo.addItem("Select Vector...")
        self._vector_combo.addItems(vectors)
        vector_row.addWidget(self._vector_combo)
        
        # Component buttons
        for label, component in [("X", "iHat"), ("Y", "jHat"), ("Z", "kHat"), ("mag", "mag")]:
            btn = QPushButton(label)
            btn.setFixedWidth(30)
            btn.clicked.connect(lambda checked, c=component: self._insert_vector_component(c))
            vector_row.addWidget(btn)
        
        vector_insert_btn = QPushButton("Insert")
        vector_insert_btn.clicked.connect(self._insert_vector)
        vector_row.addWidget(vector_insert_btn)
        var_layout.addLayout(vector_row)
        
        main_layout.addWidget(var_group)
        
        # Function buttons grid
        func_group = QGroupBox("Functions")
        func_grid = QGridLayout(func_group)
        func_grid.setSpacing(2)
        
        for row_idx, row in enumerate(self.FUNCTION_BUTTONS):
            for col_idx, (text, insert_text) in enumerate(row):
                btn = QPushButton(text)
                btn.setFixedWidth(50)
                if insert_text == "CLEAR":
                    btn.clicked.connect(self._clear_expression)
                else:
                    btn.clicked.connect(lambda checked, t=insert_text: self._insert_text(t))
                func_grid.addWidget(btn, row_idx, col_idx)
        
        main_layout.addWidget(func_group)
        
        layout.addWidget(group)
        self._params_widget = widget
        return widget
    
    def _get_available_arrays(self, item: Optional[PipelineItem]) -> Tuple[List[str], List[str]]:
        """Get scalar and vector array names from parent item."""
        scalars = []
        vectors = []
        
        if not item:
            return scalars, vectors
        
        # Get parent item
        pipeline_vm = get_pipeline_viewmodel()
        if not pipeline_vm:
            return scalars, vectors
        
        parent_id = item.parent_id
        parent = pipeline_vm.items.get(parent_id) if parent_id else None
        
        if not parent or not parent.vtk_data:
            return scalars, vectors
        
        # Get arrays from parent's point and cell data
        for data_type in [parent.vtk_data.GetPointData(), parent.vtk_data.GetCellData()]:
            for i in range(data_type.GetNumberOfArrays()):
                arr = data_type.GetArray(i)
                if arr:
                    name = arr.GetName()
                    if arr.GetNumberOfComponents() == 1:
                        if name not in scalars:
                            scalars.append(name)
                    elif arr.GetNumberOfComponents() == 3:
                        if name not in vectors:
                            vectors.append(name)
        
        return scalars, vectors
    
    def _insert_text(self, text: str) -> None:
        """Insert text at cursor position in expression."""
        if self._expression_edit:
            cursor_pos = self._expression_edit.cursorPosition()
            current = self._expression_edit.text()
            new_text = current[:cursor_pos] + text + current[cursor_pos:]
            self._expression_edit.setText(new_text)
            self._expression_edit.setCursorPosition(cursor_pos + len(text))
    
    def _clear_expression(self) -> None:
        """Clear the expression field."""
        if self._expression_edit:
            self._expression_edit.clear()
    
    def _insert_scalar(self) -> None:
        """Insert selected scalar name."""
        if self._scalar_combo and self._scalar_combo.currentIndex() > 0:
            self._insert_text(self._scalar_combo.currentText())
    
    def _insert_vector(self) -> None:
        """Insert selected vector name."""
        if self._vector_combo and self._vector_combo.currentIndex() > 0:
            self._insert_text(self._vector_combo.currentText())
    
    def _insert_vector_component(self, component: str) -> None:
        """Insert vector component expression."""
        if self._vector_combo and self._vector_combo.currentIndex() > 0:
            vec_name = self._vector_combo.currentText()
            if component == "mag":
                self._insert_text(f"mag({vec_name})")
            else:
                # Use dot product with unit vector for component
                self._insert_text(f"dot({vec_name}, {component})")
    
    def _on_expression_changed(self, text: str, item: Optional[PipelineItem]) -> None:
        """Handle expression change."""
        if not item:
            return
        params = CalculatorParams.from_dict(item.filter_params)
        params.expression = text
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _on_result_name_changed(self, text: str, item: Optional[PipelineItem]) -> None:
        """Handle result name change."""
        if not item:
            return
        params = CalculatorParams.from_dict(item.filter_params)
        params.result_array_name = text
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _on_attr_type_changed(self, index: int, item: Optional[PipelineItem]) -> None:
        """Handle attribute type change."""
        if not item:
            return
        params = CalculatorParams.from_dict(item.filter_params)
        params.attribute_type = "CELL" if index == 1 else "POINT"
        item.filter_params = params.to_dict()
        self._emit_params_changed(item)
    
    def _emit_params_changed(self, item: PipelineItem) -> None:
        """Emit parameters changed via callback."""
        if hasattr(self, '_on_params_changed_callback') and self._on_params_changed_callback:
            logger.debug(f"Calculator parameters updated for {item.id}")
            self._on_params_changed_callback(item.id, item.filter_params)
