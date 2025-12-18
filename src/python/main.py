import sys
import os
from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow

# Ensure we can find the modules if running from source without install
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    app = QApplication(sys.argv)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
