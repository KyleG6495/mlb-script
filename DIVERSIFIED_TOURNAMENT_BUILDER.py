#!/usr/bin/env python3
"""
DIVERSIFIED TOURNAMENT BUILDER
=============================
Build diverse tournament lineups exploring multiple team stacks.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
import random
warnings.filterwarnings('ignore')

class DiversifiedTournamentBuilder:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_viable_slate(self):
        """Load slate with filtering for tournament play"""
        print("TARGET: DIVERSIFIED TOURNAMENT BUILDER")
        print("Building diverse lineups with multiple team stacks")
        print("="*70)
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        df = pd.read_csv(slate_file)
        
        # Filter viable players
        viable = df[
            (df['Injury Indicator'].isna()) &
            (df['FPPG'] > 0.1)
        ].copy()
        
        # Get probable pitchers
        pitchers = viable[
            (viable['Position'] == 'P') &
            (viable['Probable Pitcher'] == 'Yes') &
            (viable['FPPG'] >= 15.0)
        ].copy()
        
        hitters = viable[viable['Position'] != 'P'].copy()
        
        slate = pd.concat([pitchers, hitters], ignore_index=True)
        print(f"SUCCESS: Tournament slate: {len(slate)} players ({len(pitchers)} pitchers, {len(hitters)} hitters)")
        
        return slate
    
    def analyze_stacking_options(self, slate):
        """Analyze all possible team stacking options"""
        print(f"\nTARGET: TEAM STACKING ANALYSIS:")
        
        hitters = slate[slate['Position'] != 'P']
        
        # Calculate team metrics
        team_analysis = hitters.groupby('Team').agg({
            'FPPG': ['sum', 'mean', 'count'],
            'Salary': ['sum', 'mean'],
            'Id': 'count'
        }).round(1)
        
        team_analysis.columns = ['total_proj', 'avg_proj', 'proj_count', 'total_sal', 'avg_sal', 'player_count']
        
        # Filter teams with enough players for stacking
        stackable_teams = team_analysis[team_analysis['player_count'] >= 3].copy()
        stackable_teams['stack_value'] = stackable_teams['total_proj'] / (stackable_teams['total_sal'] / 1000)
        stackable_teams['stack_ceiling'] = stackable_teams['total_proj'] * 1.6
        
        stackable_teams = stackable_teams.sort_values('total_proj', ascending=False)
        
        print(f"   TOP 10 STACKING TARGETS:")
        for team, data in stackable_teams.head(10).iterrows():
            print(f"     {team:4} | {data['total_proj']:5.1f} proj | {data['avg_proj']:4.1f} avg | {data['player_count']:2.0f} players | {data['stack_value']:4.1f} val")
        
        return stackable_teams
    
    def build_team_stack_lineup(self, slate, target_team, pitcher_strategy='balanced'):
        """Build lineup around specific team stack"""
        
        # Enhanced metrics
        slate = slate.copy()
        slate['value_score'] = slate['FPPG'] / (slate['Salary'] / 1000)
        slate['ceiling_est'] = slate['FPPG'] * np.where(slate['Position'] == 'P', 1.5, 1.8)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        # STEP 1: Select pitcher (different team from stack)
        pitchers = slate[
            (slate['Position'] == 'P') &
            (slate['Team'] != target_team)
        ]
        
        if pitchers.empty:
            # If forced to use same team pitcher, allow it
            pitchers = slate[slate['Position'] == 'P']
        
        if pitcher_strategy == 'premium':
            affordable_pitchers = pitchers[pitchers['Salary'] <= 11000]
            if affordable_pitchers.empty:
                affordable_pitchers = pitchers
            chosen_pitcher = affordable_pitchers.loc[affordable_pitchers['FPPG'].idxmax()]
        elif pitcher_strategy == 'value':
            affordable_pitchers = pitchers[pitchers['Salary'] <= 8500]
            if affordable_pitchers.empty:
                affordable_pitchers = pitchers.nsmallest(3, 'Salary')
            chosen_pitcher = affordable_pitchers.loc[affordable_pitchers['value_score'].idxmax()]
        else:  # balanced
            affordable_pitchers = pitchers[
                (pitchers['Salary'] >= 7000) & 
                (pitchers['Salary'] <= 10000)
            ]
            if affordable_pitchers.empty:
                affordable_pitchers = pitchers
            chosen_pitcher = affordable_pitchers.loc[affordable_pitchers['FPPG'].idxmax()]
        
        selected_players.append(chosen_pitcher)
        remaining_budget -= chosen_pitcher['Salary']
        used_ids.add(chosen_pitcher['Id'])
        
        # STEP 2: Build team stack (3-5 players)
        stack_candidates = slate[
            (slate['Team'] == target_team) &
            (slate['Position'] != 'P') &
            (~slate['Id'].isin(used_ids))
        ]
        
        if len(stack_candidates) < 3:
            return None  # Not enough players for stack
        
        # Select stack players with position diversity
        stack_candidates['stack_score'] = (
            stack_candidates['FPPG'] * 0.5 +
            stack_candidates['value_score'] * 0.3 +
            stack_candidates['ceiling_est'] * 0.2
        )
        
        stack_players = []
        stack_budget = remaining_budget * 0.65  # Reserve for stack
        
        # Prioritize different positions for stack diversity
        position_priorities = ['C', '1B', '2B', '3B', 'SS', 'OF']
        random.shuffle(position_priorities)  # Add randomness
        
        for pos in position_priorities:
            pos_candidates = stack_candidates[
                (stack_candidates['Roster Position'].str.contains(pos, na=False)) &
                (~stack_candidates['Id'].isin(used_ids)) &
                (stack_candidates['Salary'] <= stack_budget)
            ]
            
            if not pos_candidates.empty and len(stack_players) < 4:
                chosen = pos_candidates.loc[pos_candidates['stack_score'].idxmax()]
                stack_players.append(chosen)
                stack_budget -= chosen['Salary']
                used_ids.add(chosen['Id'])
        
        # Fill remaining stack spots
        while len(stack_players) < 4:
            remaining_stack = stack_candidates[
                (~stack_candidates['Id'].isin(used_ids)) &
                (stack_candidates['Salary'] <= stack_budget)
            ]
            
            if remaining_stack.empty:
                break
                
            chosen = remaining_stack.loc[remaining_stack['stack_score'].idxmax()]
            stack_players.append(chosen)
            stack_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(stack_players) < 3:
            return None  # Couldn't build proper stack
        
        selected_players.extend(stack_players)
        remaining_budget -= sum(p['Salary'] for p in stack_players)
        
        # STEP 3: Fill remaining positions
        positions_needed = 9 - len(selected_players)
        
        for i in range(positions_needed):
            remaining_candidates = slate[
                (~slate['Id'].isin(used_ids)) &
                (slate['Position'] != 'P')
            ]
            
            positions_left = positions_needed - i
            if positions_left > 1:
                max_spend = (remaining_budget - (positions_left-1) * 2000)
            else:
                max_spend = remaining_budget
            
            affordable = remaining_candidates[
                (remaining_candidates['Salary'] <= max_spend) &
                (remaining_candidates['Salary'] >= 2000)
            ]
            
            if affordable.empty:
                return None
            
            # Selection preference: different teams for diversity
            affordable['selection_score'] = (
                affordable['FPPG'] * 0.5 +
                affordable['value_score'] * 0.3 +
                affordable['ceiling_est'] * 0.2
            )
            
            # Bonus for different teams (diversification)
            used_teams = set(p['Team'] for p in selected_players if p['Position'] != 'P')
            for team in used_teams:
                different_team_bonus = np.where(affordable['Team'] != team, 0.5, 0)
                affordable.loc[:, 'selection_score'] += different_team_bonus
            
            chosen = affordable.loc[affordable['selection_score'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            total_ceiling = sum(p['ceiling_est'] for p in selected_players)
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'total_ceiling': total_ceiling,
                'stack_team': target_team,
                'stack_size': len(stack_players),
                'pitcher_strategy': pitcher_strategy
            }
        
        return None
    
    def generate_diversified_lineups(self, slate, count=25):
        """Generate diversified tournament lineups"""
        print(f"\nTARGET: GENERATING {count} DIVERSIFIED TOURNAMENT LINEUPS")
        print("="*70)
        
        # Get stacking options
        team_analysis = self.analyze_stacking_options(slate)
        top_teams = team_analysis.head(12).index.tolist()  # Top 12 stackable teams
        
        lineups = []
        pitcher_strategies = ['premium', 'balanced', 'value']
        
        for i in range(count):
            # Cycle through teams and strategies
            target_team = top_teams[i % len(top_teams)]
            pitcher_strategy = pitcher_strategies[i % len(pitcher_strategies)]
            
            lineup = self.build_team_stack_lineup(slate, target_team, pitcher_strategy)
            
            if lineup:
                lineup['lineup_id'] = f"DIV_{i+1:02d}"
                lineup['strategy'] = f"{target_team}_{pitcher_strategy}"
                lineups.append(lineup)
                
                print(f"SUCCESS: {lineup['lineup_id']} ({lineup['strategy']}): ${lineup['total_salary']:,} | {lineup['total_projected']:.1f} proj | {lineup['total_ceiling']:.1f} ceil | {lineup['stack_size']}-man {lineup['stack_team']}")
            else:
                print(f"ERROR: Failed {i+1} ({target_team}_{pitcher_strategy})")
        
        return lineups
    
    def export_diversified_lineups(self, lineups):
        """Export diversified lineups"""
        if not lineups:
            print("ERROR: No lineups to export")
            return
        
        print(f"\n EXPORTING {len(lineups)} DIVERSIFIED LINEUPS...")
        
        # Prepare export data
        export_data = []
        
        for lineup in lineups:
            row = {
                'Lineup_ID': lineup['lineup_id'],
                'Strategy': lineup['strategy'],
                'Stack_Team': lineup['stack_team'],
                'Stack_Size': lineup['stack_size'],
                'Pitcher_Strategy': lineup['pitcher_strategy'],
                'Total_Salary': lineup['total_salary'],
                'Projected_FPPG': lineup['total_projected'],
                'Ceiling_FPPG': lineup['total_ceiling'],
                'Upside_Ratio': lineup['total_ceiling'] / lineup['total_projected']
            }
            
            # Map players to positions
            positions_filled = {}
            
            for player in lineup['players']:
                name = f"{player['First Name']} {player['Last Name']}"
                
                if player['Position'] == 'P':
                    row['P'] = name
                else:
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
        
        # Save diversified lineups
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"diversified_tournament_lineups_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        df = pd.DataFrame(export_data)
        df.to_csv(filepath, index=False)
        
        print(f"SUCCESS: Diversified lineups exported: {filename}")
        
        # Portfolio analysis
        projections = [l['total_projected'] for l in lineups]
        ceilings = [l['total_ceiling'] for l in lineups]
        
        print(f"\nLINEUP: DIVERSIFIED PORTFOLIO ANALYSIS:")
        print(f"  DATA: Projected: {min(projections):.1f} - {max(projections):.1f} FPPG (avg: {np.mean(projections):.1f})")
        print(f"  START: Ceiling: {min(ceilings):.1f} - {max(ceilings):.1f} FPPG (avg: {np.mean(ceilings):.1f})")
        
        # Tournament readiness
        competitive_lineups = sum(1 for c in ceilings if c >= 220)
        elite_lineups = sum(1 for c in ceilings if c >= 250)
        
        print(f"\nTARGET: TOURNAMENT COMPETITIVENESS:")
        print(f"   220+ ceiling lineups: {competitive_lineups}/{len(lineups)} ({competitive_lineups/len(lineups)*100:.0f}%)")
        print(f"   250+ ceiling lineups: {elite_lineups}/{len(lineups)} ({elite_lineups/len(lineups)*100:.0f}%)")
        
        # Stack diversity
        stack_teams = {}
        for lineup in lineups:
            team = lineup['stack_team']
            stack_teams[team] = stack_teams.get(team, 0) + 1
        
        print(f"\nTARGET: STACK DIVERSIFICATION:")
        print(f"  DATA: Teams stacked: {len(stack_teams)} different teams")
        for team, count in sorted(stack_teams.items(), key=lambda x: x[1], reverse=True):
            print(f"     {team}: {count} lineups")
        
        # Top lineups
        print(f"\n TOP 5 DIVERSIFIED LINEUPS:")
        sorted_lineups = sorted(lineups, key=lambda x: x['total_ceiling'], reverse=True)
        
        for i, lineup in enumerate(sorted_lineups[:5], 1):
            upside = lineup['total_ceiling'] / lineup['total_projected']
            print(f"  {i}. {lineup['lineup_id']} ({lineup['strategy']}): {lineup['total_projected']:.1f}  {lineup['total_ceiling']:.1f} ({upside:.1f}x) | {lineup['stack_size']}-man {lineup['stack_team']}")
        
        return filepath

def main():
    print("TARGET: DIVERSIFIED TOURNAMENT BUILDER")
    print("Building diverse lineups with multiple team stacks")
    print("="*70)
    
    builder = DiversifiedTournamentBuilder()
    
    try:
        # Load viable slate
        slate = builder.load_viable_slate()
        
        # Generate diversified lineups
        lineups = builder.generate_diversified_lineups(slate, count=25)
        
        if lineups:
            # Export lineups
            filepath = builder.export_diversified_lineups(lineups)
            print(f"\nCOMPLETE: DIVERSIFICATION COMPLETE!")
            print(f"TARGET: Generated {len(lineups)} diversified tournament lineups")
            print(f"TIP: Strategy: Multiple team stacks, pitcher diversity")
            print(f"LINEUP: Ready for tournament domination!")
        else:
            print("ERROR: Failed to generate diversified lineups")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
