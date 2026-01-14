
import pytest
from unittest.mock import MagicMock, patch
import vtk
import numpy as np
from filters.calculator_filter import CalculatorFilter, CalculatorParams
from models.pipeline_item import PipelineItem


@pytest.fixture
def render_service():
    return MagicMock()


@pytest.fixture
def calculator_filter(render_service):
    return CalculatorFilter(render_service)


@pytest.fixture
def sample_data_with_arrays():
    """Create sample VTK data with scalar and vector arrays."""
    source = vtk.vtkSphereSource()
    source.SetThetaResolution(10)
    source.SetPhiResolution(10)
    source.Update()
    data = source.GetOutput()
    
    # Add a scalar array "Temp"
    num_points = data.GetNumberOfPoints()
    temp_array = vtk.vtkFloatArray()
    temp_array.SetName("Temp")
    temp_array.SetNumberOfTuples(num_points)
    for i in range(num_points):
        temp_array.SetValue(i, float(i * 10))
    data.GetPointData().AddArray(temp_array)
    
    # Add a vector array "Velocity"
    vel_array = vtk.vtkFloatArray()
    vel_array.SetName("Velocity")
    vel_array.SetNumberOfComponents(3)
    vel_array.SetNumberOfTuples(num_points)
    for i in range(num_points):
        vel_array.SetTuple3(i, float(i), float(i * 2), float(i * 3))
    data.GetPointData().AddArray(vel_array)
    
    return data


def test_calculator_params():
    """Test CalculatorParams creation and serialization."""
    # Test defaults
    params = CalculatorParams()
    assert params.expression == ""
    assert params.result_array_name == "Result"
    assert params.attribute_type == "POINT"
    
    # Test custom values
    params = CalculatorParams(
        expression="Temp * 2",
        result_array_name="DoubleTemp",
        attribute_type="CELL"
    )
    assert params.expression == "Temp * 2"
    
    # Test to/from dict
    data = params.to_dict()
    assert "expression" in data
    assert "result_array_name" in data
    
    new_params = CalculatorParams.from_dict(data)
    assert new_params.expression == params.expression
    assert new_params.result_array_name == params.result_array_name


def test_filter_properties(calculator_filter):
    """Test filter property values."""
    assert calculator_filter.filter_type == "calculator_filter"
    assert calculator_filter.display_name == "Calculator"
    assert not calculator_filter.apply_immediately
    assert calculator_filter.params_class == CalculatorParams


def test_apply_simple_scalar_expression(calculator_filter, sample_data_with_arrays):
    """Test simple scalar multiplication."""
    params = {
        "expression": "Temp * 2",
        "result_array_name": "DoubleTemp",
        "attribute_type": "POINT"
    }
    
    actor, output = calculator_filter.apply_filter(sample_data_with_arrays, params)
    
    assert isinstance(actor, vtk.vtkActor)
    assert isinstance(output, vtk.vtkDataSet)
    
    # Check result array exists
    result_arr = output.GetPointData().GetArray("DoubleTemp")
    assert result_arr is not None
    
    # Verify calculation (first few values)
    orig_arr = sample_data_with_arrays.GetPointData().GetArray("Temp")
    for i in range(min(5, result_arr.GetNumberOfTuples())):
        expected = orig_arr.GetValue(i) * 2
        actual = result_arr.GetValue(i)
        assert abs(actual - expected) < 0.001, f"Mismatch at {i}: {actual} != {expected}"


def test_apply_vector_magnitude(calculator_filter, sample_data_with_arrays):
    """Test vector magnitude function."""
    params = {
        "expression": "mag(Velocity)",
        "result_array_name": "VelMag",
        "attribute_type": "POINT"
    }
    
    actor, output = calculator_filter.apply_filter(sample_data_with_arrays, params)
    
    result_arr = output.GetPointData().GetArray("VelMag")
    assert result_arr is not None
    
    # Verify magnitude calculation for first point
    vel_arr = sample_data_with_arrays.GetPointData().GetArray("Velocity")
    v0, v1, v2 = vel_arr.GetTuple3(0)
    expected_mag = np.sqrt(v0**2 + v1**2 + v2**2)
    actual = result_arr.GetValue(0)
    assert abs(actual - expected_mag) < 0.001


def test_apply_math_functions(calculator_filter, sample_data_with_arrays):
    """Test math functions like sqrt, abs."""
    params = {
        "expression": "sqrt(Temp)",
        "result_array_name": "SqrtTemp",
        "attribute_type": "POINT"
    }
    
    actor, output = calculator_filter.apply_filter(sample_data_with_arrays, params)
    
    result_arr = output.GetPointData().GetArray("SqrtTemp")
    assert result_arr is not None


def test_empty_expression_handling(calculator_filter, sample_data_with_arrays):
    """Test that empty expression returns original data."""
    params = {
        "expression": "",
        "result_array_name": "Result",
        "attribute_type": "POINT"
    }
    
    actor, output = calculator_filter.apply_filter(sample_data_with_arrays, params)
    
    # Should return original data unchanged
    assert output.GetNumberOfPoints() == sample_data_with_arrays.GetNumberOfPoints()


def test_create_default_params(calculator_filter):
    """Test default parameters creation."""
    defaults = calculator_filter.create_default_params()
    assert "expression" in defaults
    assert "result_array_name" in defaults
    assert defaults["result_array_name"] == "Result"


def test_vector_dot_product(calculator_filter, sample_data_with_arrays):
    """Test dot product for vector component extraction."""
    params = {
        "expression": "dot(Velocity, iHat)",
        "result_array_name": "VelX",
        "attribute_type": "POINT"
    }
    
    actor, output = calculator_filter.apply_filter(sample_data_with_arrays, params)
    
    result_arr = output.GetPointData().GetArray("VelX")
    assert result_arr is not None
    
    # Verify X component extraction
    vel_arr = sample_data_with_arrays.GetPointData().GetArray("Velocity")
    for i in range(min(5, result_arr.GetNumberOfTuples())):
        expected = vel_arr.GetTuple3(i)[0]  # X component
        actual = result_arr.GetValue(i)
        assert abs(actual - expected) < 0.001


def test_function_buttons_configuration(calculator_filter):
    """Test that function buttons are properly configured."""
    buttons = calculator_filter.FUNCTION_BUTTONS
    assert len(buttons) == 5  # 5 rows
    
    # Check first row has Clear
    first_row = buttons[0]
    assert first_row[0] == ("Clear", "CLEAR")
    
    # Check some math functions exist
    all_funcs = [item for row in buttons for item in row]
    func_names = [f[0] for f in all_funcs]
    
    assert "sin" in func_names
    assert "cos" in func_names
    assert "mag" in func_names
    assert "dot" in func_names
    assert "sqrt" in func_names
