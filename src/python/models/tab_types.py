"""Constants and enums for the tab system."""
from enum import StrEnum


class TabType(StrEnum):
    """Enumeration of supported tab types."""
    VTK = "vtk"
    TABLE = "table"
    GRAPH = "graph"
