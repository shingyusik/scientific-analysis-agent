# 14. 상수 및 기본값 정의

이 문서는 애플리케이션 전반에서 사용되는 모든 상수와 기본값을 정리합니다.

---

## 14.1 윈도우 및 레이아웃

### 14.1.1 윈도우 크기

```python
DEFAULT_WINDOW_WIDTH = 1400   # 픽셀
DEFAULT_WINDOW_HEIGHT = 900   # 픽셀
```

### 14.1.2 레이아웃 비율

```python
# 메인 스플리터 (수평)
MAIN_SPLITTER_STRETCH = [2, 5, 2]  # 좌측:중앙:우측
MAIN_SPLITTER_SIZES = [350, 750, 300]  # 초기 픽셀 크기

# 좌측 사이드바 스플리터 (수직)
LEFT_SIDEBAR_STRETCH = [1, 1]  # Pipeline:Details
```

---

## 14.2 UI 요소 크기

### 14.2.1 버튼 및 입력

```python
RESET_BUTTON_WIDTH = 50       # Reset 버튼 너비 (픽셀)
SPINBOX_WIDTH = 100           # 스핀박스 너비 (픽셀)
CHAT_BUBBLE_MAX_WIDTH = 400   # 채팅 버블 최대 너비 (픽셀)
OFFSET_LIST_MIN_WIDTH = 400   # 오프셋 리스트 최소 너비 (픽셀)
```

---

## 14.3 타이밍 상수

### 14.3.1 지연 시간 (밀리초)

```python
UI_REENABLE_DELAY_MS = 100        # UI 재활성화 지연
DEFAULT_ANIMATION_INTERVAL_MS = 100  # 애니메이션 프레임 간격 (10fps)
SCROLL_TO_BOTTOM_DELAY_MS = 10    # 스크롤 지연
```

---

## 14.4 텍스트 미리보기 길이

```python
TOOL_RESULT_PREVIEW_LENGTH = 100  # 도구 결과 미리보기
LOG_MESSAGE_PREVIEW_LENGTH = 50   # 로그 메시지 미리보기
CHAT_TOOL_PREVIEW_LENGTH = 80     # 채팅 도구 활동 미리보기
```

---

## 14.5 렌더링 기본값

### 14.5.1 점/선/투명도

```python
DEFAULT_POINT_SIZE = 3.0          # Points 모드 점 크기
DEFAULT_LINE_WIDTH = 1.0          # Wireframe 선 두께
DEFAULT_GAUSSIAN_SCALE_FACTOR = 0.05  # Point Gaussian 스케일
DEFAULT_OPACITY = 1.0             # 기본 불투명도
OPACITY_SLIDER_MAX = 100          # 슬라이더 최대값 (0-100)
```

### 14.5.2 화살표/미리보기 지오메트리

```python
DEFAULT_ARROW_SHAFT_RADIUS = 0.05   # 화살표 축 반경
DEFAULT_ARROW_TIP_RADIUS = 0.15     # 화살표 끝 반경
DEFAULT_ARROW_TIP_LENGTH = 0.3      # 화살표 끝 길이
DEFAULT_ARROW_RESOLUTION = 20       # 화살표 해상도
DEFAULT_PLANE_PREVIEW_OPACITY = 0.4 # 평면 미리보기 투명도
```

---

## 14.6 스칼라 바 / 범례

### 14.6.1 위치 및 크기

```python
DEFAULT_SCALAR_BAR_POSITION_X = 0.9   # 화면 우측 90%
DEFAULT_SCALAR_BAR_POSITION_Y = 0.3   # 화면 하단 30%
DEFAULT_SCALAR_BAR_WIDTH = 0.08       # 화면 너비의 8%
DEFAULT_SCALAR_BAR_HEIGHT = 0.4       # 화면 높이의 40%
DEFAULT_SCALAR_BAR_NUM_LABELS = 5     # 라벨 개수
DEFAULT_SCALAR_BAR_TITLE_SEPARATION = 12  # 제목-바 간격
```

### 14.6.2 범례 설정

```python
DEFAULT_LEGEND_SETTINGS = {
    "font_size": 12,
    "font_color": (1.0, 1.0, 1.0),  # 흰색 (RGB 0-1)
    "bold": True,
    "italic": False,
    "position_x": 0.9,
    "position_y": 0.3,
    "width": 0.08,
    "height": 0.4,
}
```

---

## 14.7 카메라 기본 설정

```python
DEFAULT_CAMERA_POSITION = (1, 1, 1)       # Isometric 위치
DEFAULT_CAMERA_FOCAL_POINT = (0, 0, 0)    # 원점
DEFAULT_CAMERA_VIEW_UP = (0, 0, 1)        # Z축이 위
```

---

## 14.8 좌표축 위젯

```python
AXES_WIDGET_VIEWPORT = (0.0, 0.0, 0.2, 0.2)
# (x_min, y_min, x_max, y_max)
# 화면 좌하단 20% 영역
```

---

## 14.9 배경색 프리셋

```python
DEFAULT_BACKGROUND_COLOR = (0.32, 0.34, 0.43)  # Warm Gray

BACKGROUND_PRESETS = {
    # 이름: (주색상, 보조색상)
    # 보조색상이 None이면 단색, 있으면 그라데이션
    
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

---

## 14.10 표현 스타일

```python
REPRESENTATION_STYLES = [
    "Surface",           # 표면 렌더링
    "Wireframe",         # 와이어프레임
    "Points",            # 점
    "Surface With Edges", # 표면 + 에지
    "Point Gaussian",    # 가우시안 스플랫
]
```

---

## 14.11 필터 관련

### 14.11.1 Slice Filter

```python
DEFAULT_SLICE_PARAMS = {
    "origin": [0.0, 0.0, 0.0],
    "normal": [1.0, 0.0, 0.0],
    "offsets": [0.0],
    "show_preview": True,
}
```

### 14.11.2 Clip Filter

```python
DEFAULT_CLIP_PARAMS = {
    "origin": [0.0, 0.0, 0.0],
    "normal": [1.0, 0.0, 0.0],
    "show_preview": True,
}
```

### 14.11.3 Threshold Filter

```python
DEFAULT_THRESHOLD_PARAMS = {
    "array_name": "",
    "component": 0,
    "lower_bound": 0.0,
    "upper_bound": 1.0,
    "method": "between",      # "between", "above", "below"
    "attribute_type": "POINT", # "POINT" or "CELL"
}
```

### 14.11.4 Calculator Filter

```python
DEFAULT_CALCULATOR_PARAMS = {
    "expression": "",
    "result_array_name": "Result",
    "attribute_type": "POINT",
}
```

---

## 14.12 채팅/에이전트

### 14.12.1 메시지 발신자

```python
SENDER_TYPES = {
    "user": "user",
    "assistant": "assistant",
    "system": "system",
}
```

### 14.12.2 버블 색상 (참고용)

```python
MESSAGE_BUBBLE_COLORS = {
    "user": "#DCF8C6",       # 연녹색
    "assistant": "#E8E8E8",  # 회색
    "system": "#FFE4B5",     # 연주황
}
```

---

## 14.13 탭 타입

```python
class TabType:
    VTK = "vtk"
    TABLE = "table"
    GRAPH = "graph"
```

---

## 14.14 그래프 타입

```python
GRAPH_TYPES = [
    "line",       # 선 그래프
    "scatter",    # 산점도
    "bar",        # 막대 그래프
    "histogram",  # 히스토그램
]
```

---

## 14.15 Calculator 함수

```python
CALCULATOR_FUNCTIONS = [
    ("sin", "sin("),
    ("cos", "cos("),
    ("tan", "tan("),
    ("exp", "exp("),
    ("log", "log("),
    ("sqrt", "sqrt("),
    ("abs", "abs("),
    ("pow", "pow(,)"),
]

CALCULATOR_OPERATORS = [
    ("+", "+"),
    ("-", "-"),
    ("*", "*"),
    ("/", "/"),
    ("(", "("),
    (")", ")"),
]
```

---

## 14.16 스핀박스 범위

### 14.16.1 일반 스핀박스

```python
SPINBOX_RANGE_MIN = -1e10
SPINBOX_RANGE_MAX = 1e10
SPINBOX_DECIMALS = 6
SPINBOX_SINGLE_STEP = 0.1
```

### 14.16.2 과학 스핀박스

```python
SCIENTIFIC_SPINBOX_DECIMALS = 15
SCIENTIFIC_SPINBOX_RANGE = (-1e30, 1e30)
```

---

## 14.17 파일 필터

```python
VTK_FILE_FILTER = "VTK Files (*.vtu *.vti *.vtk)"
CSV_FILE_FILTER = "CSV Files (*.csv);;All Files (*)"
IMAGE_FILE_FILTERS = (
    "PNG Image (*.png);;"
    "JPEG Image (*.jpg);;"
    "SVG Vector (*.svg);;"
    "PDF Document (*.pdf)"
)
```

---

## 14.18 상수 사용 예시

```python
# 파일에서 상수 임포트
from utils.constants import (
    DEFAULT_WINDOW_WIDTH,
    DEFAULT_WINDOW_HEIGHT,
    DEFAULT_BACKGROUND_COLOR,
    REPRESENTATION_STYLES,
    UI_REENABLE_DELAY_MS,
)

# 사용
self.resize(DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT)
self._renderer.SetBackground(*DEFAULT_BACKGROUND_COLOR)
```

---

## 14.19 상수 파일 위치

모든 상수는 다음 파일에 중앙 집중화되어 있습니다:

```
src/python/utils/constants.py
```

새로운 상수 추가 시 이 파일에 추가하고, 카테고리별로 그룹화하여 관리합니다.

---

*이 문서로 포팅 가이드가 완료되었습니다. [README.md](./README.md)로 돌아가기*
