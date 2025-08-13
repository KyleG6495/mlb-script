# Props Betting Results Analysis Guide

## Overview

Analyze your PrizePicks and Underdog Fantasy prop bet performance with detailed breakdowns, win rates, and value analysis.

## Quick Start

### PrizePicks Analysis
```bash
python analyze_props_results.py
# or
python analyze_props_results.py prizepicks
```

### Underdog Fantasy Analysis  
```bash
python analyze_props_results.py underdog
```

### Specific Date Analysis
```bash
python analyze_props_results.py prizepicks 2025-07-21
```

## What You Get

### 📈 Overall Performance Metrics
- **Total Bets Placed**: Count of all prop bets analyzed
- **Overall Win Rate**: Percentage of winning bets
- **Winning vs Losing Bets**: Raw count breakdown

### 🎯 Performance by Confidence Level
- **HIGH Confidence**: Win rate for high-confidence picks
- **MEDIUM/LOW Confidence**: Performance across confidence tiers
- **Average Expected Value (EV)**: Expected value by confidence

### 📊 Performance by Stat Type
Track which prop categories perform best:
- **Home Runs**: Power hitting props
- **Total Bases**: Hitting production props  
- **RBIs**: Run production props
- **Hits**: Contact hitting props
- **Runs**: Scoring props
- **Pitcher Strikeouts**: Pitching props

### ⬆️ Performance by Bet Type
- **OVER Bets**: Performance on over props
- **UNDER Bets**: Performance on under props

### 🌟 Best Performing Players
Identify which players consistently hit their props:
- Players with multiple bets (2+)
- Sorted by win rate and total wins
- Perfect records highlighted

### 💰 Value Tier Analysis
Expected Value performance breakdown:
- **Premium (EV > 0.5)**: Highest value bets
- **High (EV 0.2-0.5)**: Strong value bets
- **Medium (EV 0.1-0.2)**: Moderate value bets  
- **Low (EV < 0.1)**: Lower value bets

### 🏆 Top Performing Bets
- **Top 10 Winning Bets by EV**: Your best value wins
- **Biggest Missed Opportunities**: High EV bets that lost

## Sample Analysis Output

```
📈 OVERALL PERFORMANCE
========================================
Total Bets: 576
Winning Bets: 200  
Win Rate: 34.7%

🎯 PERFORMANCE BY CONFIDENCE LEVEL
==================================================
HIGH        : 179/509 (35.2%) | Avg EV: 0.693
MEDIUM      : 21/67 (31.3%) | Avg EV: 0.172

📊 PERFORMANCE BY STAT TYPE
========================================
Total Bases         :  59/122 ( 48.4%)
Hits                :  50/115 ( 43.5%)
RBIs                :  42/117 ( 35.9%)
Home Runs           :  16/101 ( 15.8%)

⬆️ PERFORMANCE BY BET TYPE
===================================
OVER      :  68/ 82 ( 82.9%)
UNDER     : 132/494 ( 26.7%)

🌟 BEST PERFORMING PLAYERS
===================================
Aaron Judge              : 4/4 (100.0%)
Cole Young               : 3/3 (100.0%)
Vladimir Guerrero Jr.    : 4/5 (80.0%)
```

## Files Generated

### 1. **Detailed Results CSV**
`prizepicks_results_YYYYMMDD.csv` contains:
- Every prop bet with outcome
- Player, stat type, line, bet type
- Actual performance vs line
- Win/loss result
- Confidence and EV data
- Result display string

### 2. **Stats Template CSV**
`prizepicks_actual_stats_YYYYMMDD.csv` for manual entry:
- Player names and teams
- Batting stats (H, R, RBI, HR, SB, TB)
- Pitching stats (IP, K, W, SV)
- Template for entering real MLB stats

## Using Real Data

### Option 1: Manual Entry
1. Open `prizepicks_actual_stats_YYYYMMDD.csv`
2. Fill in actual MLB stats for each player
3. Re-run analysis for precise results

### Option 2: Import from Sources
- ESPN fantasy results
- Yahoo sports data
- MLB.com box scores
- FanDuel/DraftKings results

## Key Insights to Track

### 🔍 Stat Type Performance
- **Total Bases**: Often highest win rate (48.4% in sample)
- **Home Runs**: Typically lowest win rate (15.8% in sample)  
- **OVER vs UNDER**: OVER bets often perform much better

### 📊 Value Analysis
- Higher EV doesn't always mean higher win rate
- Track correlation between confidence and performance
- Identify which stat types provide best value

### 🎯 Player Patterns
- Some players consistently hit/miss props
- Weather and park factors affect performance
- Injury status and lineup position matter

## Strategy Optimization

### Based on Results:
1. **Focus on High-Performing Stat Types**: Total Bases, Hits
2. **Consider OVER Bias**: OVER bets show higher win rates
3. **Track Player Consistency**: Target reliable performers
4. **Value vs Win Rate**: Balance EV with actual performance

### Red Flags:
- Low win rate on Home Run props
- Under-performing high EV bets
- Players with consistent misses

## Integration with Other Tools

### Combined Analysis:
1. **DFS Lineups**: Cross-reference with FanDuel performance
2. **Betting Strategy**: Combine with sportsbook analysis
3. **Player Research**: Use for future prop selection

### Workflow:
1. **Before Games**: Select props using EV analysis
2. **After Games**: Run performance analysis  
3. **Weekly Review**: Identify patterns and trends
4. **Strategy Adjustment**: Refine selection criteria

## Advanced Features

### Future Enhancements:
- Auto-import from MLB Stats API
- Weather/park factor integration
- Bankroll management tracking
- Multi-day trend analysis
- Player form tracking

### Custom Analysis:
- Filter by date ranges
- Analyze specific players/teams
- Track seasonal performance
- Compare platform performance

## Troubleshooting

### Common Issues:
- **No files found**: Check date format (YYYY-MM-DD)
- **Missing columns**: File format may vary by source
- **Simulated results**: Real stats not available, using random data

### File Compatibility:
- Works with `prediction_report` files
- Compatible with `real_ev` files  
- Supports `ev_analysis` formats
- Adapts to different column naming

## Best Practices

1. **Regular Analysis**: Review performance after each slate
2. **Data Quality**: Use real stats when possible
3. **Pattern Recognition**: Track what works over time
4. **Bankroll Management**: Size bets based on confidence/EV
5. **Continuous Learning**: Adjust strategy based on results

---

## Quick Reference Commands

```bash
# Yesterday's PrizePicks
python analyze_props_results.py

# Yesterday's Underdog  
python analyze_props_results.py underdog

# Specific date
python analyze_props_results.py prizepicks 2025-07-20

# Help and usage
python analyze_props_results.py --help
```
