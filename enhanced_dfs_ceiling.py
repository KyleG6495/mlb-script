#!/usr/bin/env python3
"""
ENHANCED DFS CEILING OPTIMIZER
=============================
Simple ceiling-focused lineup generator that integrates with your existing system.
"""

import pandas as pd
import numpy as np
from datetime import datetime

def load_enhanced_projections():
    """Load enhanced projections for ceiling targeting"""
    try:
        # Load your existing features
        hitters = pd.read_csv("../data/fd_hitter_features_enhanced.csv")
        pitchers = pd.read_csv("../data/fd_pitcher_features_final.csv")
        
        # Apply ceiling adjustments
        if 'ceiling_adjusted_proj' in hitters.columns:
            hitters['enhanced_fppg'] = hitters['ceiling_adjusted_proj']
        else:
            hitters['enhanced_fppg'] = hitters.get('projected_fppg', 10)
        
        return hitters, pitchers
    except Exception as e:
        print(f"Warning: Could not load enhanced features: {e}")
        return None, None

def generate_ceiling_lineups(slate_df, num_lineups=5):
    """Generate ceiling-focused lineups"""
    ceiling_lineups = []
    
    # Load ceiling weights if available
    try:
        weights = pd.read_csv("../data/ceiling_lineup_weights.csv")
        slate_df = slate_df.merge(weights[['Id', 'ceiling_weight', 'tournament_exposure']], 
                                 on='Id', how='left')
        slate_df['ceiling_weight'] = slate_df['ceiling_weight'].fillna(1.0)
        slate_df['tournament_exposure'] = slate_df['tournament_exposure'].fillna(1.0)
    except:
        slate_df['ceiling_weight'] = 1.0
        slate_df['tournament_exposure'] = 1.0
    
    # REALISTIC ceiling projections - ignore problematic ceiling_weight file
    # Use simple 15% boost to base FPPG for tournament upside
    slate_df['ceiling_fppg'] = slate_df['FPPG'] * 1.15  # Simple realistic boost
    
    # Ensure realistic ranges (no MLB player should project over 35 FPPG)
    slate_df['ceiling_fppg'] = slate_df['ceiling_fppg'].clip(upper=35.0)
    
    print(f"Targeting ceiling: Generating {num_lineups} high-upside lineups...")
    print(f"REALISTIC FPPG range: {slate_df['ceiling_fppg'].min():.1f} - {slate_df['ceiling_fppg'].max():.1f}")
    
    for i in range(num_lineups):
        # Add small randomization for diversity
        noise = np.random.normal(1, 0.03, len(slate_df))  # Small variance for lineup diversity
        slate_df['random_ceiling'] = slate_df['ceiling_fppg'] * noise
        
        # Simple greedy selection optimized for ceiling with STRICT salary cap
        lineup = []
        remaining_salary = 35000  # STRICT limit
        positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}  # 9 players total (UTIL is implicit)
        used_players = set()  # Track used players to prevent duplicates
        
        for pos, count in positions_needed.items():
            for _ in range(count):
                # Filter available players for this position
                pos_players = slate_df[
                    (slate_df['Position'].str.contains(pos)) &
                    (slate_df['Salary'] <= remaining_salary) &
                    (~slate_df['Id'].isin(used_players))  # Prevent duplicates
                ]
                
                if len(pos_players) > 0:
                    # Sort by ceiling projection per dollar (value)
                    pos_players['value'] = pos_players['random_ceiling'] / pos_players['Salary'] * 1000
                    selected = pos_players.nlargest(1, 'value').iloc[0]
                    
                    lineup.append({
                        'Name': f"{selected['First Name']} {selected['Last Name']}",
                        'Position': selected['Position'],
                        'Salary': int(selected['Salary']),
                        'FPPG': round(selected['FPPG'], 2),
                        'Ceiling_FPPG': round(selected['ceiling_fppg'], 2),  # Realistic ceiling
                        'Lineup': f"Ceiling_{i+1}"
                    })
                    remaining_salary -= selected['Salary']
                    used_players.add(selected['Id'])  # Mark as used
                else:
                    print(f"Warning: Could not fill {pos} position in lineup {i+1}")
        
        # Only add complete lineups that meet salary cap (should be 9 players)
        if len(lineup) == 9:
            total_salary = sum(p['Salary'] for p in lineup)
            if total_salary <= 35000:
                ceiling_lineups.extend(lineup)
                print(f"✅ Lineup {i+1}: ${total_salary:,} salary, {sum(p['Ceiling_FPPG'] for p in lineup):.1f} ceiling FPPG")
            else:
                print(f"Warning: Lineup {i+1} over salary cap (${total_salary:,}), skipping")
        else:
            print(f"Warning: Incomplete lineup {i+1} (only {len(lineup)} players), skipping")
    
    return pd.DataFrame(ceiling_lineups)

# Main execution
if __name__ == "__main__":
    print("ENHANCED DFS WITH CEILING TARGETING")
    print("=" * 50)
    
    # Load slate
    slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    
    # CRITICAL: Filter for only ACTIVE players who are actually playing
    print(f"DATA: Total players in slate: {len(slate)}")
    
    # Filter out injured players
    active_slate = slate[slate['Injury Indicator'].fillna('') == ''].copy()
    print(f" After removing injured: {len(active_slate)}")
    
    # Filter for players with batting orders (actually starting)
    # Batting order > 0 means they're in the starting lineup
    starting_hitters = active_slate[
        (active_slate['Position'] != 'P') & 
        (pd.to_numeric(active_slate['Batting Order'], errors='coerce') > 0)
    ]
    
    # Keep all probable pitchers (they don't have batting orders)
    probable_pitchers = active_slate[
        (active_slate['Position'] == 'P') & 
        (active_slate['Probable Pitcher'].fillna('').str.lower() == 'yes')
    ]
    
    # Combine starting hitters and probable pitchers
    playing_only = pd.concat([starting_hitters, probable_pitchers], ignore_index=True)
    
    print(f"BASEBALL: Starting hitters: {len(starting_hitters)}")
    print(f" Probable pitchers: {len(probable_pitchers)}")
    print(f"SUCCESS: Total PLAYING players: {len(playing_only)}")
    
    if len(playing_only) < 50:  # Need enough players to build lineups
        print("WARNING: WARNING: Very few confirmed players found")
        print("TIME: This usually means batting orders haven't been posted yet")
        print("TIP: Consider waiting for lineups to be announced")
        print("ERROR: CANNOT generate reliable ceiling lineups without confirmed starters")
        print("ERROR: Enhanced ceiling optimizer requires batting orders to be posted")
        print("SWAP: Please re-run after batting orders are available (usually 2-3 hours before games)")
        exit(1)  # Exit without generating lineups
    
    # Generate ceiling lineups with ONLY confirmed playing players
    ceiling_lineups = generate_ceiling_lineups(playing_only, num_lineups=5)
    
    if len(ceiling_lineups) > 0:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/enhanced_ceiling_lineups_{timestamp}.csv"
        ceiling_lineups.to_csv(output_file, index=False)
        
        print(f"Ceiling lineups saved: {output_file}")
        
        # Show summary
        lineup_summary = ceiling_lineups.groupby('Lineup').agg({
            'Salary': 'sum',
            'FPPG': 'sum', 
            'Ceiling_FPPG': 'sum'
        }).reset_index()
        
        print("Ceiling Lineup Summary:")
        for _, row in lineup_summary.iterrows():
            total_salary = int(row['Salary'])
            total_fppg = round(row['FPPG'], 1)
            ceiling_fppg = round(row['Ceiling_FPPG'], 1)
            
            # Validation check
            status = "SUCCESS:" if total_salary <= 35000 else "ERROR: OVER CAP"
            print(f"   {row['Lineup']}: ${total_salary:,} | {total_fppg} FPPG | {ceiling_fppg} ceiling {status}")
            
        # Overall validation
        valid_lineups = lineup_summary[lineup_summary['Salary'] <= 35000]
        print(f"\nDATA: Generated {len(valid_lineups)} valid ceiling lineups under $35,000 cap")
        
        if len(valid_lineups) > 0:
            avg_ceiling = valid_lineups['Ceiling_FPPG'].mean()
            print(f"TARGET: Average ceiling projection: {avg_ceiling:.1f} FPPG")
    else:
        print("Failed to generate ceiling lineups")
