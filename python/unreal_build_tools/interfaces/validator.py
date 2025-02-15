from abc import ABC, abstractmethod
from pathlib import Path
from ..structs import ValidationResult, PluginInfo

class IValidator(ABC):
    """Interface for plugin validation implementations."""
    
    def __init__(self, plugin_info: PluginInfo):
        """Initialize validator with plugin information.
        
        Args:
            plugin_info: Information about the plugin to validate
        """
        self.plugin_info = plugin_info
    
    @abstractmethod
    def validate(self) -> ValidationResult:
        """Run validation checks on the plugin.
        
        Returns:
            ValidationResult containing validation status and any errors/warnings
        """
        pass
