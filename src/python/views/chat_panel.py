import markdown
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QScrollArea, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Signal, Qt, QTimer


class MessageBubble(QFrame):
    """Chat message bubble widget."""
    
    def __init__(self, sender: str, content: str = "", parent=None):
        super().__init__(parent)
        self._sender = sender
        self._content_label = None
        self._is_user = sender == "User"
        self._setup_ui(sender, content)
    
    def _setup_ui(self, sender: str, content: str) -> None:
        is_user = self._is_user
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
        
        self._content_label = QLabel()
        self._content_label.setWordWrap(True)
        self._content_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._content_label.setOpenExternalLinks(True)
        
        if is_user:
            self._content_label.setText(content)
            self._content_label.setStyleSheet("color: #ffffff; font-size: 13px;")
        else:
            self._content_label.setTextFormat(Qt.TextFormat.RichText)
            self._content_label.setStyleSheet("color: #000000; font-size: 13px;")
            if content:
                self._content_label.setText(self._render_markdown(content))
        
        bubble_layout.addWidget(self._content_label)
        
        outer_layout.addWidget(bubble)
        
        if not is_user:
            outer_layout.addStretch()
    
    def update_content(self, content: str) -> None:
        """Update the message content (for streaming)."""
        if self._content_label:
            if self._is_user:
                self._content_label.setText(content)
            else:
                self._content_label.setText(self._render_markdown(content))
    
    def _render_markdown(self, content: str) -> str:
        """Convert markdown to styled HTML."""
        html = markdown.markdown(
            content,
            extensions=['fenced_code', 'tables', 'nl2br']
        )
        
        styled_html = f"""
        <style>
            code {{
                background-color: #e8e8e8;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
            pre {{
                background-color: #e8e8e8;
                padding: 8px;
                border-radius: 6px;
                overflow-x: auto;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
            }}
            ul, ol {{
                margin: 4px 0;
                padding-left: 20px;
            }}
            p {{
                margin: 4px 0;
            }}
        </style>
        {html}
        """
        return styled_html


class ChatPanel(QWidget):
    """Panel for chat/agent interaction."""
    
    message_sent = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._streaming_bubble = None
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
        self._scroll_to_bottom()
    
    def start_streaming(self) -> None:
        """Start a streaming message bubble."""
        self._streaming_bubble = MessageBubble("Agent", "▌")
        self._messages_layout.insertWidget(self._messages_layout.count() - 1, self._streaming_bubble)
        self._scroll_to_bottom()
    
    def update_streaming(self, content: str) -> None:
        """Update the streaming message content."""
        if self._streaming_bubble:
            self._streaming_bubble.update_content(content + "▌")
            self._scroll_to_bottom()
    
    def finish_streaming(self) -> None:
        """Finish streaming and finalize the message."""
        if self._streaming_bubble:
            current_text = self._streaming_bubble._content_label.toPlainText() if self._streaming_bubble._content_label else ""
            if current_text.endswith("▌"):
                current_text = current_text[:-1]
            self._streaming_bubble.update_content(current_text)
        self._streaming_bubble = None
    
    def _scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the chat."""
        QTimer.singleShot(10, lambda: self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        ))
    
    def clear_display(self) -> None:
        """Clear the chat display."""
        self._streaming_bubble = None
        while self._messages_layout.count() > 1:
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
