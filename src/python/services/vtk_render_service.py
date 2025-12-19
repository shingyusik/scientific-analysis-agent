import vtk
from typing import Any, Tuple, List

try:
    import sa_engine
except ImportError:
    sa_engine = None


class VTKRenderService:
    """Service for VTK rendering operations."""
    
    def __init__(self):
        self._engine = sa_engine.Engine() if sa_engine else None
    
    @property
    def engine(self):
        return self._engine
    
    def create_cone_source(self) -> Tuple[Any, Any]:
        """Create a cone source with elevation scalars."""
        cone = vtk.vtkConeSource()
        cone.SetHeight(3.0)
        cone.SetRadius(1.0)
        cone.SetResolution(40)
        cone.Update()
        
        elev = vtk.vtkElevationFilter()
        elev.SetInputData(cone.GetOutput())
        elev.SetLowPoint(-1.5, 0, 0)
        elev.SetHighPoint(1.5, 0, 0)
        elev.Update()
        
        output_data = elev.GetOutput()
        actor = self.create_actor(output_data)
        actor.GetProperty().SetColor(1.0, 0.6, 0.2)
        
        return actor, output_data
    
    def create_actor(self, data: Any, use_dataset_mapper: bool = False) -> Any:
        """Create a VTK actor from data."""
        if use_dataset_mapper:
            mapper = vtk.vtkDataSetMapper()
        else:
            mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        
        return actor
    
    def create_actor_for_file(self, data: Any) -> Any:
        """Create actor optimized for file data."""
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetEdgeColor(0, 0, 0)
        actor.GetProperty().EdgeVisibilityOn()
        
        return actor
    
    def apply_slice(self, data: Any, origin: List[float], normal: List[float]) -> Tuple[Any, Any]:
        """Apply slice filter using C++ engine."""
        if self._engine:
            sliced_data = self._engine.apply_slice(
                data, origin[0], origin[1], origin[2],
                normal[0], normal[1], normal[2]
            )
        else:
            plane = vtk.vtkPlane()
            plane.SetOrigin(origin)
            plane.SetNormal(normal)
            
            cutter = vtk.vtkCutter()
            cutter.SetInputData(data)
            cutter.SetCutFunction(plane)
            cutter.Update()
            sliced_data = cutter.GetOutput()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(sliced_data)
        
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1, 1, 1)
        
        return actor, sliced_data
    
    def apply_contour(self, data: Any, value: float, array_name: str = None) -> Tuple[Any, Any]:
        """Apply contour filter."""
        contour = vtk.vtkContourFilter()
        contour.SetInputData(data)
        
        if array_name:
            contour.SelectInputScalars(array_name)
        
        contour.SetValue(0, value)
        contour.Update()
        
        contour_data = contour.GetOutput()
        actor = self.create_actor(contour_data)
        
        return actor, contour_data
    
    def apply_elevation(self, data: Any) -> Any:
        """Apply elevation filter."""
        bounds = data.GetBounds()
        
        elev = vtk.vtkElevationFilter()
        elev.SetInputData(data)
        elev.SetLowPoint(bounds[0], bounds[2], bounds[4])
        elev.SetHighPoint(bounds[1], bounds[3], bounds[5])
        elev.Update()
        
        return elev.GetOutput()
    
    def set_representation(self, actor: Any, style: str) -> None:
        """Set actor representation style."""
        actor._representation_style = style
        
        current_mapper = actor.GetMapper()
        data = current_mapper.GetInput()
        prop = actor.GetProperty()
        
        prop.SetRepresentationToSurface()
        prop.EdgeVisibilityOff()
        
        if style == "Point Gaussian":
            if not isinstance(current_mapper, vtk.vtkGlyph3DMapper):
                sphere = vtk.vtkSphereSource()
                sphere.SetRadius(1.0)
                sphere.SetThetaResolution(8)
                sphere.SetPhiResolution(8)
                
                new_mapper = vtk.vtkGlyph3DMapper()
                new_mapper.SetInputData(data)
                new_mapper.SetSourceConnection(sphere.GetOutputPort())
                new_mapper.SetScaleModeToNoDataScaling()
                new_mapper.SetScaleFactor(0.05)
                
                actor.SetMapper(new_mapper)
            prop.SetRepresentationToSurface()
            return
        
        if isinstance(current_mapper, (vtk.vtkPointGaussianMapper, vtk.vtkGlyph3DMapper)):
            new_mapper = vtk.vtkDataSetMapper()
            new_mapper.SetInputData(data)
            actor.SetMapper(new_mapper)
        
        if style == "Points":
            prop.SetRepresentationToPoints()
            prop.SetPointSize(3.0)
        elif style == "Wireframe":
            prop.SetRepresentationToWireframe()
            prop.SetLineWidth(1.0)
        elif style == "Surface":
            prop.SetRepresentationToSurface()
        elif style == "Surface With Edges":
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOn()
            prop.SetLineWidth(1.0)
    
    def get_representation_style(self, actor: Any) -> str:
        """Get actor's current representation style."""
        return getattr(actor, '_representation_style', 'Surface')
    
    def set_color_by(self, actor: Any, array_name: str, array_type: str = 'POINT') -> None:
        """Set coloring by scalar array."""
        mapper = actor.GetMapper()
        if not mapper:
            return
        
        if array_name == "__SolidColor__":
            mapper.ScalarVisibilityOff()
            return
        
        mapper.ScalarVisibilityOn()
        if array_type == 'POINT':
            mapper.SetScalarModeToUsePointFieldData()
        else:
            mapper.SetScalarModeToUseCellFieldData()
        
        mapper.SelectColorArray(array_name)
        
        data = mapper.GetInput()
        if data:
            if array_type == 'POINT':
                arr = data.GetPointData().GetArray(array_name)
            else:
                arr = data.GetCellData().GetArray(array_name)
            
            if arr:
                rng = arr.GetRange()
                mapper.SetScalarRange(rng)
    
    def set_opacity(self, actor: Any, value: float) -> None:
        """Set actor opacity (0.0 - 1.0)."""
        actor.GetProperty().SetOpacity(value)
    
    def set_point_size(self, actor: Any, size: float) -> None:
        """Set point size for Points representation."""
        actor.GetProperty().SetPointSize(size)
    
    def set_line_width(self, actor: Any, width: float) -> None:
        """Set line width for Wireframe representation."""
        actor.GetProperty().SetLineWidth(width)
    
    def set_gaussian_scale(self, actor: Any, scale: float) -> None:
        """Set scale factor for Point Gaussian representation."""
        mapper = actor.GetMapper()
        if hasattr(mapper, "SetScaleFactor"):
            mapper.SetScaleFactor(scale)
    
    def get_data_info(self, data: Any) -> dict:
        """Get data information using C++ engine if available."""
        if self._engine:
            return self._engine.get_data_info(data)
        
        info = {
            "Number of Points": str(data.GetNumberOfPoints()),
            "Number of Cells": str(data.GetNumberOfCells()),
        }
        bounds = data.GetBounds()
        info["Bounds"] = f"X[{bounds[0]:.4g}, {bounds[1]:.4g}] Y[{bounds[2]:.4g}, {bounds[3]:.4g}] Z[{bounds[4]:.4g}, {bounds[5]:.4g}]"
        return info
    
    def get_data_arrays(self, data: Any) -> List[Tuple[str, str]]:
        """Get list of available data arrays."""
        arrays = []
        
        pd = data.GetPointData()
        for i in range(pd.GetNumberOfArrays()):
            name = pd.GetArrayName(i)
            if name:
                arrays.append((name, 'POINT'))
        
        cd = data.GetCellData()
        for i in range(cd.GetNumberOfArrays()):
            name = cd.GetArrayName(i)
            if name:
                arrays.append((name, 'CELL'))
        
        return arrays

