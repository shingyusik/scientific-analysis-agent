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
        self._ax.clear()
        
        info = self._viewmodel.get_info()
        source_count = info.get("source_count", 0)
        
        if source_count == 0:
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
            
        try:
            # Delegate rendering to ViewModel which handles multiple sources
            self._viewmodel._render_plot(self._ax)
            
            # Tight layout
            self._figure.tight_layout()
            self._canvas.draw()
            
            # Update info label
            graph_type = info.get("graph_type", "Unknown").capitalize()
            self._info_label.setText(f"Type: {graph_type} | Sources: {source_count}")
            self._export_btn.setEnabled(True)
            
            logger.info(f"Plot updated: {graph_type} with {source_count} sources")
            
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
