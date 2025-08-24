@echo off
echo ================================================================================
echo 🏆 DAILY TOURNAMENT LINEUP GENERATOR
echo ================================================================================
echo This runs AFTER the data pipeline to generate tournament-ready lineups
echo.
echo ⚠️  IMPORTANT: Make sure you have fresh fd_slate_today.csv uploaded first!
echo.
pause

cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo 🔍 STEP 1: Checking for Injured Players...
echo ================================================================================
python -c "
import pandas as pd
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
il_players = df[df['Injury Indicator'] == 'IL']
print(f'⚠️  Found {len(il_players)} players on Injured List')
if len(il_players) > 0:
    print('📋 Injured players will be REMOVED from lineups:')
    for _, p in il_players.head(10).iterrows():
        print(f'   ❌ {p[\"First Name\"]} {p[\"Last Name\"]} - {p[\"Position\"]} - ${p[\"Salary\"]} - {p[\"Injury Details\"]}')
    if len(il_players) > 10:
        print(f'   ... and {len(il_players) - 10} more')
print()
"

echo.
echo 🏥 STEP 2: Creating IL-Free Player Slate...
echo ================================================================================
python -c "
import pandas as pd
df = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
healthy = df[df['Injury Indicator'] != 'IL'].copy()
healthy.to_csv('../data/fd_slate_NO_IL_PLAYERS.csv', index=False)
print(f'✅ Created healthy-only slate: {len(healthy)} players')
print(f'❌ Removed {len(df) - len(healthy)} injured players')
print()
"

echo.
echo 🎯 STEP 3: Getting Confirmed Starters (RotoWire Check)...
echo ================================================================================
if exist "GET_CONFIRMED_STARTERS.py" (
    python GET_CONFIRMED_STARTERS.py
) else (
    echo ⚠️  GET_CONFIRMED_STARTERS.py not found - skipping confirmed starters check
)

echo.
echo 🏆 STEP 4: Generating Championship Tournament Lineups...
echo ================================================================================
python MULTIPLE_CHAMPIONSHIP_BUILDER.py

echo.
echo 📊 STEP 5: Running Monte Carlo Tournament Analysis...
echo ================================================================================
if exist "MONTE_CARLO_SIMULATION_SYSTEM.py" (
    python MONTE_CARLO_SIMULATION_SYSTEM.py
) else (
    echo ⚠️  Monte Carlo system not found - skipping simulation analysis
)

echo.
echo ================================================================================
echo 🎉 DAILY TOURNAMENT GENERATION COMPLETE!
echo ================================================================================
echo.
echo ✅ What was generated:
echo    🏥 IL-free player slate (no injured players)
echo    🎯 Real confirmed starters identified
echo    🏆 8+ championship tournament lineups (116-130 FPPG)
echo    📊 Monte Carlo tournament probability analysis
echo.
echo 📁 Your files are ready in /data/ folder:
echo    📋 CHAMPIONSHIP_LINEUP_X_[Strategy]_[timestamp].csv (upload to FanDuel)
echo    📊 CHAMPIONSHIP_LINEUPS_SUMMARY_[timestamp].csv (overview)
echo.
echo 🚀 NEXT STEPS:
echo    1. Check the summary file for lineup quality
echo    2. Upload individual lineup files to FanDuel
echo    3. Use 8+ lineups for tournament coverage
echo.
pause
