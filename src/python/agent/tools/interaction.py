from typing import List, Dict, Any
from langchain_core.tools import tool
from langgraph.types import interrupt
from agent.models import InputRequest
from utils.logger import get_logger, log_execution

logger = get_logger("AgentTools")

@tool(args_schema=InputRequest)
@log_execution(start_msg="[Tool] Request User Input", end_msg="[Tool] User Input Received")
def request_user_input(
    description: str,
    fields: List[Dict[str, Any]]
) -> str:
    """Request specific input or selection from the user when parameters are needed.
    This will show a structured form to the user.
    """
    # Ensure fields are serialized to dicts for the UI
    serialized_fields = [
        f.model_dump() if hasattr(f, "model_dump") else f 
        for f in fields
    ]
    
    user_input = interrupt({
        "description": description,
        "fields": serialized_fields
    })
    
    return f"User Input Received: {user_input}. Proceed with the requested action using these values."
