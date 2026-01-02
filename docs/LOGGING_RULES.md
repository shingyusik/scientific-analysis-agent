# Scientific Analysis Agent Logging Rules

This document outlines the "Clean Logging" strategy adopted for the Scientific Analysis Agent project. The goal is to maintain a logging system that provides high observability without cluttering log files with excessive noise.

## Core Principles

1.  **Cleanliness**: Avoid logging loops, frequent rendering updates, or simple getter/setter calls.
2.  **Observability**: Focus on application lifecycle, business logic entry points, external I/O, and error conditions.
3.  **Consistency**: Use standard naming conventions and English messages.

## Implementation Guide

### 1. Setup

Import the logging utilities in every file that requires logging:

```python
from utils.logger import get_logger, log_execution

logger = get_logger("ModuleName")  # Use a short, descriptive name (max 15 chars)
```

### 2. Levels

*   **INFO**: Major business events, state changes, external system interactions. (e.g., "File Loaded", "Agent Processing Started")
    *   *Default configuration logs INFO and above.*
*   **DEBUG**: Detailed execution flow, function entry/exit, variable states.
    *   *Note: `@log_execution` defaults to DEBUG level.*
*   **WARNING**: Recoverable issues, missing configuration (e.g., "Env file not found").
*   **ERROR**: Exceptions, feature failures (e.g., "Agent Processing Error").

### 3. @log_execution Decorator

Use the decorator for functions representing a *unit of work*:

```python
@log_execution(start_msg="Starting Task...", end_msg="Task Finished")
def complex_task():
    ...
```

*   **Default Behavior**: Logs at `DEBUG` level.
*   **Override**: Use `level="INFO"` for critical entry points (e.g., `main()`, `load_file()`).
*   **Arguments**: Always provide explicit `start_msg` and `end_msg` in English.

### 4. Naming Conventions (Logger Names)

| Module | Logger Name |
| :--- | :--- |
| `main.py` | `MainEntry` |
| `config.py` | `Config` |
| `file_loader_service.py` | `FileLoader` |
| `vtk_render_service.py` | `VTKRender` |
| `pipeline_viewmodel.py` | `PipelineVM` |
| `vtk_viewmodel.py` | `VTKVM` |
| `chat_viewmodel.py` | `ChatVM` |
| `agent/graph.py` | `AgentGraph` |
| `agent/tools/*.py` | `AgentTools` |
| `filters/*.py` | `FilterOps` |

## Forbidden Patterns

*   ❌ Logging inside render loops (e.g., VTK render call).
*   ❌ Logging inside frequently called property getters/setters.
*   ❌ Using `print()` statements (Use `logger` instead).
*   ❌ Logging large objects or binary data contents.
