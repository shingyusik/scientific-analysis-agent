
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent.graph import create_guardrail_node, route_after_guardrail, should_continue, GuardrailDecision
from agent.state import AgentState

@pytest.fixture
def mock_model():
    model = MagicMock()
    # Mocking with_structured_output for guardrail
    structured = MagicMock()
    model.with_structured_output.return_value = structured
    return model, structured

@pytest.fixture
def mock_tools():
    tool1 = MagicMock()
    tool1.name = "test_tool"
    tool1.description = "A test tool for testing"
    return [tool1]

def test_guardrail_node_blocked(mock_model, mock_tools):
    model, structured = mock_model
    
    # Setup mock decision
    decision = GuardrailDecision(decision="blocked", reason="Off topic")
    structured.invoke.return_value = decision
    
    node = create_guardrail_node(model, mock_tools)
    
    state = {"messages": [HumanMessage(content="Tell me a joke")]}
    result = node(state)
    
    assert result["blocked"] is True
    assert "messages" in result
    assert isinstance(result["messages"][0], AIMessage)
    assert "죄송합니다" in result["messages"][0].content

def test_guardrail_node_allowed(mock_model, mock_tools):
    model, structured = mock_model
    
    # Setup mock decision
    decision = GuardrailDecision(decision="allowed", reason="Valid request")
    structured.invoke.return_value = decision
    
    node = create_guardrail_node(model, mock_tools)
    
    state = {"messages": [HumanMessage(content="Load data")]}
    result = node(state)
    
    assert result["blocked"] is False
    assert "messages" not in result # No blocking message added

def test_route_after_guardrail():
    # Blocked case
    assert route_after_guardrail({"blocked": True}) == "end"
    # Allowed case
    assert route_after_guardrail({"blocked": False}) == "agent"
    # Default case
    assert route_after_guardrail({}) == "agent"

def test_should_continue():
    # Case with tool calls
    msg_with_tool = AIMessage(content="", tool_calls=[{"name": "tool", "args": {}, "id": "call_1"}])
    state_tools = {"messages": [msg_with_tool]}
    assert should_continue(state_tools) == "tools"
    
    # Case without tool calls
    msg_no_tool = AIMessage(content="Done")
    state_end = {"messages": [msg_no_tool]}
    assert should_continue(state_end) == "end"
