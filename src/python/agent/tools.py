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


@tool
def get_filter_params(item_id: Optional[str] = None) -> str:
    """Get the current parameters of a filter item.
    
    Args:
        item_id: ID of the filter item. If not provided, uses selected item.
    
    Returns:
        Current filter parameters as a formatted string.
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
    
    if "filter" not in item.item_type:
        return f"Error: Item '{item.name}' is not a filter (type: {item.item_type})"
    
    params = item.filter_params
    if not params:
        return f"No parameters found for '{item.name}'"
    
    result = [f"Filter: {item.name} (id: {item.id}, type: {item.item_type})"]
    result.append("Parameters:")
    
    if item.item_type == "slice_filter":
        origin = params.get("origin", [0, 0, 0])
        normal = params.get("normal", [1, 0, 0])
        offsets = params.get("offsets", [0.0])
        result.append(f"  - origin: [{origin[0]:.4f}, {origin[1]:.4f}, {origin[2]:.4f}]")
        result.append(f"  - normal: [{normal[0]:.4f}, {normal[1]:.4f}, {normal[2]:.4f}]")
        result.append(f"  - offsets: {offsets}")
    elif item.item_type == "clip_filter":
        origin = params.get("origin", [0, 0, 0])
        normal = params.get("normal", [1, 0, 0])
        result.append(f"  - origin: [{origin[0]:.4f}, {origin[1]:.4f}, {origin[2]:.4f}]")
        result.append(f"  - normal: [{normal[0]:.4f}, {normal[1]:.4f}, {normal[2]:.4f}]")
    else:
        for key, value in params.items():
            result.append(f"  - {key}: {value}")
    
    return "\n".join(result)


@tool
def update_slice_filter_params(
    item_id: Optional[str] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    normal_x: Optional[float] = None,
    normal_y: Optional[float] = None,
    normal_z: Optional[float] = None,
    offsets: Optional[str] = None,
    apply: bool = True
) -> str:
    """Update parameters of an existing slice filter.
    
    Args:
        item_id: ID of the slice filter item. If not provided, uses selected item.
        origin_x: X coordinate of slice plane origin.
        origin_y: Y coordinate of slice plane origin.
        origin_z: Z coordinate of slice plane origin.
        normal_x: X component of slice plane normal vector.
        normal_y: Y component of slice plane normal vector.
        normal_z: Z component of slice plane normal vector.
        offsets: Comma-separated offset values (e.g., "0.0" or "-1.0,0.0,1.0" for multiple slices).
        apply: If True, immediately recalculate the filter with new parameters (default: True).
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
    
    if item.item_type != "slice_filter":
        return f"Error: Item '{item.name}' is not a slice filter (type: {item.item_type})"
    
    params = item.filter_params.copy()
    updated = []
    
    current_origin = params.get("origin", [0.0, 0.0, 0.0])
    if origin_x is not None:
        current_origin[0] = origin_x
        updated.append(f"origin_x={origin_x}")
    if origin_y is not None:
        current_origin[1] = origin_y
        updated.append(f"origin_y={origin_y}")
    if origin_z is not None:
        current_origin[2] = origin_z
        updated.append(f"origin_z={origin_z}")
    params["origin"] = current_origin
    
    current_normal = params.get("normal", [1.0, 0.0, 0.0])
    if normal_x is not None:
        current_normal[0] = normal_x
        updated.append(f"normal_x={normal_x}")
    if normal_y is not None:
        current_normal[1] = normal_y
        updated.append(f"normal_y={normal_y}")
    if normal_z is not None:
        current_normal[2] = normal_z
        updated.append(f"normal_z={normal_z}")
    params["normal"] = current_normal
    
    if offsets is not None:
        try:
            offset_list = [float(x.strip()) for x in offsets.split(",")]
            params["offsets"] = offset_list
            updated.append(f"offsets={offset_list}")
        except ValueError:
            return f"Error: Invalid offsets format. Use comma-separated numbers (e.g., '0.0' or '-1.0,0.0,1.0')"
    
    if not updated:
        return "No parameters were changed. Specify at least one parameter to update."
    
    vm.update_filter_params(target_id, params)
    
    if apply:
        vm.commit_filter(target_id)
        return f"Updated and applied slice filter '{item.name}': {', '.join(updated)}"
    else:
        return f"Updated slice filter '{item.name}' (not applied yet): {', '.join(updated)}"


@tool
def update_clip_filter_params(
    item_id: Optional[str] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    normal_x: Optional[float] = None,
    normal_y: Optional[float] = None,
    normal_z: Optional[float] = None,
    apply: bool = True
) -> str:
    """Update parameters of an existing clip filter.
    
    Args:
        item_id: ID of the clip filter item. If not provided, uses selected item.
        origin_x: X coordinate of clip plane origin.
        origin_y: Y coordinate of clip plane origin.
        origin_z: Z coordinate of clip plane origin.
        normal_x: X component of clip plane normal vector.
        normal_y: Y component of clip plane normal vector.
        normal_z: Z component of clip plane normal vector.
        apply: If True, immediately recalculate the filter with new parameters (default: True).
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
    
    if item.item_type != "clip_filter":
        return f"Error: Item '{item.name}' is not a clip filter (type: {item.item_type})"
    
    params = item.filter_params.copy()
    updated = []
    
    current_origin = params.get("origin", [0.0, 0.0, 0.0])
    if origin_x is not None:
        current_origin[0] = origin_x
        updated.append(f"origin_x={origin_x}")
    if origin_y is not None:
        current_origin[1] = origin_y
        updated.append(f"origin_y={origin_y}")
    if origin_z is not None:
        current_origin[2] = origin_z
        updated.append(f"origin_z={origin_z}")
    params["origin"] = current_origin
    
    current_normal = params.get("normal", [1.0, 0.0, 0.0])
    if normal_x is not None:
        current_normal[0] = normal_x
        updated.append(f"normal_x={normal_x}")
    if normal_y is not None:
        current_normal[1] = normal_y
        updated.append(f"normal_y={normal_y}")
    if normal_z is not None:
        current_normal[2] = normal_z
        updated.append(f"normal_z={normal_z}")
    params["normal"] = current_normal
    
    if not updated:
        return "No parameters were changed. Specify at least one parameter to update."
    
    vm.update_filter_params(target_id, params)
    
    if apply:
        vm.commit_filter(target_id)
        return f"Updated and applied clip filter '{item.name}': {', '.join(updated)}"
    else:
        return f"Updated clip filter '{item.name}' (not applied yet): {', '.join(updated)}"


def get_all_tools() -> list:
    return [
        get_pipeline_info,
        apply_slice_filter,
        apply_clip_filter,
        set_visibility,
        set_color_by,
        delete_item,
        get_filter_params,
        update_slice_filter_params,
        update_clip_filter_params,
    ]

