from PySide6.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox, 
                                 QLabel, QCheckBox, QLineEdit, QDoubleSpinBox)
from PySide6.QtCore import Signal
from viewmodels.graph_viewmodel import GraphViewModel

class GraphPropertiesWidget(QWidget):
    """Properties widget for Graph tabs."""
    
    graph_updated = Signal()
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self._item = None
        self._viewmodel = None
        self._setup_ui()
        
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        # Graph type
        self._type_combo = QComboBox()
        self._type_combo.addItems(["line", "scatter", "histogram", "bar"])
        self._type_combo.currentTextChanged.connect(self._on_config_changed)
        form.addRow("Graph Type:", self._type_combo)
        
        # X-axis array
        self._x_array_combo = QComboBox()
        self._x_array_combo.currentTextChanged.connect(self._on_config_changed)
        form.addRow("X Axis Array:", self._x_array_combo)
        
        # Y-axis array
        self._y_array_combo = QComboBox()
        self._y_array_combo.currentTextChanged.connect(self._on_config_changed)
        form.addRow("Y Axis Array:", self._y_array_combo)
        
        # Array type
        self._array_type_combo = QComboBox()
        self._array_type_combo.addItems(["POINT", "CELL"])
        self._array_type_combo.currentTextChanged.connect(self._on_config_changed)
        form.addRow("Array Type:", self._array_type_combo)
        
        # Title
        self._title_edit = QLineEdit()
        self._title_edit.editingFinished.connect(self._on_config_changed)
        form.addRow("Title:", self._title_edit)
        
        # Labels
        self._x_label_edit = QLineEdit()
        self._x_label_edit.editingFinished.connect(self._on_config_changed)
        form.addRow("X Label:", self._x_label_edit)
        
        self._y_label_edit = QLineEdit()
        self._y_label_edit.editingFinished.connect(self._on_config_changed)
        form.addRow("Y Label:", self._y_label_edit)
        
        # Style
        self._grid_check = QCheckBox("Show Grid")
        self._grid_check.setChecked(True)
        self._grid_check.toggled.connect(self._on_config_changed)
        form.addRow("", self._grid_check)
        
        self._legend_check = QCheckBox("Show Legend")
        self._legend_check.toggled.connect(self._on_config_changed)
        form.addRow("", self._legend_check)
        
        layout.addLayout(form)
        layout.addStretch()
        
    def set_item(self, item, viewmodel: GraphViewModel) -> None:
        """Set the current pipeline item and its graph viewmodel."""
        self._item = item
        self._viewmodel = viewmodel
        
        if not item or not viewmodel:
            self._x_array_combo.clear()
            self._y_array_combo.clear()
            self.setEnabled(False)
            return
            
        self.setEnabled(True)
        
        # Update array lists
        self.blockSignals(True)
        self._x_array_combo.clear()
        self._y_array_combo.clear()
        
        self._x_array_combo.addItem("__Index__")
        
        data_arrays = item.get_data_arrays()
        for name, arr_type, components in data_arrays:
            self._x_array_combo.addItem(name)
            self._y_array_combo.addItem(name)
            
        # Set current selection from viewmodel
        config = viewmodel.get_plot_config()
        self._type_combo.setCurrentText(config.get("graph_type", "line"))
        self._x_array_combo.setCurrentText(config.get("x_array", "__Index__"))
        self._y_array_combo.setCurrentText(config.get("y_array", ""))
        self._array_type_combo.setCurrentText(config.get("array_type", "POINT"))
        self._title_edit.setText(config.get("title", ""))
        self._x_label_edit.setText(config.get("x_label", ""))
        self._y_label_edit.setText(config.get("y_label", ""))
        self._grid_check.setChecked(config.get("show_grid", True))
        self._legend_check.setChecked(config.get("show_legend", False))
        
        self.blockSignals(False)
        
    def _on_config_changed(self, *_args) -> None:
        """Handle any configuration change."""
        if not self._item or not self._viewmodel:
            return
            
        # Update viewmodel
        self._viewmodel.set_graph_type(self._type_combo.currentText())
        self._viewmodel.set_data_source(
            self._item.id,
            self._x_array_combo.currentText(),
            self._y_array_combo.currentText(),
            self._array_type_combo.currentText()
        )
        
        self._viewmodel.update_style(
            title=self._title_edit.text(),
            x_label=self._x_label_edit.text(),
            y_label=self._y_label_edit.text(),
            show_grid=self._grid_check.isChecked(),
            show_legend=self._legend_check.isChecked()
        )
        
        self.graph_updated.emit()
