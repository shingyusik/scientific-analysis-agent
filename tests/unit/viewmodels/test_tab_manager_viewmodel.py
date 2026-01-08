
import pytest
from unittest.mock import MagicMock, patch
from viewmodels.tab_manager_viewmodel import TabManagerViewModel

@pytest.fixture
def tab_vm(qapp):
    return TabManagerViewModel()

def test_initial_state(tab_vm):
    assert len(tab_vm._tab_registry) == 0

def test_create_vtk_view(tab_vm):
    mock_signal = MagicMock()
    tab_vm.vtk_view_requested.connect(mock_signal)
    
    result = tab_vm.create_vtk_view("Test View")
    
    assert "requested" in result
    mock_signal.assert_called_with("Test View")

@patch('viewmodels.tab_manager_viewmodel.get_pipeline_viewmodel')
def test_create_table_view(mock_get_vm, tab_vm):
    # Mock pipeline VM and item
    mock_pipeline = MagicMock()
    mock_item = MagicMock()
    mock_item.id = "item1"
    mock_item.name = "Item 1"
    mock_pipeline.items.get.return_value = mock_item
    mock_pipeline.selected_item = mock_item
    mock_get_vm.return_value = mock_pipeline
    
    mock_signal = MagicMock()
    tab_vm.table_view_requested.connect(mock_signal)
    
    # Test with everything provided
    tab_vm.create_table_view("item1", "Test Table", "POINT")
    mock_signal.assert_called_with("item1", "Test Table", "POINT")
    
    # Test default values (should use selected item and auto-generated name)
    tab_vm.create_table_view()
    mock_signal.assert_called_with("item1", "Table - Item 1", "POINT")

@patch('viewmodels.tab_manager_viewmodel.get_pipeline_viewmodel')
def test_create_graph_view(mock_get_vm, tab_vm):
    # Mock setup similar to table view
    mock_pipeline = MagicMock()
    mock_item = MagicMock()
    mock_item.id = "item1"
    mock_item.name = "Item 1"
    # Mock get_data_arrays to return a list of tuples (name, range)
    mock_item.get_data_arrays.return_value = [("Array1", (0, 1))]
    
    mock_pipeline.items.get.return_value = mock_item
    mock_pipeline.selected_item = mock_item
    mock_get_vm.return_value = mock_pipeline
    
    mock_signal = MagicMock()
    tab_vm.graph_view_requested.connect(mock_signal)
    
    # Test with explicit params
    tab_vm.create_graph_view("line", "item1", "Array1", "Index", "Test Graph")
    mock_signal.assert_called_with("line", "item1", "Array1", "Index", "Test Graph", "POINT")
    
    # Test defaults
    # Should default to "line", selected item (item1), first array (Array1), "Index" x-axis
    tab_vm.create_graph_view()
    mock_signal.assert_called_with("line", "item1", "Array1", "__Index__", "Graph - Array1", "POINT")

def test_tab_lifecycle(tab_vm):
    # Register
    tab_vm.register_tab("tab1", "Tab 1", "vtk")
    assert "tab1" in tab_vm._tab_registry
    assert tab_vm._tab_registry["tab1"]["name"] == "Tab 1"
    assert tab_vm._tab_registry["tab1"]["type"] == "vtk"
    
    # Rename
    tab_vm.update_tab_name("tab1", "New Name")
    assert tab_vm._tab_registry["tab1"]["name"] == "New Name"
    
    # Pin
    mock_pin_sig = MagicMock()
    tab_vm.tab_pin_requested.connect(mock_pin_sig)
    tab_vm.pin_tab("tab1", True)
    mock_pin_sig.assert_called_with("tab1", True)
    
    # Sync pin status
    tab_vm.update_tab_pin_status("tab1", True)
    assert tab_vm._tab_registry["tab1"]["pinned"] is True
    
    # Close
    mock_close_sig = MagicMock()
    tab_vm.tab_close_requested.connect(mock_close_sig)
    tab_vm.close_tab("tab1")
    mock_close_sig.assert_called_with("tab1")
    
    # Unregister
    tab_vm.unregister_tab("tab1")
    assert "tab1" not in tab_vm._tab_registry
    
def test_list_tabs(tab_vm):
    assert "No tabs" in tab_vm.list_tabs()
    
    tab_vm.register_tab("tab1", "Tab 1", "vtk")
    listing = tab_vm.list_tabs()
    assert "Tab 1" in listing
    assert "VTK" in listing
