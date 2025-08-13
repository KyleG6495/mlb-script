@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   QUICK PRE-SLATE UPDATE
echo   Lineups + Betting Only (Fast!)
echo ========================================
echo.
echo This quickly updates for lineup changes:
echo   - Filtered DFS (with latest injury info)
echo   - Enhanced Betting (recalculated EV opportunities)
echo.
echo Time: ~5-10 minutes (vs 90-100 for full pipeline)
echo.
echo Use this when:
echo   - Lineups posted/changed
echo   - Injury updates
echo   - 1 hour before slate
echo.
echo Press any key to start quick update...
pause
echo.

echo Rebuilding Filtered DFS Lineups (most accurate)...
call "DAILY_RUNNERS\2A_FILTERED_DFS.bat"
if errorlevel 1 (
    echo WARNING: Filtered DFS failed
    goto error
) else (
    echo SUCCESS: Filtered DFS completed with latest lineups!
)

echo.
echo Recalculating Enhanced Betting Opportunities...
call "DAILY_RUNNERS\4_ENHANCED_BETTING.bat"
if errorlevel 1 (
    echo WARNING: Enhanced betting failed
    goto error
) else (
    echo SUCCESS: Enhanced betting updated - check console for new EV opportunities!
)

echo.
echo ========================================
echo [COMPLETE] QUICK UPDATE COMPLETE!
echo ========================================
echo.
echo [UPDATED] FILES UPDATED:
echo   [DFS] Latest filtered DFS lineups (injury-aware)
echo   [BETTING] Fresh betting opportunities with current data
echo.
echo [FILES] USE THESE UPDATED FILES:
echo   [GOLD] filtered_dfs_lineup_*.csv (Upload to FanDuel)
echo   [EV] Console output above (90%+ EV betting opportunities)
echo.
goto end

:error
echo.
echo [ERROR] ERROR in quick update!
echo Try running individual components or full pipeline.
echo.

:end
echo [READY] Quick update complete! Ready for slate!
pause
