import os
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage

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
    
    workflow = StateGraph(AgentState)
    
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tool_node)
    
    workflow.set_entry_point("agent")
    
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
