#!/usr/bin/env python3
"""
BLIND AUGUST 13TH LINEUP GENERATION
Generate lineups using our enhanced system WITHOUT looking at actual results
"""

import pandas as pd
import numpy as np
from datetime import datetime

def generate_blind_aug13_lineups():
    """Generate August 13th lineups using enhanced system, then test against results"""
    
    print("TARGET: BLIND AUGUST 13TH LINEUP GENERATION")
    print("=" * 50)
    print("Using enhanced aggressive system WITHOUT looking at actual scores...")
    
    try:
        # Load August 13th enhanced projections (our base data)
        df_projections = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        print(f"SUCCESS: Loaded Aug 13th projections: {len(df_projections)} players")
        
        # Apply our enhanced aggressive system
        df_enhanced = apply_enhanced_system_blind(df_projections)
        
        # Generate multiple lineup strategies
        lineups = generate_multiple_strategies(df_enhanced)
        
        # NOW test against actual results
        print(f"\nDATA: TESTING AGAINST ACTUAL RESULTS")
        print("=" * 40)
        test_lineups_against_actual(lineups)
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

def apply_enhanced_system_blind(df):
    """Apply our enhanced aggressive system to August 13th data"""
    
    print(f"\nSTART: APPLYING ENHANCED AGGRESSIVE SYSTEM")
    print("=" * 45)
    
    df_enhanced = df.copy()
    
    # Use enhanced_fppg as base projection
    df_enhanced['base_projection'] = df_enhanced['enhanced_fppg'].fillna(df_enhanced['FPPG'])
    df_enhanced['aggressive_projection'] = df_enhanced['base_projection'].copy()
    
    # Simulate ownership based on salary
    df_enhanced['simulated_ownership'] = simulate_ownership_blind(df_enhanced)
    
    nuclear_targets = []
    
    # Apply aggressive boosts to value players
    value_players = df_enhanced[
        (df_enhanced['Salary'] <= 3500) & 
        (df_enhanced['Position'] != 'P') &
        (df_enhanced['Batting Order'] > 0)  # Starting players only
    ].copy()
    
    print(f" Analyzing {len(value_players)} value players ($3,500)...")
    
    for idx, player in value_players.iterrows():
        original_proj = player['base_projection']
        
        # Calculate aggressive multiplier
        multiplier = 1.0
        
        # Salary-based boost
        if player['Salary'] <= 2500:
            multiplier += 0.6  # 60% boost for min salary
        elif player['Salary'] <= 3000:
            multiplier += 0.4  # 40% boost
        elif player['Salary'] <= 3500:
            multiplier += 0.2  # 20% boost
        
        # Position-based boost
        if player['Position'] in ['OF', 'SS', '2B']:
            multiplier += 0.1  # Speed positions
        
        # Batting order boost
        if player['Batting Order'] <= 3:
            multiplier += 0.15  # Top of order
        elif player['Batting Order'] <= 5:
            multiplier += 0.1   # Heart of order
        
        # Low ownership boost
        if player['simulated_ownership'] < 5:
            multiplier += 0.2  # Contrarian boost
        
        # Apply multiplier
        enhanced_proj = original_proj * multiplier
        df_enhanced.at[idx, 'aggressive_projection'] = enhanced_proj
        
        if enhanced_proj >= 25:  # Nuclear threshold
            nuclear_targets.append({
                'name': f"{player['Nickname']} {player['Last Name']}",
                'team': player['Team'],
                'position': player['Position'],
                'salary': player['Salary'],
                'original_proj': original_proj,
                'aggressive_proj': enhanced_proj,
                'multiplier': multiplier,
                'ownership': player['simulated_ownership']
            })
    
    # Apply value pitcher boosts
    value_pitchers = df_enhanced[
        (df_enhanced['Position'] == 'P') &
        (df_enhanced['Probable Pitcher'] == 'Yes') &
        (df_enhanced['Salary'] >= 6000) &
        (df_enhanced['Salary'] <= 10000)
    ].copy()
    
    for idx, pitcher in value_pitchers.iterrows():
        original_proj = pitcher['base_projection']
        enhanced_proj = original_proj * 1.15  # 15% value pitcher boost
        df_enhanced.at[idx, 'aggressive_projection'] = enhanced_proj
    
    # Display nuclear targets found
    nuclear_targets.sort(key=lambda x: x['aggressive_proj'], reverse=True)
    
    print(f"\n NUCLEAR VALUE TARGETS FOUND (25 pts projected):")
    for target in nuclear_targets[:10]:  # Top 10
        print(f"   {target['name']} ({target['team']}) - {target['position']}")
        print(f"      ${target['salary']} (~{target['ownership']:.1f}% owned)")
        print(f"      {target['original_proj']:.1f}  {target['aggressive_proj']:.1f} pts (x{target['multiplier']:.2f})")
    
    print(f"\nTIP: Found {len(nuclear_targets)} total nuclear targets")
    
    return df_enhanced

def simulate_ownership_blind(df):
    """Simulate ownership without looking at results"""
    
    ownership = []
    for _, player in df.iterrows():
        salary = player['Salary']
        
        # Lower salary generally = lower ownership
        if salary <= 2500:
            own = np.random.uniform(1, 5)
        elif salary <= 3000:
            own = np.random.uniform(3, 8)
        elif salary <= 3500:
            own = np.random.uniform(5, 12)
        elif salary <= 4000:
            own = np.random.uniform(8, 18)
        else:
            own = np.random.uniform(15, 35)
        
        ownership.append(round(own, 1))
    
    return ownership

def generate_multiple_strategies(df_enhanced):
    """Generate multiple lineup strategies"""
    
    print(f"\n GENERATING MULTIPLE LINEUP STRATEGIES")
    print("=" * 45)
    
    # Filter to starting players
    probable_pitchers = df_enhanced[
        (df_enhanced['Position'] == 'P') & 
        (df_enhanced['Probable Pitcher'] == 'Yes')
    ].copy()
    
    starting_hitters = df_enhanced[
        (df_enhanced['Position'] != 'P') & 
        (df_enhanced['Batting Order'] > 0)
    ].copy()
    
    print(f"SUCCESS: Available: {len(probable_pitchers)} pitchers, {len(starting_hitters)} hitters")
    
    strategies = [
        ("Nuclear Value Hunt", build_nuclear_lineup_blind),
        ("Miami Stack Attack", build_miami_stack_blind),
        ("Value Pitcher Special", build_value_pitcher_blind),
        ("Contrarian Crusher", build_contrarian_blind)
    ]
    
    lineups = []
    for strategy_name, build_func in strategies:
        print(f"\nTARGET: Building: {strategy_name}")
        lineup = build_func(probable_pitchers, starting_hitters)
        if lineup:
            lineups.append((strategy_name, lineup))
            display_lineup_blind(strategy_name, lineup)
        else:
            print(f"ERROR: Could not build {strategy_name}")
    
    return lineups

def build_nuclear_lineup_blind(pitchers, hitters):
    """Build nuclear value focused lineup"""
    
    # Get best value pitcher
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000)
    ].sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with value pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Fill with nuclear value hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions:
        best_player = find_best_nuclear_for_position(pos, hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def build_miami_stack_blind(pitchers, hitters):
    """Build Miami stack lineup (based on projections showing MIA strength)"""
    
    # Get non-Miami value pitcher
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000) &
        (pitchers['Team'] != 'MIA')
    ].sort_values('aggressive_projection', ascending=False)
    
    if len(value_pitchers) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Prioritize Miami players
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    miami_players = hitters[hitters['Team'] == 'MIA'].sort_values('aggressive_projection', ascending=False)
    
    for pos in positions:
        # Try Miami first
        miami_option = find_player_for_position(pos, miami_players, remaining_salary, used_players)
        if miami_option is not None:
            best_player = miami_option
        else:
            # Fall back to any team
            best_player = find_best_nuclear_for_position(pos, hitters, remaining_salary, used_players)
        
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def build_value_pitcher_blind(pitchers, hitters):
    """Build lineup with cheapest viable pitcher for max hitter salary"""
    
    # Get cheapest probable pitcher
    cheap_pitchers = pitchers.sort_values('Salary', ascending=True)
    
    if len(cheap_pitchers) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with cheap pitcher
    pitcher = cheap_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Fill with best available hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions:
        best_player = find_best_nuclear_for_position(pos, hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def build_contrarian_blind(pitchers, hitters):
    """Build contrarian lineup with low ownership focus"""
    
    # Get low ownership pitcher
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] <= 10000)
    ].sort_values(['simulated_ownership', 'aggressive_projection'], ascending=[True, False])
    
    if len(value_pitchers) == 0:
        return None
    
    lineup = []
    remaining_salary = 35000
    used_players = set()
    
    # Start with contrarian pitcher
    pitcher = value_pitchers.iloc[0]
    lineup.append(('P', pitcher))
    remaining_salary -= pitcher['Salary']
    used_players.add(pitcher['Id'])
    
    # Fill with contrarian hitters
    positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions:
        best_player = find_best_contrarian_for_position(pos, hitters, remaining_salary, used_players)
        if best_player is not None:
            lineup.append((pos, best_player))
            remaining_salary -= best_player['Salary']
            used_players.add(best_player['Id'])
    
    return lineup if len(lineup) == 9 else None

def find_best_nuclear_for_position(position, players, max_salary, used_players):
    """Find best nuclear value player for position"""
    
    eligible = get_eligible_for_position(position, players)
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    # Sort by aggressive projection
    return available.nlargest(1, 'aggressive_projection').iloc[0]

def find_best_contrarian_for_position(position, players, max_salary, used_players):
    """Find best contrarian player for position"""
    
    eligible = get_eligible_for_position(position, players)
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    # Sort by low ownership + high projection
    available = available.copy()
    available['contrarian_score'] = available['aggressive_projection'] / (available['simulated_ownership'] + 1)
    return available.nlargest(1, 'contrarian_score').iloc[0]

def find_player_for_position(position, players, max_salary, used_players):
    """Find any player for position from specific pool"""
    
    eligible = get_eligible_for_position(position, players)
    available = eligible[
        (eligible['Salary'] <= max_salary) &
        (~eligible['Id'].isin(used_players))
    ]
    
    if len(available) == 0:
        return None
    
    return available.nlargest(1, 'aggressive_projection').iloc[0]

def get_eligible_for_position(position, players):
    """Get eligible players for position"""
    
    if position == 'C':
        return players[players['Position'].str.contains('C', na=False)]
    elif position in ['1B', '2B', '3B', 'SS']:
        return players[players['Position'].str.contains(position, na=False)]
    elif position == 'OF':
        return players[players['Position'].str.contains('OF', na=False)]
    else:
        return players

def display_lineup_blind(strategy_name, lineup):
    """Display lineup without actual results"""
    
    total_salary = sum(player['Salary'] for _, player in lineup)
    total_projection = sum(player['aggressive_projection'] for _, player in lineup)
    
    print(f"  MONEY: Salary: ${total_salary:,} (${35000-total_salary:,} remaining)")
    print(f"  TARGET: Projection: {total_projection:.1f} points")
    
    for pos, player in lineup:
        proj = player['aggressive_projection']
        ownership = player.get('simulated_ownership', 10)
        print(f"    {pos}: {player['Nickname']} {player['Last Name']} ({player['Team']}) - "
              f"${player['Salary']} - {proj:.1f} pts (~{ownership:.1f}% owned)")

def test_lineups_against_actual(lineups):
    """Test our blind lineups against actual August 13th results"""
    
    try:
        # Load actual results
        df_results = pd.read_csv("../data/actual_results_latest.csv")
        df_aug13 = df_results[df_results['date'] == '2025-08-13'].copy()
        
        print(f"SUCCESS: Loaded actual August 13th results: {len(df_aug13)} players")
        
        # Create lookup for actual points by name (more reliable than player_id)
        actual_lookup = {}
        for _, player in df_aug13.iterrows():
            # Use name as key
            name_key = player['name'].lower().replace(' ', '').replace('.', '')
            actual_lookup[name_key] = player['fanduel_points']
        
        print(f"\nLINEUP: LINEUP PERFORMANCE RESULTS:")
        print("=" * 40)
        
        for strategy_name, lineup in lineups:
            print(f"\nTARGET: {strategy_name.upper()}:")
            print("-" * 30)
            
            total_salary = 0
            total_projected = 0
            total_actual = 0
            lineup_details = []
            
            for pos, player in lineup:
                salary = player['Salary']
                projected = player['aggressive_projection']
                
                # Try to match by name
                player_name = f"{player['Nickname']} {player['Last Name']}".lower().replace(' ', '').replace('.', '')
                actual = actual_lookup.get(player_name, 0)
                
                # Also try just last name
                if actual == 0:
                    last_name_key = player['Last Name'].lower().replace(' ', '').replace('.', '')
                    for key, points in actual_lookup.items():
                        if last_name_key in key:
                            actual = points
                            break
                
                total_salary += salary
                total_projected += projected
                total_actual += actual
                
                lineup_details.append((pos, player, projected, actual))
            
            # Display results
            print(f"Salary: ${total_salary:,}")
            print(f"Projected: {total_projected:.1f} points")
            print(f"ACTUAL: {total_actual:.1f} points")
            
            if total_actual > 0:
                accuracy = (total_projected/total_actual*100)
                print(f"Accuracy: {accuracy:.1f}%")
            else:
                print(f"Accuracy: No matches found")
            
            # Performance assessment
            winning_score = 271.6
            if total_actual >= winning_score:
                print(f"LINEUP: WOULD HAVE WON! (Winner: {winning_score})")
            elif total_actual >= 200:
                print(f"MONEY: Would have cashed BIG!")
            elif total_actual >= 150:
                print(f" Would have min-cashed")
            else:
                print(f"ERROR: Would not have cashed ({total_actual:.1f} pts)")
            
            # Show all players with actual scores
            print(f"\nFull lineup results:")
            for pos, player, proj, actual in lineup_details:
                status = "SUCCESS:" if actual > 0 else ""
                print(f"  {status} {pos}: {player['Nickname']} {player['Last Name']} ({player['Team']}) - "
                      f"${player['Salary']} - Proj: {proj:.1f}, Actual: {actual:.1f}")
        
        # Also show what big scores we missed
        print(f"\n BIG SCORES WE MISSED:")
        big_scores = df_aug13[df_aug13['fanduel_points'] >= 30].sort_values('fanduel_points', ascending=False)
        for _, player in big_scores.head(10).iterrows():
            print(f"   {player['name']} ({player['team']}) - {player['fanduel_points']:.1f} pts")
        
    except Exception as e:
        print(f"ERROR: Error testing lineups: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    generate_blind_aug13_lineups()
