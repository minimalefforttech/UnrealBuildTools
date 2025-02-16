"""Module for staging Unreal Engine plugin files for packaging.

This module handles copying and filtering plugin files according to 
FilterPlugin.ini configuration for preparation before packaging.
"""

from pathlib import Path
import shutil
import logging

from .core.structs import PluginInfo
from .core.filter_config import parse_filter_config

logger = logging.getLogger(__name__)

def resolve_glob_pattern(base_dir: Path, pattern: str) -> set[Path]:
    """Resolve a glob pattern against a base directory."""
    if pattern.startswith('/'):
        pattern = pattern[1:]
    pattern = pattern.replace('\\', '/')
    
    matched = set()
    for path in base_dir.glob(pattern):
        if path.is_file():
            # resolve() will return the actual case-sensitive path from the filesystem
            matched.add(path.resolve())
    
    return matched

def stage_plugin_files(plugin_info: PluginInfo, staging_dir: Path, verbose: bool = False) -> Path:
    """Copy filtered plugin files to staging directory."""
    include_patterns = parse_filter_config(plugin_info.source_dir)
    target_dir = staging_dir / plugin_info.source_dir.name
    
    if verbose:
        logger.info("Include patterns:")
        for pattern in include_patterns:
            logger.info(f"  {pattern}")
    
    target_dir.mkdir(parents=True)
    shutil.copy2(plugin_info.uplugin_file, target_dir / plugin_info.uplugin_file.name)
    
    included_files = set()
    for pattern in include_patterns:
        included_files.update(resolve_glob_pattern(plugin_info.source_dir, pattern))
    
    for path in included_files:
        src_path = plugin_info.source_dir / path.relative_to(plugin_info.source_dir)
        dst_path = target_dir / path.relative_to(plugin_info.source_dir)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_path, dst_path)
        if verbose:
            logger.info(f"Copied: {path.relative_to(plugin_info.source_dir)}")
    
    return target_dir
