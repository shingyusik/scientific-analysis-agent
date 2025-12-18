# PRD: Scientific Analysis Agent (SA-Agent)

## 1. 프로젝트 개요 (Overview)

* **프로젝트명:** SA-Agent (Scientific Analysis Agent)
* **목적:** VTK 기반 고성능 3D 시각화와 LangGraph 에이전트를 결합하여, 사용자가 자연어로 복잡한 수치 해석 데이터를 분석할 수 있는 데스크톱 애플리케이션 구축.
* **핵심 가치:** * **Native Performance:** C++/VTK 기반의 고속 데이터 처리.
* **AI Integration:** LLM 기반 에이전트의 워크플로우 자동화.
* **Compliance:** LGPL v3 라이선스를 준수하는 상용화 가능 아키텍처.



---

## 2. 타겟 사용자 및 유스케이스

* **타겟:** CFD/FEA 엔지니어, 수치 해석 연구원, 데이터 과학자.
* **주요 유스케이스:**
1. 대용량 시뮬레이션 결과 파일(`.vtu`, `.vti`) 로드 및 시각화.
2. 자연어 명령을 통한 특정 물리량(압력, 속도 등)의 임계값 필터링.
3. 에이전트를 활용한 데이터 통계 분석 및 결과 리포팅.



---

## 3. 시스템 아키텍처 (Architecture)

### **3.1 계층 구조**

* **Presentation Layer:** PySide6 기반 GUI. `QVTKRenderWindowInteractor`를 통한 시각화 패널 구현.
* **Intelligence Layer:** LangGraph 기반 에이전트. 사용자의 의도를 분석하고 분석 도구(Tool)를 호출.
* **Computation Layer:** C++ 17 및 VTK Native 라이브러리. Pybind11를 통해 Python과 데이터 공유.

### **3.2 데이터 흐름**

1. **Input:** 사용자가 사이드바 대화창에 분석 명령 입력.
2. **Reasoning:** LangGraph 에이전트가 상태(State)를 확인하고 최적의 C++ 도구 선택.
3. **Action:** C++ 엔진이 메모리 상의 VTK 데이터를 처리 (예: Slice, Clip).
4. **Sync:** 연산 완료 시 Qt Signal을 발생시켜 UI 스레드의 시각화 패널 갱신(`Render()`).

---

## 4. 상세 기능 요구사항 (Requirements)

### **F-1: 시각화 및 UI**

* **F-1.1:** 메인 화면에 VTK 렌더링 윈도우 배치.
* **F-1.2:** 우측 사이드바에 실시간 채팅 인터페이스 구현.
* **F-1.3:** 파일 탐색기를 통한 로컬 VTK 데이터 업로드 기능.

### **F-2: 분석 에이전트**

* **F-2.1:** LangGraph를 이용한 분석 단계 제어 (데이터 로드 -> 전처리 -> 분석 -> 시각화).
* **F-2.2:** LLM Tool Calling을 통한 C++ 함수 실행.
* **F-2.3:** 이전 분석 결과를 기억하고 후속 질문에 답변하는 Context 유지.

### **F-3: 고성능 연산 모듈**

* **F-3.1:** C++ 기반의 대용량 Mesh 데이터 필터링 알고리즘.
* **F-3.2:** 특정 영역의 물리량 추출 및 통계 연산 (Mean, Max, Min).
* **F-3.3:** Pybind11을 활용한 Python-C++ 간 제로 카피(Zero-copy) 데이터 접근 지향.

---

## 5. 기술 스택 (Tech Stack)

| 항목 | 기술 | 라이선스 |
| --- | --- | --- |
| **GUI** | PySide6 (Qt for Python) | **LGPL v3** |
| **Visualization** | VTK (Native C++) | BSD |
| **Agent** | LangGraph / Python | MIT |
| **Binding** | Pybind11 | BSD |
| **Build Tool** | CMake / Setuptools | - |

---

## 6. 라이선스 및 배포 전략 (Compliance)

* **LGPL 준수:** Qt 라이브러리를 동적 링크(`.dll`, `.so`) 방식으로 배포하여 소스코드 비공개 권리 유지.
* **배포 방식:** PyInstaller 또는 Nuitka의 `--onedir` 옵션을 사용하여 라이브러리 분리 배포.
* **고지 의무:** 앱 내 'About' 메뉴를 통해 Qt 사용 및 LGPL 라이선스 명시.

---

## 7. 개발 단계별 로드맵

1. **1단계 (PoC):** PySide6 내 VTK 윈도우 삽입 및 기초 C++ 모듈 바인딩.
2. **2단계 (Agent):** LangGraph 기본 노드 설계 및 단순 가시화 제어 도구 연결.
3. **3단계 (Analysis):** 복잡한 수치 해석 알고리즘(C++) 추가 및 에이전트 추론 고도화.
4. **4단계 (Optimization):** 멀티 스레딩을 통한 UI 프리징 방지 및 최종 패키징.
