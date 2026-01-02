from typing import Optional
from langchain_core.tools import tool
from agent.tools.context import get_pipeline_viewmodel
from utils.logger import get_logger, log_execution

logger = get_logger("AgentTools")

@tool
@log_execution(start_msg="[Tool] Apply Slice Filter", end_msg="[Tool] Slice Filter Applied")
def apply_slice_filter(
    normal_x: float = 1.0,
    normal_y: float = 0.0,
    normal_z: float = 0.0,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    offsets: str = "0.0",
    show_plane: bool = True,
    item_id: Optional[str] = None
) -> str:
    """Apply a slice filter to cut data along a plane.
    
    Args:
        normal_x: X component of the slice plane normal vector (default: 1.0 for YZ plane)
        normal_y: Y component of the slice plane normal vector (default: 0.0)
        normal_z: Z component of the slice plane normal vector (default: 0.0)
        origin_x: X coordinate of the slice plane origin (optional, defaults to data center)
        origin_y: Y coordinate of the slice plane origin (optional, defaults to data center)
        origin_z: Z coordinate of the slice plane origin (optional, defaults to data center)
        offsets: Comma-separated list of offset values for multiple slices (default: "0.0")
        show_plane: Whether to show the interactive slice plane widget (default: True)
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
    
    center = target_item.vtk_data.GetCenter() if target_item.vtk_data else (0.0, 0.0, 0.0)
    origin = [
        origin_x if origin_x is not None else center[0],
        origin_y if origin_y is not None else center[1],
        origin_z if origin_z is not None else center[2]
    ]
    
    try:
        offset_list = [float(x.strip()) for x in offsets.split(",")]
    except ValueError:
        return "Error: Invalid offsets format. Use comma-separated numbers (e.g., '0.0' or '-1.0,0.0,1.0')"
    
    params = {
        "origin": origin,
        "normal": [normal_x, normal_y, normal_z],
        "offsets": offset_list,
        "show_preview": show_plane
    }
    
    result = vm.apply_filter("slice_filter", target_id, params)
    if result:
        vm.commit_filter(result.id)
        return f"Successfully applied slice filter to '{target_item.name}'. New item: '{result.name}' (id: {result.id})"
    return "Error: Failed to apply slice filter"


@tool
@log_execution(start_msg="[Tool] Apply Clip Filter", end_msg="[Tool] Clip Filter Applied")
def apply_clip_filter(
    normal_x: float = 1.0,
    normal_y: float = 0.0,
    normal_z: float = 0.0,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    show_plane: bool = True,
    item_id: Optional[str] = None
) -> str:
    """Apply a clip filter to remove part of the data on one side of a plane.
    
    Args:
        normal_x: X component of the clip plane normal vector (default: 1.0)
        normal_y: Y component of the clip plane normal vector (default: 0.0)
        normal_z: Z component of the clip plane normal vector (default: 0.0)
        origin_x: X coordinate of the clip plane origin (optional, defaults to data center)
        origin_y: Y coordinate of the clip plane origin (optional, defaults to data center)
        origin_z: Z coordinate of the clip plane origin (optional, defaults to data center)
        show_plane: Whether to show the interactive clip plane widget (default: True)
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
    
    center = target_item.vtk_data.GetCenter() if target_item.vtk_data else (0.0, 0.0, 0.0)
    origin = [
        origin_x if origin_x is not None else center[0],
        origin_y if origin_y is not None else center[1],
        origin_z if origin_z is not None else center[2]
    ]
    
    params = {
        "origin": origin,
        "normal": [normal_x, normal_y, normal_z],
        "show_preview": show_plane
    }
    
    result = vm.apply_filter("clip_filter", target_id, params)
    if result:
        vm.commit_filter(result.id)
        return f"Successfully applied clip filter to '{target_item.name}'. New item: '{result.name}' (id: {result.id})"
    return "Error: Failed to apply clip filter"


@tool
@log_execution(start_msg="[Tool] Get Filter Params", end_msg="[Tool] Params Retrieved")
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
    
    filter_instance = vm.get_filter(item.item_type)
    if filter_instance:
        result.append(filter_instance.format_params(params))
    else:
        for key, value in params.items():
            result.append(f"  - {key}: {value}")
    
    return "\n".join(result)


@tool
@log_execution(start_msg="[Tool] Update Slice Params", end_msg="[Tool] Slice Params Updated")
def update_slice_filter_params(
    item_id: Optional[str] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    normal_x: Optional[float] = None,
    normal_y: Optional[float] = None,
    normal_z: Optional[float] = None,
    offsets: Optional[str] = None,
    show_plane: Optional[bool] = None,
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
        show_plane: Whether to show the interactive slice plane widget.
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
    
    if show_plane is not None:
        params["show_preview"] = show_plane
        updated.append(f"show_plane={show_plane}")
    
    if not updated:
        return "No parameters were changed. Specify at least one parameter to update."
    
    vm.update_filter_params(target_id, params)
    
    if apply:
        vm.commit_filter(target_id)
        return f"Updated and applied slice filter '{item.name}': {', '.join(updated)}"
    else:
        return f"Updated slice filter '{item.name}' (not applied yet): {', '.join(updated)}"


@tool
@log_execution(start_msg="[Tool] Update Clip Params", end_msg="[Tool] Clip Params Updated")
def update_clip_filter_params(
    item_id: Optional[str] = None,
    origin_x: Optional[float] = None,
    origin_y: Optional[float] = None,
    origin_z: Optional[float] = None,
    normal_x: Optional[float] = None,
    normal_y: Optional[float] = None,
    normal_z: Optional[float] = None,
    show_plane: Optional[bool] = None,
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
        show_plane: Whether to show the interactive clip plane widget.
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
    
    if show_plane is not None:
        params["show_preview"] = show_plane
        updated.append(f"show_plane={show_plane}")
    
    if not updated:
        return "No parameters were changed. Specify at least one parameter to update."
    
    vm.update_filter_params(target_id, params)
    
    if apply:
        vm.commit_filter(target_id)
        return f"Updated and applied clip filter '{item.name}': {', '.join(updated)}"
    else:
        return f"Updated clip filter '{item.name}' (not applied yet): {', '.join(updated)}"
