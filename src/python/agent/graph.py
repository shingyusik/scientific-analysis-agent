import os
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from agent.state import AgentState
from agent.tools import get_all_tools
from config import Config

SYSTEM_PROMPT = """You are SA-Agent, a scientific analysis assistant for VTK visualization.

Your capabilities:
1. Query pipeline information (loaded data, filters, visibility)
2. Apply filters (slice, clip) to data
3. Control visibility and color mapping
4. Delete items from the pipeline

Guidelines:
- Always check the pipeline state first with get_pipeline_info if unsure
- When applying filters, use the selected item if no item_id is specified
- Provide clear, concise responses about what actions you took
- If an error occurs, explain it clearly and suggest alternatives

Respond in Korean when the user speaks Korean."""

GUARDRAIL_PROMPT = """You are a guardrail that classifies user requests.

This is a scientific visualization assistant. Only allow requests related to:
- VTK data visualization
- Pipeline operations (filters, visibility, color mapping)
- Data analysis and queries about loaded data
- General greetings and questions about the assistant's capabilities

Classify the following user message as:
- "allowed" - if it's a valid scientific visualization request or greeting
- "blocked" - if it's off-topic, harmful, or inappropriate

Respond with ONLY "allowed" or "blocked"."""


def create_guardrail_node(model):
    def guardrail_node(state: AgentState) -> dict:
        messages = state["messages"]
        if not messages:
            return {"blocked": False}
        
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {"blocked": False}
        
        response = model.invoke([
            SystemMessage(content=GUARDRAIL_PROMPT),
            HumanMessage(content=f"User message: {last_message.content}")
        ])
        
        if "blocked" in response.content.lower():
            block_response = AIMessage(
                content="죄송합니다. 이 요청은 과학 시각화 분석과 관련이 없어 처리할 수 없습니다. "
                        "VTK 데이터 시각화, 필터 적용, 파이프라인 조작 등에 관해 질문해 주세요."
            )
            return {"messages": [block_response], "blocked": True}
        
        return {"blocked": False}
    
    return guardrail_node


def route_after_guardrail(state: AgentState) -> Literal["agent", "end"]:
    if state.get("blocked", False):
        return "end"
    return "agent"


def should_continue(state: AgentState) -> Literal["tools", "end"]:
    messages = state["messages"]
    last_message = messages[-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return "end"


def create_agent_node(model, tools: list):
    model_with_tools = model.bind_tools(tools)
    
    def agent_node(state: AgentState) -> dict:
        messages = state["messages"]
        
        if not messages or messages[0].type != "system":
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)
        
        response = model_with_tools.invoke(messages)
        return {"messages": [response]}
    
    return agent_node


def create_agent():
    if not Config.is_configured():
        return None
    
    model = init_chat_model(
        os.getenv("MODEL_NAME", "gpt-4o-mini"),
        temperature=0
    )
    
    tools = get_all_tools()
    tool_node = ToolNode(tools)
    agent_node = create_agent_node(model, tools)
    guardrail_node = create_guardrail_node(model)
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("guardrail", guardrail_node)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("guardrail")
    
    workflow.add_conditional_edges(
        "guardrail",
        route_after_guardrail,
        {"agent": "agent", "end": END}
    )
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()
