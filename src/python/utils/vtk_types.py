"""
VTK Type Aliases for improved type hinting.

These type aliases provide more descriptive type hints for VTK objects
throughout the codebase, improving code readability and IDE support.
"""

from typing import Any, Union

# VTK Actor types
VTKActor = Any  # vtk.vtkActor
VTKActor3D = Any  # vtk.vtkActor3D
VTKActorCollection = Any  # vtk.vtkActorCollection

# VTK Data types
VTKDataSet = Any  # vtk.vtkDataSet (base class for all VTK datasets)
VTKUnstructuredGrid = Any  # vtk.vtkUnstructuredGrid
VTKStructuredGrid = Any  # vtk.vtkStructuredGrid
VTKPolyData = Any  # vtk.vtkPolyData
VTKRectilinearGrid = Any  # vtk.vtkRectilinearGrid
VTKImageData = Any  # vtk.vtkImageData
VTKMultiBlockDataSet = Any  # vtk.vtkMultiBlockDataSet

# VTK Array types
VTKArray = Any  # vtk.vtkDataArray (base for all VTK arrays)
VTKFloatArray = Any  # vtk.vtkFloatArray
VTKDoubleArray = Any  # vtk.vtkDoubleArray

# VTK Mapper types
VTKMapper = Any  # vtk.vtkMapper
VTKDataSetMapper = Any  # vtk.vtkDataSetMapper
VTKPolyDataMapper = Any  # vtk.vtkPolyDataMapper

# VTK Renderer types
VTKRenderer = Any  # vtk.vtkRenderer
VTKRenderWindow = Any  # vtk.vtkRenderWindow
VTKRenderWindowInteractor = Any  # vtk.vtkRenderWindowInteractor

# VTK Camera
VTKCamera = Any  # vtk.vtkCamera

# VTK Filters
VTKPlane = Any  # vtk.vtkPlane
VTKCutter = Any  # vtk.vtkCutter
VTKClipDataSet = Any  # vtk.vtkClipDataSet

# VTK Widgets
VTKScalarBarWidget = Any  # vtk.vtkScalarBarWidget
VTKOrientationMarkerWidget = Any  # vtk.vtkOrientationMarkerWidget

# VTK Lookup Table
VTKLookupTable = Any  # vtk.vtkLookupTable
VTKScalarBarActor = Any  # vtk.vtkScalarBarActor

# General VTK object type (for when specific type is unknown)
VTKObject = Any  # General VTK object

# Union types for common use cases
VTKDataInput = Union[VTKDataSet, VTKUnstructuredGrid, VTKPolyData, VTKStructuredGrid]
