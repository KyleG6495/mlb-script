@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🚀 ENHANCED DFS SIMULATION ONLY
echo   Advanced Game State Projections
echo ========================================
echo.
echo This runs ONLY the enhanced DFS simulation system:
echo   📊 Game state simulation
echo   🎯 Advanced projections  
echo   ⚡ Enhanced DFS lineups
echo.
echo Time: ~10-15 minutes
echo.
echo Prerequisites:
echo   ✅ Data pipeline completed (1_DATA_PIPELINE.bat)
echo   ✅ Player features finalized
echo.
echo Press any key to start enhanced DFS simulation...
pause
echo.

echo 🚀 Running Enhanced DFS Simulation...
echo =====================================
call "DAILY_RUNNERS\2B_ENHANCED_DFS.bat"

if errorlevel 1 goto error

echo.
echo ✅ Enhanced DFS Simulation Complete!
echo.
echo 📊 OUTPUT FILES GENERATED:
echo   • Enhanced DFS lineups with game simulation
echo   • Advanced projection files
echo   • Detailed simulation reports
echo.
goto end

:error
echo.
echo ❌ ERROR: Enhanced DFS simulation failed!
echo Check the Python script for errors.
echo.
pause
exit /b 1

:end
echo.
echo 🎯 Enhanced DFS simulation complete!
echo Advanced lineups ready! 🚀
echo.
pause
