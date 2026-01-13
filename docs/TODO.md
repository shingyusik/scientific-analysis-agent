# Project Roadmap & TODO

## 🚀 P0: Agent Multimodal Integration (에이전트 시각적 상호작용)
**목표:** 에이전트가 사용자가 보는 화면(차트, 3D 뷰)을 이해하고 피드백을 줄 수 있도록 함.
- [ ] **이미지 input**: 에이전트에게 이미지 입력을 가능하게 함
- [ ] **VTK Render View LLM에 넘기기**: 현재 렌더링된 3D 뷰를 캡처하여 에이전트에게 전달
- [ ] **AI한테 그림으로 설명**: 에이전트가 시각 자료를 바탕으로 설명하거나, 반대로 그림으로 답변하는 기능 고려

## 🛠 P1: Core Analysis Tools (핵심 데이터 분석 도구)
**목표:** 과학적 분석에 필수적인 데이터 조작 및 필터링 기능 강화.
- [ ] **Calculator Filter**: 수식을 이용한 데이터 파생 변수 생성 기능
- [ ] **Extract Data Filter**:
    - [ ] 좌->우 드래그 선택 (Contain Selection)
    - [ ] 우->좌 드래그 선택 (Intersect Selection)

## 💬 P2: Chat UX & Context Management (대화 경험 및 컨텍스트 관리)
**목표:** 장기적인 분석 작업을 위한 대화 편의성 및 메모리 관리.
- [ ] **Context Window 남은 양 확인 바**: 토큰 제한에 대한 가시성 제공
- [ ] **메모리 연결**: 프로젝트/세션 간 컨텍스트 유지
- [ ] **이전 대화 참조 걸기**: 특정 메시지나 컨텍스트를 인용하여 질문
- [ ] **이전 요청 수정 후 재요청**: 프롬프트 수정 및 재생성 UX

## 📊 P3: Advanced Visualization (고급 시각화)
**목표:** 다양한 분석 니즈를 충족하는 그래프 타입 추가.
- [ ] **Subplot**: 다중 그래프 레이아웃 지원
- [ ] **3D Plot (Contour)**: 등고선 등 고급 3D 표현
- [ ] **Heatmap**: 데이터 밀도 및 상관분석 시각화

## 🧠 P4: Reasoning & Intelligence (추론 능력 고도화)
**목표:** 에이전트의 문제 해결 능력 향상.
- [ ] **Sequential Thinking**: 복잡한 문제를 단계별로 추론하는 프로세스 내재화
- [ ] **난이도 측정 LLM**: 작업 난이도에 따라 모델을 선택하거나 리소스를 배분하는 메타 인지 기능