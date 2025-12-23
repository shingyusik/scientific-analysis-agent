from abc import ABC, abstractmethod
from typing import Any, Tuple, Optional, List
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from models.pipeline_item import PipelineItem
from services.vtk_render_service import VTKRenderService


class FilterBase(ABC):
    """Base class for all filters."""
    
    def __init__(self, render_service: VTKRenderService):
        self._render_service = render_service
    
    @property
    @abstractmethod
    def filter_type(self) -> str:
        """Return the filter type identifier (e.g., 'slice_filter')."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Return the display name for the filter (e.g., 'Slice')."""
        pass
    
    @abstractmethod
    def apply_filter(self, data: Any, params: dict) -> Tuple[Any, Any]:
        """
        Apply the filter to data.
        
        Args:
            data: Input VTK data
            params: Filter parameters dictionary
            
        Returns:
            Tuple of (actor, output_data)
        """
        pass
    
    @abstractmethod
    def create_default_params(self) -> dict:
        """Create default parameters for the filter."""
        pass
    
    @abstractmethod
    def create_params_widget(self, parent: QWidget, item: Optional[PipelineItem] = None,
                            parent_bounds: Optional[Tuple[float, ...]] = None) -> Optional[QWidget]:
        """
        Create a widget for editing filter parameters.
        
        Args:
            parent: Parent widget
            item: Current pipeline item (if editing existing filter)
            parent_bounds: Bounds of parent data (for range calculations)
            
        Returns:
            QWidget for parameter editing, or None if no parameters needed
        """
        pass
    
    def get_params_changed_signal(self, widget: QWidget) -> Optional[Signal]:
        """
        Get the signal emitted when parameters change.
        
        Args:
            widget: The parameter widget created by create_params_widget
            
        Returns:
            Signal that emits (item_id, params_dict), or None
        """
        return None
    
    def validate_params(self, params: dict) -> Tuple[bool, str]:
        """
        Validate filter parameters.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, ""
    
    def get_plane_preview_params(self, params: dict) -> Optional[Tuple[List[float], List[float], bool]]:
        """
        Get plane preview parameters for visualization.
        
        Args:
            params: Filter parameters dictionary
            
        Returns:
            Tuple of (origin, normal, show_preview) or None if no preview supported
        """
        return None

