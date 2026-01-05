
import pytest
from unittest.mock import MagicMock, patch
import vtk
from services.file_loader_service import FileLoaderService
import os

@pytest.fixture
def loader():
    return FileLoaderService()

@patch("os.path.exists")
@patch("os.path.splitext")
def test_is_supported(mock_split, mock_exists, loader):
    mock_split.return_value = ("test", ".vtk")
    assert loader.is_supported("test.vtk") is True
    
    mock_split.return_value = ("test", ".xyz")
    assert loader.is_supported("test.xyz") is False

@patch("os.path.exists")
def test_load_file_not_found(mock_exists, loader):
    mock_exists.return_value = False
    with pytest.raises(FileNotFoundError):
        loader.load("nonexistent.vtk")

@patch("os.path.exists")
@patch("os.path.splitext")
def test_load_unsupported_format(mock_split, mock_exists, loader):
    mock_exists.return_value = True
    mock_split.return_value = ("data", ".xyz")
    
    with pytest.raises(ValueError, match="Unsupported format"):
        loader.load("data.xyz")

@patch("services.file_loader_service.vtk.vtkDataSetReader")
@patch("os.path.exists")
def test_load_vtk_success(mock_exists, mock_reader_cls, loader):
    mock_exists.return_value = True
    mock_reader = MagicMock()
    mock_reader_cls.return_value = mock_reader
    
    # Setup reader output
    mock_output = MagicMock()
    mock_reader.GetOutput.return_value = mock_output
    
    result_data, name = loader.load("test.vtk")
    
    # Checks
    mock_reader_cls.assert_called_once()
    mock_reader.SetFileName.assert_called_with("test.vtk")
    mock_reader.Update.assert_called_once()
    
    assert result_data == mock_output
    assert name == "test.vtk"

@patch("glob.glob")
@patch("os.path.exists")
def test_detect_time_series(mock_exists, mock_glob, loader):
    mock_exists.return_value = True
    
    # Scenario: data_01.vtk, data_02.vtk, data_03.vtk
    base_path = "path/to/data_01.vtk"
    
    # Must match glob pattern based on loader logic
    # detect_time_series logic:
    # 1. extract base (data_) and ext (.vtk)
    # 2. glob "path/to/data_*.vtk"
    mock_glob.return_value = [
        "path/to/data_01.vtk",
        "path/to/data_03.vtk", 
        "path/to/data_02.vtk",
        "path/to/other.vtk" # Should be ignored by regex
    ]
    
    series = loader.detect_time_series(base_path)
    
    assert series is not None
    assert len(series) == 3
    assert series[0].endswith("data_01.vtk")
    assert series[1].endswith("data_02.vtk")
    assert series[2].endswith("data_03.vtk")

@patch("os.path.exists")
def test_detect_time_series_single_file(mock_exists, loader):
    mock_exists.return_value = True
    # If regex doesn't match pattern like _01, returns None
    assert loader.detect_time_series("data.vtk") is None

def test_natural_sort_key(loader):
    files = ["data_1.vtk", "data_10.vtk", "data_2.vtk"]
    sorted_files = sorted(files, key=loader._natural_sort_key)
    assert sorted_files == ["data_1.vtk", "data_2.vtk", "data_10.vtk"]

@patch("services.file_loader_service.FileLoaderService.load")
def test_load_time_series(mock_load, loader):
    # Setup mocks
    mock_data1 = MagicMock()
    mock_data2 = MagicMock()
    
    # Side effect for load: return (data, name)
    mock_load.side_effect = [
        (mock_data1, "data_1.vtk"),
        (mock_data2, "data_2.vtk")
    ]
    
    files = ["data_1.vtk", "data_2.vtk"]
    
    data_list, series_name, sorted_paths = loader.load_time_series(files)
    
    assert len(data_list) == 2
    assert data_list[0] == mock_data1
    assert data_list[1] == mock_data2
    assert "data" in series_name
