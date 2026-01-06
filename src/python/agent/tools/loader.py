from typing import List
from langchain_core.tools import BaseTool

from utils.app_context import get_pipeline_viewmodel, get_vtk_viewmodel, get_time_series_manager
from agent.tools.interaction import request_user_input
from utils.tool_registry import generate_tools
from utils.logger import get_logger
import filters

logger = get_logger("ToolLoader")

def get_all_tools() -> List[BaseTool]:
    """
    Gather all available tools from various sources:
    1. PipelineViewModel (Visualization tools)
    2. VTKViewModel (Camera tools)
    3. TimeSeriesManager (Animation tools)
    4. Filter Classes (Slice/Clip tools)
    5. Static tools (Interaction)
    """
    pipeline_vm = get_pipeline_viewmodel()
    vtk_vm = get_vtk_viewmodel()
    ts_manager = get_time_series_manager()
    
    # Static tools
    tools = [
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
    
    # Dynamic tools from TimeSeriesManager
    if ts_manager:
        ts_tools = generate_tools(ts_manager)
        logger.info(f"Generated {len(ts_tools)} tools from TimeSeriesManager")
        tools.extend(ts_tools)
    else:
        logger.warning("TimeSeriesManager not available, animation tools will be missing")
    
    # Dynamic tools from Filter Classes
    for filter_type in filters.get_all_filter_types():
        filter_cls = filters.get_filter(filter_type)
        if filter_cls:
            cls_tools = generate_tools(filter_cls, filter_type)
            if cls_tools:
                logger.info(f"Generated {len(cls_tools)} tools from filter class {filter_cls.__name__}")
                tools.extend(cls_tools)
        
    return tools
