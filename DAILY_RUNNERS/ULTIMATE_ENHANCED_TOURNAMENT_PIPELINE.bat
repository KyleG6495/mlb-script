@echo off
echo ===============================================
echo 🚀 ULTIMATE ENHANCED TOURNAMENT PIPELINE
echo 💎 Complete Data + Confirmed Starters + Enhanced Models
echo ===============================================
echo.

echo ⚡ FEATURES:
echo   ✅ 20-step historical data pipeline COMPLETE
echo   ✅ Weather and park factors integrated
echo   ✅ Rolling 5-game performance features  
echo   ✅ Confirmed RotoWire starting lineups
echo   ✅ Enhanced ML projections
echo   ✅ Tournament volume generation
echo.
echo 🎯 TARGET: 210+ point lineups with confirmed starters
echo.
echo Press any key to start ultimate pipeline...
pause
echo.

echo 🔍 STEP 1: Update Confirmed Starters Analysis...
echo 📊 Using RotoWire verified lineups with enhanced data
python ..\DYNAMIC_CONFIRMED_STARTERS.py
if errorlevel 1 (
    echo ❌ Failed to get confirmed starters!
    pause
    exit /b 1
)

echo.
echo 🧠 STEP 2: Generate Enhanced Model Improvements...  
echo ⚡ ML optimizations using historical + weather + park data
python ..\PRACTICAL_MODEL_IMPROVEMENTS.py
if errorlevel 1 (
    echo ⚠️ Model improvements failed - continuing with existing models
)

echo.
echo 🎮 STEP 3: Game State Enhanced DFS...
echo 🏟️ Advanced projections with park factors and weather
python ..\GAME_STATE_ENHANCED_DFS.py
if errorlevel 1 (
    echo ❌ Game state analysis failed!
    pause
    exit /b 1
)

echo.
echo 🎯 STEP 4: Enhanced Lineup Optimization...
echo 💎 Combining confirmed starters with enhanced projections  
python ..\ENHANCED_ML_DFS.py
if errorlevel 1 (
    echo ❌ Enhanced lineup optimization failed!
    pause
    exit /b 1
)

echo.
echo 🏆 STEP 5: Tournament Volume Generation...
echo 🎭 20 diverse lineups using enhanced confirmed starters
python ..\TOURNAMENT_VOLUME_GENERATOR.py
if errorlevel 1 (
    echo ❌ Tournament volume generation failed!
    pause
    exit /b 1
)

echo.
echo 💰 STEP 6: Enhanced Prop Analysis...
echo 🎲 Advanced betting opportunities with weather/park context
call 3_PROP_MODELS.bat
if errorlevel 1 (
    echo ⚠️ Prop analysis had issues - check output files
)

echo.
echo ===============================================
echo 🎉 ULTIMATE ENHANCED PIPELINE COMPLETE!
echo ===============================================
echo.
echo 💎 ENHANCED RESULTS:
echo   🎯 Confirmed starting players only (RotoWire verified)
echo   📊 Historical performance + weather + park factors
echo   🧠 Enhanced ML projections with 210+ point targets
echo   🏆 Diverse tournament lineups ready for submission
echo   💰 Advanced prop betting analysis
echo.
echo 📋 Enhanced Output Files:
echo   🎯 Enhanced_game_state_projections.csv
echo   🏆 TOURNAMENT_VOLUME_[timestamp].csv (enhanced)
echo   💰 Enhanced_prop_predictions.csv
echo   📊 Enhanced_betting_opportunities.csv
echo.
echo 🚨 ULTIMATE SAFETY: Only confirmed starters + enhanced data!
echo.

pause
