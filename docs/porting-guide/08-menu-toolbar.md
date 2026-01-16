# 8. 메뉴바 및 툴바 구성

## 8.1 메뉴바 (Menu Bar)

### 8.1.1 전체 구조

```
┌────────┬──────────┬────────┐
│  File  │ Filters  │  View  │
└────────┴──────────┴────────┘
```

### 8.1.2 MenuBarManager 클래스

```python
class MenuBarManager:
    """
    메뉴바 설정 및 관리
    MainWindow에서 추출하여 코드 정리
    """
    def __init__(self,
                 main_window: QMainWindow,
                 pipeline_vm: PipelineViewModel,
                 on_load_file: Callable,
                 on_apply_filter: Callable[[str], None],
                 create_tab: Callable[[str, str], None]):
        pass
```

## 8.2 File 메뉴

### 8.2.1 메뉴 항목

```
┌─────────────────────────┐
│ 📂 Load Data...   Ctrl+O│
├─────────────────────────┤
│ ❌ Exit           Ctrl+Q│
└─────────────────────────┘
```

| 항목 | 단축키 | 콜백 | 동작 |
|------|--------|------|------|
| Load Data... | Ctrl+O | `_on_load_file` | 파일 다이얼로그 열기 |
| Exit | Ctrl+Q | `main_window.close` | 애플리케이션 종료 |

### 8.2.2 Load Data 동작

```python
def _on_load_file(self):
    file_names, _ = QFileDialog.getOpenFileNames(
        self,
        "Load Data",
        "",
        "VTK Files (*.vtu *.vti *.vtk)"
    )
    
    if not file_names:
        return
    
    if len(file_names) > 1:
        # 다중 파일: 시계열로 로드
        item = self._pipeline_vm.load_time_series(file_names)
    else:
        # 단일 파일
        item = self._pipeline_vm.load_file(file_names[0])
    
    if item:
        self._vtk_vm.add_actor(item.actor)
        self._vtk_vm.reset_camera()
        self._pipeline_vm.select_item(item.id)
```

## 8.3 Filters 메뉴

### 8.3.1 메뉴 항목

```
┌─────────────────────────┐
│ ✂️ Slice                │
│ 🔪 Clip                 │
│ 📊 Threshold            │
│ 🧮 Calculator           │
└─────────────────────────┘
```

### 8.3.2 동적 생성

```python
def _populate_filters_menu(self, menu: QMenu):
    """
    필터 레지스트리에서 동적으로 메뉴 생성
    """
    for filter_type, display_name in self._pipeline_vm.get_available_filters():
        action = QAction(display_name, self._main_window)
        action.triggered.connect(
            lambda checked=False, ft=filter_type: self._on_apply_filter(ft)
        )
        menu.addAction(action)
```

### 8.3.3 필터 레지스트리

```python
# filters/__init__.py에서 정의
FILTER_REGISTRY = {
    "slice_filter": SliceFilter,
    "clip_filter": ClipFilter,
    "threshold_filter": ThresholdFilter,
    "calculator_filter": CalculatorFilter,
}

def get_available_filters():
    return [
        ("slice_filter", "Slice"),
        ("clip_filter", "Clip"),
        ("threshold_filter", "Threshold"),
        ("calculator_filter", "Calculator"),
    ]
```

### 8.3.4 필터 적용 동작

```python
def _on_apply_filter(self, filter_type: str):
    selected = self._pipeline_vm.selected_item
    
    if not selected:
        QMessageBox.warning(self, "Warning", 
            "Please select a source in Pipeline Browser.")
        return
    
    item = self._pipeline_vm.apply_filter(filter_type, selected.id)
    
    if item:
        self._vtk_vm.add_actor(item.actor)
        self._vtk_vm.request_render()
        self._pipeline_vm.select_item(item.id)
```

## 8.4 View 메뉴

### 8.4.1 메뉴 항목

```
┌─────────────────────────┐
│ 🖥️ New 3D View Tab      │
│ 📋 New Table View Tab   │
│ 📈 New Graph View Tab   │
└─────────────────────────┘
```

| 항목 | 파라미터 | 동작 |
|------|----------|------|
| New 3D View Tab | `("vtk", "3D View")` | VTK 탭 생성 |
| New Table View Tab | `("table", "Table")` | 테이블 탭 생성 |
| New Graph View Tab | `("graph", "Graph")` | 그래프 탭 생성 |

---

## 8.5 View Controls Toolbar

### 8.5.1 전체 구조

```
┌────────────────────────────────────────────────────────────────────────────────┐
│ [Camera View] [Home] │ [XY] [YZ] [XZ] │ [Fit Range] [Custom Range] │          │
│                      │                │                            │[BG▼][Rep▼]
└────────────────────────────────────────────────────────────────────────────────┘
```

### 8.5.2 ToolbarManager 클래스

```python
class ToolbarManager:
    """
    툴바 설정 및 관리
    """
    def __init__(self,
                 main_window: QMainWindow,
                 vtk_vm: VTKViewModel,
                 pipeline_vm: PipelineViewModel,
                 on_camera_view: Callable,
                 on_fit_range: Callable,
                 on_custom_range: Callable):
        pass
```

### 8.5.3 버튼 정의

| 버튼 | 텍스트 | 콜백 |
|------|--------|------|
| Camera View | "Camera View" | `_on_camera_view` |
| Home | "Home (Reset)" | `vtk_vm.reset_camera` |
| XY Plane | "XY Plane" | `vtk_vm.set_view_plane("xy")` |
| YZ Plane | "YZ Plane" | `vtk_vm.set_view_plane("yz")` |
| XZ Plane | "XZ Plane" | `vtk_vm.set_view_plane("xz")` |
| Fit Range | "Fit Range" | `_on_fit_range` |
| Custom Range | "Custom Range" | `_on_custom_range` |

### 8.5.4 드롭다운 스타일

```python
DROPDOWN_BUTTON_STYLE = (
    "QToolButton { padding-right: 15px; } "
    "QToolButton::menu-indicator { "
    "    subcontrol-origin: padding; "
    "    subcontrol-position: center right; "
    "}"
)
```

## 8.6 Background 드롭다운

### 8.6.1 메뉴 항목

```
┌─────────────────────────┐
│ Warm Gray (Default)     │ ← 현재 선택 표시
│ Blue Gray               │
│ Dark Gray               │
│ Neutral Gray            │
│ Light Gray              │
│ White                   │
│ Black                   │
│ Gradient Background     │
└─────────────────────────┘
```

### 8.6.2 프리셋 정의

```python
BACKGROUND_PRESETS = {
    "Warm Gray (Default)": ((0.32, 0.34, 0.43), None),
    "Blue Gray": ((0.25, 0.30, 0.38), None),
    "Dark Gray": ((0.15, 0.15, 0.18), None),
    "Neutral Gray": ((0.3, 0.3, 0.3), None),
    "Light Gray": ((0.8, 0.8, 0.82), None),
    "White": ((0.95, 0.95, 0.97), None),
    "Black": ((0.05, 0.05, 0.07), None),
    "Gradient Background": ((0.2, 0.2, 0.3), (0.5, 0.5, 0.6)),
}
```

### 8.6.3 버튼 텍스트 동기화

```python
def _on_background_changed(self, name: str):
    """배경 변경 시 버튼 텍스트 업데이트"""
    if self._background_btn:
        self._background_btn.setText(name)
```

## 8.7 Representation 드롭다운

### 8.7.1 메뉴 항목

```
┌─────────────────────────┐
│ Surface                 │ ← 선택된 아이템의 현재 스타일
│ Wireframe               │
│ Points                  │
│ Surface With Edges      │
│ Point Gaussian          │
└─────────────────────────┘
```

### 8.7.2 스타일 정의

```python
REPRESENTATION_STYLES = [
    "Surface",
    "Wireframe",
    "Points",
    "Surface With Edges",
    "Point Gaussian",
]
```

### 8.7.3 선택 아이템 동기화

```python
def _set_selected_item_representation(self, style: str):
    """선택된 아이템의 표현 스타일 변경"""
    selected = self._pipeline_vm.selected_item
    if selected:
        self._pipeline_vm.set_representation(selected.id, style)
        self._vtk_vm.request_render()

def _on_item_selected(self, item):
    """아이템 선택 시 버튼 텍스트 업데이트"""
    if item and self._representation_btn:
        style = self._vtk_vm.get_representation_style(item.actor)
        self._representation_btn.setText(style)
```

---

## 8.8 Time Animation Toolbar

### 8.8.1 전체 구조

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│ [|◀] [◀|] [◀] [▶] [|▶] [▶|] [⟳]  │  Time: [▼ Dropdown] [Spinner ↕] │ max is 0 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 8.8.2 TimeAnimationWidget 클래스

```python
class TimeAnimationWidget(QWidget):
    """시계열 애니메이션 제어 위젯"""
    
    time_index_changed = Signal(int)
    
    def __init__(self, time_manager: TimeSeriesManager):
        self._time_manager = time_manager
```

### 8.8.3 버튼 정의 (좌→우 순서)

| 버튼 | 아이콘 | 동작 |
|------|--------|------|
| First Frame | `\|◀` | 첫 번째 프레임으로 이동 |
| Previous Frame | `◀\|` | 이전 프레임으로 이동 |
| Play Backward | `◀` | 역방향 재생 |
| Play Forward | `▶` | 정방향 재생 |
| Next Frame | `\|▶` | 다음 프레임으로 이동 |
| Last Frame | `▶\|` | 마지막 프레임으로 이동 |
| Loop | `⟳` | 반복 재생 토글 |

### 8.8.4 시간 선택 컨트롤

```python
# 드롭다운
self._time_combo = QComboBox()
# 시간 스텝별로 항목 추가
for i in range(max_time + 1):
    self._time_combo.addItem(f"Time {i}")

# 스피너
self._time_spinner = QSpinBox()
self._time_spinner.setRange(0, max_time)
```

### 8.8.5 프레임 표시

```python
self._frame_label = QLabel("Frame: 0 / 0")

def _on_time_changed(self, item_id: str, time_index: int):
    self._frame_label.setText(
        f"Frame: {time_index} / {self._max_time}"
    )
```

### 8.8.6 활성화 상태

```python
def _update_enabled_state(self):
    """시계열 데이터 없으면 비활성화"""
    enabled = self._has_time_series
    
    self._play_back_btn.setEnabled(enabled)
    self._play_pause_btn.setEnabled(enabled)
    self._play_forward_btn.setEnabled(enabled)
    self._loop_btn.setEnabled(enabled)
    self._time_combo.setEnabled(enabled)
    self._time_spinner.setEnabled(enabled)
```

### 8.8.7 TimeSeriesManager

```python
class TimeSeriesManager(QObject):
    """시계열 데이터 재생 관리"""
    
    time_changed = Signal(str, int)  # item_id, time_index
    animation_state_changed = Signal(bool, bool)  # is_playing, is_forward
    
    def __init__(self):
        self._timer = QTimer()
        self._timer.timeout.connect(self._advance_time)
        self._interval_ms = DEFAULT_ANIMATION_INTERVAL_MS  # 100ms
        self._is_playing = False
        self._is_forward = True
        self._is_looping = False
```

### 8.8.8 애니메이션 상수

```python
DEFAULT_ANIMATION_INTERVAL_MS = 100  # 초당 10 프레임
```

---

*다음: [09-dialogs-popups.md](./09-dialogs-popups.md) - 다이얼로그 및 팝업 상세*
