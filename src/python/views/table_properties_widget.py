from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, 
                                 QLabel, QCheckBox, QPushButton)
from PySide6.QtCore import Signal
from viewmodels.table_viewmodel import TableViewModel

class TablePropertiesWidget(QWidget):
    """Properties widget for Table tabs."""
    
    array_changed = Signal(str, str) # array_name, array_type
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._item = None
        self._viewmodel = None
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Array selection
        self._array_combo = QComboBox()
        self._array_combo.currentTextChanged.connect(self._on_array_changed)
        form.addRow("Data Array:", self._array_combo)
        
        # Array type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["POINT", "CELL"])
        self._type_combo.currentTextChanged.connect(self._on_array_changed)
        form.addRow("Array Type:", self._type_combo)
        
        layout.addLayout(form)
        layout.addStretch()
        
    def set_item(self, item, viewmodel: TableViewModel) -> None:
        """Set the current pipeline item and its table viewmodel."""
        self._item = item
        self._viewmodel = viewmodel
        
        if not item or not viewmodel:
            self._array_combo.clear()
            self.setEnabled(False)
            return
            
        self.setEnabled(True)
        
        # Update array list
        self._array_combo.blockSignals(True)
        self._array_combo.clear()
        
        data_arrays = item.get_data_arrays()
        for name, arr_type, components in data_arrays:
            self._array_combo.addItem(name)
            
        # Set current selection from viewmodel
        info = viewmodel.get_info()
        current_array = info.get("array_name")
        current_type = info.get("array_type", "POINT")
        
        if current_array:
            self._array_combo.setCurrentText(current_array)
        
        self._type_combo.setCurrentText(current_type)
        self._array_combo.blockSignals(False)
        
    def _on_array_changed(self, _) -> None:
        """Handle array or type change."""
        if not self._item or not self._viewmodel:
            return
            
        array_name = self._array_combo.currentText()
        array_type = self._type_combo.currentText()
        
        if array_name:
            self._viewmodel.set_data_source(self._item.id, array_name, array_type)
            self.array_changed.emit(array_name, array_type)
