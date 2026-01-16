# 4. 중앙 패널 (탭 뷰 시스템)

## 4.1 TabbedViewWidget 개요

### 4.1.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `TabbedViewWidget` (QTabWidget 확장) |
| 탭 위치 | 상단 |
| 탭 닫기 가능 | ✅ (고정 탭 제외) |
| 탭 이동 가능 | ✅ |

### 4.1.2 레이아웃

```
┌──────────────────────────────────────────────────────────────────────┐
│ [📌 3D View ×] [Table ×] [Graph ×]                          [+]     │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                                                                      │
│                        Active Tab Content                            │
│                                                                      │
│                    (VTKWidget / TableViewWidget /                    │
│                     GraphViewWidget)                                 │
│                                                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

## 4.2 탭 타입

### 4.2.1 지원 탭 타입

| 타입 | 식별자 | 위젯 | 설명 |
|------|--------|------|------|
| 3D View | `"vtk"` | `VTKWidget` | VTK 3D 렌더링 |
| Table | `"table"` | `TableViewWidget` | 데이터 테이블 |
| Graph | `"graph"` | `GraphViewWidget` | Matplotlib 그래프 |

### 4.2.2 탭 메타데이터

```python
# 각 탭의 메타데이터 구조
tab_metadata = {
    "id": str,          # 고유 탭 ID (예: "tab_1")
    "type": str,        # "vtk", "table", "graph"
    "name": str,        # 표시 이름
    "pinned": bool,     # 고정 여부
    "index": int,       # 현재 탭 인덱스
    "widget": QWidget,  # 실제 위젯 참조
}
```

## 4.3 탭 생성

### 4.3.1 [+] 버튼 클릭 시

```
┌─────────────────────────────────────┐
│         Create New Tab              │
├─────────────────────────────────────┤
│                                     │
│  Tab Type: [▼ 3D View / Table / Graph]
│                                     │
│  Tab Name: [________________]       │
│                                     │
├─────────────────────────────────────┤
│        [Cancel]       [OK]          │
└─────────────────────────────────────┘
```

### 4.3.2 TabCreationDialog

```python
class TabCreationDialog(QDialog):
    """
    탭 생성 다이얼로그
    """
    def __init__(self):
        self._type_combo = QComboBox()
        self._type_combo.addItems(["3D View", "Table", "Graph"])
        
        self._name_edit = QLineEdit()
        # 기본 이름은 타입에 따라 자동 설정
        
        buttons = QDialogButtonBox(OK | Cancel)
```

### 4.3.3 타입별 기본 이름

| 타입 | 기본 이름 | 중복 시 |
|------|-----------|---------|
| 3D View | "3D View" | "3D View 2", "3D View 3"... |
| Table | "Table" | "Table 2", "Table 3"... |
| Graph | "Graph" | "Graph 2", "Graph 3"... |

## 4.4 탭 관리

### 4.4.1 우클릭 컨텍스트 메뉴

```
┌─────────────────────────┐
│ 📌 Pin Tab              │  (또는 Unpin Tab)
│ ✏️ Rename Tab           │
│ ─────────────────────── │
│ ❌ Close Tab            │
│ 🗑️ Close Other Tabs    │
└─────────────────────────┘
```

### 4.4.2 Pin/Unpin 동작

- **Pin**: 탭 닫기 버튼(×) 숨김, 삭제 불가
- **Unpin**: 탭 닫기 버튼 표시, 삭제 가능
- 고정 탭 표시: 탭 이름 앞에 📌 아이콘

### 4.4.3 Rename 동작

```
┌────────────────────────────────────┐
│         Rename Tab                  │
├────────────────────────────────────┤
│  New Name: [________________]       │
├────────────────────────────────────┤
│      [Cancel]       [OK]            │
└────────────────────────────────────┘
```

### 4.4.4 Close 동작

1. 고정(pinned) 탭은 닫기 불가 (경고 메시지)
2. 닫기 전 확인 메시지 없음 (즉시 닫기)
3. 마지막 하나 남은 탭은 닫을 수 있음 (빈 상태 허용)

## 4.5 시그널 정의

```python
class TabbedViewWidget(QTabWidget):
    tab_created = Signal(str, str, str)   # tab_id, tab_type, tab_name
    tab_closed = Signal(str)              # tab_id
    tab_pinned = Signal(str, bool)        # tab_id, is_pinned
    tab_renamed = Signal(str, str)        # tab_id, new_name
```

## 4.6 탭 전환 시 동작

### 4.6.1 _on_tab_changed 흐름

```
[사용자가 탭 클릭]
         │
         ▼
[currentChanged 시그널]
         │
         ▼
[MainWindow._on_tab_changed]
         │
         ├──▶ active_tab_id, active_tab_type 업데이트
         │
         └──▶ [_update_for_active_tab]
                      │
                      ├──▶ Properties Panel 모드 변경
                      │     (VTK용 / Table용 / Graph용)
                      │
                      └──▶ 선택된 아이템으로 탭 콘텐츠 업데이트
```

### 4.6.2 Properties Panel 모드

| 탭 타입 | Properties Panel 표시 내용 |
|---------|---------------------------|
| VTK | 렌더링 속성 (색상, 투명도, 표현 방식 등) |
| Table | 테이블 속성 (TablePropertiesWidget) |
| Graph | 그래프 속성 (GraphPropertiesWidget) |

## 4.7 아이템-탭 매핑

### 4.7.1 매핑 구조

```python
# MainWindow에서 관리
_tab_item_mapping: Dict[str, str] = {}  # {tab_id: item_id}
```

### 4.7.2 매핑 동작

- Pipeline에서 아이템 선택 시, 현재 활성 탭에 해당 아이템 매핑
- 탭 전환 시, 매핑된 아이템으로 콘텐츠 업데이트

## 4.8 탭별 데이터 업데이트

### 4.8.1 VTK 탭 업데이트

```python
def _update_vtk_tab(self):
    """
    모든 파이프라인 아이템의 actor가 이미 VTK 렌더러에 추가되어 있음
    → 별도 업데이트 불필요 (Properties Panel만 갱신)
    """
    pass
```

### 4.8.2 Table 탭 업데이트

```python
def _update_table_tab(self, item):
    """
    선택된 아이템의 데이터를 테이블에 로드
    """
    widget = self._get_validated_tab_widget(TabType.TABLE)
    if not widget:
        return
    
    # 같은 아이템이면 새로고침만
    if widget.viewmodel.source_item_id == item.id:
        widget.viewmodel.set_visibility(item.visible)
        if item.visible:
            widget.viewmodel.refresh_data()
        return
    
    # 새 아이템 로드
    widget.viewmodel.set_data_source(item.id, "POINT")
```

### 4.8.3 Graph 탭 업데이트

```python
def _update_graph_tab(self, item):
    """
    모든 visible 아이템을 그래프 데이터 소스로 추가
    """
    widget = self._get_validated_tab_widget(TabType.GRAPH)
    if not widget:
        return
    
    # 모든 visible 아이템 추가
    for pid, pitem in self._pipeline_vm.items.items():
        if pitem.visible:
            widget.viewmodel.add_data_source(pid)
```

## 4.9 새 VTK 탭 생성 시 초기화

```python
def _initialize_vtk_widget_with_data(self, widget):
    """
    기존 파이프라인의 모든 visible actor를 새 VTK 위젯에 추가
    """
    for item in self._pipeline_vm.items.values():
        if item.actor and item.visible:
            widget.add_actor(item.actor)
    
    widget.reset_camera()
    widget.render()
```

## 4.10 VTK 위젯 시그널 연결

새 VTK 탭 생성 시 연결해야 하는 시그널:

```python
def _connect_vtk_widget_signals(self, widget):
    self._vtk_vm.render_requested.connect(widget.render)
    self._vtk_vm.actor_added.connect(widget.add_actor)
    self._vtk_vm.actor_removed.connect(widget.remove_actor)
    self._vtk_vm.actor_visibility_changed.connect(widget.set_actor_visibility)
    self._vtk_vm.clear_scene_requested.connect(widget.clear_scene)
    self._vtk_vm.background_changed.connect(widget.set_background)
    self._vtk_vm.camera_reset_requested.connect(widget.reset_camera)
    self._vtk_vm.view_plane_requested.connect(widget.set_view_plane)
    self._vtk_vm.plane_preview_requested.connect(widget.update_plane_preview)
    self._vtk_vm.plane_preview_hide_requested.connect(widget.hide_plane_preview)
    self._vtk_vm.camera_apply_requested.connect(widget.apply_camera_state)
    self._vtk_vm.scalar_bar_update_requested.connect(widget.update_scalar_bar)
    self._vtk_vm.scalar_bar_hide_requested.connect(widget.hide_scalar_bar)
    self._vtk_vm.legend_settings_changed.connect(widget.apply_legend_settings)
    self._chat_vm.render_requested.connect(widget.render)
```

## 4.11 TabManagerViewModel

AI 에이전트가 탭을 관리할 수 있도록 하는 ViewModel:

### 4.11.1 시그널

```python
class TabManagerViewModel(QObject):
    vtk_view_requested = Signal(str)               # tab_name
    table_view_requested = Signal(str, str, str)   # item_id, tab_name, array_type
    graph_view_requested = Signal(str, str, str, str, str, str)  
                    # graph_type, item_id, y_array, x_array, tab_name, array_type
    tab_close_requested = Signal(str)              # tab_id
    tab_pin_requested = Signal(str, bool)          # tab_id, pinned
```

### 4.11.2 탭 레지스트리

```python
def register_tab(self, tab_id, tab_name, tab_type, pinned=False):
    """탭 생성 시 등록"""
    
def unregister_tab(self, tab_id):
    """탭 삭제 시 등록 해제"""
    
def get_tabs_info(self):
    """에이전트 도구용 - 모든 탭 정보 반환"""
```

---

*다음: [05-vtk-render-view.md](./05-vtk-render-view.md) - VTK 렌더 뷰 상세*
