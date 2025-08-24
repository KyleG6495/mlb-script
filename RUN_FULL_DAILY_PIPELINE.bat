@echo off
cd /d "%~dp0"
echo ========================================
echo    FULL DAILY MLB PIPELINE
echo ========================================
echo Starting complete pipeline with fresh data scraping...
echo.

REM Step 1: Scrape fresh data (players, games, weather, etc.)
echo [1/4] Scraping fresh MLB data...
call RUN_ENHANCED_OPTIMIZER_ONLY.bat

REM Step 2: Train ML models with new data
echo.
echo [2/4] Training ML models with fresh data...
powershell -ExecutionPolicy Bypass -File ".\run_train_all_props.ps1"

REM Step 3: Generate predictions and lineups
echo.
echo [3/4] Generating predictions and optimal lineups...
python enhanced_fanduel_optimizer.py

REM Step 4: Analyze betting props
echo.
echo [4/4] Analyzing betting opportunities...
python analyze_uf_props.py

echo.
echo ========================================
echo    FULL PIPELINE COMPLETE!
echo ========================================
echo Models trained, lineups optimized, props analyzed
echo Ready for DFS and betting decisions
pause
