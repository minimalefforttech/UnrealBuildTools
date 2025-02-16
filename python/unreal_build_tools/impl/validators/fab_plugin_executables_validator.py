import fnmatch
from typing import List
from unreal_build_tools.interfaces.validator import IValidator
from unreal_build_tools.core.structs import ValidationResult, PluginInfo
from unreal_build_tools.core.constants import EXECUTABLE_PATTERNS

class FabPluginNoExecutablesValidator(IValidator):
    """Validates executable files in plugin."""

    def validate(self) -> ValidationResult:
        """Check for executable files in plugin directory.
        
        Returns:
            ValidationResult: Contains validation status and any errors
        """
        errors: List[str] = []
        source_dir = self.plugin_info.source_dir
        
        for filepath in source_dir.rglob('*'):
            if not filepath.is_file():
                continue
                
            rel_path = str(filepath.relative_to(source_dir))
            
            if any(fnmatch.fnmatch(filepath.name, pat) for pat in EXECUTABLE_PATTERNS):
                errors.append(f"Executable file found: {rel_path}")

        return ValidationResult(
            name="Executable Files Validation",
            success=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
