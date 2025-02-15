from pathlib import Path
from typing import List
from ..interfaces.validator import IValidator
from ..structs import ValidationResult, PluginInfo
from ..constants import SOURCE_FILE_EXTENSIONS, THIRD_PARTY_MARKER, COMMENT_PREFIXES

class FabPluginCopyrightValidator(IValidator):
    """Validates copyright notices in source files."""

    def strip_comment_markers(self, line: str) -> str:
        """Strip common comment markers and whitespace from a line."""
        line = line.strip()
        for prefix in COMMENT_PREFIXES:
            if line.startswith(prefix):
                line = line[len(prefix):].strip()
        return line

    def validate(self) -> ValidationResult:
        """Check if source files have copyright notices.
        
        Returns:
            ValidationResult: Contains validation status and any errors
        """
        errors: List[str] = []
        source_dir = self.plugin_info.source_dir
        
        for filepath in source_dir.rglob('*'):
            if not filepath.is_file():
                continue
                
            rel_path = str(filepath.relative_to(source_dir))
            
            # Check copyright for source files
            if any(filepath.name.endswith(ext) for ext in SOURCE_FILE_EXTENSIONS):
                if THIRD_PARTY_MARKER not in rel_path:
                    try:
                        with filepath.open('r', encoding='utf-8') as f:
                            first_line = self.strip_comment_markers(f.readline())
                            if not first_line.lower().startswith('copyright'):
                                errors.append(f"Missing copyright notice on first line in: {rel_path}")
                    except Exception as e:
                        errors.append(f"Failed to check copyright in {rel_path}: {str(e)}")

        return ValidationResult(
            name="Copyright Notice Validation",
            success=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
