"""Utilities for getting or inferring required inputs from the user.
This module provides interactive utilities for selecting Unreal Engine versions
and finding Unreal plugin files, with input validation and error handling.
The utilities handle cases where inputs are not provided by searching common
locations and providing interactive prompts where needed. All functions include
validation to ensure valid inputs are returned or appropriate errors are raised.
"""
from unreal_build_tools import platform_utils
from unreal_build_tools.logging import setup_logger

from typing import List, Optional
from pathlib import Path

logger = setup_logger(__name__)

def select_ue_version(versions: Optional[List[str]], base_path: Optional[Path]=None) -> str:
    """Interactive UE version selection.
    
    Args:
        versions (List[str]): List of available UE versions
        base_path (Optional[Path], optional): Base Epic Games installation path.
            Defaults to None, which will use the default base path.
    
    Returns:
        str: Selected UE version
        
    Raises:
        RuntimeError: If no UE installations are found
    """
    versions = versions or platform_utils.get_ue_versions(base_path)
    if not versions:
        logger.error("No UE installations found!")
        raise RuntimeError("No UE installations found!")

    logger.info("Available UE versions:")
    for idx, version in enumerate(versions, 1):
        logger.info(f"{idx}. {version}")

    while True:
        try:
            choice = int(input(f"Select UE version (1-{len(versions)}): "))
            if 1 <= choice <= len(versions):
                selected = versions[choice - 1]
                logger.debug(f"Selected UE version: {selected}")
                return selected
        except ValueError:
            pass
        logger.warning(f"Invalid selection. Please enter a number between 1 and {len(versions)}")


def find_uplugin(path: Optional[str] = None) -> Path:
    """Find and validate plugin path.
    
    Args:
        path (Optional[str], optional): Path to .uplugin file. Defaults to None.
            If None, searches current directory for .uplugin files.
    
    Returns:
        Path: Resolved absolute path to the plugin file
        
    Raises:
        RuntimeError: If plugin file is not found or multiple plugins exist
    """
    if path:
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
    else:
        directory = Path.cwd()
        logger.debug("Searching for plugins in current directory")

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
