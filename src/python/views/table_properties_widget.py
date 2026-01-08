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
        
        # Array type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["POINT", "CELL"])
        self._type_combo.currentTextChanged.connect(self._on_array_type_changed)
        form.addRow("Array Type:", self._type_combo)
        
        layout.addLayout(form)
        layout.addStretch()
        
    def set_item(self, item, viewmodel: TableViewModel) -> None:
        """Set the current pipeline item and its table viewmodel."""
        self._item = item
        self._viewmodel = viewmodel
        
        if not item or not viewmodel:
            self.setEnabled(False)
            return
            
        self.setEnabled(True)
        
        # Set current selection from viewmodel
        info = viewmodel.get_info()
        current_type = info.get("array_type", "POINT")
        
        self._type_combo.blockSignals(True)
        self._type_combo.setCurrentText(current_type)
        self._type_combo.blockSignals(False)
        
    def _on_array_type_changed(self, _) -> None:
        """Handle array type change."""
        if not self._item or not self._viewmodel:
            return
            
        array_type = self._type_combo.currentText()
        self._viewmodel.set_data_source(self._item.id, array_type)
        # Signal updated to just string (type) if needed, but original signal was (name, type)
        # We can emit ("ALL", array_type) or change signal. 
        # Since TablePropertiesWidget signal 'array_changed' might be connected elsewhere...
        # Let's check usages. 
        # It's NOT connected in MainWindow or PropertiesPanel based on previous reads.
        self.array_changed.emit("ALL", array_type)
