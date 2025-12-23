from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QDoubleSpinBox, QDialog, 
                               QDialogButtonBox, QListWidget, QListWidgetItem,
                               QAbstractItemView, QGroupBox, QFormLayout,
                               QComboBox, QSpinBox)
from PySide6.QtCore import Qt, Signal
from typing import List, Tuple
import numpy as np


class ScientificDoubleSpinBox(QDoubleSpinBox):
    """SpinBox optimized for scientific values."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setDecimals(15)
        self.setRange(-1e30, 1e30)
        self.setStepType(QDoubleSpinBox.AdaptiveDecimalStepType)
    
    def textFromValue(self, value):
        return format(value, '.10g')


class GenerateSeriesDialog(QDialog):
    """Dialog for generating a series of offset values."""
    
    def __init__(self, min_val: float = -1.0, max_val: float = 1.0, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generate Number Series")
        self.setMinimumWidth(400)
        
        self._min_val = min_val
        self._max_val = max_val
        self._result: List[float] = []
        
        layout = QVBoxLayout(self)
        
        range_group = QGroupBox("Range")
        range_layout = QHBoxLayout(range_group)
        
        self._min_spin = ScientificDoubleSpinBox()
        self._min_spin.setValue(min_val)
        self._min_spin.valueChanged.connect(self._update_preview)
        
        range_layout.addWidget(self._min_spin)
        range_layout.addWidget(QLabel("-"))
        
        self._max_spin = ScientificDoubleSpinBox()
        self._max_spin.setValue(max_val)
        self._max_spin.valueChanged.connect(self._update_preview)
        range_layout.addWidget(self._max_spin)
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedWidth(30)
        refresh_btn.setToolTip("Reset to data range")
        refresh_btn.clicked.connect(self._reset_range)
        range_layout.addWidget(refresh_btn)
        
        layout.addWidget(range_group)
        
        type_layout = QFormLayout()
        self._type_combo = QComboBox()
        self._type_combo.addItem("Linear")
        self._type_combo.currentIndexChanged.connect(self._update_preview)
        type_layout.addRow("Type:", self._type_combo)
        
        self._samples_spin = QSpinBox()
        self._samples_spin.setRange(2, 1000)
        self._samples_spin.setValue(10)
        self._samples_spin.valueChanged.connect(self._update_preview)
        type_layout.addRow("Number of Samples:", self._samples_spin)
        layout.addLayout(type_layout)
        
        self._preview_label = QLabel()
        self._preview_label.setWordWrap(True)
        self._preview_label.setStyleSheet("color: #666; padding: 10px;")
        layout.addWidget(self._preview_label)
        
        layout.addStretch()
        
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).setText("Generate")
        button_box.accepted.connect(self._on_generate)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self._update_preview()
    
    def _reset_range(self) -> None:
        """Reset range to initial data range."""
        self._min_spin.setValue(self._min_val)
        self._max_spin.setValue(self._max_val)
    
    def _generate_series(self) -> List[float]:
        """Generate the series based on current settings."""
        min_v = self._min_spin.value()
        max_v = self._max_spin.value()
        n = self._samples_spin.value()
        
        if self._type_combo.currentText() == "Linear":
            return list(np.linspace(min_v, max_v, n))
        return [min_v]
    
    def _update_preview(self) -> None:
        """Update the preview label."""
        series = self._generate_series()
        formatted = [format(v, '.6g') for v in series]
        if len(formatted) > 8:
            preview_text = ", ".join(formatted[:4]) + ", ..., " + ", ".join(formatted[-2:])
        else:
            preview_text = ", ".join(formatted)
        self._preview_label.setText(f"Sample series: {preview_text}")
    
    def _on_generate(self) -> None:
        """Handle generate button click."""
        self._result = self._generate_series()
        self.accept()
    
    def get_result(self) -> List[float]:
        """Get the generated series."""
        return self._result


class OffsetListWidget(QWidget):
    """Widget for managing a list of offset values."""
    
    offsets_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._value_range: Tuple[float, float] = (-1.0, 1.0)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        range_label_layout = QHBoxLayout()
        self._range_label = QLabel("Value Range: [-1.0, 1.0]")
        range_label_layout.addWidget(self._range_label)
        range_label_layout.addStretch()
        layout.addLayout(range_label_layout)
        
        list_layout = QHBoxLayout()
        
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self._list_widget.setMinimumHeight(150)
        self._list_widget.setMaximumHeight(200)
        self._list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        list_layout.addWidget(self._list_widget)
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(2)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(30, 30)
        add_btn.setToolTip("Add new offset value")
        add_btn.clicked.connect(self._on_add)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("-")
        remove_btn.setFixedSize(30, 30)
        remove_btn.setToolTip("Remove selected offset")
        remove_btn.clicked.connect(self._on_remove)
        btn_layout.addWidget(remove_btn)
        
        series_btn = QPushButton("⋯")
        series_btn.setFixedSize(30, 30)
        series_btn.setToolTip("Generate number series")
        series_btn.clicked.connect(self._on_generate_series)
        btn_layout.addWidget(series_btn)
        
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(30, 30)
        clear_btn.setToolTip("Clear all offsets")
        clear_btn.clicked.connect(self._on_clear)
        btn_layout.addWidget(clear_btn)
        
        refresh_btn = QPushButton("↻")
        refresh_btn.setFixedSize(30, 30)
        refresh_btn.setToolTip("Refresh value range")
        refresh_btn.clicked.connect(self._on_refresh_range)
        btn_layout.addWidget(refresh_btn)
        
        btn_layout.addStretch()
        list_layout.addLayout(btn_layout)
        
        layout.addLayout(list_layout)
        
        self._add_item(0.0)
    
    def set_value_range(self, min_val: float, max_val: float) -> None:
        """Set the valid value range for offsets."""
        self._value_range = (min_val, max_val)
        self._range_label.setText(f"Value Range: [{format(min_val, '.7g')}, {format(max_val, '.7g')}]")
    
    def set_offsets(self, offsets: List[float]) -> None:
        """Set the offset values."""
        self._list_widget.clear()
        for offset in offsets:
            self._add_item(offset)
    
    def get_offsets(self) -> List[float]:
        """Get current offset values."""
        offsets = []
        for i in range(self._list_widget.count()):
            item = self._list_widget.item(i)
            offsets.append(item.data(Qt.UserRole))
        return offsets
    
    def _add_item(self, value: float) -> None:
        """Add a new offset item."""
        item = QListWidgetItem(format(value, '.15g'))
        item.setData(Qt.UserRole, value)
        self._list_widget.addItem(item)
    
    def _on_add(self) -> None:
        """Add a new offset value at 0."""
        self._add_item(0.0)
        self._emit_change()
    
    def _on_remove(self) -> None:
        """Remove selected offset."""
        current = self._list_widget.currentRow()
        if current >= 0 and self._list_widget.count() > 1:
            self._list_widget.takeItem(current)
            self._emit_change()
    
    def _on_generate_series(self) -> None:
        """Open generate series dialog."""
        dialog = GenerateSeriesDialog(self._value_range[0], self._value_range[1], self)
        if dialog.exec() == QDialog.Accepted:
            series = dialog.get_result()
            self._list_widget.clear()
            for value in series:
                self._add_item(value)
            self._emit_change()
    
    def _on_clear(self) -> None:
        """Clear all offsets and add default 0."""
        self._list_widget.clear()
        self._add_item(0.0)
        self._emit_change()
    
    def _on_refresh_range(self) -> None:
        """Request range refresh (parent should handle this)."""
        pass
    
    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle double-click to edit value."""
        from PySide6.QtWidgets import QInputDialog
        current_value = item.data(Qt.UserRole)
        new_value, ok = QInputDialog.getDouble(
            self, "Edit Offset", "Offset value:",
            current_value, -1e30, 1e30, 10
        )
        if ok:
            item.setText(format(new_value, '.15g'))
            item.setData(Qt.UserRole, new_value)
            self._emit_change()
    
    def _emit_change(self) -> None:
        """Emit offsets changed signal."""
        self.offsets_changed.emit(self.get_offsets())

