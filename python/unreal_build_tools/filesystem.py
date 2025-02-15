"""File system utilities for Unreal Build Tools.

This module provides utilities for finding and managing plugin files
and build directories related to Unreal Engine plugins.
"""
from contextlib import contextmanager
from typing import Union, Iterator
import tempfile
import shutil
import sys
from pathlib import Path
from unreal_build_tools.logging import setup_logger

logger = setup_logger(__name__)

def find_uplugin(path: Union[str, None, Path] = None) -> Path:
    """Find and validate plugin path.
    
    Args:
        path (Union[str, None, Path], optional): Path to .uplugin file or directory.
            If None or directory, searches for .uplugin files in that directory.
            Defaults to current working directory.
    
    Returns:
        Path: Resolved absolute path to the plugin file
        
    Raises:
        RuntimeError: If plugin file is not found or multiple plugins exist
    """
    if path is None:
        path = Path.cwd()
    plugin_path = Path(path)
    if plugin_path.is_file():
        if plugin_path.suffix != ".uplugin":
            logger.error(f"Invalid file type: {plugin_path}")
            raise RuntimeError(f"Invalid file type: {plugin_path}")
        logger.debug(f"Using specified plugin file: {plugin_path}")
        return plugin_path.resolve()
    elif plugin_path.is_dir():
        directory = plugin_path
        logger.debug(f"Searching for plugins in directory: {directory}")
    else:
        logger.error(f"Invalid path: {plugin_path}")
        raise RuntimeError(f"Invalid path: {plugin_path}")

    plugins = list(directory.glob("*.uplugin"))
    if not plugins:
        logger.error("No .uplugin file found in current directory")
        raise RuntimeError("No .uplugin file found in current directory")
    if len(plugins) > 1:
        logger.error("Multiple .uplugin files found. Please specify one.")
        raise RuntimeError("Multiple .uplugin files found. Please specify one.")
    
    plugin_path = plugins[0]
    logger.info(f"Found plugin file: {plugin_path}")
    return plugin_path.resolve()


@contextmanager
def temporary_directory() -> Iterator[Path]:
    """Create and manage a temporary directory that auto-cleans.
    
    Yields:
        Path: Path to temporary directory
        
    Note:
        Directory and contents are automatically removed when exiting context
    """
    temp_dir = tempfile.mkdtemp(prefix='ubt_')
    try:
        yield Path(temp_dir)
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup temporary directory {temp_dir}: {e}", 
                  file=sys.stderr)
