import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from config import Config
from services.vtk_render_service import VTKRenderService
from services.file_loader_service import FileLoaderService
from viewmodels.pipeline_viewmodel import PipelineViewModel
from viewmodels.vtk_viewmodel import VTKViewModel
from viewmodels.chat_viewmodel import ChatViewModel
from views.main_window import MainWindow


from utils.logger import get_logger, log_execution

logger = get_logger("MainEntry")

@log_execution(start_msg="애플리케이션 시작", end_msg="애플리케이션 종료")
def main():
    app = QApplication(sys.argv)
    Config.load()
    
    render_service = VTKRenderService()
    file_loader = FileLoaderService()
    
    pipeline_vm = PipelineViewModel(render_service, file_loader)
    vtk_vm = VTKViewModel(render_service)
    chat_vm = ChatViewModel(pipeline_vm, vtk_vm)
    
    window = MainWindow(pipeline_vm, vtk_vm, chat_vm)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
