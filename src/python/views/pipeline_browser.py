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
        self._all_items: Dict[str, PipelineItem] = {}
        
        self.itemChanged.connect(self._on_item_changed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        self.itemSelectionChanged.connect(self._on_selection_changed)
    
    def add_item(self, pipeline_item: PipelineItem) -> QTreeWidgetItem:
        """Add a pipeline item and rebuild tree to maintain correct order."""
        self._all_items[pipeline_item.id] = pipeline_item
        self._rebuild_tree()
        return self._item_map.get(pipeline_item.id)
    
    def _rebuild_tree(self) -> None:
        """Rebuild entire tree based on branching logic."""
        selected_id = self.get_selected_item_id()
        
        self.blockSignals(True)
        self.clear()
        self._item_map.clear()
        
        roots = [item for item in self._all_items.values() if not item.parent_id]
        for root in roots:
            self._add_item_recursive(root, None)
        
        self.blockSignals(False)
        
        if selected_id and selected_id in self._item_map:
            self.setCurrentItem(self._item_map[selected_id])
    
    def _add_item_recursive(self, item: PipelineItem, ui_parent: Optional[QTreeWidgetItem]) -> None:
        """Recursively add item. If only one child, keep same level."""
        if ui_parent:
            tree_item = QTreeWidgetItem(ui_parent)
            ui_parent.setExpanded(True)
        else:
            tree_item = QTreeWidgetItem(self)
        
        tree_item.setText(0, item.name)
        tree_item.setCheckState(0, Qt.Checked if item.visible else Qt.Unchecked)
        tree_item.setData(0, Qt.UserRole, item.id)
        self._item_map[item.id] = tree_item
        
        children = [child for child in self._all_items.values() if child.parent_id == item.id]
        
        if len(children) == 1:
            self._add_item_recursive(children[0], ui_parent)
        else:
            for child in children:
                self._add_item_recursive(child, tree_item)
    
    def remove_item(self, item_id: str) -> None:
        """Remove an item from the tree and rebuild if needed."""
        if item_id not in self._all_items:
            return
        
        del self._all_items[item_id]
        self._rebuild_tree()
    
    def update_item(self, pipeline_item: PipelineItem) -> None:
        """Update tree item display."""
        self._all_items[pipeline_item.id] = pipeline_item
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
        self._all_items.clear()
    
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

