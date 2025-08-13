@echo off
cd /d "C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts"
echo ========================================
echo   🎯 BETTING OPPORTUNITIES ONLY
echo   Quick EV Recalculation  
echo ========================================
echo.
echo This ONLY recalculates betting opportunities:
echo   💰 Enhanced betting analysis (90%+ EV opportunities)
echo   📊 Uses existing player data/predictions
echo   ⚡ Super fast update
echo.
echo Time: ~3-5 minutes
echo.
echo Use this when:
echo   ✅ Just want fresh betting opportunities
echo   ✅ Sportsbook lines changed
echo   ✅ Quick EV check before placing bets
echo.
echo Press any key to recalculate betting opportunities...
pause
echo.

echo 💰 Recalculating Enhanced Betting Opportunities...
call "DAILY_RUNNERS\4_ENHANCED_BETTING.bat"
if errorlevel 1 (
    echo ⚠️ Enhanced betting failed - check Python script
    goto error
) else (
    echo ✅ Enhanced betting opportunities updated!
    echo.
    echo 💎 CHECK CONSOLE OUTPUT ABOVE FOR:
    echo   🔥 Top 5 EV opportunities (90%+ expected value)
    echo   📊 Total profitable opportunities found
    echo   🎯 Confidence levels for each bet
)

echo.
echo ========================================
echo 💰 BETTING OPPORTUNITIES UPDATED!
echo ========================================
echo.
echo 🎯 WHAT TO DO NOW:
echo   1. Review the EV opportunities in console output above
echo   2. Focus on 90%+ EV bets shown
echo   3. Place your enhanced betting picks
echo   4. Profit! 💎
echo.
goto end

:error
echo.
echo ❌ ERROR updating betting opportunities!
echo Check enhanced_automated_betting_system.py for issues.
echo.

:end
echo 🚀 Betting opportunities refreshed! Ready to bet! 💰
pause
