
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from viewmodels.graph_viewmodel import GraphViewModel

@pytest.fixture
def graph_vm(qapp):
    return GraphViewModel()

def test_set_graph_type(graph_vm):
    mock_signal = MagicMock()
    graph_vm.plot_config_updated.connect(mock_signal)
    
    # Valid
    assert graph_vm.set_graph_type("scatter") is True
    assert graph_vm.graph_type == "scatter"
    mock_signal.assert_called_once()
    
    # Invalid
    assert graph_vm.set_graph_type("infinite_donut") is False
    # Should remain unchanged ("scatter" from previous step)
    assert graph_vm.graph_type == "scatter" 

@patch('viewmodels.graph_viewmodel.get_pipeline_viewmodel')
@patch('viewmodels.graph_viewmodel.vtk_to_numpy')
def test_set_data_source_index_x(mock_vtk_to_numpy, mock_get_vm, graph_vm):
    # Setup VM/Item
    mock_pipeline = MagicMock()
    mock_item = MagicMock()
    mock_item.vtk_data = MagicMock()
    mock_pipeline.items.get.return_value = mock_item
    mock_get_vm.return_value = mock_pipeline
    
    # Setup Data
    mock_item.vtk_data.GetPointData.return_value.GetArray.return_value = MagicMock()
    mock_item.vtk_data.GetNumberOfPoints.return_value = 5
    
    # Mock Y array (Scalar)
    y_array = MagicMock()
    y_array.GetNumberOfComponents.return_value = 1
    mock_item.vtk_data.GetPointData.return_value.GetArray.return_value = y_array
    
    # Mock data [10, 20, 30, 40, 50]
    mock_vtk_to_numpy.return_value = np.array([10, 20, 30, 40, 50])
    
    # Execute
    success = graph_vm.set_data_source("item1", "__Index__", "ScalarArray")
    assert success is True
    
    data = graph_vm.get_plot_config("item1")
    np.testing.assert_array_equal(data["x_data"], np.array([0, 1, 2, 3, 4]))
    np.testing.assert_array_equal(data["y_data"], np.array([10, 20, 30, 40, 50]))

@patch('viewmodels.graph_viewmodel.get_pipeline_viewmodel')
@patch('viewmodels.graph_viewmodel.vtk_to_numpy')
def test_set_data_source_vector_component(mock_vtk_to_numpy, mock_get_vm, graph_vm):
    # Setup VM/Item
    mock_pipeline = MagicMock()
    mock_item = MagicMock()
    mock_item.vtk_data = MagicMock()
    mock_pipeline.items.get.return_value = mock_item
    mock_get_vm.return_value = mock_pipeline
    
    mock_item.vtk_data.GetNumberOfPoints.return_value = 3
    
    # Mock Vector Array
    vec_array = MagicMock()
    vec_array.GetNumberOfComponents.return_value = 3
    
    # Return vector array for Y retrieval
    mock_item.vtk_data.GetPointData.return_value.GetArray.return_value = vec_array
    
    # Mock return: [ [1,2,3], [4,5,6], [7,8,9] ]
    mock_vtk_to_numpy.return_value = np.array([[1,2,3], [4,5,6], [7,8,9]])
    
    # Extract component 1 (Y component)
    graph_vm.set_data_source("item1", "__Index__", "VectorArray", y_component=1)
    
    data = graph_vm.get_plot_config("item1")
    # Should get [2, 5, 8]
    np.testing.assert_array_equal(data["y_data"], np.array([2, 5, 8]))

def test_extract_component_invalid(graph_vm):
    # Test internal helper directly for edge case
    vtk_array = MagicMock()
    vtk_array.GetNumberOfComponents.return_value = 3
    
    with patch('viewmodels.graph_viewmodel.vtk_to_numpy') as mock_v2n:
        mock_v2n.return_value = np.array([[1,2,3]])
        
        # Invalid component index 99
        res = graph_vm._extract_component(vtk_array, 99, 1)
        # Should return zeros validation
        assert np.array_equal(res, np.zeros(1))

def test_style_update(graph_vm):
    # Test global style settings (line_color requires item_id since it's per-series)
    graph_vm.set_plot_style(title="My Plot", show_grid=True)
    
    mock_signal = MagicMock()
    graph_vm.plot_config_updated.connect(mock_signal)
    
    # Trigger another update to verify signal
    graph_vm.set_plot_style(show_grid=False, y_label="Value")
    mock_signal.assert_called_once()
    
    config = graph_vm.get_plot_config()
    assert config["title"] == "My Plot"
    assert config["y_label"] == "Value"
    assert config["show_grid"] is False
