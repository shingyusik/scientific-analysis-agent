
import pytest
from unittest.mock import MagicMock, patch, ANY
from PySide6.QtCore import QObject
from viewmodels.vtk_viewmodel import VTKViewModel

@pytest.fixture
def vtk_vm(qapp):
    render_service = MagicMock()
    vm = VTKViewModel(render_service)
    return vm

def test_initial_state(vtk_vm):
    assert vtk_vm._current_background[0] == "Warm Gray (Default)"
    assert vtk_vm.render_service is not None

def test_set_background_preset(vtk_vm):
    mock_slot = MagicMock()
    vtk_vm.background_changed.connect(mock_slot)
    
    vtk_vm.set_background_preset("Blue Gray")
    
    assert vtk_vm._current_background[0] == "Blue Gray"
    mock_slot.assert_called_with((0.2, 0.3, 0.4), None)

def test_reset_camera_tool(vtk_vm):
    mock_slot = MagicMock()
    vtk_vm.camera_reset_requested.connect(mock_slot)
    
    result = vtk_vm.reset_camera()
    
    assert "default view" in result
    mock_slot.assert_called_once()

def test_set_view_plane_tool(vtk_vm):
    mock_slot = MagicMock()
    vtk_vm.view_plane_requested.connect(mock_slot)
    
    result = vtk_vm.set_view_plane("xy")
    assert "XY" in result
    mock_slot.assert_called_with("xy")
    
    result_invalid = vtk_vm.set_view_plane("invalid")
    assert "Invalid" in result_invalid

def test_camera_state_tools(vtk_vm):
    # Test get_camera_state wrapping
    # We need to simulate the async response for get_camera_state_sync
    # Or mock the sync method directly since we are testing tool wrapper
    
    with patch.object(vtk_vm, "get_camera_state_sync") as mock_sync:
        mock_sync.return_value = {"position": [1, 2, 3]}
        result = vtk_vm.get_camera_state_tool()
        assert "position" in result
        assert "[1, 2, 3]" in result

    # Test apply_camera_state_tool
    mock_apply_slot = MagicMock()
    vtk_vm.camera_apply_requested.connect(mock_apply_slot)
    
    result = vtk_vm.apply_camera_state_tool(position=[10, 10, 10], zoom=2.0)
    
    assert "Applied" in result
    mock_apply_slot.assert_called_once()
    call_args = mock_apply_slot.call_args[0][0]
    assert call_args["position"] == [10, 10, 10]
    assert call_args["zoom"] == 2.0
    assert "view_up" not in call_args

def test_actor_management(vtk_vm):
    actor = MagicMock()
    
    mock_add_slot = MagicMock()
    vtk_vm.actor_added.connect(mock_add_slot)
    
    vtk_vm.add_actor(actor)
    mock_add_slot.assert_called_with(actor)
    
    mock_remove_slot = MagicMock()
    vtk_vm.actor_removed.connect(mock_remove_slot)
    
    vtk_vm.remove_actor(actor)
    mock_remove_slot.assert_called_with(actor)

def test_clear_scene(vtk_vm):
    mock_slot = MagicMock()
    vtk_vm.clear_scene_requested.connect(mock_slot)
    
    vtk_vm.clear_scene()
    mock_slot.assert_called_once()

def test_plane_preview_signals(vtk_vm):
    mock_preview = MagicMock()
    vtk_vm.plane_preview_requested.connect(mock_preview)
    vtk_vm.show_plane_preview([0,0,0], [1,0,0], (0,1,0,1,0,1))
    mock_preview.assert_called()
    
    mock_hide = MagicMock()
    vtk_vm.plane_preview_hide_requested.connect(mock_hide)
    vtk_vm.hide_plane_preview()
    mock_hide.assert_called_once()
