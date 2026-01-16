# 12. 데이터 흐름 및 아키텍처

## 12.1 MVVM 아키텍처

### 12.1.1 계층 구조

```
┌─────────────────────────────────────────────────────────────────────┐
│                           View Layer                                 │
│  (MainWindow, VTKWidget, ChatPanel, PropertiesPanel, ...)           │
├─────────────────────────────────────────────────────────────────────┤
│                         ViewModel Layer                              │
│  (PipelineViewModel, VTKViewModel, ChatViewModel, ...)              │
├─────────────────────────────────────────────────────────────────────┤
│                          Model Layer                                 │
│  (PipelineItem, TableDataModel, ChatMessage, ...)                   │
├─────────────────────────────────────────────────────────────────────┤
│                         Service Layer                                │
│  (VTKRenderService, FileLoaderService, AgentService)                │
└─────────────────────────────────────────────────────────────────────┘
```

### 12.1.2 계층별 책임

| 계층 | 책임 | 예시 |
|------|------|------|
| View | UI 렌더링, 사용자 입력 처리 | 버튼 클릭, 텍스트 표시 |
| ViewModel | 상태 관리, 비즈니스 로직 조정 | 아이템 선택, 필터 적용 |
| Model | 데이터 구조 정의 | PipelineItem 속성들 |
| Service | 핵심 기능 구현 | VTK 렌더링, 파일 로딩 |

### 12.1.3 의존성 규칙

```
View → ViewModel → Model
         ↓
      Service
```

- View는 ViewModel만 알고 있음
- ViewModel은 Model과 Service를 사용
- Model은 순수 데이터 (다른 계층 의존 없음)
- Service는 외부 라이브러리와 상호작용

---

## 12.2 Signal-Slot 패턴

### 12.2.1 Qt Signal 정의

```python
from PySide6.QtCore import Signal

class PipelineViewModel(QObject):
    # 데이터 변경 시그널
    item_added = Signal(object)           # PipelineItem
    item_removed = Signal(str)            # item_id
    item_updated = Signal(object)         # PipelineItem
    
    # 선택 시그널
    selection_changed = Signal(object)    # PipelineItem or None
    
    # 스타일 시그널
    item_style_changed = Signal(str, str) # item_id, style
```

### 12.2.2 Signal 연결

```python
# MainWindow에서 Signal-Slot 연결
def _connect_signals(self):
    # ViewModel → View 연결
    self._pipeline_vm.item_added.connect(self._on_item_added)
    self._pipeline_vm.selection_changed.connect(self._on_selection_changed)
    
    # View → ViewModel 연결
    self._pipeline_browser.item_selected.connect(
        lambda item_id: self._pipeline_vm.select_item(item_id)
    )
```

### 12.2.3 Signal 발생

```python
class PipelineViewModel:
    def add_item(self, item: PipelineItem):
        self.items[item.id] = item
        self.item_added.emit(item)  # Signal 발생
```

### 12.2.4 Signal 수신 (Slot)

```python
class MainWindow:
    def _on_item_added(self, item: PipelineItem):
        # Pipeline Browser에 아이템 추가
        self._pipeline_browser.add_item(item)
        
        # VTK에 actor 추가
        if item.actor:
            self._vtk_vm.add_actor(item.actor)
```

---

## 12.3 데이터 흐름 다이어그램

### 12.3.1 파일 로드 흐름

```
┌──────────────┐
│ User Action  │  File → Load Data...
└──────┬───────┘
       ▼
┌──────────────┐
│   View       │  QFileDialog.getOpenFileNames()
│ (MainWindow) │
└──────┬───────┘
       ▼
┌──────────────┐
│  ViewModel   │  pipeline_vm.load_file(path)
│ (PipelineVM) │
└──────┬───────┘
       ▼
┌──────────────┐
│   Service    │  file_loader.load(path)
│(FileLoader)  │     → VTK reader 사용
└──────┬───────┘
       ▼
┌──────────────┐
│    Model     │  PipelineItem 생성
│(PipelineItem)│     - vtk_data
└──────┬───────┘     - actor
       ▼
┌──────────────┐
│   Service    │  render_service.create_actor()
│(VTKRender)   │
└──────┬───────┘
       ▼
┌──────────────┐
│  ViewModel   │  item_added.emit(item)
│ (Signal)     │
└──────┬───────┘
       │
       ├────────────────┬────────────────┐
       ▼                ▼                ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   View       │ │    View      │ │    View      │
│(Pipeline     │ │  (VTKWidget) │ │ (Properties) │
│  Browser)    │ │              │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
   트리에 추가      actor 추가      속성 표시
```

### 12.3.2 필터 적용 흐름

```
┌──────────────┐
│ User Action  │  Filters → Slice
└──────┬───────┘
       ▼
┌──────────────┐
│  ViewModel   │  pipeline_vm.apply_filter("slice_filter", parent_id)
│ (PipelineVM) │
└──────┬───────┘
       │
       ├──▶ 1. 필터 인스턴스 가져오기
       │        filter = filters.get_filter("slice_filter")
       │
       ├──▶ 2. 기본 파라미터 생성
       │        params = filter.create_default_params()
       │
       ├──▶ 3. 부모 데이터로 파라미터 조정
       │        params["origin"] = parent.center()
       │
       ├──▶ 4. 필터 적용
       │        actor, output = filter.apply_filter(parent.vtk_data, params)
       │
       ├──▶ 5. PipelineItem 생성
       │        item = PipelineItem(type="slice_filter", parent_id=parent.id)
       │
       └──▶ 6. Signal 발생
                item_added.emit(item)
                selection_changed.emit(item)
```

### 12.3.3 채팅 메시지 흐름

```
┌──────────────┐
│ User Input   │  "온도가 300K 이상인 영역을 보여줘"
└──────┬───────┘
       ▼
┌──────────────┐
│    View      │  message_sent.emit(text)
│ (ChatPanel)  │
└──────┬───────┘
       ▼
┌──────────────┐
│  ViewModel   │  chat_vm.send_user_message(text)
│  (ChatVM)    │
└──────┬───────┘
       │
       ├──▶ 1. 사용자 메시지 저장
       │
       ├──▶ 2. UI 비활성화 시그널
       │        streaming_started.emit()
       │
       ├──▶ 3. 에이전트 워커 시작 (별도 스레드)
       │        worker = AgentWorker(messages)
       │        worker.start()
       │
       └──▶ 4. 스트리밍 수신
                ┌─────────────────────────┐
                │   Agent Worker Thread   │
                │                         │
                │  LangGraph 실행         │
                │       │                 │
                │       ├──▶ 토큰 생성    │
                │       │    streaming_token.emit()
                │       │                 │
                │       ├──▶ 도구 호출    │
                │       │    tool_activity.emit()
                │       │                 │
                │       └──▶ 완료         │
                │            streaming_finished.emit()
                └─────────────────────────┘
```

---

## 12.4 상태 관리

### 12.4.1 PipelineViewModel 상태

```python
class PipelineViewModel(QObject):
    def __init__(self):
        # 모든 아이템 저장
        self.items: Dict[str, PipelineItem] = {}
        
        # 현재 선택된 아이템
        self._selected_item: Optional[PipelineItem] = None
        
        # 필터 인스턴스 캐시
        self._filters: Dict[str, FilterBase] = {}
```

### 12.4.2 VTKViewModel 상태

```python
class VTKViewModel(QObject):
    def __init__(self):
        # 현재 배경색
        self._background_color = DEFAULT_BACKGROUND_COLOR
        
        # Legend 설정
        self._legend_settings = DEFAULT_LEGEND_SETTINGS.copy()
        
        # 등록된 actor 목록 (선택적)
        self._actors: Set[vtkActor] = set()
```

### 12.4.3 ChatViewModel 상태

```python
class ChatViewModel(QObject):
    def __init__(self):
        # 메시지 히스토리
        self._messages: List[ChatMessage] = []
        
        # 현재 스트리밍 상태
        self._is_streaming: bool = False
        
        # 에이전트 인스턴스
        self._agent = None
        
        # 워커 스레드
        self._worker: Optional[AgentWorker] = None
```

### 12.4.4 TabManagerViewModel 상태

```python
class TabManagerViewModel(QObject):
    def __init__(self):
        # 탭 레지스트리
        self._tabs: Dict[str, TabInfo] = {}
        # {tab_id: {"name": str, "type": str, "pinned": bool}}
```

---

## 12.5 VTK 데이터 파이프라인

### 12.5.1 데이터 객체

```
vtkDataObject
     │
     ├── vtkDataSet
     │        │
     │        ├── vtkImageData          (정규 그리드)
     │        ├── vtkRectilinearGrid    (직교 그리드)
     │        ├── vtkStructuredGrid     (구조 그리드)
     │        ├── vtkPolyData           (다각형 메시)
     │        └── vtkUnstructuredGrid   (비구조 메시)
     │
     └── ...
```

### 12.5.2 파이프라인 연결

```python
# VTK 파이프라인 예시: 파일 로드 → 필터 → 매퍼 → 액터

# 1. 소스 (리더)
reader = vtk.vtkXMLUnstructuredGridReader()
reader.SetFileName("data.vtu")
reader.Update()

# 2. 필터
threshold = vtk.vtkThreshold()
threshold.SetInputData(reader.GetOutput())
threshold.ThresholdByUpper(300)
threshold.Update()

# 3. 지오메트리 추출 (UnstructuredGrid → PolyData)
geometry = vtk.vtkDataSetSurfaceFilter()
geometry.SetInputData(threshold.GetOutput())
geometry.Update()

# 4. 매퍼
mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(geometry.GetOutput())
mapper.SetScalarModeToUsePointData()
mapper.SelectColorArray("Temperature")

# 5. 액터
actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetOpacity(1.0)
```

### 12.5.3 데이터 배열

```python
# 데이터 배열 접근
data = reader.GetOutput()

# Point 데이터 배열
point_data = data.GetPointData()
num_arrays = point_data.GetNumberOfArrays()

for i in range(num_arrays):
    array = point_data.GetArray(i)
    name = array.GetName()
    num_components = array.GetNumberOfComponents()
    num_tuples = array.GetNumberOfTuples()

# Cell 데이터 배열
cell_data = data.GetCellData()
```

---

## 12.6 LangGraph 에이전트 아키텍처

### 12.6.1 그래프 구조

```
                   ┌─────────────┐
                   │   Start     │
                   └──────┬──────┘
                          │
                          ▼
                   ┌─────────────┐
           ┌───────│   Router    │───────┐
           │       └─────────────┘       │
           │              │              │
           ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Intent  │   │   Tool   │   │  Final   │
    │ Analyzer │   │ Executor │   │ Response │
    └────┬─────┘   └────┬─────┘   └────┬─────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                        ▼
                   ┌─────────────┐
                   │    End      │
                   └─────────────┘
```

### 12.6.2 노드 정의

```python
# agent/graph.py
from langgraph.graph import StateGraph

def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # 노드 추가
    workflow.add_node("router", router_node)
    workflow.add_node("intent_analyzer", intent_node)
    workflow.add_node("tool_executor", tool_node)
    workflow.add_node("response_generator", response_node)
    
    # 엣지 추가
    workflow.add_edge("router", "intent_analyzer")
    workflow.add_conditional_edges(
        "intent_analyzer",
        should_use_tool,
        {
            True: "tool_executor",
            False: "response_generator"
        }
    )
    workflow.add_edge("tool_executor", "response_generator")
    
    return workflow.compile()
```

### 12.6.3 도구 정의

```python
# agent/tools/visualization_tools.py
from langchain.tools import tool

@tool
def load_file(file_path: str) -> str:
    """VTK 파일을 로드합니다."""
    pipeline_vm = get_pipeline_viewmodel()
    item = pipeline_vm.load_file(file_path)
    return f"파일 '{file_path}' 로드 완료. 아이템 ID: {item.id}"

@tool
def apply_threshold(item_id: str, array_name: str, 
                   lower: float, upper: float) -> str:
    """Threshold 필터를 적용합니다."""
    pipeline_vm = get_pipeline_viewmodel()
    filter_item = pipeline_vm.apply_filter("threshold_filter", item_id)
    pipeline_vm.update_filter_params(filter_item.id, {
        "array_name": array_name,
        "lower_bound": lower,
        "upper_bound": upper,
        "method": "between"
    })
    pipeline_vm.commit_filter(filter_item.id)
    return f"Threshold 필터 적용 완료"
```

---

## 12.7 스레딩 모델

### 12.7.1 메인 스레드

- Qt 이벤트 루프
- UI 업데이트
- 시그널 발생/수신

### 12.7.2 워커 스레드

```python
class AgentWorker(QThread):
    """AI 에이전트 실행 워커 스레드"""
    
    token_generated = Signal(str)
    tool_called = Signal(str, str)  # name, result
    finished = Signal()
    error = Signal(str)
    
    def run(self):
        try:
            for event in self._agent.stream(self._input):
                if self._stop_requested:
                    break
                
                if "token" in event:
                    self.token_generated.emit(event["token"])
                elif "tool" in event:
                    self.tool_called.emit(
                        event["tool"]["name"],
                        event["tool"]["result"]
                    )
            
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))
```

### 12.7.3 스레드 안전성

```python
# 도구 실행 시 메인 스레드에서 UI 업데이트
@tool
def set_camera_position(x: float, y: float, z: float):
    # 메인 스레드로 시그널 발송
    QMetaObject.invokeMethod(
        vtk_vm, "apply_camera_position",
        Qt.QueuedConnection,
        Q_ARG(float, x), Q_ARG(float, y), Q_ARG(float, z)
    )
```

---

## 12.8 App Context

### 12.8.1 전역 컨텍스트

```python
# utils/app_context.py
_pipeline_viewmodel: Optional[PipelineViewModel] = None
_vtk_viewmodel: Optional[VTKViewModel] = None
_time_series_manager: Optional[TimeSeriesManager] = None
_tab_manager_viewmodel: Optional[TabManagerViewModel] = None

def set_pipeline_viewmodel(vm: PipelineViewModel):
    global _pipeline_viewmodel
    _pipeline_viewmodel = vm

def get_pipeline_viewmodel() -> PipelineViewModel:
    return _pipeline_viewmodel
```

### 12.8.2 용도

- 에이전트 도구에서 ViewModel 접근
- 전역 서비스 접근
- 주의: 최소한으로 사용 (테스트 어려움)

---

*다음: [13-performance-optimization.md](./13-performance-optimization.md) - 성능 최적화 전략*
