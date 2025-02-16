@echo off
setlocal enabledelayedexpansion

set SCRIPT_DIR=%~dp0
set PYTHON_PATH_TO_ADD=%SCRIPT_DIR%\..\python

echo !PYTHONPATH! | findstr /C:"%PYTHON_PATH_TO_ADD%" >nul
if errorlevel 1 (
    set PYTHONPATH=%PYTHON_PATH_TO_ADD%;%PYTHONPATH%
)

where python >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
) else (
    where python3 >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        set PYTHON_CMD=python3
    ) else (
        echo Python not found. Please install Python and add it to PATH.
        exit /b 1
    )
)

%PYTHON_CMD% -m unreal_build_tools.cli.package_plugin_for_fab %*
endlocal
