"""Tools for LLM to create and manage visualizations (tables and graphs)."""

from typing import Optional, Dict, Any, List
from utils.logger import get_logger
from utils.tool_registry import expose_tool
from utils.app_context import get_pipeline_viewmodel

logger = get_logger("VisualizationTools")

# Store reference to main window for tab operations
# This will be set by main window during initialization
_main_window = None


def set_main_window(main_window):
    """Set the main window reference for tab operations."""
    global _main_window
    _main_window = main_window


@expose_tool(
    name="create_table_view",
    description="Create a new table view tab showing data from a pipeline item. Parameters: item_id (pipeline item ID), array_name (data array name), tab_name (optional custom name), array_type ('POINT' or 'CELL', default 'POINT'). Returns: Success message with tab ID or error."
)
def create_table_view(item_id: str, array_name: str, tab_name: Optional[str] = None, array_type: str = "POINT") -> str:
    if not _main_window:
        return "Error: Main window not initialized"
    
    pipeline_vm = get_pipeline_viewmodel()
    if not pipeline_vm:
        return "Error: Pipeline ViewModel not available"
    
    # Verify item exists
    item = pipeline_vm.items.get(item_id)
    if not item:
        return f"Error: Pipeline item '{item_id}' not found"
    
    # Generate tab name if not provided
    if not tab_name:
        tab_name = f"Table - {array_name}"
    
    # Create the tab
    from viewmodels.table_viewmodel import TableViewModel
    from views.table_view_widget import TableViewWidget
    
    table_vm = TableViewModel()
    success = table_vm.set_data_source(item_id, array_name, array_type)
    
    if not success:
        return f"Error: Failed to load data array '{array_name}' from item '{item_id}'"
    
    widget = TableViewWidget(table_vm)
    tab_id = _main_window._tabbed_view.add_tab_with_id(widget, "table", tab_name, pinned=False)
    
    # Switch to the new tab
    index = _main_window._tabbed_view.indexOf(widget)
    _main_window._tabbed_view.setCurrentIndex(index)
    
    info = table_vm.get_info()
    logger.info(f"Table view created: tab_id={tab_id}, array={array_name}, rows={info['row_count']}")
    
    return f"Created table view '{tab_name}' (ID: {tab_id}) showing {info['row_count']} rows from array '{array_name}'"


@expose_tool(
    name="create_graph_view",
    description="Create a new graph view tab visualizing data from a pipeline item. Parameters: graph_type (line/scatter/histogram/bar), item_id (pipeline item ID), y_array (Y-axis data), x_array (optional X-axis data or '__Index__'), tab_name (optional name), array_type ('POINT' or 'CELL'). Returns: Success message or error."
)
def create_graph_view(
    graph_type: str,
    item_id: str,
    y_array: str,
    x_array: Optional[str] = None,
    tab_name: Optional[str] = None,
    array_type: str = "POINT"
) -> str:
    if not _main_window:
        return "Error: Main window not initialized"
    
    pipeline_vm = get_pipeline_viewmodel()
    if not pipeline_vm:
        return "Error: Pipeline ViewModel not available"
    
    # Verify item exists
    item = pipeline_vm.items.get(item_id)
    if not item:
        return f"Error: Pipeline item '{item_id}' not found"
    
    # Default X array to index
    if not x_array:
        x_array = "__Index__"
    
    # Generate tab name if not provided
    if not tab_name:
        tab_name = f"Graph - {y_array}"
    
    # Create the tab
    from viewmodels.graph_viewmodel import GraphViewModel
    from views.graph_view_widget import GraphViewWidget
    
    graph_vm = GraphViewModel()
    
    # Set graph type
    if not graph_vm.set_graph_type(graph_type):
        return f"Error: Invalid graph type '{graph_type}'. Must be one of: {', '.join(graph_vm.GRAPH_TYPES)}"
    
    # Set data source
    success = graph_vm.set_data_source(item_id, x_array, y_array, array_type)
    
    if not success:
        return f"Error: Failed to load data arrays from item '{item_id}'"
    
    widget = GraphViewWidget(graph_vm)
    tab_id = _main_window._tabbed_view.add_tab_with_id(widget, "graph", tab_name, pinned=False)
    
    # Switch to the new tab
    index = _main_window._tabbed_view.indexOf(widget)
    _main_window._tabbed_view.setCurrentIndex(index)
    
    info = graph_vm.get_info()
    logger.info(f"Graph view created: tab_id={tab_id}, type={graph_type}, points={info['data_points']}")
    
    return f"Created {graph_type} graph '{tab_name}' (ID: {tab_id}) with {info['data_points']} data points"


@expose_tool(
    name="list_tabs",
    description="List all open tabs with their IDs, types, and names. Returns: Formatted string listing all tabs."
)
def list_tabs() -> str:
    if not _main_window:
        return "Error: Main window not initialized"
    
    all_tabs = _main_window._tabbed_view.get_all_tabs()
    
    if not all_tabs:
        return "No tabs are currently open"
    
    lines = ["Current open tabs:"]
    for tab_id, metadata in all_tabs.items():
        name = metadata['name']
        tab_type = metadata['type'].upper()
        pinned = " (Pinned)" if metadata.get('pinned', False) else ""
        lines.append(f"  - {tab_id}: {name} [{tab_type}]{pinned}")
    
    return "\n".join(lines)


@expose_tool(
    name="close_tab",
    description="Close a specific tab by its ID. Parameters: tab_id (ID of the tab to close). Returns: Success or error message. Note: Pinned tabs cannot be closed."
)
def close_tab(tab_id: str) -> str:
    if not _main_window:
        return "Error: Main window not initialized"
    
    metadata = _main_window._tabbed_view.get_tab_metadata(tab_id)
    if not metadata:
        return f"Error: Tab '{tab_id}' not found"
    
    if metadata.get('pinned', False):
        return f"Error: Tab '{tab_id}' is pinned and cannot be closed. Unpin it first."
    
    success = _main_window._tabbed_view.close_tab_by_id(tab_id)
    
    if success:
        logger.info(f"Tab closed via tool: {tab_id}")
        return f"Successfully closed tab '{tab_id}'"
    else:
        return f"Error: Failed to close tab '{tab_id}'"


@expose_tool(
    name="pin_tab",
    description="Pin or unpin a tab to prevent accidental closure. Parameters: tab_id (ID of the tab), pinned (True to pin, False to unpin, default True). Returns: Success or error message."
)
def pin_tab(tab_id: str, pinned: bool = True) -> str:
    if not _main_window:
        return "Error: Main window not initialized"
    
    metadata = _main_window._tabbed_view.get_tab_metadata(tab_id)
    if not metadata:
        return f"Error: Tab '{tab_id}' not found"
    
    success = _main_window._tabbed_view.set_tab_pinned(tab_id, pinned)
    
    if success:
        action = "pinned" if pinned else "unpinned"
        logger.info(f"Tab {action} via tool: {tab_id}")
        return f"Successfully {action} tab '{tab_id}'"
    else:
        return f"Error: Failed to modify pin status of tab '{tab_id}'"
