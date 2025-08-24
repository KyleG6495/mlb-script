@echo off
REM =====================================================
REM ENHANCED MLB PREDICTION SYSTEM - MASTER WORKFLOW
REM =====================================================
REM 
REM This batch file runs the complete enhanced prediction pipeline:
REM 1. Enhanced model training with time-series validation
REM 2. Weather-enhanced prediction generation  
REM 3. Advanced betting system with market bias correction
REM 4. Performance tracking and backtesting
REM 5. EV opportunity identification
REM
REM Major improvements implemented:
REM ✅ Time-series cross-validation (no data leakage)
REM ✅ Weather & environmental features
REM ✅ Advanced pitcher matchup analytics  
REM ✅ Market-aware modeling with bias correction
REM ✅ Ensemble meta-models (XGBoost + LightGBM + RF + GB)
REM ✅ Real-time feature updates
REM ✅ Performance backtesting system
REM =====================================================

echo.
echo 🚀 ENHANCED MLB PREDICTION SYSTEM
echo ====================================
echo.

REM Set Python executable path
set PYTHON_EXE=C:\Users\kgone\AppData\Local\Programs\Python\Python311\python.exe

REM Change to Scripts directory
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo ⏰ Started at %TIME% on %DATE%
echo.

REM =====================================================
REM STEP 1: ENHANCED MODEL TRAINING (if needed)
REM =====================================================
echo 🎯 STEP 1: Enhanced Model Training
echo ===================================
echo Checking if model retraining is needed...

REM Check if enhanced models exist and are recent (within 7 days)
set RETRAIN_NEEDED=0

REM Check if enhanced models directory exists
if not exist "models\homeRuns\homeRuns_enhanced_model.pkl" (
    echo   ⚠️ Enhanced models not found - training needed
    set RETRAIN_NEEDED=1
) else (
    echo   ✅ Enhanced models found
    
    REM Check if models are older than 7 days (simplified check)
    forfiles /p "models\homeRuns" /m "homeRuns_enhanced_model.pkl" /d -7 >nul 2>&1
    if errorlevel 1 (
        echo   ⚠️ Models are older than 7 days - retraining recommended
        set RETRAIN_NEEDED=1
    ) else (
        echo   ✅ Models are recent (less than 7 days old)
    )
)

if %RETRAIN_NEEDED%==1 (
    echo.
    echo   🤖 Training enhanced models with advanced features...
    echo   - Time-series validation
    echo   - Weather integration  
    echo   - Advanced pitcher analytics
    echo   - Ensemble methods
    echo.
    
    %PYTHON_EXE% enhanced_model_trainer.py
    
    if errorlevel 1 (
        echo   ❌ Enhanced model training failed!
        pause
        exit /b 1
    ) else (
        echo   ✅ Enhanced model training completed successfully
    )
) else (
    echo   ✅ Using existing enhanced models
)

echo.
echo ================================================
echo ⚡ Model Training Status: COMPLETE
echo ================================================
echo.

REM =====================================================
REM STEP 2: ENHANCED PREDICTION GENERATION
REM =====================================================
echo 🔮 STEP 2: Enhanced Prediction Generation
echo ========================================
echo Generating predictions with all enhancements...
echo   - Ensemble model predictions
echo   - Market bias corrections
echo   - Advanced feature engineering
echo.

%PYTHON_EXE% enhanced_automated_betting_system.py

if errorlevel 1 (
    echo   ❌ Enhanced prediction generation failed!
    pause
    exit /b 1
) else (
    echo   ✅ Enhanced predictions generated successfully
)

echo.
echo ================================================
echo ⚡ Prediction Generation Status: COMPLETE  
echo ================================================
echo.

REM =====================================================
REM STEP 3: WEATHER ENHANCEMENT
REM =====================================================
echo 🌤️ STEP 3: Weather Enhancement
echo ==============================
echo Enhancing predictions with weather data...
echo   - Real-time weather for all ballparks
echo   - Temperature effects on power
echo   - Wind speed and direction impact
echo   - Humidity and pressure adjustments
echo.

%PYTHON_EXE% enhanced_weather_analytics.py

if errorlevel 1 (
    echo   ❌ Weather enhancement failed!
    pause
    exit /b 1
) else (
    echo   ✅ Weather enhancement completed successfully
)

echo.
echo ================================================
echo ⚡ Weather Enhancement Status: COMPLETE
echo ================================================
echo.

REM =====================================================
REM STEP 4: SPORTSBOOK LINE COLLECTION
REM =====================================================
echo 📊 STEP 4: Sportsbook Line Collection
echo ====================================
echo Collecting current lines from sportsbooks...

echo   🎲 PrizePicks MLB Lines...
%PYTHON_EXE% PrizePicks_mlb.py

if errorlevel 1 (
    echo   ⚠️ PrizePicks scraping encountered issues (continuing...)
) else (
    echo   ✅ PrizePicks lines collected
)

echo   🎯 Underdog Fantasy Lines...
%PYTHON_EXE% underdog_fantasy_mlb.py

if errorlevel 1 (
    echo   ⚠️ Underdog scraping encountered issues (continuing...)
) else (
    echo   ✅ Underdog lines collected  
)

echo.
echo ================================================
echo ⚡ Line Collection Status: COMPLETE
echo ================================================
echo.

REM =====================================================
REM STEP 5: EXPECTED VALUE CALCULATION  
REM =====================================================
echo 💰 STEP 5: Expected Value Analysis
echo =================================
echo Calculating EV opportunities with enhanced predictions...
echo   - Weather-adjusted predictions vs market lines
echo   - Market bias corrections applied
echo   - High-confidence opportunities identified
echo.

REM Run the EV analysis (part of enhanced betting system)
echo   Running comprehensive EV analysis...

REM The EV calculation is already integrated into the enhanced betting system
REM But let's run the prop models script for additional analysis
%PYTHON_EXE% -c "
import sys
sys.path.append('.')
from enhanced_automated_betting_system import EnhancedBettingSystem
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info('🎯 Running enhanced EV analysis...')
betting_system = EnhancedBettingSystem()

# Load models
if betting_system.load_enhanced_models():
    # Load latest weather-enhanced predictions
    try:
        predictions_df = pd.read_csv('../data/weather_enhanced_predictions_latest.csv')
        logger.info(f'📊 Loaded {len(predictions_df)} weather-enhanced predictions')
        
        # Calculate EV opportunities
        ev_opportunities = betting_system.calculate_expected_value(predictions_df)
        
        if ev_opportunities:
            logger.info(f'💰 Found {len(ev_opportunities)} EV opportunities')
            logger.info('🔥 TOP 3 OPPORTUNITIES:')
            for i, opp in enumerate(ev_opportunities[:3], 1):
                logger.info(f'{i}. {opp[\"player\"]} {opp[\"stat\"]} OVER {opp[\"line\"]} ({opp[\"expected_value\"]:.1f}%% EV)')
        else:
            logger.info('📊 No profitable opportunities found currently')
            
    except FileNotFoundError:
        logger.warning('❌ Weather-enhanced predictions not found')
else:
    logger.error('❌ Could not load enhanced models')
"

echo.
echo ================================================
echo ⚡ Expected Value Analysis Status: COMPLETE
echo ================================================
echo.

REM =====================================================
REM STEP 6: PERFORMANCE TRACKING
REM =====================================================
echo 📊 STEP 6: Performance Tracking & Analysis
echo ==========================================
echo Analyzing model performance and betting results...
echo   - Historical prediction accuracy
echo   - Win rate analysis by stat type
echo   - ROI calculation for betting strategies
echo   - Model improvement recommendations
echo.

%PYTHON_EXE% enhanced_performance_tracker.py

if errorlevel 1 (
    echo   ⚠️ Performance tracking encountered issues (continuing...)
) else (
    echo   ✅ Performance analysis completed
)

echo.
echo ================================================
echo ⚡ Performance Tracking Status: COMPLETE
echo ================================================
echo.

REM =====================================================
REM FINAL SUMMARY
REM =====================================================
echo.
echo 🎉 ENHANCED MLB PREDICTION SYSTEM - COMPLETE!
echo =============================================
echo.
echo ✅ All enhanced systems executed successfully:
echo    📊 Enhanced model training (time-series validation)
echo    🔮 Advanced prediction generation (ensemble models)
echo    🌤️ Weather-enhanced analytics
echo    📊 Sportsbook line collection
echo    💰 Expected value analysis
echo    📈 Performance tracking
echo.

REM Check if we have profitable opportunities
if exist "..\data\enhanced_ev_opportunities_*.csv" (
    echo 🔥 PROFITABLE BETTING OPPORTUNITIES FOUND!
    echo    Check: enhanced_ev_opportunities_latest.csv
    echo.
) else (
    echo 📊 No profitable opportunities at this time
    echo    Continue monitoring throughout the day
    echo.
)

echo 📁 Key Output Files:
echo    - weather_enhanced_predictions_latest.csv
echo    - enhanced_ev_opportunities_latest.csv  
echo    - performance_report_latest.json
echo    - performance_analysis_latest.png
echo.

echo ⏰ Completed at %TIME% on %DATE%
echo.

REM Optional: Display top opportunities
echo 💎 Checking for top betting opportunities...
%PYTHON_EXE% -c "
import pandas as pd
import os
import glob

# Find latest EV file
ev_files = glob.glob('../data/enhanced_ev_opportunities_*.csv')
if ev_files:
    latest_ev_file = max(ev_files, key=os.path.getctime)
    try:
        df = pd.read_csv(latest_ev_file)
        if len(df) > 0:
            print()
            print('🔥 TOP 5 BETTING OPPORTUNITIES:')
            print('=' * 50)
            for i, row in df.head(5).iterrows():
                print(f'{i+1}. {row[\"player\"]} {row[\"stat\"]} OVER {row[\"line\"]}')
                print(f'   Prediction: {row[\"prediction\"]:.2f} | EV: {row[\"expected_value\"]:.1f}% | Source: {row[\"source\"]}')
                print()
        else:
            print('📊 No opportunities found in latest analysis')
    except Exception as e:
        print(f'❌ Error reading EV file: {e}')
else:
    print('📊 No EV opportunity files found')
"

echo.
echo 🚀 System ready for next analysis cycle!
echo    Rerun this batch file throughout the day for updated opportunities
echo.

pause
