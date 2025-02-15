from __future__ import absolute_import, unicode_literals
import os
import platform
from pathlib import Path
from typing import List, Optional
from .exceptions import PlatformError
from .logging import setup_logger
from .constants import Platform, ENV

logger = setup_logger(__name__)

def get_platform() -> Platform:
    """Get current platform identifier."""
    try:
        system = platform.system().lower()
        if system == "windows":
            return Platform.WIN64
        elif system == "darwin":
            return Platform.MAC
        elif system == "linux":
            return Platform.LINUX
        return Platform.UNKNOWN
    except Exception as e:
        logger.exception("Failed to determine platform")
        raise PlatformError(f"Could not determine platform: {str(e)}")

def is_platform_supported(platform_name: Platform) -> bool:
    """Check if platform is supported."""
    from .constants import SUPPORTED_PLATFORMS
    return platform_name in SUPPORTED_PLATFORMS

def get_base_path() -> Path:
    """Get platform-specific UE installation path.
    
    Returns:
        Path
    Raises:
        PlatformError: If Epic Games directory is not found
    """
    if os.getenv(ENV.ENGINE_BASE_DIR):
        base_path = Path(os.getenv(ENV.ENGINE_BASE_DIR))
    
    else:
        platform_name = get_platform()
        if platform_name == Platform.WIN64:
            base_path = Path(r"C:\Program Files\Epic Games")
        elif platform_name == Platform.MAC:
            base_path = Path("/Users/Shared/Epic Games")
        elif platform_name == Platform.LINUX:
            base_path = Path.home() / ".local/share/Epic Games"
    
    if not base_path.is_dir():
        raise PlatformError(
            f"Epic Games directory not found at: {base_path}\n"
            "Please make sure Unreal Engine is installed in the default location\n"
            "or set the UBT_ENGINE_BASE_DIR environment variable"
        )
    return base_path

def get_engine_path(version: str) -> Path:
    """
    Get Unreal Engine installation path.
    
    Args:
        version: Engine version string
        
    Returns:
        Path to engine
    
    Raises:
        PlatformError: If engine path could not be located
    """
    base_path = get_base_path()
    engine_path = base_path / f"UE_{version}"

    if not engine_path.is_dir():
        raise PlatformError(f"Could not locate Unreal Engine {version}")
    return engine_path



def get_uat_script(ue_path: Path) -> Path:
    """Get platform-specific UAT script path.
    
    Args:
        ue_path (Path): Path to Unreal Engine installation
    
    Returns:
        Path: Path to the appropriate RunUAT script
        
    Raises:
        PlatformError: If UAT script is not found
    """
    system = platform.system().lower()
    if system == "windows":
        uat_path = ue_path / "Engine/Build/BatchFiles/RunUAT.bat"
    else:
        uat_path = ue_path / "Engine/Build/BatchFiles/RunUAT.sh"
    
    if not uat_path.exists():
        raise PlatformError(
            f"UAT script not found at: {uat_path}\n"
            "Please verify your Unreal Engine installation"
        )
    
    return uat_path


def get_ue_versions(base_path: Optional[Path]=None) -> List[str]:
    """Find all installed UE versions.
    
    Args:
        base_path (Path): Base Epic Games installation path
    
    Returns:
        List[str]: Sorted list of installed UE versions
    """
    base_path = base_path or get_base_path()
    versions = []
    for path in base_path.glob("UE_*"):
        if path.is_dir():
            version = path.name[3:]  # Strip "UE_" prefix
            versions.append(version)
    return sorted(versions)