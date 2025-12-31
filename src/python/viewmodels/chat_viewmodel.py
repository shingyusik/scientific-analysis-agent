import json
from PySide6.QtCore import QObject, Signal, QThread
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk, BaseMessage, ToolMessage

from config import Config
from agent import create_agent, set_pipeline_viewmodel, set_vtk_viewmodel
from langgraph.types import Command

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel
    from viewmodels.vtk_viewmodel import VTKViewModel


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
    input_requested = Signal(str, list)  # description, fields
    finished = Signal(dict) # state updates
    error = Signal(str)
    
    def __init__(self, agent, input_data: Any, config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self._agent = agent
        self._input_data = input_data
        self._config = config
        self._stop_requested = False
    
    def stop(self):
        self._stop_requested = True
    
    def run(self):
        try:
            # Check if input is a Command object (for resumption) or standard messages
            if isinstance(self._input_data, Command):
                input_payload = self._input_data
            else:
                input_payload = {
                    "messages": self._input_data, 
                    "pipeline_context": {}, 
                    "blocked": False,
                    "waiting_for_input": False,
                    "input_fields": []
                }
            
            # Initialize a default state to avoid reference errors
            state = {"waiting_for_input": False, "input_fields": []}
            interrupt_handled = False
            
            for mode, event in self._agent.stream(
                input_payload,
                config=self._config,
                stream_mode=["messages", "updates"]
            ):
                if self._stop_requested:
                    break
                if mode == "updates":
                    # Check for interruption
                    if event.get("__interrupt__"):
                        interrupt_obj = event.get("__interrupt__")[0]
                        
                        # In some versions/contexts, this might be an Interrupt object wrapper
                        if hasattr(interrupt_obj, "value"):
                            interrupt_value = interrupt_obj.value
                        else:
                            interrupt_value = interrupt_obj
                            
                        # Our tool returns {description, fields}
                        description = interrupt_value.get("description", "")
                        fields = interrupt_value.get("fields", [])
                        state["waiting_for_input"] = True
                        state["waiting_for_input"] = True
                        state["input_fields"] = fields
                        self.input_requested.emit(description, fields)
                        interrupt_handled = True
                    
                    # If it's a regular update, we might want to capture state changes
                    # But for now, we rely on the final snapshot or specific fields
                    if isinstance(event, dict):
                         state.update(event)
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
                    
            
            
            # Check final state for any remaining interruption needed via snapshot
            # This is a fallback in case the stream didn't yield the __interrupt__ event explicitly
            if not interrupt_handled:
                snapshot = self._agent.get_state(self._config)
                if snapshot.tasks:
                    for task in snapshot.tasks:
                        if task.interrupts:
                            interrupt_value = task.interrupts[0].value
                            # Handle wrapped Interrupt object if valid
                            if hasattr(interrupt_value, "value"):
                                interrupt_value = interrupt_value.value
                                
                            description = interrupt_value.get("description", "")
                            fields = interrupt_value.get("fields", [])
                            state["waiting_for_input"] = True
                            state["input_fields"] = fields
                            self.input_requested.emit(description, fields)
                            break
            
            self.finished.emit(state)
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
    input_requested = Signal(str, list)  # description, fields
    conversation_cleared = Signal()
    
    def __init__(self, pipeline_vm: Optional["PipelineViewModel"] = None, 
                 vtk_vm: Optional["VTKViewModel"] = None):
        super().__init__()
        self._messages: List[ChatMessage] = []
        self._agent = None
        self._pipeline_vm = pipeline_vm
        self._vtk_vm = vtk_vm
        self._worker: Optional[StreamingAgentWorker] = None
        self._current_response = ""
        self._waiting_for_input = False
        self._thread_config = {"configurable": {"thread_id": "1"}}
        
        self._initialize_agent()
    
    def _initialize_agent(self) -> None:
        if self._pipeline_vm:
            set_pipeline_viewmodel(self._pipeline_vm)
        if self._vtk_vm:
            set_vtk_viewmodel(self._vtk_vm)
        
        if Config.is_configured():
            self._agent = create_agent()
    
    def set_vtk_viewmodel(self, vm: "VTKViewModel") -> None:
        self._vtk_vm = vm
        set_vtk_viewmodel(vm)
    
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
        
        # If we are resuming from input, we don't need to pass all messages again if using memory,
        # but here we are stateless between runs unless we use the thread check.
        # However, for simplicity with 'waiting_for_input' logic:
        # If we are NOT waiting for input, we start fresh or append.
        # If we ARE waiting for input, we should separate that logic (see submit_user_input).
        
        # This starting method is for NEW user messages.
        self._waiting_for_input = False
        
        # This starting method is for NEW user messages.
        self._waiting_for_input = False
        
        self._worker = StreamingAgentWorker(self._agent, lc_messages, self._thread_config, parent=self)
        self._worker.token_received.connect(self._on_token_received)
        self._worker.tool_activity.connect(self._on_tool_activity)
        self._worker.input_requested.connect(self._on_input_requested)
        self._worker.finished.connect(self._on_streaming_finished)
        self._worker.error.connect(self._on_agent_error)
        self._worker.start()

    def submit_user_input(self, values: dict) -> None:
        """Submit user input as a tool result to resume the agent."""
        if not self._agent:
            return
            
        self.agent_thinking.emit()
        self._waiting_for_input = False
        self.streaming_started.emit()
        
        # Resume execution with the user's input
        # We pass Command(resume=values) which will be the return value of interrupt() in the tool.
        
        # Now run again to continue execution
        # We pass Command object as input to resume
        self._worker = StreamingAgentWorker(self._agent, Command(resume=values), self._thread_config, parent=self)
        self._worker.token_received.connect(self._on_token_received)
        self._worker.tool_activity.connect(self._on_tool_activity)
        self._worker.input_requested.connect(self._on_input_requested)
        self._worker.finished.connect(self._on_streaming_finished)
        self._worker.error.connect(self._on_agent_error)
        self._worker.start()
    
    def _on_input_requested(self, description: str, fields: list) -> None:
        self.input_requested.emit(description, fields)
    
    def _on_token_received(self, token: str) -> None:
        self._current_response += token
        self.streaming_token.emit(self._current_response)
    
    def _on_tool_activity(self, tool_name: str, result: str) -> None:
        self.tool_activity.emit(tool_name, result)
    
    def _on_streaming_finished(self, state: dict) -> None:
        is_blocked = state.get("blocked", False)
        if self._current_response:
            if is_blocked:
                if self._messages and self._messages[-1].sender == "User":
                    self._messages.pop()
            else:
                msg = ChatMessage("Agent", self._current_response)
                self._messages.append(msg)
            self.agent_response.emit(self._current_response)
        
        self._waiting_for_input = state.get("waiting_for_input", False)
        self._input_fields = state.get("input_fields", [])
        
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
    
    def stop_generation(self) -> None:
        """Stop the agent execution thread."""
        if self._worker and self._worker.isRunning():
            # Set stop flag to exit the worker loop gracefully
            self._worker.stop()
            
            # Capture worker to a local variable for safe cleanup
            worker = self._worker
            
            # Disconnect signals to avoid further updates to this viewmodel
            try:
                worker.token_received.disconnect(self._on_token_received)
                worker.tool_activity.disconnect(self._on_tool_activity)
                worker.input_requested.disconnect(self._on_input_requested)
                worker.finished.disconnect(self._on_streaming_finished)
                worker.error.disconnect(self._on_agent_error)
            except (RuntimeError, TypeError):
                # Signals might already be disconnected
                pass
            
            # Save the current response as a message before clearing
            if self._current_response:
                msg = ChatMessage("Agent", self._current_response)
                self._messages.append(msg)
                self.agent_response.emit(self._current_response)
                self._current_response = ""
            
            # Immediately notify UI that streaming has "finished"
            self.streaming_finished.emit()
            
            # Allow the worker to clean itself up when it finally terminates
            worker.finished.connect(worker.deleteLater)
            
            # We keep a reference in a dedicated list to prevent GC while the thread is running
            if not hasattr(self, '_stopping_workers'):
                self._stopping_workers = []
            self._stopping_workers.append(worker)
            
            # Helper to remove from list when officially done
            def finalize_cleanup(w=worker):
                if hasattr(self, '_stopping_workers') and w in self._stopping_workers:
                    self._stopping_workers.remove(w)
            
            worker.finished.connect(finalize_cleanup)
            
            # Clear main reference to allow a new message to be sent
            self._worker = None
    
    def initialize_with_engine_message(self, message: str) -> None:
        """Initialize with engine greeting message."""
        self.add_system_message(message)
    
    def clear_history(self) -> None:
        """Clear chat history."""
        self._messages.clear()
    
    def start_new_conversation(self) -> None:
        """Start a new conversation, clearing chat history only."""
        self.clear_history()
        self.conversation_cleared.emit()
