# 3. 좌측 사이드바 상세

## 3.1 구조 개요

```
┌──────────────────────────┐
│    Pipeline Browser      │  ← QTreeWidget 확장
│    (PipelineBrowserWidget)
├──────────────────────────┤
│    Details Tabs          │  ← QTabWidget
│   ┌────────────┬────────┐│
│   │ Properties │  Info  ││
│   └────────────┴────────┘│
│                          │
│   (Properties Panel)     │  ← 동적 콘텐츠
│   or                     │
│   (Info Page)            │  ← QTextEdit (읽기 전용)
│                          │
└──────────────────────────┘
```

---

## 3.2 Pipeline Browser

### 3.2.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `PipelineBrowserWidget` (QTreeWidget 확장) |
| 헤더 라벨 | "Pipeline Browser" |
| 컬럼 수 | 1 (아이템 이름) |

### 3.2.2 트리 아이템 구조

각 아이템은 다음 정보를 포함:

```python
class PipelineItem:
    id: str              # 고유 ID (UUID)
    name: str            # 표시 이름
    parent_id: str       # 부모 아이템 ID (없으면 None)
    item_type: str       # "source", "slice_filter", "clip_filter" 등
    visible: bool        # 가시성 상태
    actor: VTKActor      # VTK 렌더링 액터
    vtk_data: VTKData    # VTK 데이터 객체
    filter_params: dict  # 필터 파라미터 (필터인 경우)
```

### 3.2.3 트리 시각화

```
Pipeline Browser
├─ [✓] cylinder.vtu           ← 소스 (체크박스로 가시성)
│   ├─ [✓] Slice              ← 필터 (부모에 적용된)
│   └─ [✓] Threshold          ← 또 다른 필터
└─ [✓] cone_source            ← 다른 소스
```

### 3.2.4 체크박스 동작

- **체크(✓)**: 아이템 표시 (visible = true)
- **미체크(☐)**: 아이템 숨김 (visible = false)

### 3.2.5 계층 표시 규칙

```python
def _add_item_recursive(self, item, ui_parent):
    """
    특별 규칙: 자식이 하나만 있으면 같은 레벨에 표시
    (깊은 중첩 방지)
    """
    children = [c for c in items if c.parent_id == item.id]
    
    if len(children) == 1:
        # 같은 레벨에 추가
        self._add_item_recursive(children[0], ui_parent)
    else:
        # 자식으로 추가
        for child in children:
            self._add_item_recursive(child, tree_item)
```

### 3.2.6 우클릭 컨텍스트 메뉴

```
┌─────────────────┐
│   Delete        │
└─────────────────┘
```

| 메뉴 | 동작 |
|------|------|
| Delete | 선택된 아이템 삭제 (item_delete_requested 시그널 발생) |

### 3.2.7 시그널 정의

```python
class PipelineBrowserWidget(QTreeWidget):
    item_selected = Signal(str)           # item_id
    item_visibility_changed = Signal(str, bool)  # item_id, visible
    item_delete_requested = Signal(str)   # item_id
```

---

## 3.3 Details Tabs

### 3.3.1 탭 구성

| 순서 | 탭 이름 | 내용 |
|------|---------|------|
| 1 | Properties | `PropertiesPanel` 위젯 |
| 2 | Information | `QTextEdit` (읽기 전용) |

---

## 3.4 Properties Panel

### 3.4.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `PropertiesPanel` (QWidget 확장) |
| 스크롤 | QScrollArea 래핑 |
| 동적 콘텐츠 | 선택된 아이템/탭 타입에 따라 변경 |

### 3.4.2 탭 타입별 인터페이스

```python
class TabType(Enum):
    VTK = "vtk"       # 3D 뷰용 속성
    TABLE = "table"   # 테이블 뷰용 속성  
    GRAPH = "graph"   # 그래프 뷰용 속성
```

### 3.4.3 VTK 탭용 Properties Panel 구조

```
┌──────────────────────────────────────────┐
│  [Filter Params Section]                 │  ← 필터 아이템인 경우만
│  ┌────────────────────────────────────┐  │
│  │  (필터별 동적 위젯)                │  │
│  │  [Apply] 버튼                      │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  [View Controls Section]                 │
│  ┌────────────────────────────────────┐  │
│  │  Camera Position X: [___]          │  │
│  │  Camera Position Y: [___]          │  │
│  │  Camera Position Z: [___]          │  │
│  │  ...                               │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  [Coloring Section]                      │
│  ┌────────────────────────────────────┐  │
│  │  Color By: [▼ Combo]               │  │
│  │  Component: [▼ Combo]              │  │
│  │  [Fit Range] [Custom Range]        │  │
│  │  Custom Min: [___]                 │  │
│  │  Custom Max: [___]                 │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  [Styling Section]                       │
│  ┌────────────────────────────────────┐  │
│  │  Representation: [▼ Combo]         │  │
│  │  Opacity: [━━━━━━●━━] 100%         │  │
│  │  Point Size: [___]  (Points 모드)  │  │
│  │  Line Width: [___]  (Wireframe)    │  │
│  │  Gaussian Scale: [___]             │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  [Legend Settings Section]               │
│  ┌────────────────────────────────────┐  │
│  │  Font Size: [___]                  │  │
│  │  Position X: [___]                 │  │
│  │  Position Y: [___]                 │  │
│  │  Width: [___]                      │  │
│  │  Height: [___]                     │  │
│  └────────────────────────────────────┘  │
├──────────────────────────────────────────┤
│  ┌────────────────────────────────────┐  │
│  │        [Delete] 버튼               │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 3.4.4 시그널 정의

```python
class PropertiesPanel(QWidget):
    apply_filter_requested = Signal(str)       # item_id
    delete_requested = Signal(str)             # item_id
    opacity_changed = Signal(str, float)       # item_id, opacity
    point_size_changed = Signal(str, float)    # item_id, size
    line_width_changed = Signal(str, float)    # item_id, width
    gaussian_scale_changed = Signal(str, float) # item_id, scale
    color_by_changed = Signal(str, str, str, str) # item_id, array_name, array_type, component
    filter_params_changed = Signal(str, dict)  # item_id, params
    legend_settings_changed = Signal(dict)     # settings
    custom_range_requested = Signal()
    representation_style_changed = Signal(str, str) # item_id, style
```

### 3.4.5 Representation 옵션

```python
REPRESENTATION_STYLES = [
    "Surface",           # 표면 렌더링
    "Wireframe",         # 와이어프레임
    "Points",            # 점 렌더링
    "Surface With Edges", # 표면 + 에지
    "Point Gaussian",    # 가우시안 스플랫
]
```

### 3.4.6 스타일별 표시 컨트롤

| 스타일 | Point Size | Line Width | Gaussian Scale |
|--------|------------|------------|----------------|
| Surface | ❌ | ❌ | ❌ |
| Wireframe | ❌ | ✅ | ❌ |
| Points | ✅ | ❌ | ❌ |
| Surface With Edges | ❌ | ✅ (에지) | ❌ |
| Point Gaussian | ❌ | ❌ | ✅ |

### 3.4.7 Opacity 슬라이더

```python
OPACITY_SLIDER_MAX = 100  # 0-100 범위

# 슬라이더 값 -> 실제 불투명도
opacity = slider_value / 100.0  # 0.0 ~ 1.0
```

### 3.4.8 Color By 콤보박스

```
┌─────────────────────────────────┐
│ Solid Color                     │  ← 단일 색상
├─────────────────────────────────┤
│ --- POINT ---                   │  ← 구분자
│ Pressure                        │  ← Point 데이터
│ Velocity                        │
├─────────────────────────────────┤
│ --- CELL ---                    │  ← 구분자
│ CellId                          │  ← Cell 데이터
│ Temperature                     │
└─────────────────────────────────┘
```

### 3.4.9 Component 콤보박스 (벡터 데이터)

```
┌─────────────────────────────────┐
│ Magnitude                       │  ← 벡터 크기
│ X                               │  ← X 성분
│ Y                               │  ← Y 성분
│ Z                               │  ← Z 성분
└─────────────────────────────────┘
```

---

## 3.5 Information Page

### 3.5.1 기본 정보

| 속성 | 값 |
|------|-----|
| 위젯 | `QTextEdit` |
| 읽기 전용 | `True` |
| 내용 | 선택된 아이템의 상세 정보 |

### 3.5.2 표시 정보 예시

```
Name: cylinder.vtu
Type: source
Visible: True
Data Type: UnstructuredGrid

Bounds:
  X: [-1.0000, 1.0000]
  Y: [-1.0000, 1.0000]
  Z: [-0.5000, 0.5000]

Points: 482
Cells: 960

POINT Data Arrays:
  - Pressure (1 components)
  - Velocity (3 components)

CELL Data Arrays:
  - CellId (1 components)
```

---

## 3.6 상호작용 흐름

### 3.6.1 아이템 선택 시

```
[사용자가 트리 아이템 클릭]
         │
         ▼
[PipelineBrowserWidget.item_selected 시그널]
         │
         ▼
[MainWindow._on_browser_selection]
         │
         ▼
[PipelineViewModel.select_item]
         │
         ▼
[PipelineViewModel.selection_changed 시그널]
         │
         ├──▶ [MainWindow._on_selection_changed]
         │            │
         │            ├──▶ Properties Panel 업데이트
         │            ├──▶ Info Page 업데이트
         │            └──▶ 현재 탭 뷰 업데이트
         │
         └──▶ [ToolbarManager._on_item_selected]
                      │
                      └──▶ Representation 버튼 텍스트 업데이트
```

### 3.6.2 가시성 변경 시

```
[사용자가 체크박스 클릭]
         │
         ▼
[item_visibility_changed 시그널(item_id, visible)]
         │
         ▼
[MainWindow._on_visibility_changed]
         │
         ├──▶ [PipelineViewModel.set_visibility]
         │
         ├──▶ [VTKViewModel.set_actor_visibility]
         │
         └──▶ [각 탭의 viewmodel 업데이트]
                  └──▶ Table: set_visibility
                  └──▶ Graph: 데이터 추가/제거
```

### 3.6.3 삭제 요청 시

```
[우클릭 → Delete 선택]
         │
         ▼
[item_delete_requested 시그널]
         │
         ▼
[MainWindow._on_delete_requested]
         │
         ├──▶ [VTKViewModel.remove_actor]
         │
         ├──▶ [PipelineViewModel.delete_item]
         │            │
         │            └──▶ 자식 아이템들도 재귀적 삭제
         │
         └──▶ [VTKViewModel.hide_plane_preview]
```

---

*다음: [04-center-panel.md](./04-center-panel.md) - 중앙 패널 상세*
