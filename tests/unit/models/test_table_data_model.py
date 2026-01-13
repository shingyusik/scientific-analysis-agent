import pytest
from unittest.mock import MagicMock
import numpy as np
from models.table_data_model import TableDataModel


@pytest.fixture
def table_model(qapp):
    return TableDataModel()


def test_initial_state(table_model):
    """Test initial empty state."""
    assert table_model.rowCount() == 0
    assert table_model.columnCount() == 0
    assert table_model.get_data_array() is None
    assert table_model.get_headers() == []


def test_set_data(table_model):
    """Test setting data and headers."""
    data = np.array([
        [0, 10.5, 1, 0, 0],
        [1, 20.3, 0, 1, 0],
        [2, 30.1, 0, 0, 1]
    ])
    headers = ["Index", "Scalar", "Vec_X", "Vec_Y", "Vec_Z"]
    
    table_model.set_data(data, headers)
    
    assert table_model.rowCount() == 3
    assert table_model.columnCount() == 5
    assert table_model.get_headers() == headers
    assert np.array_equal(table_model.get_data_array(), data)


def test_data_display_role(table_model):
    """Test data retrieval with DisplayRole."""
    from PySide6.QtCore import Qt, QModelIndex
    
    data = np.array([[0, 10.123456789, 1.0]])
    headers = ["Index", "Value", "Flag"]
    table_model.set_data(data, headers)
    
    # Test integer display
    index = table_model.index(0, 0)
    assert table_model.data(index, Qt.DisplayRole) == "0"
    
    # Test float display (scientific notation)
    index = table_model.index(0, 1)
    display_value = table_model.data(index, Qt.DisplayRole)
    assert "10.1235" in display_value  # Should be formatted with .6g


def test_data_alignment_role(table_model):
    """Test text alignment for numbers vs text."""
    from PySide6.QtCore import Qt
    
    data = np.array([[42, 3.14]])
    headers = ["Int", "Float"]
    table_model.set_data(data, headers)
    
    # Numbers should be right-aligned
    index = table_model.index(0, 0)
    alignment = table_model.data(index, Qt.TextAlignmentRole)
    assert alignment == (Qt.AlignRight | Qt.AlignVCenter)


def test_header_data(table_model):
    """Test header data retrieval."""
    from PySide6.QtCore import Qt
    
    headers = ["Col1", "Col2", "Col3"]
    data = np.array([[1, 2, 3]])
    table_model.set_data(data, headers)
    
    # Horizontal headers
    assert table_model.headerData(0, Qt.Horizontal, Qt.DisplayRole) == "Col1"
    assert table_model.headerData(1, Qt.Horizontal, Qt.DisplayRole) == "Col2"
    
    # Vertical headers (row numbers)
    assert table_model.headerData(0, Qt.Vertical, Qt.DisplayRole) == "0"


def test_sort_ascending(table_model):
    """Test sorting in ascending order."""
    from PySide6.QtCore import Qt
    
    data = np.array([
        [2, 30.0],
        [0, 10.0],
        [1, 20.0]
    ])
    headers = ["Index", "Value"]
    table_model.set_data(data, headers)
    
    # Sort by Value column (ascending)
    table_model.sort(1, Qt.AscendingOrder)
    
    sorted_data = table_model.get_data_array()
    assert sorted_data[0, 1] == 10.0
    assert sorted_data[1, 1] == 20.0
    assert sorted_data[2, 1] == 30.0


def test_sort_descending(table_model):
    """Test sorting in descending order."""
    from PySide6.QtCore import Qt
    
    data = np.array([
        [0, 10.0],
        [1, 20.0],
        [2, 30.0]
    ])
    headers = ["Index", "Value"]
    table_model.set_data(data, headers)
    
    # Sort by Value column (descending)
    table_model.sort(1, Qt.DescendingOrder)
    
    sorted_data = table_model.get_data_array()
    assert sorted_data[0, 1] == 30.0
    assert sorted_data[1, 1] == 20.0
    assert sorted_data[2, 1] == 10.0


def test_clear(table_model):
    """Test clearing data."""
    data = np.array([[1, 2, 3]])
    headers = ["A", "B", "C"]
    table_model.set_data(data, headers)
    
    table_model.clear()
    
    assert table_model.rowCount() == 0
    assert table_model.columnCount() == 0
    assert table_model.get_data_array() is None
    assert table_model.get_headers() == []


def test_invalid_index(table_model):
    """Test data retrieval with invalid index."""
    from PySide6.QtCore import Qt
    
    data = np.array([[1, 2]])
    headers = ["A", "B"]
    table_model.set_data(data, headers)
    
    # Out of bounds index
    index = table_model.index(10, 10)
    assert table_model.data(index, Qt.DisplayRole) is None
