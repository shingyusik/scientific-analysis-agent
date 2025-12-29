from PySide6.QtCore import QObject, Signal, QThread
from typing import List, Optional, TYPE_CHECKING
from langchain_core.messages import HumanMessage, AIMessage

from config import Config
from agent import create_agent, set_pipeline_viewmodel

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel


class ChatMessage:
    """Represents a single chat message."""
    
    def __init__(self, sender: str, content: str):
        self.sender = sender
        self.content = content
    
    def __str__(self) -> str:
        return f"{self.sender}: {self.content}"


class AgentWorker(QThread):
    """Worker thread for agent execution."""
    
    finished = Signal(str)
    error = Signal(str)
    
    def __init__(self, agent, message: str, parent=None):
        super().__init__(parent)
        self._agent = agent
        self._message = message
    
    def run(self):
        try:
            result = self._agent.invoke({
                "messages": [HumanMessage(content=self._message)],
                "pipeline_context": {}
            })
            
            messages = result.get("messages", [])
            if messages:
                last_message = messages[-1]
                if isinstance(last_message, AIMessage):
                    self.finished.emit(last_message.content)
                else:
                    self.finished.emit(str(last_message))
            else:
                self.finished.emit("No response from agent")
        except Exception as e:
            self.error.emit(str(e))


class ChatViewModel(QObject):
    """ViewModel for chat/agent interaction."""
    
    message_added = Signal(object)  # ChatMessage
    agent_thinking = Signal()
    agent_response = Signal(str)
    render_requested = Signal()
    
    def __init__(self, pipeline_vm: Optional["PipelineViewModel"] = None):
        super().__init__()
        self._messages: List[ChatMessage] = []
        self._agent = None
        self._pipeline_vm = pipeline_vm
        self._worker: Optional[AgentWorker] = None
        
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        if self._pipeline_vm:
            set_pipeline_viewmodel(self._pipeline_vm)
        
        if Config.is_configured():
            self._agent = create_agent()
            if self._agent:
                self.add_system_message("Agent initialized. Ready to assist.")
        else:
            self.add_system_message(
                "OPENAI_API_KEY not configured. "
                "Please set it in .env file to enable AI features."
            )
    
    def set_pipeline_viewmodel(self, vm: "PipelineViewModel") -> None:
        self._pipeline_vm = vm
        set_pipeline_viewmodel(vm)
    
    @property
    def messages(self) -> List[ChatMessage]:
        return self._messages.copy()
    
    @property
    def is_agent_available(self) -> bool:
        return self._agent is not None
    
    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        msg = ChatMessage("System", content)
        self._messages.append(msg)
        self.message_added.emit(msg)
    
    def send_user_message(self, content: str) -> None:
        """Send a user message and trigger agent processing."""
        if not content.strip():
            return
        
        msg = ChatMessage("User", content)
        self._messages.append(msg)
        self.message_added.emit(msg)
        
        self._process_with_agent(content)
    
    def _process_with_agent(self, content: str) -> None:
        """Process message with LangGraph agent."""
        self.agent_thinking.emit()
        
        if not self._agent:
            response = "Agent not available. Please configure OPENAI_API_KEY."
            self._add_agent_response(response)
            return
        
        self._worker = AgentWorker(self._agent, content, self)
        self._worker.finished.connect(self._on_agent_finished)
        self._worker.error.connect(self._on_agent_error)
        self._worker.start()
    
    def _on_agent_finished(self, response: str) -> None:
        self._add_agent_response(response)
        self.render_requested.emit()
        self._cleanup_worker()
    
    def _on_agent_error(self, error: str) -> None:
        self._add_agent_response(f"Error: {error}")
        self._cleanup_worker()
    
    def _add_agent_response(self, response: str) -> None:
        msg = ChatMessage("Agent", response)
        self._messages.append(msg)
        self.message_added.emit(msg)
        self.agent_response.emit(response)
    
    def _cleanup_worker(self) -> None:
        if self._worker:
            self._worker.deleteLater()
            self._worker = None
    
    def initialize_with_engine_message(self, message: str) -> None:
        """Initialize with engine greeting message."""
        self.add_system_message(message)
    
    def clear_history(self) -> None:
        """Clear chat history."""
        self._messages.clear()
