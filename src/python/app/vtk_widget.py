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
        self.renderer.SetBackground(0.32, 0.34, 0.43) # Warm Gray (Matches Default preset)
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
        
        # --- Scalar Bar Widget (Robust Color Legend) ---
        self.scalar_bar_widget = vtk.vtkScalarBarWidget()
        self.scalar_bar_widget.SetInteractor(self.vtkWidget.GetRenderWindow().GetInteractor())
        self.scalar_bar_widget.On() # Enable it initially to configure
        
        sb_rep = self.scalar_bar_widget.GetRepresentation()
        sb_rep.SetPosition(0.9, 0.3)
        sb_rep.SetPosition2(0.08, 0.4)
        
        # Default invisible
        self.scalar_bar_widget.Off()

        # Render a test object by default
        self.render_cone()

    def update_scalar_bar(self, actor, title=None):
        if not actor or not self.scalar_bar_widget: return
        
        mapper = actor.GetMapper()
        if not mapper: return
        
        # Get scalar range from data
        data = mapper.GetInput()
        if not data: return
            
        scalars = data.GetPointData().GetScalars() or data.GetCellData().GetScalars()
        if not scalars: return
             
        # Determine Title
        # 1. Try Mapper's selected array name
        scalar_name = mapper.GetArrayName()
        # 2. Try Title argument
        if not scalar_name and title:
            scalar_name = title
        # 3. Try underlying scalar data name
        if not scalar_name and scalars.GetName():
            scalar_name = scalars.GetName()
        # 4. Fallback
        if not scalar_name:
            scalar_name = "Scalars"
            
        lut = mapper.GetLookupTable()
        if not lut:
            mapper.CreateDefaultLookupTable()
            lut = mapper.GetLookupTable()
            
        if lut:
            # Sync LUT
            rng = scalars.GetRange()
            lut.SetRange(rng[0], rng[1])
            lut.Build()

            sb_actor = self.scalar_bar_widget.GetScalarBarActor()
            sb_actor.SetLookupTable(lut)
            sb_actor.SetTitle(scalar_name)
            sb_actor.SetNumberOfLabels(5)

            # Enforce size and position updates via Representation
            sb_rep = self.scalar_bar_widget.GetRepresentation()
            sb_rep.SetPosition(0.9, 0.3)
            sb_rep.SetPosition2(0.08, 0.4)
            
            # Styling
            for p in [sb_actor.GetTitleTextProperty(), sb_actor.GetLabelTextProperty()]:
                p.SetColor(1, 1, 1)
                p.ShadowOn()
                p.BoldOn()
                p.ItalicOff()
                p.SetFontFamilyToArial()
            
            # Use widget to control visibility
            self.scalar_bar_widget.On()
            self.vtkWidget.GetRenderWindow().Render()
        else:
            self.hide_scalar_bar()

    def hide_scalar_bar(self):
        if self.scalar_bar_widget:
            self.scalar_bar_widget.Off()
            self.vtkWidget.GetRenderWindow().Render()

    def set_color_by(self, actor, array_name, array_type='POINT'):
        if not actor: return
        mapper = actor.GetMapper()
        if not mapper: return
        
        if array_name == "__SolidColor__":
            mapper.ScalarVisibilityOff()
            self.hide_scalar_bar()
        else:
            mapper.ScalarVisibilityOn()
            if array_type == 'POINT':
                mapper.SetScalarModeToUsePointFieldData()
            else:
                mapper.SetScalarModeToUseCellFieldData()
            
            mapper.SelectColorArray(array_name)
            
            # Reset LUT range
            data = mapper.GetInput()
            if data:
                if array_type == 'POINT':
                    arr = data.GetPointData().GetArray(array_name)
                else:
                    arr = data.GetCellData().GetArray(array_name)
                
                if arr:
                    rng = arr.GetRange()
                    mapper.SetScalarRange(rng)
                    
            self.update_scalar_bar(actor)
            
        self.vtkWidget.GetRenderWindow().Render()

    def render_cone(self):
        if not self.renderer: return None, None
        
        # Source
        cone = vtk.vtkConeSource()
        cone.SetHeight(3.0)
        cone.SetRadius(1.0)
        cone.SetResolution(40)
        cone.Update()
        
        # Add elevation scalars so contouring works by default
        elev = vtk.vtkElevationFilter()
        elev.SetInputData(cone.GetOutput())
        elev.SetLowPoint(-1.5, 0, 0)
        elev.SetHighPoint(1.5, 0, 0)
        elev.Update()
        
        output_data = elev.GetOutput()
        
        # Mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(output_data)
        
        # Actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(1.0, 0.6, 0.2) # Orange
        
        self.renderer.AddActor(actor)
        self.reset_camera()
        
        # Initial Coloring
        self.set_color_by(actor, "Elevation")
        
        return actor, output_data

    def render_file(self, file_path):
        if not self.renderer: return None, None
        
        if not os.path.exists(file_path):
            return None, None

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
            return None, None
            
        reader.SetFileName(file_path)
        reader.Update()
        
        data_obj = reader.GetOutput()
        
        # Create Mapper
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(data_obj)
        
        # Create Actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetEdgeColor(0, 0, 0)
        actor.GetProperty().EdgeVisibilityOn()
        
        self.renderer.AddActor(actor)
        self.reset_camera()
        self.vtkWidget.GetRenderWindow().Render()
        
        return actor, data_obj

    def remove_actor(self, actor):
        if not self.renderer or not actor: return
        self.renderer.RemoveActor(actor)
        self.vtkWidget.GetRenderWindow().Render()

    def set_actor_visibility(self, actor, visible):
        if not actor: return
        actor.SetVisibility(visible)
        self.vtkWidget.GetRenderWindow().Render()

    def set_background_color(self, color1, color2=None):
        if not self.renderer: return
        self.renderer.SetBackground(*color1)
        if color2:
            self.renderer.SetBackground2(*color2)
            self.renderer.GradientBackgroundOn()
        else:
            self.renderer.GradientBackgroundOff()
        self.vtkWidget.GetRenderWindow().Render()

    def set_actor_representation(self, actor, style):
        if not actor: return
        
        # Store style for UI properties panel
        actor._representation_style = style
        
        current_mapper = actor.GetMapper()
        data = current_mapper.GetInput()
        prop = actor.GetProperty()
        
        # 1. Reset actor properties to a clean state
        prop.SetRepresentationToSurface()
        prop.EdgeVisibilityOff()
        
        # 2. Handle Mapper Swapping
        if style == "Point Gaussian":
            if not isinstance(current_mapper, vtk.vtkGlyph3DMapper):
                sphere = vtk.vtkSphereSource()
                sphere.SetRadius(1.0) # Set base radius to 1.0 so ScaleFactor = Radius
                sphere.SetThetaResolution(8)
                sphere.SetPhiResolution(8)
                
                new_mapper = vtk.vtkGlyph3DMapper()
                new_mapper.SetInputData(data)
                new_mapper.SetSourceConnection(sphere.GetOutputPort())
                new_mapper.SetScaleModeToNoDataScaling()
                new_mapper.SetScaleFactor(0.05)
                
                actor.SetMapper(new_mapper)
            prop.SetRepresentationToSurface()
            self.vtkWidget.GetRenderWindow().Render()
            return

        if isinstance(current_mapper, (vtk.vtkPointGaussianMapper, vtk.vtkGlyph3DMapper)):
            new_mapper = vtk.vtkDataSetMapper()
            new_mapper.SetInputData(data)
            actor.SetMapper(new_mapper)
            
        # 3. Apply specific styles
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
            
        self.vtkWidget.GetRenderWindow().Render()

    def set_point_size(self, actor, value):
        if not actor: return
        actor.GetProperty().SetPointSize(value)
        self.vtkWidget.GetRenderWindow().Render()

    def set_line_width(self, actor, value):
        if not actor: return
        actor.GetProperty().SetLineWidth(value)
        self.vtkWidget.GetRenderWindow().Render()

    def set_gaussian_scale(self, actor, value):
        if not actor: return
        mapper = actor.GetMapper()
        if hasattr(mapper, "SetScaleFactor"):
            mapper.SetScaleFactor(value)
            self.vtkWidget.GetRenderWindow().Render()

    def apply_slice(self, data_obj, origin=(0,0,0), normal=(1,0,0)):
        if not data_obj: return None
        
        # Define the plane for slicing
        plane = vtk.vtkPlane()
        plane.SetOrigin(origin)
        plane.SetNormal(normal)
        
        # Cutter filter creates a slice (cross-section)
        cutter = vtk.vtkCutter()
        cutter.SetInputData(data_obj)
        cutter.SetCutFunction(plane)
        cutter.Update()
        
        return cutter.GetOutput()

    def apply_contour(self, data_obj, value, array_name=None):
        if not data_obj: return None
        
        contour = vtk.vtkContourFilter()
        contour.SetInputData(data_obj)
        
        if array_name:
            contour.SelectInputScalars(array_name)
            
        contour.SetValue(0, value)
        contour.Update()
        
        return contour.GetOutput()

    def apply_elevation(self, data_obj):
        if not data_obj: return None
        bounds = data_obj.GetBounds()
        
        elev = vtk.vtkElevationFilter()
        elev.SetInputData(data_obj)
        elev.SetLowPoint(bounds[0], bounds[2], bounds[4])
        elev.SetHighPoint(bounds[1], bounds[3], bounds[5])
        elev.Update()
        return elev.GetOutput()

    def set_actor_opacity(self, actor, value):
        if not actor: return
        # Opacity in VTK is 0.0 - 1.0, but UI sends 0-100
        # Wait, previous implementation might have changed this. 
        # Checking main_window call: lambda v: self.vtk_widget.set_actor_opacity(actor, v/100.0)
        # So actor.SetOpacity(value) expects 0.0-1.0
        actor.GetProperty().SetOpacity(value)
        self.vtkWidget.GetRenderWindow().Render()

    # --- Plane Preview Logic ---
    def setup_slice_preview(self):
        self.preview_plane_source = vtk.vtkPlaneSource()
        self.preview_plane_mapper = vtk.vtkPolyDataMapper()
        self.preview_plane_mapper.SetInputConnection(self.preview_plane_source.GetOutputPort())
        
        self.preview_plane_actor = vtk.vtkActor()
        self.preview_plane_actor.SetMapper(self.preview_plane_mapper)
        self.preview_plane_actor.GetProperty().SetColor(0.2, 0.4, 1.0) # Light blue
        self.preview_plane_actor.GetProperty().SetOpacity(0.4)
        self.preview_plane_actor.VisibilityOff()
        self.renderer.AddActor(self.preview_plane_actor)

    def update_slice_preview(self, origin, normal, bounds=None):
        if not hasattr(self, 'preview_plane_source'):
            self.setup_slice_preview()
            
        self.preview_plane_source.SetOrigin(-0.5, -0.5, 0)
        self.preview_plane_source.SetPoint1(0.5, -0.5, 0)
        self.preview_plane_source.SetPoint2(-0.5, 0.5, 0)
        self.preview_plane_source.SetNormal(normal)
        self.preview_plane_source.SetCenter(0, 0, 0) # Center relative to source
        
        self.preview_plane_actor.SetPosition(origin)
        
        # Scale based on bounds to cover the object
        if bounds:
            size_x = bounds[1] - bounds[0]
            size_y = bounds[3] - bounds[2]
            size_z = bounds[5] - bounds[4]
            scale = max(size_x, size_y, size_z) * 1.5 # 50% bigger than max dimension
            self.preview_plane_actor.SetScale(scale, scale, scale)

        self.preview_plane_actor.VisibilityOn()
        self.preview_plane_actor.Modified()
        self.vtkWidget.GetRenderWindow().Render()

    def hide_slice_preview(self):
        if hasattr(self, 'preview_plane_actor'):
            self.preview_plane_actor.VisibilityOff()
            self.vtkWidget.GetRenderWindow().Render()

    def get_actor_style(self, actor):
        return getattr(actor, '_representation_style', 'Surface')

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
