import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Optional
from utils.tool_registry import expose_tool, expose_filter_tool, generate_tools

# Dummy Data Structure for Filter
@dataclass
class DummyParams:
    value: float
    origin: List[float]
    normal: List[float]

# Dummy Class with Tools
class DummyToolProvider:
    display_name = "Dummy Provider"
    
    @expose_tool("simple_tool", "A simple tool description")
    def simple_action(self, arg1: str):
        return f"Action: {arg1}"

    @expose_filter_tool("apply_dummy", "Apply dummy filter", DummyParams)
    def apply_dummy(self, params: DummyParams):
        pass

@pytest.fixture
def mock_pipeline_vm():
    vm = MagicMock()
    # Setup for dynamic tool execution
    vm.items = {}
    vm.apply_filter.return_value = MagicMock(id="new_id", name="new_item")
    return vm

def test_expose_tool_decorator():
    provider = DummyToolProvider()
    assert getattr(provider.simple_action, "_is_tool") is True
    assert getattr(provider.simple_action, "_tool_name") == "simple_tool"
    assert getattr(provider.simple_action, "_tool_description") == "A simple tool description"

def test_expose_filter_tool_decorator():
    provider = DummyToolProvider()
    assert getattr(provider.apply_dummy, "_is_filter_tool") is True
    assert getattr(provider.apply_dummy, "_tool_name") == "apply_dummy"
    assert getattr(provider.apply_dummy, "_params_model") == DummyParams

def test_generate_tools_count():
    provider = DummyToolProvider()
    tools = generate_tools(provider)
    # Expect 1 simple tool + 1 apply filter tool + 1 update filter tool = 3
    assert len(tools) == 3 

def test_generate_tools_names():
    provider = DummyToolProvider()
    tools = generate_tools(provider)
    tool_names = [t.name for t in tools]
    assert "simple_tool" in tool_names
    assert "apply_dummy" in tool_names
    assert "update_dummy_params" in tool_names

@patch("utils.tool_registry.get_logger")
def test_simple_tool_execution(mock_get_logger):
    # This test is a bit complex because StructuredTool wraps the function.
    # We want to verify generate_tools returns a usable tool.
    provider = DummyToolProvider()
    tools = generate_tools(provider)
    
    simple_tool = next(t for t in tools if t.name == "simple_tool")
    # structured tools need keyword arguments matching the function signature
    result = simple_tool.invoke({"arg1": "test"}) 
    assert result == "Action: test"

def test_filter_tool_pydantic_model():
    provider = DummyToolProvider()
    tools = generate_tools(provider)
    
    apply_tool = next(t for t in tools if t.name == "apply_dummy")
    schema = apply_tool.args_schema
    fields = schema.model_fields
    
    # check flattened fields
    assert "value" in fields
    assert "origin_x" in fields
    assert "origin_y" in fields
    assert "origin_z" in fields
    assert "normal_x" in fields
    
    # check default values logic
    # origin default is 0.0
    assert fields["origin_x"].default == 0.0
    # normal default is 1.0 (from heuristic in code)
    assert fields["normal_x"].default == 1.0 

@patch("utils.app_context.get_pipeline_viewmodel")
def test_dynamic_tool_execution(mock_get_vm, mock_pipeline_vm):
    mock_get_vm.return_value = mock_pipeline_vm
    
    # Setup selected item
    mock_pipeline_vm.selected_item = MagicMock(id="item1")
    mock_pipeline_vm.items = {"item1": MagicMock(id="item1", name="Item 1")}
    
    provider = DummyToolProvider()
    # Hack to inject filter_type for the test since we process DummyToolProvider instance
    provider.filter_type = "DummyFilter" 
    
    tools = generate_tools(provider)
    apply_tool = next(t for t in tools if t.name == "apply_dummy")
    
    # Mocking arguments passed to the tool
    args = {
        "value": 10.0,
        "origin_x": 1.0, "origin_y": 2.0, "origin_z": 3.0,
        "normal_x": 0.0, "normal_y": 1.0, "normal_z": 0.0
    }
    
    result = apply_tool.invoke(args)
    
    # Verify apply_filter was called on VM
    mock_pipeline_vm.apply_filter.assert_called_once()
    call_args = mock_pipeline_vm.apply_filter.call_args
    assert call_args[0][0] == "DummyFilter" # filter_type
    assert call_args[0][1] == "item1" # target_id
    
    params = call_args[0][2]
    assert params["value"] == 10.0
    assert params["origin"] == [1.0, 2.0, 3.0]
    assert params["normal"] == [0.0, 1.0, 0.0]
    
    assert "Applied" in result

@patch("utils.app_context.get_pipeline_viewmodel")
def test_dynamic_update_tool_execution(mock_get_vm, mock_pipeline_vm):
    mock_get_vm.return_value = mock_pipeline_vm
    
    # Setup item with existing params
    mock_item = MagicMock(id="item1", name="Item 1")
    mock_item.filter_params = {
        "value": 5.0,
        "origin": [0.0, 0.0, 0.0],
        "normal": [1.0, 0.0, 0.0]
    }
    mock_pipeline_vm.items = {"item1": mock_item}
    
    provider = DummyToolProvider()
    tools = generate_tools(provider)
    update_tool = next(t for t in tools if t.name == "update_dummy_params")
    
    # Update only one field
    args = {"item_id": "item1", "value": 20.0}
    result = update_tool.invoke(args)
    
    mock_pipeline_vm.update_filter_params.assert_called_once()
    params = mock_pipeline_vm.update_filter_params.call_args[0][1]
    assert params["value"] == 20.0
    assert params["origin"] == [0.0, 0.0, 0.0] # Unchanged
