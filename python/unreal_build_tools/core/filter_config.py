"""Module for parsing Unreal Engine's FilterPlugin.ini configuration files.

This module provides functionality to parse FilterPlugin.ini files, which are used
to specify which files should be included when packaging an Unreal Engine plugin.
It handles the specific syntax of these files, including the ... wildcard for
recursive directory inclusion and pattern matching.
"""

from pathlib import Path
from typing import List
import configparser
import fnmatch
import shutil
import logging

logger = logging.getLogger(__name__)

def parse_filter_config(plugin_root: Path) -> List[str]:
    """Parse FilterPlugin.ini to get files to include.
    
    Args:
        plugin_root (Path): Plugin root directory
        
    Returns:
        List[str]: List of file/directory patterns to include
        
    Raises:
        RuntimeError: If FilterPlugin.ini is missing or invalid
    """
    filter_path = plugin_root / "Config" / "FilterPlugin.ini"
    if not filter_path.exists():
        raise RuntimeError(
            "FilterPlugin.ini not found in Config directory.\n"
            "This file is required to specify which files should be packaged."
        )
    
    config = configparser.ConfigParser(allow_no_value=True)
    try:
        with filter_path.open(encoding='utf-8') as f:
            config.read_file(f)
    except Exception as e:
        raise RuntimeError(f"Failed to parse FilterPlugin.ini: {e}")
    
    if not config.has_section('FilterPlugin'):
        raise RuntimeError("FilterPlugin.ini must have a [FilterPlugin] section")
    
    # Get all non-empty, non-comment lines
    patterns = []
    for key in config['FilterPlugin']:
        # In FilterPlugin.ini, the patterns are actually the keys
        pattern = key.strip()
        # Normalize pattern separators and remove leading slash
        pattern = pattern.replace('\\', '/')
        if pattern and not pattern.startswith(';'):
            patterns.append(pattern.replace("...", "**/*.*"))
    
    return patterns
