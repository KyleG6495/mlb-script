@echo off
setlocal enabledelayedexpansion

echo Debugging file existence checks...
echo.

REM Test individual files
echo Testing 1_DATA_PIPELINE.bat:
if exist "1_DATA_PIPELINE.bat" (
    echo ✅ Found 1_DATA_PIPELINE.bat
    findstr /c:"config_batch.bat" "1_DATA_PIPELINE.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Contains config_batch.bat call
    ) else (
        echo ❌ Missing config_batch.bat call
    )
) else (
    echo ❌ 1_DATA_PIPELINE.bat not found
)

echo.
echo Testing COMPLETE_DAILY_WORKFLOW.bat:
if exist "COMPLETE_DAILY_WORKFLOW.bat" (
    echo ✅ Found COMPLETE_DAILY_WORKFLOW.bat
    findstr /c:"config_batch.bat" "COMPLETE_DAILY_WORKFLOW.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Contains config_batch.bat call
    ) else (
        echo ❌ Missing config_batch.bat call
    )
) else (
    echo ❌ COMPLETE_DAILY_WORKFLOW.bat not found
)

echo.
echo Testing 2_DFS_MODELS.bat:
if exist "2_DFS_MODELS.bat" (
    echo ✅ Found 2_DFS_MODELS.bat
    findstr /c:"config_batch.bat" "2_DFS_MODELS.bat" >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ Contains config_batch.bat call
    ) else (
        echo ❌ Missing config_batch.bat call
    )
) else (
    echo ❌ 2_DFS_MODELS.bat not found
)

pause
