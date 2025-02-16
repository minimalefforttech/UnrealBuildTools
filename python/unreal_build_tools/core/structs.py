from __future__ import absolute_import, unicode_literals
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
from .constants import Platform

@dataclass
class PluginConfig:
    """Configuration for an Unreal plugin."""
    name: str
    version: str
    supported_target_platforms: List[str]
    dependencies: Optional[List[str]] = None
    extra_settings: Optional[Dict[str, str]] = None

@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    message: str
    artifacts: List[str]
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None

@dataclass
class ValidationResult:
    """Results from a validation operation."""
    name: str
    success: bool
    errors: List[str]
    warnings: List[str]

@dataclass
class CompilerConfig:
    """Configuration settings for the Unreal Engine compiler implementation."""
    platform: Platform  # Target build platform (WIN64, LINUX, MAC)
    engine_path: Path  # Path to Unreal Engine installation
    source: Path  # Path to source (.uplugin file)
    output_dir: Path  # Output directory for compiled plugin
    extra_arguments: Optional[Dict[str, Any]] = None  # Additional compiler arguments

@dataclass
class PluginInfo:
    """Information about the plugin to be validated."""
    source_dir: Path  # Root directory of the plugin
    uplugin_file: Path  # Path to the .uplugin file
    versions: List[str]  # List of UE versions to validate against
    plugin_data: Optional[Dict[str, Any]] = None  # Loaded .uplugin data
