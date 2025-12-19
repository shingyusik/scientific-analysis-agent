from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
                               QPushButton, QLabel, QFileDialog, QSplitter, QTreeWidget, QTreeWidgetItem, 
                               QTabWidget, QMenuBar, QMenu, QToolButton, QDoubleSpinBox, QSlider, 
                               QFormLayout, QGroupBox, QScrollArea, QSpinBox, QMessageBox, QCheckBox, QComboBox)
import vtk
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from app.vtk_widget import VTKWidget
import os

class ScientificDoubleSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDecimals(15) # Show many decimals if present
        self.setRange(-1e30, 1e30) # Very wide range
        self.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)

    def textFromValue(self, value):
        # Use general format 'g' with high precision, then strip trailing zeros
        # This naturally handles both scientific and standard notation cleanly
        formatted = format(value, '.10g')
        return formatted

    def validate(self, text, pos):
        # Allow 'e' and '-' for scientific notation input
        return super().validate(text, pos)

try:
    import sa_engine
except ImportError:
    sa_engine = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Analysis Agent")
        self.resize(1400, 900)
        
        # --- 1. Menu Bar ---
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        
        load_action = QAction("Load Data...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_file)
        file_menu.addAction(load_action)
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Filters Menu
        self.filters_menu = menu_bar.addMenu("Filters")
        
        slice_action = QAction("Slice", self)
        slice_action.triggered.connect(self.on_slice)
        self.filters_menu.addAction(slice_action)

        # --- 2. Toolbar (View Controls) ---
        toolbar = self.addToolBar("View Controls")
        
        action_reset = toolbar.addAction("Home (Reset)")
        action_reset.triggered.connect(lambda: self.vtk_widget.reset_camera())
        
        toolbar.addSeparator()
        
        action_xy = toolbar.addAction("XY Plane")
        action_xy.triggered.connect(lambda: self.vtk_widget.set_view_xy())
        
        action_yz = toolbar.addAction("YZ Plane")
        action_yz.triggered.connect(lambda: self.vtk_widget.set_view_yz())
        
        action_xz = toolbar.addAction("XZ Plane")
        action_xz.triggered.connect(lambda: self.vtk_widget.set_view_xz())

        toolbar.addSeparator()

        # Background Color Dropdown
        bg_tool_button = QToolButton()
        bg_tool_button.setText("Background")
        bg_tool_button.setPopupMode(QToolButton.InstantPopup)
        # Add padding to avoid overlap with the arrow
        bg_tool_button.setStyleSheet("QToolButton { padding-right: 15px; } QToolButton::menu-indicator { subcontrol-origin: padding; subcontrol-position: center right; }")
        
        bg_menu = QMenu(self)
        
        # Color presets
        presets = [
            ("Warm Gray (Default)", (0.32, 0.34, 0.43), None),
            ("Blue Gray", (0.2, 0.3, 0.4), None),
            ("Dark Gray", (0.1, 0.1, 0.1), None),
            ("Neutral Gray", (0.5, 0.5, 0.5), None),
            ("Light Gray", (0.8, 0.8, 0.8), None),
            ("White", (1.0, 1.0, 1.0), None),
            ("Black", (0.0, 0.0, 0.0), None),
            ("Gradient Background", (0.32, 0.34, 0.43), (0.0, 0.0, 0.0)),
        ]
        
        for name, c1, c2 in presets:
            action = bg_menu.addAction(name)
            # Use default arguments in lambda to capture loop variables correctly
            action.triggered.connect(lambda checked=False, col1=c1, col2=c2: self.vtk_widget.set_background_color(col1, col2))
        
        bg_tool_button.setMenu(bg_menu)
        toolbar.addWidget(bg_tool_button)

        # Representation Style Dropdown
        rep_tool_button = QToolButton()
        rep_tool_button.setText("Representation")
        rep_tool_button.setPopupMode(QToolButton.InstantPopup)
        rep_tool_button.setStyleSheet("QToolButton { padding-right: 15px; } QToolButton::menu-indicator { subcontrol-origin: padding; subcontrol-position: center right; }")
        
        rep_menu = QMenu(self)
        rep_styles = ["Points", "Point Gaussian", "Wireframe", "Surface", "Surface With Edges"]
        
        for style in rep_styles:
            action = rep_menu.addAction(style)
            action.triggered.connect(lambda checked=False, s=style: self.change_selected_representation(s))
            
        rep_tool_button.setMenu(rep_menu)
        toolbar.addWidget(rep_tool_button)

        # --- 3. Main Layout (Splitter) ---
        # We use QSplitter for resizable panels: [Left Sidebar] | [VTK View] | [Right Chat]
        main_splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(main_splitter)

        # [Left Sidebar] Pipeline Browser & Properties
        left_sidebar = QSplitter(Qt.Vertical)
        
        # 1. Working Tree (Pipeline Browser)
        self.pipeline_tree = QTreeWidget()
        self.pipeline_tree.setHeaderLabel("Pipeline Browser")
        self.pipeline_tree.itemChanged.connect(self.toggle_visibility) # Handle checkbox changes
        self.pipeline_tree.setContextMenuPolicy(Qt.CustomContextMenu) # Enable Right-click
        self.pipeline_tree.customContextMenuRequested.connect(self.show_context_menu)
        self.pipeline_tree.itemSelectionChanged.connect(self.on_selection_changed)
        left_sidebar.addWidget(self.pipeline_tree)
        
        # 2. Properties/Information Tabs
        self.details_tabs = QTabWidget()
        
        # Properties Tab (Dynamic Controls)
        self.properties_scroll = QScrollArea()
        self.properties_scroll.setWidgetResizable(True)
        self.properties_widget = QWidget()
        self.properties_layout = QVBoxLayout(self.properties_widget)
        self.properties_layout.setAlignment(Qt.AlignTop)
        self.properties_scroll.setWidget(self.properties_widget)
        
        self.details_tabs.addTab(self.properties_scroll, "Properties")
        
        # Information Tab
        self.info_page = QTextEdit()
        self.info_page.setReadOnly(True)
        self.details_tabs.addTab(self.info_page, "Information")
        
        left_sidebar.addWidget(self.details_tabs)
        left_sidebar.setStretchFactor(0, 1) # Tree
        left_sidebar.setStretchFactor(1, 1) # Tabs
        
        main_splitter.addWidget(left_sidebar)

        # [Center] VTK Visualization
        self.vtk_widget = VTKWidget()
        main_splitter.addWidget(self.vtk_widget)

        # [Right] Chat/Control Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        
        # Chat Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        right_layout.addWidget(self.chat_display)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.returnPressed.connect(self.handle_send) # Enter key sends
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        right_layout.addLayout(input_layout)
        
        # Removed "Load VTK File" button as requested
        
        main_splitter.addWidget(right_panel)
        
        # Set initial stretch factors (Sidebar: ~22%, VTK: ~55%, Chat: ~22%)
        main_splitter.setStretchFactor(0, 2)
        main_splitter.setStretchFactor(1, 5)
        main_splitter.setStretchFactor(2, 2)
        
        # Set explicit initial widths in pixels
        main_splitter.setSizes([350, 750, 300])
        
        # Initialize Engine
        if sa_engine:
            self.engine = sa_engine.Engine()
            msg = self.engine.greet("User")
            self.chat_display.append(f"System: {msg}")
        else:
            self.chat_display.append("System: Warning - sa_engine not available.")

        # Test Item (Cone) initial render
        # We need to manually add it to tree and get actor
        self.vtk_widget.clear_scene() # Start clean
        cone_actor, cone_data = self.vtk_widget.render_cone()
        self.add_pipeline_item("Cone Source", "Analysis Generator", cone_actor, cone_data)

    def handle_send(self):
        text = self.input_field.text()
        if not text:
            return
        self.chat_display.append(f"User: {text}")
        self.input_field.clear()
        # Todo: Integrate LangGraph agent here
        self.chat_display.append("Agent: (Thinking...) [Agent logic to be implemented]")

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Data", "", "VTK Files (*.vtu *.vti *.vtk)")
        if file_name:
            base_name = os.path.basename(file_name)
            self.chat_display.append(f"System: Loading {file_name}...")
            try:
                actor, data_obj = self.vtk_widget.render_file(file_name)
                if actor:
                    # Add to Pipeline
                    item = self.add_pipeline_item(base_name, "File Source", actor, data_obj)
                    
                    # Setup initial scalar bar if scalars exist
                    if data_obj and (data_obj.GetPointData().GetScalars() or data_obj.GetCellData().GetScalars()):
                        # Create default LUT for consistent visualization
                        mapper = actor.GetMapper()
                        if mapper:
                            mapper.CreateDefaultLookupTable()
                            mapper.SetScalarRange(data_obj.GetScalarRange())
                        
                    self.pipeline_tree.setCurrentItem(item)
                    self.update_properties_panel(item)
                    
                    self.chat_display.append(f"System: Loaded {base_name}")
                else:
                    self.chat_display.append("System: Failed to render file.")
                
            except Exception as e:
                self.chat_display.append(f"System: Error loading file - {e}")

    def on_slice(self):
        item = self.pipeline_tree.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Please select a source in Pipeline Browser.")
            return
            
        parent_data = item.data(0, Qt.UserRole + 3) # We'll store data_obj in Role+3
        if not parent_data: return
        
        # Use C++ Engine to apply slice
        center = parent_data.GetCenter()
        sliced_data = self.engine.apply_slice(parent_data, center[0], center[1], center[2], 1, 0, 0)
        
        if sliced_data:
            # Create mapper/actor for result
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(sliced_data)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(1, 1, 1) # Default white for slice
            
            self.vtk_widget.renderer.AddActor(actor)
            self.vtk_widget.vtkWidget.GetRenderWindow().Render()
            
            slice_item = self.add_pipeline_item(f"Slice ({item.text(0)})", "Slice Filter", actor, sliced_data, parent=item)
            slice_item.setData(0, Qt.UserRole + 4, center)
            slice_item.setData(0, Qt.UserRole + 5, [1, 0, 0])
            self.update_properties_panel(slice_item) # Refresh with parameters
            self.chat_display.append(f"System: [C++ Engine] Applied Slice filter to {item.text(0)}.")

    def add_pipeline_item(self, name, type_desc, actor=None, data_obj=None, parent=None):
        if parent:
            item = QTreeWidgetItem(parent)
            parent.setExpanded(True)
        else:
            item = QTreeWidgetItem(self.pipeline_tree)
            
        item.setText(0, name)
        item.setCheckState(0, Qt.Checked)
        
        # Information extraction using C++ Engine
        info_str = "No data object."
        if data_obj:
            try:
                # Call C++ engine to get info map
                engine_info = self.engine.get_data_info(data_obj)
                
                # Format into a string for display
                lines = []
                for k, v in engine_info.items():
                    lines.append(f"{k}: {v}")
                
                # Still add array info from Python for now as it's easier to list
                pt_data = data_obj.GetPointData()
                cell_data = data_obj.GetCellData()
                pt_arrays = [pt_data.GetArrayName(i) for i in range(pt_data.GetNumberOfArrays())]
                cell_arrays = [cell_data.GetArrayName(i) for i in range(cell_data.GetNumberOfArrays())]
                
                lines.append(f"Point Arrays: {', '.join(pt_arrays) if pt_arrays else 'None'}")
                lines.append(f"Cell Arrays: {', '.join(cell_arrays) if cell_arrays else 'None'}")
                
                info_str = "\n".join(lines)
            except Exception as e:
                info_str = f"Error extracting info: {e}"

        # Store metadata inside the item
        item.setData(0, Qt.UserRole, actor)
        item.setData(0, Qt.UserRole + 1, type_desc)
        item.setData(0, Qt.UserRole + 2, info_str)
        item.setData(0, Qt.UserRole + 3, data_obj)
        
        if not parent:
            self.pipeline_tree.setCurrentItem(item)
        self.update_properties_panel(item)
        return item

    def toggle_visibility(self, item, column):
        actor = item.data(0, Qt.UserRole)
        visible = (item.checkState(0) == Qt.Checked)
        self.vtk_widget.set_actor_visibility(actor, visible)
        
        # If hiding the currently selected item, hide the scalar bar too
        if not visible and item == self.pipeline_tree.currentItem():
            self.vtk_widget.hide_scalar_bar()
        # If showing and it is selected, try to show scalar bar
        elif visible and item == self.pipeline_tree.currentItem():
            self.update_properties_panel(item)

    def change_selected_representation(self, style):
        item = self.pipeline_tree.currentItem()
        if not item:
            self.chat_display.append("System: Please select an item in the Pipeline Browser first.")
            return
        
        actor = item.data(0, Qt.UserRole)
        if actor:
            self.vtk_widget.set_actor_representation(actor, style)
            self.update_properties_panel(item) # Update controls for new style
            self.chat_display.append(f"System: Set '{item.text(0)}' representation to {style}.")

    def show_context_menu(self, position):
        item = self.pipeline_tree.itemAt(position)
        if not item: return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.pipeline_tree.viewport().mapToGlobal(position))
        
        if action == delete_action:
            self.delete_item(item)

    def delete_item(self, item):
        # 1. Recursive helper to remove actors of this item and all its children
        def remove_actors_recursive(target_item):
            # Remove this item's actor
            actor = target_item.data(0, Qt.UserRole)
            if actor:
                self.vtk_widget.remove_actor(actor)
            
            # Recursively handle children
            for i in range(target_item.childCount()):
                remove_actors_recursive(target_item.child(i))

        # 2. Perform actor removal
        remove_actors_recursive(item)
        self.vtk_widget.hide_slice_preview() # Safety: hide preview if it was active
        
        # 3. Remove from Tree
        parent = item.parent()
        if parent:
            parent.removeChild(item)
        else:
            index = self.pipeline_tree.indexOfTopLevelItem(item)
            if index != -1:
                self.pipeline_tree.takeTopLevelItem(index)
        
        # 4. UI cleanup
        self.update_properties_panel(None)
        self.info_page.setPlainText("")
        self.vtk_widget.vtkWidget.GetRenderWindow().Render()

    def update_properties_panel(self, item):
        # Clear existing controls
        while self.properties_layout.count():
            child = self.properties_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not item:
            self.properties_layout.addWidget(QLabel("No item selected."))
            self.info_page.setPlainText("")
            self.vtk_widget.hide_slice_preview()
            return
            
        name = item.text(0)
        actor = item.data(0, Qt.UserRole)
        type_desc = item.data(0, Qt.UserRole + 1)
        info_str = item.data(0, Qt.UserRole + 2)
        
        # Update Information Page (Includes Name and Type now)
        full_info = f"Name: {name}\nType: {type_desc}\n\n{info_str if info_str else ''}"
        self.info_page.setPlainText(full_info)
        
        if not actor: 
            self.properties_layout.addWidget(QLabel("No styling properties available for this source."))
            self.vtk_widget.hide_scalar_bar()
            return

        # 0. Color By Control
        mapper = actor.GetMapper()
        data = mapper.GetInput() if mapper else None
        
        if data:
            # Collect arrays
            arrays = [] # list of (name, type)
            pd = data.GetPointData()
            for i in range(pd.GetNumberOfArrays()):
                name = pd.GetArrayName(i)
                if name: arrays.append((name, 'POINT'))
                
            cd = data.GetCellData()
            for i in range(cd.GetNumberOfArrays()):
                name = cd.GetArrayName(i)
                if name: arrays.append((name, 'CELL'))
            
            # Only show if there are arrays
            if arrays:
                color_layout = QHBoxLayout()
                color_group = QGroupBox("Color By")
                color_inner_layout = QVBoxLayout(color_group)
                
                combo = QComboBox()
                combo.addItem("Solid Color", "__SolidColor__")
                
                current_array = mapper.GetArrayName()
                current_idx = 0
                
                for idx, (name, type_) in enumerate(arrays):
                    combo.addItem(f"{name} ({type_})", (name, type_))
                    # Check if currently selected
                    if mapper.GetScalarVisibility() and name == current_array:
                        current_idx = idx + 1
                        
                combo.setCurrentIndex(current_idx)
                
                def on_color_change(idx):
                    data_val = combo.itemData(idx)
                    if data_val == "__SolidColor__":
                        self.vtk_widget.set_color_by(actor, "__SolidColor__")
                    else:
                        limit_name, limit_type = data_val
                        self.vtk_widget.set_color_by(actor, limit_name, limit_type)
                        
                combo.currentIndexChanged.connect(on_color_change)
                
                color_inner_layout.addWidget(combo)
                self.properties_layout.addWidget(color_group)

        # Update Scalar Bar (Legend) based on current state (redundant check but keeps consistency)
        has_scalars = False
        if mapper and mapper.GetScalarVisibility():
             has_scalars = True
        
        if has_scalars and mapper.GetScalarVisibility():
            # Only show if visibility is ON. 
            # Do NOT pass title=name, let vtk_widget figure out the variable name.
            self.vtk_widget.update_scalar_bar(actor)
        else:
            self.vtk_widget.hide_scalar_bar()
        
        # 1. Action Button (Apply) - Only for Filters
        if "Filter" in type_desc:
            apply_btn = QPushButton("Apply")
            # Using a more prominent styling for the main action button
            apply_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c3e50; 
                    color: white; 
                    font-weight: bold; 
                    padding: 10px; 
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #34495e;
                }
                QPushButton:pressed {
                    background-color: #1a252f;
                }
            """)
            apply_btn.setCursor(Qt.PointingHandCursor)
            apply_btn.clicked.connect(lambda: self.commit_filter_changes(item))
            self.properties_layout.addWidget(apply_btn)

        # 2. Styling Controls
        style = self.vtk_widget.get_actor_style(actor)
        style_group = QGroupBox(f"Styling: {style}")
        style_layout = QFormLayout(style_group)
        
        # Opacity Control (Common for all styles)
        opacity_layout = QHBoxLayout()
        opacity_slider = QSlider(Qt.Horizontal)
        opacity_slider.setRange(0, 100)
        current_opacity = int(actor.GetProperty().GetOpacity() * 100)
        opacity_slider.setValue(current_opacity)
        
        opacity_spin = QSpinBox()
        opacity_spin.setRange(0, 100)
        opacity_spin.setSuffix("%")
        opacity_spin.setValue(current_opacity)
        
        def update_opacity(val):
            # Ensure val is treated as int, though QSpinBox and QSlider provide ints
            int_val = int(val) 
            self.vtk_widget.set_actor_opacity(actor, int_val / 100.0)
            opacity_slider.blockSignals(True)
            opacity_slider.setValue(int_val)
            opacity_slider.blockSignals(False)
            opacity_spin.blockSignals(True)
            opacity_spin.setValue(int_val)
            opacity_spin.blockSignals(False)
            
        opacity_slider.valueChanged.connect(update_opacity)
        opacity_spin.valueChanged.connect(update_opacity)
        
        opacity_reset = QPushButton("Reset")
        opacity_reset.setFixedWidth(50)
        opacity_reset.clicked.connect(lambda: update_opacity(100))
        
        opacity_layout.addWidget(opacity_slider)
        opacity_layout.addWidget(opacity_spin)
        opacity_layout.addWidget(opacity_reset)
        style_layout.addRow("Opacity:", opacity_layout)
        
        if style == "Points":
            size_spin = ScientificDoubleSpinBox()
            size_spin.setValue(actor.GetProperty().GetPointSize())
            size_spin.valueChanged.connect(lambda v: self.vtk_widget.set_point_size(actor, v))
            
            reset_btn = QPushButton("Reset")
            reset_btn.setFixedWidth(50)
            reset_btn.clicked.connect(lambda: [size_spin.setValue(3.0), self.vtk_widget.set_point_size(actor, 3.0)])
            
            row_layout = QHBoxLayout()
            row_layout.addWidget(size_spin)
            row_layout.addWidget(reset_btn)
            style_layout.addRow("Point Size:", row_layout)
            
        elif style in ["Wireframe", "Surface With Edges"]:
            width_spin = ScientificDoubleSpinBox()
            width_spin.setValue(actor.GetProperty().GetLineWidth())
            width_spin.valueChanged.connect(lambda v: self.vtk_widget.set_line_width(actor, v))
            
            reset_btn = QPushButton("Reset")
            reset_btn.setFixedWidth(50)
            reset_btn.clicked.connect(lambda: [width_spin.setValue(1.0), self.vtk_widget.set_line_width(actor, 1.0)])
            
            row_layout = QHBoxLayout()
            row_layout.addWidget(width_spin)
            row_layout.addWidget(reset_btn)
            style_layout.addRow("Line Width:", row_layout)
            
        elif style == "Point Gaussian":
            scale_spin = ScientificDoubleSpinBox()
            
            mapper = actor.GetMapper()
            current_scale = mapper.GetScaleFactor() if hasattr(mapper, "GetScaleFactor") else 0.05
            scale_spin.setValue(current_scale)
            scale_spin.valueChanged.connect(lambda v: self.vtk_widget.set_gaussian_scale(actor, v))
            
            reset_btn = QPushButton("Reset")
            reset_btn.setFixedWidth(50)
            reset_btn.clicked.connect(lambda: [scale_spin.setValue(0.05), self.vtk_widget.set_gaussian_scale(actor, 0.05)])
            
            row_layout = QHBoxLayout()
            row_layout.addWidget(scale_spin)
            row_layout.addWidget(reset_btn)
            style_layout.addRow("Sphere Radius:", row_layout)
            
        self.properties_layout.addWidget(style_group)
        
        # 3. Filter Specific Controls
        if "Filter" in type_desc:
            filter_group = QGroupBox("Filter Parameters")
            filter_layout = QFormLayout(filter_group)
            
            if "Slice" in type_desc:
                # Origin
                origin = item.data(0, Qt.UserRole + 4) or [0, 0, 0]
                for i, label in enumerate(["Origin X", "Origin Y", "Origin Z"]):
                    spin = ScientificDoubleSpinBox()
                    spin.setValue(origin[i])
                    # Use index closure for lambda
                    spin.valueChanged.connect(lambda v, idx=i: self.update_slice_params(item, 'origin', idx, v))
                    filter_layout.addRow(label, spin)
                
                # Preview Toggle
                show_plane_cb = QCheckBox("Show Plane")
                preview_visible = item.data(0, Qt.UserRole + 6)
                if preview_visible is None: preview_visible = True # Default to on
                show_plane_cb.setChecked(preview_visible)
                show_plane_cb.toggled.connect(lambda v: self.toggle_slice_preview(item, v))
                filter_layout.addRow("", show_plane_cb)
                
                # Normal
                normal = item.data(0, Qt.UserRole + 5) or [1, 0, 0]
                for i, label in enumerate(["Normal X", "Normal Y", "Normal Z"]):
                    spin = ScientificDoubleSpinBox()
                    spin.setRange(-1, 1) # Normal is typical -1 to 1
                    spin.setValue(normal[i])
                    spin.valueChanged.connect(lambda v, idx=i: self.update_slice_params(item, 'normal', idx, v))
                    filter_layout.addRow(label, spin)
            
            self.properties_layout.addWidget(filter_group)
            
            # If it's a slice, show initial preview
            if "Slice" in type_desc:
                self.update_slice_preview(item)
            
        else:
            self.vtk_widget.hide_slice_preview()
            
        self.properties_layout.addStretch() # Push everything to top

    def on_selection_changed(self):
        item = self.pipeline_tree.currentItem()
        self.update_properties_panel(item)

    def update_slice_preview(self, item):
        parent_item = item.parent()
        if not parent_item: return
        parent_data = parent_item.data(0, Qt.UserRole + 3)
        origin = item.data(0, Qt.UserRole + 4)
        normal = item.data(0, Qt.UserRole + 5)
        preview_visible = item.data(0, Qt.UserRole + 6)
        if preview_visible is None: preview_visible = True

        if preview_visible and parent_data and origin and normal:
            self.vtk_widget.update_slice_preview(origin, normal, parent_data.GetBounds())
        else:
            self.vtk_widget.hide_slice_preview()

    def toggle_slice_preview(self, item, visible):
        item.setData(0, Qt.UserRole + 6, visible)
        self.update_slice_preview(item)

    def update_slice_params(self, item, param_type, index, value):
        # Update roles only, show preview
        origin = list(item.data(0, Qt.UserRole + 4) or [0,0,0])
        normal = list(item.data(0, Qt.UserRole + 5) or [1,0,0])
        
        if param_type == 'origin': origin[index] = value
        else: normal[index] = value
        
        item.setData(0, Qt.UserRole + 4, origin)
        item.setData(0, Qt.UserRole + 5, normal)
        self.update_slice_preview(item)

    def commit_filter_changes(self, item):
        actor = item.data(0, Qt.UserRole)
        type_desc = item.data(0, Qt.UserRole + 1)
        parent_item = item.parent()
        if not parent_item: return
        parent_data = parent_item.data(0, Qt.UserRole + 3)
        
        if "Slice" in type_desc:
            origin = item.data(0, Qt.UserRole + 4)
            normal = item.data(0, Qt.UserRole + 5)
            self.chat_display.append(f"System: [C++ Engine] Recalculating Slice...")
            sliced_data = self.engine.apply_slice(parent_data, origin[0], origin[1], origin[2], normal[0], normal[1], normal[2])
            actor.GetMapper().SetInputData(sliced_data)
            
        self.vtk_widget.vtkWidget.GetRenderWindow().Render()
        self.chat_display.append(f"System: Filter applied.")
