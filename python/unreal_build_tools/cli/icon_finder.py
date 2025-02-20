import sys
import argparse
from pathlib import Path
from ..core.platform_utils import get_base_path, get_ue_versions
from ..ui.icon_finder.main import run_app

def parse_args():
    parser = argparse.ArgumentParser(description='Unreal Engine Icon Browser')
    parser.add_argument('--base-path', type=Path, help='Base path for UE installations')
    parser.add_argument('--versions', nargs='+', help='UE versions to search')
    parser.add_argument('--icon-types', nargs='+', choices=['svg', 'png'], 
                       default=['svg', 'png'], help='Icon types to include')
    
    args = parser.parse_args()
    
    # Use defaults if not specified
    if not args.base_path:
        args.base_path = get_base_path()
    if not args.versions:
        args.versions = get_ue_versions(args.base_path)
        
    return args

def main():
    """Entry point for the icon finder CLI"""
    args = parse_args()
    return run_app(versions=args.versions, base_path=args.base_path, icon_types=args.icon_types)

if __name__ == "__main__":
    sys.exit(main())
