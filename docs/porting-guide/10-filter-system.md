# 10. 필터 시스템 상세

## 10.1 필터 아키텍처 개요

### 10.1.1 클래스 다이어그램

```
                    FilterBase (ABC)
                         │
         ┌───────────────┼───────────────┬───────────────┐
         │               │               │               │
    SliceFilter    ClipFilter    ThresholdFilter  CalculatorFilter
```

### 10.1.2 필터 레지스트리

```python
# filters/__init__.py
FILTER_REGISTRY = {
    "slice_filter": SliceFilter,
    "clip_filter": ClipFilter,
    "threshold_filter": ThresholdFilter,
    "calculator_filter": CalculatorFilter,
}

def get_filter_class(filter_type: str) -> type:
    return FILTER_REGISTRY.get(filter_type)

def get_available_filters() -> List[Tuple[str, str]]:
    """(filter_type, display_name) 쌍 반환"""
    return [
        ("slice_filter", "Slice"),
        ("clip_filter", "Clip"),
        ("threshold_filter", "Threshold"),
        ("calculator_filter", "Calculator"),
    ]
```

## 10.2 FilterBase 추상 클래스

### 10.2.1 필수 추상 메서드

```python
class FilterBase(ABC):
    def __init__(self, render_service: VTKRenderService):
        self._render_service = render_service
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """표시 이름 (예: 'Slice')"""
        pass
    
    @property
    @abstractmethod
    def filter_type(self) -> str:
        """필터 타입 식별자 (예: 'slice_filter')"""
        pass
    
    @abstractmethod
    def apply_filter(self, data, params: dict) -> Tuple[Any, Any]:
        """
        필터 적용
        Returns: (actor, output_data)
        """
        pass
    
    @abstractmethod
    def create_default_params(self) -> dict:
        """기본 파라미터 생성"""
        pass
    
    @abstractmethod
    def create_params_widget(self, parent, item, parent_bounds, 
                             on_params_changed) -> QWidget:
        """파라미터 편집 위젯 생성"""
        pass
```

### 10.2.2 선택적 메서드

```python
class FilterBase:
    @property
    def apply_immediately(self) -> bool:
        """
        True: 필터 생성 즉시 적용
        False: Apply 버튼 클릭 후 적용 (Threshold)
        """
        return True
    
    @property
    def params_class(self) -> Optional[type]:
        """파라미터 데이터클래스 (있으면)"""
        return None
    
    def validate_params(self, params: dict) -> Tuple[bool, str]:
        """파라미터 유효성 검사"""
        return True, ""
    
    def get_plane_preview_params(self, params: dict):
        """평면 미리보기 파라미터 (Slice, Clip용)"""
        return None
```

---

## 10.3 Slice Filter

### 10.3.1 파라미터

```python
@dataclass
class SliceParams:
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    normal: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    offsets: List[float] = field(default_factory=lambda: [0.0])
    show_preview: bool = True
```

### 10.3.2 UI 위젯

```
┌──────────────────────────────────────────────────┐
│  [Filter Parameters: Slice]                      │
├──────────────────────────────────────────────────┤
│                                                  │
│  Origin                                          │
│  X: [____0.0000____]  [Reset]                    │
│  Y: [____0.0000____]                             │
│  Z: [____0.0000____]                             │
│                                                  │
│  Normal                                          │
│  X: [____1.0000____]  [Reset]                    │
│  Y: [____0.0000____]                             │
│  Z: [____0.0000____]                             │
│                                                  │
│  Offsets                                         │
│  ┌──────────────────────────────────────────┐    │
│  │  0.0                                     │    │
│  │  0.5                                     │    │
│  │  1.0                                     │    │
│  └──────────────────────────────────────────┘    │
│  [Add] [Remove] [Generate Series] [Clear]        │
│                                                  │
│  [✓] Show Plane Preview                          │
│                                                  │
├──────────────────────────────────────────────────┤
│              [Apply]                             │
└──────────────────────────────────────────────────┘
```

### 10.3.3 동작 원리

```python
def apply_filter(self, data, params):
    origin = params.get("origin", [0, 0, 0])
    normal = params.get("normal", [1, 0, 0])
    offsets = params.get("offsets", [0.0])
    
    if len(offsets) == 1:
        # 단일 슬라이스
        output = self._apply_single_slice(data, origin, normal)
    else:
        # 다중 슬라이스 (Append)
        append_filter = vtk.vtkAppendPolyData()
        for offset in offsets:
            offset_origin = [o + offset * n for o, n in zip(origin, normal)]
            slice_output = self._apply_single_slice(data, offset_origin, normal)
            append_filter.AddInputData(slice_output)
        append_filter.Update()
        output = append_filter.GetOutput()
    
    actor = self._render_service.create_actor_from_polydata(output)
    return actor, output
```

### 10.3.4 Origin/Normal 기본값

```python
def create_default_params(self):
    # 데이터 중심점을 origin으로, X축을 normal로
    return {
        "origin": [0.0, 0.0, 0.0],
        "normal": [1.0, 0.0, 0.0],
        "offsets": [0.0],
        "show_preview": True,
    }
```

### 10.3.5 Reset 버튼 동작

```python
def _reset_origin(self, spins, item):
    """데이터 중심점으로 리셋"""
    if item and item.vtk_data:
        bounds = item.vtk_data.GetBounds()
        center = [
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2,
        ]
        for i, spin in enumerate(spins):
            spin.setValue(center[i])
```

---

## 10.4 Clip Filter

### 10.4.1 파라미터

```python
@dataclass
class ClipParams:
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    normal: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    show_preview: bool = True
```

### 10.4.2 UI 위젯

```
┌──────────────────────────────────────────────────┐
│  [Filter Parameters: Clip]                       │
├──────────────────────────────────────────────────┤
│                                                  │
│  Origin                                          │
│  X: [____0.0000____]  [Reset]                    │
│  Y: [____0.0000____]                             │
│  Z: [____0.0000____]                             │
│                                                  │
│  Normal (clip direction)                         │
│  X: [____1.0000____]  [Reset]                    │
│  Y: [____0.0000____]                             │
│  Z: [____0.0000____]                             │
│                                                  │
│  [✓] Show Plane Preview                          │
│                                                  │
├──────────────────────────────────────────────────┤
│              [Apply]                             │
└──────────────────────────────────────────────────┘
```

### 10.4.3 동작 원리

```python
def apply_filter(self, data, params):
    origin = params.get("origin", [0, 0, 0])
    normal = params.get("normal", [1, 0, 0])
    
    # 평면 생성
    plane = vtk.vtkPlane()
    plane.SetOrigin(*origin)
    plane.SetNormal(*normal)
    
    # 클리핑
    clipper = vtk.vtkClipDataSet()
    clipper.SetInputData(data)
    clipper.SetClipFunction(plane)
    clipper.Update()
    
    output = clipper.GetOutput()
    actor = self._render_service.create_actor_from_data(output)
    return actor, output
```

---

## 10.5 Threshold Filter

### 10.5.1 파라미터

```python
@dataclass
class ThresholdParams:
    array_name: str = ""
    component: int = 0
    lower_bound: float = 0.0
    upper_bound: float = 1.0
    method: str = "between"  # "between", "above", "below"
    attribute_type: str = "POINT"  # "POINT" or "CELL"
```

### 10.5.2 UI 위젯

```
┌──────────────────────────────────────────────────┐
│  [Filter Parameters: Threshold]                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Array: [▼ Pressure              ▼]              │
│                                                  │
│  Component: ( ) X  ( ) Y  ( ) Z  (•) Magnitude   │
│                                                  │
│  Method                                          │
│  ( ) Above Lower:  [____0.0____]                 │
│  ( ) Below Upper:  [____1.0____]                 │
│  (•) Between                                     │
│                                                  │
│  Range                                           │
│  Lower: [____0.0____]                            │
│  Upper: [____1.0____]                            │
│                                                  │
├──────────────────────────────────────────────────┤
│              [Apply]                             │
└──────────────────────────────────────────────────┘
```

### 10.5.3 특수 동작

```python
@property
def apply_immediately(self):
    return False  # Apply 버튼 클릭 필요
```

### 10.5.4 동작 원리

```python
def apply_filter(self, data, params):
    threshold = vtk.vtkThreshold()
    threshold.SetInputData(data)
    
    # 배열 설정
    if params["attribute_type"] == "POINT":
        threshold.SetInputArrayToProcess(0, 0, 0, 
            vtk.vtkDataObject.FIELD_ASSOCIATION_POINTS,
            params["array_name"])
    else:
        threshold.SetInputArrayToProcess(0, 0, 0,
            vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS,
            params["array_name"])
    
    # 임계값 방법
    if params["method"] == "between":
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)
        threshold.SetLowerThreshold(params["lower_bound"])
        threshold.SetUpperThreshold(params["upper_bound"])
    elif params["method"] == "above":
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_LOWER)
        threshold.SetLowerThreshold(params["lower_bound"])
    elif params["method"] == "below":
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_UPPER)
        threshold.SetUpperThreshold(params["upper_bound"])
    
    threshold.Update()
    output = threshold.GetOutput()
    actor = self._render_service.create_actor_from_data(output)
    return actor, output
```

---

## 10.6 Calculator Filter

### 10.6.1 파라미터

```python
@dataclass
class CalculatorParams:
    expression: str = ""
    result_array_name: str = "Result"
    attribute_type: str = "POINT"  # "POINT" or "CELL"
```

### 10.6.2 UI 위젯

```
┌──────────────────────────────────────────────────────────────┐
│  [Filter Parameters: Calculator]                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Expression:                                                 │
│  [________Velocity_X^2 + Velocity_Y^2________________]       │
│  [Clear]                                                     │
│                                                              │
│  Functions:                                                  │
│  [sin] [cos] [tan] [exp] [log] [sqrt] [abs] [pow]           │
│  [+] [-] [*] [/] [(] [)]                                    │
│                                                              │
│  Scalars:     [▼ Pressure     ▼]  [Insert]                  │
│  Vectors:     [▼ Velocity     ▼]  [Insert]                  │
│  Components:  [.X] [.Y] [.Z]                                 │
│                                                              │
│  Result Array Name: [____Result_____]                        │
│                                                              │
│  Attribute Type: [▼ POINT / CELL ▼]                         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│              [Apply]                                         │
└──────────────────────────────────────────────────────────────┘
```

### 10.6.3 함수 버튼

```python
FUNCTION_BUTTONS = [
    ("sin", "sin("),
    ("cos", "cos("),
    ("tan", "tan("),
    ("exp", "exp("),
    ("log", "log("),
    ("sqrt", "sqrt("),
    ("abs", "abs("),
    ("pow", "pow(,)"),
    ("+", "+"),
    ("-", "-"),
    ("*", "*"),
    ("/", "/"),
    ("(", "("),
    (")", ")"),
]
```

### 10.6.4 동작 원리

```python
def apply_filter(self, data, params):
    calculator = vtk.vtkArrayCalculator()
    calculator.SetInputData(data)
    
    # 속성 타입
    if params["attribute_type"] == "POINT":
        calculator.SetAttributeTypeToPointData()
    else:
        calculator.SetAttributeTypeToCellData()
    
    # 배열 변수 등록
    for array_name in self._get_array_names(data, params["attribute_type"]):
        calculator.AddScalarArrayName(array_name)
        # 벡터 배열은 컴포넌트로 분리
        if self._is_vector_array(data, array_name):
            calculator.AddVectorArrayName(array_name)
    
    # 수식 및 결과 설정
    calculator.SetFunction(params["expression"])
    calculator.SetResultArrayName(params["result_array_name"])
    
    calculator.Update()
    output = calculator.GetOutput()
    actor = self._render_service.create_actor_from_data(output)
    return actor, output
```

---

## 10.7 필터 적용 흐름

### 10.7.1 메뉴에서 필터 선택

```
[User clicks Filters → Slice]
         │
         ▼
[MainWindow._on_apply_filter("slice_filter")]
         │
         ▼
[PipelineViewModel.apply_filter("slice_filter", parent_id)]
         │
         ├──▶ 1. 필터 인스턴스 가져오기
         │        filter = self.get_filter("slice_filter")
         │
         ├──▶ 2. 기본 파라미터 생성
         │        params = filter.create_default_params()
         │
         ├──▶ 3. 부모 데이터 경계로 파라미터 조정
         │        params["origin"] = center_of_parent
         │
         ├──▶ 4. 필터 적용 (apply_immediately=True인 경우)
         │        actor, output = filter.apply_filter(parent_data, params)
         │
         ├──▶ 5. PipelineItem 생성
         │        item = PipelineItem(
         │            name="Slice",
         │            item_type="slice_filter",
         │            parent_id=parent_id,
         │            filter_params=params,
         │            actor=actor,
         │            vtk_data=output
         │        )
         │
         └──▶ 6. 시그널 발생
                  self.item_added.emit(item)
```

### 10.7.2 파라미터 변경 시

```
[User changes parameter in Properties Panel]
         │
         ▼
[on_params_changed callback]
         │
         ▼
[PropertiesPanel.filter_params_changed signal]
         │
         ▼
[MainWindow._on_filter_params_changed(item_id, params)]
         │
         ▼
[PipelineViewModel.update_filter_params(item_id, params)]
         │
         ├──▶ item.filter_params = params
         │
         └──▶ (apply_immediately=True인 경우)
                  item.actor 업데이트
                  render 요청
```

### 10.7.3 Apply 버튼 클릭 시

```
[User clicks Apply button]
         │
         ▼
[PropertiesPanel.apply_filter_requested signal(item_id)]
         │
         ▼
[PipelineViewModel.commit_filter(item_id)]
         │
         ├──▶ 1. 현재 파라미터로 필터 재적용
         │        actor, output = filter.apply_filter(parent.vtk_data, item.filter_params)
         │
         ├──▶ 2. 기존 actor 제거 → 새 actor 추가
         │
         ├──▶ 3. item.actor = actor
         │        item.vtk_data = output
         │
         └──▶ 4. item_updated 시그널
```

---

## 10.8 공통 UI 컴포넌트

### 10.8.1 ScientificDoubleSpinBox

```python
class ScientificDoubleSpinBox(QDoubleSpinBox):
    """과학적 표기법 지원 스핀박스"""
    
    def __init__(self):
        super().__init__()
        self.setDecimals(15)
        self.setRange(-1e30, 1e30)
        self.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
    
    def textFromValue(self, value):
        """작은 값은 지수 표기법 사용"""
        if abs(value) < 1e-4 and value != 0:
            return f"{value:.6e}"
        return f"{value:.6g}"
```

### 10.8.2 OffsetListWidget

```python
class OffsetListWidget(QWidget):
    """오프셋 값 리스트 관리 위젯"""
    
    offsets_changed = Signal(list)  # [float, ...]
```

### 10.8.3 UI 상수

```python
RESET_BUTTON_WIDTH = 50
SPINBOX_WIDTH = 100
OFFSET_LIST_MIN_WIDTH = 400
```

---

*다음: [11-interaction-logic.md](./11-interaction-logic.md) - 사용자 상호작용 논리*
