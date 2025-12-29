from typing import Optional, TYPE_CHECKING
from langchain_core.tools import tool

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel

_pipeline_vm: Optional["PipelineViewModel"] = None


def set_pipeline_viewmodel(vm: "PipelineViewModel") -> None:
    global _pipeline_vm
    _pipeline_vm = vm


def get_pipeline_viewmodel() -> Optional["PipelineViewModel"]:
    return _pipeline_vm


@tool
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
def apply_slice_filter(
    normal_x: float = 1.0,
    normal_y: float = 0.0,
    normal_z: float = 0.0,
    item_id: Optional[str] = None
) -> str:
    """Apply a slice filter to cut data along a plane.
    
    Args:
        normal_x: X component of the slice plane normal vector (default: 1.0 for YZ plane)
        normal_y: Y component of the slice plane normal vector (default: 0.0)
        normal_z: Z component of the slice plane normal vector (default: 0.0)
        item_id: ID of the item to apply filter to. If not provided, uses selected item.
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    target_id = item_id or (vm.selected_item.id if vm.selected_item else None)
    if not target_id:
        return "Error: No item selected. Please select an item first or provide item_id."
    
    target_item = vm.items.get(target_id)
    if not target_item:
        return f"Error: Item {target_id} not found"
    
    center = target_item.vtk_data.GetCenter() if target_item.vtk_data else (0, 0, 0)
    
    params = {
        "origin": list(center),
        "normal": [normal_x, normal_y, normal_z],
        "offsets": [0.0],
        "show_preview": False
    }
    
    result = vm.apply_filter("slice_filter", target_id, params)
    if result:
        vm.commit_filter(result.id)
        return f"Successfully applied slice filter to '{target_item.name}'. New item: '{result.name}' (id: {result.id})"
    return "Error: Failed to apply slice filter"


@tool
def apply_clip_filter(
    normal_x: float = 1.0,
    normal_y: float = 0.0,
    normal_z: float = 0.0,
    inside_out: bool = False,
    item_id: Optional[str] = None
) -> str:
    """Apply a clip filter to remove part of the data on one side of a plane.
    
    Args:
        normal_x: X component of the clip plane normal vector (default: 1.0)
        normal_y: Y component of the clip plane normal vector (default: 0.0)
        normal_z: Z component of the clip plane normal vector (default: 0.0)
        inside_out: If True, keeps the opposite side of the plane (default: False)
        item_id: ID of the item to apply filter to. If not provided, uses selected item.
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    target_id = item_id or (vm.selected_item.id if vm.selected_item else None)
    if not target_id:
        return "Error: No item selected. Please select an item first or provide item_id."
    
    target_item = vm.items.get(target_id)
    if not target_item:
        return f"Error: Item {target_id} not found"
    
    center = target_item.vtk_data.GetCenter() if target_item.vtk_data else (0, 0, 0)
    
    params = {
        "origin": list(center),
        "normal": [normal_x, normal_y, normal_z],
        "inside_out": inside_out
    }
    
    result = vm.apply_filter("clip_filter", target_id, params)
    if result:
        vm.commit_filter(result.id)
        return f"Successfully applied clip filter to '{target_item.name}'. New item: '{result.name}' (id: {result.id})"
    return "Error: Failed to apply clip filter"


@tool
def set_visibility(item_id: str, visible: bool) -> str:
    """Set the visibility of an item in the pipeline.
    
    Args:
        item_id: ID of the item to change visibility
        visible: True to show, False to hide
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    item = vm.items.get(item_id)
    if not item:
        return f"Error: Item {item_id} not found"
    
    vm.set_visibility(item_id, visible)
    status = "visible" if visible else "hidden"
    return f"Set '{item.name}' to {status}"


@tool
def set_color_by(
    array_name: str,
    item_id: Optional[str] = None,
    array_type: str = "POINT",
    component: str = ""
) -> str:
    """Set the color mapping of an item by a scalar array.
    
    Args:
        array_name: Name of the scalar array to color by. Use "__SolidColor__" for solid color.
        item_id: ID of the item. If not provided, uses selected item.
        array_type: Type of array - "POINT" or "CELL" (default: "POINT")
        component: For vector arrays, which component to use: "Magnitude", "X", "Y", or "Z" (default: "")
    """
    vm = get_pipeline_viewmodel()
    if not vm:
        return "Error: Pipeline not initialized"
    
    target_id = item_id or (vm.selected_item.id if vm.selected_item else None)
    if not target_id:
        return "Error: No item selected"
    
    item = vm.items.get(target_id)
    if not item:
        return f"Error: Item {target_id} not found"
    
    vm.set_color_by(target_id, array_name, array_type, component)
    return f"Set '{item.name}' color by '{array_name}'"


@tool
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


def get_all_tools() -> list:
    return [
        get_pipeline_info,
        apply_slice_filter,
        apply_clip_filter,
        set_visibility,
        set_color_by,
        delete_item,
    ]

