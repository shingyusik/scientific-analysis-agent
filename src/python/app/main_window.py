from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel, QFileDialog
from PySide6.QtCore import Qt
from app.vtk_widget import VTKWidget
try:
    import sa_engine
except ImportError:
    sa_engine = None

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Scientific Analysis Agent")
        self.resize(1200, 800)
        
        # Toolbar
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

        # Central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left: VTK Visualization
        self.vtk_widget = VTKWidget()
        main_layout.addWidget(self.vtk_widget, stretch=2)
        
        # Right: Chat/Control Panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        main_layout.addWidget(right_panel, stretch=1)
        
        # Chat Display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        right_layout.addWidget(self.chat_display)
        
        # Input Area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.handle_send)
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        right_layout.addLayout(input_layout)
        
        # File Upload
        self.upload_button = QPushButton("Load VTK File")
        self.upload_button.clicked.connect(self.load_file)
        right_layout.addWidget(self.upload_button)
        
        # Initialize Engine
        if sa_engine:
            self.engine = sa_engine.Engine()
            msg = self.engine.greet("User")
            self.chat_display.append(f"System: {msg}")
        else:
            self.chat_display.append("System: Warning - sa_engine not found. C++ features disabled.")

    def handle_send(self):
        text = self.input_field.text()
        if not text:
            return
        self.chat_display.append(f"User: {text}")
        self.input_field.clear()
        # Todo: Integrate LangGraph agent here
        self.chat_display.append("Agent: (Thinking...) [Agent logic to be implemented]")

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Open VTK File", "", "VTK Files (*.vtu *.vti *.vtk)")
        if file_name:
            self.chat_display.append(f"System: Loading {file_name}...")
            try:
                self.vtk_widget.render_file(file_name)
                self.chat_display.append("System: Visualization updated.")
            except Exception as e:
                self.chat_display.append(f"System: Error loading file - {e}")
