# Project Roadmap & TODO

## 🛠 P0: Core Post-Processing (필수 후처리 기능)
**목표:** "불편하더라도 쓸만한" 분석 도구가 되기 위한 데이터 가공 기능 우선 구현.
- [ ] **Calculator Filter**: 수식을 이용한 데이터 파생 변수 생성 (예: `Temp * 2`, `mag(Velocity)`)
- [ ] **Extract Data Filter**:
    - [ ] **ROI Select (Interactive)**: 화면상에서 드래그(Box Selection)하여 관심 영역 데이터만 추출
    - [ ] **Query Select**: 조건식(예: `T > 300`)으로 데이터 추출

## 📊 P1: Essential Visualization (기본 시각화 및 비교)
**목표:** 데이터 경향성을 파악하기 위한 시각화 보강.
- [ ] **Subplot**: 여러 케이스나 변수를 동시에 비교 (Multi-view)
- [ ] **Heatmap**: 2D 데이터 분포 확인
- [ ] **3D Plot (Contour)**: 3차원 등전위면/등고선 확인

## 🚀 P2: Agent Interaction (에이전트 연동)
**목표:** 분석을 보조하는 AI 기능.
- [ ] **이미지 input & VTK View**: 에이전트가 화면을 보고 상황 파악
- [ ] **난이도 측정 & Sequential Thinking**: 복잡한 요청 처리
- [ ] **이전 대화 참조**: 연속적인 분석 흐름 지원

## 📝 P3: Usability (사용성 개선)
- [ ] **Context Window Bar**: 토큰 사용량 확인
- [ ] **Session Memory**: 프로젝트 간 기억 공유