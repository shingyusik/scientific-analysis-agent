import vtk
from vtk.util import numpy_support
from typing import Any, Tuple, List
import numpy as np
from utils.logger import get_logger, log_execution

logger = get_logger("VTKRender")

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
    
    @log_execution(start_msg="Cone Source 생성 시작", end_msg="Cone Source 생성 완료")
    def create_cone_source(self) -> Tuple[Any, Any]:
        """Create a cone source with elevation scalars and vector field."""
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
        
        num_points = output_data.GetNumberOfPoints()
        if num_points > 0:
            points = output_data.GetPoints()
            vector_array = vtk.vtkFloatArray()
            vector_array.SetNumberOfComponents(3)
            vector_array.SetName("VectorField")
            
            for i in range(num_points):
                point = points.GetPoint(i)
                x, y, z = point
                
                vector_x = x
                vector_y = y
                vector_z = z
                
                vector_array.InsertNextTuple3(vector_x, vector_y, vector_z)
            
            output_data.GetPointData().AddArray(vector_array)
            output_data.GetPointData().SetActiveVectors("VectorField")
        
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
    
    @log_execution(start_msg="Contour 필터 적용", end_msg="Contour 필터 완료")
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
    
    @log_execution(start_msg="Elevation 필터 적용", end_msg="Elevation 필터 완료")
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
    
    def _get_data_object(self, data: Any, array_type: str):
        """Get PointData or CellData based on array type."""
        return data.GetPointData() if array_type == 'POINT' else data.GetCellData()
    
    def _get_or_create_derived_array(self, data: Any, arr: Any, derived_name: str, 
                                      array_type: str, compute_fn) -> Tuple[Any, str]:
        """Get existing derived array or create new one."""
        data_obj = self._get_data_object(data, array_type)
        existing = data_obj.GetArray(derived_name)
        if existing:
            return existing, derived_name
        
        vtk_array_np = numpy_support.vtk_to_numpy(arr)
        result_np = compute_fn(vtk_array_np)
        result_arr = numpy_support.numpy_to_vtk(result_np, deep=True)
        result_arr.SetName(derived_name)
        data_obj.AddArray(result_arr)
        return result_arr, derived_name
    
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
        
        arr = self._get_data_object(data, array_type).GetArray(array_name)
        if not arr:
            return
        
        actual_array = arr
        actual_array_name = array_name
        
        if arr.GetNumberOfComponents() > 1:
            if component == "Magnitude":
                actual_array, actual_array_name = self._get_or_create_derived_array(
                    data, arr, f"{array_name}_Magnitude", array_type,
                    lambda np_arr: np.linalg.norm(np_arr, axis=1)
                )
            else:
                component_idx = {"X": 0, "Y": 1, "Z": 2}.get(component, 0)
                actual_array, actual_array_name = self._get_or_create_derived_array(
                    data, arr, f"{array_name}_{component}", array_type,
                    lambda np_arr, idx=component_idx: np_arr[:, idx] if idx < np_arr.shape[1] else np_arr[:, 0]
                )
        
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
            
        logger.info(f"Color By 설정: Array={actual_array_name}, Component={component}")
    
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
        generated_suffixes = ('_Magnitude', '_X', '_Y', '_Z')
        
        def process_data_object(data_obj, type_name: str):
            names = [data_obj.GetArrayName(i) for i in range(data_obj.GetNumberOfArrays()) if data_obj.GetArrayName(i)]
            for name in names:
                is_generated = any(
                    name.endswith(suffix) and name[:-len(suffix)] in names
                    for suffix in generated_suffixes
                )
                if not is_generated:
                    arr = data_obj.GetArray(name)
                    arrays.append((name, type_name, arr.GetNumberOfComponents() if arr else 1))
        
        process_data_object(data.GetPointData(), 'POINT')
        process_data_object(data.GetCellData(), 'CELL')
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
        
        logger.info(f"Scalar Range 자동 맞춤: {rng}")
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

