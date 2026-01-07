from PySide6.QtCore import QObject, Signal
from typing import List, Optional, Any, Dict
import numpy as np
from utils.logger import get_logger
from utils.app_context import get_pipeline_viewmodel

logger = get_logger("GraphVM")


class GraphViewModel(QObject):
    """ViewModel for managing graph/chart configurations."""
    
    plot_config_updated = Signal()  # Emitted when plot configuration changes
    
    # Supported graph types
    GRAPH_TYPES = ["line", "scatter", "histogram", "bar"]
    
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._graph_type: str = "line"
        self._source_item_id: Optional[str] = None
        self._x_array_name: Optional[str] = None
        self._y_array_name: Optional[str] = None
        self._array_type: str = "POINT"  # POINT or CELL
        self._x_component: int = 0  # For vector data
        self._y_component: int = 0
        
        # Plot styling
        self._title: str = ""
        self._x_label: str = "X"
        self._y_label: str = "Y"
        self._show_grid: bool = True
        self._show_legend: bool = True
        self._line_color: str = "blue"
        self._line_width: float = 1.5
        self._marker_style: str = "o"
        self._marker_size: float = 5.0
        
        # Cached data
        self._x_data: Optional[np.ndarray] = None
        self._y_data: Optional[np.ndarray] = None
        
    @property
    def graph_type(self) -> str:
        """Get current graph type."""
        return self._graph_type
    
    def set_graph_type(self, graph_type: str) -> bool:
        """
        Set graph type.
        
        Parameters:
            graph_type: One of GRAPH_TYPES
            
        Returns:
            True if type was set successfully
        """
        if graph_type not in self.GRAPH_TYPES:
            logger.error(f"Invalid graph type: {graph_type}. Must be one of {self.GRAPH_TYPES}")
            return False
        
        self._graph_type = graph_type
        logger.info(f"Graph type set to: {graph_type}")
        self.plot_config_updated.emit()
        return True
    
    def set_data_source(
        self,
        item_id: str,
        x_array: str,
        y_array: str,
        array_type: str = "POINT",
        x_component: int = 0,
        y_component: int = 0
    ) -> bool:
        """
        Configure data source for the graph.
        
        Parameters:
            item_id: Pipeline item ID
            x_array: Name of X-axis data array
            y_array: Name of Y-axis data array
            array_type: 'POINT' or 'CELL' data
            x_component: Component index for X (if vector)
            y_component: Component index for Y (if vector)
            
        Returns:
            True if data was loaded successfully
        """
        logger.info(f"Setting graph data source: item={item_id}, x={x_array}, y={y_array}")
        
        pipeline_vm = get_pipeline_viewmodel()
        if not pipeline_vm:
            logger.error("Pipeline ViewModel not available in app context")
            return False
        
        item = pipeline_vm.items.get(item_id)
        if not item or not item.vtk_data:
            logger.error(f"Item {item_id} not found or has no VTK data")
            return False
        
        vtk_data = item.vtk_data
        
        # Get the appropriate data arrays
        if array_type == "POINT":
            data_arrays = vtk_data.GetPointData()
            num_tuples = vtk_data.GetNumberOfPoints()
        else:  # CELL
            data_arrays = vtk_data.GetCellData()
            num_tuples = vtk_data.GetNumberOfCells()
        
        # Extract X data
        if x_array == "__Index__":
            self._x_data = np.arange(num_tuples)
        else:
            x_vtk_array = data_arrays.GetArray(x_array)
            if not x_vtk_array:
                logger.error(f"X array '{x_array}' not found")
                return False
            self._x_data = self._extract_component(x_vtk_array, x_component, num_tuples)
        
        # Extract Y data
        y_vtk_array = data_arrays.GetArray(y_array)
        if not y_vtk_array:
            logger.error(f"Y array '{y_array}' not found")
            return False
        self._y_data = self._extract_component(y_vtk_array, y_component, num_tuples)
        
        # Store configuration
        self._source_item_id = item_id
        self._x_array_name = x_array
        self._y_array_name = y_array
        self._array_type = array_type
        self._x_component = x_component
        self._y_component = y_component
        
        # Update default labels if not customized
        if self._x_label == "X" or not self._x_label:
            self._x_label = x_array if x_array != "__Index__" else "Index"
        if self._y_label == "Y" or not self._y_label:
            self._y_label = y_array
        
        logger.info(f"Graph data loaded: {len(self._x_data)} points")
        self.plot_config_updated.emit()
        return True
    
    def _extract_component(self, vtk_array, component: int, num_tuples: int) -> np.ndarray:
        """Extract a single component from a VTK array."""
        num_components = vtk_array.GetNumberOfComponents()
        
        if num_components == 1:
            # Scalar data
            return np.array([vtk_array.GetValue(i) for i in range(num_tuples)])
        else:
            # Vector/tensor data - extract specific component
            return np.array([vtk_array.GetTuple(i)[component] for i in range(num_tuples)])
    
    def get_plot_config(self) -> Dict[str, Any]:
        """
        Return matplotlib plot configuration.
        
        Returns:
            Dictionary with plot parameters
        """
        return {
            "graph_type": self._graph_type,
            "x_data": self._x_data,
            "y_data": self._y_data,
            "title": self._title,
            "x_label": self._x_label,
            "y_label": self._y_label,
            "show_grid": self._show_grid,
            "show_legend": self._show_legend,
            "line_color": self._line_color,
            "line_width": self._line_width,
            "marker_style": self._marker_style,
            "marker_size": self._marker_size,
        }
    
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
        marker_size: Optional[float] = None
    ) -> None:
        """Update plot styling parameters."""
        if title is not None:
            self._title = title
        if x_label is not None:
            self._x_label = x_label
        if y_label is not None:
            self._y_label = y_label
        if show_grid is not None:
            self._show_grid = show_grid
        if show_legend is not None:
            self._show_legend = show_legend
        if line_color is not None:
            self._line_color = line_color
        if line_width is not None:
            self._line_width = line_width
        if marker_style is not None:
            self._marker_style = marker_style
        if marker_size is not None:
            self._marker_size = marker_size
        
        self.plot_config_updated.emit()
    
    def export_to_image(self, file_path: str, dpi: int = 150) -> bool:
        """
        Export graph to image file.
        
        Parameters:
            file_path: Output file path (.png, .jpg, .svg, .pdf)
            dpi: Resolution in dots per inch
            
        Returns:
            True if export succeeded
        """
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
        if self._x_data is None or self._y_data is None:
            return
        
        if self._graph_type == "line":
            ax.plot(
                self._x_data,
                self._y_data,
                color=self._line_color,
                linewidth=self._line_width,
                marker=self._marker_style if self._marker_style != "none" else None,
                markersize=self._marker_size,
                label=self._y_array_name
            )
        elif self._graph_type == "scatter":
            ax.scatter(
                self._x_data,
                self._y_data,
                c=self._line_color,
                s=self._marker_size * 10,
                marker=self._marker_style if self._marker_style != "none" else "o",
                label=self._y_array_name
            )
        elif self._graph_type == "histogram":
            ax.hist(self._y_data, bins=30, color=self._line_color, alpha=0.7, label=self._y_array_name)
        elif self._graph_type == "bar":
            ax.bar(self._x_data, self._y_data, color=self._line_color, label=self._y_array_name)
        
        if self._title:
            ax.set_title(self._title)
        ax.set_xlabel(self._x_label)
        ax.set_ylabel(self._y_label)
        
        if self._show_grid:
            ax.grid(True, alpha=0.3)
        
        if self._show_legend and self._y_array_name:
            ax.legend()
    
    def clear(self) -> None:
        """Clear all graph data."""
        self._source_item_id = None
        self._x_array_name = None
        self._y_array_name = None
        self._x_data = None
        self._y_data = None
        self.plot_config_updated.emit()
    
    def get_info(self) -> Dict[str, Any]:
        """Get graph information as a dictionary."""
        return {
            "graph_type": self._graph_type,
            "source_item_id": self._source_item_id,
            "x_array": self._x_array_name,
            "y_array": self._y_array_name,
            "array_type": self._array_type,
            "data_points": len(self._x_data) if self._x_data is not None else 0,
        }
