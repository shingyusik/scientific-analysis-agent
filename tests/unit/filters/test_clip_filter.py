
import pytest
from unittest.mock import MagicMock, patch, ANY
import vtk
import numpy as np
from filters.clip_filter import ClipFilter, ClipParams
from models.pipeline_item import PipelineItem

@pytest.fixture
def render_service():
    return MagicMock()

@pytest.fixture
def clip_filter(render_service):
    return ClipFilter(render_service)

def test_clip_params():
    params = ClipParams()
    assert params.origin == [0.0, 0.0, 0.0]
    assert params.normal == [1.0, 0.0, 0.0]
    
    data = params.to_dict()
    new_params = ClipParams.from_dict(data)
    assert new_params.origin == params.origin

def test_filter_properties(clip_filter):
    assert clip_filter.filter_type == "clip_filter"
    assert clip_filter.display_name == "Clip"

def test_apply_filter(clip_filter):
    # Cube source
    source = vtk.vtkCubeSource()
    source.SetCenter(0, 0, 0)
    source.SetXLength(2.0)
    source.Update()
    input_data = source.GetOutput()
    
    # Clip half of it
    # Normal X=1, Origin=0 -> Keep X > 0 (or X < 0 depending on vtkPlane orientation default)
    # Actually vtkClipDataSet removes data *inside* the implicit function (or outside depending on InsideOut)
    # Default vtkPlane function value is dot(normal, x-origin). Positive side usually kept.
    
    params = {
        "origin": [0.0, 0.0, 0.0],
        "normal": [1.0, 0.0, 0.0],
        "show_preview": False
    }
    
    actor, output_data = clip_filter.apply_filter(input_data, params)
    
    assert isinstance(actor, vtk.vtkActor)
    assert isinstance(output_data, vtk.vtkUnstructuredGrid) # Clip output is unstructured
    
    # Should have fewer cells/points than original or be modified
    # Original Cube has 24 points (generic).
    assert output_data.GetNumberOfPoints() > 0

def test_callbacks(clip_filter):
    item = MagicMock(spec=PipelineItem)
    item.id = "test_item"
    item.filter_params = ClipParams().to_dict()
    
    callback = MagicMock()
    clip_filter._on_params_changed_callback = callback
    
    # Test Origin
    clip_filter._on_origin_changed(1, 3.0, item)
    assert item.filter_params["origin"][1] == 3.0
    callback.assert_called()
    
    # Test Normal
    clip_filter._on_normal_changed(2, -1.0, item)
    assert item.filter_params["normal"][2] == -1.0
