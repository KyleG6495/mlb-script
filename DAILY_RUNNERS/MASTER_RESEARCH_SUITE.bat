@echo off
echo ========================================
echo  🧠 MASTER DFS RESEARCH SUITE
echo  Complete Advanced Analysis Pipeline
echo ========================================

cd /d "c:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"

echo.
echo [STEP 0] Cleaning slate data - removing injured players...
python CLEAN_SLATE_DATA.py
if %errorlevel% neq 0 (
    echo ERROR: Slate cleaning failed!
    pause
    exit /b 1
)
echo ✅ Clean slate created - Shane Bieber and 346 other injured players removed

echo.
echo [STEP 1] Advanced Stack Optimization...
python ADVANCED_STACK_OPTIMIZER.py
if %errorlevel% neq 0 (
    echo ERROR: Stack optimization failed!
    pause
    exit /b 1
)
echo ✅ Elite stacks identified

echo.
echo [STEP 2] Correlation Analysis...
python advanced_correlation_analyzer.py
if %errorlevel% neq 0 (
    echo ERROR: Correlation analysis failed!
    pause
    exit /b 1
)
echo ✅ Hidden edges discovered

echo.
echo [STEP 3] Ownership Leverage Analysis...
python ownership_leverage_analyzer.py
if %errorlevel% neq 0 (
    echo ERROR: Leverage analysis failed!
    pause
    exit /b 1
)
echo ✅ High leverage spots identified

echo.
echo [STEP 4] Regenerating Clean Ownership Projections...
python ADVANCED_OWNERSHIP_PROJECTIONS.py
if %errorlevel% neq 0 (
    echo ERROR: Ownership projection regeneration failed!
    pause
    exit /b 1
)
echo ✅ Fresh ownership projections generated with clean data

echo.
echo [STEP 5] GPP Stacking Strategy...
python ENHANCED_GPP_STACKING_STRATEGY_FIXED.py
if %errorlevel% neq 0 (
    echo ERROR: GPP strategy failed!
    pause
    exit /b 1
)
echo ✅ Tournament stacks optimized

echo.
echo ========================================
echo  🎉 RESEARCH SUITE COMPLETE!
echo ========================================
echo.
echo 📊 Research Files Generated:
echo   - team_stack_analysis_[timestamp].csv
echo   - stack_recommendations_[timestamp].csv
echo   - Clean slate with 1,472 active players
echo.
echo 🚀 Next Steps:
echo   1. Review stack recommendations
echo   2. Build lineups using insights
echo   3. Run your main data pipeline
echo   4. Launch dashboard for final analysis
echo.
pause
