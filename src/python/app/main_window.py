from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
                               QPushButton, QLabel, QFileDialog, QSplitter, QTreeWidget, QTreeWidgetItem, 
                               QTabWidget, QMenuBar, QMenu)
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
from app.vtk_widget import VTKWidget
import os

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
        self.pipeline_tree.itemClicked.connect(self.update_properties_panel)
        left_sidebar.addWidget(self.pipeline_tree)
        
        # 2. Properties/Information Tabs
        self.details_tabs = QTabWidget()
        
        # Properties Tab (Placeholder)
        self.properties_page = QTextEdit()
        self.properties_page.setPlainText("No item selected.")
        self.properties_page.setReadOnly(True) 
        self.details_tabs.addTab(self.properties_page, "Properties")
        
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
        
        # Set initial stretch factors (Sidebar: 15%, VTK: 60%, Chat: 25%)
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 5)
        main_splitter.setStretchFactor(2, 2)
        
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
                    self.chat_display.append("System: Visualization updated.")
                    # Add to Pipeline Tree
                    self.add_pipeline_item(base_name, "File Source", actor, data_obj)
                else:
                    self.chat_display.append("System: Failed to render file.")
                
            except Exception as e:
                self.chat_display.append(f"System: Error loading file - {e}")

    def add_pipeline_item(self, name, type_desc, actor=None, data_obj=None):
        item = QTreeWidgetItem(self.pipeline_tree)
        item.setText(0, name)
        item.setCheckState(0, Qt.Checked) # Checkbox for visibility
        
        # Information extraction (Using Python VTK API for now due to missing C++ headers in project)
        info_str = "No data object."
        if data_obj:
            try:
                pts = data_obj.GetNumberOfPoints()
                cells = data_obj.GetNumberOfCells()
                bounds = data_obj.GetBounds()
                bounds_str = f"[{bounds[0]:.2f}, {bounds[1]:.2f}] x [{bounds[2]:.2f}, {bounds[3]:.2f}] x [{bounds[4]:.2f}, {bounds[5]:.2f}]"
                
                pt_arrays = [data_obj.GetPointData().GetArrayName(i) for i in range(data_obj.GetPointData().GetNumberOfArrays())]
                cell_arrays = [data_obj.GetCellData().GetArrayName(i) for i in range(data_obj.GetCellData().GetNumberOfArrays())]
                
                info_str = (
                    f"Points: {pts}\n"
                    f"Cells: {cells}\n"
                    f"Bounds: {bounds_str}\n"
                    f"Point Arrays: {', '.join(pt_arrays) if pt_arrays else 'None'}\n"
                    f"Cell Arrays: {', '.join(cell_arrays) if cell_arrays else 'None'}"
                )
            except Exception as e:
                info_str = f"Error extracting info: {e}"

        # Store metadata inside the item
        item.setData(0, Qt.UserRole, actor)
        item.setData(0, Qt.UserRole + 1, type_desc)
        item.setData(0, Qt.UserRole + 2, info_str)
        
        self.pipeline_tree.setCurrentItem(item)
        self.update_properties_panel(item)

    def toggle_visibility(self, item, column):
        actor = item.data(0, Qt.UserRole)
        if actor:
            visible = (item.checkState(0) == Qt.Checked)
            self.vtk_widget.set_actor_visibility(actor, visible)

    def show_context_menu(self, position):
        item = self.pipeline_tree.itemAt(position)
        if not item: return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.pipeline_tree.viewport().mapToGlobal(position))
        
        if action == delete_action:
            self.delete_item(item)

    def delete_item(self, item):
        actor = item.data(0, Qt.UserRole)
        if actor:
            self.vtk_widget.remove_actor(actor)
        
        # Remove from tree
        index = self.pipeline_tree.indexOfTopLevelItem(item)
        self.pipeline_tree.takeTopLevelItem(index)
        
        self.properties_page.setPlainText("Deleted.")
        self.info_page.setPlainText("")

    def update_properties_panel(self, item):
        if not item:
            self.properties_page.setPlainText("No item selected.")
            self.info_page.setPlainText("")
            return
            
        name = item.text(0)
        type_desc = item.data(0, Qt.UserRole + 1)
        info_desc = item.data(0, Qt.UserRole + 2)
        
        self.properties_page.setPlainText(f"Name: {name}\nType: {type_desc}")
        self.info_page.setPlainText(info_desc)
