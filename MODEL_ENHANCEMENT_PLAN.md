# MODEL ENHANCEMENT PLAN
# Addressing Poor Performance: 36.1% Props Win Rate & Missing 210+ DFS Lineups

## 🔥 CURRENT PROBLEMS IDENTIFIED

### Props Models Issues:
1. **Home Runs: 13.9% win rate** (terrible!)
2. **Overall: 36.1% win rate** (need 55%+ for profit)
3. **Using basic features only** (missing advanced stats)
4. **No market bias correction**
5. **Treating all bet types equally**

### DFS Models Issues:
1. **Missing high-scoring lineups** (others getting 210+ points)
2. **Using log_Salary as main feature** (weak predictor)
3. **Limited feature engineering**
4. **No advanced lineup construction**
5. **Static optimization approach**

## 🚀 IMMEDIATE IMPROVEMENTS

### 1. PROPS MODEL ENHANCEMENTS

#### A. Advanced Feature Engineering
```python
# Add these powerful features:
- Recent performance trends (3-game, 7-game, 15-game)
- Matchup-specific stats (vs LHP/RHP, vs team)
- Situational splits (home/away, day/night, weather)
- Player form indicators (hot/cold streaks)
- Ballpark factors by stat type
- Pitcher quality metrics (for hitter props)
- Platoon advantages
- Rest days impact
- Team context (lineup position, run support)
```

#### B. Stat-Specific Models
```python
# Home Runs Model (Currently 13.9% - TERRIBLE!)
- Use xSLG, hard-hit rate, barrel rate
- Ballpark HR factors
- Pitcher fly ball tendencies
- Weather (wind, temperature)
- Recent power surge indicators

# Total Bases Model (Currently best at 54.1%)
- Contact quality metrics
- Expected total bases (xTB)
- Pitcher contact rates
- Ballpark dimensions impact

# Hits Model
- Contact rate vs pitcher type
- BABIP regression opportunities
- Lineup protection factors
```

#### C. Market Bias Correction
```python
# Adjust for known market inefficiencies:
- Home run props generally overpriced
- Total bases props often have value
- Player name recognition bias
- Recent performance recency bias
```

### 2. DFS MODEL ENHANCEMENTS

#### A. Advanced FPPG Prediction
```python
# Replace basic log_Salary model with:
- xFP (expected fantasy points) modeling
- Component-based scoring (H, HR, RBI, R, SB individual models)
- Game script predictions
- Lineup construction context
- Weather/park factors by fantasy scoring
```

#### B. Multi-Objective Optimization
```python
# Instead of simple FPPG maximization:
- Ceiling/floor optimization (high-upside builds)
- Correlation modeling (stack bonuses)
- Leverage optimization (tournament strategy)
- Ownership projection avoidance
- Multiple lineup generation with diversity
```

#### C. Advanced Stack Logic
```python
# Game stacking improvements:
- Run environment prediction
- Inning-by-inning scoring models
- Pitcher fatigue modeling
- Bullpen strength analysis
- Weather impact on offense
```

## 💡 SPECIFIC IMPLEMENTATIONS

### Enhanced Props Training Script
```python
# train_enhanced_props.py
def create_advanced_features(df):
    # Recent form (3, 7, 15 games)
    for window in [3, 7, 15]:
        df[f'avg_hr_{window}'] = df.groupby('player_id')['homeRuns'].rolling(window).mean()
        df[f'avg_tb_{window}'] = df.groupby('player_id')['totalBases'].rolling(window).mean()
    
    # Matchup context
    df['vs_pitcher_hand'] = get_pitcher_handedness()
    df['platoon_advantage'] = calculate_platoon_splits()
    
    # Ballpark factors
    df['hr_park_factor'] = get_park_factors('HR')
    df['hit_park_factor'] = get_park_factors('H')
    
    # Weather impact
    df['weather_boost'] = calculate_weather_impact()
    
    return df

def train_stat_specific_model(stat_type):
    # Use different features for different stats
    if stat_type == 'home_runs':
        features = ['avg_hr_7', 'hr_park_factor', 'weather_boost', 
                   'pitcher_hr_rate', 'platoon_advantage']
    elif stat_type == 'total_bases':
        features = ['avg_tb_7', 'contact_rate', 'hit_park_factor',
                   'pitcher_contact_rate', 'lineup_protection']
    
    # Use ensemble methods
    model = VotingRegressor([
        ('rf', RandomForestRegressor(n_estimators=200)),
        ('gb', GradientBoostingRegressor()),
        ('xgb', XGBRegressor())
    ])
    
    return model
```

### Enhanced DFS Optimization
```python
# optimize_fanduel_enhanced.py
def generate_multiple_lineups(n_lineups=20):
    lineups = []
    
    for i in range(n_lineups):
        # Different strategies
        if i < 5:  # Cash game lineups
            objective = 'floor'
        elif i < 15:  # GPP balanced
            objective = 'ceiling'
        else:  # High-leverage tournament
            objective = 'leverage'
        
        lineup = optimize_single_lineup(objective, used_lineups=lineups)
        lineups.append(lineup)
    
    return lineups

def calculate_game_correlations():
    # Model how players from same game correlate
    correlations = {}
    for game in games:
        # Hitters from same team (positive correlation)
        # Opposing pitcher (negative correlation)
        # Total game scoring environment
        correlations[game] = model_game_script(game)
    
    return correlations
```

## 📊 EXPECTED IMPROVEMENTS

### Props Performance Targets:
- **Home Runs**: 13.9% → 45%+ win rate
- **Overall**: 36.1% → 55%+ win rate  
- **High-value bets**: Better identification of 60%+ win rate props

### DFS Performance Targets:
- **High-scoring lineups**: Regular 180+ point lineups
- **Tournament upside**: 210+ point ceiling lineups
- **Consistency**: Better floor performance

## 🛠️ IMPLEMENTATION PRIORITY

### Week 1: Props Enhancement
1. ✅ Advanced feature engineering for home runs
2. ✅ Stat-specific model training
3. ✅ Market bias correction implementation

### Week 2: DFS Enhancement  
1. ✅ Component-based FPPG modeling
2. ✅ Game correlation analysis
3. ✅ Multi-lineup optimization

### Week 3: Integration & Testing
1. ✅ Backtesting on historical data
2. ✅ Performance validation
3. ✅ Live deployment

## 💰 EXPECTED ROI IMPROVEMENT

### Current State:
- Props: Losing money at 36.1% win rate
- DFS: Missing top-tier lineups

### Enhanced State:
- Props: Profitable at 55%+ win rate
- DFS: Regular high-scoring tournament lineups
- Combined: Significant positive ROI

Would you like me to start implementing these enhancements? I'd recommend starting with the props model improvements since that's showing the worst performance right now.
