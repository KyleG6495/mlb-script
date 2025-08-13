@echo off
echo ===============================================
echo 🚀 COMPLETE OPTIMIZATION WORKFLOW
echo 🎯 Simulations + Ownership + Advanced Lineups
echo ===============================================
echo.

echo 📊 STEP 1: Running Ultimate Optimization Engine...
echo ⚡ This includes: 2000 simulations per player, ownership projections, correlations
python ..\ULTIMATE_CONFIRMED_OPTIMIZER.py
if errorlevel 1 (
    echo ❌ Optimization failed!
    pause
    exit /b 1
)

echo.
echo 🏆 STEP 2: Constructing Advanced Lineups...
echo 🎭 Multiple strategies: Balanced, Ceiling, Leverage, Cash
python ..\ADVANCED_LINEUP_CONSTRUCTOR.py
if errorlevel 1 (
    echo ❌ Lineup construction failed!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo ✅ COMPLETE OPTIMIZATION WORKFLOW FINISHED!
echo 📈 Optimized projections created
echo 🏆 Advanced lineups generated  
echo 🎯 Ready for submission!
echo ===============================================
echo.

echo 📋 Generated files:
echo    📊 confirmed_optimized_projections.csv
echo    🏆 OPTIMIZED_LINEUPS_[timestamp].csv
echo.

pause
