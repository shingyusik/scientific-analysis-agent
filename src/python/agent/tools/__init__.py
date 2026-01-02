from agent.tools.context import set_pipeline_viewmodel, get_pipeline_viewmodel, set_vtk_viewmodel, get_vtk_viewmodel
from agent.tools.filter import (
    apply_slice_filter,
    apply_clip_filter,
    get_filter_params,
    update_slice_filter_params,
    update_clip_filter_params,
)
from agent.tools.visualization import (
    set_color_by,
    set_representation,
    set_opacity,
    set_visual_property,
    auto_fit_scalar_range,
    set_scalar_range,
    set_camera_view,
    set_view_plane,
    reset_camera_view,
)
from agent.tools.interaction import request_user_input
from utils.tool_registry import generate_tools
from utils.logger import get_logger

logger = get_logger("AgentTools")

def get_all_tools() -> list:
    pipeline_vm = get_pipeline_viewmodel()
    
    # Static tools (wrapper functions or those not on VM)
    tools = [
        apply_slice_filter,
        apply_clip_filter,
        set_color_by,
        set_representation,
        set_opacity,
        set_visual_property,
        auto_fit_scalar_range,
        set_scalar_range,
        set_camera_view,
        set_view_plane,
        reset_camera_view,
        get_filter_params,
        update_slice_filter_params,
        update_clip_filter_params,
        request_user_input,
    ]
    
    # Dynamic tools from ViewModel
    if pipeline_vm:
        vm_tools = generate_tools(pipeline_vm)
        logger.info(f"Generated {len(vm_tools)} tools from PipelineViewModel")
        tools.extend(vm_tools)
    else:
        logger.warning("PipelineViewModel not available, some tools will be missing")
        
    return tools

__all__ = [
    "set_pipeline_viewmodel",
    "get_pipeline_viewmodel",
    "set_vtk_viewmodel",
    "get_vtk_viewmodel",
    "apply_slice_filter",
    "apply_clip_filter",
    "get_filter_params",
    "update_slice_filter_params",
    "update_clip_filter_params",
    "set_color_by",
    "set_representation",
    "set_opacity",
    "set_visual_property",
    "auto_fit_scalar_range",
    "set_scalar_range",
    "set_camera_view",
    "set_view_plane",
    "reset_camera_view",
    "request_user_input",
    "get_all_tools",
]
