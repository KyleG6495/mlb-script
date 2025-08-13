#!/usr/bin/env python3
"""
SMART DFS LINEUP BUILDER
=======================
Build tournament lineups using ONLY viable players.
No injured players, only probable pitchers, focus on 210+ FPPG potential.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class SmartDFSBuilder:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_viable_slate(self):
        """Load slate with smart filtering applied"""
        print("🧠 SMART DFS LINEUP BUILDER")
        print("Building lineups with ONLY viable players")
        print("="*60)
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        df = pd.read_csv(slate_file)
        
        print(f"📊 Raw slate: {len(df)} players")
        
        # CRITICAL FILTER 1: Remove ALL injured players
        print(f"\n🏥 INJURY FILTERING:")
        injured_count = df['Injury Indicator'].notna().sum()
        df_healthy = df[df['Injury Indicator'].isna()].copy()
        print(f"  💥 Removed {injured_count} injured players")
        print(f"  ✅ Healthy players remaining: {len(df_healthy)}")
        
        # CRITICAL FILTER 2: Pitchers - ONLY probable starters
        print(f"\n⚾ PITCHER FILTERING:")
        pitchers = df_healthy[df_healthy['Position'] == 'P']
        probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes'].copy()
        non_pitchers = df_healthy[df_healthy['Position'] != 'P'].copy()
        
        print(f"  🎯 Total healthy pitchers: {len(pitchers)}")
        print(f"  ✅ Probable starters: {len(probable_pitchers)}")
        print(f"  ❌ Removed {len(pitchers) - len(probable_pitchers)} non-probable pitchers")
        
        # Combine viable players
        viable_slate = pd.concat([probable_pitchers, non_pitchers], ignore_index=True)
        print(f"\n✅ VIABLE SLATE: {len(viable_slate)} players")
        
        # CRITICAL FILTER 3: Remove players with zero/negative projections
        print(f"\n📈 PROJECTION FILTERING:")
        before_proj = len(viable_slate)
        viable_slate = viable_slate[viable_slate['FPPG'] > 0.1].copy()  # Less aggressive filtering
        removed_proj = before_proj - len(viable_slate)
        print(f"  ❌ Removed {removed_proj} players with bad projections")
        print(f"  ✅ Players with viable projections: {len(viable_slate)}")
        
        return viable_slate
    
    def analyze_game_environments(self, viable_slate):
        """Identify high-scoring game environments for stacking"""
        print(f"\n🎯 GAME ENVIRONMENT ANALYSIS:")
        
        # Calculate total projected points per game
        game_totals = viable_slate.groupby('Game').agg({
            'FPPG': 'sum',
            'Salary': 'count'
        }).rename(columns={'Salary': 'player_count'})
        
        game_totals['avg_projection'] = game_totals['FPPG'] / game_totals['player_count']
        game_totals = game_totals.sort_values('FPPG', ascending=False)
        
        print(f"  🔥 TOP 5 HIGH-SCORING GAMES:")
        for game, data in game_totals.head(5).iterrows():
            print(f"    ⭐ {game:15} | {data['FPPG']:5.1f} total FPPG | {data['avg_projection']:4.1f} avg")
        
        return game_totals
    
    def build_tournament_lineup(self, viable_slate, strategy_config):
        """Build single tournament lineup using smart player selection"""
        
        strategy_name = strategy_config['name']
        pitcher_tier = strategy_config['pitcher_tier']
        stack_focus = strategy_config.get('stack_focus', False)
        value_emphasis = strategy_config.get('value_emphasis', 0.5)
        ceiling_emphasis = strategy_config.get('ceiling_emphasis', 0.3)
        
        print(f"\n🏗️ Building {strategy_name} lineup...")
        
        # Calculate enhanced metrics
        viable_slate = viable_slate.copy()
        viable_slate['value_score'] = viable_slate['FPPG'] / (viable_slate['Salary'] / 1000)
        viable_slate['ceiling_estimate'] = viable_slate['FPPG'] * np.where(
            viable_slate['Position'] == 'P', 1.4, 1.7  # Conservative ceiling multipliers
        )
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        # 1. SELECT PITCHER based on tier strategy
        pitchers = viable_slate[
            (viable_slate['Position'] == 'P') &
            (~viable_slate['Id'].isin(used_ids))
        ]
        
        if pitcher_tier == 'premium':
            # High-salary, high-projection pitcher
            target_pitchers = pitchers[
                (pitchers['Salary'] >= 9000) &
                (pitchers['Salary'] <= remaining_budget - 22000)
            ]
            if target_pitchers.empty:
                target_pitchers = pitchers[pitchers['Salary'] <= remaining_budget - 20000]
            selection_metric = 'FPPG'
        
        elif pitcher_tier == 'value':
            # Mid-range value pitcher
            target_pitchers = pitchers[
                (pitchers['Salary'] >= 7000) &
                (pitchers['Salary'] <= 9500) &
                (pitchers['Salary'] <= remaining_budget - 18000)
            ]
            if target_pitchers.empty:
                target_pitchers = pitchers[pitchers['Salary'] <= remaining_budget - 18000]
            selection_metric = 'value_score'
        
        else:  # 'punt'
            # Low-salary, high-value pitcher
            target_pitchers = pitchers[
                (pitchers['Salary'] <= 8000) &
                (pitchers['Salary'] <= remaining_budget - 16000)
            ]
            if target_pitchers.empty:
                target_pitchers = pitchers[pitchers['Salary'] <= remaining_budget - 16000]
            selection_metric = 'value_score'
        
        if target_pitchers.empty:
            print(f"  ❌ No viable {pitcher_tier} pitchers available")
            return None
        
        chosen_pitcher = target_pitchers.loc[target_pitchers[selection_metric].idxmax()]
        selected_players.append(chosen_pitcher)
        remaining_budget -= chosen_pitcher['Salary']
        used_ids.add(chosen_pitcher['Id'])
        positions_needed.remove('P')
        
        print(f"  ⚾ Pitcher: {chosen_pitcher['First Name']} {chosen_pitcher['Last Name']} (${chosen_pitcher['Salary']}, {chosen_pitcher['FPPG']:.1f} FPPG)")
        
        # 2. FILL HITTER POSITIONS with smart selection
        for position in positions_needed:
            if position == 'UTIL':
                candidates = viable_slate[
                    (~viable_slate['Id'].isin(used_ids)) &
                    (viable_slate['Position'] != 'P')
                ]
            else:
                # Handle position filtering more carefully
                if position == 'C/1B':
                    candidates = viable_slate[
                        (viable_slate['Roster Position'].str.contains('C|1B', na=False)) &
                        (~viable_slate['Id'].isin(used_ids))
                    ]
                else:
                    candidates = viable_slate[
                        (viable_slate['Roster Position'].str.contains(position, na=False)) &
                        (~viable_slate['Id'].isin(used_ids))
                    ]
            
            # Better budget management - ensure we leave enough for remaining positions
            positions_left = len(positions_needed) - positions_needed.index(position) - 1
            if positions_left > 0:
                min_budget_needed = positions_left * 2000  # Min salary per position
                max_spend = remaining_budget - min_budget_needed
            else:
                max_spend = remaining_budget
            
            # Ensure we can afford at least the minimum
            if max_spend < 2000:
                max_spend = remaining_budget  # Emergency: use all remaining budget
            
            affordable = candidates[
                (candidates['Salary'] <= max_spend) &
                (candidates['Salary'] >= 2000)
            ]
            
            if affordable.empty:
                print(f"  ❌ No affordable {position} players (budget: ${max_spend:,}, candidates: {len(candidates)})")
                # Debug: show some candidate prices
                if len(candidates) > 0:
                    print(f"     Cheapest available: ${candidates['Salary'].min():,}")
                    print(f"     Most expensive: ${candidates['Salary'].max():,}")
                return None
            
            # Smart player selection combining value and ceiling
            affordable['selection_score'] = (
                affordable['value_score'] * value_emphasis +
                affordable['ceiling_estimate'] * ceiling_emphasis * 0.1 +  # Scale ceiling
                affordable['FPPG'] * (1 - value_emphasis - ceiling_emphasis)
            )
            
            # Apply stacking bonus if focused on game environment
            if stack_focus and len(selected_players) > 0:
                pitcher_game = selected_players[0]['Game']
                same_game_bonus = np.where(affordable['Game'] == pitcher_game, 0.1, 0)
                affordable['selection_score'] += same_game_bonus
            
            chosen = affordable.loc[affordable['selection_score'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            total_ceiling = sum(p['ceiling_estimate'] for p in selected_players)
            
            return {
                'players': selected_players,
                'strategy': strategy_name,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'total_ceiling': total_ceiling,
                'pitcher_tier': pitcher_tier
            }
        
        print(f"  ❌ Failed to build complete lineup")
        return None
    
    def generate_smart_lineups(self, viable_slate, target_count=15):
        """Generate diverse smart lineups targeting 210+ FPPG"""
        print(f"\n🎯 GENERATING {target_count} SMART TOURNAMENT LINEUPS")
        print("Target: 210+ FPPG tournament scores")
        print("="*60)
        
        # Define diverse strategies
        strategies = [
            # Premium pitcher strategies (high ceiling)
            {
                'name': 'Premium_Ceiling',
                'pitcher_tier': 'premium',
                'value_emphasis': 0.2,
                'ceiling_emphasis': 0.6,
                'stack_focus': False
            },
            {
                'name': 'Premium_Stack',
                'pitcher_tier': 'premium', 
                'value_emphasis': 0.3,
                'ceiling_emphasis': 0.4,
                'stack_focus': True
            },
            {
                'name': 'Premium_Balanced',
                'pitcher_tier': 'premium',
                'value_emphasis': 0.4,
                'ceiling_emphasis': 0.3,
                'stack_focus': False
            },
            # Value pitcher strategies (more salary for hitters)
            {
                'name': 'Value_Ceiling',
                'pitcher_tier': 'value',
                'value_emphasis': 0.2,
                'ceiling_emphasis': 0.6,
                'stack_focus': False
            },
            {
                'name': 'Value_Stack',
                'pitcher_tier': 'value',
                'value_emphasis': 0.3,
                'ceiling_emphasis': 0.4,
                'stack_focus': True
            },
            {
                'name': 'Value_Balanced',
                'pitcher_tier': 'value',
                'value_emphasis': 0.4,
                'ceiling_emphasis': 0.3,
                'stack_focus': False
            },
            # Punt pitcher strategies (maximum salary for hitters)
            {
                'name': 'Punt_Superstar',
                'pitcher_tier': 'punt',
                'value_emphasis': 0.1,
                'ceiling_emphasis': 0.7,
                'stack_focus': False
            },
            {
                'name': 'Punt_Stack',
                'pitcher_tier': 'punt',
                'value_emphasis': 0.3,
                'ceiling_emphasis': 0.4,
                'stack_focus': True
            },
            {
                'name': 'Punt_Value',
                'pitcher_tier': 'punt',
                'value_emphasis': 0.5,
                'ceiling_emphasis': 0.2,
                'stack_focus': False
            }
        ]
        
        lineups = []
        strategy_index = 0
        
        for i in range(target_count):
            strategy = strategies[strategy_index % len(strategies)]
            
            # Add randomization for more diversity
            if i >= len(strategies):
                strategy = strategy.copy()
                strategy['value_emphasis'] += np.random.uniform(-0.1, 0.1)
                strategy['ceiling_emphasis'] += np.random.uniform(-0.1, 0.1)
                strategy['name'] += f"_Var{i-len(strategies)+1}"
            
            lineup = self.build_tournament_lineup(viable_slate, strategy)
            
            if lineup:
                lineup['lineup_id'] = f"SMART_{i+1}"
                lineups.append(lineup)
                print(f"  ✅ {lineup['lineup_id']} ({lineup['strategy']}): ${lineup['total_salary']:,} | Proj: {lineup['total_projected']:.1f} | Ceil: {lineup['total_ceiling']:.1f}")
            else:
                print(f"  ❌ Failed lineup {i+1} ({strategy['name']})")
            
            strategy_index += 1
        
        print(f"\n📊 Generated {len(lineups)} smart lineups")
        return lineups
    
    def export_smart_lineups(self, lineups):
        """Export smart lineups for tournament submission"""
        if not lineups:
            print("❌ No lineups to export")
            return
        
        print(f"\n📄 EXPORTING SMART TOURNAMENT LINEUPS...")
        
        # Create lineup data for FanDuel submission
        lineup_rows = []
        
        for lineup in lineups:
            row = {}
            
            # Extract player names by position
            for player in lineup['players']:
                pos = player['Position']
                if pos == 'P':
                    row['P'] = f"{player['First Name']} {player['Last Name']}"
                else:
                    # Find first available hitter position
                    roster_pos = player['Roster Position']
                    if 'C' in roster_pos and 'C' not in row:
                        row['C'] = f"{player['First Name']} {player['Last Name']}"
                    elif '1B' in roster_pos and '1B' not in row:
                        row['1B'] = f"{player['First Name']} {player['Last Name']}"
                    elif '2B' in roster_pos and '2B' not in row:
                        row['2B'] = f"{player['First Name']} {player['Last Name']}"
                    elif '3B' in roster_pos and '3B' not in row:
                        row['3B'] = f"{player['First Name']} {player['Last Name']}"
                    elif 'SS' in roster_pos and 'SS' not in row:
                        row['SS'] = f"{player['First Name']} {player['Last Name']}"
                    elif 'OF' in roster_pos:
                        if 'OF' not in row:
                            row['OF'] = f"{player['First Name']} {player['Last Name']}"
                        elif 'OF2' not in row:
                            row['OF2'] = f"{player['First Name']} {player['Last Name']}"
                        elif 'OF3' not in row:
                            row['OF3'] = f"{player['First Name']} {player['Last Name']}"
                        else:
                            row['UTIL'] = f"{player['First Name']} {player['Last Name']}"
                    else:
                        row['UTIL'] = f"{player['First Name']} {player['Last Name']}"
            
            # Add lineup metadata
            row['Lineup_ID'] = lineup['lineup_id']
            row['Strategy'] = lineup['strategy']
            row['Total_Salary'] = lineup['total_salary']
            row['Projected_FPPG'] = lineup['total_projected']
            row['Ceiling_FPPG'] = lineup['total_ceiling']
            row['Pitcher_Tier'] = lineup['pitcher_tier']
            
            lineup_rows.append(row)
        
        # Save to CSV
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_tournament_lineups_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        lineup_df = pd.DataFrame(lineup_rows)
        lineup_df.to_csv(filepath, index=False)
        
        print(f"✅ Smart lineups exported: {filename}")
        
        # Portfolio analysis
        projections = [l['total_projected'] for l in lineups]
        ceilings = [l['total_ceiling'] for l in lineups]
        
        print(f"\n🏆 SMART PORTFOLIO ANALYSIS:")
        print(f"  📊 Projected Range: {min(projections):.1f} - {max(projections):.1f} FPPG")
        print(f"  🚀 Ceiling Range: {min(ceilings):.1f} - {max(ceilings):.1f} FPPG")
        print(f"  📈 Average Projected: {np.mean(projections):.1f} FPPG")
        print(f"  🎯 Average Ceiling: {np.mean(ceilings):.1f} FPPG")
        
        # Tournament competitiveness
        target_ceiling = 210
        competitive_lineups = sum(1 for c in ceilings if c >= target_ceiling)
        
        print(f"\n🏆 TOURNAMENT COMPETITIVENESS:")
        print(f"  🎯 Lineups with 210+ ceiling: {competitive_lineups}/{len(lineups)} ({competitive_lineups/len(lineups)*100:.1f}%)")
        
        if competitive_lineups >= len(lineups) * 0.6:
            print(f"  ✅ EXCELLENT: Strong tournament potential!")
        elif competitive_lineups >= len(lineups) * 0.4:
            print(f"  ⚠️ GOOD: Decent tournament chances")
        else:
            print(f"  🔧 FAIR: May need more ceiling optimization")
        
        # Best lineups
        print(f"\n🌟 TOP 5 SMART LINEUPS:")
        sorted_lineups = sorted(lineups, key=lambda x: x['total_ceiling'], reverse=True)
        
        for i, lineup in enumerate(sorted_lineups[:5], 1):
            efficiency = lineup['total_ceiling'] / lineup['total_projected']
            print(f"  {i}. {lineup['lineup_id']} ({lineup['strategy']}): {lineup['total_projected']:.1f} proj, {lineup['total_ceiling']:.1f} ceil, {efficiency:.1f}x upside")
        
        return filepath
    
    def run_smart_optimization(self):
        """Run complete smart DFS optimization"""
        print("🧠 SMART DFS LINEUP BUILDER")
        print("Building lineups targeting 210+ FPPG with ONLY viable players")
        print("="*80)
        
        # Load viable slate
        viable_slate = self.load_viable_slate()
        
        if len(viable_slate) < 100:
            print("❌ Not enough viable players for optimization")
            return
        
        # Analyze game environments
        game_analysis = self.analyze_game_environments(viable_slate)
        
        # Generate smart lineups
        lineups = self.generate_smart_lineups(viable_slate, target_count=15)
        
        if lineups:
            # Export lineups
            filepath = self.export_smart_lineups(lineups)
            
            print(f"\n🎉 SMART OPTIMIZATION COMPLETE!")
            print(f"🎯 Generated {len(lineups)} smart tournament lineups")
            print(f"💡 Strategy: ONLY viable players, diverse approaches")
            print(f"🏆 Target: Beat 210+ FPPG tournament threshold")
            print(f"✅ Ready for submission!")
            
        else:
            print("❌ Failed to generate smart lineups")

def main():
    print("🧠 SMART DFS LINEUP BUILDER")
    print("Building tournament lineups with ONLY viable players")
    print("="*70)
    
    builder = SmartDFSBuilder()
    
    try:
        builder.run_smart_optimization()
    except Exception as e:
        print(f"Error in smart optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
