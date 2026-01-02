from PySide6.QtCore import QObject, Signal, QTimer
from typing import Optional
from models.pipeline_item import PipelineItem
from utils.logger import get_logger, log_execution

logger = get_logger("TimeSeriesMgr")


class TimeSeriesManager(QObject):
    """Manages time series animation and playback."""
    
    time_changed = Signal(str, int)  # item_id, time_index
    animation_state_changed = Signal(bool, bool)  # is_playing, is_forward
    
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
    
    def set_loop_enabled(self, enabled: bool) -> None:
        """Enable or disable loop playback."""
        self._loop_enabled = enabled
        logger.info(f"Loop playback enabled: {enabled}")
    
    def set_interval(self, interval_ms: int) -> None:
        """Set animation interval in milliseconds."""
        old_interval = self._interval_ms
        self._interval_ms = max(10, interval_ms)
        if self._is_playing:
            self._timer.setInterval(self._interval_ms)
        
        if old_interval != self._interval_ms:
            logger.info(f"Animation interval set to {self._interval_ms}ms")
    
    @log_execution(start_msg="Forward Play Started", end_msg="Forward Play activated")
    def play_forward(self) -> None:
        """Start forward animation playback."""
        if not self.has_time_series:
            return
        
        if self._is_playing and self._play_forward:
            return
        
        if self._is_playing:
            self._timer.stop()
        
        self._play_forward = True
        
        if self.current_index >= self.max_index and not self._loop_enabled:
            self.go_to_first()
        
        self._is_playing = True
        self._timer.start(self._interval_ms)
        self.animation_state_changed.emit(True, True)
    
    @log_execution(start_msg="Backward Play Started", end_msg="Backward Play activated")
    def play_backward(self) -> None:
        """Start backward animation playback."""
        if not self.has_time_series:
            return
        
        if self._is_playing and not self._play_forward:
            return
        
        if self._is_playing:
            self._timer.stop()
        
        self._play_forward = False
        
        if self.current_index <= 0 and not self._loop_enabled:
            self.go_to_last()
        
        self._is_playing = True
        self._timer.start(self._interval_ms)
        self.animation_state_changed.emit(True, False)
    
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
    
    def go_to_first(self) -> None:
        """Go to first time step."""
        self.set_time_index(0)
    
    def go_to_last(self) -> None:
        """Go to last time step."""
        self.set_time_index(self.max_index)
    
    def step_forward(self) -> None:
        """Advance one time step."""
        if not self.has_time_series:
            return
        
        new_index = self.current_index + 1
        if new_index > self.max_index:
            if self._loop_enabled:
                new_index = 0
            else:
                return
        
        self.set_time_index(new_index)
    
    def step_backward(self) -> None:
        """Go back one time step."""
        if not self.has_time_series:
            return
        
        new_index = self.current_index - 1
        if new_index < 0:
            if self._loop_enabled:
                new_index = self.max_index
            else:
                return
        
        self.set_time_index(new_index)
    
    @log_execution(level="DEBUG") # Frequent calls, use DEBUG
    def set_time_index(self, index: int) -> None:
        """Set specific time index."""
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

