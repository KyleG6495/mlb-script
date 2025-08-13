@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🏆 CHAMPIONSHIP LINEUP BUILDER
echo   Real Starting Pitcher System
echo ========================================
echo.
echo Current directory: %CD%
echo This builds lineups using ONLY confirmed starting pitchers
echo Expected performance: 140-145 FPPG (realistic ceiling for today's slate)
echo.
echo Prerequisites:
echo   ✅ Data pipeline completed (1_DATA_PIPELINE.bat)
echo   ✅ fd_slate_today.csv updated with today's slate
echo.
echo Press any key to build championship lineup...
pause
echo.

echo Choose your championship strategy:
echo [1] Single Best Lineup (Real starters only)
echo [2] Multiple Diverse Lineups (10+ lineups with real starters)
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    echo Step 1: Building Single Championship Lineup...
    python CHAMPIONSHIP_LINEUP_BUILDER.py
    if errorlevel 1 (
        echo ❌ Championship builder failed
        echo Check that fd_slate_today.csv has today's players
        goto error
    )
) else if "%choice%"=="2" (
    echo Step 1: Building Multiple Championship Lineups...
    python MULTIPLE_CHAMPIONSHIP_BUILDER.py
    if errorlevel 1 (
        echo ❌ Multiple championship builder failed
        echo Check that fd_slate_today.csv has today's players
        goto error
    )
) else (
    echo Invalid choice, building single lineup...
    python CHAMPIONSHIP_LINEUP_BUILDER.py
    if errorlevel 1 (
        echo ❌ Championship builder failed
        echo Check that fd_slate_today.csv has today's players
        goto error
    )
)

echo.
echo ========================================
echo 🎉 CHAMPIONSHIP LINEUP COMPLETE! 
echo ========================================
echo.
echo 🎯 FILES CREATED:
if "%choice%"=="2" (
    echo   🏆 MULTIPLE_CHAMPIONSHIP_LINEUPS_*.csv (detailed view)
    echo   📋 CHAMPIONSHIP_FANDUEL_SUBMISSION_*.csv (ready for FanDuel upload)
    echo   📊 10+ diverse lineups for multi-entry tournaments
) else (
    echo   🏆 CHAMPIONSHIP_SUBMISSION_*.csv (ready for FanDuel upload)
    echo   📊 Single optimized lineup
)
echo.
echo 📊 PERFORMANCE:
echo   🎯 Target: 140-145 FPPG (realistic for today's pitcher slate)
echo   ✅ Uses ONLY confirmed starting pitchers
echo   💰 Stays within $35,000 salary cap
echo   � Best available with weak pitching slate
echo.
echo 🚀 READY FOR TOURNAMENT SUBMISSION!
echo   Upload the CHAMPIONSHIP_SUBMISSION_*.csv file to FanDuel
echo   ⚠️  Note: Today's pitching slate is weaker than usual
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in championship lineup building!
echo.
echo Troubleshooting:
echo   ❓ Did you run 1_DATA_PIPELINE.bat first?
echo   ❓ Is fd_slate_today.csv updated with today's slate?
echo   ❓ Are there players available in all positions?
echo.

:end
pause
