#!/usr/bin/env python
"""Unreal Engine Plugin Packager for Forum Asset Bundle (FAB) Distribution.

This script creates version-specific packages of an Unreal Engine plugin suitable
for distribution through the Epic Games Marketplace or direct FAB uploads.

It is a single monolithic script to simplify integrations.

Key Features:
- Creates separate zip packages for multiple UE versions
- Modifies the .uplugin file for each version while keeping source identical
- Uses FilterPlugin.ini to determine which files to include
- Handles cross-platform path issues
- Supports both Python 2 and 3

FAB Requirements:
Each UE version requires a unique plugin package with a matching EngineVersion
in the .uplugin file, even if the underlying source code is identical.
This script automates the process of creating these version-specific packages
by copying the plugin files and modifying only the EngineVersion field in
each package's .uplugin file.

Usage:
    package_plugin.py [-p PLUGIN] [-o OUTPUT] [-v VERSION [VERSION ...]]

Examples:
    # Package for all default versions
    package_plugin.py

    # Package for specific versions
    package_plugin.py -v 4.27.0 5.0.0 5.1.0

    # Package specific plugin
    package_plugin.py -p path/to/plugin.uplugin

    # Specify output directory
    package_plugin.py -o path/to/output
"""

from __future__ import print_function
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
import tempfile
from contextlib import contextmanager
from typing import List, Optional, Iterator, Tuple  # noqa: F401 (Python 2 compatibility)
import fnmatch
import configparser
import traceback
import re
import subprocess

# Plugin packaging versions
DEFAULT_VERSIONS = [
    "4.27",
    "5.0",
    "5.1",
    "5.2",
    "5.3",
    "5.4",
    "5.5"
]

# File type definitions
SOURCE_FILE_EXTENSIONS = ['.h', '.hh', '.cpp', '.cc', '.cs', '.py']
EXECUTABLE_PATTERNS = ['*.sh', '*.cmd', '*.bat', '*.exe']

# Validation settings
MAX_PATH_LENGTH = 170
COPYRIGHT_PREFIX = '// Copyright'
THIRD_PARTY_MARKER = 'ThirdParty'

# FabURL validation
FAB_URL_PATTERN = r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}'

COMMENT_PREFIXES = ['//', '/*', '"""', "'''", '#']

def strip_comment_markers(line: str) -> str:
    """Strip common comment markers and whitespace from a line.
    
    Args:
        line (str): Line to process
        
    Returns:
        str: Line with comment markers and whitespace removed
    """
    line = line.strip()
    for prefix in COMMENT_PREFIXES:
        if line.startswith(prefix):
            line = line[len(prefix):].strip()
    return line

def find_plugin(path: Optional[str] = None) -> Path:
    """Find and validate plugin path.
    
    Args:
        path (Optional[str]): Path to .uplugin file or directory containing one
    
    Returns:
        Path: Path to the plugin file
        
    Raises:
        RuntimeError: If plugin file not found or multiple plugins found
    """
    if path:
        search_path = Path(path)
        if search_path.is_file() and search_path.suffix == '.uplugin':
            return search_path.resolve()
        if search_path.is_dir():
            plugins = list(search_path.glob("*.uplugin"))
        else:
            raise RuntimeError(f"Invalid path: {path}")
    else:
        plugins = list(Path.cwd().glob("*.uplugin"))
    
    if not plugins:
        raise RuntimeError("No .uplugin file found")
    if len(plugins) > 1:
        raise RuntimeError("Multiple .uplugin files found. Please specify one.")
    
    return plugins[0].resolve()

@contextmanager
def temporary_directory() -> Iterator[Path]:
    """Create and manage a temporary directory that auto-cleans.
    
    Yields:
        Path: Path to temporary directory
        
    Note:
        Directory and contents are automatically removed when exiting context
    """
    temp_dir = tempfile.mkdtemp(prefix='plugin_package_')
    try:
        yield Path(temp_dir)
    finally:
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Failed to cleanup temporary directory {temp_dir}: {e}", 
                  file=sys.stderr)

def setup_package_dir(plugin_path: Path, output_base: Optional[str] = None) -> Path:
    """Setup package output directory.
    
    Args:
        plugin_path (Path): Path to .uplugin file
        output_base (Optional[str]): Base output directory
        
    Returns:
        Path: Package output directory
    """
    if output_base:
        package_dir = Path(output_base)
    else:
        package_dir = plugin_path.parent / ".Package"
    
    package_dir.mkdir(parents=True, exist_ok=True)
    return package_dir

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
        if pattern.startswith('/'):
            pattern = pattern[1:]
        if pattern and not pattern.startswith(';'):
            patterns.append(pattern)
    
    return patterns

def should_include_path(path: str, patterns: List[str]) -> bool:
    """Check if a path matches any of the filter patterns.
    
    Args:
        path (str): Path to check (relative to plugin root)
        patterns (List[str]): List of patterns to match against
        
    Returns:
        bool: True if path should be included
        
    Note:
        Patterns starting with / are anchored to plugin root
        The ... wildcard means "this directory and all subdirectories"
    """
    # Normalize path separators
    path = path.replace('\\', '/')
    if path.startswith('/'):
        path = path[1:]
    
    for pattern in patterns:
        
        # Handle ... wildcard
        if pattern.endswith('/...'):
            # Check if path starts with the directory part of pattern
            dir_part = pattern[:-4]  # Remove /...
            if path == dir_part or path.startswith(dir_part + '/'):
                return True
        # Regular glob pattern
        elif fnmatch.fnmatch(path, pattern):
            return True
    
    return False

def stage_plugin_files(plugin_path: Path, staging_dir: Path, verbose: bool = False) -> None:
    """Copy filtered plugin files to staging directory.
    
    Args:
        plugin_path (Path): Path to .uplugin file
        staging_dir (Path): Temporary staging directory
        verbose (bool, optional): Print detailed file operations. Defaults to False.
    """
    plugin_root = plugin_path.parent
    plugin_name = plugin_path.stem
    target_dir = staging_dir / plugin_name
    
    # Get filter patterns and normalize them
    patterns = parse_filter_config(plugin_root)
    patterns = [p.replace('\\', '/').lstrip('/').lower() for p in patterns]
    
    if verbose:
        print("\nFilter patterns:")
        for pattern in patterns:
            print(f"  {pattern}")
    
    # Create staging directory
    target_dir.mkdir(parents=True)
    
    # First pass: collect all files that match patterns
    files_to_copy = []
    skipped_files = []
    for root, _, files in os.walk(plugin_root):
        for file in files:
            src_path = Path(root) / file
            if src_path == plugin_path:  # Skip .uplugin, handled separately
                continue
            
            # Get path relative to plugin root and normalize it
            rel_path = str(src_path.relative_to(plugin_root)).replace('\\', '/')
            rel_path_lower = rel_path.lower()  # For case-insensitive matching
            
            # Check if path matches any pattern
            matched = False
            for pattern in patterns:
                if pattern.endswith('/...'):
                    dir_part = pattern[:-4]
                    if rel_path_lower == dir_part or rel_path_lower.startswith(dir_part + '/'):
                        files_to_copy.append((src_path, rel_path))
                        matched = True
                        break
                elif fnmatch.fnmatch(rel_path_lower, pattern):
                    files_to_copy.append((src_path, rel_path))
                    matched = True
                    break
            
            if not matched:
                skipped_files.append(rel_path)
    
    if verbose:
        print("\nFiles to include:")
        for _, rel_path in files_to_copy:
            print(f"  + {rel_path}")
        print("\nFiles to exclude:")
        for rel_path in skipped_files:
            if any(rel_path.endswith(ext) for ext in SOURCE_FILE_EXTENSIONS) or \
               any(fnmatch.fnmatch(rel_path, pat) for pat in EXECUTABLE_PATTERNS):
                print(f"  - {rel_path}")
    
    # Second pass: copy matched files
    for src_path, rel_path in files_to_copy:
        dst_path = target_dir / rel_path
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src_path), str(dst_path))

def validate_staged_files(staging_dir: Path) -> bool:
    """Validate staged plugin files.
    
    Args:
        staging_dir (Path): Directory containing staged files
        
    Returns:
        bool: True if validation passed
    """
    plugin_dir = next(staging_dir.iterdir())
    has_errors = False
    errors = {
        'copyright': [],
        'path_length': [],
        'executables': []
    }
    
    for filepath in plugin_dir.rglob('*'):
        if not filepath.is_file():
            continue
            
        rel_path = str(filepath.relative_to(plugin_dir))
        
        # Check path length
        if len(str(Path(plugin_dir.name) / rel_path)) > MAX_PATH_LENGTH:
            errors['path_length'].append(rel_path)
        
        # Check for executables
        if any(fnmatch.fnmatch(filepath.name, pat) for pat in EXECUTABLE_PATTERNS):
            errors['executables'].append(rel_path)
            continue
        
        # Check copyright for source files
        if any(filepath.name.endswith(ext) for ext in SOURCE_FILE_EXTENSIONS):
            if THIRD_PARTY_MARKER not in rel_path:
                try:
                    with filepath.open('r', encoding='utf-8') as f:
                        first_line = strip_comment_markers(f.readline())
                        if not first_line.lower().startswith('copyright'):
                            errors['copyright'].append(rel_path)
                except Exception:
                    continue
    
    # Report errors
    if errors['copyright']:
        has_errors = True
        print("✗ Missing copyright notice:")
        for file in errors['copyright']:
            print(f"\t✗ {file}")
    
    if errors['path_length']:
        has_errors = True
        print("✗ Path too long (>170 chars):")
        for file in errors['path_length']:
            print(f"\t✗ {file}")
    
    if errors['executables']:
        has_errors = True
        print("✗ Executable files found:")
        for file in errors['executables']:
            print(f"\t✗ {file}")
    
    if not has_errors:
        print("✓ All file validations passed!")
    
    return not has_errors

def validate_uplugin(plugin_path: Path) -> List[str]:
    """Validate uplugin file requirements.
    
    Args:
        plugin_path (Path): Path to .uplugin file
        
    Returns:
        List[str]: List of validation errors, empty if validation passed
    """
    errors = []
    try:
        with plugin_path.open('r') as f:
            data = json.load(f)
        
        if 'FabURL' not in data:
            errors.append("Missing 'FabURL' field in .uplugin file")
        elif not data['FabURL'] or not re.search(FAB_URL_PATTERN, data['FabURL'], re.I):
            errors.append(f"Invalid 'FabURL' value: {data.get('FabURL')}")
    except Exception as e:
        errors.append(f"Failed to parse .uplugin file: {e}")
    
    return errors

def validate_compilation(plugin_dir: Path, plugin_name: str, highest_version: str, uplugin_data: dict) -> bool:
    """Validate plugin compilation for highest targeted version.
    
    Args:
        plugin_dir (Path): Directory containing staged plugin
        plugin_name (str): Name of the plugin
        highest_version (str): Highest UE version being targeted
        uplugin_data (dict): Original uplugin data to modify for compilation
        
    Returns:
        bool: True if compilation succeeds
    """
    print(f"\nValidating compilation for UE {highest_version} only...")
    
    compiler_script = Path(__file__).parent / "compile_plugin.py"
    if not compiler_script.exists():
        print("✗ Compilation validation skipped: compile_plugin.py not found")
        return False
    
    # Create temporary build directory and prepare plugin
    with tempfile.TemporaryDirectory(prefix='plugin_compile_') as build_dir:
        try:
            # Create version-specific uplugin for compilation test
            uplugin_data = uplugin_data.copy()
            uplugin_data['EngineVersion'] = highest_version
            uplugin_path = plugin_dir / plugin_name / f"{plugin_name}.uplugin"
            
            with uplugin_path.open('w') as f:
                json.dump(uplugin_data, f, indent=2)
            
            # Run compiler with streamed output
            result = subprocess.run(
                [
                    sys.executable,
                    str(compiler_script),
                    "-v", highest_version,
                    "-p", str(uplugin_path),
                    "-o", build_dir
                ],
                check=False  # Don't raise on error, handle it below
            )
            
            if result.returncode == 0:
                print("✓ Compilation validation passed")
                return True
            else:
                print("✗ Compilation validation failed!")
                return False
            
        except Exception as e:
            print(f"✗ Compilation validation error: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Package Unreal Engine plugin for multiple versions")
    parser.add_argument("-p", "--plugin", help="Path to .uplugin file or containing directory")
    parser.add_argument("-o", "--output_directory", help="Output directory for packages")
    parser.add_argument("-v", "--versions", nargs="+", help="UE versions to package for")
    parser.add_argument("--skip-validation", action="store_true", 
                       help="Skip validation checks before packaging")
    parser.add_argument("--verbose", action="store_true",
                       help="Print detailed progress information")
    parser.add_argument("--no-compile", action="store_true",
                       help="Skip compilation validation")
    args = parser.parse_args()
    
    try:
        plugin_path = find_plugin(args.plugin)
        plugin_name = plugin_path.stem
        package_dir = setup_package_dir(plugin_path, args.output_directory)
        versions = args.versions if args.versions else DEFAULT_VERSIONS
        
        # Load uplugin data once
        with plugin_path.open('r') as f:
            uplugin_data = json.load(f)
        
        with temporary_directory() as temp_dir:
            print("Staging plugin files...")
            stage_plugin_files(plugin_path, temp_dir, args.verbose)
            
            if not args.skip_validation:
                print("\nValidating plugin...")
                # Validate .uplugin first
                uplugin_errors = validate_uplugin(plugin_path)
                if uplugin_errors:
                    print("✗ .uplugin validation:")
                    for error in uplugin_errors:
                        print(f"\t✗ {error}")
                    sys.exit(1)
                else:
                    print("✓ .uplugin validation")
                
                # Validate staged files
                if not validate_staged_files(temp_dir):
                    print("\n✗ Validation failed!")
                    sys.exit(1)
                
                # Validate compilation with highest version if requested
                if not args.no_compile:
                    highest_version = max(versions)
                    if not validate_compilation(temp_dir, plugin_name, highest_version, uplugin_data):
                        print("\n✗ Compilation validation failed!")
                        sys.exit(1)
            
            # Package for each version
            for version in versions:
                print(f"\nProcessing version {version}...")
                plugin_dir = next(temp_dir.iterdir())
                
                # Update version in uplugin data
                if version.count('.') == 1:
                    version += ".0"
                uplugin_data['EngineVersion'] = version
                with (plugin_dir / f"{plugin_name}.uplugin").open('w') as f:
                    json.dump(uplugin_data, f, indent=2)
                
                # Create zip archive
                zip_path = package_dir / f"{plugin_name}_UE{version}.zip"
                if zip_path.exists():
                    zip_path.unlink()
                
                shutil.make_archive(
                    base_name=str(zip_path.with_suffix('')),
                    format='zip',
                    root_dir=str(temp_dir),
                    base_dir=plugin_name
                )
                print(f"Created package: {zip_path}")
        
        print(f"\nPackaging complete! Files are in {package_dir}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nTraceback:", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
