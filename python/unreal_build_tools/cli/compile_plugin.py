from __future__ import absolute_import, unicode_literals
import argparse
import sys
import traceback
from pathlib import Path

from unreal_build_tools.logging import setup_logger
from unreal_build_tools.platform_utils import get_platform, get_engine_path
from unreal_build_tools.filesystem import find_uplugin, temporary_directory
from unreal_build_tools.structs import CompilerConfig
from unreal_build_tools.exceptions import UnrealBuildToolsError
from unreal_build_tools.impl.plugin_compiler import PluginCompiler
from unreal_build_tools.cli.inputs import select_ue_version

logger = setup_logger(__name__)

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Compile an Unreal Engine plugin')
    parser.add_argument('plugin', nargs='?', help='Path to .uplugin file')
    parser.add_argument(
        '--engine-version', '-e',
        help='Unreal Engine version'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        help='Output directory for compiled plugin'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    return parser.parse_args()

def main() -> int:
    try:
        args = parse_args()
        if args.verbose:
            logger.setLevel("DEBUG")

        plugin_path = find_uplugin(args.plugin)
        logger.info(f"Compiling plugin: {plugin_path}")

        platform = get_platform()
        
        # Get engine version from args or prompt
        engine_version = args.engine_version
        if not engine_version:
            engine_version = select_ue_version(None)
            
        engine_path = get_engine_path(engine_version)
        
        # Set up base compiler config
        config = CompilerConfig(
            platform=platform,
            engine_path=engine_path,
            source=plugin_path,
            output_dir=args.output,
        )
        # These are separate because if no output_dir is specified, we need to use a temporary directory
        if args.output:
            logger.info(f"Output directory: {config.output_dir}")
            
            compiler = PluginCompiler(config)
            success = compiler.run()
        else:
            with temporary_directory() as temp_dir:
                config.output_dir = temp_dir
                
                compiler = PluginCompiler(config)
                success = compiler.run()
                
        if not success:
            raise UnrealBuildToolsError("Plugin compilation failed")
            
        logger.info(
            "Plugin compiled successfully in temporary directory. "
            "Use --output to specify a permanent location."
        )
        
        return 0

    except UnrealBuildToolsError as e:
        traceback.print_exc()
        logger.error(str(e))
        return 1
    except Exception as e:
        traceback.print_exc()
        logger.exception("Unexpected error occurred")
        return 1

if __name__ == '__main__':
    sys.exit(main())
