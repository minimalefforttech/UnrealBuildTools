#!/bin/bash

# Ensure script fails on any error
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux"* ]]; then
    export PYTHONPATH="${SCRIPT_DIR}/../python:${PYTHONPATH}"
else
    export PYTHONPATH="${SCRIPT_DIR}/../python;${PYTHONPATH}"
fi

if command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
else
    PYTHON_CMD=python
fi

"$PYTHON_CMD" -m unreal_build_tools.cli.package_plugin_for_fab "$@"
