@echo off
REM ============================================================================
REM 🔧 BATCH CONFIGURATION - Standardized Environment Setup
REM ============================================================================
REM This file provides standardized paths and environment setup for all batch files
REM Source this file from other batch scripts: call config_batch.bat

REM Set base directories using relative paths
set "SCRIPTS_DIR=%~dp0\.."
set "DATA_DIR=%SCRIPTS_DIR%\..\data\"
set "FD_SLATE_DIR=%SCRIPTS_DIR%\..\fd_current_slate\"
set "DAILY_RUNNERS_DIR=%~dp0"

REM Change to Scripts directory for all operations
cd /d "%SCRIPTS_DIR%"

REM Virtual environment activation
set "VENV_PATH=%SCRIPTS_DIR%\.venv"
if exist "%VENV_PATH%\Scripts\activate.bat" (
    echo 🔧 Activating virtual environment...
    call "%VENV_PATH%\Scripts\activate.bat"
    set "PYTHON_EXE=%VENV_PATH%\Scripts\python.exe"
    echo ✅ Virtual environment activated
) else (
    echo ⚠️ Virtual environment not found, using system Python
    set "PYTHON_EXE=python"
)

REM Error handling function
set "ERROR_COUNT=0"

REM Logging setup
set "LOG_DIR=%SCRIPTS_DIR%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\batch_execution_%date:~-4,4%%date:~-10,2%%date:~-7,2%.log"

echo.
echo ============================================================================
echo 🔧 BATCH CONFIGURATION COMPLETE
echo Scripts Directory: %SCRIPTS_DIR%
echo Data Directory: %DATA_DIR%
echo Python Executable: %PYTHON_EXE%
echo Log File: %LOG_FILE%
echo ============================================================================
echo.
