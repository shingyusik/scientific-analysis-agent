# Scientific Analysis Agent (SA-Agent)

## Overview
SA-Agent is a desktop application combining high-performance VTK 3D visualization with a LangGraph-based AI agent. It allows users to analyze complex numerical analysis data using natural language.

## Features
- **Native Performance**: C++/VTK based high-speed data processing.
- **AI Integration**: Workflow automation using LLM-based agents.
- **Compliance**: Commercial-ready architecture complying with LGPL v3.

## Requirements
- Python 3.10+
- CMake 3.15+
- C++17 compliant compiler
- `uv` for package management

## Build & Run
1. Create a virtual environment:
   ```bash
   uv venv
   ```
2. Activate the environment (Windows):
   ```bash
   .venv\Scripts\activate
   ```
3. Install dependencies and build the project:
   ```bash
   uv pip install .
   ```
4. Run the application:
   ```bash
   uv run python src/python/main.py
   ```
