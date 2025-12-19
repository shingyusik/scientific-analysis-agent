from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PySide6.QtCore import Signal


class ChatPanel(QWidget):
    """Panel for chat/agent interaction."""
    
    message_sent = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the chat panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        self._display = QTextEdit()
        self._display.setReadOnly(True)
        layout.addWidget(self._display)
        
        input_layout = QHBoxLayout()
        
        self._input = QLineEdit()
        self._input.returnPressed.connect(self._on_send)
        input_layout.addWidget(self._input)
        
        self._send_btn = QPushButton("Send")
        self._send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self._send_btn)
        
        layout.addLayout(input_layout)
    
    def _on_send(self) -> None:
        """Handle send button/enter key."""
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.message_sent.emit(text)
    
    def append_message(self, sender: str, content: str) -> None:
        """Append a message to the display."""
        self._display.append(f"{sender}: {content}")
    
    def clear_display(self) -> None:
        """Clear the chat display."""
        self._display.clear()

