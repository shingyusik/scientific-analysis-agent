# 필터 시스템 가이드

## 개요

플러그인 방식의 필터 시스템으로, 새 필터를 추가할 때 **한 파일만 작성**하면 됩니다.

## 새 필터 추가하기

### 1. 필터 클래스 생성

`src/python/filters/` 디렉토리에 새 파일 생성 (예: `my_filter.py`):

```python
from dataclasses import dataclass, field
from typing import Any, Tuple, Optional, List
from filters.filter_base import FilterBase
from models.pipeline_item import PipelineItem
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox
import vtk


@dataclass
class MyFilterParams:
    """Parameters for my filter."""
    value: float = 0.5
    
    def to_dict(self) -> dict:
        return {"value": self.value}
    
    @classmethod
    def from_dict(cls, data: dict) -> "MyFilterParams":
        return cls(value=data.get("value", 0.5))


class MyFilter(FilterBase):
    @property
    def filter_type(self) -> str:
        return "my_filter"
    
    @property
    def display_name(self) -> str:
        return "My Filter"
    
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        """Apply filter using VTK."""
        my_params = MyFilterParams.from_dict(params)
        
        # VTK 필터 로직
        vtk_filter = vtk.vtkSomeFilter()
        vtk_filter.SetInputData(data)
        vtk_filter.SetValue(my_params.value)
        vtk_filter.Update()
        
        output_data = vtk_filter.GetOutput()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(output_data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        return actor, output_data
    
    def create_default_params(self) -> dict:
        return MyFilterParams().to_dict()
    
    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None) -> Optional[QWidget]:
        """Create parameter editing UI."""
        # UI 위젯 생성 및 반환
        # None 반환 시 파라미터 UI 없음
        pass
```

### 2. 필터 등록

`src/python/filters/__init__.py`에 한 줄 추가:

```python
from filters.my_filter import MyFilter
register_filter("my_filter", MyFilter)
```

**끝!** 메뉴는 자동으로 추가됩니다.

## 필터 구조

각 필터 파일은 다음을 포함:

| 구성 요소 | 설명 |
|----------|------|
| `*Params` | 파라미터 데이터 클래스 |
| `*Filter` | 필터 구현 클래스 |
| VTK 로직 | `apply_filter()` 내에서 직접 처리 |
| UI 위젯 | `create_params_widget()`에서 생성 |

```
filters/
├── __init__.py          # 필터 레지스트리
├── filter_base.py       # 추상 베이스 클래스
├── slice_filter.py      # SliceParams + SliceFilter
└── clip_filter.py       # ClipParams + ClipFilter
```

## 자동으로 처리되는 것들

- ✅ **Filters 메뉴**: 등록된 필터가 자동으로 메뉴에 추가
- ✅ **Properties 패널**: 필터 선택 시 UI 위젯 자동 로드
- ✅ **Apply 버튼**: 공통 처리
- ✅ **파이프라인 관리**: PipelineViewModel이 자동 처리

## 기존 방식 vs 새 방식

### 기존 방식 (5개 파일 수정)
- `models/filter_params.py` - Params 클래스
- `services/vtk_render_service.py` - VTK 로직
- `viewmodels/pipeline_viewmodel.py` - apply/update/commit
- `views/main_window.py` - 메뉴 및 핸들러
- `views/properties_panel.py` - UI 섹션

### 새 방식 (1개 파일 + 1줄)
- `filters/my_filter.py` - 모든 것 포함
- `filters/__init__.py` - `register_filter()` 1줄

## 장점

1. **자기 완결적**: 필터 관련 모든 코드가 한 파일에
2. **낮은 결합도**: 다른 파일 수정 불필요
3. **쉬운 확장**: 파일 하나 + 등록 한 줄
4. **유지보수 용이**: 필터별 독립적 관리
5. **테스트 용이**: 각 필터 독립 테스트 가능
