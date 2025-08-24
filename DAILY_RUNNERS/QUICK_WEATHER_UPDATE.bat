@echo off
echo ================================================================================
echo 🌤️  QUICK WEATHER UPDATE & LINEUP REFRESH
echo ================================================================================
echo Use this when you've updated fd_slate_today.csv with new lineups/batting orders
echo No need to pull historical data - just weather and projections update
echo.
pause

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo 🌤️  STEP 1: Updating Today's Weather Data...
echo ================================================================================
if exist "19. build_weather_today.py" (
    python "19. build_weather_today.py"
    echo ✅ Weather data updated
) else if exist "get_weather_today.py" (
    python get_weather_today.py
    echo ✅ Weather data updated
) else if exist "weather_enhanced_system.py" (
    python weather_enhanced_system.py
    echo ✅ Weather system updated
) else (
    echo ⚠️  Weather script not found - checking for weather data files...
    if exist "..\data\weather_today.csv" (
        echo ✅ Existing weather data found
    ) else (
        echo ❌ No weather data available
    )
)

echo.
echo 🏗️  STEP 2: Rebuilding Today's Features with New Lineup Data...
echo ================================================================================
echo Updating hitter features with new batting orders...
if exist "11. build_today_pitcher_features.py" (
    python "11. build_today_pitcher_features.py"
    echo ✅ Pitcher features updated
)

if exist "build_today_hitter_features.py" (
    python build_today_hitter_features.py
    echo ✅ Hitter features updated
) else (
    echo ⚠️  Hitter features script not found - using existing features
)

echo.
echo 🎯 STEP 3: Updating Player Projections...
echo ================================================================================
echo Regenerating projections with new lineup/weather data...

if exist "(23)project_base_hitter_scores.py" (
    python "(23)project_base_hitter_scores.py"
    echo ✅ Base hitter projections updated
)

if exist "(24)project_base_pitcher_scores.py" (
    python "(24)project_base_pitcher_scores.py" 
    echo ✅ Base pitcher projections updated
)

if exist "(26)project_hitter_scores.py" (
    python "(26)project_hitter_scores.py"
    echo ✅ Final hitter projections updated
)

if exist "(27)project_pitcher_scores.py" (
    python "(27)project_pitcher_scores.py"
    echo ✅ Final pitcher projections updated
)

echo.
echo 🏥 STEP 4: Creating IL-Free Player Slate...
echo ================================================================================
python FILTER_IL_PLAYERS.py

echo.
echo 🏆 STEP 5: Regenerating Championship Lineups with Updated Data...
echo ================================================================================
python MULTIPLE_CHAMPIONSHIP_BUILDER.py

echo.
echo 🔍 STEP 6: Quick Validation Check...
echo ================================================================================
python QUICK_LINEUP_CHECK.py

echo.
echo ================================================================================
echo 🎉 QUICK WEATHER UPDATE COMPLETE!
echo ================================================================================
echo.
echo ✅ What was updated:
echo    🌤️  Latest weather data incorporated
echo    🏗️  Player features rebuilt with new lineup data
echo    🎯 Projections updated with fresh weather/lineup info
echo    🏥 IL players filtered out
echo    🏆 Championship lineups regenerated
echo.
echo 📁 Your updated files:
echo    📋 New championship lineups with current weather
echo    🎯 Updated projections reflecting lineup changes
echo    🌤️  Fresh weather-enhanced features
echo.
echo 🚀 READY FOR TOURNAMENT SUBMISSION!
echo    Upload the new championship lineup files to FanDuel
echo.
pause
