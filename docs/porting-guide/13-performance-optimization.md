# 13. 성능 최적화 전략

## 13.1 대용량 데이터 처리

### 13.1.1 메모리 관리 원칙

1. **데이터 복사 최소화**: VTK 파이프라인에서 데이터 참조 유지
2. **지연 로딩**: 필요 시에만 데이터 로드
3. **가상화**: 테이블 뷰에서 화면에 보이는 데이터만 렌더링

### 13.1.2 VTK 데이터 참조

```python
# 나쁜 예: 데이터 복사
data_copy = vtk.vtkUnstructuredGrid()
data_copy.DeepCopy(original_data)  # 전체 메모리 복제

# 좋은 예: 참조 유지
data_ref = original_data  # 참조만 유지
# 또는
shallow_copy = vtk.vtkUnstructuredGrid()
shallow_copy.ShallowCopy(original_data)  # 구조만 복사, 데이터 공유
```

### 13.1.3 NumPy 변환 최적화

```python
# VTK 배열 → NumPy 배열 (Zero-copy)
from vtk.util.numpy_support import vtk_to_numpy

vtk_array = data.GetPointData().GetArray("Pressure")
numpy_array = vtk_to_numpy(vtk_array)  # 메모리 공유

# 주의: VTK 데이터가 살아있어야 함
# numpy_array가 VTK 메모리를 직접 참조
```

---

## 13.2 Table View 최적화

### 13.2.1 가상화 (Virtualization)

```python
class TableDataModel(QAbstractTableModel):
    """
    QTableView는 내부적으로 가상화 지원
    - 화면에 보이는 행만 data() 호출
    - 수백만 행도 효율적으로 처리
    """
    
    def __init__(self):
        self._data: np.ndarray = None  # 전체 데이터 (NumPy)
        self._row_count = 0
    
    def rowCount(self, parent=None):
        return self._row_count
    
    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        
        # 인덱스로 직접 접근 (O(1))
        row, col = index.row(), index.column()
        return self._format_value(self._data[row, col])
```

### 13.2.2 포맷팅 지연

```python
def _format_value(self, value):
    """
    포맷팅은 표시 시에만 수행
    - 저장 시: raw 값 유지
    - 표시 시: 문자열 변환
    """
    if isinstance(value, (int, np.integer)):
        return str(int(value))
    elif isinstance(value, float):
        return f"{value:.6g}"
    return str(value)
```

### 13.2.3 정렬 최적화

```python
def sort(self, column, order):
    """
    NumPy 배열 정렬 (매우 빠름)
    """
    self.layoutAboutToBeChanged.emit()
    
    indices = np.argsort(self._data[:, column])
    if order == Qt.DescendingOrder:
        indices = indices[::-1]
    
    self._data = self._data[indices]
    
    self.layoutChanged.emit()
```

---

## 13.3 VTK 렌더링 최적화

### 13.3.1 LOD (Level of Detail)

```python
# 대용량 메시에 대해 LOD 사용
lod_actor = vtk.vtkLODActor()
lod_actor.SetMapper(mapper)
lod_actor.SetNumberOfCloudPoints(100000)  # 간소화 포인트 수
```

### 13.3.2 렌더 요청 통합

```python
class VTKViewModel:
    def __init__(self):
        self._render_pending = False
        self._render_timer = QTimer()
        self._render_timer.timeout.connect(self._do_render)
        self._render_timer.setSingleShot(True)
    
    def request_render(self):
        """
        여러 변경사항을 하나의 렌더로 통합
        """
        if not self._render_pending:
            self._render_pending = True
            self._render_timer.start(16)  # ~60fps
    
    def _do_render(self):
        self._render_pending = False
        self.render_requested.emit()
```

### 13.3.3 Culling 활용

```python
# 뷰 프러스텀 외부 객체 제외
renderer.UseFXAAOn()  # 안티앨리어싱
renderer.SetUseDepthPeeling(1)  # 투명도 처리
renderer.SetMaximumNumberOfPeels(4)
```

---

## 13.4 시계열 데이터 최적화

### 13.4.1 현재 프레임만 로드

```python
class TimeSeriesItem:
    def __init__(self, file_paths: List[str]):
        self._file_paths = file_paths
        self._current_index = 0
        self._current_data = None  # 현재 프레임 데이터만 유지
    
    def set_time_index(self, index: int):
        if index == self._current_index:
            return
        
        # 이전 데이터 해제 (garbage collection)
        self._current_data = None
        
        # 새 데이터 로드
        self._current_index = index
        self._current_data = self._load_file(self._file_paths[index])
```

### 13.4.2 프리페칭 (선택적)

```python
class TimeSeriesManager:
    def __init__(self):
        self._prefetch_enabled = False
        self._cache_size = 3  # 현재 + 앞뒤 1프레임
    
    def _prefetch_frames(self, current_index):
        """백그라운드에서 인접 프레임 미리 로드"""
        if not self._prefetch_enabled:
            return
        
        # 비동기 로드 (별도 스레드)
        for offset in [-1, 1]:
            target_index = current_index + offset
            if 0 <= target_index < self._max_index:
                self._cache_frame_async(target_index)
```

### 13.4.3 활성 탭만 업데이트

```python
def _on_time_step_changed(self, item_id: str, time_index: int):
    """
    시간 변경 시 활성 탭만 업데이트
    - 비활성 탭은 활성화 시 갱신
    """
    if self._active_tab_type == TabType.VTK:
        if item.visible:
            self._vtk_vm.request_render()
    
    elif self._active_tab_type == TabType.TABLE:
        widget = self._tabbed_view.get_active_tab_widget()
        if widget.viewmodel.source_item_id == item_id:
            widget.viewmodel.refresh_data()
    
    # GRAPH 탭도 유사하게 처리
```

---

## 13.5 UI 반응성

### 13.5.1 비동기 작업

```python
class AgentWorker(QThread):
    """AI 처리를 별도 스레드에서 실행"""
    
    def run(self):
        # 긴 작업은 메인 스레드 블로킹 없이 실행
        result = self._agent.process(self._input)
        self.finished.emit(result)
```

### 13.5.2 프로그레스 피드백

```python
# 긴 작업 중 UI 업데이트
def load_large_file(self, path):
    self.progress_updated.emit(0, "읽는 중...")
    
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(path)
    
    # 진행률 콜백 설정
    def progress_callback(obj, event):
        progress = int(obj.GetProgress() * 100)
        self.progress_updated.emit(progress, f"로딩: {progress}%")
    
    reader.AddObserver("ProgressEvent", progress_callback)
    reader.Update()
    
    self.progress_updated.emit(100, "완료")
```

### 13.5.3 UI 재활성화 지연

```python
UI_REENABLE_DELAY_MS = 100  # 100ms 지연

def _enable_ui_interaction(self):
    """
    즉시 재활성화하면 깜빡임 발생
    짧은 지연으로 안정화
    """
    QTimer.singleShot(UI_REENABLE_DELAY_MS, self._perform_ui_reenable)
```

---

## 13.6 메모리 최적화

### 13.6.1 액터 정리

```python
def _on_item_removed(self, item_id: str):
    item = self._items.get(item_id)
    if item:
        # VTK 액터 제거
        if item.actor:
            self._renderer.RemoveActor(item.actor)
            item.actor = None
        
        # VTK 데이터 참조 해제
        item.vtk_data = None
        
        # 딕셔너리에서 제거
        del self._items[item_id]
    
    # garbage collection 힌트
    import gc
    gc.collect()
```

### 13.6.2 시그널 연결 해제

```python
def _disconnect_vtk_widget_signals(self, widget):
    """
    탭 닫기 시 시그널 연결 해제
    - 메모리 누수 방지
    - 댕글링 참조 방지
    """
    try:
        self._vtk_vm.render_requested.disconnect(widget.render)
        self._vtk_vm.actor_added.disconnect(widget.add_actor)
        # ... 다른 시그널들
    except (RuntimeError, TypeError):
        # 이미 연결 해제됨
        pass
```

### 13.6.3 위젯 정리

```python
def _clear_layout(self, layout):
    """레이아웃의 모든 위젯 안전하게 제거"""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.deleteLater()  # Qt 이벤트 루프에서 안전하게 삭제
```

---

## 13.7 캐싱 전략

### 13.7.1 필터 인스턴스 캐싱

```python
class PipelineViewModel:
    def __init__(self):
        self._filters: Dict[str, FilterBase] = {}
    
    def get_filter(self, filter_type: str) -> FilterBase:
        if filter_type not in self._filters:
            filter_class = filters.get_filter_class(filter_type)
            self._filters[filter_type] = filter_class(self._render_service)
        return self._filters[filter_type]
```

### 13.7.2 Lookup Table 재사용

```python
# 동일한 배열에 대해 LUT 재사용
_lut_cache: Dict[str, vtkLookupTable] = {}

def get_lookup_table(array_name: str, range_min: float, range_max: float):
    cache_key = f"{array_name}_{range_min}_{range_max}"
    
    if cache_key not in _lut_cache:
        lut = vtk.vtkLookupTable()
        lut.SetRange(range_min, range_max)
        lut.Build()
        _lut_cache[cache_key] = lut
    
    return _lut_cache[cache_key]
```

---

## 13.8 성능 측정

### 13.8.1 로깅 기반 측정

```python
import time
from utils.logger import get_logger

logger = get_logger("Performance")

def measure_time(func):
    """데코레이터로 실행 시간 측정"""
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.debug(f"{func.__name__}: {elapsed:.3f}s")
        return result
    return wrapper
```

### 13.8.2 VTK 렌더 시간

```python
def _on_render_end(self):
    """렌더링 완료 시간 측정"""
    render_time = self._render_window.GetLastRenderTimeInSeconds()
    if render_time > 0.1:  # 100ms 이상이면 경고
        logger.warning(f"Slow render: {render_time:.3f}s")
```

---

## 13.9 권장 사항

### 13.9.1 데이터 크기별 전략

| 데이터 크기 | 권장 전략 |
|------------|----------|
| < 100K 포인트 | 표준 처리 |
| 100K ~ 1M | LOD 액터 사용 |
| 1M ~ 10M | 프로그레시브 로딩, 캐싱 |
| > 10M | 서버사이드 렌더링 고려 |

### 13.9.2 애니메이션 프레임 수

| 프레임 수 | 권장 전략 |
|----------|----------|
| < 100 | 표준 처리 |
| 100 ~ 1000 | 현재 프레임만 로드 |
| > 1000 | 프리페칭 + 프레임 스킵 |

### 13.9.3 테이블 행 수

| 행 수 | 권장 전략 |
|------|----------|
| < 10K | 표준 처리 |
| 10K ~ 100K | 가상화 (Qt 기본) |
| 100K ~ 1M | 페이지네이션 고려 |
| > 1M | 샘플링 또는 집계 |

---

*다음: [14-constants-defaults.md](./14-constants-defaults.md) - 상수 및 기본값 정의*
