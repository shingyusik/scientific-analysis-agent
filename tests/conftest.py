import sys
import os
from pathlib import Path

# Add src/python to sys.path
src_path = Path(__file__).parent.parent / "src" / "python"
sys.path.append(str(src_path))

import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app
