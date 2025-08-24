#!/usr/bin/env python3
"""
FIXED SMART DFS LINEUP BUILDER
==============================
Build tournament lineups using proper budget allocation.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class FixedSmartDFSBuilder:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_viable_slate(self):
        """Load slate with smart filtering applied"""
        print("🧠 FIXED SMART DFS LINEUP BUILDER")
        print("Building lineups with proper budget allocation")
        print("="*60)
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        df = pd.read_csv(slate_file)
        
        print(f"📊 Raw slate: {len(df)} players")
        
        # Filter injured players
        df_healthy = df[df['Injury Indicator'].isna()].copy()
        print(f"✅ Healthy players: {len(df_healthy)}")
        
        # Filter to probable pitchers only
        pitchers = df_healthy[
            (df_healthy['Position'] == 'P') &
            (df_healthy['Probable Pitcher'] == 'Yes')
        ].copy()
        
        non_pitchers = df_healthy[df_healthy['Position'] != 'P'].copy()
        
        # Remove players with terrible projections
        pitchers = pitchers[pitchers['FPPG'] > 5.0]
        non_pitchers = non_pitchers[non_pitchers['FPPG'] > 0.1]
        
        viable_slate = pd.concat([pitchers, non_pitchers], ignore_index=True)
        print(f"✅ Viable slate: {len(viable_slate)} players ({len(pitchers)} pitchers, {len(non_pitchers)} hitters)")
        
        return viable_slate
    
    def build_optimized_lineup(self, viable_slate, strategy='balanced'):
        """Build single lineup with proper budget allocation"""
        print(f"\n🏗️ Building {strategy} lineup with smart budgeting...")
        
        # Enhanced metrics
        viable_slate = viable_slate.copy()
        viable_slate['value_score'] = viable_slate['FPPG'] / (viable_slate['Salary'] / 1000)
        viable_slate['ceiling_est'] = viable_slate['FPPG'] * np.where(
            viable_slate['Position'] == 'P', 1.5, 1.8
        )
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        # Position requirements in optimal filling order
        position_order = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        # STEP 1: Smart pitcher selection based on strategy
        pitchers = viable_slate[viable_slate['Position'] == 'P']
        
        if strategy == 'punt_pitcher':
            # Use cheap pitcher, maximize hitter salary
            affordable_pitchers = pitchers[pitchers['Salary'] <= 8000]
            if affordable_pitchers.empty:
                affordable_pitchers = pitchers.nsmallest(5, 'Salary')
            chosen_pitcher = affordable_pitchers.loc[affordable_pitchers['value_score'].idxmax()]
        
        elif strategy == 'premium_pitcher':
            # Use expensive pitcher if within budget
            premium_pitchers = pitchers[
                (pitchers['Salary'] >= 8500) & 
                (pitchers['Salary'] <= 12000)
            ]
            if premium_pitchers.empty:
                premium_pitchers = pitchers.nlargest(5, 'FPPG')
            chosen_pitcher = premium_pitchers.loc[premium_pitchers['FPPG'].idxmax()]
        
        else:  # balanced
            # Mid-range pitcher with good value
            balanced_pitchers = pitchers[
                (pitchers['Salary'] >= 7000) & 
                (pitchers['Salary'] <= 9500)
            ]
            if balanced_pitchers.empty:
                balanced_pitchers = pitchers
            # Combine projection and value
            balanced_pitchers['combo_score'] = (
                balanced_pitchers['FPPG'] * 0.6 + 
                balanced_pitchers['value_score'] * 0.4
            )
            chosen_pitcher = balanced_pitchers.loc[balanced_pitchers['combo_score'].idxmax()]
        
        selected_players.append(chosen_pitcher)
        remaining_budget -= chosen_pitcher['Salary']
        used_ids.add(chosen_pitcher['Id'])
        
        print(f"  ⚾ Pitcher: {chosen_pitcher['First Name']} {chosen_pitcher['Last Name']} (${chosen_pitcher['Salary']:,}, {chosen_pitcher['FPPG']:.1f} FPPG)")
        print(f"     Remaining budget: ${remaining_budget:,}")
        
        # STEP 2: Fill hitter positions with smart budget allocation
        remaining_positions = 8  # 8 hitters left
        
        for i, position in enumerate(['C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']):
            positions_left = remaining_positions - i
            
            # Calculate smart budget allocation
            if positions_left > 1:
                # Reserve minimum amount for remaining positions
                min_remaining_budget = (positions_left - 1) * 2000
                max_spend = remaining_budget - min_remaining_budget
                # But don't go below reasonable minimum
                max_spend = max(max_spend, 2000)
            else:
                # Last position gets all remaining budget
                max_spend = remaining_budget
            
            # Get candidates for this position
            if position == 'UTIL':
                candidates = viable_slate[
                    (~viable_slate['Id'].isin(used_ids)) &
                    (viable_slate['Position'] != 'P')
                ]
            elif position == 'C/1B':
                candidates = viable_slate[
                    (viable_slate['Roster Position'].str.contains('C|1B', na=False)) &
                    (~viable_slate['Id'].isin(used_ids))
                ]
            else:
                candidates = viable_slate[
                    (viable_slate['Roster Position'].str.contains(position, na=False)) &
                    (~viable_slate['Id'].isin(used_ids))
                ]
            
            # Filter by budget
            affordable = candidates[
                (candidates['Salary'] <= max_spend) &
                (candidates['Salary'] >= 2000)
            ]
            
            if affordable.empty:
                print(f"  ❌ No affordable {position} (budget: ${max_spend:,})")
                return None
            
            # Select best player within budget
            if strategy == 'ceiling':
                selection_metric = 'ceiling_est'
            elif strategy == 'value':
                selection_metric = 'value_score'
            else:  # balanced
                affordable['balanced_score'] = (
                    affordable['FPPG'] * 0.5 + 
                    affordable['value_score'] * 0.3 +
                    affordable['ceiling_est'] * 0.2
                )
                selection_metric = 'balanced_score'
            
            chosen = affordable.loc[affordable[selection_metric].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
            
            print(f"  👤 {position}: {chosen['First Name']} {chosen['Last Name']} (${chosen['Salary']:,}, {chosen['FPPG']:.1f} FPPG) - ${remaining_budget:,} left")
        
        # Calculate lineup totals
        total_salary = sum(p['Salary'] for p in selected_players)
        total_projected = sum(p['FPPG'] for p in selected_players)
        total_ceiling = sum(p['ceiling_est'] for p in selected_players)
        
        return {
            'players': selected_players,
            'strategy': strategy,
            'total_salary': total_salary,
            'total_projected': total_projected,
            'total_ceiling': total_ceiling
        }
    
    def generate_tournament_lineups(self, viable_slate, count=12):
        """Generate diverse tournament lineups"""
        print(f"\n🎯 GENERATING {count} TOURNAMENT LINEUPS")
        print("="*50)
        
        # Different strategies for diversity
        strategies = [
            'punt_pitcher',     # Cheap pitcher, expensive hitters
            'premium_pitcher',  # Expensive pitcher, value hitters  
            'balanced',         # Balanced approach
            'ceiling',          # High ceiling focus
            'value',           # High value focus
        ]
        
        lineups = []
        strategy_counts = {}
        
        for i in range(count):
            # Cycle through strategies with variations
            base_strategy = strategies[i % len(strategies)]
            strategy_counts[base_strategy] = strategy_counts.get(base_strategy, 0) + 1
            
            # Add variation suffix
            if strategy_counts[base_strategy] > 1:
                strategy_name = f"{base_strategy}_v{strategy_counts[base_strategy]}"
            else:
                strategy_name = base_strategy
            
            lineup = self.build_optimized_lineup(viable_slate, base_strategy)
            
            if lineup:
                lineup['lineup_id'] = f"TOUR_{i+1:02d}"
                lineup['strategy'] = strategy_name
                lineups.append(lineup)
                
                print(f"✅ {lineup['lineup_id']} ({strategy_name}): ${lineup['total_salary']:,} | {lineup['total_projected']:.1f} proj | {lineup['total_ceiling']:.1f} ceil")
            else:
                print(f"❌ Failed {i+1} ({strategy_name})")
        
        return lineups
    
    def export_lineups(self, lineups):
        """Export lineups in FanDuel format"""
        if not lineups:
            print("❌ No lineups to export")
            return
        
        print(f"\n📄 EXPORTING {len(lineups)} LINEUPS...")
        
        # Prepare FanDuel format
        export_data = []
        
        for lineup in lineups:
            row = {
                'Lineup_ID': lineup['lineup_id'],
                'Strategy': lineup['strategy'],
                'Total_Salary': lineup['total_salary'],
                'Projected_FPPG': lineup['total_projected'],
                'Ceiling_FPPG': lineup['total_ceiling']
            }
            
            # Map players to positions
            positions_filled = {}
            
            for player in lineup['players']:
                name = f"{player['First Name']} {player['Last Name']}"
                
                if player['Position'] == 'P':
                    row['P'] = name
                else:
                    # Fill hitter positions in order
                    roster_pos = player['Roster Position']
                    
                    if 'C' in roster_pos and 'C' not in positions_filled:
                        row['C'] = name
                        positions_filled['C'] = True
                    elif '1B' in roster_pos and '1B' not in positions_filled:
                        row['1B'] = name  
                        positions_filled['1B'] = True
                    elif '2B' in roster_pos and '2B' not in positions_filled:
                        row['2B'] = name
                        positions_filled['2B'] = True
                    elif '3B' in roster_pos and '3B' not in positions_filled:
                        row['3B'] = name
                        positions_filled['3B'] = True
                    elif 'SS' in roster_pos and 'SS' not in positions_filled:
                        row['SS'] = name
                        positions_filled['SS'] = True
                    elif 'OF' in roster_pos:
                        if 'OF' not in positions_filled:
                            row['OF'] = name
                            positions_filled['OF'] = True
                        elif 'OF2' not in positions_filled:
                            row['OF2'] = name
                            positions_filled['OF2'] = True
                        elif 'OF3' not in positions_filled:
                            row['OF3'] = name
                            positions_filled['OF3'] = True
                        else:
                            row['UTIL'] = name
                    else:
                        row['UTIL'] = name
            
            export_data.append(row)
        
        # Save to CSV
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tournament_lineups_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        df = pd.DataFrame(export_data)
        df.to_csv(filepath, index=False)
        
        print(f"✅ Exported to: {filename}")
        
        # Analysis
        projections = [l['total_projected'] for l in lineups]
        ceilings = [l['total_ceiling'] for l in lineups]
        
        print(f"\n🏆 TOURNAMENT PORTFOLIO ANALYSIS:")
        print(f"  📊 Projected: {min(projections):.1f} - {max(projections):.1f} FPPG (avg: {np.mean(projections):.1f})")
        print(f"  🚀 Ceiling: {min(ceilings):.1f} - {max(ceilings):.1f} FPPG (avg: {np.mean(ceilings):.1f})")
        
        # Tournament readiness
        competitive_lineups = sum(1 for c in ceilings if c >= 200)
        elite_lineups = sum(1 for c in ceilings if c >= 220)
        
        print(f"\n🎯 TOURNAMENT COMPETITIVENESS:")
        print(f"  💪 200+ ceiling lineups: {competitive_lineups}/{len(lineups)} ({competitive_lineups/len(lineups)*100:.0f}%)")
        print(f"  ⭐ 220+ ceiling lineups: {elite_lineups}/{len(lineups)} ({elite_lineups/len(lineups)*100:.0f}%)")
        
        if elite_lineups >= len(lineups) * 0.3:
            print(f"  🏆 EXCELLENT: Strong tournament potential!")
        elif competitive_lineups >= len(lineups) * 0.7:
            print(f"  ✅ GOOD: Solid tournament chances")
        else:
            print(f"  ⚠️ FAIR: Room for improvement")
        
        return filepath

def main():
    print("🧠 FIXED SMART DFS BUILDER")
    print("Building tournament lineups with proper budget allocation")
    print("="*70)
    
    builder = FixedSmartDFSBuilder()
    
    try:
        # Load viable players
        viable_slate = builder.load_viable_slate()
        
        if len(viable_slate) < 50:
            print("❌ Not enough viable players")
            return
        
        # Generate lineups
        lineups = builder.generate_tournament_lineups(viable_slate, count=12)
        
        if lineups:
            # Export lineups
            filepath = builder.export_lineups(lineups)
            print(f"\n🎉 SUCCESS: Generated {len(lineups)} tournament lineups!")
            print(f"💡 Strategy: Smart budget allocation, viable players only")
            print(f"🎯 Target: Beat tournament thresholds (200+ FPPG)")
        else:
            print("❌ Failed to generate lineups")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
