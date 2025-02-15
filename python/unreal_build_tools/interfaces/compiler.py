from abc import ABC, abstractmethod, abstractproperty
from pathlib import Path
from typing import Optional, List, Dict, Any
from ..structs import CompilerConfig
from ..constants import Platform

class ICompiler(ABC):
    """Interface for compiler implementations defining the build lifecycle."""
    
    @property
    @abstractmethod
    def compiler_config(self) -> CompilerConfig:
        """Get the compiler configuration."""
        pass
    
    @abstractmethod
    def setup(self) -> bool:
        """Prepare compiler environment and resources."""
        pass
        
    @abstractmethod
    def pre_validate(self) -> bool:
        """Validate source files and requirements before compilation.""" 
        pass

    @abstractmethod
    def compile(self) -> bool:
        """Execute the compilation process."""
        pass

    @abstractmethod
    def post_validate(self) -> bool:
        """Validate compilation results."""
        pass

    @abstractmethod
    def tear_down(self) -> None:
        """Clean up resources and temporary files."""
        pass

    @abstractmethod
    def run(self) -> bool:
        """Execute the full compilation process in order."""
        pass
