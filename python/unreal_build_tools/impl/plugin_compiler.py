from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import logging

from ..interfaces.compiler import ICompiler
from ..structs import CompilerConfig
from ..platform_utils import get_uat_script

logger = logging.getLogger(__file__)

class PluginCompiler(ICompiler):
    def __init__(self, config: CompilerConfig):
        self._config = config
        self._uat_script: Optional[Path] = None

    @property
    def compiler_config(self) -> CompilerConfig:
        """Get the compiler configuration."""
        return self._config

    def setup(self) -> bool:
        """Initialize UAT script path and verify existence."""
        try:
            self._uat_script = get_uat_script(self.compiler_config.engine_path)
            return self._uat_script.exists()
        except Exception as e:
            logger.error(f"Setup failed: {str(e)}")
            return False

    def pre_validate(self) -> bool:
        """Validate .uplugin file and UAT script existence."""
        if not self.compiler_config.source.suffix == '.uplugin':
            logger.error("Source file must be a .uplugin file")
            return False
        return True

    def compile(self) -> bool:
        """Compile the plugin using UAT BuildPlugin command."""
        try:
            cmd = [
                str(self._uat_script),
                "BuildPlugin",
                f"-Plugin={self.compiler_config.source}",
                f"-Package={self.compiler_config.output_dir}",
            ]
            
            if self.compiler_config.extra_arguments:
                for key, value in self.compiler_config.extra_arguments.items():
                    cmd.append(f"-{key}={value}")
            
            result = subprocess.call(cmd)
            return result == 0
            
        except Exception as e:
            logger.error(f"Compilation error: {str(e)}")
            return False

    def post_validate(self) -> bool:
        """Verify compilation outputs exist."""
        try:
            if not (self.compiler_config.output_dir / "Binaries").exists():
                logger.error("Missing Binaries directory in output")
                return False
            return True
        except Exception as e:
            logger.error(f"Post-validation failed: {str(e)}")
            return False

    def tear_down(self) -> None:
        """Clean up temporary build files."""
        try:
            # Clean intermediate files if needed
            logger.info("Cleaning up build artifacts")
            self._uat_script = None
        except Exception as e:
            logger.error(f"Teardown error: {str(e)}")

    def run(self) -> bool:
        """Execute all compilation steps in order."""
        try:
            logger.info("Starting plugin compilation process")
            
            if not self.setup():
                logger.error("Setup failed")
                return False
                
            if not self.pre_validate():
                logger.error("Pre-validation failed")
                return False
                
            if not self.compile():
                logger.error("Compilation failed")
                return False
                
            if not self.post_validate():
                logger.error("Post-validation failed")
                return False
                
            logger.info("Plugin compilation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Compilation process failed: {str(e)}")
            return 
        finally:
            self.tear_down()  # Ensure cleanup happens even on failure