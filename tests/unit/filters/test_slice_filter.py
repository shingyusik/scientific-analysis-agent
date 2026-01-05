
import pytest
from unittest.mock import MagicMock, patch, ANY
import vtk
import numpy as np
from filters.slice_filter import SliceFilter, SliceParams
from models.pipeline_item import PipelineItem

@pytest.fixture
def render_service():
    return MagicMock()

@pytest.fixture
def slice_filter(render_service):
    return SliceFilter(render_service)

def test_slice_params():
    # Test defaults
    params = SliceParams()
    assert params.origin == [0.0, 0.0, 0.0]
    assert params.normal == [1.0, 0.0, 0.0]
    assert params.offsets == [0.0]
    assert params.show_preview is True
    
    # Test to/from dict
    data = params.to_dict()
    assert "origin" in data
    assert "normal" in data
    
    new_params = SliceParams.from_dict(data)
    assert new_params.origin == params.origin
    assert new_params.normal == params.normal

def test_filter_properties(slice_filter):
    assert slice_filter.filter_type == "slice_filter"
    assert slice_filter.display_name == "Slice"
    assert not slice_filter.apply_immediately

@patch("filters.slice_filter.sa_engine", None)
def test_apply_filter_single_slice(slice_filter):
    # Prepare dummy input data (cube source)
    source = vtk.vtkCubeSource()
    source.Update()
    input_data = source.GetOutput()
    
    params = {
        "origin": [0.0, 0.0, 0.0],
        "normal": [1.0, 0.0, 0.0],
        "offsets": [0.0]
    }
    
    actor, output_data = slice_filter.apply_filter(input_data, params)
    
    assert isinstance(actor, vtk.vtkActor)
    assert isinstance(output_data, vtk.vtkPolyData)
    
    # Cube cut by X normal at center should have points
    assert output_data.GetNumberOfPoints() > 0

@patch("filters.slice_filter.sa_engine", None)
def test_apply_filter_multiple_slices(slice_filter):
    source = vtk.vtkCubeSource()
    source.SetXLength(10.0)
    source.Update()
    input_data = source.GetOutput()
    
    params = {
        "origin": [0.0, 0.0, 0.0],
        "normal": [1.0, 0.0, 0.0],
        "offsets": [-2.0, 0.0, 2.0] # 3 slices
    }
    
    actor, output_data = slice_filter.apply_filter(input_data, params)
    
    # Should result in appended polydata
    assert output_data.GetNumberOfPoints() > 0
    # Ideally checking connectivity or number of separate polys, 
    # but exact point count depends on triangulation.
    # Just verify it ran without error and produced output.

def test_create_default_params(slice_filter):
    defaults = slice_filter.create_default_params()
    assert "origin" in defaults
    assert "offsets" in defaults

def test_preview_params(slice_filter):
    params = {
        "origin": [1.0, 2.0, 3.0],
        "normal": [0.0, 1.0, 0.0],
        "show_preview": False
    }
    origin, normal, visible = slice_filter.get_plane_preview_params(params)
    assert origin == [1.0, 2.0, 3.0]
    assert normal == [0.0, 1.0, 0.0]
    assert visible is False

def test_callbacks(slice_filter):
    # Test if callbacks update item params
    item = MagicMock(spec=PipelineItem)
    item.id = "test_item"
    item.filter_params = SliceParams().to_dict()
    
    callback = MagicMock()
    
    # We need to test the handler method directly because we can't easily spin up Qt event loop in unit test
    # without QTest (which requires more setup).
    # We'll invoke the logic that the widget would invoke.
    
    slice_filter._on_params_changed_callback = callback
    
    # Test Origin Change logic
    slice_filter._on_origin_changed(0, 5.0, item)
    assert item.filter_params["origin"][0] == 5.0
    callback.assert_called()
    
    # Test Normal Change logic
    slice_filter._on_normal_changed(1, 1.0, item)
    assert item.filter_params["normal"][1] == 1.0
    
    # Test Offsets Change logic
    slice_filter._on_offsets_changed([1.0, 2.0], item)
    assert item.filter_params["offsets"] == [1.0, 2.0]
