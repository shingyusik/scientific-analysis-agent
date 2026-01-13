
import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from viewmodels.table_viewmodel import TableViewModel

@pytest.fixture
def table_vm(qapp):
    return TableViewModel()

@patch('viewmodels.table_viewmodel.get_pipeline_viewmodel')
@patch('viewmodels.table_viewmodel.vtk_to_numpy')
def test_set_data_source_success(mock_vtk_to_numpy, mock_get_vm, table_vm):
    # Setup PipelineVM and Item
    mock_pipeline = MagicMock()
    mock_item = MagicMock()
    mock_item.vtk_data = MagicMock()
    mock_pipeline.items.get.return_value = mock_item
    mock_get_vm.return_value = mock_pipeline
    
    # Setup VTK Data
    mock_point_data = MagicMock()
    mock_item.vtk_data.GetPointData.return_value = mock_point_data
    mock_item.vtk_data.GetNumberOfPoints.return_value = 5
    
    # Setup Arrays
    mock_point_data.GetNumberOfArrays.return_value = 2
    
    array1 = MagicMock()
    array1.GetName.return_value = "Scalar"
    array1.GetNumberOfComponents.return_value = 1
    
    array2 = MagicMock()
    array2.GetName.return_value = "Vector"
    array2.GetNumberOfComponents.return_value = 3
    
    def get_array_side_effect(index):
        if index == 0: return array1
        if index == 1: return array2
        return None
    mock_point_data.GetArray.side_effect = get_array_side_effect
    
    # Mock numpy conversion
    mock_vtk_to_numpy.side_effect = [
        np.array([10.0, 20.0, 30.0, 40.0, 50.0]), # Scalar
        np.array([[1,0,0], [0,1,0], [0,0,1], [1,1,1], [0,0,0]]) # Vector
    ]
    
    # Connect signal
    mock_signal = MagicMock()
    table_vm.data_updated.connect(mock_signal)
    
    # Execute
    success = table_vm.set_data_source("item1", "POINT")
    
    assert success is True
    assert table_vm.get_row_count() == 5
    
    # Headers: Index, Scalar, Vector_X, Vector_Y, Vector_Z
    headers = table_vm.get_column_headers()
    assert len(headers) == 5
    assert headers[1] == "Scalar"
    assert headers[2] == "Vector_X"
    
    mock_signal.assert_called_once()
    
    # Check data content
    data = table_vm.get_table_data()
    assert isinstance(data, np.ndarray)
    assert data.shape == (5, 5)  # 5 rows, 5 columns
    # Row 0: Index=0, Scalar=10, VecX=1, VecY=0, VecZ=0
    assert data[0, 0] == 0
    assert data[0, 1] == 10.0
    assert data[0, 2] == 1

def test_clear(table_vm):
    # Manually populate
    table_vm._data_array = np.array([[1, 2]])
    table_vm._column_headers = ["A", "B"]
    
    mock_signal = MagicMock()
    table_vm.data_updated.connect(mock_signal)
    
    table_vm.clear()
    
    assert table_vm.get_table_data() is None
    assert len(table_vm.get_column_headers()) == 0
    mock_signal.assert_called_once()

@patch('viewmodels.table_viewmodel.get_pipeline_viewmodel')
def test_set_data_source_failure(mock_get_vm, table_vm):
    mock_get_vm.return_value = None # No pipeline VM
    assert table_vm.set_data_source("item1") is False

