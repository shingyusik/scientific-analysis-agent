from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel
    from viewmodels.vtk_viewmodel import VTKViewModel
    from viewmodels.time_series_manager import TimeSeriesManager
    from viewmodels.tab_manager_viewmodel import TabManagerViewModel
from utils.logger import get_logger

logger = get_logger("AgentContext")

_pipeline_vm: Optional["PipelineViewModel"] = None
_vtk_vm: Optional["VTKViewModel"] = None
_time_series_manager: Optional["TimeSeriesManager"] = None
_tab_manager_vm: Optional["TabManagerViewModel"] = None


def set_pipeline_viewmodel(vm: "PipelineViewModel") -> None:
    global _pipeline_vm
    _pipeline_vm = vm
    logger.info("PipelineViewModel registered in context")


def set_vtk_viewmodel(vm: "VTKViewModel") -> None:
    global _vtk_vm
    _vtk_vm = vm
    logger.info("VTKViewModel registered in context")


def set_time_series_manager(manager: "TimeSeriesManager") -> None:
    global _time_series_manager
    _time_series_manager = manager
    logger.info("TimeSeriesManager registered in context")


def set_tab_manager_viewmodel(vm: "TabManagerViewModel") -> None:
    global _tab_manager_vm
    _tab_manager_vm = vm
    logger.info("TabManagerViewModel registered in context")


def get_pipeline_viewmodel() -> Optional["PipelineViewModel"]:
    return _pipeline_vm


def get_vtk_viewmodel() -> Optional["VTKViewModel"]:
    return _vtk_vm


def get_time_series_manager() -> Optional["TimeSeriesManager"]:
    return _time_series_manager


def get_tab_manager_viewmodel() -> Optional["TabManagerViewModel"]:
    return _tab_manager_vm
