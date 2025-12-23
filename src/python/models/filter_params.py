from dataclasses import dataclass, field
from typing import List


@dataclass
class SliceParams:
    """Parameters for slice filter."""
    
    origin: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    normal: List[float] = field(default_factory=lambda: [1.0, 0.0, 0.0])
    offsets: List[float] = field(default_factory=lambda: [0.0])
    show_preview: bool = True
    
    def to_dict(self) -> dict:
        return {
            "origin": self.origin.copy(),
            "normal": self.normal.copy(),
            "offsets": self.offsets.copy(),
            "show_preview": self.show_preview,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "SliceParams":
        return cls(
            origin=data.get("origin", [0.0, 0.0, 0.0]),
            normal=data.get("normal", [1.0, 0.0, 0.0]),
            offsets=data.get("offsets", [0.0]),
            show_preview=data.get("show_preview", True),
        )


@dataclass
class ContourParams:
    """Parameters for contour filter."""
    
    values: List[float] = field(default_factory=lambda: [0.5])
    array_name: str | None = None
    
    def to_dict(self) -> dict:
        return {
            "values": self.values.copy(),
            "array_name": self.array_name,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "ContourParams":
        return cls(
            values=data.get("values", [0.5]),
            array_name=data.get("array_name"),
        )

