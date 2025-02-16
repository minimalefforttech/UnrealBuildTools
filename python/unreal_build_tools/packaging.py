import json
from pathlib import Path
import shutil
from .core.filesystem import temporary_directory
from .core.logging import setup_logger

logger = setup_logger(__name__)

def package_version_for_fab(
    staged_plugin_dir: Path,
    version: str,
    output_dir: Path
) -> None:
    """Package plugin for specific UE version from staged files.
    
    Raises:
        ConfigurationError: If plugin files are invalid
        RuntimeError: If packaging operation fails
    """
    with temporary_directory() as temp_dir:
        # Create version directory
        version_dir = temp_dir / f"UE{version}"
        version_dir.mkdir()
        
        # Copy staged files to version directory
        plugin_name = staged_plugin_dir.name
        plugin_dir = version_dir / plugin_name
        shutil.copytree(staged_plugin_dir, plugin_dir)
        
        # Update plugin version
        uplugin_path = next(plugin_dir.glob("*.uplugin"))
        with uplugin_path.open('r') as f:
            uplugin_data = json.load(f)
        
        if version.count('.') == 1:
            uplugin_data['EngineVersion'] = f"{version}.0"
        else:
            uplugin_data['EngineVersion'] = version
            
        with uplugin_path.open('w') as f:
            json.dump(uplugin_data, f, indent=2)
        
        # Create zip archive
        zip_path = output_dir / f"{plugin_name}_UE{version}.zip"
        if zip_path.exists():
            zip_path.unlink()
        
        shutil.make_archive(
            str(zip_path.with_suffix('')),
            'zip',
            root_dir=str(version_dir),
            base_dir=plugin_name
        )
        
        logger.info(f"Created package: {zip_path}")