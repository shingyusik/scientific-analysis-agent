from typing import Callable, List, Any, Type, Optional, Dict
import inspect
from dataclasses import fields, is_dataclass
from pydantic import create_model, Field
from langchain_core.tools import StructuredTool
from utils.logger import get_logger

logger = get_logger("ToolRegistry")

def expose_tool(name: str, description: str):
    """Decorator to mark a method as an LLM tool."""
    def decorator(func: Callable):
        func._is_tool = True
        func._tool_name = name
        func._tool_description = description
        return func
    return decorator

def expose_filter_tool(name: str, description: str, params_model: Type, update_description: Optional[str] = None):
    """Decorator to expose a filter's apply_filter method as a tool.
    
    This will automatically generate a tool function that:
    1. Takes flattened arguments (e.g. normal_x, normal_y, normal_z)
    2. Converts them to the params_model structure
    3. Calls the filter's apply logic
    
    Args:
        name: Name of the apply tool
        description: Description of the apply tool
        params_model: The dataclass defining parameters
        update_description: Optional description for the update tool. If None, a generic one is generated.
    """
    def decorator(func: Callable):
        func._is_filter_tool = True
        func._tool_name = name
        func._tool_description = description
        func._update_tool_description = update_description
        func._params_model = params_model
        return func
    return decorator

def _create_pydantic_model_from_dataclass(dc_cls: Type, all_optional: bool = False) -> Type:
    """Create a Pydantic model for tool arguments from a dataclass.
    
    Special handling:
    - Lists of floats named 'origin', 'normal', 'direction' are flattened to _x, _y, _z.
    - If all_optional is True, all fields are Optional and default to None.
    """
    field_definitions = {}
    
    # item_id is always present, but in 'create' it's optional target, in 'update' it's required target
    if all_optional:
        field_definitions["item_id"] = (str, Field(..., description="ID of the item to update"))
    else:
        field_definitions["item_id"] = (Optional[str], Field(default=None, description="Target item ID (optional if selected)"))
    
    for f in fields(dc_cls):
        # Heuristic for 3D vectors
        if f.name in ["origin", "normal", "direction"] and "List[float]" in str(f.type):
            
            default_val = None if all_optional else (1.0 if f.name=="normal" else 0.0)
            target_type = Optional[float] if all_optional else float
            desc_prefix = f"{f.name}"
            
            field_definitions[f"{f.name}_x"] = (
                target_type, 
                Field(default=default_val, description=f"{desc_prefix} X component")
            )
            field_definitions[f"{f.name}_y"] = (
                target_type, 
                Field(default=default_val, description=f"{desc_prefix} Y component")
            )
            field_definitions[f"{f.name}_z"] = (
                target_type, 
                Field(default=default_val, description=f"{desc_prefix} Z component")
            )
        else:
            # Pass through other fields (like 'offsets', 'show_preview')
            pydantic_type = f.type
            default_val = f.default if f.default is not inspect._empty else None
            
            if f.name == "offsets": # Special case for Slice
                pydantic_type = str
                if all_optional:
                    default_val = None
                    field_definitions[f.name] = (Optional[str], Field(default=None, description="Comma separated offsets"))
                else:
                    field_definitions[f.name] = (str, Field(default="0.0", description="Comma separated offsets"))
            else:
                if all_optional:
                     # Make it optional
                    field_definitions[f.name] = (Optional[pydantic_type], Field(default=None, description=f.name))
                else:
                    field_definitions[f.name] = (pydantic_type, Field(default=default_val, description=f.name))
                
    model_name = f"{dc_cls.__name__}{'Update' if all_optional else ''}ToolSchema"
    return create_model(model_name, **field_definitions)

def _create_dynamic_tool_func(vm: Any, filter_instance: Any, tool_name: str, params_model: Type, filter_type: Optional[str] = None) -> Callable:
    """Create the actual function that will run when the tool is called."""
    
    def dynamic_tool_func(item_id: Optional[str] = None, **kwargs) -> str:
        # 1. Resolve Target
        pipeline_vm = vm # The passed instance is PipelineViewModel if we are generating from it? 
        # Actually filter tools are generated from Filter Classes, but they utilize PipelineViewModel to apply.
        # We need access to PipelineViewModel. 
        # Since we are inside 'generate_tools' called on a Filter Instance, 'vm' is the Filter Instance.
        # We need to get the PipelineViewModel global or passed in.
        
        # We will use the proper AppContext accessor inside the tool execution
        from utils.app_context import get_pipeline_viewmodel
        pipeline_vm = get_pipeline_viewmodel()
        if not pipeline_vm:
            return "Error: Pipeline not initialized"

        target_id = item_id or (pipeline_vm.selected_item.id if pipeline_vm.selected_item else None)
        if not target_id:
            return "Error: No item selected"
            
        target_item = pipeline_vm.items.get(target_id)
        if not target_item:
            return f"Error: Item {target_id} not found"

        # 2. Construct Params
        # We need to reconstruct the params dict from the flattened kwargs
        constructed_params = {}
        
        # Handle 3D vectors reconstruction
        vectors = ["origin", "normal", "direction"]
        for vec in vectors:
            if f"{vec}_x" in kwargs:
                # If the tool provided x, y, z
                try:
                    x = kwargs.get(f"{vec}_x", 0.0)
                    y = kwargs.get(f"{vec}_y", 0.0)
                    z = kwargs.get(f"{vec}_z", 0.0)
                    
                    # Special logic for Origin: if 0,0,0 (default) AND the user didn't explicitly specify "0", 
                    # arguably we might want to use the object center. 
                    # But implementing that 'was it default?' logic is hard here.
                    # The previous create_tool checked 'if origin_x is not None'.
                    # Here our pydantic model has defaults. 
                    
                    # To support "Auto Center", we might need to check if the user provided values.
                    # But Pydantic fills defaults. 
                    
                    # Let's rely on the user or default to (0,0,0). 
                    # Refinement: If we truly want "center by default", we should probably set the default logic *here*.
                    
                    # Allow override if not provided?
                    # Ideally, if the user didn't touch it, we use Center. 
                    # But we can't tell if they didn't touch it vs they wanted 0.
                    
                    # For now, let's just use the values.
                    constructed_params[vec] = [x, y, z]
                except:
                    pass

        # Handle other fields
        # This is generic mapping
        for field in fields(params_model):
            if field.name in kwargs:
                constructed_params[field.name] = kwargs[field.name]
            # Special case for Slice offsets string -> list
            if field.name == "offsets" and "offsets" in kwargs:
                val = kwargs["offsets"]
                if isinstance(val, str):
                    try:
                        constructed_params["offsets"] = [float(x.strip()) for x in val.split(",")]
                    except:
                        pass # Should handle error?
        
        # Apply Logic using VM
        # We use pipeline_vm.apply_filter which creates the NEW item
        # The FilterType string is needed.
        # We can get it from filter_instance.filter_type
        
        # The FilterType string is needed.
        # We prefer the explicit filter_type if provided (e.g. from class inspection)
        # otherwise try to get it from the instance
        
        target_filter_type = filter_type or getattr(filter_instance, "filter_type", None)
        
        if not target_filter_type:
            # Fallback: if it's a property object (class level access), we can't use it
            return "Error: Could not determine filter type for tool execution"
        
        # We also need to handle 'Origin is None' logic if we want auto-center
        # PipelineViewModel.apply_filter has:
        # if params is None: ... center ...
        # But we are passing params.
        # We should manually check origin here if we want Center.
        
        # Re-implement Center logic:
        if "origin" in constructed_params and target_item.vtk_data:
            # Check if origin is effectively [0,0,0] and was likely default?
            # It's safer to just let the user specify. 
            # If the user wants center, they usually rely on the default behavior of the TOOL which had 'None'.
            pass

        result_item = pipeline_vm.apply_filter(target_filter_type, target_id, constructed_params)
        
        if result_item:
            pipeline_vm.commit_filter(result_item.id)
            return f"Applied {filter_instance.display_name} to '{target_item.name}'. New item: '{result_item.name}' (id: {result_item.id})"
        return "Error: Failed to apply filter"

    return dynamic_tool_func

def _create_dynamic_update_tool_func(params_model: Type) -> Callable:
    """Create the function for UPDATE tool."""
    
    def dynamic_update_tool_func(item_id: str, **kwargs) -> str:
        from utils.app_context import get_pipeline_viewmodel
        pipeline_vm = get_pipeline_viewmodel()
        if not pipeline_vm:
            return "Error: Pipeline not initialized"
            
        if not item_id:
            return "Error: item_id is required for update"
            
        item = pipeline_vm.items.get(item_id)
        if not item:
            return f"Error: Item {item_id} not found"
            
        # Current params
        current_params = item.filter_params.copy()
        updated_keys = []
        
        # Handle 3D vectors reconstruction (partial updates)
        vectors = ["origin", "normal", "direction"]
        for vec in vectors:
            if f"{vec}_x" in kwargs or f"{vec}_y" in kwargs or f"{vec}_z" in kwargs:
                current_vec = current_params.get(vec, [0.0, 0.0, 0.0])
                new_vec = list(current_vec) # copy
                
                if f"{vec}_x" in kwargs and kwargs[f"{vec}_x"] is not None: new_vec[0] = kwargs[f"{vec}_x"]
                if f"{vec}_y" in kwargs and kwargs[f"{vec}_y"] is not None: new_vec[1] = kwargs[f"{vec}_y"]
                if f"{vec}_z" in kwargs and kwargs[f"{vec}_z"] is not None: new_vec[2] = kwargs[f"{vec}_z"]
                
                if new_vec != current_vec:
                    current_params[vec] = new_vec
                    updated_keys.append(vec)

        # Handle other fields
        for field in fields(params_model):
            # offsets special case
            if field.name == "offsets" and "offsets" in kwargs:
                val = kwargs["offsets"]
                if val is not None:
                    try:
                        current_params["offsets"] = [float(x.strip()) for x in val.split(",")]
                        updated_keys.append("offsets")
                    except:
                        pass
            elif field.name in kwargs and kwargs[field.name] is not None:
                current_params[field.name] = kwargs[field.name]
                updated_keys.append(field.name)
        
        if not updated_keys:
            return "No parameters changed."
            
        pipeline_vm.update_filter_params(item_id, current_params)
        pipeline_vm.commit_filter(item_id) # Re-apply
        
        return f"Updated parameters for {item.name}: {', '.join(updated_keys)}"

    return dynamic_update_tool_func

def generate_tools(instance: Any, filter_type_override: Optional[str] = None) -> List[StructuredTool]:
    """Generate LangChain tools from an instance."""
    tools = []
    
    # Inspect all members
    for name, member in inspect.getmembers(instance):
        func = member
        
        # Handle bound methods vs un-bound (if passing class)
        # But usually we pass instance.
        if inspect.ismethod(member):
            func = member.__func__
            
        # Standard Tools
        if getattr(func, "_is_tool", False):
            tool_name = getattr(func, "_tool_name")
            tool_description = getattr(func, "_tool_description")
            
            logger.debug(f"Generating tool '{tool_name}' from {instance.__class__.__name__}.{name}")
            
            tool = StructuredTool.from_function(
                func=member,
                name=tool_name,
                description=tool_description
            )
            tools.append(tool)
            
        # Filter Tools (Dynamic)
        if getattr(func, "_is_filter_tool", False):
            tool_name = getattr(func, "_tool_name")
            tool_description = getattr(func, "_tool_description")
            params_model = getattr(func, "_params_model")
            
            logger.debug(f"Generating dynamic filter tool '{tool_name}' from {instance.__class__.__name__}.{name}")
            
            # 1. Create APPLY Tool
            args_schema = _create_pydantic_model_from_dataclass(params_model, all_optional=False)
            wrapper_func = _create_dynamic_tool_func(instance, instance, tool_name, params_model, filter_type_override)
            
            tool = StructuredTool.from_function(
                func=wrapper_func,
                name=tool_name,
                description=tool_description,
                args_schema=args_schema
            )
            tools.append(tool)
            
            # 2. Create UPDATE Tool
            # We derive the name, e.g. apply_slice_filter -> update_slice_filter_params
            update_tool_name = tool_name.replace("apply_", "update_") + "_params"
            if not update_tool_name.startswith("update_"):
                update_tool_name = "update_" + tool_name + "_params"
                
            custom_update_desc = getattr(func, "_update_tool_description", None)
            update_desc = custom_update_desc or f"Update parameters for an existing {tool_name.replace('apply_', '').replace('_', ' ')} item."
            
            update_schema = _create_pydantic_model_from_dataclass(params_model, all_optional=True)
            update_func = _create_dynamic_update_tool_func(params_model)
            
            update_tool = StructuredTool.from_function(
                func=update_func,
                name=update_tool_name,
                description=update_desc,
                args_schema=update_schema
            )
            tools.append(update_tool)
            
    return tools
