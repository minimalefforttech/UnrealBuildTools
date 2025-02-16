#!/usr/bin/env python
"""CLI tool for packaging Forum Asset Bundle (FAB) plugins."""

import argparse
import json
import logging
import shutil
import sys
import tempfile
import traceback
from pathlib import Path
from typing import List, Optional
from contextlib import contextmanager

from unreal_build_tools.core.structs import PluginInfo, CompilerConfig
from unreal_build_tools.core.filesystem import find_uplugin, temporary_directory
from unreal_build_tools.core.platform_utils import get_engine_path, get_platform
from unreal_build_tools.impl.validators.fab_plugin_uplugin_validator import FabPluginUpluginValidator
from unreal_build_tools.impl.validators.fab_plugin_path_validator import FabPluginPathValidator
from unreal_build_tools.impl.validators.fab_plugin_copyright_validator import FabPluginCopyrightValidator
from unreal_build_tools.impl.validators.fab_plugin_executables_validator import FabPluginNoExecutablesValidator
from unreal_build_tools.impl.plugin_compiler import PluginCompiler
from unreal_build_tools.core.exceptions import ValidationError, BuildError, ConfigurationError
from unreal_build_tools.packaging import package_version_for_fab
from unreal_build_tools.staging import stage_plugin_files

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

DEFAULT_VERSIONS = ["4.27", "5.0", "5.1", "5.2", "5.3", "5.4", "5.5"]

# TODO: Move these functions to a module

def validate_plugin(plugin_info: PluginInfo, engine_path: Optional[Path] = None) -> bool:
    """Run all plugin validations."""
    validators = [
        FabPluginUpluginValidator(plugin_info),
        FabPluginPathValidator(plugin_info),
        FabPluginCopyrightValidator(plugin_info),
        FabPluginNoExecutablesValidator(plugin_info)
    ]
    
    success = True
    for validator in validators:
        result = validator.validate()
        if not result.success:
            success = False
            logger.error(f"\n{result.name} failed:")
            for error in result.errors:
                logger.error(f"  ✗ {error}")
            for warning in result.warnings:
                logger.warning(f"  ! {warning}")
        else:
            logger.info(f"✓ {result.name} passed")
    
    # Validate compilation if engine path provided
    if engine_path and success:
        logger.info("\nValidating compilation...")
        success = validate_compilation(plugin_info, engine_path)
    
    return success

def validate_compilation(plugin_info: PluginInfo, engine_path: Path) -> None:
    """Validate plugin compilation against latest supported version.
    
    Raises:
        BuildError: If compilation fails
        ConfigurationError: If engine path is invalid
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Copy plugin to temp directory
        temp_plugin_dir = temp_dir_path / plugin_info.source_dir.name
        shutil.copytree(plugin_info.source_dir, temp_plugin_dir)
        
        # Update .uplugin for latest version
        latest_version = max(DEFAULT_VERSIONS)
        temp_uplugin = temp_plugin_dir / plugin_info.uplugin_file.name
        with temp_uplugin.open('r') as f:
            uplugin_data = json.load(f)
        
        uplugin_data['EngineVersion'] = f"{latest_version}.0"
        with temp_uplugin.open('w') as f:
            json.dump(uplugin_data, f, indent=2)
        
        # Try compilation
        config = CompilerConfig(
            platform=get_platform(),
            source=temp_uplugin,
            output_dir=temp_dir_path / "build",
            engine_path=engine_path
        )
        compiler = PluginCompiler(config)
        
        if not compiler.run():
            raise BuildError(f"Compilation failed for UE {latest_version}")
            
        logger.info(f"✓ Compilation validation passed (UE {latest_version})")


def main():
    parser = argparse.ArgumentParser(description="Package Unreal Engine plugin for FAB distribution")
    parser.add_argument("-p", "--plugin", help="Path to .uplugin file or containing directory")
    parser.add_argument("-o", "--output", help="Output directory for packages")
    parser.add_argument("-v", "--versions", nargs="+", default=DEFAULT_VERSIONS,
                       help="UE versions to package for")
    parser.add_argument("-e", "--engine", help="Engine version for validation, defaults to highest version packaged")
    parser.add_argument("--skip-validation", action="store_true",
                       help="Skip validation checks")
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    args = parser.parse_args()
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(tempfile.mkdtemp())
    versions = args.versions or DEFAULT_VERSIONS
    try:
        # Find plugin and setup
        plugin_path = find_uplugin(args.plugin)
        initial_plugin_info = PluginInfo(
            uplugin_file=plugin_path,
            source_dir=plugin_path.parent,
            versions=versions
        )
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Stage plugin files first
        with temporary_directory() as staging_dir:
            logger.info("\nStaging plugin files...")
            staged_plugin_dir = stage_plugin_files(initial_plugin_info, staging_dir, args.verbose)
            
            # Create new plugin info from staged files
            staged_plugin_info = PluginInfo(
                uplugin_file=next(staged_plugin_dir.glob("*.uplugin")),
                source_dir=staged_plugin_dir,
                versions=versions
            )
            
            # Rest of processing uses staged_plugin_info
            if not args.skip_validation:
                logger.info("\nValidating plugin...")
                engine_path = get_engine_path(args.engine or versions[-1])
                try:
                    validate_plugin(staged_plugin_info, engine_path)
                except (ValidationError, BuildError) as e:
                    logger.error(f"Validation failed: {e}")
                    sys.exit(1)
            
            for version in versions:
                logger.info(f"\nPackaging for UE {version}...")
                try:
                    package_version_for_fab(staged_plugin_info.source_dir, version, output_dir)
                except (ConfigurationError, RuntimeError) as e:
                    logger.error(f"Packaging failed: {e}")
                    sys.exit(1)
                    
        logger.info(f"\nPackaging complete! Files are in: {output_dir}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
