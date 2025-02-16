from __future__ import absolute_import, unicode_literals
import logging
import sys
from typing import Optional

def setup_logger(name: str) -> logging.Logger:
    """Configure a logger with console output."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Console handler
        console = logging.StreamHandler(sys.stdout)
        console.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        console.setFormatter(formatter)
        logger.addHandler(console)
        
        # Prevent propagation to root logger
        logger.propagate = False
    
    return logger
