
# ENHANCED ELITE DFS WORKFLOW
# Now includes all advanced edge techniques

@echo off
echo.
echo ====================================================
echo         ELITE DFS WORKFLOW v2.0 - ENHANCED
echo ====================================================
echo.

echo Step 1: Data Pipeline (Foundation)
echo --------------------------------
cd "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
call python collect_data.py
call python process_slate.py
echo Base data ready
echo.

echo Step 2: Advanced Edge Analysis  
echo --------------------------------
call python ELITE_ADVANCED_STACK_OPTIMIZER.py
call python umpire_edge_analyzer.py
call python ownership_leverage_analyzer.py
echo Advanced analysis complete
echo.

echo Step 3: Stack Optimization
echo ----------------------------
call python ADVANCED_STACK_OPTIMIZER.py
call python generate_lineups_enhanced.py
echo Optimized stacks generated
echo.

echo Step 4: Launch Elite Dashboard
echo --------------------------------
call python COMPLETE_ELITE_DFS_DASHBOARD.py
echo Dashboard launched with all features
echo.

echo ENHANCED WORKFLOW COMPLETE!
echo All advanced edge techniques now active
pause
