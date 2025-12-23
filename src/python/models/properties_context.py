from dataclasses import dataclass, field
from typing import List, Tuple, Any, Optional


@dataclass
class PropertiesPanelContext:
    """Context data for PropertiesPanel display."""
    
    style: str = "Surface"
    data_arrays: List[Tuple[str, str]] = field(default_factory=list)
    current_array: Optional[str] = None
    scalar_visible: bool = False
    
    @classmethod
    def from_item(cls, item: Any, vtk_vm: Any) -> "PropertiesPanelContext":
        """Create context from a pipeline item."""
        if not item or not item.actor:
            return cls()
        
        style = vtk_vm.get_representation_style(item.actor)
        data_arrays = vtk_vm.get_data_arrays(item.vtk_data) if item.vtk_data else []
        
        current_array = None
        scalar_visible = False
        
        mapper = item.actor.GetMapper()
        if mapper:
            current_array = mapper.GetArrayName()
            scalar_visible = mapper.GetScalarVisibility()
        
        return cls(
            style=style,
            data_arrays=data_arrays,
            current_array=current_array,
            scalar_visible=scalar_visible,
        )

