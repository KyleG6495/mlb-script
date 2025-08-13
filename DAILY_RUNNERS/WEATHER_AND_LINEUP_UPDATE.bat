@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🌤️ WEATHER + LINEUP QUICK UPDATE  
echo   Smart Data Refresh (No Full Pipeline)
echo ========================================
echo.
echo This updates key data points without full pipeline:
echo   🌤️ Weather data (temperature, wind, humidity)
echo   👥 Batting orders (if posted)
echo   ⚾ Probable pitchers (if changed)
echo   🔧 Filtered DFS lineups
echo   💰 Enhanced betting opportunities
echo.
echo Time: ~8-12 minutes (vs 90-100 for full pipeline)
echo.
echo Use this when:
echo   ✅ Weather changed significantly  
echo   ✅ Major lineup changes
echo   ✅ Probable pitcher changes
echo.
echo Press any key to start weather + lineup update...
pause
echo.

echo 🌤️ Updating weather data...
python scrape_weather_data.py
if errorlevel 1 (
    echo ⚠️ Weather update failed - continuing with existing data
)

echo.
echo 👥 Checking for batting order updates...
python check_batting_orders.py
if errorlevel 1 (
    echo ⚠️ Batting order check failed - using existing lineups
)

echo.
echo ⚾ Updating probable pitchers...
python (008)filter_probable_pitchers.py
if errorlevel 1 (
    echo ⚠️ Pitcher update failed - using existing data
)

echo.
echo 🔧 Rebuilding Filtered DFS with updated data...
call "DAILY_RUNNERS\2A_FILTERED_DFS.bat"
if errorlevel 1 (
    echo ⚠️ Filtered DFS failed
    goto error
) else (
    echo ✅ Filtered DFS completed with fresh data!
)

echo.
echo 💰 Recalculating Enhanced Betting with weather factors...
call "DAILY_RUNNERS\4_ENHANCED_BETTING.bat"  
if errorlevel 1 (
    echo ⚠️ Enhanced betting failed
    goto error
) else (
    echo ✅ Enhanced betting updated with weather impact!
)

echo.
echo ========================================
echo 🌤️ WEATHER + LINEUP UPDATE COMPLETE!
echo ========================================
echo.
echo ✅ UPDATED:
echo   🌤️ Weather data (temperature impact on HRs)
echo   👥 Latest batting orders
echo   ⚾ Probable pitcher changes  
echo   🎯 Filtered DFS lineups
echo   💰 Enhanced betting opportunities
echo.
echo 📁 USE THESE UPDATED FILES:
echo   🥇 filtered_dfs_lineup_*.csv (Upload to FanDuel)
echo   💎 Console output above (Updated EV opportunities)
echo.
goto end

:error
echo.
echo ❌ ERROR in weather + lineup update!
echo Consider running full pipeline or individual components.
echo.

:end
echo 🚀 Weather + lineup update complete! 🌤️⚾
pause
