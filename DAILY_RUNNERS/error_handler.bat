@echo off
REM ============================================================================
REM 🚨 ERROR HANDLING UTILITIES - Standardized Error Management
REM ============================================================================
REM Usage: call error_handler.bat "script_name" %errorlevel% "optional_message"

setlocal
set "SCRIPT_NAME=%~1"
set "ERROR_CODE=%~2"
set "ERROR_MESSAGE=%~3"

if %ERROR_CODE% neq 0 (
    set /a ERROR_COUNT+=1
    echo.
    echo ❌ ERROR IN %SCRIPT_NAME%
    echo    Error Code: %ERROR_CODE%
    if not "%ERROR_MESSAGE%"=="" echo    Message: %ERROR_MESSAGE%
    echo    Time: %date% %time%
    echo.
    
    REM Log error
    echo [ERROR] %date% %time% - %SCRIPT_NAME% failed with code %ERROR_CODE% >> "%LOG_FILE%" 2>nul
    
    REM Ask user what to do
    echo Choose an option:
    echo   [C] Continue with next step
    echo   [R] Retry this step  
    echo   [Q] Quit workflow
    echo.
    choice /c CRQ /n /m "Your choice: "
    
    if errorlevel 3 (
        echo 🛑 Workflow aborted by user
        exit /b %ERROR_CODE%
    )
    if errorlevel 2 (
        echo 🔄 Retrying %SCRIPT_NAME%...
        exit /b 999
    )
    if errorlevel 1 (
        echo ⚠️ Continuing with warnings...
        exit /b 0
    )
) else (
    echo ✅ %SCRIPT_NAME% completed successfully
    echo [SUCCESS] %date% %time% - %SCRIPT_NAME% completed >> "%LOG_FILE%" 2>nul
)

endlocal
exit /b 0
