from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QScrollArea, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Signal, Qt


class MessageBubble(QFrame):
    """Chat message bubble widget."""
    
    def __init__(self, sender: str, content: str, parent=None):
        super().__init__(parent)
        self._sender = sender
        self._setup_ui(sender, content)
    
    def _setup_ui(self, sender: str, content: str) -> None:
        is_user = sender == "User"
        is_system = sender == "System"
        
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        outer_layout = QHBoxLayout(self)
        outer_layout.setContentsMargins(8, 4, 8, 4)
        
        if is_user:
            outer_layout.addStretch()
        
        bubble = QFrame()
        bubble.setFrameShape(QFrame.Shape.StyledPanel)
        bubble.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        bubble.setMaximumWidth(400)
        
        if is_user:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #0084ff;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
        elif is_system:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #e0e0e0;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
        else:
            bubble.setStyleSheet("""
                QFrame {
                    background-color: #f0f0f0;
                    border-radius: 12px;
                    padding: 8px 12px;
                }
            """)
        
        bubble_layout = QVBoxLayout(bubble)
        bubble_layout.setContentsMargins(0, 0, 0, 0)
        bubble_layout.setSpacing(4)
        
        if not is_user:
            sender_label = QLabel(sender)
            sender_label.setStyleSheet("color: #666666; font-size: 11px; font-weight: bold;")
            bubble_layout.addWidget(sender_label)
        
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if is_user:
            content_label.setStyleSheet("color: #ffffff; font-size: 13px;")
        else:
            content_label.setStyleSheet("color: #000000; font-size: 13px;")
        
        bubble_layout.addWidget(content_label)
        
        outer_layout.addWidget(bubble)
        
        if not is_user:
            outer_layout.addStretch()


class ChatPanel(QWidget):
    """Panel for chat/agent interaction."""
    
    message_sent = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the chat panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setStyleSheet("QScrollArea { border: none; }")
        
        self._messages_container = QWidget()
        self._messages_layout = QVBoxLayout(self._messages_container)
        self._messages_layout.setContentsMargins(0, 8, 0, 8)
        self._messages_layout.setSpacing(2)
        self._messages_layout.addStretch()
        
        self._scroll_area.setWidget(self._messages_container)
        layout.addWidget(self._scroll_area)
        
        input_container = QWidget()
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(8, 8, 8, 8)
        input_layout.setSpacing(8)
        
        self._input = QLineEdit()
        self._input.setPlaceholderText("메시지를 입력하세요...")
        self._input.returnPressed.connect(self._on_send)
        input_layout.addWidget(self._input)
        
        self._send_btn = QPushButton("Send")
        self._send_btn.clicked.connect(self._on_send)
        input_layout.addWidget(self._send_btn)
        
        layout.addWidget(input_container)
    
    def _on_send(self) -> None:
        """Handle send button/enter key."""
        text = self._input.text().strip()
        if text:
            self._input.clear()
            self.message_sent.emit(text)
    
    def append_message(self, sender: str, content: str) -> None:
        """Append a message bubble to the display."""
        bubble = MessageBubble(sender, content)
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, bubble)
        
        self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        )
    
    def clear_display(self) -> None:
        """Clear the chat display."""
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
