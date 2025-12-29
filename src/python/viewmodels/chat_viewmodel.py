from PySide6.QtCore import QObject, Signal, QThread
from typing import List, Optional, TYPE_CHECKING
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, BaseMessage, ToolMessage

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
    
    def to_langchain_message(self) -> Optional[BaseMessage]:
        """Convert to LangChain message format."""
        if self.sender == "User":
            return HumanMessage(content=self.content)
        elif self.sender == "Agent":
            return AIMessage(content=self.content)
        return None


class StreamingAgentWorker(QThread):
    """Worker thread for streaming agent execution."""
    
    token_received = Signal(str)
    tool_activity = Signal(str, str)  # tool_name, result
    finished = Signal(bool)
    error = Signal(str)
    
    def __init__(self, agent, messages: List[BaseMessage], parent=None):
        super().__init__(parent)
        self._agent = agent
        self._messages = messages
    
    def run(self):
        try:
            is_blocked = False
            for mode, event in self._agent.stream(
                {"messages": self._messages, "pipeline_context": {}, "blocked": False},
                stream_mode=["messages", "values"]
            ):
                if mode == "values":
                    is_blocked = event.get("blocked", False)
                    continue
                
                message, metadata = event
                node_name = metadata.get("langgraph_node", "")
                
                if isinstance(message, AIMessageChunk):
                    if node_name == "guardrail":
                        continue
                    if hasattr(message, 'tool_call_chunks') and message.tool_call_chunks:
                        for tc in message.tool_call_chunks:
                            if tc.get('name'):
                                self.tool_activity.emit(tc['name'], "호출 중...")
                    if message.content:
                        self.token_received.emit(message.content)
                elif isinstance(message, AIMessage):
                    if hasattr(message, 'tool_calls') and message.tool_calls:
                        for tc in message.tool_calls:
                            self.tool_activity.emit(tc['name'], "호출 중...")
                    if message.content:
                        self.token_received.emit(message.content)
                elif isinstance(message, ToolMessage):
                    result_preview = message.content[:100] if len(message.content) > 100 else message.content
                    self.tool_activity.emit(message.name, result_preview)
            
            self.finished.emit(is_blocked)
        except Exception as e:
            self.error.emit(str(e))


class ChatViewModel(QObject):
    """ViewModel for chat/agent interaction."""
    
    message_added = Signal(object)  # ChatMessage
    message_updated = Signal(str, str)  # message_id, new_content
    streaming_started = Signal()
    streaming_token = Signal(str)
    streaming_finished = Signal()
    agent_thinking = Signal()
    agent_response = Signal(str)
    render_requested = Signal()
    tool_activity = Signal(str, str)  # tool_name, result
    
    def __init__(self, pipeline_vm: Optional["PipelineViewModel"] = None):
        super().__init__()
        self._messages: List[ChatMessage] = []
        self._agent = None
        self._pipeline_vm = pipeline_vm
        self._worker: Optional[StreamingAgentWorker] = None
        self._current_response = ""
        
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
    
    def _get_langchain_messages(self) -> List[BaseMessage]:
        """Convert chat history to LangChain message format."""
        lc_messages = []
        for msg in self._messages:
            lc_msg = msg.to_langchain_message()
            if lc_msg:
                lc_messages.append(lc_msg)
        return lc_messages
    
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
        
        self._process_with_agent()
    
    def _process_with_agent(self) -> None:
        """Process message with LangGraph agent using streaming."""
        self.agent_thinking.emit()
        
        if not self._agent:
            response = "Agent not available. Please configure OPENAI_API_KEY."
            self._add_agent_response(response)
            return
        
        self._current_response = ""
        self.streaming_started.emit()
        
        lc_messages = self._get_langchain_messages()
        self._worker = StreamingAgentWorker(self._agent, lc_messages, self)
        self._worker.token_received.connect(self._on_token_received)
        self._worker.tool_activity.connect(self._on_tool_activity)
        self._worker.finished.connect(self._on_streaming_finished)
        self._worker.error.connect(self._on_agent_error)
        self._worker.start()
    
    def _on_token_received(self, token: str) -> None:
        self._current_response += token
        self.streaming_token.emit(self._current_response)
    
    def _on_tool_activity(self, tool_name: str, result: str) -> None:
        self.tool_activity.emit(tool_name, result)
    
    def _on_streaming_finished(self, is_blocked: bool) -> None:
        if self._current_response:
            if is_blocked:
                if self._messages and self._messages[-1].sender == "User":
                    self._messages.pop()
            else:
                msg = ChatMessage("Agent", self._current_response)
                self._messages.append(msg)
            self.agent_response.emit(self._current_response)
        
        self.streaming_finished.emit()
        self.render_requested.emit()
        self._cleanup_worker()
    
    def _on_agent_error(self, error: str) -> None:
        self._add_agent_response(f"Error: {error}")
        self.streaming_finished.emit()
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
