@echo off
echo ===============================================
echo 🚀 DAILY MLB DOMINATION WORKFLOW
echo 🎯 Complete Process: DFS + Props + Analysis
echo ===============================================
echo.

echo 📊 STEP 1: Generate Confirmed Starters...
python ..\Scripts\DYNAMIC_CONFIRMED_STARTERS.py
if errorlevel 1 (
    echo ❌ Failed to generate confirmed starters!
    pause
    exit /b 1
)

echo.
echo 🔥 STEP 2: Run Complete Optimization...
echo ⚡ Simulations + Ownership + Correlations + Weather
python ..\Scripts\ULTIMATE_CONFIRMED_OPTIMIZER.py
if errorlevel 1 (
    echo ❌ Optimization failed!
    pause
    exit /b 1
)

echo.
echo 🏆 STEP 3: Generate Elite Lineups...
echo 🎭 Multiple strategies: Balanced, Ceiling, Leverage
python ..\Scripts\ADVANCED_LINEUP_CONSTRUCTOR.py
if errorlevel 1 (
    echo ❌ Lineup construction failed!
    pause
    exit /b 1
)

echo.
echo 💰 STEP 4: Run Prop Models...
echo 🎲 Betting opportunities analysis
call 3_PROP_MODELS.bat
if errorlevel 1 (
    echo ❌ Prop models failed!
    pause
    exit /b 1
)

echo.
echo ===============================================
echo ✅ DAILY MLB DOMINATION COMPLETE!
echo 🏆 Elite lineups generated
echo 💰 Prop picks identified
echo 📊 Complete analysis ready
echo ===============================================
echo.

echo 📋 Today's Output Files:
echo    🏆 OPTIMIZED_LINEUPS_[timestamp].csv
echo    💰 prop_recommendations_[timestamp].csv
echo    📊 confirmed_optimized_projections.csv
echo.

echo 🎯 Next Steps:
echo    1. Review lineups in fd_current_slate folder
echo    2. Check prop picks in data folder
echo    3. Submit your best lineups to FanDuel
echo    4. Place recommended prop bets
echo.

pause
