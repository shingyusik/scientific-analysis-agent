from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple
import uuid


@dataclass
class ColorByInfo:
    """Information about current color by setting."""
    array_name: str = "__SolidColor__"
    array_type: str = "POINT"
    component: str = ""
    
    @property
    def is_solid_color(self) -> bool:
        return self.array_name == "__SolidColor__"


@dataclass
class PipelineItem:
    """Represents a single item in the visualization pipeline."""
    
    name: str
    item_type: str  # "source", "slice_filter", "contour_filter", etc.
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    vtk_data: Any = None
    actor: Any = None
    visible: bool = True
    parent_id: str | None = None
    filter_params: dict = field(default_factory=dict)
    color_by: ColorByInfo = field(default_factory=ColorByInfo)
    
    is_time_series: bool = False
    time_steps: List[Any] = field(default_factory=list)
    time_file_paths: List[str] = field(default_factory=list)
    current_time_index: int = 0
    
    @property
    def time_step_count(self) -> int:
        """Get total number of time steps."""
        return len(self.time_steps) if self.time_steps else 0
    
    @property
    def max_time_index(self) -> int:
        """Get maximum valid time index."""
        return max(0, self.time_step_count - 1)
    
    def set_time_index(self, index: int) -> bool:
        """
        Set current time index and update vtk_data.
        
        Returns:
            True if index changed, False otherwise
        """
        if not self.is_time_series or not self.time_steps:
            return False
        
        index = max(0, min(index, self.max_time_index))
        if index == self.current_time_index:
            return False
        
        self.current_time_index = index
        self.vtk_data = self.time_steps[index]
        return True
    
    def get_info_string(self) -> str:
        """Generate information string about this item."""
        lines = [f"Name: {self.name}", f"Type: {self.item_type}"]
        
        if self.is_time_series:
            lines.append(f"Time Series: {self.time_step_count} steps")
            lines.append(f"Current Step: {self.current_time_index}")
        
        if self.vtk_data:
            try:
                data = self.vtk_data
                lines.append(f"Number of Points: {data.GetNumberOfPoints()}")
                lines.append(f"Number of Cells: {data.GetNumberOfCells()}")
                
                bounds = data.GetBounds()
                lines.append(f"Bounds: X[{bounds[0]:.4g}, {bounds[1]:.4g}] "
                           f"Y[{bounds[2]:.4g}, {bounds[3]:.4g}] "
                           f"Z[{bounds[4]:.4g}, {bounds[5]:.4g}]")
                
                pt_data = data.GetPointData()
                cell_data = data.GetCellData()
                pt_arrays = [pt_data.GetArrayName(i) for i in range(pt_data.GetNumberOfArrays())]
                cell_arrays = [cell_data.GetArrayName(i) for i in range(cell_data.GetNumberOfArrays())]
                
                lines.append(f"Point Arrays: {', '.join(pt_arrays) if pt_arrays else 'None'}")
                lines.append(f"Cell Arrays: {', '.join(cell_arrays) if cell_arrays else 'None'}")
            except Exception as e:
                lines.append(f"Error extracting info: {e}")
        
        return "\n".join(lines)

