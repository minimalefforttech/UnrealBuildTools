class UnrealBuildToolsError(Exception):
    """Base exception for all UnrealBuildTools errors."""
    pass

class PlatformError(UnrealBuildToolsError):
    """Raised when a platform-specific operation fails."""
    pass

class BuildError(UnrealBuildToolsError):
    """Raised when a build operation fails."""
    pass

class ConfigurationError(Exception):
    """Raised when there is an error in the configuration."""
    pass

class EngineError(UnrealBuildToolsError):
    """Raised when there is an error related to Unreal Engine."""
    pass

class ValidationError(Exception):
    """Raised when validation fails."""
    pass
