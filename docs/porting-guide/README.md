# SA-Agent 포팅 가이드

이 문서는 Scientific Analysis Agent (SA-Agent) 프로젝트를 다른 언어/프레임워크로 포팅하기 위한 상세 기능 및 시각화 명세입니다.

## 📁 문서 구조

```
porting-guide/
├── README.md                        # 이 파일 - 문서 개요
├── 01-app-overview.md              # 애플리케이션 전체 개요
├── 02-main-window-layout.md        # 메인 윈도우 레이아웃 및 크기
├── 03-left-sidebar.md              # 좌측 사이드바 (Pipeline Browser, Properties, Info)
├── 04-center-panel.md              # 중앙 패널 (탭 뷰 시스템)
├── 05-vtk-render-view.md           # VTK 렌더 뷰 상세
├── 06-table-graph-views.md         # 테이블/그래프 뷰 상세
├── 07-right-sidebar-chat.md        # 우측 채팅 패널
├── 08-menu-toolbar.md              # 메뉴바 및 툴바 구성
├── 09-dialogs-popups.md            # 다이얼로그 및 팝업 상세
├── 10-filter-system.md             # 필터 시스템 상세
├── 11-interaction-logic.md         # 사용자 상호작용 논리
├── 12-data-flow-architecture.md    # 데이터 흐름 및 아키텍처
├── 13-performance-optimization.md  # 성능 최적화 전략
└── 14-constants-defaults.md        # 상수 및 기본값 정의
```

## 🎯 문서 목적

1. **UI/UX 재현성**: 모든 버튼, 입력창의 위치와 크기를 정확히 파악
2. **상호작용 논리**: 각 UI 요소 간의 연결 및 동작 흐름 이해
3. **성능 전략**: 대용량 데이터 처리를 위한 최적화 기법 파악
4. **기능 완전성**: 모든 기능이 빠짐없이 포팅될 수 있도록 상세 명세

## 📊 기술 스택 요약

| 계층 | 현재 기술 | 역할 |
|------|-----------|------|
| **GUI** | PySide6 (Qt for Python) | UI 프레임워크 |
| **시각화** | VTK + QVTKRenderWindowInteractor | 3D 렌더링 |
| **AI 에이전트** | LangGraph + LangChain | 자연어 처리 및 도구 호출 |
| **차트** | Matplotlib | 2D 그래프 |
| **아키텍처** | MVVM 패턴 | View - ViewModel - Model |

## 🔗 문서 읽기 순서

1. 먼저 `01-app-overview.md`를 읽어 전체 구조 파악
2. `02-main-window-layout.md`로 레이아웃 이해
3. 각 패널별 상세 문서 (03~07) 순차적 읽기
4. `11-interaction-logic.md`로 상호작용 이해
5. `12-data-flow-architecture.md`로 데이터 흐름 파악
6. 필요에 따라 나머지 문서 참조

---

*이 문서는 SA-Agent v1.0 기준으로 작성되었습니다.*
