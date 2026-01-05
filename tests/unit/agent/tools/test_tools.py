
import pytest
from unittest.mock import MagicMock, patch
from agent.tools.interaction import request_user_input
from agent.tools.loader import get_all_tools

def test_request_user_input():
    # Calling this tool should trigger an interrupt (or we check its schema)
    # Since 'interrupt' raises GraphInterrupt exception in recent LangGraph versions or behaves specifically
    # We'll mock interrupt to verify it's called with correct data
    
    with patch("agent.tools.interaction.interrupt") as mock_interrupt:
        mock_interrupt.return_value = "Mock Input"
        
        fields = [{"name": "test", "label": "Test", "type": "text"}]
        result = request_user_input.invoke({
            "description": "Test input",
            "fields": fields
        })
        
        assert "Mock Input" in result
        mock_interrupt.assert_called_once()
        call_args = mock_interrupt.call_args[0][0]
        assert call_args["description"] == "Test input"
        assert len(call_args["fields"]) == 1

@patch("agent.tools.loader.get_pipeline_viewmodel")
@patch("agent.tools.loader.get_vtk_viewmodel")
@patch("filters.get_all_filter_types")
def test_get_all_tools(mock_get_filters, mock_get_vtk_vm, mock_get_pipeline_vm):
    # Setup Mocks
    mock_pipeline_vm = MagicMock()
    mock_get_pipeline_vm.return_value = mock_pipeline_vm
    
    mock_vtk_vm = MagicMock()
    mock_get_vtk_vm.return_value = mock_vtk_vm
    
    mock_get_filters.return_value = [] # No dynamic filters for simplicity
    
    # We need to mock generate_tools to return dummy tools
    with patch("agent.tools.loader.generate_tools") as mock_generate:
        mock_tool = MagicMock()
        mock_generate.return_value = [mock_tool]
        
        tools = get_all_tools()
        
        # Expect: 
        # 1 static tool (request_user_input)
        # + 1 from PipelineVM
        # + 1 from VTKVM
        # = 3 tools total
        
        # Note: generate_tools is called twice (once for pipeline, once for vtk)
        assert len(tools) == 3
        
        assert request_user_input in tools
        assert mock_tool in tools
