#!/usr/bin/env python
from __future__ import print_function
import argparse
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Optional, List, Tuple  # noqa: F401 (Python 2 compatibility)

try:
    input = raw_input  # Python 2
except NameError:
    pass  # Python 3

def get_ue_base_path() -> Path:
    """Get platform-specific UE installation path.
    
    Returns:
        Path: Base installation path for Unreal Engine
        
    Raises:
        RuntimeError: If Epic Games directory is not found
    """
    system = platform.system().lower()
    if system == "windows":
        base_path = Path(r"C:\Program Files\Epic Games")
    elif system == "darwin":
        base_path = Path("/Users/Shared/Epic Games")
    else:  # linux
        base_path = Path.home() / ".local/share/Epic Games"
    
    if not base_path.exists():
        raise RuntimeError(
            f"Epic Games directory not found at: {base_path}\n"
            "Please make sure Unreal Engine is installed in the default location"
        )
    
    return base_path

def get_uat_script(ue_path: Path) -> Path:
    """Get platform-specific UAT script path.
    
    Args:
        ue_path (Path): Path to Unreal Engine installation
    
    Returns:
        Path: Path to the appropriate RunUAT script
        
    Raises:
        RuntimeError: If UAT script is not found
    """
    system = platform.system().lower()
    if system == "windows":
        uat_path = ue_path / "Engine/Build/BatchFiles/RunUAT.bat"
    else:
        uat_path = ue_path / "Engine/Build/BatchFiles/RunUAT.sh"
    
    if not uat_path.exists():
        raise RuntimeError(
            f"UAT script not found at: {uat_path}\n"
            "Please verify your Unreal Engine installation"
        )
    
    return uat_path

def find_ue_versions(base_path: Path) -> List[str]:
    """Find all installed UE versions.
    
    Args:
        base_path (Path): Base Epic Games installation path
    
    Returns:
        List[str]: Sorted list of installed UE versions
    """
    versions = []
    for path in base_path.glob("UE_*"):
        if path.is_dir():
            version = path.name[3:]  # Strip "UE_" prefix
            versions.append(version)
    return sorted(versions, key=lambda v: [int(x) for x in v.split('.')])

def select_ue_version(versions: List[str]) -> str:
    """Interactive UE version selection.
    
    Args:
        versions (List[str]): List of available UE versions
    
    Returns:
        str: Selected UE version
        
    Raises:
        RuntimeError: If no UE installations are found
    """
    if not versions:
        raise RuntimeError("No UE installations found!")

    print("Available UE versions:")
    for idx, version in enumerate(versions, 1):
        print(f"{idx}. {version}")

    while True:
        try:
            choice = int(input(f"Select UE version (1-{len(versions)}): "))
            if 1 <= choice <= len(versions):
                return versions[choice - 1]
        except ValueError:
            pass
        print("Invalid selection. Please enter a number between 1 and", len(versions))

def find_plugin(path: Optional[str] = None) -> Path:
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
    else:
        plugins = list(Path.cwd().glob("*.uplugin"))
        if not plugins:
            raise RuntimeError("No .uplugin file found in current directory")
        if len(plugins) > 1:
            raise RuntimeError("Multiple .uplugin files found. Please specify one.")
        plugin_path = plugins[0]

    if not plugin_path.exists():
        raise RuntimeError(f"Plugin file not found: {plugin_path}")
    
    return plugin_path.resolve()

def setup_output_path(plugin_path: Path, ue_version: str, base_path: Optional[str] = None) -> Path:
    """Configure output directory.
    
    Args:
        plugin_path (Path): Path to the .uplugin file
        ue_version (str): Unreal Engine version
        base_path (Optional[str], optional): Base output directory. Defaults to None.
            If None, uses ./Builds
            If specified, uses base_path
    
    Returns:
        Path: Configured and cleaned output directory path in format:
              [base_path]/[ue_version]/[plugin_name]/
        
    Note:
        Will attempt to clean existing output directory if it exists
    """
    if base_path:
        output_base = Path(base_path)
    else:
        output_base = Path.cwd() / ".Builds"
    
    output_path = output_base / ue_version / plugin_path.stem
    
    if output_path.exists():
        print(f"Cleaning previous build directory: {output_path}")
        try:
            for item in output_path.rglob("*"):
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    item.rmdir()
            output_path.rmdir()
        except Exception as e:
            print(f"Warning: Could not clean directory completely: {e}")

    return output_path

def build_plugin(ue_version: str, plugin_path: Path, output_path: Path) -> int:
    """Execute the plugin build process.
    
    Args:
        ue_version (str): Unreal Engine version
        plugin_path (Path): Path to the .uplugin file
        output_path (Path): Build output directory
    
    Returns:
        int: Return code from build process (0 for success)
        
    Raises:
        RuntimeError: If UE installation or UAT script not found
    """
    ue_path = get_ue_base_path() / f"UE_{ue_version}"
    if not ue_path.exists():
        raise RuntimeError(f"UE {ue_version} installation not found at: {ue_path}")

    uat_script = get_uat_script(ue_path)

    print(f"Building plugin for UE {ue_version}")
    print(f"Plugin: {plugin_path}")
    print(f"Output: {output_path}")

    cmd = [
        str(uat_script.resolve()),
        "BuildPlugin",
        f"-Plugin={plugin_path.resolve()}",
        f"-Package={output_path.resolve()}"
    ]


    # if platform.system() != "Windows" and uat_script.suffix == ".sh":
    #     os.chmod(uat_script, 0o755)

    return subprocess.call(cmd)

def main():
    """Main entry point for the plugin compiler.
    
    Command line arguments:
        -v, --version: Unreal Engine version (e.g., 5.1)
        -p, --plugin: Path to .uplugin file
        -o, --output: Build output directory, defaults to ./.Builds/
    
    The output will be compiled to:
        [OUTPUT_DIR]/[UE_VERSION]/[PLUGIN_NAME]/
        
    Returns:
        int: Process exit code (0 for success)
    """
    parser = argparse.ArgumentParser(description="Unreal Engine Plugin Compiler")
    parser.add_argument("-v", "--version", help="Unreal Engine version (e.g., 5.1)")
    parser.add_argument("-p", "--plugin", help="Path to .uplugin file")
    parser.add_argument("-o", "--output_directory", 
                       help="Output directory (default: ./.Builds/[UE_VERSION]/[PLUGIN_NAME]/)")
    args = parser.parse_args()

    # Find UE version
    versions = find_ue_versions(get_ue_base_path())
    ue_version = args.version or select_ue_version(versions)
    
    # Find and validate plugin
    plugin_path = find_plugin(args.plugin)
    
    # Setup output directory
    output_path = setup_output_path(plugin_path, ue_version, args.output_directory)
        
    try:
        # Build the plugin
        result = build_plugin(ue_version, plugin_path, output_path)
        sys.exit(result)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
