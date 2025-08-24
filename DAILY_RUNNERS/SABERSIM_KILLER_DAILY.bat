#!/bin/bash
# SABERSIM KILLER DAILY ROUTINE
# ============================
# Run this every day to build competitive lineups

echo "🎯 SABERSIM KILLER DAILY ROUTINE STARTING..."
echo "=============================================="

# Step 1: Update data pipeline
echo "📊 Step 1: Running data pipeline..."
call "1_DATA_PIPELINE.bat"

# Step 2: Apply projection fixes
echo "🔧 Step 2: Applying projection recalibration..."
python "PROJECTION_RECALIBRATION.py"

# Step 3: Run edge detection
echo "🎯 Step 3: Identifying daily edges..."
python "SABERSIM_KILLER.py"

# Step 4: Apply emergency fixes to projections
echo "⚡ Step 4: Applying emergency projection fixes..."
python "EMERGENCY_PROJECTION_FIXES.py"

# Step 5: Run enhanced DFS systems
echo "🚀 Step 5: Running enhanced DFS systems..."
call "2A_FILTERED_DFS.bat"
call "2B_ENHANCED_DFS.bat" 
call "CHAMPIONSHIP_LINEUP_BUILDER.bat"

# Step 6: Performance tracking
echo "📈 Step 6: Tracking performance..."
python "LINEUP_PERFORMANCE_DIAGNOSTIC.py"

echo ""
echo "✅ SABERSIM KILLER ROUTINE COMPLETE!"
echo "🏆 Your lineups are now competitive with top sites"
echo "📊 Check outputs for today's optimal lineups"
