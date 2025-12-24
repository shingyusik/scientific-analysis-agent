from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from typing import Optional, Dict
from models.pipeline_item import PipelineItem


class PipelineBrowserWidget(QTreeWidget):
    """Widget for displaying and managing pipeline items."""
    
    item_selected = Signal(str)  # item_id
    item_visibility_changed = Signal(str, bool)  # item_id, visible
    item_delete_requested = Signal(str)  # item_id
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabel("Pipeline Browser")
        
        self._item_map: Dict[str, QTreeWidgetItem] = {}
        
        self.itemChanged.connect(self._on_item_changed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def add_item(self, pipeline_item: PipelineItem) -> QTreeWidgetItem:
        """Add a pipeline item to the tree."""
        if pipeline_item.parent_id and pipeline_item.parent_id in self._item_map:
            parent_widget = self._item_map[pipeline_item.parent_id]
            tree_item = QTreeWidgetItem(parent_widget)
            parent_widget.setExpanded(True)
        else:
            tree_item = QTreeWidgetItem(self)
        
        tree_item.setText(0, pipeline_item.name)
        tree_item.setCheckState(0, Qt.Checked if pipeline_item.visible else Qt.Unchecked)
        tree_item.setData(0, Qt.UserRole, pipeline_item.id)
        
        self._item_map[pipeline_item.id] = tree_item
        
        if not pipeline_item.parent_id:
            self.setCurrentItem(tree_item)
        
        return tree_item
    
    def remove_item(self, item_id: str) -> None:
        """Remove an item from the tree."""
        tree_item = self._item_map.get(item_id)
        if not tree_item:
            return
        
        parent = tree_item.parent()
        if parent:
            parent.removeChild(tree_item)
        else:
            index = self.indexOfTopLevelItem(tree_item)
            if index != -1:
                self.takeTopLevelItem(index)
        
        del self._item_map[item_id]
    
    def update_item(self, pipeline_item: PipelineItem) -> None:
        """Update tree item display."""
        tree_item = self._item_map.get(pipeline_item.id)
        if tree_item:
            tree_item.setText(0, pipeline_item.name)
            self.blockSignals(True)
            tree_item.setCheckState(0, Qt.Checked if pipeline_item.visible else Qt.Unchecked)
            self.blockSignals(False)
    
    def select_item(self, item_id: str) -> None:
        """Select an item in the tree without emitting signals."""
        tree_item = self._item_map.get(item_id)
        if tree_item:
            self.blockSignals(True)
            self.setCurrentItem(tree_item)
            self.blockSignals(False)
    
    def get_selected_item_id(self) -> Optional[str]:
        """Get the ID of the currently selected item."""
        current = self.currentItem()
        if current:
            return current.data(0, Qt.UserRole)
        return None
    
    def clear_all(self) -> None:
        """Clear all items."""
        self.clear()
        self._item_map.clear()
    
    def _on_item_changed(self, item: QTreeWidgetItem, column: int) -> None:
        """Handle item checkbox changes."""
        item_id = item.data(0, Qt.UserRole)
        if item_id:
            visible = item.checkState(0) == Qt.Checked
            self.item_visibility_changed.emit(item_id, visible)
    
    def _on_selection_changed(self) -> None:
        """Handle selection changes."""
        item_id = self.get_selected_item_id()
        self.item_selected.emit(item_id if item_id else "")
    
    def _show_context_menu(self, position) -> None:
        """Show context menu."""
        item = self.itemAt(position)
        if not item:
            return
        
        item_id = item.data(0, Qt.UserRole)
        if not item_id:
            return
        
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        action = menu.exec(self.viewport().mapToGlobal(position))
        
        if action == delete_action:
            self.item_delete_requested.emit(item_id)

