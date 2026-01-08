from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                                QPushButton, QFileDialog, QMessageBox, QSizePolicy)
from PySide6.QtCore import Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from viewmodels.graph_viewmodel import GraphViewModel
from utils.logger import get_logger

logger = get_logger("GraphViewWidget")


class GraphViewWidget(QWidget):
    """Widget for displaying matplotlib graphs from VTK data."""
    
    export_requested = Signal(str)  # format: png, jpg, svg, pdf
    
    def __init__(self, viewmodel: GraphViewModel, parent: QWidget = None):
        super().__init__(parent)
        self._viewmodel = viewmodel
        
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self) -> None:
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Info bar
        info_layout = QHBoxLayout()
        self._info_label = QLabel("No data loaded")
        self._info_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        info_layout.addWidget(self._info_label)
        
        self._export_btn = QPushButton("Export to Image")
        self._export_btn.clicked.connect(self._on_export_clicked)
        self._export_btn.setEnabled(False)
        info_layout.addWidget(self._export_btn)
        
        layout.addLayout(info_layout)
        
        # Matplotlib figure
        self._figure = Figure(figsize=(8, 6))
        self._canvas = FigureCanvas(self._figure)
        self._canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Navigation toolbar for zoom/pan
        self._toolbar = NavigationToolbar(self._canvas, self)
        
        layout.addWidget(self._toolbar)
        layout.addWidget(self._canvas)
        
        # Initialize with empty plot
        self._ax = self._figure.add_subplot(111)
        self._ax.text(0.5, 0.5, 'No data loaded', 
                     horizontalalignment='center',
                     verticalalignment='center',
                     transform=self._ax.transAxes,
                     fontsize=14, color='gray')
        self._ax.set_xticks([])
        self._ax.set_yticks([])
        self._canvas.draw()
        
    def _connect_signals(self) -> None:
        """Connect viewmodel signals."""
        self._viewmodel.plot_config_updated.connect(self._update_plot)
        
    def _update_plot(self) -> None:
        """Update plot display from viewmodel configuration."""
        config = self._viewmodel.get_plot_config()
        
        x_data = config.get("x_data")
        y_data = config.get("y_data")
        
        if x_data is None or y_data is None:
            # Clear plot
            self._ax.clear()
            self._ax.text(0.5, 0.5, 'No data loaded', 
                         horizontalalignment='center',
                         verticalalignment='center',
                         transform=self._ax.transAxes,
                         fontsize=14, color='gray')
            self._ax.set_xticks([])
            self._ax.set_yticks([])
            self._canvas.draw()
            self._info_label.setText("No data loaded")
            self._export_btn.setEnabled(False)
            return
        
        # Render based on graph type
        graph_type = config.get("graph_type", "line")
        
        try:
            # Check if we can do a fast update (same graph type, existing plot)
            # Only supported for line plots for now
            can_fast_update = (
                graph_type == "line" 
                and len(self._ax.lines) > 0 
                and self._ax.get_title() == config.get("title", "")
                and self._ax.get_xlabel() == config.get("x_label", "X")
                and self._ax.get_ylabel() == config.get("y_label", "Y")
            )

            if can_fast_update:
                # Fast update: just set new data
                line = self._ax.lines[0]
                line.set_data(x_data, y_data)
                
                # Update styling if needed (usually less frequent)
                line.set_color(config.get("line_color", "blue"))
                line.set_linewidth(config.get("line_width", 1.5))
                marker = config.get("marker_style")
                line.set_marker(marker if marker != "none" else None)
                line.set_markersize(config.get("marker_size", 5.0))
                
                # Rescale axes
                self._ax.relim()
                self._ax.autoscale_view()
                
                # Update legend label
                if config.get("show_legend", False) and self._ax.get_legend():
                    line.set_label(config.get("y_label", "Data"))
                    self._ax.legend()
                    
                self._canvas.draw()
                
            else:
                # Full redraw (fallback for other types or major changes)
                self._ax.clear()
                
                if graph_type == "line":
                    self._ax.plot(
                        x_data,
                        y_data,
                        color=config.get("line_color", "blue"),
                        linewidth=config.get("line_width", 1.5),
                        marker=config.get("marker_style") if config.get("marker_style") != "none" else None,
                        markersize=config.get("marker_size", 5.0),
                        label=config.get("y_label", "Data")
                    )
                elif graph_type == "scatter":
                    marker = config.get("marker_style", "o")
                    if marker == "none":
                        marker = "o"
                    self._ax.scatter(
                        x_data,
                        y_data,
                        c=config.get("line_color", "blue"),
                        s=config.get("marker_size", 5.0) * 10,
                        marker=marker,
                        label=config.get("y_label", "Data")
                    )
                elif graph_type == "histogram":
                    self._ax.hist(
                        y_data,
                        bins=30,
                        color=config.get("line_color", "blue"),
                        alpha=0.7,
                        label=config.get("y_label", "Data")
                    )
                elif graph_type == "bar":
                    self._ax.bar(
                        x_data,
                        y_data,
                        color=config.get("line_color", "blue"),
                        label=config.get("y_label", "Data")
                    )
                
                # Apply styling
                title = config.get("title", "")
                if title:
                    self._ax.set_title(title, fontsize=12, fontweight='bold')
                
                self._ax.set_xlabel(config.get("x_label", "X"), fontsize=10)
                self._ax.set_ylabel(config.get("y_label", "Y"), fontsize=10)
                
                if config.get("show_grid", True):
                    self._ax.grid(True, alpha=0.3, linestyle='--')
                
                if config.get("show_legend", False):
                    self._ax.legend()
                
                # Tight layout to prevent label cutoff
                self._figure.tight_layout()
                self._canvas.draw()
            
            # Update info label
            info = self._viewmodel.get_info()
            graph_type_display = info.get("graph_type", "Unknown").capitalize()
            data_points = info.get("data_points", 0)
            self._info_label.setText(f"Type: {graph_type_display} | Points: {data_points:,}")
            self._export_btn.setEnabled(True)
            
            logger.info(f"Plot updated: {graph_type} with {data_points} points (Fast update: {can_fast_update})")
            
        except Exception as e:
            logger.error(f"Failed to render plot: {e}")
            self._ax.clear()
            self._ax.text(0.5, 0.5, f'Error rendering plot:\n{str(e)}', 
                         horizontalalignment='center',
                         verticalalignment='center',
                         transform=self._ax.transAxes,
                         fontsize=10, color='red')
            self._canvas.draw()
            self._export_btn.setEnabled(False)
        
    def _on_export_clicked(self) -> None:
        """Handle export button click."""
        info = self._viewmodel.get_info()
        if info.get("data_points", 0) == 0:
            return
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export Graph",
            "",
            "PNG Image (*.png);;JPEG Image (*.jpg);;SVG Vector (*.svg);;PDF Document (*.pdf)"
        )
        
        if not file_path:
            return
        
        # Determine format from filter if extension not provided
        if not any(file_path.endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.svg', '.pdf']):
            if "PNG" in selected_filter:
                file_path += '.png'
            elif "JPEG" in selected_filter:
                file_path += '.jpg'
            elif "SVG" in selected_filter:
                file_path += '.svg'
            elif "PDF" in selected_filter:
                file_path += '.pdf'
            else:
                file_path += '.png'  # Default
        
        success = self._viewmodel.export_to_image(file_path, dpi=150)
        
        if success:
            QMessageBox.information(self, "Export Successful", f"Graph exported to:\n{file_path}")
            # Extract format from extension
            fmt = file_path.split('.')[-1].lower()
            self.export_requested.emit(fmt)
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export graph.")
    
    @property
    def viewmodel(self) -> GraphViewModel:
        """Get the viewmodel instance."""
        return self._viewmodel

    def clear_data(self) -> None:
        """Clear the graph data."""
        self._ax.clear()
        self._ax.text(0.5, 0.5, 'No data loaded', 
                     horizontalalignment='center',
                     verticalalignment='center',
                     transform=self._ax.transAxes,
                     fontsize=14, color='gray')
        self._ax.set_xticks([])
        self._ax.set_yticks([])
        self._canvas.draw()
        self._info_label.setText("No data loaded")
        self._export_btn.setEnabled(False)
        self._viewmodel.clear()  # Use proper ViewModel method

    def set_data_visibility(self, visible: bool) -> None:
        """Set visibility of data (dims the graph if hidden)."""
        opacity = 1.0 if visible else 0.3
        self._canvas.setWindowOpacity(opacity) # Visual feedback
        self._canvas.setEnabled(visible)
        self._toolbar.setEnabled(visible)
        self._info_label.setEnabled(visible)
        self._export_btn.setEnabled(visible and self._viewmodel.get_info().get("data_points", 0) > 0)
