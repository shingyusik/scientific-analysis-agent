
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
