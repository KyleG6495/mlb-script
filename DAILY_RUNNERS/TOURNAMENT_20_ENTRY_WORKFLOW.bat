@echo off
echo ===============================================
echo 🏆 20-ENTRY TOURNAMENT VOLUME WORKFLOW
echo 🎯 Maximum Diversity for Tournament Domination
echo ===============================================
echo.

echo 📊 STEP 1: Generate Confirmed Starters...
python ..\DYNAMIC_CONFIRMED_STARTERS.py
if errorlevel 1 (
    echo ❌ Failed to generate confirmed starters!
    pause
    exit /b 1
)

echo.
echo 🔥 STEP 2: Run Complete Optimization...
echo ⚡ Simulations + Ownership + Correlations
python ..\ULTIMATE_CONFIRMED_OPTIMIZER.py
if errorlevel 1 (
    echo ❌ Optimization failed!
    pause
    exit /b 1
)

echo.
echo 🏆 STEP 3: Generate 20 Tournament Lineups...
echo 🎭 10 Different Strategies for Maximum Diversity
python ..\TOURNAMENT_VOLUME_GENERATOR.py
if errorlevel 1 (
    echo ❌ Tournament volume generation failed!
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
echo ✅ 20-ENTRY TOURNAMENT WORKFLOW COMPLETE!
echo 🏆 20 diverse lineups generated
echo 💰 Prop picks identified
echo 📊 Complete portfolio analysis ready
echo ===============================================
echo.

echo 📋 Today's Output Files:
echo    🏆 TOURNAMENT_VOLUME_[timestamp].csv (20 lineups)
echo    💰 prop_recommendations_[timestamp].csv
echo    📊 confirmed_optimized_projections.csv
echo.

echo 🎯 Portfolio Features:
echo    ✅ 10 Different strategies (ceiling, leverage, contrarian, etc.)
echo    ✅ Maximum player diversity across lineups
echo    ✅ Salary distribution optimization
echo    ✅ Team stacking variety
echo    ✅ Ownership level diversification
echo.

echo 🏆 Tournament Strategy:
echo    💡 Use ALL 20 lineups for maximum coverage
echo    💡 Different ownership levels reduce correlation
echo    💡 Multiple strategies capture different scenarios
echo    💡 Portfolio approach maximizes tournament equity
echo.

pause
