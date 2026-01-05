import logging
import pytest
from unittest.mock import MagicMock, patch
import utils.logger as logger_module
from utils.logger import setup_logger, get_logger, log_execution

@pytest.fixture(autouse=True)
def reset_logger():
    # Setup
    original_logger = logger_module._logger
    logger_module._logger = None
    yield
    # Teardown
    logger_module._logger = original_logger

@patch("logging.handlers.RotatingFileHandler")
@patch("utils.logger.Path")
def test_setup_logger(mock_path, mock_handler):
    # Mocking Path to prevent file creation
    mock_dir = MagicMock()
    mock_path.return_value.parent.parent.parent.parent.__truediv__.return_value = mock_dir
    
    logger = setup_logger("DEBUG")
    
    assert logger.name == "scientific_analysis_agent"
    assert logger.level == logging.DEBUG
    # Check if directory creation was called
    mock_dir.mkdir.assert_called_with(exist_ok=True)
    # Check if handler was added
    mock_handler.assert_called()

def test_get_logger():
    # Ensure setup is called
    adapter = get_logger("TestComponent")
    assert isinstance(adapter, logging.LoggerAdapter)
    assert adapter.extra["name_short"] == "TestComponent"

def test_log_execution_decorator():
    # Mock get_logger to verify calls
    with patch("utils.logger.get_logger") as mock_get_logger:
        mock_adapter = MagicMock()
        mock_get_logger.return_value = mock_adapter
        
        @log_execution(level="INFO", start_msg="Start", end_msg="End")
        def dummy_func(x):
            return x * 2
            
        result = dummy_func(5)
        
        assert result == 10
        # Check calls
        mock_adapter.info.assert_any_call("Start")
        # The end message contains execution time, so we check using string containment
        mock_adapter.info.asset_called()
        calls = [args[0] for args, _ in mock_adapter.info.call_args_list]
        assert "Start" in calls
        assert any("End" in c for c in calls)

def test_log_execution_exception():
    with patch("utils.logger.get_logger") as mock_get_logger:
        mock_adapter = MagicMock()
        mock_get_logger.return_value = mock_adapter
        
        @log_execution
        def failing_func():
            raise ValueError("Test Error")
            
        with pytest.raises(ValueError):
            failing_func()
            
        # Should verify logger.error was called
        mock_adapter.error.assert_called()
