#!/usr/bin/env python3
"""
EMERGENCY PROJECTION FIXES
=========================
Apply these immediately to fix your lineups.
"""

def apply_emergency_fixes(df):
    """
    EMERGENCY FIXES - Apply these to your projection dataframe RIGHT NOW
    """
    
    # 1. POSITION MULTIPLIERS (Based on actual missed performance)
    position_fixes = {
        'P': 1.15,   # Missing pitcher studs like Max Fried
        'C': 1.25,   # MASSIVELY undervaluing catchers
        '1B': 1.20,  # Missing power 1B guys
        '2B': 1.05,
        '3B': 1.10,
        'SS': 1.10,  # Missing top SS
        'OF': 1.15,  # Missing OF studs
        'CF': 1.15,
        'LF': 1.15,
        'RF': 1.15
    }
    
    # Apply position fixes
    for position, multiplier in position_fixes.items():
        mask = df['position'] == position
        df.loc[mask, 'fppg_projection'] *= multiplier
        print(f"✅ Applied {multiplier}x multiplier to {position}")
    
    # 2. TEAM STACK BONUSES (Teams that are hot)
    hot_teams = {
        'BAL': 1.20,  # 41.2 avg pts - they're ON FIRE
        'DET': 1.15,  # 45.2 avg pts - very hot
        'MIN': 1.10,  # Brooks Lee went off
        'CLE': 1.10,  # Manzardo crushing
        'TEX': 1.10   # Higashioka hot
    }
    
    # Apply team bonuses
    for team, bonus in hot_teams.items():
        mask = df['team'] == team
        df.loc[mask, 'fppg_projection'] *= bonus
        count = mask.sum()
        print(f"🔥 Applied {bonus}x bonus to {count} {team} players")
    
    # 3. RECENCY BIAS (Recent performance matters more)
    if 'last_3_games_avg' in df.columns and 'season_avg' in df.columns:
        # Players outperforming recently get big boost
        recent_boost = 1.0 + (df['last_3_games_avg'] - df['season_avg']) * 0.4
        recent_boost = recent_boost.clip(0.7, 1.8)  # Allow bigger range
        df['fppg_projection'] *= recent_boost
        print(f"📈 Applied recency bias to all players")
    
    # 4. MATCHUP BONUSES
    # Against bad pitchers (ERA > 4.5)
    if 'opp_pitcher_era' in df.columns:
        bad_pitcher_mask = df['opp_pitcher_era'] > 4.5
        df.loc[bad_pitcher_mask, 'fppg_projection'] *= 1.20
        count = bad_pitcher_mask.sum()
        print(f"💪 Applied 1.20x bonus to {count} players vs bad pitching")
    
    # High total games (Over 8.5 runs)
    if 'game_total' in df.columns:
        high_total_mask = df['game_total'] > 8.5
        df.loc[high_total_mask, 'fppg_projection'] *= 1.15
        count = high_total_mask.sum()
        print(f"🚀 Applied 1.15x bonus to {count} players in high-total games")
    
    # 5. SALARY EFFICIENCY BOOST
    # Boost mid-tier guys who provide value
    if 'salary' in df.columns:
        # Sweet spot players ($3000-$4500 hitters, $7000-$9500 pitchers)
        hitter_mask = (~df['position'].isin(['P'])) & (df['salary'].between(3000, 4500))
        pitcher_mask = (df['position'] == 'P') & (df['salary'].between(7000, 9500))
        
        df.loc[hitter_mask, 'fppg_projection'] *= 1.10
        df.loc[pitcher_mask, 'fppg_projection'] *= 1.10
        
        hitter_count = hitter_mask.sum()
        pitcher_count = pitcher_mask.sum()
        print(f"💰 Applied value bonus to {hitter_count} hitters, {pitcher_count} pitchers")
    
    return df

# INTEGRATION CODE for your existing scripts:
integration_code = '''
# ADD THIS TO YOUR MAIN PROJECTION SCRIPT:

# After you load your projections dataframe:
df = apply_emergency_fixes(df)

# Your existing optimization code here...
'''

print("🚨 EMERGENCY FIXES READY!")
print("="*50)
print("Copy the apply_emergency_fixes() function into your main projection script")
print("Apply it RIGHT BEFORE you run your lineup optimizer")
print("This should immediately improve your player selection")

if __name__ == "__main__":
    print("Emergency fixes code generated - integrate into your system!")
