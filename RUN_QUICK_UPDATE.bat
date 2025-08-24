@echo off
cd /d "%~dp0"
echo ========================================
echo    QUICK UPDATE PIPELINE
echo ========================================
echo Updating lineups and weather without retraining models...
echo.

REM Step 1: Refresh betting lines (quick scrape)
echo [1/4] Refreshing PrizePicks lines...
python prizepicks_mlb.py

echo [2/4] Refreshing Underdog Fantasy lines...
python underdog_fantasy_mlb.py

REM Step 2: Re-optimize lineups (uses existing trained models)
echo.
echo [3/4] Re-optimizing lineups with current data...
python enhanced_fanduel_optimizer.py

REM Step 3: Re-analyze betting props with fresh lines
echo.
echo [4/4] Re-analyzing betting opportunities with fresh lines...
python analyze_uf_props.py

echo.
echo ========================================
echo    QUICK UPDATE COMPLETE!
echo ========================================
echo Lineups updated, props re-analyzed
echo Models unchanged (use full pipeline to retrain)
pause
