@echo off
REM Daily Automated MLB Betting Analysis
echo Starting Daily MLB Betting Analysis...

REM Set the working directory
cd "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

REM Run the automated betting system
"C:\Users\kgone\AppData\Local\Programs\Python\Python311\python.exe" -c "
from automated_betting_system import AutomatedBettingSystem
from datetime import datetime

# Initialize system
system = AutomatedBettingSystem()

# Run analysis for today
today = datetime.now().strftime('%%Y-%%m-%%d')
print(f'🚀 Running betting analysis for {today}')
system.run_daily_analysis(today, min_edge=0.05)
"

echo ✅ Daily analysis complete! Check the betting_analysis folder for results.
pause
