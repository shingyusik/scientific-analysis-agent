import vtk
from vtk.util import numpy_support
from typing import Any, Tuple, List
import numpy as np

try:
    import sa_engine
except ImportError:
    sa_engine = None


class VTKRenderService:
    """Service for VTK rendering operations."""
    
    def __init__(self):
        self._engine = sa_engine.Engine() if sa_engine else None
        self._actor_styles: dict[int, str] = {}
    
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
        self._actor_styles[id(actor)] = style
        
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
        return self._actor_styles.get(id(actor), 'Surface')
    
    def set_color_by(self, actor: Any, array_name: str, array_type: str = 'POINT', component: str = 'Magnitude') -> None:
        """Set coloring by scalar array. For vector arrays, can use magnitude or components (X, Y, Z)."""
        mapper = actor.GetMapper()
        if not mapper:
            return
        
        if array_name == "__SolidColor__":
            mapper.ScalarVisibilityOff()
            return
        
        data = mapper.GetInput()
        if not data:
            return
        
        if array_type == 'POINT':
            arr = data.GetPointData().GetArray(array_name)
        else:
            arr = data.GetCellData().GetArray(array_name)
        
        if not arr:
            return
        
        actual_array_name = array_name
        actual_array = arr
        
        if arr.GetNumberOfComponents() > 1:
            if component == "Magnitude":
                magnitude_name = f"{array_name}_Magnitude"
                
                if array_type == 'POINT':
                    existing = data.GetPointData().GetArray(magnitude_name)
                    if existing:
                        actual_array = existing
                        actual_array_name = magnitude_name
                    else:
                        vtk_array_np = numpy_support.vtk_to_numpy(arr)
                        num_tuples, num_components = vtk_array_np.shape
                        
                        magnitude_np = np.linalg.norm(vtk_array_np, axis=1)
                        
                        magnitude = numpy_support.numpy_to_vtk(magnitude_np, deep=True)
                        magnitude.SetName(magnitude_name)
                        
                        data.GetPointData().AddArray(magnitude)
                        actual_array = magnitude
                        actual_array_name = magnitude_name
                else:
                    existing = data.GetCellData().GetArray(magnitude_name)
                    if existing:
                        actual_array = existing
                        actual_array_name = magnitude_name
                    else:
                        vtk_array_np = numpy_support.vtk_to_numpy(arr)
                        num_tuples, num_components = vtk_array_np.shape
                        
                        magnitude_np = np.linalg.norm(vtk_array_np, axis=1)
                        
                        magnitude = numpy_support.numpy_to_vtk(magnitude_np, deep=True)
                        magnitude.SetName(magnitude_name)
                        
                        data.GetCellData().AddArray(magnitude)
                        actual_array = magnitude
                        actual_array_name = magnitude_name
            else:
                component_idx = {"X": 0, "Y": 1, "Z": 2}.get(component, 0)
                component_name = f"{array_name}_{component}"
                
                if array_type == 'POINT':
                    existing = data.GetPointData().GetArray(component_name)
                    if existing:
                        actual_array = existing
                        actual_array_name = component_name
                    else:
                        vtk_array_np = numpy_support.vtk_to_numpy(arr)
                        num_tuples, num_components = vtk_array_np.shape
                        
                        if component_idx < num_components:
                            component_np = vtk_array_np[:, component_idx]
                            
                            component_arr = numpy_support.numpy_to_vtk(component_np, deep=True)
                            component_arr.SetName(component_name)
                            
                            data.GetPointData().AddArray(component_arr)
                            actual_array = component_arr
                            actual_array_name = component_name
                else:
                    existing = data.GetCellData().GetArray(component_name)
                    if existing:
                        actual_array = existing
                        actual_array_name = component_name
                    else:
                        vtk_array_np = numpy_support.vtk_to_numpy(arr)
                        num_tuples, num_components = vtk_array_np.shape
                        
                        if component_idx < num_components:
                            component_np = vtk_array_np[:, component_idx]
                            
                            component_arr = numpy_support.numpy_to_vtk(component_np, deep=True)
                            component_arr.SetName(component_name)
                            
                            data.GetCellData().AddArray(component_arr)
                            actual_array = component_arr
                            actual_array_name = component_name
        
        mapper.ScalarVisibilityOn()
        if array_type == 'POINT':
            mapper.SetScalarModeToUsePointFieldData()
        else:
            mapper.SetScalarModeToUseCellFieldData()
        
        mapper.SelectColorArray(actual_array_name)
        
        rng = actual_array.GetRange()
        mapper.SetScalarRange(rng)
        
        lut = mapper.GetLookupTable()
        if lut:
            lut.SetHueRange(0.6667, 0.0)
            lut.SetRange(rng[0], rng[1])
            lut.Modified()
    
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
    
    def get_data_arrays(self, data: Any) -> List[Tuple[str, str, int]]:
        """Get list of available data arrays with component count."""
        arrays = []
        generated_suffixes = ['_Magnitude', '_X', '_Y', '_Z']
        
        pd = data.GetPointData()
        point_array_names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays()) if pd.GetArrayName(i)]
        
        for name in point_array_names:
            is_generated = False
            for suffix in generated_suffixes:
                if name.endswith(suffix):
                    base_name = name[:-len(suffix)]
                    if base_name in point_array_names:
                        is_generated = True
                        break
            if not is_generated:
                arr = pd.GetArray(name)
                num_components = arr.GetNumberOfComponents() if arr else 1
                arrays.append((name, 'POINT', num_components))
        
        cd = data.GetCellData()
        cell_array_names = [cd.GetArrayName(i) for i in range(cd.GetNumberOfArrays()) if cd.GetArrayName(i)]
        
        for name in cell_array_names:
            is_generated = False
            for suffix in generated_suffixes:
                if name.endswith(suffix):
                    base_name = name[:-len(suffix)]
                    if base_name in cell_array_names:
                        is_generated = True
                        break
            if not is_generated:
                arr = cd.GetArray(name)
                num_components = arr.GetNumberOfComponents() if arr else 1
                arrays.append((name, 'CELL', num_components))
        
        return arrays
    
    def fit_scalar_range(self, actor: Any) -> bool:
        """Set scalar range to data min/max values."""
        mapper = actor.GetMapper()
        if not mapper or not mapper.GetScalarVisibility():
            return False
        
        data = mapper.GetInput()
        if not data:
            return False
        
        array_name = mapper.GetArrayName()
        scalars = None
        
        if array_name:
            scalar_mode = mapper.GetScalarMode()
            if scalar_mode == vtk.VTK_SCALAR_MODE_USE_POINT_FIELD_DATA:
                scalars = data.GetPointData().GetArray(array_name)
            elif scalar_mode == vtk.VTK_SCALAR_MODE_USE_CELL_FIELD_DATA:
                scalars = data.GetCellData().GetArray(array_name)
        
        if not scalars:
            scalars = data.GetPointData().GetScalars() or data.GetCellData().GetScalars()
        
        if not scalars:
            return False
        
        rng = scalars.GetRange()
        mapper.SetScalarRange(rng[0], rng[1])
        
        lut = mapper.GetLookupTable()
        if lut:
            lut.SetHueRange(0.6667, 0.0)
            lut.SetRange(rng[0], rng[1])
            lut.Modified()
        
        return True
    
    def set_custom_scalar_range(self, actor: Any, min_val: float, max_val: float) -> bool:
        """Set custom scalar range."""
        mapper = actor.GetMapper()
        if not mapper or not mapper.GetScalarVisibility():
            return False
        
        mapper.SetScalarRange(min_val, max_val)
        
        lut = mapper.GetLookupTable()
        if lut:
            lut.SetHueRange(0.6667, 0.0)
            lut.SetRange(min_val, max_val)
            lut.Modified()
        
        return True

