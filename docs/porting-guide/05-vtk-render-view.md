# 5. VTK 렌더 뷰 상세

## 5.1 VTKWidget 개요

### 5.1.1 기본 정보

| 속성 | 값 |
|------|-----|
| 클래스 | `VTKWidget` (QWidget 확장) |
| 핵심 컴포넌트 | `QVTKRenderWindowInteractor` |
| 렌더러 | `vtkRenderer` |
| 인터랙터 스타일 | `vtkInteractorStyleTrackballCamera` |

### 5.1.2 레이아웃 구조

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│                      VTK Render Window                       │
│                                                              │
│  ┌─────────┐                                                 │
│  │ Axes    │                        ┌─────────────────────┐  │
│  │ Widget  │                        │   Scalar Bar        │  │
│  │         │                        │   (범례/컬러바)     │  │
│  │ (좌하단)│                        │   (우측)            │  │
│  └─────────┘                        └─────────────────────┘  │
│                                                              │
│                      [3D 메시 렌더링]                        │
│                                                              │
│                      ┌─────────────────────┐                 │
│                      │ Plane Preview       │                 │
│                      │ (필터 미리보기)     │                 │
│                      └─────────────────────┘                 │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## 5.2 초기화

### 5.2.1 VTKWidget.__init__

```python
def __init__(self):
    # 렌더러 생성
    self._renderer = vtk.vtkRenderer()
    
    # 렌더 윈도우 생성
    self._render_window = vtk.vtkRenderWindow()
    self._render_window.AddRenderer(self._renderer)
    
    # Qt 인터랙터 생성
    self._interactor = QVTKRenderWindowInteractor(self)
    self._interactor.SetRenderWindow(self._render_window)
    
    # 인터랙터 스타일 설정 (트랙볼 카메라)
    style = vtk.vtkInteractorStyleTrackballCamera()
    self._interactor.SetInteractorStyle(style)
    
    # 배경색 설정
    self._renderer.SetBackground(*DEFAULT_BACKGROUND_COLOR)
    
    # 축 위젯 설정
    self._setup_axes()
    
    # 스칼라 바 설정
    self._setup_scalar_bar()
    
    # 평면 미리보기 설정
    self._setup_plane_preview()
    
    # 인터랙터 시작
    self._interactor.Initialize()
    self._interactor.Start()
```

## 5.3 Axes Widget (좌표축 표시)

### 5.3.1 설정

```python
AXES_WIDGET_VIEWPORT = (0.0, 0.0, 0.2, 0.2)  # 좌하단 20%

def _setup_axes(self):
    self._axes_actor = vtk.vtkAxesActor()
    
    self._orientationWidget = vtk.vtkOrientationMarkerWidget()
    self._orientationWidget.SetOrientationMarker(self._axes_actor)
    self._orientationWidget.SetInteractor(self._interactor)
    self._orientationWidget.SetViewport(*AXES_WIDGET_VIEWPORT)
    self._orientationWidget.SetEnabled(1)
    self._orientationWidget.InteractiveOff()  # 드래그 비활성화
```

### 5.3.2 표시 위치

| 뷰포트 파라미터 | 값 | 설명 |
|----------------|-----|------|
| x_min | 0.0 | 좌측 경계 |
| y_min | 0.0 | 하단 경계 |
| x_max | 0.2 | 우측 경계 (20%) |
| y_max | 0.2 | 상단 경계 (20%) |

## 5.4 Scalar Bar (컬러바/범례)

### 5.4.1 기본 설정

```python
# 기본 위치 및 크기
DEFAULT_SCALAR_BAR_POSITION_X = 0.9   # 우측 90% 위치
DEFAULT_SCALAR_BAR_POSITION_Y = 0.3   # 하단 30% 위치
DEFAULT_SCALAR_BAR_WIDTH = 0.08       # 너비 8%
DEFAULT_SCALAR_BAR_HEIGHT = 0.4       # 높이 40%
DEFAULT_SCALAR_BAR_NUM_LABELS = 5     # 라벨 개수
DEFAULT_SCALAR_BAR_TITLE_SEPARATION = 12  # 제목-바 간격
```

### 5.4.2 시각화

```
         [Pressure]     ← 제목
        ┌─────────┐
    1.0 │ ███████ │     ← 최대값
        │ ███████ │
    0.5 │ ███████ │
        │ ███████ │
    0.0 │ ███████ │     ← 최소값
        └─────────┘
```

### 5.4.3 업데이트 함수

```python
def update_scalar_bar(self, actor, title=None):
    """
    액터의 Lookup Table을 사용하여 스칼라 바 업데이트
    
    1. mapper에서 lookup table 가져오기
    2. scalar bar에 lookup table 연결
    3. 제목 설정
    4. 위젯 활성화
    """
    mapper = actor.GetMapper()
    if not mapper:
        self.hide_scalar_bar()
        return
    
    lut = mapper.GetLookupTable()
    self._scalar_bar.SetLookupTable(lut)
    
    if title:
        self._scalar_bar.SetTitle(title)
    
    self._scalar_bar_widget.SetEnabled(1)
    self.render()
```

### 5.4.4 Legend Settings

```python
DEFAULT_LEGEND_SETTINGS = {
    "font_size": 12,
    "font_color": (1.0, 1.0, 1.0),  # 흰색
    "bold": True,
    "italic": False,
    "position_x": 0.9,
    "position_y": 0.3,
    "width": 0.08,
    "height": 0.4,
}
```

## 5.5 Plane Preview (평면 미리보기)

### 5.5.1 용도

- Slice Filter, Clip Filter 적용 전 평면 위치 미리보기
- 반투명 평면과 방향 화살표로 표시

### 5.5.2 구성 요소

```python
def _setup_plane_preview(self):
    # 평면 소스
    self._plane_source = vtk.vtkPlaneSource()
    
    # 평면 매퍼 및 액터
    self._plane_mapper = vtk.vtkPolyDataMapper()
    self._plane_actor = vtk.vtkActor()
    self._plane_actor.GetProperty().SetOpacity(DEFAULT_PLANE_PREVIEW_OPACITY)
    self._plane_actor.GetProperty().SetColor(0.8, 0.8, 0.2)  # 노란색
    
    # 법선 방향 화살표
    self._arrow_source = vtk.vtkArrowSource()
    self._arrow_actor = vtk.vtkActor()
    self._arrow_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 빨간색
```

### 5.5.3 화살표 설정

```python
DEFAULT_ARROW_SHAFT_RADIUS = 0.05
DEFAULT_ARROW_TIP_RADIUS = 0.15
DEFAULT_ARROW_TIP_LENGTH = 0.3
DEFAULT_ARROW_RESOLUTION = 20
DEFAULT_PLANE_PREVIEW_OPACITY = 0.4
```

### 5.5.4 업데이트

```python
def update_plane_preview(self, origin, normal, bounds):
    """
    평면 미리보기 위치 및 방향 업데이트
    
    Args:
        origin: [x, y, z] 평면 원점
        normal: [nx, ny, nz] 법선 벡터
        bounds: (xmin, xmax, ymin, ymax, zmin, zmax) 데이터 경계
    """
    # 평면 크기를 데이터 경계에 맞춤
    size = max(
        bounds[1] - bounds[0],
        bounds[3] - bounds[2],
        bounds[5] - bounds[4]
    ) * 0.5
    
    # 평면 설정
    self._plane_source.SetOrigin(origin)
    self._plane_source.SetNormal(normal)
    # ... 평면 점들 계산
    
    # 화살표 위치 및 방향 설정
    self._arrow_transform.Identity()
    self._arrow_transform.Translate(origin)
    self._arrow_transform.RotateWXYZ(angle, rotation_axis)
    self._arrow_transform.Scale(arrow_scale)
    
    self._plane_actor.SetVisibility(1)
    self._arrow_actor.SetVisibility(1)
    self.render()
```

## 5.6 카메라 제어

### 5.6.1 기본 카메라 설정

```python
DEFAULT_CAMERA_POSITION = (1, 1, 1)      # Isometric 위치
DEFAULT_CAMERA_FOCAL_POINT = (0, 0, 0)   # 원점
DEFAULT_CAMERA_VIEW_UP = (0, 0, 1)       # Z축이 위
```

### 5.6.2 카메라 상태 조회

```python
def get_camera_state(self):
    """현재 카메라 파라미터 반환"""
    camera = self._renderer.GetActiveCamera()
    return {
        "position": list(camera.GetPosition()),
        "focal_point": list(camera.GetFocalPoint()),
        "view_up": list(camera.GetViewUp()),
        "zoom": camera.GetViewAngle(),
    }
```

### 5.6.3 카메라 상태 적용

```python
def apply_camera_state(self, state):
    """카메라 파라미터 설정"""
    camera = self._renderer.GetActiveCamera()
    
    if "position" in state:
        camera.SetPosition(*state["position"])
    if "focal_point" in state:
        camera.SetFocalPoint(*state["focal_point"])
    if "view_up" in state:
        camera.SetViewUp(*state["view_up"])
    if "zoom" in state:
        camera.SetViewAngle(state["zoom"])
    
    self.render()
```

### 5.6.4 평면 뷰 설정

```python
def set_view_xy(self):
    """XY 평면 뷰 (위에서 아래로)"""
    camera = self._renderer.GetActiveCamera()
    camera.SetPosition(0, 0, 1)
    camera.SetFocalPoint(0, 0, 0)
    camera.SetViewUp(0, 1, 0)
    self._renderer.ResetCamera()
    self.render()

def set_view_yz(self):
    """YZ 평면 뷰 (옆에서)"""
    camera.SetPosition(1, 0, 0)
    camera.SetViewUp(0, 0, 1)
    # ...

def set_view_xz(self):
    """XZ 평면 뷰 (앞에서)"""
    camera.SetPosition(0, 1, 0)
    camera.SetViewUp(0, 0, 1)
    # ...
```

### 5.6.5 카메라 리셋

```python
def reset_camera(self):
    """Isometric 뷰로 리셋"""
    camera = self._renderer.GetActiveCamera()
    camera.SetPosition(*DEFAULT_CAMERA_POSITION)
    camera.SetFocalPoint(*DEFAULT_CAMERA_FOCAL_POINT)
    camera.SetViewUp(*DEFAULT_CAMERA_VIEW_UP)
    self._renderer.ResetCamera()
    self.render()
```

## 5.7 배경색

### 5.7.1 기본 배경색

```python
DEFAULT_BACKGROUND_COLOR = (0.32, 0.34, 0.43)  # Warm Gray
```

### 5.7.2 프리셋

```python
BACKGROUND_PRESETS = {
    "Warm Gray (Default)": ((0.32, 0.34, 0.43), None),
    "Blue Gray": ((0.25, 0.30, 0.38), None),
    "Dark Gray": ((0.15, 0.15, 0.18), None),
    "Neutral Gray": ((0.3, 0.3, 0.3), None),
    "Light Gray": ((0.8, 0.8, 0.82), None),
    "White": ((0.95, 0.95, 0.97), None),
    "Black": ((0.05, 0.05, 0.07), None),
    "Gradient Background": ((0.2, 0.2, 0.3), (0.5, 0.5, 0.6)),  # 그라데이션
}
```

### 5.7.3 배경 설정

```python
def set_background(self, color1, color2=None):
    """
    배경색 설정
    
    Args:
        color1: (r, g, b) 주 색상
        color2: (r, g, b) 그라데이션 색상 (선택)
    """
    if color2:
        self._renderer.SetBackground(color1)
        self._renderer.SetBackground2(color2)
        self._renderer.GradientBackgroundOn()
    else:
        self._renderer.SetBackground(color1)
        self._renderer.GradientBackgroundOff()
    self.render()
```

## 5.8 액터 관리

### 5.8.1 액터 추가

```python
def add_actor(self, actor):
    """렌더러에 액터 추가"""
    if actor:
        self._renderer.AddActor(actor)
        self.render()
```

### 5.8.2 액터 제거

```python
def remove_actor(self, actor):
    """렌더러에서 액터 제거"""
    if actor:
        self._renderer.RemoveActor(actor)
        self.render()
```

### 5.8.3 씬 클리어

```python
def clear_scene(self):
    """모든 액터 제거 (축, 스칼라바 제외)"""
    actors = self._renderer.GetActors()
    actors.InitTraversal()
    while True:
        actor = actors.GetNextActor()
        if not actor:
            break
        # 미리보기 액터는 제외
        if actor not in [self._plane_actor, self._arrow_actor]:
            self._renderer.RemoveActor(actor)
    self.render()
```

### 5.8.4 가시성 설정

```python
def set_actor_visibility(self, actor, visible):
    """액터 가시성 설정"""
    if actor:
        actor.SetVisibility(1 if visible else 0)
        self.render()
```

## 5.9 마우스/키보드 상호작용

### 5.9.1 기본 인터랙터 스타일 (TrackballCamera)

| 입력 | 동작 |
|------|------|
| 좌클릭 드래그 | 회전 (Rotate) |
| 우클릭 드래그 | 줌 (Zoom) |
| 중클릭 드래그 | 패닝 (Pan) |
| 스크롤 휠 | 줌 인/아웃 |

### 5.9.2 카메라 변경 콜백

```python
def _on_interaction(self, obj, event):
    """인터랙션 중 카메라 상태 업데이트 시그널 발생"""
    self.camera_changed.emit(self.get_camera_state())
```

### 5.9.3 인터랙션 비활성화

AI 처리 중 VTK 인터랙션 비활성화:

```python
def set_interaction_enabled(self, enabled):
    """VTK 인터랙터 및 위젯 활성화/비활성화"""
    if enabled:
        self._interactor.Enable()
        self._orientationWidget.SetEnabled(1)
    else:
        self._interactor.Disable()
        self._orientationWidget.SetEnabled(0)
    self.render()
```

## 5.10 시그널 정의

```python
class VTKWidget(QWidget):
    initialized = Signal()           # 초기화 완료
    camera_changed = Signal(dict)    # 카메라 상태 변경
```

---

*다음: [06-table-graph-views.md](./06-table-graph-views.md) - 테이블/그래프 뷰 상세*
