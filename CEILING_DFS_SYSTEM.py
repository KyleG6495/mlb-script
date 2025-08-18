#!/usr/bin/env python3
"""
CEILING-FOCUSED DFS SYSTEM
=========================
Target tournament-winning lineups by focusing on ceiling outcomes.
Learned from 301.1 FPPG optimal hindsight analysis.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class CeilingDFSOptimizer:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_slate_data(self):
        """Load current slate for ceiling optimization"""
        print("TARGET: CEILING DFS SYSTEM - Loading slate data...")
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        if not slate_file.exists():
            print("ERROR: No slate file found")
            return None
            
        slate_df = pd.read_csv(slate_file)
        print(f"SUCCESS: Loaded slate with {len(slate_df)} available players")
        
        return slate_df
    
    def apply_injury_filtering(self, slate_df):
        """Apply proven injury filtering"""
        print("STEP: Applying injury/probable pitcher filtering...")
        
        original_count = len(slate_df)
        
        # Remove injured players
        if 'Injury Indicator' in slate_df.columns:
            injured_players = slate_df['Injury Indicator'].notna()
            injured_count = injured_players.sum()
            print(f"  Removing {injured_count} injured players")
            slate_df = slate_df[~injured_players]
        
        # Remove non-probable pitchers
        if 'Probable Pitcher' in slate_df.columns:
            pitchers = slate_df[slate_df['Position'] == 'P']
            non_probable = pitchers['Probable Pitcher'] != 'Yes'
            non_probable_ids = set(pitchers[non_probable]['Id'])
            slate_df = slate_df[~slate_df['Id'].isin(non_probable_ids)]
            probable_count = (pitchers['Probable Pitcher'] == 'Yes').sum()
            print(f"  Keeping only {probable_count} probable pitchers")
        
        filtered_count = len(slate_df)
        print(f"  Filtered: {original_count}  {filtered_count} players ({filtered_count/original_count*100:.1f}% remaining)")
        
        return slate_df
    
    def calculate_ceiling_scores(self, slate_df):
        """Calculate ceiling potential for each player"""
        print("START: Calculating ceiling potential scores...")
        
        slate_df = slate_df.copy()
        
        # Base ceiling calculation
        slate_df['base_ceiling'] = slate_df['FPPG'] * 3.0  # 3x projection as ceiling
        
        # Position-specific ceiling adjustments
        slate_df['position_multiplier'] = 1.0
        
        # Pitchers: Elite pitchers have highest ceilings (like Framber's 55 FPPG)
        pitcher_mask = slate_df['Position'] == 'P'
        slate_df.loc[pitcher_mask & (slate_df['Salary'] >= 9000), 'position_multiplier'] = 1.5  # Elite pitchers
        slate_df.loc[pitcher_mask & (slate_df['Salary'] >= 7000) & (slate_df['Salary'] < 9000), 'position_multiplier'] = 1.3  # Good pitchers
        slate_df.loc[pitcher_mask & (slate_df['Salary'] < 7000), 'position_multiplier'] = 1.1  # Value pitchers
        
        # Hitters: Power positions and superstars
        superstar_salary = slate_df['Salary'] >= 4000  # Like Acuna Jr, Yelich
        power_positions = slate_df['Roster Position'].str.contains('3B|SS|OF', na=False)
        value_ceiling = (slate_df['Salary'] <= 3500) & (slate_df['FPPG'] >= 8.0)  # Like Josh Naylor
        
        slate_df.loc[superstar_salary & power_positions, 'position_multiplier'] = 1.4  # Superstar power
        slate_df.loc[power_positions & ~superstar_salary, 'position_multiplier'] = 1.2  # Regular power
        slate_df.loc[value_ceiling, 'position_multiplier'] = 1.6  # Value ceiling bombs
        
        # Calculate final ceiling score
        slate_df['ceiling_score'] = slate_df['base_ceiling'] * slate_df['position_multiplier']
        
        # Ceiling per dollar (key metric)
        slate_df['ceiling_per_dollar'] = slate_df['ceiling_score'] / slate_df['Salary'] * 1000
        
        print(f"PROGRESS: Ceiling scores range: {slate_df['ceiling_score'].min():.1f} - {slate_df['ceiling_score'].max():.1f}")
        
        return slate_df
    
    def identify_ceiling_plays(self, slate_df):
        """Identify specific ceiling play types"""
        print("TARGET: Identifying ceiling play categories...")
        
        slate_df = slate_df.copy()
        slate_df['ceiling_category'] = 'Standard'
        
        # Elite Pitchers (like Framber Valdez - 55 FPPG)
        elite_pitchers = (
            (slate_df['Position'] == 'P') &
            (slate_df['Salary'] >= 9000) &
            (slate_df['FPPG'] >= 30)
        )
        slate_df.loc[elite_pitchers, 'ceiling_category'] = 'Elite_Pitcher'
        
        # Superstar Hitters (like Acuna Jr - 34+ FPPG)
        superstars = (
            (slate_df['Position'] != 'P') &
            (slate_df['Salary'] >= 4000) &
            (slate_df['FPPG'] >= 12)
        )
        slate_df.loc[superstars, 'ceiling_category'] = 'Superstar_Hitter'
        
        # Value Ceiling Bombs (like Josh Naylor - 30+ FPPG from $3400)
        value_bombs = (
            (slate_df['Position'] != 'P') &
            (slate_df['Salary'] <= 3500) &
            (slate_df['FPPG'] >= 8) &
            (slate_df['ceiling_per_dollar'] >= 15)
        )
        slate_df.loc[value_bombs, 'ceiling_category'] = 'Value_Bomb'
        
        # Power Plays (3B/SS/OF with good ceiling)
        power_plays = (
            (slate_df['Position'] != 'P') &
            (slate_df['Roster Position'].str.contains('3B|SS|OF', na=False)) &
            (slate_df['ceiling_score'] >= 25) &
            (~slate_df['ceiling_category'].isin(['Elite_Pitcher', 'Superstar_Hitter', 'Value_Bomb']))
        )
        slate_df.loc[power_plays, 'ceiling_category'] = 'Power_Play'
        
        # Safe Floor (consistent performers)
        safe_floor = (
            (slate_df['Position'] != 'P') &
            (slate_df['FPPG'] >= 8) &
            (slate_df['Salary'] >= 2500) &
            (~slate_df['ceiling_category'].isin(['Elite_Pitcher', 'Superstar_Hitter', 'Value_Bomb', 'Power_Play']))
        )
        slate_df.loc[safe_floor, 'ceiling_category'] = 'Safe_Floor'
        
        # Print ceiling categories
        category_counts = slate_df['ceiling_category'].value_counts()
        print(" Ceiling Categories:")
        for category, count in category_counts.items():
            print(f"  {category}: {count} players")
        
        return slate_df
    
    def build_ceiling_lineup(self, enhanced_slate):
        """Build lineup targeting ceiling outcomes"""
        print("LINEUP: Building CEILING-FOCUSED lineup...")
        
        # Ceiling lineup strategy: 1 Elite + 2-3 Ceiling + 3-4 Value + 2-3 Floor
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        # 1. SMART PITCHER SELECTION (elite if budget allows, value if not)
        print("  Step 1: Selecting pitcher...")
        pitcher_candidates = enhanced_slate[
            (enhanced_slate['Position'] == 'P') &
            (~enhanced_slate['Id'].isin(used_ids))
        ]
        
        if not pitcher_candidates.empty:
            # Try elite first, but fallback to value if budget tight
            elite_pitchers = pitcher_candidates[
                (pitcher_candidates['ceiling_category'] == 'Elite_Pitcher') &
                (pitcher_candidates['Salary'] <= remaining_budget - 20000)  # Leave $20k for rest
            ]
            
            if not elite_pitchers.empty:
                chosen_pitcher = elite_pitchers.loc[elite_pitchers['ceiling_score'].idxmax()]
                print(f"    Selected ELITE pitcher: {chosen_pitcher['First Name']} {chosen_pitcher['Last Name']} (${chosen_pitcher['Salary']}, {chosen_pitcher['ceiling_score']:.1f} ceiling)")
            else:
                # Fallback to affordable pitcher with good ceiling
                affordable_pitchers = pitcher_candidates[
                    pitcher_candidates['Salary'] <= remaining_budget - 16000  # Leave $16k for rest
                ]
                if not affordable_pitchers.empty:
                    chosen_pitcher = affordable_pitchers.loc[affordable_pitchers['ceiling_per_dollar'].idxmax()]
                    print(f"    Selected VALUE pitcher: {chosen_pitcher['First Name']} {chosen_pitcher['Last Name']} (${chosen_pitcher['Salary']}, {chosen_pitcher['ceiling_score']:.1f} ceiling)")
                else:
                    print("    ERROR: No affordable pitchers")
                    return None
            
            selected_players.append(chosen_pitcher)
            remaining_budget -= chosen_pitcher['Salary']
            used_ids.add(chosen_pitcher['Id'])
            positions_needed.remove('P')
        else:
            print("    ERROR: No pitchers available")
            return None
        
        # 2. TARGET CEILING PLAYS (2-3 players with smart budgeting)
        print("  Step 2: Selecting ceiling plays...")
        ceiling_targets = ['Superstar_Hitter', 'Value_Bomb', 'Power_Play']
        ceiling_count = 0
        max_ceiling = 2  # Reduced from 3 for better budget management
        
        # Sort positions by priority (fill expensive positions first)
        position_priority = ['OF', 'OF', '3B', 'SS', '2B', 'C/1B', 'OF', 'UTIL']
        
        for position in position_priority:
            if ceiling_count >= max_ceiling or position not in positions_needed:
                continue
                
            if position == 'UTIL':
                candidates = enhanced_slate[~enhanced_slate['Id'].isin(used_ids)]
            else:
                candidates = enhanced_slate[
                    (enhanced_slate['Roster Position'].str.contains(position, na=False)) &
                    (~enhanced_slate['Id'].isin(used_ids))
                ]
            
            # Smart budget allocation - leave enough for remaining positions
            positions_left = len(positions_needed) - 1
            min_budget_per_remaining = 2200  # Slightly higher minimum
            max_spend = remaining_budget - (positions_left * min_budget_per_remaining)
            
            # Look for ceiling plays that fit budget
            ceiling_candidates = candidates[
                (candidates['ceiling_category'].isin(ceiling_targets)) &
                (candidates['Salary'] <= max_spend) &
                (candidates['Salary'] >= 2000)  # Minimum salary filter
            ]
            
            if not ceiling_candidates.empty:
                # Balance ceiling score with budget efficiency
                ceiling_candidates['budget_efficiency'] = (
                    ceiling_candidates['ceiling_score'] / ceiling_candidates['Salary'] * 1000
                )
                chosen = ceiling_candidates.loc[ceiling_candidates['budget_efficiency'].idxmax()]
                print(f"    Selected CEILING {chosen['ceiling_category']}: {chosen['First Name']} {chosen['Last Name']} (${chosen['Salary']}, {chosen['ceiling_score']:.1f} ceiling)")
                selected_players.append(chosen)
                remaining_budget -= chosen['Salary']
                used_ids.add(chosen['Id'])
                positions_needed.remove(position)
                ceiling_count += 1
        
        # 3. FILL REMAINING WITH OPTIMAL VALUE
        print("  Step 3: Filling remaining positions with optimal value...")
        for position in positions_needed:
            if position == 'UTIL':
                candidates = enhanced_slate[~enhanced_slate['Id'].isin(used_ids)]
            else:
                candidates = enhanced_slate[
                    (enhanced_slate['Roster Position'].str.contains(position, na=False)) &
                    (~enhanced_slate['Id'].isin(used_ids))
                ]
            
            # Smart budget management for remaining positions
            positions_left = len(positions_needed) - positions_needed.index(position) - 1
            if positions_left > 0:
                min_budget_needed = positions_left * 2000
                max_spend = remaining_budget - min_budget_needed
            else:
                max_spend = remaining_budget  # Last position gets all remaining
            
            affordable = candidates[
                (candidates['Salary'] <= max_spend) &
                (candidates['Salary'] >= 2000)
            ]
            
            if affordable.empty:
                # Emergency fallback - try lower salary minimum
                affordable = candidates[candidates['Salary'] <= max_spend]
                if affordable.empty:
                    print(f"    ERROR: No affordable {position} players (budget: ${max_spend})")
                    return None
            
            # Prioritize value bombs first, then ceiling per dollar
            value_bombs = affordable[affordable['ceiling_category'] == 'Value_Bomb']
            
            if not value_bombs.empty:
                chosen = value_bombs.loc[value_bombs['ceiling_score'].idxmax()]
                category = "VALUE BOMB"
            else:
                # Choose best ceiling per dollar for remaining budget
                chosen = affordable.loc[affordable['ceiling_per_dollar'].idxmax()]
                category = affordable.loc[affordable['ceiling_per_dollar'].idxmax(), 'ceiling_category']
            
            print(f"    Selected {category}: {chosen['First Name']} {chosen['Last Name']} (${chosen['Salary']}, {chosen['ceiling_score']:.1f} ceiling)")
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            total_ceiling = sum(p['ceiling_score'] for p in selected_players)
            
            print(f"\nSUCCESS: CEILING LINEUP BUILT!")
            print(f"  MONEY: Total Salary: ${total_salary:,}")
            print(f"  DATA: Projected FPPG: {total_projected:.1f}")
            print(f"  START: Ceiling FPPG: {total_ceiling:.1f}")
            print(f"  TARGET: Ceiling vs Projected: {total_ceiling/total_projected:.1f}x")
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'total_ceiling': total_ceiling,
                'lineup_type': 'CEILING_FOCUSED'
            }
        
        return None
    
    def export_ceiling_lineup(self, lineup):
        """Export lineup in FanDuel format"""
        if not lineup:
            print("ERROR: No lineup to export")
            return
        
        print(" Exporting ceiling lineup...")
        
        lineup_df = pd.DataFrame({
            'Id': [p['Id'] for p in lineup['players']],
            'Position': [p['Roster Position'] for p in lineup['players']],
            'First Name': [p['First Name'] for p in lineup['players']],
            'Nickname': [p.get('Nickname', '') for p in lineup['players']],
            'Last Name': [p['Last Name'] for p in lineup['players']],
            'FPPG': [p['FPPG'] for p in lineup['players']],
            'Played': [p.get('Played', 0) for p in lineup['players']],
            'Salary': [p['Salary'] for p in lineup['players']],
            'Game': [p.get('Game', '') for p in lineup['players']],
            'Team': [p.get('Team', '') for p in lineup['players']],
            'Opponent': [p.get('Opponent', '') for p in lineup['players']],
            'Injury Indicator': [p.get('Injury Indicator', '') for p in lineup['players']],
            'Injury Details': [p.get('Injury Details', '') for p in lineup['players']],
            'Tier': [p.get('Tier', '') for p in lineup['players']],
            'Roster Position': [p['Roster Position'] for p in lineup['players']],
            'Ceiling Score': [p['ceiling_score'] for p in lineup['players']],
            'Ceiling Category': [p['ceiling_category'] for p in lineup['players']]
        })
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ceiling_dfs_lineup_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        lineup_df.to_csv(filepath, index=False)
        print(f"SUCCESS: Ceiling lineup exported: {filename}")
        
        # Show lineup summary
        print(f"\nLINEUP: CEILING LINEUP SUMMARY:")
        for i, player in enumerate(lineup['players'], 1):
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player['Roster Position']
            salary = player['Salary']
            projected = player['FPPG']
            ceiling = player['ceiling_score']
            category = player['ceiling_category']
            
            print(f"{i:2}. {name:20} ({pos:4}) ${salary:5,} | Proj: {projected:5.1f} | Ceil: {ceiling:5.1f} | {category}")
        
        return filepath
    
    def run_ceiling_optimization(self):
        """Run complete ceiling-focused DFS optimization"""
        print("START: CEILING-FOCUSED DFS OPTIMIZATION")
        print("Building lineups to target 200+ FPPG tournament scores")
        print("="*70)
        
        # Load and filter slate
        slate_df = self.load_slate_data()
        if slate_df is None:
            return
        
        filtered_slate = self.apply_injury_filtering(slate_df)
        enhanced_slate = self.calculate_ceiling_scores(filtered_slate)
        enhanced_slate = self.identify_ceiling_plays(enhanced_slate)
        
        # Build ceiling lineup
        ceiling_lineup = self.build_ceiling_lineup(enhanced_slate)
        
        if ceiling_lineup:
            # Export lineup
            filepath = self.export_ceiling_lineup(ceiling_lineup)
            
            print(f"\nCOMPLETE: CEILING OPTIMIZATION COMPLETE!")
            print(f"TARGET: Target: 200+ FPPG tournament performance")
            print(f"PROGRESS: Ceiling Potential: {ceiling_lineup['total_ceiling']:.1f} FPPG")
            print(f"TIP: Strategy: Elite pitcher + ceiling hitters + value bombs")
            
            if ceiling_lineup['total_ceiling'] >= 200:
                print(f"SUCCESS: EXCELLENT: Lineup has 200+ ceiling potential!")
            elif ceiling_lineup['total_ceiling'] >= 150:
                print(f"WARNING:  GOOD: Solid ceiling lineup")
            else:
                print(f"ERROR: FAIR: May need more ceiling upside")
                
        else:
            print("ERROR: Failed to build ceiling lineup")

def main():
    print("TARGET: CEILING-FOCUSED DFS SYSTEM")
    print("Target tournament-winning scores like the 210+ FPPG leaderboard")
    print("="*70)
    
    optimizer = CeilingDFSOptimizer()
    
    try:
        optimizer.run_ceiling_optimization()
    except Exception as e:
        print(f"Error in ceiling optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
