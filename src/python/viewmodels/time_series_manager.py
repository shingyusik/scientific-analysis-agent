from PySide6.QtCore import QObject, Signal, QTimer
from typing import Optional
from models.pipeline_item import PipelineItem
from utils.logger import get_logger, log_execution
from utils.tool_registry import expose_tool

logger = get_logger("TimeSeriesMgr")


class TimeSeriesManager(QObject):
    """Manages time series playback and animation."""
    
    time_changed = Signal(str, int)  # item_id, time_index
    animation_state_changed = Signal(bool, bool)  # is_playing, is_forward
    animation_start_requested = Signal(bool)  # True for forward, False for backward
    
    DEFAULT_INTERVAL_MS = 100
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_item: Optional[PipelineItem] = None
        self._is_playing = False
        self._play_forward = True
        self._loop_enabled = False
        self._interval_ms = self.DEFAULT_INTERVAL_MS
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_timer_tick)
        
        # Connect signal to slot for thread-safe timer control
        self.animation_start_requested.connect(self._start_animation_timer)
    
    @property
    def current_item(self) -> Optional[PipelineItem]:
        return self._current_item
    
    @property
    def is_playing(self) -> bool:
        return self._is_playing
    
    @property
    def is_playing_forward(self) -> bool:
        return self._play_forward
    
    @property
    def loop_enabled(self) -> bool:
        return self._loop_enabled
    
    @property
    def interval_ms(self) -> int:
        return self._interval_ms
    
    @property
    def current_index(self) -> int:
        if self._current_item and self._current_item.is_time_series:
            return self._current_item.current_time_index
        return 0
    
    @property
    def max_index(self) -> int:
        if self._current_item and self._current_item.is_time_series:
            return self._current_item.max_time_index
        return 0
    
    @property
    def has_time_series(self) -> bool:
        return self._current_item is not None and self._current_item.is_time_series
    
    @log_execution(start_msg="Time Series Item Set", end_msg="Time Series Item Setting Completed")
    def set_item(self, item: Optional[PipelineItem]) -> None:
        """Set the current item to control."""
        if self._is_playing:
            self.pause()
        
        self._current_item = item
        if item:
            logger.info(f"Time series item set: {item.name} (Max index: {item.max_time_index})")
    
    @expose_tool(
        name="set_loop_playback",
        description=(
            "Enables or disables looping for time series playback.\n"
            "Parameters:\n"
            "- enabled: True to enable looping, False to disable.\n"
            "Returns:\n"
            "- None."
        )
    )
    def set_loop_enabled(self, enabled: bool) -> None:
        """Enable or disable loop playback."""
        self._loop_enabled = enabled
        logger.info(f"Loop playback enabled: {enabled}")
    
    @expose_tool(
        name="set_playback_speed",
        description=(
            "Sets the animation speed.\n"
            "Parameters:\n"
            "- interval_ms: Delay between frames in milliseconds (min 10).\n"
            "Returns:\n"
            "- None."
        )
    )
    def set_interval(self, interval_ms: int) -> None:
        """Set animation interval in milliseconds."""
        old_interval = self._interval_ms
        self._interval_ms = max(10, interval_ms)
        if self._is_playing:
            self._timer.setInterval(self._interval_ms)
        
        if old_interval != self._interval_ms:
            logger.info(f"Animation interval set to {self._interval_ms}ms")
    
    @expose_tool(
        name="play_animation",
        description=(
            "Starts playing the time series animation forwards.\n"
            "Returns:\n"
            "- None."
        )
    )
    @log_execution(start_msg="Forward Play Started", end_msg="Forward Play activated")
    def play_forward(self) -> None:
        """Start forward animation playback."""
        # Auto-detect time series item if not set
        if not self.has_time_series:
            self._auto_select_time_series_item()
        
        # Check again after auto-selection attempt
        if not self.has_time_series:
            logger.warning("No time series item available for playback")
            return
        
        if self._is_playing and self._play_forward:
            return
        
        if self._is_playing:
            self.pause()
        
        self._play_forward = True
        
        if self.current_index >= self.max_index and not self._loop_enabled:
            self.go_to_first()
        
        self._is_playing = True
        # Request timer start via signal for thread safety
        self.animation_start_requested.emit(True)
        self.animation_state_changed.emit(True, True)
    
    def _auto_select_time_series_item(self) -> None:
        """Automatically find and select a time series item from the pipeline."""
        from utils.app_context import get_pipeline_viewmodel
        pipeline_vm = get_pipeline_viewmodel()
        
        if not pipeline_vm:
            logger.warning("PipelineViewModel not available for auto-selection")
            return
        
        # Find first time series item in pipeline
        for item in pipeline_vm.items.values():
            if item.is_time_series:
                logger.info(f"Auto-selected time series item: {item.name}")
                self.set_item(item)
                return
        
        logger.warning("No time series items found in pipeline")
    
    def _start_animation_timer(self, forward: bool) -> None:
        """Slot to start timer in main thread (called via signal)."""
        self._timer.start(self._interval_ms)
        logger.debug(f"Animation timer started ({'forward' if forward else 'backward'})")
    
    @log_execution(start_msg="Backward Play Started", end_msg="Backward Play activated")
    def play_backward(self) -> None:
        """Start backward animation playback."""
        if not self.has_time_series:
            return
        
        if self._is_playing and not self._play_forward:
            return
        
        if self._is_playing:
            self.pause()
        
        self._play_forward = False
        
        if self.current_index <= 0 and not self._loop_enabled:
            self.go_to_last()
        
        self._is_playing = True
        # Request timer start via signal for thread safety
        self.animation_start_requested.emit(False)
        self.animation_state_changed.emit(True, False)
    
    @expose_tool(
        name="pause_animation",
        description=(
            "Pauses the currently running animation.\n"
            "Returns:\n"
            "- None."
        )
    )
    @log_execution(start_msg="Playback Paused", end_msg="Playback Paused")
    def pause(self) -> None:
        """Pause animation playback."""
        if not self._is_playing:
            return
        
        self._is_playing = False
        self._timer.stop()
        self.animation_state_changed.emit(False, self._play_forward)
    
    def toggle_play_forward(self) -> None:
        """Toggle forward play and pause."""
        if self._is_playing and self._play_forward:
            self.pause()
        else:
            self.play_forward()
    
    def toggle_play_backward(self) -> None:
        """Toggle backward play and pause."""
        if self._is_playing and not self._play_forward:
            self.pause()
        else:
            self.play_backward()
    
    @expose_tool(
        name="go_to_first_step",
        description=(
            "Jumps to the very first time step (index 0).\n"
            "Returns:\n"
            "- None."
        )
    )
    def go_to_first(self) -> None:
        """Go to first time step."""
        if not self.has_time_series:
            self._auto_select_time_series_item()
        self.set_time_index(0)
    
    @expose_tool(
        name="go_to_last_step",
        description=(
            "Jumps to the very last time step.\n"
            "Returns:\n"
            "- None."
        )
    )
    def go_to_last(self) -> None:
        """Go to last time step."""
        if not self.has_time_series:
            self._auto_select_time_series_item()
        self.set_time_index(self.max_index)
    
    @expose_tool(
        name="step_forward_animation",
        description=(
            "Moves one time step forward.\n"
            "Returns:\n"
            "- None."
        )
    )
    def step_forward(self) -> None:
        """Advance one time step."""
        if not self.has_time_series:
            self._auto_select_time_series_item()
        
        if not self.has_time_series:
            return
        
        new_index = self.current_index + 1
        if new_index > self.max_index:
            if self._loop_enabled:
                new_index = 0
            else:
                return
        
        self.set_time_index(new_index)
    
    @expose_tool(
        name="step_backward_animation",
        description=(
            "Moves one time step backward.\n"
            "Returns:\n"
            "- None."
        )
    )
    def step_backward(self) -> None:
        """Go back one time step."""
        if not self.has_time_series:
            self._auto_select_time_series_item()
        
        if not self.has_time_series:
            return
        
        new_index = self.current_index - 1
        if new_index < 0:
            if self._loop_enabled:
                new_index = self.max_index
            else:
                return
        
        self.set_time_index(new_index)
    
    @expose_tool(
        name="set_time_step",
        description=(
            "Jumps to a specific time step index.\n"
            "Parameters:\n"
            "- index: Integer time step index (0 to max_index).\n"
            "Returns:\n"
            "- None."
        )
    )
    @log_execution(level="DEBUG") # Frequent calls, use DEBUG
    def set_time_index(self, index: int) -> None:
        """Set specific time index."""
        if not self._current_item or not self._current_item.is_time_series:
            self._auto_select_time_series_item()
        
        if not self._current_item or not self._current_item.is_time_series:
            return
        
        if self._current_item.set_time_index(index):
            self.time_changed.emit(self._current_item.id, self._current_item.current_time_index)
    
    def _on_timer_tick(self) -> None:
        """Handle timer tick for animation."""
        if not self.has_time_series:
            self.pause()
            return
        
        if self._play_forward:
            new_index = self.current_index + 1
            if new_index > self.max_index:
                if self._loop_enabled:
                    new_index = 0
                else:
                    self.pause()
                    return
        else:
            new_index = self.current_index - 1
            if new_index < 0:
                if self._loop_enabled:
                    new_index = self.max_index
                else:
                    self.pause()
                    return
        
        self.set_time_index(new_index)

