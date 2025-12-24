import os
import re
import glob
import vtk
from typing import Any, Tuple, List, Optional


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
    
    def detect_time_series(self, file_path: str) -> Optional[List[str]]:
        """
        Detect time series files based on filename pattern.
        
        Looks for files with same base name but different trailing numbers.
        E.g., data_000.vtk, data_001.vtk, data_002.vtk
        
        Args:
            file_path: Path to one of the series files
            
        Returns:
            Sorted list of file paths if series detected, None otherwise
        """
        if not os.path.exists(file_path):
            return None
        
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        
        number_pattern = re.compile(r'(\d+)$')
        match = number_pattern.search(name)
        
        if not match:
            return None
        
        number_str = match.group(1)
        base_name = name[:match.start()]
        num_digits = len(number_str)
        
        glob_pattern = os.path.join(directory, f"{base_name}*{ext}")
        candidate_files = glob.glob(glob_pattern)
        
        series_files = []
        series_pattern = re.compile(rf'^{re.escape(base_name)}(\d{{{num_digits}}})$')
        
        for candidate in candidate_files:
            candidate_name = os.path.splitext(os.path.basename(candidate))[0]
            if series_pattern.match(candidate_name):
                series_files.append(candidate)
        
        if len(series_files) <= 1:
            return None
        
        def extract_number(path):
            name = os.path.splitext(os.path.basename(path))[0]
            m = number_pattern.search(name)
            return int(m.group(1)) if m else 0
        
        series_files.sort(key=extract_number)
        return series_files
    
    def _natural_sort_key(self, path: str):
        """Generate sort key for natural sorting (numeric-aware)."""
        filename = os.path.basename(path)
        return [int(c) if c.isdigit() else c.lower() 
                for c in re.split(r'(\d+)', filename)]
    
    def load_time_series(self, file_paths: List[str]) -> Tuple[List[Any], str]:
        """
        Load all files in a time series.
        
        Args:
            file_paths: List of file paths in the series
            
        Returns:
            Tuple of (list of vtk_data_objects, series_name)
        """
        if not file_paths:
            raise ValueError("No files provided for time series")
        
        sorted_paths = sorted(file_paths, key=self._natural_sort_key)
        
        data_list = []
        for path in sorted_paths:
            data, _ = self.load(path)
            data_list.append(data)
        
        first_name = os.path.basename(sorted_paths[0])
        last_name = os.path.basename(sorted_paths[-1])
        name, ext = os.path.splitext(first_name)
        
        match = re.search(r'(\d+)$', name)
        if match:
            base = name[:match.start()]
            first_num = match.group(1)
            last_match = re.search(r'(\d+)$', os.path.splitext(last_name)[0])
            last_num = last_match.group(1) if last_match else first_num
            series_name = f"{base}[{first_num}-{last_num}]{ext}"
        else:
            series_name = f"{first_name} (series)"
        
        return data_list, series_name, sorted_paths

