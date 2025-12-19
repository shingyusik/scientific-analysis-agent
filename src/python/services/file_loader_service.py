import os
import vtk
from typing import Any, Tuple


class FileLoaderService:
    """Service for loading VTK data files."""
    
    SUPPORTED_EXTENSIONS = {".vtu", ".vti", ".vtk"}
    
    def load(self, file_path: str) -> Tuple[Any, str]:
        """
        Load a VTK data file.
        
        Args:
            file_path: Path to the VTK file
            
        Returns:
            Tuple of (vtk_data_object, base_filename)
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is not supported
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported format: {ext}. Supported: {self.SUPPORTED_EXTENSIONS}")
        
        reader = self._get_reader(ext)
        reader.SetFileName(file_path)
        reader.Update()
        
        return reader.GetOutput(), os.path.basename(file_path)
    
    def _get_reader(self, ext: str) -> Any:
        """Get appropriate VTK reader for file extension."""
        if ext == ".vtu":
            return vtk.vtkXMLUnstructuredGridReader()
        elif ext == ".vti":
            return vtk.vtkXMLImageDataReader()
        elif ext == ".vtk":
            return vtk.vtkDataSetReader()
        else:
            raise ValueError(f"No reader for extension: {ext}")
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file format is supported."""
        ext = os.path.splitext(file_path)[1].lower()
        return ext in self.SUPPORTED_EXTENSIONS

