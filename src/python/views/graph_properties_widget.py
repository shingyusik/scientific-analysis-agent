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
        form.addRow("Graph Type:", self._type_combo)
        
        # X-axis array
        self._x_array_combo = QComboBox()
        form.addRow("X Axis Array:", self._x_array_combo)
        
        # Y-axis array
        self._y_array_combo = QComboBox()
        self._y_array_combo.currentIndexChanged.connect(self._on_y_array_changed)
        form.addRow("Y Axis Array:", self._y_array_combo)
        
        # Y-axis component
        self._y_component_combo = QComboBox()
        self._y_component_combo.addItem("Magnitude", -1)
        self._y_component_combo.setEnabled(False)
        form.addRow("  Component:", self._y_component_combo)
        
        # Array type
        self._array_type_combo = QComboBox()
        self._array_type_combo.addItems(["POINT", "CELL"])
        form.addRow("Array Type:", self._array_type_combo)
        
        # Title
        self._title_edit = QLineEdit()
        form.addRow("Title:", self._title_edit)
        
        # Labels
        self._x_label_edit = QLineEdit()
        form.addRow("X Label:", self._x_label_edit)
        
        self._y_label_edit = QLineEdit()
        form.addRow("Y Label:", self._y_label_edit)
        
        # Style
        self._grid_check = QCheckBox("Show Grid")
        self._grid_check.setChecked(True)
        form.addRow("", self._grid_check)
        
        self._legend_check = QCheckBox("Show Legend")
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
        
        self._x_array_combo.addItem("__Index__", 1)
        
        data_arrays = item.get_data_arrays()
        for name, arr_type, components in data_arrays:
            # Store component count in user data
            self._x_array_combo.addItem(name, components)
            self._y_array_combo.addItem(name, components)
            
        # Set current selection from viewmodel
        # Use item_id to get series-specific config (arrays, components)
        config = viewmodel.get_plot_config(item.id)
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
        
        # Update component options
        self._on_y_array_changed()
        
        # Restore component selection
        y_comp = config.get("y_component", 0)
        # Find data and select
        idx = self._y_component_combo.findData(y_comp)
        if idx >= 0:
            self._y_component_combo.setCurrentIndex(idx)
        
    def _on_y_array_changed(self, index: int = -1) -> None:
        """Update component dropdown based on selected Y array."""
        idx = self._y_array_combo.currentIndex()
        if idx < 0:
            return
            
        num_components = self._y_array_combo.itemData(idx)
        if num_components is None:
            num_components = 1
            
        self._y_component_combo.blockSignals(True)
        self._y_component_combo.clear()
        
        if num_components > 1:
            self._y_component_combo.addItem("Magnitude", -1)
            self._y_component_combo.addItem("X", 0)
            self._y_component_combo.addItem("Y", 1)
            if num_components >= 3:
                self._y_component_combo.addItem("Z", 2)
            self._y_component_combo.setEnabled(True)
            self._y_component_combo.setCurrentIndex(0) # Default to Magnitude
        else:
            self._y_component_combo.addItem("Magnitude", -1)
            self._y_component_combo.setEnabled(False)
            
        self._y_component_combo.blockSignals(False)
        
    def apply_changes(self) -> None:
        """Apply the current configuration to the viewmodel."""
        if not self._item or not self._viewmodel:
            return
            
        # Get selected component
        y_component = 0
        if self._y_component_combo.isEnabled():
            y_component = self._y_component_combo.currentData()
            if y_component is None:
                y_component = -1 # Default to Magnitude if issue
        
        # Update viewmodel
        self._viewmodel.set_graph_type(self._type_combo.currentText())
        self._viewmodel.set_data_source(
            self._item.id,
            self._x_array_combo.currentText(),
            self._y_array_combo.currentText(),
            self._array_type_combo.currentText(),
            x_component=0, # Assuming X-axis usually uses Index or scalar
            y_component=y_component
        )
        
        self._viewmodel.set_plot_style(
            title=self._title_edit.text(),
            x_label=self._x_label_edit.text(),
            y_label=self._y_label_edit.text(),
            show_grid=self._grid_check.isChecked(),
            show_legend=self._legend_check.isChecked()
        )
        
        self.graph_updated.emit()
