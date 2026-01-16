# 1. 애플리케이션 전체 개요

## 1.1 애플리케이션 소개

**SA-Agent (Scientific Analysis Agent)**는 VTK 기반 고성능 3D 시각화와 LangGraph 에이전트를 결합한 데스크톱 애플리케이션입니다. 사용자가 자연어로 복잡한 수치 해석 데이터(CFD/FEA 시뮬레이션 결과)를 분석할 수 있습니다.

## 1.2 핵심 기능

### 1.2.1 데이터 로드 및 시각화
- **지원 파일 형식**: `.vtu`, `.vti`, `.vtk`
- **시계열 데이터**: 다중 파일 로드 시 자동 시계열 인식
- **3D 렌더링**: VTK 기반 고성능 메시 시각화

### 1.2.2 데이터 필터링
- **Slice Filter**: 평면으로 데이터 절단
- **Clip Filter**: 평면 기준 데이터 클리핑
- **Threshold Filter**: 스칼라 값 범위로 필터링
- **Calculator Filter**: 수식 기반 파생 변수 생성

### 1.2.3 AI 에이전트 통합
- **자연어 명령**: 채팅으로 분석 작업 요청
- **도구 자동 호출**: 필터 적용, 뷰 변경 등 자동 실행
- **스트리밍 응답**: 실시간 응답 표시

### 1.2.4 다중 뷰 시스템
- **3D View**: VTK 렌더 뷰
- **Table View**: 데이터 테이블 표시
- **Graph View**: Matplotlib 그래프

## 1.3 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────────────────┐
│                            MainWindow                                    │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌────────────────────────────┐  ┌──────────────────┐ │
│  │ Left Sidebar │  │      Center Panel          │  │  Right Sidebar   │ │
│  │              │  │   (TabbedViewWidget)       │  │   (ChatPanel)    │ │
│  │ - Pipeline   │  │                            │  │                  │ │
│  │   Browser    │  │  ┌──────┐ ┌──────┐ ┌────┐  │  │ - 메시지 목록   │ │
│  │              │  │  │3D Tab│ │Table │ │Graph│ │  │ - 입력창        │ │
│  │ - Properties │  │  └──────┘ └──────┘ └────┘  │  │ - 버튼들        │ │
│  │   Panel      │  │                            │  │                  │ │
│  │              │  │  ┌────────────────────────┐│  │                  │ │
│  │ - Info Page  │  │  │                        ││  │                  │ │
│  └──────────────┘  │  │    Active Tab View     ││  │                  │ │
│                    │  │                        ││  │                  │ │
│                    │  └────────────────────────┘│  └──────────────────┘ │
├─────────────────────────────────────────────────────────────────────────┤
│              Menu Bar  |  Toolbar  |  Time Animation Toolbar            │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1.4 MVVM 아키텍처 패턴

### 1.4.1 구성 요소

| 계층 | 컴포넌트 | 역할 |
|------|----------|------|
| **View** | MainWindow, VTKWidget, ChatPanel 등 | UI 표시 및 사용자 입력 처리 |
| **ViewModel** | PipelineViewModel, VTKViewModel, ChatViewModel | 상태 관리 및 비즈니스 로직 |
| **Model** | PipelineItem, TableDataModel | 데이터 구조 정의 |
| **Service** | VTKRenderService, FileLoaderService | 핵심 서비스 로직 |

### 1.4.2 데이터 흐름

```
User Input → View → ViewModel → Service → ViewModel (Signal) → View Update
                       ↑              ↓
                    Model  ←──────────┘
```

## 1.5 신호(Signal) 기반 통신

Qt의 Signal-Slot 메커니즘을 사용하여 컴포넌트 간 느슨한 결합을 유지합니다:

```python
# ViewModel에서 Signal 정의
class PipelineViewModel(QObject):
    item_added = Signal(object)      # 아이템 추가됨
    item_removed = Signal(str)       # 아이템 삭제됨 (item_id)
    selection_changed = Signal(object) # 선택 변경됨

# View에서 Signal 연결
self._pipeline_vm.item_added.connect(self._on_item_added)
```

## 1.6 주요 파일 구조

```
src/python/
├── main.py                      # 애플리케이션 진입점
├── config.py                    # 설정 파일
│
├── views/                       # View 계층
│   ├── main_window.py          # 메인 윈도우
│   ├── vtk_widget.py           # VTK 렌더 위젯
│   ├── chat_panel.py           # 채팅 패널
│   ├── properties_panel.py     # 속성 패널
│   ├── pipeline_browser.py     # 파이프라인 브라우저
│   ├── tabbed_view_widget.py   # 탭 뷰 컨테이너
│   ├── table_view_widget.py    # 테이블 뷰
│   ├── graph_view_widget.py    # 그래프 뷰
│   ├── time_animation_widget.py # 시간 애니메이션 컨트롤
│   ├── menu_manager.py         # 메뉴바 관리
│   ├── toolbar_manager.py      # 툴바 관리
│   └── common_widgets.py       # 공통 위젯
│
├── viewmodels/                  # ViewModel 계층
│   ├── pipeline_viewmodel.py   # 파이프라인 상태 관리
│   ├── vtk_viewmodel.py        # VTK 뷰 상태 관리
│   ├── chat_viewmodel.py       # 채팅 상태 관리
│   ├── table_viewmodel.py      # 테이블 상태 관리
│   ├── graph_viewmodel.py      # 그래프 상태 관리
│   └── time_series_manager.py  # 시계열 관리
│
├── models/                      # Model 계층
│   ├── pipeline_item.py        # 파이프라인 아이템
│   └── table_data_model.py     # 테이블 데이터 모델
│
├── filters/                     # 필터 시스템
│   ├── filter_base.py          # 필터 기본 클래스
│   ├── slice_filter.py         # Slice 필터
│   ├── clip_filter.py          # Clip 필터
│   ├── threshold_filter.py     # Threshold 필터
│   └── calculator_filter.py    # Calculator 필터
│
├── services/                    # Service 계층
│   ├── vtk_render_service.py   # VTK 렌더링 서비스
│   └── file_loader_service.py  # 파일 로드 서비스
│
├── agent/                       # AI 에이전트
│   ├── graph.py                # LangGraph 그래프 정의
│   ├── models.py               # 에이전트 모델
│   └── tools/                  # 도구 정의
│
└── utils/                       # 유틸리티
    ├── constants.py            # 상수 정의
    ├── logger.py               # 로깅
    └── app_context.py          # 앱 컨텍스트
```

## 1.7 시작점 - main.py

```python
# 간략화된 진입점 구조
def main():
    app = QApplication(sys.argv)
    
    # 서비스 초기화
    render_service = VTKRenderService()
    file_loader = FileLoaderService()
    
    # ViewModel 초기화
    pipeline_vm = PipelineViewModel(render_service, file_loader)
    vtk_vm = VTKViewModel(render_service)
    chat_vm = ChatViewModel(pipeline_vm, vtk_vm)
    
    # MainWindow 생성
    window = MainWindow(pipeline_vm, vtk_vm, chat_vm)
    window.show()
    
    sys.exit(app.exec())
```

---

*다음: [02-main-window-layout.md](./02-main-window-layout.md) - 메인 윈도우 레이아웃 상세*
