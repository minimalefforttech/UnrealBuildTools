import json
import re
from typing import List
from unreal_build_tools.interfaces.validator import IValidator
from unreal_build_tools.core.structs import ValidationResult, PluginInfo
from unreal_build_tools.core.constants import FAB_URL_PATTERN

class FabPluginUpluginValidator(IValidator):
    """Validates the .uplugin file content."""

    def validate(self) -> ValidationResult:
        """Validate uplugin file requirements.
        
        Returns:
            ValidationResult: Contains validation status and any errors
        """
        errors: List[str] = []
        uplugin_path = self.plugin_info.uplugin_file
        
        try:
            with uplugin_path.open('r') as f:
                data = json.load(f)
            
            if 'FabURL' not in data:
                errors.append("Missing 'FabURL' field in .uplugin file")
            elif not data['FabURL'] or not re.search(FAB_URL_PATTERN, data['FabURL'], re.I):
                errors.append(f"Invalid 'FabURL' value: {data.get('FabURL')}")
                
        except Exception as e:
            errors.append(f"Failed to parse .uplugin file: {str(e)}")

        return ValidationResult(
            name="Uplugin File Validation",
            success=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
