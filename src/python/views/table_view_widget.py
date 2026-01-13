from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTableView, QHeaderView, 
                                QMenu, QFileDialog, QMessageBox, QHBoxLayout,
                                QLabel, QPushButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from viewmodels.table_viewmodel import TableViewModel
from models.table_data_model import TableDataModel
from utils.logger import get_logger

logger = get_logger("TableViewWidget")


class TableViewWidget(QWidget):
    """Widget for displaying tabular data from VTK pipeline items."""
    
    export_requested = Signal(str)  # format: csv
    
    def __init__(self, viewmodel: TableViewModel, parent: QWidget = None):
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
        
        self._export_btn = QPushButton("Export to CSV")
        self._export_btn.clicked.connect(self._on_export_clicked)
        self._export_btn.setEnabled(False)
        info_layout.addWidget(self._export_btn)
        
        layout.addLayout(info_layout)
        
        # Table view with model
        self._model = TableDataModel(self)
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        self._table.setSelectionMode(QTableView.ExtendedSelection)
        self._table.setSortingEnabled(True)
        
        # Optimize column resizing for performance
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        
        # Context menu
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self._table)
        
    def _connect_signals(self) -> None:
        """Connect viewmodel signals."""
        self._viewmodel.data_updated.connect(self._update_table)
        
    def _update_table(self) -> None:
        """Update table display from viewmodel data."""
        headers = self._viewmodel.get_column_headers()
        data_array = self._viewmodel.get_table_data()
        
        if not headers or data_array is None or data_array.size == 0:
            self._model.clear()
            self._info_label.setText("No data loaded")
            self._export_btn.setEnabled(False)
            return
        
        # Update the model (this triggers view update automatically)
        self._model.set_data(data_array, headers)
        
        # Resize columns to contents only on first load for better UX
        # (subsequent updates won't resize to avoid jarring experience)
        if self._table.horizontalHeader().sectionSize(0) == 100:  # Default size
            self._table.resizeColumnsToContents()
        
        # Update info label
        info = self._viewmodel.get_info()
        array_name = info.get("array_name", "Unknown")
        row_count = info.get("row_count", 0)
        self._info_label.setText(f"Array: {array_name} | Rows: {row_count:,}")
        self._export_btn.setEnabled(True)
        
        logger.info(f"Table updated: {row_count} rows, {len(headers)} columns")
        
    def _show_context_menu(self, pos) -> None:
        """Show context menu for table operations."""
        menu = QMenu(self)
        
        export_action = QAction("Export to CSV...", self)
        export_action.triggered.connect(self._on_export_clicked)
        export_action.setEnabled(self._viewmodel.get_row_count() > 0)
        menu.addAction(export_action)
        
        menu.exec_(self._table.viewport().mapToGlobal(pos))
        
    def _on_export_clicked(self) -> None:
        """Handle export button click."""
        if self._viewmodel.get_row_count() == 0:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Table Data",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not file_path:
            return
        
        if not file_path.endswith('.csv'):
            file_path += '.csv'
        
        success = self._viewmodel.export_to_csv(file_path)
        
        if success:
            QMessageBox.information(self, "Export Successful", f"Data exported to:\n{file_path}")
            self.export_requested.emit("csv")
        else:
            QMessageBox.critical(self, "Export Failed", "Failed to export table data.")
    
    @property
    def viewmodel(self) -> TableViewModel:
        """Get the viewmodel instance."""
        return self._viewmodel

    def clear_data(self) -> None:
        """Clear the table data."""
        self._model.clear()
        self._info_label.setText("No data loaded")
        self._export_btn.setEnabled(False)
        self._viewmodel.clear()  # Use proper ViewModel method

    def set_data_visibility(self, visible: bool) -> None:
        """Set visibility of data (dims the table if hidden)."""
        opacity = 1.0 if visible else 0.3
        self._table.setWindowOpacity(opacity) # Visual feedback
        self._table.setEnabled(visible)
        self._info_label.setEnabled(visible)
        self._export_btn.setEnabled(visible and self._viewmodel.get_row_count() > 0)
