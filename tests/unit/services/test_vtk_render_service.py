
import pytest
from unittest.mock import MagicMock, patch, ANY
import vtk
from services.vtk_render_service import VTKRenderService

@pytest.fixture
def render_service():
    return VTKRenderService()

def test_create_cone_source(render_service):
    actor, data = render_service.create_cone_source()
    
    assert isinstance(actor, vtk.vtkActor)
    assert isinstance(data, vtk.vtkPolyData) # Cone output is polydata
    
    # Check if vector field was added
    assert data.GetPointData().HasArray("VectorField") == 1
    
def test_create_actor(render_service):
    mock_data = vtk.vtkPolyData()
    actor = render_service.create_actor(mock_data)
    
    assert isinstance(actor, vtk.vtkActor)
    mapper = actor.GetMapper()
    assert isinstance(mapper, vtk.vtkPolyDataMapper)
    
def test_set_representation(render_service):
    actor = vtk.vtkActor()
    # Need a mapper with input for set_representation to work logically 
    # (though mock might be easier, let's use real simple vtk objects)
    cube = vtk.vtkCubeSource()
    cube.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(cube.GetOutput())
    actor.SetMapper(mapper)
    
    # Test Wireframe
    render_service.set_representation(actor, "Wireframe")
    assert actor.GetProperty().GetRepresentationAsString() == "Wireframe"
    assert render_service.get_representation_style(actor) == "Wireframe"
    
    # Test Points
    render_service.set_representation(actor, "Points")
    assert actor.GetProperty().GetRepresentationAsString() == "Points"
    
    # Test Surface
    render_service.set_representation(actor, "Surface")
    assert actor.GetProperty().GetRepresentationAsString() == "Surface"

def test_set_opacity(render_service):
    actor = vtk.vtkActor()
    render_service.set_opacity(actor, 0.5)
    assert actor.GetProperty().GetOpacity() == 0.5

def test_visual_properties(render_service):
    actor = vtk.vtkActor()
    
    render_service.set_point_size(actor, 5.0)
    assert actor.GetProperty().GetPointSize() == 5.0
    
    render_service.set_line_width(actor, 2.0)
    assert actor.GetProperty().GetLineWidth() == 2.0

def test_fit_scalar_range(render_service):
    # Setup data with scalars
    source = vtk.vtkCubeSource()
    source.Update()
    data = source.GetOutput()
    
    # Add dummy scalars
    scalars = vtk.vtkFloatArray()
    scalars.SetName("TestScalars")
    scalars.SetNumberOfComponents(1)
    scalars.InsertNextValue(0.0)
    scalars.InsertNextValue(10.0)
    # Fill rest to match points? 
    # Cube has 24 points or 8 points depending on generic/source
    for _ in range(data.GetNumberOfPoints() - 2):
        scalars.InsertNextValue(5.0)
        
    data.GetPointData().SetScalars(scalars)
    
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(data)
    mapper.ScalarVisibilityOn()
    
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    
    # Pre-condition: Range might be default (0, 1)
    
    success = render_service.fit_scalar_range(actor)
    
    assert success is True
    rng = mapper.GetScalarRange()
    assert rng[0] == 0.0
    assert rng[1] == 10.0

def test_set_custom_scalar_range(render_service):
    mapper = vtk.vtkPolyDataMapper()
    mapper.ScalarVisibilityOn()
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    
    success = render_service.set_custom_scalar_range(actor, -5.0, 5.0)
    
    assert success is True
    rng = mapper.GetScalarRange()
    assert rng[0] == -5.0
    assert rng[1] == 5.0

@patch("services.vtk_render_service.VTKRenderService._get_data_object")
@patch("services.vtk_render_service.logger")
def test_set_color_by_solid(mock_logger, mock_get_data_obj, render_service):
    actor = MagicMock()
    mapper = MagicMock()
    actor.GetMapper.return_value = mapper
    
    render_service.set_color_by(actor, "__SolidColor__")
    
    mapper.ScalarVisibilityOff.assert_called_once()
    mock_logger.info.assert_called_with("Color By Set: Solid Color")

