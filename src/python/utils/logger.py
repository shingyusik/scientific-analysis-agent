import logging

from datetime import datetime
from pathlib import Path
from typing import Optional



_logger: Optional[logging.Logger] = None
_log_level: int = logging.INFO


def setup_logger(level: str = "INFO") -> logging.Logger:
    global _logger, _log_level

    _log_level = getattr(logging, level.upper(), logging.INFO)

    if _logger is not None:
        _logger.setLevel(_log_level)
        for handler in _logger.handlers:
            handler.setLevel(_log_level)
        return _logger

    _logger = logging.getLogger("scientific_analysis_agent")
    _logger.setLevel(_log_level)
    _logger.propagate = False

    if _logger.handlers:
        _logger.handlers.clear()



    from logging.handlers import RotatingFileHandler

    log_dir = Path(__file__).parent.parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "sa_agent.log"

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setLevel(_log_level)
    file_format = "[%(asctime)s] %(levelname)-8s | %(name_short)-16s | %(message)s"
    file_handler.setFormatter(logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S"))
    _logger.addHandler(file_handler)

    return _logger


def get_logger(name: str) -> logging.LoggerAdapter:
    global _logger

    if _logger is None:
        setup_logger()

    return logging.LoggerAdapter(_logger, {"name_short": name})


import functools
import time
from typing import Callable, Any, Union

def log_execution(
    func: Optional[Callable] = None, 
    *, 
    level: str = "DEBUG",
    start_msg: Optional[str] = None,
    end_msg: Optional[str] = None
) -> Any:
    """
    Decorator to log the start and end of a function execution.
    Can be used as:
    @log_execution
    @log_execution(level="INFO")
    @log_execution(start_msg="Loading data...", end_msg="Data loaded")
    """
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            # Resolve logger for the function's module
            logger = get_logger(f.__module__)
            
            # Get the logging method (debug, info, etc.)
            log_method = getattr(logger, level.lower(), logger.debug)
            
            func_name = f.__qualname__
            
            # Use custom start message or default
            msg_start = start_msg if start_msg is not None else f"Starting {func_name}..."
            log_method(msg_start)
            
            start_time = time.time()
            
            try:
                result = f(*args, **kwargs)
                elapsed = time.time() - start_time
                
                # Use custom end message or default
                if end_msg is not None:
                    msg_end = f"{end_msg} (took {elapsed:.4f}s)"
                else:
                    msg_end = f"Finished {func_name} (took {elapsed:.4f}s)"
                
                log_method(msg_end)
                return result
            except Exception as e:
                logger.error(f"Error in {func_name}: {e}")
                raise
        return wrapper

    if func is None:
        return decorator
    return decorator(func)


