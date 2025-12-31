from PySide6.QtCore import QObject, Signal, QEventLoop, QTimer
from typing import Tuple, List, Any, Optional
from services.vtk_render_service import VTKRenderService
from utils.logger import get_logger

logger = get_logger("VTKVM")


class VTKViewModel(QObject):
    """ViewModel for VTK viewer state management."""
    
    render_requested = Signal()
    background_changed = Signal(tuple, object)  # (color1, color2 or None)
    camera_reset_requested = Signal()
    view_plane_requested = Signal(str)  # "xy", "yz", "xz"
    actor_added = Signal(object)  # actor
    actor_removed = Signal(object)  # actor
    actor_visibility_changed = Signal(object, bool)  # actor, visible
    clear_scene_requested = Signal()
    plane_preview_requested = Signal(list, list, tuple)  # origin, normal, bounds
    plane_preview_hide_requested = Signal()
    scalar_bar_update_requested = Signal(object)  # actor
    scalar_bar_hide_requested = Signal()
    legend_settings_changed = Signal(dict)  # legend settings dictionary
    
    # Camera controls
    camera_query_requested = Signal()
    camera_state_changed = Signal(dict)
    camera_apply_requested = Signal(dict)
    
    BACKGROUND_PRESETS = [
        ("Warm Gray (Default)", (0.32, 0.34, 0.43), None),
        ("Blue Gray", (0.2, 0.3, 0.4), None),
        ("Dark Gray", (0.1, 0.1, 0.1), None),
        ("Neutral Gray", (0.5, 0.5, 0.5), None),
        ("Light Gray", (0.8, 0.8, 0.8), None),
        ("White", (1.0, 1.0, 1.0), None),
        ("Black", (0.0, 0.0, 0.0), None),
        ("Gradient Background", (0.32, 0.34, 0.43), (0.0, 0.0, 0.0)),
    ]
    
    REPRESENTATION_STYLES = ["Points", "Point Gaussian", "Wireframe", "Surface", "Surface With Edges"]
    
    def __init__(self, render_service: VTKRenderService):
        super().__init__()
        self._render_service = render_service
        self._current_background = self.BACKGROUND_PRESETS[0]
        self._last_camera_state = {}
    
    @property
    def render_service(self) -> VTKRenderService:
        return self._render_service
    
    def set_background(self, color1: Tuple[float, float, float], 
                       color2: Tuple[float, float, float] = None) -> None:
        """Set background color."""
        self._current_background = ("Custom", color1, color2)
        self._current_background = ("Custom", color1, color2)
        self.background_changed.emit(color1, color2)
        logger.info(f"배경색 변경: Custom ({color1}, {color2})")
    
    def set_background_preset(self, preset_name: str) -> None:
        """Set background from preset."""
        for name, c1, c2 in self.BACKGROUND_PRESETS:
            if name == preset_name:
                self._current_background = (name, c1, c2)
                self.background_changed.emit(c1, c2)
                logger.info(f"배경색 프리셋 변경: {preset_name}")
                break
    
    def reset_camera(self) -> None:
        """Request camera reset."""
        self.camera_reset_requested.emit()
        logger.info("카메라 리셋 요청")
    
    def set_view_plane(self, plane: str) -> None:
        """Request view plane change."""
        if plane in ("xy", "yz", "xz"):
            self.view_plane_requested.emit(plane)
            logger.info(f"뷰 평면 변경 요청: {plane}")
    
    def add_actor(self, actor: Any) -> None:
        """Request actor to be added to renderer."""
        self.actor_added.emit(actor)
        self.render_requested.emit()
    
    def remove_actor(self, actor: Any) -> None:
        """Request actor to be removed from renderer."""
        self.actor_removed.emit(actor)
        self.render_requested.emit()
    
    def set_actor_visibility(self, actor: Any, visible: bool) -> None:
        """Request actor visibility change."""
        self.actor_visibility_changed.emit(actor, visible)
        self.render_requested.emit()
    
    def clear_scene(self) -> None:
        """Request to clear all actors from scene."""
        self.clear_scene_requested.emit()
    
    def request_render(self) -> None:
        """Request a render update."""
        self.render_requested.emit()
    
    def show_plane_preview(self, origin: List[float], normal: List[float], 
                           bounds: Tuple[float, ...]) -> None:
        """Request plane preview display."""
        self.plane_preview_requested.emit(origin, normal, bounds)
    
    def hide_plane_preview(self) -> None:
        """Request to hide plane preview."""
        self.plane_preview_hide_requested.emit()
    
    def update_scalar_bar(self, actor: Any) -> None:
        """Request scalar bar update for actor."""
        self.scalar_bar_update_requested.emit(actor)
    
    def hide_scalar_bar(self) -> None:
        """Request to hide scalar bar."""
        self.scalar_bar_hide_requested.emit()
    
    def set_legend_settings(self, settings: dict) -> None:
        """Request legend settings update."""
        self.legend_settings_changed.emit(settings)
        self.render_requested.emit()
    
    def request_camera_query(self) -> None:
        """Request current camera state."""
        self.camera_query_requested.emit()
    
    def notify_camera_state(self, state: dict) -> None:
        """Notify that camera state has been retrieved."""
        self._last_camera_state = state
        self.camera_state_changed.emit(state)
        
    def get_camera_state_sync(self, timeout_ms: int = 1000) -> dict:
        """Get the current camera state synchronously using a local event loop."""
        loop = QEventLoop()
        result_captured = [False]
        state_data = {}

        def on_state(state):
            nonlocal state_data
            state_data = state
            result_captured[0] = True
            loop.quit()

        self.camera_state_changed.connect(on_state)
        self.camera_query_requested.emit()
        
        # Use a timer for timeout
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        timer.start(timeout_ms)

        loop.exec()
        
        self.camera_state_changed.disconnect(on_state)
        
        if result_captured[0]:
            return state_data
        return self._last_camera_state  # Return cached state if timeout
    
    def apply_camera_state(self, state: dict) -> None:
        """Apply new camera settings (position, focal_point, view_up, zoom)."""
        self.camera_apply_requested.emit(state)
        self.render_requested.emit()
        logger.info(f"카메라 상태 적용: {state}")
    
    def get_representation_style(self, actor: Any) -> str:
        """Get actor's current representation style."""
        return self._render_service.get_representation_style(actor)
    
    def get_data_arrays(self, data: Any) -> List[Tuple[str, str, int]]:
        """Get available data arrays with component count."""
        if data:
            return self._render_service.get_data_arrays(data)
        return []
    
    def fit_scalar_range(self, actor: Any) -> bool:
        """Fit scalar range to data min/max."""
        return self._render_service.fit_scalar_range(actor)
    
    def set_custom_scalar_range(self, actor: Any, min_val: float, max_val: float) -> bool:
        """Set custom scalar range."""
        return self._render_service.set_custom_scalar_range(actor, min_val, max_val)

