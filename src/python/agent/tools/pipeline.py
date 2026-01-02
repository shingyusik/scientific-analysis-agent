from langchain_core.tools import tool
from agent.tools.context import get_pipeline_viewmodel
from utils.logger import get_logger, log_execution

logger = get_logger("AgentTools")

@tool
@log_execution(start_msg="[Tool] Get Pipeline Info", end_msg="[Tool] Info Retrieved")
def get_pipeline_info() -> str:
    """Get information about current loaded data and applied filters in the pipeline.
    Returns a summary of all items including their names, types, and visibility status.
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    items = vm.items
    if not items:
        return "No items in pipeline. Load a file first."
    
    result = []
    for item_id, item in items.items():
        info = f"- {item.name} (type: {item.item_type}, id: {item_id}, visible: {item.visible})"
        if item.parent_id:
            info += f" [parent: {item.parent_id}]"
        if item.vtk_data:
            num_points = item.vtk_data.GetNumberOfPoints()
            num_cells = item.vtk_data.GetNumberOfCells()
            info += f" [points: {num_points}, cells: {num_cells}]"
        result.append(info)
    
    selected = vm.selected_item
    selected_info = f"\nCurrently selected: {selected.name} ({selected.id})" if selected else "\nNo item selected"
    
    return "Pipeline items:\n" + "\n".join(result) + selected_info


@tool
@log_execution(start_msg="[Tool] Select Pipeline Item", end_msg="[Tool] Item Selected")
def select_pipeline_item(item_id: str) -> str:
    """Select an item in the pipeline. This makes it the active item for subsequent filter applications.
    
    Args:
        item_id: ID of the item to select
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    item = vm.items.get(item_id)
    if not item:
        return f"Error: Item {item_id} not found"
    
    vm.select_item(item_id)
    return f"Selected item: '{item.name}' (id: {item_id})"


@tool
@log_execution(start_msg="[Tool] Delete Item", end_msg="[Tool] Item Deleted")
def delete_item(item_id: str) -> str:
    """Delete an item from the pipeline. This will also delete all child items.
    
    Args:
        item_id: ID of the item to delete
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    item = vm.items.get(item_id)
    if not item:
        return f"Error: Item {item_id} not found"
    
    item_name = item.name
    vm.delete_item(item_id)
    return f"Deleted '{item_name}' and its children"
