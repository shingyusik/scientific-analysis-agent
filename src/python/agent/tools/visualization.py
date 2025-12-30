from typing import Optional
from langchain_core.tools import tool
from agent.tools.context import get_pipeline_viewmodel

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
def set_representation(style: str, item_id: Optional[str] = None) -> str:
    """Set the representation style of an item (e.g., Surface, Wireframe, Points).
    
    Args:
        style: Representation style. One of: "Surface", "Surface With Edges", "Wireframe", "Points", "Point Gaussian".
        item_id: ID of the item. If not provided, uses selected item.
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
    
    vm.set_representation(target_id, style)
    return f"Set '{item.name}' representation to '{style}'"


@tool
def set_opacity(opacity: float, item_id: Optional[str] = None) -> str:
    """Set the opacity of an item.
    
    Args:
        opacity: Opacity value between 0.0 (transparent) and 1.0 (opaque).
        item_id: ID of the item. If not provided, uses selected item.
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
    
    vm.set_opacity(target_id, opacity)
    return f"Set '{item.name}' opacity to {opacity}"


@tool
def set_visual_property(
    point_size: Optional[float] = None,
    line_width: Optional[float] = None,
    gaussian_scale: Optional[float] = None,
    item_id: Optional[str] = None
) -> str:
    """Set visual properties like point size, line width, or gaussian scale.
    
    Args:
        point_size: Size of points (when representation is "Points").
        line_width: Width of lines (when representation is "Wireframe" or "Surface With Edges").
        gaussian_scale: Scale factor (when representation is "Point Gaussian").
        item_id: ID of the item. If not provided, uses selected item.
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
    
    updates = []
    if point_size is not None:
        vm.set_point_size(target_id, point_size)
        updates.append(f"point_size={point_size}")
    if line_width is not None:
        vm.set_line_width(target_id, line_width)
        updates.append(f"line_width={line_width}")
    if gaussian_scale is not None:
        vm.set_gaussian_scale(target_id, gaussian_scale)
        updates.append(f"gaussian_scale={gaussian_scale}")
    
    if not updates:
        return "No properties specified to update."
    
    return f"Updated visual properties for '{item.name}': {', '.join(updates)}"


@tool
def auto_fit_scalar_range(item_id: Optional[str] = None) -> str:
    """Automatically fit the scalar coloring range of an item to its data min/max values.
    
    Args:
        item_id: ID of the item. If not provided, uses selected item.
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
    
    success = vm.render_service.fit_scalar_range(item.actor)
    if success:
        vm.item_updated.emit(item)
        return f"Rescaled '{item.name}' scalar range to match data bounds."
    return f"Error: Failed to auto-fit range for '{item.name}' (maybe not colored by array?)"


@tool
def set_scalar_range(
    min_val: float,
    max_val: float,
    item_id: Optional[str] = None
) -> str:
    """Set a custom scalar coloring range for an item.
    
    Args:
        min_val: Minimum value for the scalar range.
        max_val: Maximum value for the scalar range.
        item_id: ID of the item. If not provided, uses selected item.
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
    
    success = vm.render_service.set_custom_scalar_range(item.actor, min_val, max_val)
    if success:
        vm.item_updated.emit(item)
        return f"Set '{item.name}' scalar range to [{min_val}, {max_val}]."
    return f"Error: Failed to set custom range for '{item.name}'"
