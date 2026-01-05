# Test Coverage Plan & Recommended Structure

## Tests Folder Structure
I recommend mirroring the `src/python` structure within `tests` directory. This makes it easy to locate tests for specific modules.

```text
tests/
├── conftest.py                 # Shared fixtures (QApplication, Mocks)
├── unit/                       # Unit tests (Isolated)
│   ├── agent/
│   │   ├── tools/
│   │   │   ├── test_interaction.py
│   │   │   └── test_loader.py
│   │   ├── test_graph.py
│   │   └── test_state.py
│   ├── filters/
│   │   ├── test_slice_filter.py
│   │   └── test_clip_filter.py
│   ├── services/
│   │   ├── test_file_loader_service.py
│   │   └── test_vtk_render_service.py
│   ├── utils/
│   │   ├── test_logger.py      # Existing
│   │   └── test_tool_registry.py # Existing
│   └── viewmodels/
│       ├── test_pipeline_viewmodel.py # Existing
│       ├── test_chat_viewmodel.py
│       └── test_vtk_viewmodel.py
└── integration/                # Integration tests (Combined)
    └── test_workflow.py        # e.g. Load file -> Apply Filter -> Verify output
```

## Prioritized Test List

### 1. High Priority (Core Infrastructure & Logic)
These components are fundamental to the application's function. Failures here break everything.

*   **[ ] `src/python/services/file_loader_service.py`**
    *   **Why**: Handles reading files (vtp, vtu, etc.) and time series detection.
    *   **Test Cases**:
        *   Load single file (mocked VTK reader).
        *   Detect time series (regex patterns for filenames).
        *   Handle missing files or invalid formats.

*   **[ ] `src/python/services/vtk_render_service.py`**
    *   **Why**: Wraps VTK complexity. Controls actors, mappers, and camera.
    *   **Test Cases**:
        *   Create actor from dataset.
        *   Wait/Get scalar range.
        *   Camera reset logic (mocking bounds).

*   **[ ] `src/python/filters/*.py` (Slice, Clip)**
    *   **Why**: The main scientific analysis value add.
    *   **Test Cases**:
        *   **Slice**: Update normal/origin, verify `vtkCutter` parameters update.
        *   **Clip**: Update plane, verify input/output connection.
        *   Verify `create_default_params`.

### 2. Medium Priority (Agent & Interaction)
Components that manage the "intelligence" and user flow.

*   **[ ] `src/python/agent/graph.py`**
    *   **Why**: Defines the LangGraph workflow.
    *   **Test Cases**:
        *   Verify state transitions (Router logic).
        *   Verify tool node execution (mocks).

*   **[ ] `src/python/agent/tools/*.py`**
    *   **Why**: The actual tools the LLM calls.
    *   **Test Cases**:
        *   `loader.py`: `load_data` tool wrapping.
        *   `interaction.py`: `reset_camera` wrapping.

*   **[ ] `src/python/viewmodels/chat_viewmodel.py`**
    *   **Why**: Handles message history and streaming updates for UI.
    *   **Test Cases**:
        *   Add user message / append agent stream.
        *   Clear history logic.
        *   Handle stop signal.

### 3. Low Priority (UI Views & Pure Data Models)
*   **[ ] `src/python/views/*.py`**: Hard to unit test (requires GUI interaction). Best left for manual verification or specialized integration tests later.
*   **[ ] `src/python/models/*.py`**: Mostly dataclasses, implicitly tested by others.

## Next Steps recommendations
1.  Restructure `tests/` folder to `tests/unit/utils`, `tests/unit/viewmodels` and move existing files.
2.  Start with **Services** tests (FileLoader).
