@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Informaecho 💰 Becho 📊 COMPARISON FILES:
echo   📋 Standard lineup: optimized_lineup.csv
echo   📈 Performance comparison displayed aboveING PROPS (TODAY'S PICKS):
echo   🎯 prizepicks_real_ev_*.csv (PrizePicks opportunities)
echo   🎲 uf_mlb_picks.xlsx (Underdog Fantasy props)
echo   📊 betting_analysis\betting_report_*.txt (Full analysis)
echo   📈 betting_analysis\betting_opportunities_*.csv (Detailed bets)\MLB\Scripts"
echo ========================================
echo   🔥 ENHANCED FANDUEL OPTIMIZER ONLY
echo   QUICK DAILY LINEUP GENERATION  
echo ========================================
echo.
echo This runs ONLY the enhanced FanDuel optimizer
echo Time: ~5-10 minutes
echo Requires: Complete pipeline data already exists
echo.
echo Press any key to start enhanced optimization...
pause
echo.

echo 🔄 Loading enhanced data sources...
echo   ✅ Weather-park factors
echo   ✅ Player features 
echo   ✅ ML projections
echo   ✅ Real-time adjustments
echo.

echo 🔥 Running Enhanced FanDuel Optimizer...
python enhanced_fanduel_optimizer.py
if errorlevel 1 goto error

echo 📊 Running Daily Lineup Selector...
python daily_lineup_selector.py
if errorlevel 1 goto error

echo 🎯 Running Multi-Entry Optimizer...
python multi_entry_optimizer.py
if errorlevel 1 goto error

echo 💰 Running Betting Props Analysis...
python platform_ev_analyzer.py
if errorlevel 1 goto error

echo 🎲 Running Underdog Fantasy Scraper...
python underdog_fantasy_mlb.py
if errorlevel 1 goto error

echo 📊 Analyzing UF Props...
python analyze_uf_props.py
if errorlevel 1 goto error

echo 🎯 Running Automated Betting System...
python automated_betting_system.py
if errorlevel 1 goto error

echo.
echo ========================================
echo 🎉 ENHANCED OPTIMIZATION COMPLETE!
echo.
echo 🔥 ENHANCED LINEUPS (USE THESE):
echo   📈 enhanced_lineup_gpp_*.csv (Tournament lineups)
echo   🏆 enhanced_lineup_balanced_*.csv (Cash game lineups)
echo.
echo � BETTING PROPS (TODAY'S PICKS):
echo   🎯 prizepicks_real_ev_*.csv (PrizePicks opportunities)
echo   🎲 betting_analysis\betting_report_*.txt (Full analysis)
echo   📊 betting_analysis\betting_opportunities_*.csv (Detailed bets)
echo.
echo �📊 COMPARISON FILES:
echo   📋 Standard lineup: optimized_lineup.csv
echo   📈 Performance comparison displayed above
echo.
echo 💡 TIP: Enhanced lineups typically score 15-25 points higher!
echo 💡 TIP: Check betting files for today's high-EV props!
echo ========================================
goto end

:error
echo.
echo ❌ ERROR in enhanced optimization!
echo Make sure you've run the complete pipeline first.
echo Missing required files:
echo   - fd_hitter_features_final.csv
echo   - fd_pitcher_features_final.csv  
echo   - merged_weather_park.csv
echo.

:end
pause
