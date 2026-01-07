from PySide6.QtCore import QObject, Signal
from typing import List, Optional, Any, Dict
import vtk
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
        self._data_rows: List[List[Any]] = []
        self._column_headers: List[str] = []
        
    @property
    def source_item_id(self) -> Optional[str]:
        """Get the source pipeline item ID."""
        return self._source_item_id
    
    def set_data_source(self, item_id: str, array_type: str = "POINT") -> bool:
        """
        Load ALL data arrays from a pipeline item.
        
        Parameters:
            item_id: Pipeline item ID
            array_type: 'POINT' or 'CELL' data
            
        Returns:
            True if data was loaded successfully
        """
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
        
        self._source_item_id = item_id
        self._array_type = array_type
        
        # Build column headers from ALL arrays
        self._column_headers = ["Index"]
        array_info = []  # (array, num_components, column_names)
        
        for i in range(data_arrays.GetNumberOfArrays()):
            array = data_arrays.GetArray(i)
            if not array:
                continue
                
            array_name = array.GetName() or f"Array_{i}"
            num_components = array.GetNumberOfComponents()
            
            col_names = []
            if num_components == 1:
                col_names.append(array_name)
            elif num_components == 3:
                col_names = [f"{array_name}_X", f"{array_name}_Y", f"{array_name}_Z"]
            else:
                col_names = [f"{array_name}_{j}" for j in range(num_components)]
            
            self._column_headers.extend(col_names)
            array_info.append((array, num_components, col_names))
        
        # Extract rows - iterate once through all tuples
        self._data_rows = []
        for i in range(num_tuples):
            row = [i]  # Index column
            for array, num_components, _ in array_info:
                if num_components == 1:
                    row.append(array.GetValue(i))
                else:
                    tuple_data = array.GetTuple(i)
                    row.extend(tuple_data)
            self._data_rows.append(row)
        
        logger.info(f"Table data loaded: {len(self._data_rows)} rows, {len(self._column_headers)} columns from {len(array_info)} arrays")
        self.data_updated.emit()
        return True
    
    def get_table_data(self) -> List[List[Any]]:
        """Return table rows (including index column)."""
        return self._data_rows
    
    def get_column_headers(self) -> List[str]:
        """Return column names."""
        return self._column_headers
    
    def get_row_count(self) -> int:
        """Return number of data rows."""
        return len(self._data_rows)
    
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
        try:
            import csv
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow(self._column_headers)
                
                # Write data rows
                writer.writerows(self._data_rows)
            
            logger.info(f"Table data exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export table data: {e}")
            return False
    
    def clear(self) -> None:
        """Clear all table data."""
        self._source_item_id = None
        self._data_rows = []
        self._column_headers = []
        self.data_updated.emit()
        
    def get_info(self) -> Dict[str, Any]:
        """Get table information as a dictionary."""
        return {
            "source_item_id": self._source_item_id,
            "array_type": self._array_type,
            "row_count": len(self._data_rows),
            "column_count": len(self._column_headers),
        }
