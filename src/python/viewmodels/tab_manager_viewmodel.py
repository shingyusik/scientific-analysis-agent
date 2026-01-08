from PySide6.QtCore import QObject, Signal
from typing import Optional, Dict, Any, List
from utils.logger import get_logger
from utils.tool_registry import expose_tool
from utils.app_context import get_pipeline_viewmodel

logger = get_logger("TabManagerVM")


class TabManagerViewModel(QObject):
    """ViewModel for managing UI tabs independently of the pipeline."""
    
    # Signals for UI control
    tab_creation_requested = Signal(str, str, str)  # tab_type, tab_name, extra_data (json)
    tab_close_requested = Signal(str)  # tab_id
    tab_pin_requested = Signal(str, bool)  # tab_id, pinned
    
    # Specific view requests (routed to tab_creation_requested internally or handled by main window convenience)
    vtk_view_requested = Signal(str)  # tab_name
    table_view_requested = Signal(str, str, str)  # item_id, tab_name, array_type
    graph_view_requested = Signal(str, str, str, str, str, str)  # graph_type, item_id, y_array, x_array, tab_name, array_type
    
    def __init__(self):
        super().__init__()
        self._tab_registry: Dict[str, Dict[str, Any]] = {}  # {tab_id: {name, type, pinned}}

    # ==================== Tab Management Tools ====================
    
    @expose_tool(
        name="create_vtk_view",
        description=(
            "Creates a new VTK 3D render view tab showing all visible pipeline objects.\n"
            "Use this when the user asks for a 'render view', '3D view', 'VTK view', or similar.\n"
            "Parameters:\n"
            "- tab_name: (Optional) Custom name for the tab. Default: 'Render View'.\n"
            "Returns:\n"
            "- Success message."
        )
    )
    def create_vtk_view(self, tab_name: Optional[str] = None) -> str:
        """Request creation of a VTK render view tab."""
        if not tab_name:
            tab_name = "Render View"
        
        self.vtk_view_requested.emit(tab_name)
        logger.info(f"VTK view requested: name={tab_name}")
        return f"VTK render view '{tab_name}' creation requested"
    
    @expose_tool(
        name="create_table_view",
        description=(
            "Creates a new table view tab showing ALL data arrays from a pipeline item.\n"
            "The table will display all available point or cell data in columns.\n"
            "Parameters:\n"
            "- item_id: Pipeline item ID (optional, uses selected item if not provided).\n"
            "- tab_name: (Optional) Custom name for the tab.\n"
            "- array_type: 'POINT' or 'CELL' (default 'POINT').\n"
            "Returns:\n"
            "- Success message or error."
        )
    )
    def create_table_view(self, item_id: Optional[str] = None,
                          tab_name: Optional[str] = None, array_type: str = "POINT") -> str:
        """Request creation of a table view tab."""
        pipeline_vm = get_pipeline_viewmodel()
        
        # Use selected item if not provided
        if not item_id:
            if pipeline_vm and pipeline_vm.selected_item:
                item_id = pipeline_vm.selected_item.id
            else:
                return "Error: No item_id provided and no item is currently selected"
        
        if pipeline_vm:
            item = pipeline_vm.items.get(item_id)
            if not item:
                return f"Error: Pipeline item '{item_id}' not found"
            
            if not tab_name:
                tab_name = f"Table - {item.name}"
        else:
             if not tab_name:
                tab_name = f"Table - {item_id}"
        
        self.table_view_requested.emit(item_id, tab_name, array_type)
        logger.info(f"Table view requested: item={item_id}")
        return f"Table view '{tab_name}' creation requested"
        
    @expose_tool(
        name="create_graph_view",
        description=(
            "Creates a new graph view tab visualizing data from a pipeline item.\n"
            "Parameters:\n"
            "- graph_type: 'line', 'scatter', 'histogram', or 'bar'.\n"
            "- item_id: (Optional) Pipeline item ID. Uses selected item if not provided.\n"
            "- y_array: (Optional) Name of Y-axis data array. Uses first available if not provided.\n"
            "- x_array: (Optional) X-axis array or '__Index__' (default).\n"
            "- tab_name: (Optional) Custom name for the tab.\n"
            "- array_type: 'POINT' or 'CELL' (default 'POINT').\n"
            "Returns:\n"
            "- Success message or error."
        )
    )
    def create_graph_view(self, graph_type: str = "line", item_id: Optional[str] = None, 
                          y_array: Optional[str] = None, x_array: Optional[str] = None, 
                          tab_name: Optional[str] = None, array_type: str = "POINT") -> str:
        """Request creation of a graph view tab."""
        pipeline_vm = get_pipeline_viewmodel()
        
        # Use selected item if not provided
        if not item_id:
            if pipeline_vm and pipeline_vm.selected_item:
                item_id = pipeline_vm.selected_item.id
            else:
                return "Error: No item_id provided and no item is currently selected"
        
        if pipeline_vm:
            item = pipeline_vm.items.get(item_id)
            if not item:
                return f"Error: Pipeline item '{item_id}' not found"
            
            # Auto-select first available array if y_array not provided
            if not y_array:
                data_arrays = item.get_data_arrays()
                if data_arrays:
                    y_array = data_arrays[0][0]  # First array name
                else:
                    y_array = "Index"  # Fallback
        
        valid_types = ["line", "scatter", "histogram", "bar"]
        if graph_type not in valid_types:
            return f"Error: Invalid graph type '{graph_type}'. Must be one of: {', '.join(valid_types)}"
        
        if not x_array:
            x_array = "__Index__"
        if not tab_name:
            tab_name = f"Graph - {y_array}"
        
        self.graph_view_requested.emit(graph_type, item_id, y_array, x_array, tab_name, array_type)
        logger.info(f"Graph view requested: type={graph_type}, item={item_id}, y={y_array}")
        return f"{graph_type.capitalize()} graph '{tab_name}' creation requested"
    
    @expose_tool(
        name="close_tab",
        description=(
            "Closes a specific tab by its ID.\n"
            "Parameters:\n"
            "- tab_id: ID of the tab to close.\n"
            "Returns:\n"
            "- Success or error message. Pinned tabs cannot be closed."
        )
    )
    def close_tab(self, tab_id: str) -> str:
        """Request tab closure."""
        self.tab_close_requested.emit(tab_id)
        logger.info(f"Tab close requested: {tab_id}")
        return f"Tab '{tab_id}' close requested"
    
    @expose_tool(
        name="pin_tab",
        description=(
            "Pins or unpins a tab to prevent accidental closure.\n"
            "Parameters:\n"
            "- tab_id: ID of the tab.\n"
            "- pinned: True to pin, False to unpin (default True).\n"
            "Returns:\n"
            "- Success or error message."
        )
    )
    def pin_tab(self, tab_id: str, pinned: bool = True) -> str:
        """Request tab pin/unpin."""
        self.tab_pin_requested.emit(tab_id, pinned)
        action = "pin" if pinned else "unpin"
        logger.info(f"Tab {action} requested: {tab_id}")
        return f"Tab '{tab_id}' {action} requested"
    
    def register_tab(self, tab_id: str, name: str, tab_type: str, pinned: bool = False) -> None:
        """Register a tab in the internal registry (called by MainWindow)."""
        self._tab_registry[tab_id] = {
            'name': name,
            'type': tab_type,
            'pinned': pinned
        }
    
    def unregister_tab(self, tab_id: str) -> None:
        """Unregister a tab from the registry (called by MainWindow)."""
        if tab_id in self._tab_registry:
            del self._tab_registry[tab_id]
    
    def update_tab_pin_status(self, tab_id: str, pinned: bool) -> None:
        """Update tab pin status in registry."""
        if tab_id in self._tab_registry:
            self._tab_registry[tab_id]['pinned'] = pinned
    
    def update_tab_name(self, tab_id: str, new_name: str) -> None:
        """Update tab name in registry."""
        if tab_id in self._tab_registry:
            self._tab_registry[tab_id]['name'] = new_name
    
    @expose_tool(
        name="list_tabs",
        description=(
            "Lists all currently open tabs with their IDs, types, and names.\n"
            "Returns:\n"
            "- A formatted string listing all tabs."
        )
    )
    def list_tabs(self) -> str:
        """List all open tabs."""
        if not self._tab_registry:
            return "No tabs are currently open"
        
        lines = ["Current open tabs:"]
        for tab_id, info in self._tab_registry.items():
            name = info['name']
            tab_type = info['type'].upper()
            pinned = " (Pinned)" if info.get('pinned', False) else ""
            lines.append(f"  - {tab_id}: {name} [{tab_type}]{pinned}")
        
        return "\n".join(lines)
