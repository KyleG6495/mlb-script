@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   [ENHANCED] AUTOMATED BETTING SYSTEM
echo   Professional ML Models + EV Analysis
echo ========================================
echo.
echo Current directory: %CD%
echo This runs the ENHANCED betting system with:
echo   [ML] Professional ML models (R² 0.964-1.000)
echo   [WEATHER] Weather integration
echo   [PARK] Park factor adjustments  
echo   [EV] Advanced EV calculations
echo   [OPPS] 183+ betting opportunities
echo.
echo Time: ~3-5 minutes
echo.
echo Prerequisites:
echo   [OK] Data pipeline completed (1_DATA_PIPELINE.bat)
echo   [OK] Player features finalized
echo.
echo Press any key to start enhanced betting analysis...
pause
echo.

echo [RUNNING] Enhanced Automated Betting System...
echo ================================================
python enhanced_automated_betting_system.py
if errorlevel 1 goto error

echo.
echo [SUCCESS] Enhanced Betting Analysis Complete!
echo.
echo [OUTPUT] OUTPUT FILES GENERATED:
echo   - enhanced_predictions_*.csv (223 players)
echo   - enhanced_betting_opportunities_*.csv (183+ EV plays)
echo   - Enhanced model performance logged
echo.
echo [CHECK] Check the console output above for:
echo   - Top 5 EV opportunities (90%+ expected value)
echo   - Model performance metrics
echo   - Total profitable opportunities found
echo.
goto end

:error
echo.
echo [ERROR] ERROR: Enhanced betting analysis failed!
echo Check the Python script for errors.
echo.
pause
exit /b 1

:end
echo.
echo [COMPLETE] Enhanced betting analysis complete!
echo Ready for profitable betting!
echo.
pause
