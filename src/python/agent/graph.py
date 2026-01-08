import os
from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langchain.chat_models import init_chat_model
from langchain_core.messages import SystemMessage, AIMessage, HumanMessage

from agent.state import AgentState
from agent.tools import get_all_tools
from agent.models import GuardrailDecision
from config import Config
from utils.logger import get_logger, log_execution

logger = get_logger("AgentGraph")

SYSTEM_PROMPT = """You are SA-Agent, a scientific analysis assistant for VTK visualization.

Your capabilities:
1. Query pipeline information (loaded data, filters, visibility)
2. Apply filters (slice, clip) to data
3. Control visibility and color mapping
4. Delete items from the pipeline
5. Manage Tabs (Create, Close, List) - You can create multiple views (Table, Graph, Render)
6. Request specific input or selection from the user when parameters are needed


Guidelines:
- Always check the pipeline state first with get_pipeline_info if unsure
- When applying filters, use the selected item if no item_id is specified
- Provide clear, concise responses about what actions you took
- If an error occurs, explain it clearly and suggest alternatives

CRITICAL RULE FOR DELETING/CLOSING:
- "Close Tab", "Remove View", "Delete View", "Close Graph", "Remove Table" -> Use `close_tab` tool.
- "Delete Data", "Remove Source", "Delete Object", "Remove Filter" -> Use `delete_item` tool.
- If the user asks to "delete graph" or "remove table", FIRST call `list_tabs` to see if there is a tab with that name.
- If a tab exists, close the tab. Do NOT delete the pipeline item unless the user explicitly says "delete data".
- NEVER guess. If unsure whether to close a tab or delete data, ASK the user.

Handling Missing Parameters (CRITICAL):
- If the user requests an action but does not provide ALL necessary parameters, YOU MUST NOT GUESS OR ASSUME.
- YOU MUST NOT list options or ask for values in a plain text chat response.
- YOU MUST use the `request_user_input` tool to create a structured form for the user.
- This applies to ALL missing parameters, including:
  * Complex parameters (e.g., Normal vector, Origin point for filters)
  * Simple selection parameters (e.g., background color preset, representation style)
  * Any required parameter that the user did not explicitly provide
- The ONLY way to get missing parameters is via the `request_user_input` tool.
- When `request_user_input` returns the values, IMMEDIATELY execute the requested action using those values. Do not ask for confirmation.

Example 1: If user asks "Apply slice filter":
Call `request_user_input` with:
- description: "To apply the slice filter, I need to know the slice plane orientation."
- fields: [
    {"name": "normal_x", "label": "Normal X", "type": "number", "default": 1.0},
    {"name": "normal_y", "label": "Normal Y", "type": "number", "default": 0.0},
    ...
  ]

Example 2: If user asks "Change background color":
Call `request_user_input` with:
- description: "Please select a background preset."
- fields: [
    {"name": "preset_name", "label": "Background Preset", "type": "select", 
     "options": ["Warm Gray (Default)", "Blue Gray", "Dark Gray", "Neutral Gray", "Light Gray", "White", "Black", "Gradient Background"]}
  ]

Respond in Korean when the user speaks Korean."""

GUARDRAIL_PROMPT = """You are a SECURITY & RELEVANCE FILTER. 

SCOPE:
This is a scientific visualization agent. Use the provided "AVAILABLE TOOLS" list to understand the *domain*, but DO NOT enforce usage or parameters.

CRITICAL INSTRUCTION - STATE BLINDNESS:
1. You are BLIND to the current application state (open tabs, loaded data, etc.).
2. **NEVER** BLOCK a request because "item not found", "tab not open", "parameter missing", or "feature not supported".
3. **NEVER** guess the state. If the user says "Unpin 3D view", ASSUME "3D view" exists.
4. VALIDATION IS THE AGENT'S JOB. Your job is ONLY to filter SPAM or SECURITY threats.
5. If the request contains keywords related to visualization, data, UI, or general conversation -> **ALLOW**.

DECISION LOGIC:
- Is it SPAM/Junk? (e.g. "dhfuqhw", "buy crypto") -> BLOCK.
- Is it HARMFUL/Illegal? -> BLOCK.
- Is it unrelated to the software? (e.g. "Who is the president?", "Write a poem") -> BLOCK.
- Is it a Visualization request? (e.g. "delete view", "make it red", "pin tab") -> ALLOW (even if impossible).

EXAMPLES:

User: "3D view의 핀고정을 해제해줘" (Unpin 3D view)
Decision: allowed
Reason: Visualization intent (Tab management).

User: "Delete the graph that doesn't exist"
Decision: allowed
Reason: Visualization intent (Agent handles the error).

User: "sdfjskldf"
Decision: blocked
Reason: Gibberish/Spam.

User: "Hack the server"
Decision: blocked
Reason: Security threat.

User: "Close all tabs"
Decision: allowed
Reason: UI intent.

User: "Show me the weather"
Decision: blocked
Reason: Irrelevant topic.

Respond with the structured output.
"""


def create_guardrail_node(model, tools: list):
    # Bind the model with structured output
    structured_model = model.with_structured_output(GuardrailDecision)
    
    # Create tool context string
    tool_descriptions = []
    for t in tools:
        # Use first line of description for brevity
        short_desc = t.description.split('\n')[0]
        tool_descriptions.append(f"- {t.name}: {short_desc}")
    tool_context = "\n".join(tool_descriptions)
    
    def guardrail_node(state: AgentState) -> dict:
        messages = state["messages"]
        if not messages:
            return {"blocked": False}
        
        last_message = messages[-1]
        if not isinstance(last_message, HumanMessage):
            return {"blocked": False}
            
        # Dynamic System Message with Tool Context
        dynamic_system_prompt = f"""{GUARDRAIL_PROMPT}

AVAILABLE TOOLS IN SYSTEM (Use these to judge relevance):
{tool_context}

If the user request maps to ANY of these tools, it is ALLOWED.
"""
        
        # Pass all messages for full context
        guardrail_messages = [SystemMessage(content=dynamic_system_prompt)] + list(messages)
        
        # Invoke the structured model with full context
        decision: GuardrailDecision = structured_model.invoke(guardrail_messages)
        
        logger.debug(f"Guardrail decision: {decision.decision} (Reason: {decision.reason})")
        
        if decision.decision == "blocked":
            logger.info(f"Guardrail Blocked: {decision.reason}")
            response_content = (
                "죄송합니다. 이 요청은 과학 시각화 분석과 관련이 없어 처리할 수 없습니다. "
                "VTK 데이터 시각화, 필터 적용, 파이프라인 조작 등에 관해 질문해 주세요.\n\n"
                f"(Reason: {decision.reason})"
            )
            block_response = AIMessage(content=response_content)
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
        
        logger.info("Agent Invocation Start")
        response = model_with_tools.invoke(messages)
        logger.info(f"Agent Invocation End (Response type: {type(response).__name__})")
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
    logger.info(f"Initialized tool node with {len(tools)} tools")
    agent_node = create_agent_node(model, tools)
    guardrail_node = create_guardrail_node(model, tools)
    
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
    
    
    checkpointer = MemorySaver()
    logger.info("Agent Workflow Compiled")
    return workflow.compile(checkpointer=checkpointer)
