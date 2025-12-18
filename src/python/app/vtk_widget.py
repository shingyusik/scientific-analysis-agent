from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QMessageBox
import vtk
import os

# Check if we can import the interactor
try:
    from vtk.modules.vtkGUISupportQt import QVTKRenderWindowInteractor
except ImportError:
    try:
        from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    except ImportError:
        QVTKRenderWindowInteractor = None

class VTKWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        if QVTKRenderWindowInteractor is None:
            label = QLabel("Error: vtk.qt.QVTKRenderWindowInteractor not found.\nEnsure 'vtk' is installed with Qt support.")
            label.setStyleSheet("background-color: black; color: red; alignment: center;")
            self.layout.addWidget(label)
            self.vtkWidget = None
            self.renderer = None
            return

        # Setup VTK Interactor
        self.vtkWidget = QVTKRenderWindowInteractor(self)
        self.layout.addWidget(self.vtkWidget)
        
        # Setup Renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.2, 0.3, 0.4) # Nice slate blue
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        
        # Initialize
        self.vtkWidget.Initialize()
        
        # Set Interaction Style to Trackball Camera (Standard CAD-like controls)
        # Left Click Drag: Rotate
        # Right Click Drag: Zoom
        # Middle Click Drag: Pan
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.vtkWidget.GetRenderWindow().GetInteractor().SetInteractorStyle(style)
        
        # Add Global Coordinate Axes
        self.axes_actor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2) # Bottom-left corner
        self.axes_widget.SetEnabled(1)
        self.axes_widget.InteractiveOn()
        
        self.vtkWidget.Start()
        
        # Render a test object by default
        self.render_cone()

    def render_cone(self):
        if not self.renderer: return None
        
        # Source
        cone = vtk.vtkConeSource()
        cone.SetHeight(3.0)
        cone.SetRadius(1.0)
        cone.SetResolution(10)
        
        # Mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(cone.GetOutputPort())
        
        # Actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.6, 0.2) # Orange
        
        # self.clear_scene() # No longer auto-clearing for multi-object support logic
        self.renderer.AddActor(actor)
        self.reset_camera() # Set initial view to Isometric
        
        return actor

    def render_file(self, file_path):
        if not self.renderer: return None
        
        if not os.path.exists(file_path):
            return None

        ext = os.path.splitext(file_path)[1].lower()
        reader = None
        
        if ext == '.vtu':
            reader = vtk.vtkXMLUnstructuredGridReader()
        elif ext == '.vti':
            reader = vtk.vtkXMLImageDataReader()
        elif ext == '.vtk':
            reader = vtk.vtkDataSetReader()
        else:
            print(f"Unsupported format: {ext}")
            return None
            
        reader.SetFileName(file_path)
        reader.Update()
        
        # Create Mapper
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        
        # Create Actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetEdgeColor(0, 0, 0)
        actor.GetProperty().EdgeVisibilityOn()
        
        # self.clear_scene()
        self.renderer.AddActor(actor)
        self.reset_camera() # Set initial view to Isometric
        self.vtkWidget.GetRenderWindow().Render()
        
        return actor

    def remove_actor(self, actor):
        if not self.renderer or not actor: return
        self.renderer.RemoveActor(actor)
        self.vtkWidget.GetRenderWindow().Render()

    def set_actor_visibility(self, actor, visible):
        if not actor: return
        actor.SetVisibility(visible)
        self.vtkWidget.GetRenderWindow().Render()

    def clear_scene(self):
        self.renderer.RemoveAllViewProps()
        # Re-add axes if cleared (though axes is a widget, RemoveAllViewProps usually removes actors/props)
        # Actually RemoveAllViewProps removes props added to renderer. AxesWidget is separate.
        self.vtkWidget.GetRenderWindow().Render()

    def reset_camera(self):
        if not self.renderer: return
        # Reset camera parameters to Isometric view (1, 1, 1)
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(1, 1, 1) 
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1) # Z-up assumption for 3D view
        
        self.renderer.ResetCamera() # Fit to bounds
        self.vtkWidget.GetRenderWindow().Render()

    def set_view_xy(self):
        if not self.renderer: return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0, 0, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 1, 0)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

    def set_view_yz(self):
        if not self.renderer: return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(1, 0, 0)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()

    def set_view_xz(self): # Request was ZX/XZ
        if not self.renderer: return
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(0, -1, 0)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 0, 1)
        self.renderer.ResetCamera()
        self.vtkWidget.GetRenderWindow().Render()
