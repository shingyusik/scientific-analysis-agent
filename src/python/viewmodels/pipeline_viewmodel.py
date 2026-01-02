from PySide6.QtCore import QObject, Signal
from typing import Optional, List, Dict, Any
from models.pipeline_item import PipelineItem
from services.vtk_render_service import VTKRenderService
from services.file_loader_service import FileLoaderService
import filters
from utils.logger import get_logger, log_execution

logger = get_logger("PipelineVM")


class PipelineViewModel(QObject):
    """ViewModel for managing the visualization pipeline."""
    
    item_added = Signal(object)  # PipelineItem
    item_removed = Signal(str)   # item_id
    item_updated = Signal(object)  # PipelineItem
    selection_changed = Signal(object)  # PipelineItem or None
    message = Signal(str)  # Status messages
    time_series_loaded = Signal(object)  # PipelineItem with time series
    
    def __init__(self, render_service: VTKRenderService, file_loader: FileLoaderService):
        super().__init__()
        self._render_service = render_service
        self._file_loader = file_loader
        self._items: dict[str, PipelineItem] = {}
        self._selected_id: Optional[str] = None
        self._filter_instances: Dict[str, Any] = {}
    
    @property
    def items(self) -> dict[str, PipelineItem]:
        return self._items
    
    @property
    def selected_item(self) -> Optional[PipelineItem]:
        if self._selected_id:
            return self._items.get(self._selected_id)
        return None
    
    @property
    def render_service(self) -> VTKRenderService:
        return self._render_service
    
    def get_filter(self, filter_type: str):
        """Get or create a filter instance."""
        if filter_type not in self._filter_instances:
            filter_class = filters.get_filter(filter_type)
            if filter_class:
                self._filter_instances[filter_type] = filter_class(self._render_service)
        return self._filter_instances.get(filter_type)
    
    def get_available_filters(self) -> List[tuple]:
        """Get list of (filter_type, display_name) for all registered filters."""
        result = []
        for filter_type in filters.get_all_filter_types():
            filter_instance = self.get_filter(filter_type)
            if filter_instance:
                result.append((filter_type, filter_instance.display_name))
        return result
    
    def select_item(self, item_id: Optional[str]) -> None:
        """Select a pipeline item."""
        self._selected_id = item_id
        self.selection_changed.emit(self.selected_item)
    
    def add_source(self, name: str, vtk_data, actor, item_type: str = "source", 
                   parent_id: str = None, color_by: "ColorByInfo" = None) -> PipelineItem:
        """Add a new source to the pipeline."""
        from models.pipeline_item import ColorByInfo
        
        item = PipelineItem(
            name=name,
            item_type=item_type,
            vtk_data=vtk_data,
            actor=actor,
            parent_id=parent_id,
            color_by=color_by if color_by else ColorByInfo(),
        )
        self._items[item.id] = item
        self.item_added.emit(item)
        logger.info(f"Source Added: {name} ({item.id})")
        return item
    
    @log_execution(start_msg="Creating Cone Source", end_msg="Cone Source Created")
    def create_cone_source(self) -> PipelineItem:
        """Create default cone source."""
        from models.pipeline_item import ColorByInfo
        
        actor, data = self._render_service.create_cone_source()
        color_by = ColorByInfo(array_name="Elevation", array_type="POINT", component="")
        self._render_service.set_color_by(actor, "Elevation", "POINT", "")
        item = self.add_source("Cone Source", data, actor, "source", color_by=color_by)
        return item
    
    @log_execution(start_msg="Loading File", end_msg="File Loaded")
    def load_file(self, file_path: str, check_time_series: bool = True) -> Optional[PipelineItem]:
        """Load a VTK file and add to pipeline."""
        try:
            if check_time_series:
                series_files = self._file_loader.detect_time_series(file_path)
                if series_files and len(series_files) > 1:
                    return self.load_time_series(series_files)
            
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
    
    @log_execution(start_msg="Loading Time Series File", end_msg="Time Series File Loaded")
    def load_time_series(self, file_paths: List[str]) -> Optional[PipelineItem]:
        """Load a time series of VTK files and add to pipeline."""
        try:
            self.message.emit(f"Loading time series ({len(file_paths)} files)...")
            
            data_list, series_name, sorted_paths = self._file_loader.load_time_series(file_paths)
            
            first_data = data_list[0]
            actor = self._render_service.create_actor_for_file(first_data)
            
            mapper = actor.GetMapper()
            if mapper:
                mapper.CreateDefaultLookupTable()
                if first_data.GetScalarRange():
                    mapper.SetScalarRange(first_data.GetScalarRange())
            
            item = PipelineItem(
                name=series_name,
                item_type="time_series_source",
                vtk_data=first_data,
                actor=actor,
                is_time_series=True,
                time_steps=data_list,
                time_file_paths=sorted_paths,
                current_time_index=0,
            )
            self._items[item.id] = item
            self.item_added.emit(item)
            self.time_series_loaded.emit(item)
            
            self.message.emit(f"Loaded time series: {series_name} ({len(sorted_paths)} steps)")
            return item
        except Exception as e:
            self.message.emit(f"Error loading time series: {e}")
            return None
    
    def update_time_step(self, item_id: str, time_index: int) -> None:
        """Update item to show specific time step."""
        item = self._items.get(item_id)
        if not item or not item.is_time_series:
            return
        
        item.set_time_index(time_index)
        
        if item.actor and item.vtk_data:
            mapper = item.actor.GetMapper()
            if mapper:
                mapper.SetInputData(item.vtk_data)
                mapper.Modified()
        
        self.item_updated.emit(item)
    
    @log_execution(start_msg="Applying Filter", end_msg="Filter Applied")
    def apply_filter(self, filter_type: str, parent_id: str, 
                     params: dict = None) -> Optional[PipelineItem]:
        """Apply a filter to a parent item using the filter registry."""
        import vtk
        
        parent = self._items.get(parent_id)
        if not parent or not parent.vtk_data:
            self.message.emit("Please select a valid source.")
            return None
        
        filter_instance = self.get_filter(filter_type)
        if not filter_instance:
            self.message.emit(f"Unknown filter type: {filter_type}")
            return None
        
        if params is None:
            params = filter_instance.create_default_params()
            if hasattr(parent.vtk_data, 'GetCenter'):
                center = parent.vtk_data.GetCenter()
                if 'origin' in params:
                    params['origin'] = list(center)
        
        if filter_instance.apply_immediately:
            actor, filtered_data = filter_instance.apply_filter(parent.vtk_data, params)
        else:
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputData(parent.vtk_data)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(1, 1, 1)
            filtered_data = parent.vtk_data
        
        item = PipelineItem(
            name=f"{filter_instance.display_name} ({parent.name})",
            item_type=filter_type,
            vtk_data=filtered_data,
            actor=actor,
            parent_id=parent_id,
            filter_params=params,
        )
        self._items[item.id] = item
        self.item_added.emit(item)
        
        if filter_instance.apply_immediately:
            self.message.emit(f"Applied {filter_instance.display_name} filter to {parent.name}.")
        else:
            self.message.emit(f"Created {filter_instance.display_name} filter. Click Apply to execute.")
        return item
    
    def update_filter_params(self, item_id: str, params: dict) -> None:
        """Update filter parameters (preview only, not applied yet)."""
        item = self._items.get(item_id)
        if not item or "filter" not in item.item_type:
            return
        
        item.filter_params.update(params)
        self.item_updated.emit(item)
    
    @log_execution(start_msg="Committing Filter", end_msg="Filter Committed")
    def commit_filter(self, item_id: str) -> None:
        """Apply filter changes using current parameters."""
        item = self._items.get(item_id)
        if not item or "filter" not in item.item_type:
            return
        
        parent = self._items.get(item.parent_id)
        if not parent or not parent.vtk_data:
            return
        
        filter_instance = self.get_filter(item.item_type)
        if not filter_instance:
            return
        
        self.message.emit(f"Recalculating {filter_instance.display_name}...")
        
        _, filtered_data = filter_instance.apply_filter(parent.vtk_data, item.filter_params)
        item.vtk_data = filtered_data
        item.actor.GetMapper().SetInputData(filtered_data)
        self.message.emit("Filter applied.")
        self.item_updated.emit(item)
    
    @log_execution(start_msg="Deleting Item", end_msg="Item Deleted")
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
    
    def set_color_by(self, item_id: str, array_name: str, array_type: str = 'POINT', component: str = '') -> None:
        """Set coloring by scalar array."""
        from models.pipeline_item import ColorByInfo
        
        item = self._items.get(item_id)
        if item and item.actor:
            self._render_service.set_color_by(item.actor, array_name, array_type, component)
            item.color_by = ColorByInfo(array_name=array_name, array_type=array_type, component=component)
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
    
    def get_root_source_id(self, item_id: str) -> Optional[str]:
        """Get the root source ID for an item by traversing up the parent chain."""
        item = self._items.get(item_id)
        if not item:
            return None
        
        while item.parent_id:
            parent = self._items.get(item.parent_id)
            if not parent:
                break
            item = parent
        
        return item.id