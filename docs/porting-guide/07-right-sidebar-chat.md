# 7. 우측 채팅 패널 상세

## 7.1 ChatPanel 개요

### 7.1.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `ChatPanel` (QWidget 확장) |
| 스크롤 | QScrollArea |
| 입력 | QLineEdit |

### 7.1.2 레이아웃 구조

```
┌──────────────────────────────────────────┐
│              Chat Panel                   │
├──────────────────────────────────────────┤
│  ┌────────────────────────────────────┐  │
│  │                                    │  │
│  │        Message Scroll Area         │  │
│  │                                    │  │
│  │  ┌────────────────────────────┐    │  │
│  │  │  User Message Bubble       │    │  │
│  │  └────────────────────────────┘    │  │
│  │                                    │  │
│  │  ┌────────────────────────────┐    │  │
│  │  │ ▼ Tool Activities (접기)  │    │  │
│  │  │   - load_file: 성공       │    │  │
│  │  │   - apply_filter: 성공    │    │  │
│  │  └────────────────────────────┘    │  │
│  │                                    │  │
│  │  ┌────────────────────────────┐    │  │
│  │  │  AI Message Bubble         │    │  │
│  │  │  (Markdown 렌더링)         │    │  │
│  │  └────────────────────────────┘    │  │
│  │                                    │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  [New] [입력창________________] [Send]   │
│  or                                      │
│  [New] [입력창________________] [Cancel] │  ← AI 처리 중
└──────────────────────────────────────────┘
```

## 7.2 메시지 버블 (MessageBubble)

### 7.2.1 기본 정보

```python
CHAT_BUBBLE_MAX_WIDTH = 400  # 최대 너비 (픽셀)
```

### 7.2.2 스타일 구분

| 발신자 | 정렬 | 배경색 | 텍스트 정렬 |
|--------|------|--------|-------------|
| 사용자 (user) | 우측 | #DCF8C6 (연녹색) | 좌측 |
| AI (assistant) | 좌측 | #E8E8E8 (회색) | 좌측 |
| 시스템 (system) | 좌측 | #FFE4B5 (연주황) | 좌측 |

### 7.2.3 Markdown 렌더링

```python
def _render_markdown(self, content: str) -> str:
    """
    Markdown을 HTML로 변환
    
    지원 기능:
    - 헤더 (# ## ###)
    - 굵은체 (**text**)
    - 기울임체 (*text*)
    - 코드 블록 (```code```)
    - 인라인 코드 (`code`)
    - 리스트 (- item)
    - 링크 ([text](url))
    """
    html = markdown.markdown(content, extensions=['fenced_code'])
    
    # 스타일 적용
    styled_html = f"""
    <style>
        pre {{ background-color: #2d2d2d; color: #f8f8f2; 
              padding: 10px; border-radius: 5px; }}
        code {{ font-family: 'Consolas', monospace; }}
    </style>
    {html}
    """
    return styled_html
```

### 7.2.4 버블 레이아웃

```
┌───────────────────────────────────────┐
│  [발신자 라벨]                        │  ← "You" 또는 "AI"
├───────────────────────────────────────┤
│                                       │
│  메시지 내용                          │
│  (HTML 렌더링)                        │
│                                       │
└───────────────────────────────────────┘
```

## 7.3 도구 활동 섹션 (CollapsibleToolSection)

### 7.3.1 접힘 상태 (기본)

```
┌────────────────────────────────────────┐
│ ▶ 3 activities performed               │
└────────────────────────────────────────┘
```

### 7.3.2 펼침 상태

```
┌────────────────────────────────────────┐
│ ▼ 3 activities performed               │
├────────────────────────────────────────┤
│  ✓ load_file: 파일 로드 성공           │
│  ✓ apply_filter: 필터 적용 성공        │
│  ✓ set_camera: 카메라 설정 완료        │
└────────────────────────────────────────┘
```

### 7.3.3 스타일링

```python
# 헤더 스타일
header_style = """
    font-weight: bold;
    color: #666;
    padding: 5px;
    background: #f5f5f5;
    border-radius: 3px;
"""

# 활동 항목 스타일
activity_style = """
    padding-left: 15px;
    color: #333;
    font-family: monospace;
    font-size: 11px;
"""
```

### 7.3.4 결과 미리보기

```python
CHAT_TOOL_PREVIEW_LENGTH = 80  # 최대 80자

def add_activity(self, tool_name: str, result: str):
    # 결과 문자열 축약
    preview = result[:CHAT_TOOL_PREVIEW_LENGTH]
    if len(result) > CHAT_TOOL_PREVIEW_LENGTH:
        preview += "..."
    
    self._activities.append((tool_name, preview))
```

## 7.4 입력 폼 버블 (InputFormBubble)

### 7.4.1 용도

AI가 사용자 입력을 요청할 때 표시되는 동적 폼

### 7.4.2 레이아웃

```
┌────────────────────────────────────────┐
│  [폼 설명 텍스트]                      │
├────────────────────────────────────────┤
│                                        │
│  필드1: [________________]             │
│  필드2: [________________]             │
│  필드3: [▼ 드롭다운 선택 ▼]            │
│  필드4: [✓] 체크박스                   │
│                                        │
├────────────────────────────────────────┤
│              [Submit]                   │
└────────────────────────────────────────┘
```

### 7.4.3 지원 필드 타입

```python
FIELD_TYPES = {
    "text": QLineEdit,           # 텍스트 입력
    "number": QDoubleSpinBox,    # 숫자 입력
    "select": QComboBox,         # 드롭다운 선택
    "checkbox": QCheckBox,       # 체크박스
}
```

### 7.4.4 필드 정의 구조

```python
field = {
    "name": str,         # 필드 이름
    "type": str,         # "text", "number", "select", "checkbox"
    "label": str,        # 표시 라벨
    "default": Any,      # 기본값
    "options": List[str], # select 타입일 때 옵션 목록
    "min": float,        # number 타입 최소값
    "max": float,        # number 타입 최대값
}
```

### 7.4.5 Submit 시그널

```python
class InputFormBubble(QFrame):
    submitted = Signal(dict)  # {field_name: value, ...}
```

## 7.5 입력 영역

### 7.5.1 레이아웃

```
┌────────────────────────────────────────────────────────────┐
│ [New] [입력창__________________________] [Send/Cancel]     │
└────────────────────────────────────────────────────────────┘
```

### 7.5.2 버튼 상태

| 상태 | New 버튼 | 입력창 | 우측 버튼 |
|------|----------|--------|-----------|
| 대기 중 | 활성화 | 활성화 | "Send" |
| AI 처리 중 | 비활성화 | 비활성화 | "Cancel" |

### 7.5.3 입력창 동작

```python
# Enter 키로 전송
self._input_field.returnPressed.connect(self._on_send)

# 전송 처리
def _on_send(self):
    text = self._input_field.text().strip()
    if text:
        self._input_field.clear()
        self.message_sent.emit(text)
```

### 7.5.4 Cancel 버튼 동작

```python
def _on_cancel_clicked(self):
    """
    AI 처리 중단
    - 스트리밍 중지
    - 작업 스레드 종료
    - UI 재활성화
    """
    self.cancel_requested.emit()
```

## 7.6 스트리밍 응답 처리

### 7.6.1 스트리밍 시작

```python
def start_streaming(self):
    """
    스트리밍 시작 시:
    1. 새 AI 메시지 버블 생성 (빈 상태)
    2. 새 Tool Section 생성
    """
    self._streaming_bubble = MessageBubble("assistant", "")
    self._current_tool_section = CollapsibleToolSection()
    
    self._messages_layout.addWidget(self._current_tool_section)
    self._messages_layout.addWidget(self._streaming_bubble)
```

### 7.6.2 토큰 수신

```python
def update_streaming(self, content: str):
    """
    토큰 수신 시:
    - 기존 버블 내용에 추가
    - 스크롤을 하단으로 유지
    """
    if self._streaming_bubble:
        self._streaming_bubble.update_content(content)
        self._scroll_to_bottom()
```

### 7.6.3 스크롤 동작

```python
SCROLL_TO_BOTTOM_DELAY_MS = 10  # 지연 시간

def _scroll_to_bottom(self):
    """
    비동기로 스크롤 (UI 업데이트 후)
    """
    QTimer.singleShot(
        SCROLL_TO_BOTTOM_DELAY_MS,
        lambda: self._scroll_area.verticalScrollBar().setValue(
            self._scroll_area.verticalScrollBar().maximum()
        )
    )
```

### 7.6.4 스트리밍 완료

```python
def finish_streaming(self):
    """
    스트리밍 완료 시:
    - 스트리밍 버블 참조 해제
    - Tool Section 축소 상태로 전환
    """
    self._streaming_bubble = None
    if self._current_tool_section:
        self._current_tool_section._toggle_collapsed()
```

## 7.7 시그널 정의

```python
class ChatPanel(QWidget):
    message_sent = Signal(str)           # 사용자 메시지 전송
    new_conversation_requested = Signal() # 새 대화 시작
    cancel_requested = Signal()          # AI 처리 취소
```

## 7.8 ChatViewModel 연결

```python
# MainWindow에서 시그널 연결
self._chat_panel.message_sent.connect(self._chat_vm.send_user_message)
self._chat_panel.new_conversation_requested.connect(
    self._chat_vm.start_new_conversation
)
self._chat_panel.cancel_requested.connect(self._chat_vm.stop_generation)

# ChatViewModel에서 UI 업데이트
self._chat_vm.message_added.connect(
    lambda msg: self._chat_panel.append_message(msg.sender, msg.content)
)
self._chat_vm.streaming_started.connect(self._chat_panel.start_streaming)
self._chat_vm.streaming_token.connect(self._chat_panel.update_streaming)
self._chat_vm.streaming_finished.connect(self._chat_panel.finish_streaming)
self._chat_vm.tool_activity.connect(self._chat_panel.add_tool_activity)
self._chat_vm.input_requested.connect(
    lambda desc, fields: self._chat_panel.show_input_form(desc, fields, self._chat_vm)
)
self._chat_vm.conversation_cleared.connect(self._chat_panel.clear_display)
```

## 7.9 새 대화 시작

```python
def start_new_conversation(self):
    """
    새 대화 시작:
    1. 채팅 기록만 클리어 (파이프라인 유지)
    2. 초기 시스템 메시지 표시
    """
    self._messages.clear()
    self.conversation_cleared.emit()
    
    # 초기 메시지
    greeting = "Welcome! I'm your Scientific Analysis Agent. ..."
    self.initialize_with_engine_message(greeting)
```

---

*다음: [08-menu-toolbar.md](./08-menu-toolbar.md) - 메뉴바 및 툴바 구성 상세*
</Parameter>
<parameter name="Complexity">5
