
import pytest
from unittest.mock import MagicMock, patch
from viewmodels.pipeline_viewmodel import PipelineViewModel
from models.pipeline_item import PipelineItem

@pytest.fixture
def mock_render_service():
    service = MagicMock()
    # Mock create_cone_source
    service.create_cone_source.return_value = (MagicMock(), MagicMock())
    return service

@pytest.fixture
def mock_file_loader():
    return MagicMock()

@pytest.fixture
def pipeline_vm(qapp, mock_render_service, mock_file_loader):
    # qapp fixture ensures QApplication exists
    vm = PipelineViewModel(mock_render_service, mock_file_loader)
    return vm

def test_initial_state(pipeline_vm):
    assert len(pipeline_vm.items) == 0
    assert pipeline_vm.selected_item is None

def test_add_source(pipeline_vm):
    vtk_data = MagicMock()
    actor = MagicMock()
    
    item = pipeline_vm.add_source("Source 1", vtk_data, actor)
    
    assert len(pipeline_vm.items) == 1
    assert item.id in pipeline_vm.items
    assert pipeline_vm.items[item.id] == item
    assert item.name == "Source 1"

def test_select_item(pipeline_vm):
    item = pipeline_vm.add_source("Source 1", MagicMock(), MagicMock())
    
    # Connect mock to signal
    mock_slot = MagicMock()
    pipeline_vm.selection_changed.connect(mock_slot)
    
    result = pipeline_vm.select_item(item.id)
        
    assert pipeline_vm.selected_item == item
    assert "Selected item" in result
    mock_slot.assert_called_with(item)

def test_delete_item(pipeline_vm):
    item = pipeline_vm.add_source("Source 1", MagicMock(), MagicMock())
    
    # Select it first
    pipeline_vm.select_item(item.id)
    assert pipeline_vm.selected_item is not None
    
    # Connect mock to signal
    mock_slot = MagicMock()
    pipeline_vm.item_removed.connect(mock_slot)
    
    pipeline_vm.delete_item(item.id)
    
    assert len(pipeline_vm.items) == 0
    assert pipeline_vm.selected_item is None
    mock_slot.assert_called_with(item.id)

def test_get_pipeline_info(pipeline_vm):
    item = pipeline_vm.add_source("Source 1", MagicMock(), MagicMock())
    # Mock vtk data calls
    item.vtk_data.GetNumberOfPoints.return_value = 100
    item.vtk_data.GetNumberOfCells.return_value = 50
    
    info = pipeline_vm.get_pipeline_info()
    
    assert "Source 1" in info
    assert "points: 100" in info
    assert "cells: 50" in info

def test_set_visibility_tool(pipeline_vm):
    actor = MagicMock()
    item = pipeline_vm.add_source("Source 1", MagicMock(), actor)
    
    result = pipeline_vm.set_visibility(item.id, False)
    
    assert not item.visible
    actor.SetVisibility.assert_called_with(False)
    assert "hidden" in result

def test_hierarchy_deletion(pipeline_vm):
    # Create parent
    parent = pipeline_vm.add_source("Parent", MagicMock(), MagicMock())
    
    # Manually create child mocked item
    child_actor = MagicMock()
    child = PipelineItem("Child", "filter", vtk_data=MagicMock(), actor=child_actor, parent_id=parent.id)
    pipeline_vm._items[child.id] = child
    
    assert len(pipeline_vm.items) == 2
    
    # Delete parent should delete child
    pipeline_vm.delete_item(parent.id)
    assert len(pipeline_vm.items) == 0


def test_get_item_data_arrays_no_item(pipeline_vm):
    """Test get_item_data_arrays with no item selected."""
    result = pipeline_vm.get_item_data_arrays()
    assert "Error" in result
    assert "No item specified" in result


def test_get_item_data_arrays_not_found(pipeline_vm):
    """Test get_item_data_arrays with invalid item_id."""
    result = pipeline_vm.get_item_data_arrays("invalid-id")
    assert "Error" in result
    assert "not found" in result


def test_get_item_data_arrays_empty(pipeline_vm):
    """Test get_item_data_arrays with item that has no arrays."""
    vtk_data = MagicMock()
    # Mock point and cell data with no arrays
    pt_data = MagicMock()
    pt_data.GetNumberOfArrays.return_value = 0
    cell_data = MagicMock()
    cell_data.GetNumberOfArrays.return_value = 0
    vtk_data.GetPointData.return_value = pt_data
    vtk_data.GetCellData.return_value = cell_data
    
    item = pipeline_vm.add_source("Empty Data", vtk_data, MagicMock())
    
    result = pipeline_vm.get_item_data_arrays(item.id)
    assert "No data arrays available" in result


def test_get_item_data_arrays_with_arrays(pipeline_vm):
    """Test get_item_data_arrays with item that has both point and cell arrays."""
    vtk_data = MagicMock()
    
    # Mock point data with one scalar and one vector
    pt_arr1 = MagicMock()
    pt_arr1.GetName.return_value = "Temperature"
    pt_arr1.GetNumberOfComponents.return_value = 1
    
    pt_arr2 = MagicMock()
    pt_arr2.GetName.return_value = "Velocity"
    pt_arr2.GetNumberOfComponents.return_value = 3
    
    pt_data = MagicMock()
    pt_data.GetNumberOfArrays.return_value = 2
    pt_data.GetArray.side_effect = lambda i: [pt_arr1, pt_arr2][i]
    
    # Mock cell data with one scalar
    cell_arr = MagicMock()
    cell_arr.GetName.return_value = "Pressure"
    cell_arr.GetNumberOfComponents.return_value = 1
    
    cell_data = MagicMock()
    cell_data.GetNumberOfArrays.return_value = 1
    cell_data.GetArray.return_value = cell_arr
    
    vtk_data.GetPointData.return_value = pt_data
    vtk_data.GetCellData.return_value = cell_data
    
    item = pipeline_vm.add_source("Test Data", vtk_data, MagicMock())
    
    result = pipeline_vm.get_item_data_arrays(item.id)
    
    assert "Test Data" in result
    assert "Point Data" in result
    assert "Temperature" in result
    assert "scalar" in result
    assert "Velocity" in result
    assert "vector" in result
    assert "3 components" in result
    assert "Cell Data" in result
    assert "Pressure" in result


def test_get_item_data_arrays_with_selected_item(pipeline_vm):
    """Test get_item_data_arrays uses selected item when no item_id provided."""
    vtk_data = MagicMock()
    pt_arr = MagicMock()
    pt_arr.GetName.return_value = "Scalar"
    pt_arr.GetNumberOfComponents.return_value = 1
    
    pt_data = MagicMock()
    pt_data.GetNumberOfArrays.return_value = 1
    pt_data.GetArray.return_value = pt_arr
    
    cell_data = MagicMock()
    cell_data.GetNumberOfArrays.return_value = 0
    
    vtk_data.GetPointData.return_value = pt_data
    vtk_data.GetCellData.return_value = cell_data
    
    item = pipeline_vm.add_source("Selected Item", vtk_data, MagicMock())
    pipeline_vm.select_item(item.id)
    
    # Call without item_id, should use selected item
    result = pipeline_vm.get_item_data_arrays()
    
    assert "Selected Item" in result
    assert "Scalar" in result

