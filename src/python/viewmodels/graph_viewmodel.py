from PySide6.QtCore import QObject, Signal
from typing import List, Optional, Any, Dict
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy

from utils.logger import get_logger
from utils.app_context import get_pipeline_viewmodel
from utils.vtk_types import VTKArray

logger = get_logger("GraphVM")


class GraphViewModel(QObject):
    """ViewModel for managing graph/chart configurations."""
    
    plot_config_updated = Signal()  # Emitted when plot configuration changes
    
    # Supported graph types
    GRAPH_TYPES = ["line", "scatter", "histogram", "bar"]
    
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._graph_type: str = "line"
        
        # New: Store multiple data sources
        # Key: item_id, Value: dict with data and config
        self._data_sources: Dict[str, Any] = {}
        
        # Current active item for property editing (optional, or handled by UI)
        # We might not need to store "current" here if UI passes it. 
        # But for 'set_data_source' backward compatibility, we'll need to know.
        
        # Plot styling (Global)
        self._title: str = ""
        self._x_label: str = "X"
        self._y_label: str = "Y"
        self._show_grid: bool = True
        self._show_legend: bool = True
        
        # Styling defaults
        self._default_colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
    @property
    def graph_type(self) -> str:
        """Get current graph type."""
        return self._graph_type
    
    def set_graph_type(self, graph_type: str) -> bool:
        """Set graph type (Global)."""
        if graph_type not in self.GRAPH_TYPES:
            logger.error(f"Invalid graph type: {graph_type}")
            return False
        self._graph_type = graph_type
        logger.info(f"Graph type set to: {graph_type}")
        self.plot_config_updated.emit()
        return True
    
    def add_data_source(
        self,
        item_id: str,
        x_array: str = None,
        y_array: str = None,
        array_type: str = None,
        x_component: int = None,
        y_component: int = None,
        line_color: str = None,
        line_width: float = None,
        marker_style: str = None,
        marker_size: float = None
    ) -> bool:
        """Add or update a data source."""
        logger.info(f"Adding/Updating graph source: {item_id}")
        
        pipeline_vm = get_pipeline_viewmodel()
        if not pipeline_vm:
            return False
        
        item = pipeline_vm.items.get(item_id)
        if not item or not item.vtk_data:
            logger.error(f"Item {item_id} not valid")
            return False
            
        # Get existing config if available
        existing = self._data_sources.get(item_id)
        
        # --- Resolve Parameters (Merge incoming with existing or defaults) ---
        
        # 1. Arrays & Data Type
        if y_array is None:
            if existing:
                y_array = existing["y_array"]
                # If reusing Y, reuse Type too unless specified
                if array_type is None: array_type = existing["array_type"]
            else:
                # Default for new source: Pick first available
                data_arrays = item.get_data_arrays()
                if data_arrays:
                    y_array = data_arrays[0][0]
                    if array_type is None: array_type = data_arrays[0][1]
                else:
                    logger.error("No data arrays found")
                    return False
        
        # If array_type is still None (and not set by logic above), default to POINT
        if array_type is None:
            array_type = "POINT"
            
        if x_array is None:
            x_array = existing["x_array"] if existing else "__Index__"
            
        if x_component is None:
            x_component = existing["x_component"] if existing else 0
            
        if y_component is None:
            y_component = existing["y_component"] if existing else 0

        # 2. Styling
        if line_color is None:
            if existing:
                line_color = existing["line_color"]
            else:
                # New source: Cycle colors
                idx = len(self._data_sources) % len(self._default_colors)
                line_color = self._default_colors[idx]
        
        if line_width is None:
            line_width = existing["line_width"] if existing else 1.5
            
        if marker_style is None:
            marker_style = existing["marker_style"] if existing else "o"
            
        if marker_size is None:
            marker_size = existing["marker_size"] if existing else 5.0

        # --- Load Data ---
        vtk_data = item.vtk_data
        if array_type == "POINT":
            data_provider = vtk_data.GetPointData()
            num_tuples = vtk_data.GetNumberOfPoints()
        else:
            data_provider = vtk_data.GetCellData()
            num_tuples = vtk_data.GetNumberOfCells()

        # Extract X
        if x_array == "__Index__":
            x_data = np.arange(num_tuples)
        else:
            x_vtk = data_provider.GetArray(x_array)
            if not x_vtk: 
                return False
            x_data = self._extract_component(x_vtk, x_component, num_tuples)
            
        # Extract Y
        y_vtk = data_provider.GetArray(y_array)
        if not y_vtk:
            return False
        y_data = self._extract_component(y_vtk, y_component, num_tuples)
            
        # Store
        self._data_sources[item_id] = {
            "x_array": x_array,
            "y_array": y_array,
            "array_type": array_type,
            "x_component": x_component,
            "y_component": y_component,
            "x_data": x_data,
            "y_data": y_data,
            "line_color": line_color,
            "line_width": line_width,
            "marker_style": marker_style,
            "marker_size": marker_size
        }
        
        # Update global labels if empty (only for first source usually)
        if not self._y_label or self._y_label == "Y":
             self._y_label = y_array
        
        self.plot_config_updated.emit()
        return True

    def remove_data_source(self, item_id: str) -> None:
        """Remove a data source."""
        if item_id in self._data_sources:
            del self._data_sources[item_id]
            self.plot_config_updated.emit()

    def set_data_source(self, item_id: str, x_array: str, y_array: str, array_type: str = "POINT", x_component: int = 0, y_component: int = 0) -> bool:
        """Legacy compatibility wrapper / Update specific source."""
        # Preserve existing style if present
        style_args = {}
        if item_id in self._data_sources:
            src = self._data_sources[item_id]
            style_args = {
                "line_color": src.get("line_color"),
                "line_width": src.get("line_width"),
                "marker_style": src.get("marker_style"),
                "marker_size": src.get("marker_size")
            }
            
        return self.add_data_source(item_id, x_array, y_array, array_type, x_component, y_component, **style_args)
        
    def refresh_data(self) -> bool:
        """Reload data using current configuration for all sources."""
        if not self._data_sources:
            return False
            
        success_any = False
        # Create a copy of keys to avoid modification during iteration issues if any
        for item_id in list(self._data_sources.keys()):
            src = self._data_sources[item_id]
            # Re-add uses the stored config to re-fetch data
            if self.add_data_source(
                item_id, 
                src["x_array"], 
                src["y_array"], 
                src["array_type"],
                src["x_component"],
                src["y_component"],
                src["line_color"],
                src["line_width"],
                src["marker_style"],
                src["marker_size"]
            ):
                success_any = True
                
        return success_any
    
    def _extract_component(self, vtk_array: VTKArray, component: int, num_tuples: int) -> np.ndarray:
        """Extract a single component from a VTK array."""
        try:
            # Zero-copy conversion to numpy
            np_array = vtk_to_numpy(vtk_array)
            
            num_components = vtk_array.GetNumberOfComponents()
            
            if num_components == 1:
                return np_array
            else:
                # Vector/tensor data - extract specific component using numpy slicing
                if component == -1:
                    # Magnitude
                    return np.linalg.norm(np_array, axis=1)
                elif component < 0 or component >= num_components:
                    logger.warning(f"Invalid component index {component} for array with {num_components} components")
                    return np.zeros(num_tuples)
                return np_array[:, component]
        except Exception as e:
            logger.error(f"Error extracting component: {e}")
            return np.zeros(num_tuples)
    
    def get_plot_config(self, item_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Return matplotlib plot configuration.
        If item_id provided, returns series-specific config.
        Otherwise returns global config.
        """
        config = {
            "graph_type": self._graph_type,
            "title": self._title,
            "x_label": self._x_label,
            "y_label": self._y_label,
            "show_grid": self._show_grid,
            "show_legend": self._show_legend,
        }
        
        if item_id and item_id in self._data_sources:
            src = self._data_sources[item_id]
            config.update({
                "x_array": src["x_array"],
                "y_array": src["y_array"],
                "array_type": src["array_type"],
                "x_component": src["x_component"],
                "y_component": src["y_component"],
                "x_data": src["x_data"],
                "y_data": src["y_data"],
                "line_color": src["line_color"],
                "line_width": src["line_width"],
                "marker_style": src["marker_style"],
                "marker_size": src["marker_size"]
            })
        elif self._data_sources:
             # Fallback: ignore series specific if not requested or return first?
             # Properties panels might fail without keys.
             pass
             
        return config
    
    def set_plot_style(
        self,
        title: Optional[str] = None,
        x_label: Optional[str] = None,
        y_label: Optional[str] = None,
        show_grid: Optional[bool] = None,
        show_legend: Optional[bool] = None,
        line_color: Optional[str] = None,
        line_width: Optional[float] = None,
        marker_style: Optional[str] = None,
        marker_size: Optional[float] = None,
        item_id: Optional[str] = None  # New: Target specific series
    ) -> None:
        """Update plot styling parameters."""
        # Global settings
        if title is not None: self._title = title
        if x_label is not None: self._x_label = x_label
        if y_label is not None: self._y_label = y_label
        if show_grid is not None: self._show_grid = show_grid
        if show_legend is not None: self._show_legend = show_legend
        
        # Series settings
        if item_id and item_id in self._data_sources:
            src = self._data_sources[item_id]
            if line_color is not None: src["line_color"] = line_color
            if line_width is not None: src["line_width"] = line_width
            if marker_style is not None: src["marker_style"] = marker_style
            if marker_size is not None: src["marker_size"] = marker_size
        
        self.plot_config_updated.emit()
    
    def export_to_image(self, file_path: str, dpi: int = 150) -> bool:
        """Export graph to image file."""
        try:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(8, 6))
            self._render_plot(ax)
            
            fig.savefig(file_path, dpi=dpi, bbox_inches='tight')
            plt.close(fig)
            
            logger.info(f"Graph exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export graph: {e}")
            return False
    
    def _render_plot(self, ax) -> None:
        """Render the plot on a matplotlib axes."""
        if not self._data_sources:
            return
            
        pipeline_vm = get_pipeline_viewmodel()
        
        for item_id, src in self._data_sources.items():
            # Check visibility
            if pipeline_vm:
                p_item = pipeline_vm.items.get(item_id)
                if p_item and not p_item.visible:
                    continue
            
            x_data = src["x_data"]
            y_data = src["y_data"]
            label = src["y_array"]
            
            if x_data is None or y_data is None:
                continue

            if self._graph_type == "line":
                ax.plot(
                    x_data, y_data,
                    color=src["line_color"],
                    linewidth=src["line_width"],
                    marker=src["marker_style"] if src["marker_style"] != "none" else None,
                    markersize=src["marker_size"],
                    label=label
                )
            elif self._graph_type == "scatter":
                ax.scatter(
                    x_data, y_data,
                    c=src["line_color"],
                    s=src["marker_size"] * 10,
                    marker=src["marker_style"] if src["marker_style"] != "none" else "o",
                    label=label
                )
            elif self._graph_type == "histogram":
                ax.hist(y_data, bins=30, color=src["line_color"], alpha=0.7, label=label)
            elif self._graph_type == "bar":
                ax.bar(x_data, y_data, color=src["line_color"], label=label)
        
        if self._title:
            ax.set_title(self._title)
        ax.set_xlabel(self._x_label)
        ax.set_ylabel(self._y_label)
        
        if self._show_grid:
            ax.grid(True, alpha=0.3)
        
        if self._show_legend:
            ax.legend()
    
    def clear(self) -> None:
        """Clear all graph data."""
        self._data_sources.clear()
        self.plot_config_updated.emit()
    
    def get_info(self) -> Dict[str, Any]:
        """Get graph information as a dictionary."""
        return {
            "graph_type": self._graph_type,
            "source_count": len(self._data_sources),
            "sources": list(self._data_sources.keys())
        }
