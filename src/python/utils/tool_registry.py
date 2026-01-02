from typing import Callable, List, Any
import inspect
from langchain_core.tools import StructuredTool
from utils.logger import get_logger

logger = get_logger("ToolRegistry")

def expose_tool(name: str, description: str):
    """Decorator to mark a method as an LLM tool.
    
    Args:
        name: The name of the tool (e.g., 'select_pipeline_item')
        description: The description of what the tool does
    """
    def decorator(func: Callable):
        func._is_tool = True
        func._tool_name = name
        func._tool_description = description
        return func
    return decorator

def generate_tools(vm_instance: Any) -> List[StructuredTool]:
    """Generate LangChain tools from a ViewModel instance.
    
    Scans the instance for methods decorated with @expose_tool and converts
    them into StructuredTool objects.
    """
    tools = []
    
    # Inspect all members of the instance
    # We inspect the class to find the underlying functions with attributes,
    # then bind them to the instance.
    for name, member in inspect.getmembers(vm_instance):
        if not inspect.ismethod(member):
            continue
            
        # The attribute is stored on the function object, not the bound method
        func = member.__func__
        
        if getattr(func, "_is_tool", False):
            tool_name = getattr(func, "_tool_name")
            tool_description = getattr(func, "_tool_description")
            
            logger.debug(f"Generating tool '{tool_name}' from {vm_instance.__class__.__name__}.{name}")
            
            # Create the tool using from_function to automatically handle arguments and types
            tool = StructuredTool.from_function(
                func=member,
                name=tool_name,
                description=tool_description
            )
            tools.append(tool)
            
    return tools
