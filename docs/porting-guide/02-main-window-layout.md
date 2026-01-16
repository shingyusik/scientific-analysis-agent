# 2. 메인 윈도우 레이아웃

## 2.1 윈도우 기본 설정

### 2.1.1 윈도우 크기 및 제목

```python
# 기본 윈도우 크기
DEFAULT_WINDOW_WIDTH = 1400   # 픽셀
DEFAULT_WINDOW_HEIGHT = 900   # 픽셀

# 윈도우 제목
title = "Scientific Analysis Agent"
```

## 2.2 메인 레이아웃 구조

메인 윈도우는 **수평 QSplitter**를 사용하여 3개의 주요 영역으로 분할됩니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Menu Bar (File | Filters | View)                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  View Controls Toolbar                                                       │
│  Time Animation Toolbar                                                      │
├──────────────┬────────────────────────────────────────────┬─────────────────┤
│              │                                            │                 │
│  Left        │           Center                           │                 │
│  Sidebar     │           Panel                            │                 │
│              │                                            │                 │
│  - Pipeline  │           (750px)                          │                 │
│    Browser   │                                            │   ┌───────────┐ │
│              │                                            │   │ ChatInput │ │
│  - Details   │                                            │   │ [Send]    │ │
│    Tabs      │                                            │   │ [Cancel]  │ │
│              │                                            │   │ [New]     │ │
│  (350px)     │                                            │   └───────────┘ │
│              │                                            │     (300px)     │
└──────────────┴────────────────────────────────────────────┴─────────────────┘
```

### 2.2.1 스플리터 설정

```python
# 메인 수평 스플리터 (3개 영역)
main_splitter = QSplitter(Qt.Horizontal)

# 스트레치 팩터 (비율)
main_splitter.setStretchFactor(0, 2)  # 좌측 사이드바
main_splitter.setStretchFactor(1, 5)  # 중앙 패널
main_splitter.setStretchFactor(2, 2)  # 우측 사이드바

# 초기 크기 (픽셀)
main_splitter.setSizes([350, 750, 300])
```

### 2.2.2 영역별 비율

| 영역 | 스트레치 팩터 | 초기 크기 | 비율 |
|------|--------------|----------|------|
| 좌측 사이드바 | 2 | 350px | ~25% |
| 중앙 패널 | 5 | 750px | ~54% |
| 우측 사이드바 | 2 | 300px | ~21% |

## 2.3 좌측 사이드바 레이아웃

좌측 사이드바는 **수직 QSplitter**로 상/하 분할됩니다.

```
┌──────────────────────┐
│   Pipeline Browser   │
│                      │
│  (트리 위젯)         │
│                      │
├──────────────────────┤
│                      │
│    Details Tabs      │
│  ┌────────┬────────┐ │
│  │Properties│ Info │ │
│  └────────┴────────┘ │
│                      │
│  (탭 콘텐츠 영역)    │
│                      │
└──────────────────────┘
```

### 2.3.1 수직 스플리터 설정

```python
# 좌측 사이드바 수직 스플리터
left_sidebar = QSplitter(Qt.Vertical)

# 스트레치 팩터 (1:1 비율)
left_sidebar.setStretchFactor(0, 1)  # Pipeline Browser
left_sidebar.setStretchFactor(1, 1)  # Details Tabs
```

### 2.3.2 컴포넌트

| 순서 | 컴포넌트 | 클래스 | 설명 |
|------|----------|--------|------|
| 1 | Pipeline Browser | `PipelineBrowserWidget` | 파이프라인 아이템 트리 |
| 2 | Details Tabs | `QTabWidget` | Properties + Information 탭 |

## 2.4 중앙 패널 레이아웃

중앙 패널은 **TabbedViewWidget** (QTabWidget 확장)으로 구성됩니다.

```
┌────────────────────────────────────────────────────────────┐
│ ┌─────────┐ ┌──────────┐ ┌──────────┐            [+] 버튼 │
│ │ 3D View │ │  Table   │ │  Graph   │                     │
│ └─────────┘ └──────────┘ └──────────┘                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│                                                            │
│                    Active Tab Content                      │
│                      (VTK/Table/Graph)                     │
│                                                            │
│                                                            │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 2.4.1 탭 기능

- **탭 추가**: 좌측 상단 `[+]` 버튼
- **탭 닫기**: 각 탭의 `[x]` 버튼 (고정 탭 제외)
- **탭 재정렬**: 드래그 앤 드롭
- **우클릭 메뉴**: Pin/Unpin, Rename, Close Others 등

### 2.4.2 기본 탭

- **3D View**: 초기 생성, 고정(pinned) 상태

## 2.5 우측 사이드바 (채팅 패널)

단일 컴포넌트로 구성:

```
┌──────────────────────┐
│     Chat Panel       │
│                      │
│  ┌────────────────┐  │
│  │  메시지 영역   │  │
│  │  (스크롤 가능) │  │
│  │                │  │
│  └────────────────┘  │
│                      │
│  ┌────────────────┐  │
│  │ 입력창 + 버튼  │  │
│  └────────────────┘  │
└──────────────────────┘
```

## 2.6 메뉴바 구성

```
┌──────────────────────────────────────────────────────────┐
│  File  │  Filters  │  View                               │
└──────────────────────────────────────────────────────────┘
```

### 2.6.1 File 메뉴

| 메뉴 항목 | 단축키 | 동작 |
|----------|--------|------|
| Load Data... | Ctrl+O | 파일 로드 다이얼로그 |
| Exit | Ctrl+Q | 애플리케이션 종료 |

### 2.6.2 Filters 메뉴

| 메뉴 항목 | 동작 |
|----------|------|
| Slice | 선택 아이템에 Slice 필터 적용 |
| Clip | 선택 아이템에 Clip 필터 적용 |
| Threshold | 선택 아이템에 Threshold 필터 적용 |
| Calculator | 선택 아이템에 Calculator 필터 적용 |

### 2.6.3 View 메뉴

| 메뉴 항목 | 동작 |
|----------|------|
| New 3D View Tab | 새 VTK 렌더 탭 생성 |
| New Table View Tab | 새 테이블 탭 생성 |
| New Graph View Tab | 새 그래프 탭 생성 |

## 2.7 툴바 구성

### 2.7.1 View Controls Toolbar

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [Camera View] [Home] │ [XY Plane] [YZ Plane] [XZ Plane] │ [Fit Range]       │
│                      │                                   │ [Custom Range]    │
│                      │                                   │ [Background ▼]    │
│                      │                                   │ [Representation ▼]│
└──────────────────────────────────────────────────────────────────────────────┘
```

| 버튼/드롭다운 | 동작 |
|--------------|------|
| Camera View | 카메라 설정 다이얼로그 표시 |
| Home (Reset) | 카메라 초기화 (isometric view) |
| XY Plane | XY 평면 뷰로 전환 |
| YZ Plane | YZ 평면 뷰로 전환 |
| XZ Plane | XZ 평면 뷰로 전환 |
| Fit Range | 스칼라 범위 자동 맞춤 |
| Custom Range | 스칼라 범위 수동 설정 다이얼로그 |
| Background ▼ | 배경색 프리셋 선택 |
| Representation ▼ | 표현 스타일 선택 |

### 2.7.2 Time Animation Toolbar

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [◀◀] [▶] [▶▶] [⟳]  │  Time Step: [▼ Combo] [Spinner ↕]  │  Frame: X/Y    │
└────────────────────────────────────────────────────────────────────────────┘
```

| 컨트롤 | 동작 |
|--------|------|
| ◀◀ (Play Back) | 역방향 재생 |
| ▶ (Play/Pause) | 정방향 재생/일시정지 |
| ▶▶ (Play Forward) | 정방향 재생 |
| ⟳ (Loop) | 반복 재생 토글 |
| Combo | 시간 스텝 드롭다운 선택 |
| Spinner | 시간 스텝 숫자 직접 입력 |
| Frame: X/Y | 현재 프레임 / 전체 프레임 표시 |

## 2.8 반응형 동작

### 2.8.1 스플리터 드래그

- 사용자가 스플리터 경계를 드래그하여 영역 크기 조절 가능
- 최소/최대 크기 제한 없음 (Qt 기본값)

### 2.8.2 윈도우 리사이즈

- 스트레치 팩터에 따라 각 영역 비례적으로 크기 조절
- VTK 위젯은 자동으로 렌더 버퍼 크기 조절

## 2.9 UI 비활성화 동작

AI 에이전트가 응답 중일 때 UI를 비활성화:

```python
def _disable_ui_interaction(self):
    QApplication.setOverrideCursor(Qt.WaitCursor)  # 대기 커서
    
    self._tabbed_view.setEnabled(False)
    self._toolbar.setEnabled(False)
    self._pipeline_browser.setEnabled(False)
    self._properties_panel.setEnabled(False)
    self._details_tabs.setEnabled(False)
    self.menuBar().setEnabled(False)
```

### 2.9.1 재활성화

```python
UI_REENABLE_DELAY_MS = 100  # 100ms 딜레이 후 재활성화

def _enable_ui_interaction(self):
    QTimer.singleShot(UI_REENABLE_DELAY_MS, self._perform_ui_reenable)
```

---

*다음: [03-left-sidebar.md](./03-left-sidebar.md) - 좌측 사이드바 상세*
