# Project Roadmap & TODO

## ✅ Completed Features (완료된 기능)
- [x] **Calculator Filter**: 수식 기반 데이터 파생 변수 생성 (`src/python/filters/calculator_filter.py`)
- [x] **Slice Filter**: 평면으로 데이터 슬라이싱
- [x] **Clip Filter**: 평면으로 데이터 클리핑
- [x] **Line/Scatter/Histogram/Bar Graph**: 기본 그래프 타입 지원
- [x] **Multi-source Graph**: 여러 데이터 소스를 한 그래프에 표시
- [x] **Time Series Support**: 시계열 데이터 재생 및 탐색
- [x] **Basic Agent Graph**: Guardrail → Agent → Tools 구조, Dynamic tool 로딩

---

## 🛠 P0: Core Post-Processing (필수 후처리 기능)
**목표:** "불편하더라도 쓸만한" 분석 도구가 되기 위한 데이터 추출/필터링 기능.

- [x] **Threshold Filter**: 스칼라 값 범위로 데이터 필터링 (예: `T > 300 AND T < 500`) (`src/python/filters/threshold_filter.py`)
- [ ] **Contour Filter**: 등고선/등전위면 생성
- [ ] **Extract Data Filter**:
    - [ ] **ROI Select (Interactive)**: 화면상에서 드래그(Box Selection)하여 관심 영역 데이터만 추출
    - [ ] **Query Select**: 조건식으로 데이터 추출

---

## 📊 P1: Essential Visualization (기본 시각화 및 비교)
**목표:** 데이터 경향성을 파악하기 위한 시각화 보강.

- [ ] **Interactive Data Inspection (Hover)**: Render View의 데이터 포인트에 마우스를 올리면 값 표시 (Tooltip)
- [ ] **Subplot**: 여러 케이스나 변수를 동시에 비교 (Multi-view)
- [ ] **Heatmap**: 2D 데이터 분포 확인
- [ ] **3D Plot (Surface/Contour)**: 3차원 표면/등고선 확인

---

## 🧠 P2: Smarter Agent Architecture (에이전트 고도화)
**목표:** 복잡한 요청을 더 정확하고 효율적으로 처리하는 Multi-Agent 시스템 구축.

### Phase 1: Planning & Classification (계획 및 분류)
- [ ] **Classifier Agent (Router Node)**:
    - 사용자 요청을 분류 (Simple Tool Call / Multi-step Plan / Clarification Needed)
    - 요청 복잡도에 따라 적절한 처리 경로로 라우팅
    - 예: "슬라이스 필터 적용" → Simple, "온도 분포 분석하고 보고서 작성" → Multi-step

- [ ] **Planning Agent Node**:
    - Multi-step 작업을 위한 실행 계획 생성
    - Sub-task 분해 및 의존성 관리
    - 예: "열전달 분석" → [데이터 로드, 온도 필터, 시각화, 통계 추출]

### Phase 2: State & Context Enhancement (상태 및 컨텍스트 강화)
- [ ] **Enhanced AgentState**:
    - `current_plan: List[SubTask]` - 현재 실행 중인 계획
    - `execution_history: List[StepResult]` - 실행 이력
    - `user_preferences: Dict` - 사용자 선호도 (단위, 색상 테마 등)
    
- [ ] **Context Injection Node**:
    - 매 턴마다 현재 Pipeline 상태를 State에 자동 주입
    - 선택된 아이템, 가시성, 시간 스텝 등 동적 컨텍스트 제공

### Phase 3: Verification & Self-Correction (검증 및 자가 수정)
- [ ] **Verification Node**:
    - Tool 실행 결과 검증 (성공/실패, 예상 결과와 일치 여부)
    - 예: "슬라이스 적용 후 데이터가 생성되었는지 확인"
    
- [ ] **Re-planning on Failure**:
    - 검증 실패 시 대안 전략 수립
    - 최대 재시도 횟수 제한

### Phase 4: Multi-Modal & Memory (멀티모달 및 장기 기억)
- [ ] **이미지 Input (Vision)**:
    - 사용자가 이미지를 직접 업로드하여 에이전트와 대화
    - VTK Render View 스크린샷을 자동 캡처하여 전달
    - "이 그래프에서 이상한 점이 있니?" 같은 질문 처리

- [ ] **Session Memory**:
    - RAG 기반 장기 기억 저장 (이전 분석 결과, 사용자 선호도)
    - 프로젝트 간 컨텍스트 유지

---

## 📝 P3: Usability (사용성 개선)
- [ ] **Context Window Bar**: 토큰 사용량 확인
- [ ] **이전 대화 참조**: 특정 메시지 인용 기능

---