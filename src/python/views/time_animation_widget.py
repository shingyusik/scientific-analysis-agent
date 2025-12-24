from PySide6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, 
                               QSpinBox, QLabel, QComboBox)
from PySide6.QtCore import Signal
from PySide6.QtGui import QIcon
from viewmodels.time_series_manager import TimeSeriesManager


class TimeAnimationWidget(QWidget):
    """Widget for controlling time series animation playback."""
    
    time_index_changed = Signal(int)
    
    def __init__(self, time_manager: TimeSeriesManager, parent=None):
        super().__init__(parent)
        self._time_manager = time_manager
        self._setup_ui()
        self._connect_signals()
        self._update_enabled_state()
    
    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        btn_style = """
            QPushButton {
                min-width: 24px;
                max-width: 24px;
                min-height: 24px;
                max-height: 24px;
                padding: 0px;
                font-size: 10px;
                font-weight: bold;
            }
        """
        
        self._btn_first = QPushButton("|◀")
        self._btn_first.setStyleSheet(btn_style)
        self._btn_first.setToolTip("Go to first step")
        layout.addWidget(self._btn_first)
        
        self._btn_step_back = QPushButton("◀")
        self._btn_step_back.setStyleSheet(btn_style)
        self._btn_step_back.setToolTip("Previous step")
        layout.addWidget(self._btn_step_back)
        
        self._btn_play_back = QPushButton("◀")
        self._btn_play_back.setStyleSheet(btn_style)
        self._btn_play_back.setToolTip("Play backward")
        self._btn_play_back.setCheckable(True)
        layout.addWidget(self._btn_play_back)
        
        self._btn_play_forward = QPushButton("▶")
        self._btn_play_forward.setStyleSheet(btn_style)
        self._btn_play_forward.setToolTip("Play forward")
        self._btn_play_forward.setCheckable(True)
        layout.addWidget(self._btn_play_forward)
        
        self._btn_step_forward = QPushButton("▶")
        self._btn_step_forward.setStyleSheet(btn_style)
        self._btn_step_forward.setToolTip("Next step")
        layout.addWidget(self._btn_step_forward)
        
        self._btn_last = QPushButton("▶|")
        self._btn_last.setStyleSheet(btn_style)
        self._btn_last.setToolTip("Go to last step")
        layout.addWidget(self._btn_last)
        
        self._btn_loop = QPushButton("⟳")
        self._btn_loop.setStyleSheet(btn_style)
        self._btn_loop.setToolTip("Toggle loop")
        self._btn_loop.setCheckable(True)
        layout.addWidget(self._btn_loop)
        
        layout.addSpacing(10)
        
        self._label_time = QLabel("Time:")
        layout.addWidget(self._label_time)
        
        self._combo_time = QComboBox()
        self._combo_time.setMinimumWidth(60)
        self._combo_time.setToolTip("Select time step")
        layout.addWidget(self._combo_time)
        
        self._spin_current = QSpinBox()
        self._spin_current.setMinimum(0)
        self._spin_current.setMaximum(0)
        self._spin_current.setMinimumWidth(50)
        self._spin_current.setToolTip("Current time step")
        layout.addWidget(self._spin_current)
        
        self._label_max = QLabel("max is 0")
        layout.addWidget(self._label_max)
        
        layout.addStretch()
    
    def _connect_signals(self) -> None:
        """Connect widget signals to handlers."""
        self._btn_first.clicked.connect(self._time_manager.go_to_first)
        self._btn_step_back.clicked.connect(self._time_manager.step_backward)
        self._btn_play_back.clicked.connect(self._on_play_back_clicked)
        self._btn_play_forward.clicked.connect(self._on_play_forward_clicked)
        self._btn_step_forward.clicked.connect(self._time_manager.step_forward)
        self._btn_last.clicked.connect(self._time_manager.go_to_last)
        self._btn_loop.clicked.connect(self._on_loop_clicked)
        
        self._combo_time.currentIndexChanged.connect(self._on_combo_changed)
        self._spin_current.valueChanged.connect(self._on_spin_changed)
        
        self._time_manager.time_changed.connect(self._on_time_changed)
        self._time_manager.animation_state_changed.connect(self._on_animation_state_changed)
    
    def _on_play_forward_clicked(self) -> None:
        """Handle play forward button click."""
        self._time_manager.toggle_play_forward()
    
    def _on_play_back_clicked(self) -> None:
        """Handle play backward button click."""
        self._time_manager.toggle_play_backward()
    
    def _on_loop_clicked(self) -> None:
        """Handle loop button click."""
        self._time_manager.set_loop_enabled(self._btn_loop.isChecked())
    
    def _on_combo_changed(self, index: int) -> None:
        """Handle combo box selection change."""
        if index >= 0:
            self._time_manager.set_time_index(index)
    
    def _on_spin_changed(self, value: int) -> None:
        """Handle spin box value change."""
        self._time_manager.set_time_index(value)
    
    def _on_time_changed(self, item_id: str, time_index: int) -> None:
        """Handle time change from manager."""
        self._combo_time.blockSignals(True)
        self._spin_current.blockSignals(True)
        
        self._combo_time.setCurrentIndex(time_index)
        self._spin_current.setValue(time_index)
        
        self._combo_time.blockSignals(False)
        self._spin_current.blockSignals(False)
        
        self.time_index_changed.emit(time_index)
    
    def _on_animation_state_changed(self, is_playing: bool, is_forward: bool) -> None:
        """Handle animation state change."""
        if is_playing:
            if is_forward:
                self._btn_play_forward.setChecked(True)
                self._btn_play_forward.setText("⏸")
                self._btn_play_back.setChecked(False)
                self._btn_play_back.setText("◀")
            else:
                self._btn_play_back.setChecked(True)
                self._btn_play_back.setText("⏸")
                self._btn_play_forward.setChecked(False)
                self._btn_play_forward.setText("▶")
        else:
            self._btn_play_forward.setChecked(False)
            self._btn_play_forward.setText("▶")
            self._btn_play_back.setChecked(False)
            self._btn_play_back.setText("◀")
    
    def update_for_item(self, has_time_series: bool, max_index: int, current_index: int) -> None:
        """Update widget state for a pipeline item."""
        self._combo_time.blockSignals(True)
        self._spin_current.blockSignals(True)
        
        self._combo_time.clear()
        
        if has_time_series:
            for i in range(max_index + 1):
                self._combo_time.addItem(str(i))
            self._combo_time.setCurrentIndex(current_index)
            
            self._spin_current.setMaximum(max_index)
            self._spin_current.setValue(current_index)
            self._label_max.setText(f"max is {max_index}")
        else:
            self._spin_current.setMaximum(0)
            self._spin_current.setValue(0)
            self._label_max.setText("max is 0")
        
        self._combo_time.blockSignals(False)
        self._spin_current.blockSignals(False)
        
        self._update_enabled_state()
    
    def _update_enabled_state(self) -> None:
        """Update enabled state of all controls."""
        has_series = self._time_manager.has_time_series
        
        self._btn_first.setEnabled(has_series)
        self._btn_step_back.setEnabled(has_series)
        self._btn_play_back.setEnabled(has_series)
        self._btn_play_forward.setEnabled(has_series)
        self._btn_step_forward.setEnabled(has_series)
        self._btn_last.setEnabled(has_series)
        self._btn_loop.setEnabled(has_series)
        self._combo_time.setEnabled(has_series)
        self._spin_current.setEnabled(has_series)
    
    def reset(self) -> None:
        """Reset widget to initial state."""
        self._time_manager.pause()
        self._btn_loop.setChecked(False)
        self.update_for_item(False, 0, 0)

