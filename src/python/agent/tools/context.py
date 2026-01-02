from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel
    from viewmodels.vtk_viewmodel import VTKViewModel
from utils.logger import get_logger

logger = get_logger("AgentContext")

_pipeline_vm: Optional["PipelineViewModel"] = None
_vtk_vm: Optional["VTKViewModel"] = None


def set_pipeline_viewmodel(vm: "PipelineViewModel") -> None:
    global _pipeline_vm
    _pipeline_vm = vm
    logger.info("PipelineViewModel registered in context")


def set_vtk_viewmodel(vm: "VTKViewModel") -> None:
    global _vtk_vm
    _vtk_vm = vm
    logger.info("VTKViewModel registered in context")


def get_pipeline_viewmodel() -> Optional["PipelineViewModel"]:
    return _pipeline_vm


def get_vtk_viewmodel() -> Optional["VTKViewModel"]:
    return _vtk_vm
