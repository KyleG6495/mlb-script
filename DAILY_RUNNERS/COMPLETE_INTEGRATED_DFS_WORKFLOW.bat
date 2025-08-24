@echo off
echo =====================================
echo COMPLETE INTEGRATED DFS WORKFLOW
echo =====================================
echo Connecting ALL systems for unified decisions:
echo - Stack Analysis + Umpire Data + Weather
echo - Integrated lineup generation
echo - FanDuel format conversion
echo =====================================

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo 🔄 Activating Python environment...
call .venv\Scripts\activate.bat

echo.
echo 🚀 Starting integrated workflow...
python RUN_COMPLETE_INTEGRATED_WORKFLOW.py

echo.
echo ===============================================
echo WORKFLOW COMPLETE - CHECK RESULTS ABOVE
echo ===============================================
echo.
echo 📋 Next Steps:
echo 1. Open dashboard: python COMPLETE_ELITE_DFS_DASHBOARD.py
echo 2. Check Advanced Edge tab for umpire analysis
echo 3. Upload lineups from fd_current_slate folder
echo.
pause
