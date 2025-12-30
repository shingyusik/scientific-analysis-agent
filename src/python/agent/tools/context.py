from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from viewmodels.pipeline_viewmodel import PipelineViewModel

_pipeline_vm: Optional["PipelineViewModel"] = None


def set_pipeline_viewmodel(vm: "PipelineViewModel") -> None:
    global _pipeline_vm
    _pipeline_vm = vm


def get_pipeline_viewmodel() -> Optional["PipelineViewModel"]:
    return _pipeline_vm
