# ADR-001: Python Package Structure for Unreal Build Tools

## Status
Completed

## Context
The current build tools exist as monolithic packages within Unreal Engine. We need to convert these into a maintainable, cross-platform Python package with clear interfaces and validation capabilities.

## Decision
We will restructure the tools into a Python package with the following structure:

```
UnrealBuildTools/
├── python/
│   └── unreal_build_tools/
│       ├── interfaces/
│       │   ├── validator.py
│       │   └── compiler.py
│       ├── impl/
│       │   ├── plugin_compiler.py
│       │   └── validators/
│       │       └── assorted_validators...
│       ├── cli/
│       │   ├── compile_plugin.py
│       │   ├── inputs.py
│       │   └── package_plugin_for_fab.py
│       ├── core/
│       │   ├── constants.py
│       │   ├── structs.py
│       │   ├── platform_utils.py
│       │   ├── exceptions.py
│       │   ├── filter_config.py
│       │   └── logging.py
│       ├── packaging.py
│       └── staging.py
├── bin/
│   ├── package_plugin_for_fab.sh
│   ├── package_plugin_for_fab.bat
│   ├── compile_plugin.sh
│   └── compile_plugin.bat
└── tests/
```

### Key Components:
1. Package structure under unreal_build_tools/
2. Clear separation of interfaces, validators, and CLI tools
3. Common utilities and constants at package root level
4. Platform-agnostic shell scripts in bin/

## Consequences
### Positive
- Simpler, flatter structure for easier navigation
- Clear separation between interfaces and implementations
- Unified constants and structures at package level
- Simple shell scripts for cross-platform execution

### Negative
- Less granular organization for future expansion
- Platform-specific code needs careful organization in utils

## Implementation Notes
- Shell scripts in bin/ will handle platform detection and argument forwarding
- Constants and structures centralized in dedicated files
- Platform-specific logic consolidated in platform_utils.py
- CLI tools designed for direct execution via shell scripts
