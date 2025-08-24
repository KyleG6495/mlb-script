@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🎯 MASTER DFS WORKFLOW SYSTEM
echo   Complete Automated Pipeline
echo ========================================
echo.
echo This will run the complete DFS workflow:
echo   1. Check prerequisites (slate data, scripts)
echo   2. Interactive lineup generation (with/without props)
echo   3. Optional performance validation
echo   4. Generate FanDuel-ready files
echo   5. Provide next steps and performance expectations
echo.
echo Prerequisites automatically checked:
echo   ✅ fd_slate_today.csv (updated slate data)
echo   ✅ SIMPLE_CLEAN_GENERATOR.py (proven system)
echo   ✅ MY_DAILY_PROPS_DIVERSIFIED.py (prop integration)
echo   ✅ PROPER_VALIDATION.py (performance validation)
echo.
echo Press any key to start the complete workflow...
pause
echo.

python MASTER_DFS_WORKFLOW.py

echo.
echo ========================================
echo 🎯 MASTER WORKFLOW COMPLETE!
echo ========================================
pause
