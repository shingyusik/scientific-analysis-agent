# Agent Architecture Design

## 현재 구조 (Current)

> ⚠️ **Guardrail 임시 비활성화** (2025-01-15): 판단 기준이 애매하여 바이패스됨. `src/python/agent/graph.py` 참조.

```mermaid
flowchart LR
    U[User] --> A[Agent]
    A -->|tool_calls| T[Tools]
    T --> A
    A -->|done| E2[END]
    
    G[Guardrail]:::disabled -.->|"비활성화됨"| A
    
    style A fill:#99ccff
    style T fill:#99ff99
    classDef disabled fill:#cccccc,stroke:#999999,stroke-dasharray: 5 5
```

---

## 목표 구조 (Target - Phase 1~3)

```mermaid
flowchart TB
    U[User] --> G[Guardrail]
    G -->|blocked| E1[END]
    G -->|allowed| C{Classifier}
    
    C -->|simple| A[Agent]
    C -->|multi-step| P[Planner]
    C -->|need_info| REQ[User Input Form]
    REQ -->|resume| C
    
    P --> A
    A -->|tool_calls| T[Tools]
    T --> A
    A -->|done| V{Verifier}
    
    V -->|success| E2[END]
    V -->|fail| R[Re-plan]
    R --> A

    style G fill:#ff9999
    style C fill:#ffcc99
    style P fill:#ffff99
    style A fill:#99ccff
    style T fill:#99ff99
    style V fill:#cc99ff
    style R fill:#ff99cc
    style REQ fill:#ffccff
```

---

## Phase 4: Multi-Modal & Memory

```mermaid
flowchart TB
    subgraph Input
        U[User]
        IMG[Image]
        VTK[VTK View]
    end
    
    subgraph Context
        CTX[Injector]
        MEM[(Memory)]
    end
    
    U --> CTX
    IMG --> CTX
    VTK --> CTX
    MEM --> CTX
    
    CTX --> G[Guardrail]
    G -->|blocked| E1[END]
    G -->|allowed| C{Classifier}
    
    C -->|simple| A[Agent]
    C -->|multi-step| P[Planner]
    C -->|need_info| REQ[User Input Form]
    REQ -->|resume| C
    
    P --> A
    A -->|tool_calls| T[Tools]
    T --> A
    A -->|done| V{Verifier}
    
    V -->|success| E2[END]
    V -->|success| MEM
    V -->|fail| R[Re-plan]
    R --> A

    style G fill:#ff9999
    style C fill:#ffcc99
    style P fill:#ffff99
    style A fill:#99ccff
    style T fill:#99ff99
    style V fill:#cc99ff
    style R fill:#ff99cc
    style REQ fill:#ffccff
```

---

## 노드 역할

| Node | 역할 |
|------|------|
| ~~**Guardrail**~~ | ⚠️ **비활성화됨** - 보안/스팸 필터링 |
| **Classifier** | 요청 복잡도 분류 (simple/multi-step) |
| **Planner** | 멀티스텝 작업 계획 수립 |
| **Agent** | 도구 호출 및 응답 생성 |
| **Tools** | 실제 기능 실행 |
| **Verifier** | 결과 검증 |
| **Re-plan** | 실패 시 대안 수립 |
| **Injector** | 현재 상태/이미지 주입 |
| **Memory** | 장기 기억 (RAG) |

---

## State 구조

```mermaid
classDiagram
    class AgentState {
        messages: List
        blocked: bool
        pipeline_context: Dict
        current_plan: List
        execution_history: List
        classification: str
        retry_count: int
    }
```
