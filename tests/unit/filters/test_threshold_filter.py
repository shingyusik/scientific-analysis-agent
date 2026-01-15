import pytest
from unittest.mock import MagicMock
import vtk
import numpy as np
from filters.threshold_filter import ThresholdFilter, ThresholdParams

@pytest.fixture
def render_service():
    return MagicMock()

@pytest.fixture
def threshold_filter(render_service):
    return ThresholdFilter(render_service)

@pytest.fixture
def sample_data():
    """Create sample VTK data with scalar and vector arrays."""
    source = vtk.vtkSphereSource()
    source.SetThetaResolution(10)
    source.SetPhiResolution(10)
    source.Update()
    data = source.GetOutput()
    
    num_points = data.GetNumberOfPoints()
    
    # Scalar array: 0 to num_points-1
    scalars = vtk.vtkFloatArray()
    scalars.SetName("Pressure")
    scalars.SetNumberOfTuples(num_points)
    for i in range(num_points):
        scalars.SetValue(i, float(i))
    data.GetPointData().AddArray(scalars)
    
    # Vector array: [i, i*2, i*3]
    vectors = vtk.vtkFloatArray()
    vectors.SetName("Velocity")
    vectors.SetNumberOfComponents(3)
    vectors.SetNumberOfTuples(num_points)
    for i in range(num_points):
        vectors.SetTuple3(i, float(i), float(i*2), float(i*3))
    data.GetPointData().AddArray(vectors)
    
    return data

def test_threshold_params():
    params = ThresholdParams(array_name="Test", lower_bound=10.0, upper_bound=20.0)
    d = params.to_dict()
    assert d["array_name"] == "Test"
    assert d["lower_bound"] == 10.0
    
    new_p = ThresholdParams.from_dict(d)
    assert new_p.array_name == "Test"
    assert new_p.lower_bound == 10.0

def test_apply_scalar_between(threshold_filter, sample_data):
    params = {
        "array_name": "Pressure",
        "lower_bound": 10.0,
        "upper_bound": 20.0,
        "method": "between",
        "attribute_type": "POINT"
    }
    actor, output = threshold_filter.apply_filter(sample_data, params)
    
    assert output is not None
    assert output.GetNumberOfPoints() > 0
    
    # Check values: With AllScalars=0, some points might be outside range,
    # but at least some points should be inside.
    res_scalars = [output.GetPointData().GetArray("Pressure").GetValue(i) 
                   for i in range(output.GetNumberOfPoints())]
    assert any(10.0 <= val <= 20.0 for val in res_scalars)

def test_apply_vector_component(threshold_filter, sample_data):
    # Velocity_Y is [0, 2, 4, ..., i*2]
    # Filter Velocity_Y between 15 and 25
    params = {
        "array_name": "Velocity",
        "component": 1, # Y component
        "lower_bound": 15.0,
        "upper_bound": 25.0,
        "method": "between",
        "attribute_type": "POINT"
    }
    actor, output = threshold_filter.apply_filter(sample_data, params)
    
    assert output is not None
    assert output.GetNumberOfPoints() > 0
    
    res_vectors = [output.GetPointData().GetArray("Velocity").GetTuple3(i)[1]
                   for i in range(output.GetNumberOfPoints())]
    assert any(15.0 <= val <= 25.0 for val in res_vectors)

def test_apply_above(threshold_filter, sample_data):
    # Pressure > 40 (user enters 40 in upper_bound)
    params = {
        "array_name": "Pressure",
        "upper_bound": 40.0,
        "method": "above",
        "attribute_type": "POINT"
    }
    actor, output = threshold_filter.apply_filter(sample_data, params)
    
    assert output is not None
    assert output.GetNumberOfPoints() > 0
    
    res_scalars = [output.GetPointData().GetArray("Pressure").GetValue(i) 
                   for i in range(output.GetNumberOfPoints())]
    assert any(val >= 40.0 for val in res_scalars)

def test_apply_below(threshold_filter, sample_data):
    # Pressure < 10 (user enters 9 in lower_bound)
    params = {
        "array_name": "Pressure",
        "lower_bound": 9.0,
        "method": "below",
        "attribute_type": "POINT"
    }
    actor, output = threshold_filter.apply_filter(sample_data, params)
    
    assert output is not None
    assert output.GetNumberOfPoints() > 0
    
    res_scalars = [output.GetPointData().GetArray("Pressure").GetValue(i) 
                   for i in range(output.GetNumberOfPoints())]
    assert any(val <= 9.0 for val in res_scalars)
