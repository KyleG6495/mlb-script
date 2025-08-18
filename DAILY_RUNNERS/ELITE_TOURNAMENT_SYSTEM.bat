@echo off
echo ================================================
echo ELITE TOURNAMENT SYSTEM - ENHANCED
echo Based on 104-point, top 35% finish analysis
echo ================================================
echo.

echo [%time%] Starting Elite Tournament System...

cd /d "c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo Step 1: Elite Tournament Analysis
echo ================================
python "ELITE_TOURNAMENT_SYSTEM_ENHANCED.py"
if %errorlevel% neq 0 (
    echo ERROR: Elite tournament analysis failed
    pause
    exit /b 1
)

echo.
echo Step 2: Elite Lineup Builder  
echo =============================
python "ELITE_TOURNAMENT_LINEUP_BUILDER.py"
if %errorlevel% neq 0 (
    echo ERROR: Elite lineup builder failed
    pause
    exit /b 1
)

echo.
echo Step 3: Enhanced Late Swap Monitoring
echo ====================================
echo Starting enhanced late swap system with Waldrep patterns...
python "LATE_SWAP_AUTOMATION.py" --elite-mode
if %errorlevel% neq 0 (
    echo WARNING: Late swap system encountered issues
)

echo.
echo ================================================
echo ELITE SYSTEM COMPLETE!
echo ================================================
echo.
echo ✅ Elite patterns analyzed (Waldrep anchor strategy)
echo ✅ Tournament lineups generated (40%% anchors, 30%% stacks)  
echo ✅ Late swap monitoring active (contrarian opportunities)
echo.
echo 🎯 TARGET: Consistent top 20%% finishes with 120+ upside
echo 🏆 Based on your proven 104-point tournament success
echo.
echo Check fd_current_slate/ folder for generated lineups
echo.
pause
