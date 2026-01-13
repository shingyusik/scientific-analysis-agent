from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from typing import Optional, List, Any
import numpy as np

from utils.logger import get_logger

logger = get_logger("TableDataModel")


class TableDataModel(QAbstractTableModel):
    """
    High-performance table model using NumPy arrays for large datasets.
    
    This model provides on-demand data rendering (virtualization) which significantly
    improves performance when displaying large tables compared to QTableWidget.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: Optional[np.ndarray] = None
        self._headers: List[str] = []
        self._sort_column: int = -1
        self._sort_order: Qt.SortOrder = Qt.AscendingOrder
        
    def set_data(self, data: Optional[np.ndarray], headers: List[str]) -> None:
        """
        Set the table data and headers.
        
        Parameters:
            data: NumPy array of shape (rows, columns)
            headers: List of column header names
        """
        self.beginResetModel()
        self._data = data
        self._headers = headers
        self._sort_column = -1
        self.endResetModel()
        
        if data is not None:
            logger.info(f"TableDataModel loaded: {data.shape[0]} rows, {data.shape[1]} columns")
        else:
            logger.info("TableDataModel cleared")
    
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows."""
        if parent.isValid() or self._data is None:
            return 0
        return self._data.shape[0]
    
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns."""
        if parent.isValid() or self._data is None:
            return 0
        return self._data.shape[1]
    
    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """
        Return data for the given index and role.
        
        This method is called on-demand for visible cells only.
        """
        if not index.isValid() or self._data is None:
            return None
        
        row = index.row()
        col = index.column()
        
        if row < 0 or row >= self._data.shape[0] or col < 0 or col >= self._data.shape[1]:
            return None
        
        if role == Qt.DisplayRole:
            value = self._data[row, col]
            
            # Format the value for display
            if isinstance(value, (np.floating, float)):
                return f"{value:.6g}"  # Scientific notation for large/small numbers
            else:
                return str(value)
        
        elif role == Qt.TextAlignmentRole:
            value = self._data[row, col]
            
            # Right-align numbers, left-align text
            if isinstance(value, (np.integer, np.floating, int, float)):
                return Qt.AlignRight | Qt.AlignVCenter
            else:
                return Qt.AlignLeft | Qt.AlignVCenter
        
        return None
    
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Return header data for the given section."""
        if role != Qt.DisplayRole:
            return None
        
        if orientation == Qt.Horizontal:
            if 0 <= section < len(self._headers):
                return self._headers[section]
        else:  # Vertical (row numbers)
            return str(section)
        
        return None
    
    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """
        Sort the table by the given column.
        
        Parameters:
            column: Column index to sort by
            order: Qt.AscendingOrder or Qt.DescendingOrder
        """
        if self._data is None or column < 0 or column >= self._data.shape[1]:
            return
        
        self.layoutAboutToBeChanged.emit()
        
        # Get the sort indices
        sort_indices = np.argsort(self._data[:, column])
        
        if order == Qt.DescendingOrder:
            sort_indices = sort_indices[::-1]
        
        # Reorder the data
        self._data = self._data[sort_indices]
        
        self._sort_column = column
        self._sort_order = order
        
        self.layoutChanged.emit()
        logger.info(f"Table sorted by column {column} ({'ascending' if order == Qt.AscendingOrder else 'descending'})")
    
    def get_data_array(self) -> Optional[np.ndarray]:
        """Return the underlying NumPy array (for export, etc.)."""
        return self._data
    
    def get_headers(self) -> List[str]:
        """Return the column headers."""
        return self._headers
    
    def clear(self) -> None:
        """Clear all data."""
        self.set_data(None, [])
