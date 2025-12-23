from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Signal
import vtk
from typing import Any, Tuple, List

try:
    from vtk.modules.vtkGUISupportQt import QVTKRenderWindowInteractor
except ImportError:
    try:
        from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    except ImportError:
        QVTKRenderWindowInteractor = None


class VTKWidget(QWidget):
    """VTK rendering widget - handles only rendering and display."""
    
    initialized = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        
        if QVTKRenderWindowInteractor is None:
            label = QLabel("Error: vtk.qt.QVTKRenderWindowInteractor not found.")
            label.setStyleSheet("background-color: black; color: red;")
            self._layout.addWidget(label)
            self.vtk_widget = None
            self.renderer = None
            return
        
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self._layout.addWidget(self.vtk_widget)
        
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.32, 0.34, 0.43)
        self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
        
        self.vtk_widget.Initialize()
        
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtk_widget.GetRenderWindow().GetInteractor().SetInteractorStyle(style)
        
        self._setup_axes()
        self._setup_scalar_bar()
        self._setup_slice_preview()
        
        self.vtk_widget.Start()
        self.initialized.emit()
    
    def _setup_axes(self) -> None:
        """Setup orientation axes widget."""
        self.axes_actor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtk_widget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.SetEnabled(1)
        self.axes_widget.InteractiveOn()
    
    def _setup_scalar_bar(self) -> None:
        """Setup scalar bar widget."""
        self.scalar_bar_widget = vtk.vtkScalarBarWidget()
        self.scalar_bar_widget.SetInteractor(self.vtk_widget.GetRenderWindow().GetInteractor())
        self.scalar_bar_widget.On()
        
        sb_rep = self.scalar_bar_widget.GetRepresentation()
        sb_rep.SetPosition(0.9, 0.3)
        sb_rep.SetPosition2(0.08, 0.4)
        
        self.scalar_bar_widget.Off()
        self._current_scalar_bar_actor = None
    
    def _setup_slice_preview(self) -> None:
        """Setup slice preview plane."""
        self._preview_plane_source = vtk.vtkPlaneSource()
        self._preview_plane_mapper = vtk.vtkPolyDataMapper()
        self._preview_plane_mapper.SetInputConnection(self._preview_plane_source.GetOutputPort())
        
        self._preview_plane_actor = vtk.vtkActor()
        self._preview_plane_actor.SetMapper(self._preview_plane_mapper)
        self._preview_plane_actor.GetProperty().SetColor(0.2, 0.4, 1.0)
        self._preview_plane_actor.GetProperty().SetOpacity(0.4)
        self._preview_plane_actor.VisibilityOff()
        self.renderer.AddActor(self._preview_plane_actor)
    
    def add_actor(self, actor: Any) -> None:
        """Add actor to renderer."""
        if self.renderer and actor:
            self.renderer.AddActor(actor)
            self.render()
    
    def remove_actor(self, actor: Any) -> None:
        """Remove actor from renderer."""
        if self.renderer and actor:
            self.renderer.RemoveActor(actor)
            self.render()
    
    def render(self) -> None:
        """Trigger render update."""
        if self.vtk_widget:
            self.vtk_widget.GetRenderWindow().Render()
    
    def clear_scene(self) -> None:
        """Remove all actors from scene."""
        if self.renderer:
            self.renderer.RemoveAllViewProps()
            if hasattr(self, '_preview_plane_actor'):
                self.renderer.AddActor(self._preview_plane_actor)
            self.render()
    
    def set_background(self, color1: Tuple[float, float, float], 
                       color2: Tuple[float, float, float] = None) -> None:
        """Set background color."""
        if not self.renderer:
            return
        self.renderer.SetBackground(*color1)
        if color2:
            self.renderer.SetBackground2(*color2)
            self.renderer.GradientBackgroundOn()
        else:
            self.renderer.GradientBackgroundOff()
        self.render()
    
    def reset_camera(self) -> None:
        """Reset camera to isometric view."""
        if not self.renderer:
            return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(1, 1, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.render()
    
    def set_view_xy(self) -> None:
        """Set XY plane view."""
        if not self.renderer:
            return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0, 0, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 1, 0)
        self.renderer.ResetCamera()
        self.render()
    
    def set_view_yz(self) -> None:
        """Set YZ plane view."""
        if not self.renderer:
            return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(1, 0, 0)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.render()
    
    def set_view_xz(self) -> None:
        """Set XZ plane view."""
        if not self.renderer:
            return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0, -1, 0)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.render()
    
    def set_view_plane(self, plane: str) -> None:
        """Set view to specified plane."""
        if plane == "xy":
            self.set_view_xy()
        elif plane == "yz":
            self.set_view_yz()
        elif plane == "xz":
            self.set_view_xz()
    
    def update_slice_preview(self, origin: List[float], normal: List[float], 
                             bounds: Tuple[float, ...]) -> None:
        """Update slice preview plane."""
        self._preview_plane_source.SetOrigin(-0.5, -0.5, 0)
        self._preview_plane_source.SetPoint1(0.5, -0.5, 0)
        self._preview_plane_source.SetPoint2(-0.5, 0.5, 0)
        self._preview_plane_source.SetNormal(normal)
        self._preview_plane_source.SetCenter(0, 0, 0)
        
        self._preview_plane_actor.SetPosition(origin)
        
        if bounds:
            size_x = bounds[1] - bounds[0]
            size_y = bounds[3] - bounds[2]
            size_z = bounds[5] - bounds[4]
            scale = max(size_x, size_y, size_z) * 1.5
            self._preview_plane_actor.SetScale(scale, scale, scale)
        
        self._preview_plane_actor.VisibilityOn()
        self._preview_plane_actor.Modified()
        self.render()
    
    def hide_slice_preview(self) -> None:
        """Hide slice preview plane."""
        if hasattr(self, '_preview_plane_actor'):
            self._preview_plane_actor.VisibilityOff()
            self.render()
    
    def update_scalar_bar(self, actor: Any, title: str = None) -> None:
        """Update scalar bar for actor."""
        if not actor or not self.scalar_bar_widget:
            return
        
        mapper = actor.GetMapper()
        if not mapper or not mapper.GetScalarVisibility():
            self.hide_scalar_bar()
            return
        
        data = mapper.GetInput()
        if not data:
            return
        
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
            self.hide_scalar_bar()
            return
        
        scalar_name = array_name
        if not scalar_name and title:
            scalar_name = title
        if not scalar_name and scalars.GetName():
            scalar_name = scalars.GetName()
        if not scalar_name:
            scalar_name = "Scalars"
        
        lut = mapper.GetLookupTable()
        if not lut:
            mapper.CreateDefaultLookupTable()
            lut = mapper.GetLookupTable()
        
        if lut:
            rng = scalars.GetRange()
            lut.SetRange(rng[0], rng[1])
            lut.Build()
            
            sb_actor = self.scalar_bar_widget.GetScalarBarActor()
            sb_actor.SetLookupTable(lut)
            sb_actor.SetTitle(scalar_name)
            sb_actor.SetNumberOfLabels(5)
            
            sb_rep = self.scalar_bar_widget.GetRepresentation()
            sb_rep.SetPosition(0.9, 0.3)
            sb_rep.SetPosition2(0.08, 0.4)
            
            for p in [sb_actor.GetTitleTextProperty(), sb_actor.GetLabelTextProperty()]:
                p.SetColor(1, 1, 1)
                p.ShadowOn()
                p.BoldOn()
                p.ItalicOff()
                p.SetFontFamilyToArial()
            
            self._current_scalar_bar_actor = actor
            self.scalar_bar_widget.On()
            self.render()
        else:
            self.hide_scalar_bar()
    
    def hide_scalar_bar(self) -> None:
        """Hide scalar bar."""
        if self.scalar_bar_widget:
            self.scalar_bar_widget.Off()
            self._current_scalar_bar_actor = None
            self.render()
    
    def set_actor_visibility(self, actor: Any, visible: bool) -> None:
        """Set actor visibility."""
        if actor:
            actor.SetVisibility(visible)
            if not visible and hasattr(self, '_current_scalar_bar_actor') and self._current_scalar_bar_actor == actor:
                self.hide_scalar_bar()
            self.render()

