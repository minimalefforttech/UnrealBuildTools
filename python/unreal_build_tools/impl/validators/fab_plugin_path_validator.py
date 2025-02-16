from pathlib import Path
from typing import List
from unreal_build_tools.interfaces.validator import IValidator
from unreal_build_tools.core.structs import ValidationResult, PluginInfo
from unreal_build_tools.core.constants import MAX_PATH_LENGTH

class FabPluginPathValidator(IValidator):
    """Validates path lengths in plugin files."""

    def validate(self) -> ValidationResult:
        """Check if any file paths exceed maximum length.
        
        Returns:
            ValidationResult: Contains validation status and any errors
        """
        errors: List[str] = []
        source_dir = self.plugin_info.source_dir
        plugin_name = source_dir.name
        
        for filepath in source_dir.rglob('*'):
            if not filepath.is_file():
                continue
                
            rel_path = str(filepath.relative_to(source_dir))
            full_path = str(Path(plugin_name) / rel_path)
            
            if len(full_path) > MAX_PATH_LENGTH:
                errors.append(
                    f"Path exceeds {MAX_PATH_LENGTH} characters: {rel_path}"
                )

        return ValidationResult(
            name="Path Length Validation",
            success=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
