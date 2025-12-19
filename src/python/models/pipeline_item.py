from dataclasses import dataclass, field
from typing import Any
import uuid


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
    
    def get_info_string(self) -> str:
        """Generate information string about this item."""
        lines = [f"Name: {self.name}", f"Type: {self.item_type}"]
        
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

