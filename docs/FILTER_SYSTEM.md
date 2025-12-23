# 필터 시스템 가이드

## 개요

플러그인 방식의 필터 시스템으로, 새 필터를 추가할 때 최소한의 코드 변경만 필요합니다.

## 새 필터 추가하기

### 1. 필터 클래스 생성

`src/python/filters/` 디렉토리에 새 파일 생성 (예: `clip_filter.py`):

```python
from typing import Any, Tuple, Optional
from filters.filter_base import FilterBase
from PySide6.QtWidgets import QWidget

class ClipFilter(FilterBase):
    @property
    def filter_type(self) -> str:
        return "clip_filter"
    
    @property
    def display_name(self) -> str:
        return "Clip"
    
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        # 필터 로직 구현
        # VTK 필터를 사용하여 data를 처리하고 (actor, output_data) 반환
        pass
    
    def create_default_params(self) -> dict:
        # 기본 파라미터 반환
        return {}
    
    def create_params_widget(self, parent: QWidget, item=None, parent_bounds=None):
        # 파라미터 편집 UI 위젯 생성
        # None 반환 시 파라미터 UI 없음
        pass
```

### 2. 필터 등록

`src/python/filters/__init__.py`에 등록:

```python
from filters.clip_filter import ClipFilter

register_filter("clip_filter", ClipFilter)
```

### 3. 메뉴에 추가 (선택사항)

`src/python/views/main_window.py`의 `_setup_menu_bar()`에 추가:

```python
clip_action = QAction("Clip", self)
clip_action.triggered.connect(lambda: self._on_filter_action("clip_filter"))
filters_menu.addAction(clip_action)
```

## 기존 코드와의 비교

### 기존 방식 (의존성 많음)
- `filter_params.py` - 파라미터 클래스 추가
- `vtk_render_service.py` - apply 메서드 추가
- `pipeline_viewmodel.py` - apply, update, commit 분기 추가
- `main_window.py` - 메뉴 및 핸들러 추가
- `properties_panel.py` - UI 섹션 추가

**총 5개 파일 수정 필요**

### 새 방식 (의존성 최소화)
- `filters/new_filter.py` - 필터 클래스 생성
- `filters/__init__.py` - 등록만 추가

**총 2개 파일만 수정 (또는 1개 파일 + 1줄 등록)**

## 필터 시스템 구조

```
filters/
├── __init__.py          # 필터 레지스트리
├── filter_base.py       # 추상 베이스 클래스
├── slice_filter.py      # Slice 필터 구현
└── clip_filter.py       # Clip 필터 구현 (예시)
```

## 장점

1. **낮은 결합도**: 각 필터가 독립적인 모듈
2. **쉬운 확장**: 새 필터 추가가 매우 간단
3. **유지보수 용이**: 필터별 코드가 한 곳에 집중
4. **테스트 용이**: 각 필터를 독립적으로 테스트 가능

