from agent.tools.context import set_pipeline_viewmodel, get_pipeline_viewmodel, set_vtk_viewmodel, get_vtk_viewmodel
from agent.tools.pipeline import get_pipeline_info, select_pipeline_item, delete_item
from agent.tools.filter import (
    apply_slice_filter,
    apply_clip_filter,
    get_filter_params,
    update_slice_filter_params,
    update_clip_filter_params,
)
from agent.tools.visualization import (
    set_visibility,
    set_color_by,
    set_representation,
    set_opacity,
    set_visual_property,
    auto_fit_scalar_range,
    set_scalar_range,
    set_camera_view,
    set_view_plane,
    reset_camera_view,
)
from agent.tools.interaction import request_user_input

def get_all_tools() -> list:
    return [
        get_pipeline_info,
        select_pipeline_item,
        apply_slice_filter,
        apply_clip_filter,
        set_visibility,
        set_color_by,
        set_representation,
        set_opacity,
        set_visual_property,
        auto_fit_scalar_range,
        set_scalar_range,
        set_camera_view,
        set_view_plane,
        reset_camera_view,
        delete_item,
        get_filter_params,
        update_slice_filter_params,
        update_clip_filter_params,
        request_user_input,
    ]

__all__ = [
    "set_pipeline_viewmodel",
    "get_pipeline_viewmodel",
    "set_vtk_viewmodel",
    "get_vtk_viewmodel",
    "get_pipeline_info",
    "select_pipeline_item",
    "delete_item",
    "apply_slice_filter",
    "apply_clip_filter",
    "get_filter_params",
    "update_slice_filter_params",
    "update_clip_filter_params",
    "set_visibility",
    "set_color_by",
    "set_representation",
    "set_opacity",
    "set_visual_property",
    "auto_fit_scalar_range",
    "set_scalar_range",
    "set_camera_view",
    "set_view_plane",
    "reset_camera_view",
    "request_user_input",
    "get_all_tools",
]
