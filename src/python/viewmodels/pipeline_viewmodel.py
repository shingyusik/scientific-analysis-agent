from PySide6.QtCore import QObject, Signal
from typing import Optional, List
from models.pipeline_item import PipelineItem
from models.filter_params import SliceParams
from services.vtk_render_service import VTKRenderService
from services.file_loader_service import FileLoaderService


class PipelineViewModel(QObject):
    """ViewModel for managing the visualization pipeline."""
    
    item_added = Signal(object)  # PipelineItem
    item_removed = Signal(str)   # item_id
    item_updated = Signal(object)  # PipelineItem
    selection_changed = Signal(object)  # PipelineItem or None
    message = Signal(str)  # Status messages
    
    def __init__(self, render_service: VTKRenderService, file_loader: FileLoaderService):
        super().__init__()
        self._render_service = render_service
        self._file_loader = file_loader
        self._items: dict[str, PipelineItem] = {}
        self._selected_id: Optional[str] = None
    
    @property
    def items(self) -> dict[str, PipelineItem]:
        return self._items
    
    @property
    def selected_item(self) -> Optional[PipelineItem]:
        if self._selected_id:
            return self._items.get(self._selected_id)
        return None
    
    def select_item(self, item_id: Optional[str]) -> None:
        """Select a pipeline item."""
        self._selected_id = item_id
        self.selection_changed.emit(self.selected_item)
    
    def add_source(self, name: str, vtk_data, actor, item_type: str = "source", 
                   parent_id: str = None) -> PipelineItem:
        """Add a new source to the pipeline."""
        item = PipelineItem(
            name=name,
            item_type=item_type,
            vtk_data=vtk_data,
            actor=actor,
            parent_id=parent_id,
        )
        self._items[item.id] = item
        self.item_added.emit(item)
        return item
    
    def create_cone_source(self) -> PipelineItem:
        """Create default cone source."""
        actor, data = self._render_service.create_cone_source()
        item = self.add_source("Cone Source", data, actor, "source")
        self._render_service.set_color_by(actor, "Elevation")
        return item
    
    def load_file(self, file_path: str) -> Optional[PipelineItem]:
        """Load a VTK file and add to pipeline."""
        try:
            self.message.emit(f"Loading {file_path}...")
            data, filename = self._file_loader.load(file_path)
            actor = self._render_service.create_actor_for_file(data)
            
            mapper = actor.GetMapper()
            if mapper:
                mapper.CreateDefaultLookupTable()
                if data.GetScalarRange():
                    mapper.SetScalarRange(data.GetScalarRange())
            
            item = self.add_source(filename, data, actor, "file_source")
            self.message.emit(f"Loaded {filename}")
            return item
        except Exception as e:
            self.message.emit(f"Error loading file: {e}")
            return None
    
    def apply_slice(self, parent_id: str, origin: List[float] = None, 
                    normal: List[float] = None, offsets: List[float] = None) -> Optional[PipelineItem]:
        """Apply slice filter to a parent item."""
        parent = self._items.get(parent_id)
        if not parent or not parent.vtk_data:
            self.message.emit("Please select a valid source.")
            return None
        
        if origin is None:
            center = parent.vtk_data.GetCenter()
            origin = list(center)
        if normal is None:
            normal = [1.0, 0.0, 0.0]
        if offsets is None:
            offsets = [0.0]
        
        actor, sliced_data = self._render_service.apply_slice(
            parent.vtk_data, origin, normal, offsets
        )
        
        slice_params = SliceParams(origin=origin, normal=normal, offsets=offsets)
        item = PipelineItem(
            name=f"Slice ({parent.name})",
            item_type="slice_filter",
            vtk_data=sliced_data,
            actor=actor,
            parent_id=parent_id,
            filter_params=slice_params.to_dict(),
        )
        self._items[item.id] = item
        self.item_added.emit(item)
        self.message.emit(f"[C++ Engine] Applied Slice filter to {parent.name}.")
        return item
    
    def update_slice_params(self, item_id: str, origin: List[float] = None, 
                            normal: List[float] = None, offsets: List[float] = None,
                            show_preview: bool = None) -> None:
        """Update slice filter parameters (preview only, not applied yet)."""
        item = self._items.get(item_id)
        if not item or item.item_type != "slice_filter":
            return
        
        params = SliceParams.from_dict(item.filter_params)
        if origin is not None:
            params.origin = origin
        if normal is not None:
            params.normal = normal
        if offsets is not None:
            params.offsets = offsets
        if show_preview is not None:
            params.show_preview = show_preview
        
        item.filter_params = params.to_dict()
        self.item_updated.emit(item)
    
    def commit_filter(self, item_id: str) -> None:
        """Apply filter changes using current parameters."""
        item = self._items.get(item_id)
        if not item:
            return
        
        parent = self._items.get(item.parent_id)
        if not parent or not parent.vtk_data:
            return
        
        if item.item_type == "slice_filter":
            params = SliceParams.from_dict(item.filter_params)
            self.message.emit("[C++ Engine] Recalculating Slice...")
            
            _, sliced_data = self._render_service.apply_slice(
                parent.vtk_data, params.origin, params.normal, params.offsets
            )
            item.vtk_data = sliced_data
            item.actor.GetMapper().SetInputData(sliced_data)
            self.message.emit("Filter applied.")
            self.item_updated.emit(item)
    
    def delete_item(self, item_id: str) -> None:
        """Delete item and its children from pipeline."""
        item = self._items.get(item_id)
        if not item:
            return
        
        children_to_delete = [
            child_id for child_id, child in self._items.items()
            if child.parent_id == item_id
        ]
        for child_id in children_to_delete:
            self.delete_item(child_id)
        
        del self._items[item_id]
        
        if self._selected_id == item_id:
            self._selected_id = None
            self.selection_changed.emit(None)
        
        self.item_removed.emit(item_id)
    
    def set_visibility(self, item_id: str, visible: bool) -> None:
        """Set item visibility."""
        item = self._items.get(item_id)
        if item and item.actor:
            item.visible = visible
            item.actor.SetVisibility(visible)
            self.item_updated.emit(item)
    
    def set_representation(self, item_id: str, style: str) -> None:
        """Set representation style for an item."""
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_representation(item.actor, style)
            self.item_updated.emit(item)
            self.message.emit(f"Set '{item.name}' representation to {style}.")
    
    def set_color_by(self, item_id: str, array_name: str, array_type: str = 'POINT', component: str = 'Magnitude') -> None:
        """Set coloring by scalar array."""
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_color_by(item.actor, array_name, array_type, component)
            self.item_updated.emit(item)
    
    def set_opacity(self, item_id: str, opacity: float) -> None:
        """Set actor opacity."""
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_opacity(item.actor, opacity)
    
    def set_point_size(self, item_id: str, size: float) -> None:
        """Set point size."""
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_point_size(item.actor, size)
    
    def set_line_width(self, item_id: str, width: float) -> None:
        """Set line width."""
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_line_width(item.actor, width)
    
    def set_gaussian_scale(self, item_id: str, scale: float) -> None:
        """Set gaussian scale."""
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_gaussian_scale(item.actor, scale)
    
    def get_parent_item(self, item_id: str) -> Optional[PipelineItem]:
        """Get parent item."""
        item = self._items.get(item_id)
        if item and item.parent_id:
            return self._items.get(item.parent_id)
        return None
    
    def get_children(self, item_id: str) -> List[PipelineItem]:
        """Get child items."""
        return [
            item for item in self._items.values()
            if item.parent_id == item_id
        ]

