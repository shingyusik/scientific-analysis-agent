from PySide6.QtCore import QObject, Signal
from typing import List, Optional, Any, Dict
import vtk
import numpy as np
from vtk.util.numpy_support import vtk_to_numpy

from utils.logger import get_logger
from utils.app_context import get_pipeline_viewmodel

logger = get_logger("TableVM")


class TableViewModel(QObject):
    """ViewModel for managing table data extracted from VTK pipeline items."""
    
    data_updated = Signal()  # Emitted when table data changes
    
    def __init__(self, parent: QObject = None):
        super().__init__(parent)
        self._source_item_id: Optional[str] = None
        self._array_type: str = "POINT"  # POINT or CELL
        self._is_visible: bool = True
        self._data_array: Optional[np.ndarray] = None
        self._column_headers: List[str] = []
        
    @property
    def source_item_id(self) -> Optional[str]:
        """Get the source pipeline item ID."""
        return self._source_item_id
        
    def set_visibility(self, visible: bool) -> None:
        """Set the visibility of the table data."""
        if self._is_visible == visible:
            return
            
        self._is_visible = visible
        if visible:
            self.refresh_data()
        else:
            # Clear data visual but keep configuration
            self._data_array = None
            self.data_updated.emit()
    
    def set_data_source(self, item_id: str, array_type: str = "POINT") -> bool:
        """
        Load ALL data arrays from a pipeline item.
        """
        self._source_item_id = item_id
        self._array_type = array_type
        
        if not self._is_visible:
            self._data_array = None
            self.data_updated.emit()
            return True

        logger.info(f"Setting table data source: item={item_id}, type={array_type}")
        
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
        
        if data_arrays.GetNumberOfArrays() == 0:
            logger.error(f"No {array_type} data arrays found")
            return False
        
        # Build column headers and collect data arrays
        self._column_headers = ["Index"]
        
        # Create index array
        cols_data = [np.arange(num_tuples)]
        
        for i in range(data_arrays.GetNumberOfArrays()):
            array = data_arrays.GetArray(i)
            if not array:
                continue
                
            array_name = array.GetName() or f"Array_{i}"
            num_components = array.GetNumberOfComponents()
            
            # Convert VTK array to numpy (zero-copy if possible)
            try:
                np_array = vtk_to_numpy(array)
            except Exception as e:
                logger.warning(f"Failed to convert array {array_name} to numpy: {e}")
                continue
            
            if num_components == 1:
                self._column_headers.append(array_name)
                cols_data.append(np_array)
            elif num_components == 3:
                self._column_headers.extend([f"{array_name}_X", f"{array_name}_Y", f"{array_name}_Z"])
                cols_data.append(np_array[:, 0])
                cols_data.append(np_array[:, 1])
                cols_data.append(np_array[:, 2])
            else:
                for j in range(num_components):
                    self._column_headers.append(f"{array_name}_{j}")
                    cols_data.append(np_array[:, j])
        
        # Stack all columns efficiently
        if len(cols_data) > 1:
            # Use column_stack to create the matrix
            self._data_array = np.column_stack(cols_data)
        else:
            self._data_array = cols_data[0].reshape(-1, 1)
        
        logger.info(f"Table data loaded: {self._data_array.shape[0]} rows, {self._data_array.shape[1]} columns")
        self.data_updated.emit()
        return True
        
    def refresh_data(self) -> bool:
        """Reload data using current configuration."""
        if not self._source_item_id:
            return False
        return self.set_data_source(self._source_item_id, self._array_type)
    
    def get_table_data(self) -> Optional[np.ndarray]:
        """Return table data as NumPy array."""
        return self._data_array
    
    def get_column_headers(self) -> List[str]:
        """Return column names."""
        return self._column_headers
    
    def get_row_count(self) -> int:
        """Return number of data rows."""
        return 0 if self._data_array is None else self._data_array.shape[0]
    
    def get_column_count(self) -> int:
        """Return number of columns."""
        return len(self._column_headers)
    
    def export_to_csv(self, file_path: str) -> bool:
        """
        Export table data to CSV file.
        
        Parameters:
            file_path: Output file path
            
        Returns:
            True if export succeeded
        """
        if self._data_array is None:
            logger.error("No data to export")
            return False
            
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(self._column_headers)
                
                # Write data rows (convert NumPy array to list for CSV writer)
                writer.writerows(self._data_array.tolist())
            
            logger.info(f"Table data exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export table data: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all table data."""
        self._source_item_id = None
        self._data_array = None
        self._column_headers = []
        self.data_updated.emit()
        
    def get_info(self) -> Dict[str, Any]:
        """Get table information as a dictionary."""
        row_count = 0 if self._data_array is None else self._data_array.shape[0]
        return {
            "source_item_id": self._source_item_id,
            "array_type": self._array_type,
            "row_count": row_count,
            "column_count": len(self._column_headers),
        }
