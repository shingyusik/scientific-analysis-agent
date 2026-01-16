# 6. 테이블 및 그래프 뷰 상세

## 6.1 테이블 뷰 (TableViewWidget)

### 6.1.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `TableViewWidget` (QWidget 확장) |
| 테이블 위젯 | `QTableView` |
| 데이터 모델 | `TableDataModel` (QAbstractTableModel 확장) |
| ViewModel | `TableViewModel` |

### 6.1.2 레이아웃 구조

```
┌──────────────────────────────────────────────────────────────────────┐
│  Array: Velocity | Rows: 1,234,567                [Export to CSV]    │
├──────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────┐   │
│ │  Point ID  │  X        │  Y        │  Z        │  Magnitude  ││   │
│ ├────────────┼───────────┼───────────┼───────────┼─────────────┼┤   │
│ │     0      │  0.12345  │  0.00000  │  1.23456  │   1.24567   ││   │
│ │     1      │ -0.98765  │  2.34567  │  0.00000  │   2.52837   ││   │
│ │     2      │  1.11111  │ -1.11111  │  1.11111  │   1.92450   ││   │
│ │    ...     │    ...    │    ...    │    ...    │     ...     ││   │
│ └────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.1.3 Info Bar 구성

| 요소 | 위젯 | 내용 |
|------|------|------|
| 정보 라벨 | `QLabel` | "Array: {array_name} \| Rows: {row_count:,}" |
| 내보내기 버튼 | `QPushButton` | "Export to CSV" |

### 6.1.4 테이블 설정

```python
self._table = QTableView()
self._table.setAlternatingRowColors(True)      # 줄무늬 색상
self._table.setSelectionBehavior(QTableView.SelectRows)  # 행 선택
self._table.setSelectionMode(QTableView.ExtendedSelection)  # 다중 선택
self._table.setSortingEnabled(True)            # 정렬 가능

# 컬럼 리사이즈 모드
self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
self._table.horizontalHeader().setStretchLastSection(True)
```

### 6.1.5 우클릭 컨텍스트 메뉴

```
┌──────────────────┐
│ Export to CSV... │
└──────────────────┘
```

### 6.1.6 CSV 내보내기

```python
def _on_export_clicked(self):
    file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Export Table Data",
        "",
        "CSV Files (*.csv);;All Files (*)"
    )
    
    if file_path:
        if not file_path.endswith('.csv'):
            file_path += '.csv'
        
        success = self._viewmodel.export_to_csv(file_path)
        # 성공/실패 메시지 박스 표시
```

### 6.1.7 TableViewModel

```python
class TableViewModel(QObject):
    data_updated = Signal()   # 데이터 업데이트 시그널
    
    def set_data_source(self, item_id: str, array_type: str) -> bool:
        """
        파이프라인 아이템의 데이터를 테이블 소스로 설정
        
        Args:
            item_id: 파이프라인 아이템 ID
            array_type: "POINT" 또는 "CELL"
        
        Returns:
            성공 여부
        """
        
    def get_column_headers(self) -> List[str]:
        """컬럼 헤더 반환 (Point ID, 배열별 컴포넌트)"""
        
    def get_table_data(self) -> np.ndarray:
        """테이블 데이터 (NumPy 배열)"""
        
    def get_row_count(self) -> int:
        """행 개수"""
        
    def export_to_csv(self, file_path: str) -> bool:
        """CSV 파일로 내보내기"""
        
    def refresh_data(self):
        """데이터 새로고침 (시계열 변경 시)"""
        
    def set_visibility(self, visible: bool):
        """가시성 설정 (UI 활성화/비활성화)"""
```

### 6.1.8 TableDataModel (성능 최적화)

```python
class TableDataModel(QAbstractTableModel):
    """
    대용량 데이터를 위한 최적화된 테이블 모델
    - 가상화: 필요한 데이터만 로드
    - NumPy 배열 직접 참조
    - 포맷팅은 표시 시에만 수행
    """
    
    def __init__(self):
        self._data: np.ndarray = None
        self._headers: List[str] = []
    
    def set_data(self, data: np.ndarray, headers: List[str]):
        """데이터 설정 (전체 리셋)"""
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self.endResetModel()
    
    def rowCount(self, parent=None) -> int:
        return len(self._data) if self._data is not None else 0
    
    def columnCount(self, parent=None) -> int:
        return len(self._headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            row, col = index.row(), index.column()
            value = self._data[row, col]
            # 숫자 포맷팅 (표시 시에만)
            if isinstance(value, (int, np.integer)):
                return str(int(value))
            else:
                return f"{value:.6g}"
        return None
```

---

## 6.2 그래프 뷰 (GraphViewWidget)

### 6.2.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `GraphViewWidget` (QWidget 확장) |
| 차트 라이브러리 | Matplotlib |
| 캔버스 | `FigureCanvasQTAgg` |
| 툴바 | `NavigationToolbar2QT` |
| ViewModel | `GraphViewModel` |

### 6.2.2 레이아웃 구조

```
┌──────────────────────────────────────────────────────────────────────┐
│  Type: Line | Sources: 3                          [Export to Image]  │
├──────────────────────────────────────────────────────────────────────┤
│  [🔍] [🏠] [⬅️] [➡️] [📏] [💾]   ← Matplotlib 내비게이션 툴바        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│        ▲                                                             │
│        │                    ●──●                                     │
│        │              ●──●      ╲                                    │
│   Y    │         ●──●            ╲──●                                │
│   axis │    ●──●                     ╲──●                            │
│        │                                                             │
│        └────────────────────────────────────────▶                    │
│                        X axis                                        │
│                                                                      │
│                    [Legend]                                          │
│                    ─── Source 1                                      │
│                    ─── Source 2                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2.3 Info Bar 구성

| 요소 | 위젯 | 내용 |
|------|------|------|
| 정보 라벨 | `QLabel` | "Type: {graph_type} \| Sources: {count}" |
| 내보내기 버튼 | `QPushButton` | "Export to Image" |

### 6.2.4 Matplotlib 내비게이션 툴바

| 아이콘 | 기능 |
|--------|------|
| 🔍 Zoom | 영역 선택 줌 |
| 🏠 Home | 원래 뷰 복원 |
| ⬅️ Back | 이전 뷰 |
| ➡️ Forward | 다음 뷰 |
| 📏 Pan | 드래그로 이동 |
| 💾 Save | 이미지 저장 |

### 6.2.5 그래프 타입

```python
GRAPH_TYPES = [
    "line",        # 선 그래프
    "scatter",     # 산점도
    "bar",         # 막대 그래프
    "histogram",   # 히스토그램
]
```

### 6.2.6 이미지 내보내기

```python
def _on_export_clicked(self):
    file_path, selected_filter = QFileDialog.getSaveFileName(
        self,
        "Export Graph",
        "",
        "PNG Image (*.png);;"
        "JPEG Image (*.jpg);;"
        "SVG Vector (*.svg);;"
        "PDF Document (*.pdf)"
    )
    
    if file_path:
        success = self._viewmodel.export_to_image(file_path, dpi=150)
```

### 6.2.7 GraphViewModel

```python
class GraphViewModel(QObject):
    plot_config_updated = Signal()   # 그래프 설정 변경 시그널
    
    def set_graph_type(self, graph_type: str):
        """그래프 타입 설정 (line, scatter, bar, histogram)"""
        
    def set_data_source(self, item_id: str, x_array: str, 
                        y_array: str, array_type: str) -> bool:
        """
        단일 데이터 소스 설정
        
        Args:
            item_id: 파이프라인 아이템 ID
            x_array: X축 배열 이름 (또는 "index"/"Point ID")
            y_array: Y축 배열 이름
            array_type: "POINT" 또는 "CELL"
        """
        
    def add_data_source(self, item_id: str):
        """다중 소스 모드에서 소스 추가"""
        
    def remove_data_source(self, item_id: str):
        """데이터 소스 제거"""
        
    def _render_plot(self, ax):
        """
        Matplotlib Axes에 그래프 렌더링
        - 각 소스별로 선/점 그리기
        - 범례, 축 라벨 설정
        """
        
    def export_to_image(self, file_path: str, dpi: int = 150) -> bool:
        """이미지 파일로 내보내기"""
        
    def refresh_data(self):
        """데이터 새로고침"""
```

### 6.2.8 다중 소스 지원

```python
class GraphViewModel:
    def __init__(self):
        self._data_sources: Dict[str, SourceConfig] = {}
        # {item_id: {x_array, y_array, array_type, color, label}}
    
    def _render_plot(self, ax):
        for item_id, config in self._data_sources.items():
            item = get_pipeline_item(item_id)
            
            # 숨김 아이템은 건너뛰기
            if not item.visible:
                continue
            
            x_data, y_data = self._get_data(item, config)
            
            if self._graph_type == "line":
                ax.plot(x_data, y_data, label=config.label, 
                        color=config.color)
            elif self._graph_type == "scatter":
                ax.scatter(x_data, y_data, label=config.label,
                           color=config.color, s=10)
            # ...
        
        ax.legend()
        ax.set_xlabel(self._x_label)
        ax.set_ylabel(self._y_label)
```

---

## 6.3 Properties Panel - 테이블/그래프용

### 6.3.1 TablePropertiesWidget

```
┌──────────────────────────────────────────┐
│  [Table Properties]                      │
│  ┌────────────────────────────────────┐  │
│  │  Data Source                       │  │
│  │  Array Type: [▼ POINT / CELL]      │  │
│  │                                    │  │
│  │  Display Settings                  │  │
│  │  Precision: [___] (소수점 자릿수)  │  │
│  │  Page Size: [___] (가상화 단위)    │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 6.3.2 GraphPropertiesWidget

```
┌──────────────────────────────────────────┐
│  [Graph Properties]                      │
│  ┌────────────────────────────────────┐  │
│  │  Graph Type                        │  │
│  │  Type: [▼ Line/Scatter/Bar/Hist]   │  │
│  │                                    │  │
│  │  Data Mapping                      │  │
│  │  X Axis: [▼ Array Combo]           │  │
│  │  Y Axis: [▼ Array Combo]           │  │
│  │                                    │  │
│  │  Appearance                        │  │
│  │  [✓] Show Legend                   │  │
│  │  [✓] Show Grid                     │  │
│  │  Title: [________________]         │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘
```

---

## 6.4 뷰 간 데이터 동기화

### 6.4.1 가시성 동기화

```python
def _on_visibility_changed(self, item_id: str, visible: bool):
    """
    Pipeline Browser에서 가시성 변경 시 모든 뷰 업데이트
    """
    # VTK 뷰: 액터 가시성
    item = self._pipeline_vm.items.get(item_id)
    if item and item.actor:
        self._vtk_vm.set_actor_visibility(item.actor, visible)
    
    # Table 뷰: 활성화/비활성화
    for tab_id, meta in self._tabbed_view.get_all_tabs().items():
        widget = self._tabbed_view.get_tab_widget_by_id(tab_id)
        
        if meta['type'] == 'table':
            if widget.viewmodel.source_item_id == item_id:
                widget.viewmodel.set_visibility(visible)
        
        elif meta['type'] == 'graph':
            if visible:
                widget.viewmodel.add_data_source(item_id)
            # 숨김 시에도 설정 유지 (렌더링만 건너뜀)
            widget.viewmodel.plot_config_updated.emit()
```

### 6.4.2 시계열 동기화

```python
def _on_time_step_changed(self, item_id: str, time_index: int):
    """
    시간 스텝 변경 시 활성 탭만 업데이트 (성능 최적화)
    """
    if self._active_tab_type == TabType.VTK:
        if item.visible:
            self._vtk_vm.request_render()
    
    elif self._active_tab_type == TabType.TABLE:
        widget = self._tabbed_view.get_active_tab_widget()
        if widget.viewmodel.source_item_id == item_id:
            widget.viewmodel.refresh_data()
    
    elif self._active_tab_type == TabType.GRAPH:
        widget = self._tabbed_view.get_active_tab_widget()
        if item_id in widget.viewmodel._data_sources:
            widget.viewmodel.refresh_data()
```

---

*다음: [07-right-sidebar-chat.md](./07-right-sidebar-chat.md) - 우측 채팅 패널 상세*
