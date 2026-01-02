from agent.tools.context import set_pipeline_viewmodel, get_pipeline_viewmodel, set_vtk_viewmodel, get_vtk_viewmodel
from agent.tools.filter import (
    apply_slice_filter,
    apply_clip_filter,
    get_filter_params,
    update_slice_filter_params,
    update_clip_filter_params,
)
from agent.tools.interaction import request_user_input
from utils.tool_registry import generate_tools
from utils.logger import get_logger

logger = get_logger("AgentTools")

def get_all_tools() -> list:
    pipeline_vm = get_pipeline_viewmodel()
    vtk_vm = get_vtk_viewmodel()
    
    # Static tools (remaining manual tools like filters and interaction)
    tools = [
        apply_slice_filter,
        apply_clip_filter,
        get_filter_params,
        update_slice_filter_params,
        update_clip_filter_params,
        request_user_input,
    ]
    
    # Dynamic tools from PipelineViewModel
    if pipeline_vm:
        vm_tools = generate_tools(pipeline_vm)
        logger.info(f"Generated {len(vm_tools)} tools from PipelineViewModel")
        tools.extend(vm_tools)
    else:
        logger.warning("PipelineViewModel not available, some tools will be missing")
        
    # Dynamic tools from VTKViewModel
    if vtk_vm:
        vtk_tools = generate_tools(vtk_vm)
        logger.info(f"Generated {len(vtk_tools)} tools from VTKViewModel")
        tools.extend(vtk_tools)
    else:
        logger.warning("VTKViewModel not available, camera tools will be missing")
        
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
    "request_user_input",
    "get_all_tools",
]
