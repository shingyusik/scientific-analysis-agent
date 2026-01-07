from PySide6.QtWidgets import (QTabWidget, QWidget, QMenu, QInputDialog, QMessageBox,
                                QToolButton, QDialog, QVBoxLayout, QLabel, QComboBox,
                                QLineEdit, QDialogButtonBox, QFormLayout)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from typing import Dict, Optional
from utils.logger import get_logger

logger = get_logger("TabbedViewWidget")


class TabCreationDialog(QDialog):
    """Dialog for creating new tabs."""
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Create New Tab")
        self.setModal(True)
        
        layout = QFormLayout(self)
        
        # Tab type selection
        self._type_combo = QComboBox()
        self._type_combo.addItems(["VTK Render View", "Table View", "Graph View"])
        layout.addRow("Tab Type:", self._type_combo)
        
        # Tab name
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Enter tab name...")
        layout.addRow("Tab Name:", self._name_edit)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        # Set default name based on type
        self._type_combo.currentTextChanged.connect(self._update_default_name)
        self._update_default_name(self._type_combo.currentText())
        
    def _update_default_name(self, tab_type: str) -> None:
        """Update default name based on selected type."""
        if tab_type == "VTK Render View":
            self._name_edit.setText("Render View")
        elif tab_type == "Table View":
            self._name_edit.setText("Table")
        elif tab_type == "Graph View":
            self._name_edit.setText("Graph")
    
    def get_tab_type(self) -> str:
        """Get selected tab type."""
        type_map = {
            "VTK Render View": "vtk",
            "Table View": "table",
            "Graph View": "graph"
        }
        return type_map.get(self._type_combo.currentText(), "vtk")
    
    def get_tab_name(self) -> str:
        """Get entered tab name."""
        return self._name_edit.text().strip() or "New Tab"


class TabbedViewWidget(QTabWidget):
    """
    Enhanced QTabWidget with tab management features:
    - Add/Remove tabs
    - Reorderable tabs (drag-and-drop)
    - Pinnable tabs (cannot be closed)
    """
    
    tab_created = Signal(str, str, str)  # tab_id, tab_type, tab_name
    tab_closed = Signal(str)  # tab_id
    tab_pinned = Signal(str, bool)  # tab_id, pinned
    tab_renamed = Signal(str, str)  # tab_id, new_name
    
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        
        # Tab ID counter
        self._next_tab_id = 0
        
        # Tab metadata: {tab_id: {"type": str, "name": str, "pinned": bool, "index": int}}
        self._tab_metadata: Dict[str, Dict] = {}
        
        # Enable tab features
        self.setMovable(True)  # Drag-and-drop to reorder
        self.setTabsClosable(True)  # Show close buttons
        self.setDocumentMode(True)  # Better visual style
        
        # Add "+" button for creating new tabs
        self._add_button = QToolButton()
        self._add_button.setText("+")
        self._add_button.setToolTip("Add new tab")
        self._add_button.clicked.connect(self._on_add_tab_clicked)
        self.setCornerWidget(self._add_button, Qt.TopRightCorner)
        
        # Connect signals
        self.tabCloseRequested.connect(self._on_tab_close_requested)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def add_tab_with_id(self, widget: QWidget, tab_type: str, tab_name: str, pinned: bool = False) -> str:
        """
        Add a tab with automatic ID assignment.
        
        Parameters:
            widget: Widget to display in tab
            tab_type: Type of tab ('vtk', 'table', 'graph')
            tab_name: Display name for tab
            pinned: Whether tab is pinned (cannot be closed)
            
        Returns:
            tab_id: Unique identifier for this tab
        """
        tab_id = f"tab_{self._next_tab_id}"
        self._next_tab_id += 1
        
        # Add tab
        index = self.addTab(widget, tab_name)
        
        # Store metadata
        self._tab_metadata[tab_id] = {
            "type": tab_type,
            "name": tab_name,
            "pinned": pinned,
            "index": index,
            "widget": widget
        }
        
        # Update close button visibility
        self._update_tab_close_button(index, pinned)
        
        # Set tooltip
        self.setTabToolTip(index, f"{tab_type.upper()}: {tab_name}" + (" (Pinned)" if pinned else ""))
        
        logger.info(f"Tab added: id={tab_id}, type={tab_type}, name={tab_name}, pinned={pinned}")
        
        return tab_id
    
    def _update_tab_close_button(self, index: int, pinned: bool) -> None:
        """Update close button visibility for a tab."""
        # Get the tab bar's close button widget
        tab_bar = self.tabBar()
        
        # PySide6 doesn't directly expose close button, but we can disable closing via event filter
        # For now, we'll handle this in _on_tab_close_requested
        pass
    
    def _on_add_tab_clicked(self) -> None:
        """Handle add tab button click."""
        dialog = TabCreationDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            tab_type = dialog.get_tab_type()
            tab_name = dialog.get_tab_name()
            
            # Generate temp ID for signal (actual widget will be created by main window)
            tab_id = f"tab_{self._next_tab_id}"
            self._next_tab_id += 1
            
            # Emit signal for main window to create appropriate widget
            self.tab_created.emit(tab_id, tab_type, tab_name)
            
            logger.info(f"Tab creation requested: type={tab_type}, name={tab_name}")
    
    def _on_tab_close_requested(self, index: int) -> None:
        """Handle tab close request."""
        tab_id = self._get_tab_id_by_index(index)
        
        if not tab_id:
            return
        
        metadata = self._tab_metadata.get(tab_id)
        if not metadata:
            return
        
        # Check if pinned
        if metadata.get("pinned", False):
            QMessageBox.warning(
                self,
                "Cannot Close Tab",
                f"Tab '{metadata['name']}' is pinned and cannot be closed.\n"
                "Unpin it first from the context menu."
            )
            return
        
        # Confirm closure for non-empty tabs
        tab_name = metadata["name"]
        reply = QMessageBox.question(
            self,
            "Close Tab",
            f"Close tab '{tab_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._close_tab(tab_id, index)
    
    def _close_tab(self, tab_id: str, index: int) -> None:
        """Close a tab and clean up."""
        # Remove tab
        self.removeTab(index)
        
        # Clean up metadata
        if tab_id in self._tab_metadata:
            del self._tab_metadata[tab_id]
        
        # Update indices for remaining tabs
        self._update_tab_indices()
        
        # Emit signal
        self.tab_closed.emit(tab_id)
        
        logger.info(f"Tab closed: id={tab_id}")
    
    def _update_tab_indices(self) -> None:
        """Update stored indices after tab removal/reorder."""
        for tab_id, metadata in self._tab_metadata.items():
            widget = metadata["widget"]
            new_index = self.indexOf(widget)
            if new_index >= 0:
                metadata["index"] = new_index
    
    def _get_tab_id_by_index(self, index: int) -> Optional[str]:
        """Get tab ID from tab index."""
        widget = self.widget(index)
        for tab_id, metadata in self._tab_metadata.items():
            if metadata["widget"] == widget:
                return tab_id
        return None
    
    def _show_context_menu(self, pos) -> None:
        """Show context menu for tab operations."""
        # Get tab at position
        tab_bar = self.tabBar()
        index = tab_bar.tabAt(pos)
        
        if index < 0:
            return
        
        tab_id = self._get_tab_id_by_index(index)
        if not tab_id:
            return
        
        metadata = self._tab_metadata.get(tab_id)
        if not metadata:
            return
        
        menu = QMenu(self)
        
        # Pin/Unpin action
        pinned = metadata.get("pinned", False)
        pin_action = QAction("Unpin Tab" if pinned else "Pin Tab", self)
        pin_action.triggered.connect(lambda: self._toggle_pin(tab_id, pinned))
        menu.addAction(pin_action)
        
        # Rename action
        rename_action = QAction("Rename Tab", self)
        rename_action.triggered.connect(lambda: self._rename_tab(tab_id))
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        # Close action
        close_action = QAction("Close Tab", self)
        close_action.setEnabled(not pinned)
        close_action.triggered.connect(lambda: self._on_tab_close_requested(index))
        menu.addAction(close_action)
        
        # Close others action
        close_others_action = QAction("Close Other Tabs", self)
        close_others_action.setEnabled(self.count() > 1)
        close_others_action.triggered.connect(lambda: self._close_other_tabs(tab_id))
        menu.addAction(close_others_action)
        
        menu.exec_(self.mapToGlobal(pos))
    
    def _toggle_pin(self, tab_id: str, currently_pinned: bool) -> None:
        """Toggle pin status of a tab."""
        metadata = self._tab_metadata.get(tab_id)
        if not metadata:
            return
        
        new_pinned = not currently_pinned
        metadata["pinned"] = new_pinned
        
        # Update tooltip
        index = metadata["index"]
        tab_name = metadata["name"]
        tab_type = metadata["type"]
        self.setTabToolTip(index, f"{tab_type.upper()}: {tab_name}" + (" (Pinned)" if new_pinned else ""))
        
        self.tab_pinned.emit(tab_id, new_pinned)
        logger.info(f"Tab {tab_id} pinned status: {new_pinned}")
    
    def _rename_tab(self, tab_id: str) -> None:
        """Rename a tab."""
        metadata = self._tab_metadata.get(tab_id)
        if not metadata:
            return
        
        current_name = metadata["name"]
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Tab",
            "Enter new tab name:",
            text=current_name
        )
        
        if ok and new_name.strip():
            new_name = new_name.strip()
            metadata["name"] = new_name
            
            # Update tab text
            index = metadata["index"]
            self.setTabText(index, new_name)
            
            # Update tooltip
            tab_type = metadata["type"]
            pinned = metadata["pinned"]
            self.setTabToolTip(index, f"{tab_type.upper()}: {new_name}" + (" (Pinned)" if pinned else ""))
            
            self.tab_renamed.emit(tab_id, new_name)
            logger.info(f"Tab {tab_id} renamed to: {new_name}")
    
    def _close_other_tabs(self, keep_tab_id: str) -> None:
        """Close all tabs except the specified one."""
        tabs_to_close = []
        
        for tab_id, metadata in self._tab_metadata.items():
            if tab_id != keep_tab_id and not metadata.get("pinned", False):
                tabs_to_close.append((tab_id, metadata["index"]))
        
        if not tabs_to_close:
            QMessageBox.information(self, "No Tabs to Close", "All other tabs are pinned.")
            return
        
        reply = QMessageBox.question(
            self,
            "Close Other Tabs",
            f"Close {len(tabs_to_close)} other tab(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Sort by index descending to avoid index shifting issues
            tabs_to_close.sort(key=lambda x: x[1], reverse=True)
            
            for tab_id, index in tabs_to_close:
                self._close_tab(tab_id, index)
    
    def get_tab_metadata(self, tab_id: str) -> Optional[Dict]:
        """Get metadata for a tab."""
        return self._tab_metadata.get(tab_id)
    
    def get_all_tabs(self) -> Dict[str, Dict]:
        """Get all tab metadata."""
        return self._tab_metadata.copy()
    
    def close_tab_by_id(self, tab_id: str) -> bool:
        """
        Close a tab by its ID.
        
        Returns:
            True if tab was closed successfully
        """
        metadata = self._tab_metadata.get(tab_id)
        if not metadata:
            return False
        
        if metadata.get("pinned", False):
            logger.warning(f"Cannot close pinned tab: {tab_id}")
            return False
        
        index = metadata["index"]
        self._close_tab(tab_id, index)
        return True
    
    def set_tab_pinned(self, tab_id: str, pinned: bool) -> bool:
        """
        Set pin status of a tab.
        
        Returns:
            True if pin status was updated
        """
        metadata = self._tab_metadata.get(tab_id)
        if not metadata:
            return False
        
        if metadata["pinned"] == pinned:
            return True  # Already in desired state
        
        self._toggle_pin(tab_id, metadata["pinned"])
        return True
