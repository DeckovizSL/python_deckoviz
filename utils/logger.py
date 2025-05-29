"""
Logger setup for Deckoviz.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logger(name, logfile=None, level=logging.INFO):
    """
    Set up a logger with the specified name and configuration.
    
    Args:
        name: Logger name
        logfile: Optional log file name
        level: Logging level (default: INFO)
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if logfile specified
    if logfile:
        # Create logs directory if it doesn't exist
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Create file handler
        file_handler = logging.FileHandler(os.path.join("logs", logfile))
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
