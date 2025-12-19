from PySide6.QtCore import QObject, Signal
from typing import List


class ChatMessage:
    """Represents a single chat message."""
    
    def __init__(self, sender: str, content: str):
        self.sender = sender
        self.content = content
    
    def __str__(self) -> str:
        return f"{self.sender}: {self.content}"


class ChatViewModel(QObject):
    """ViewModel for chat/agent interaction."""
    
    message_added = Signal(object)  # ChatMessage
    agent_thinking = Signal()
    agent_response = Signal(str)
    
    def __init__(self):
        super().__init__()
        self._messages: List[ChatMessage] = []
        self._agent = None
    
    @property
    def messages(self) -> List[ChatMessage]:
        return self._messages.copy()
    
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
        
        response = "(Thinking...) [Agent logic to be implemented]"
        
        msg = ChatMessage("Agent", response)
        self._messages.append(msg)
        self.message_added.emit(msg)
        self.agent_response.emit(response)
    
    def initialize_with_engine_message(self, message: str) -> None:
        """Initialize with engine greeting message."""
        self.add_system_message(message)
    
    def clear_history(self) -> None:
        """Clear chat history."""
        self._messages.clear()

