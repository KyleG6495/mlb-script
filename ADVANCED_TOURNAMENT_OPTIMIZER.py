#!/usr/bin/env python3
"""
ADVANCED TOURNAMENT OPTIMIZER
============================
Build elite tournament lineups with game stacking, correlation, and ownership prediction.
Target: 250+ FPPG ceiling to dominate tournaments.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from itertools import combinations
warnings.filterwarnings('ignore')

class AdvancedTournamentOptimizer:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_elite_slate(self):
        """Load slate with advanced filtering for elite tournament play"""
        print("LINEUP: ADVANCED TOURNAMENT OPTIMIZER")
        print("Building elite lineups with stacking & correlation")
        print("="*70)
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        df = pd.read_csv(slate_file)
        
        print(f"DATA: Raw slate: {len(df)} players")
        
        # Elite filtering - only top performers
        viable = df[
            (df['Injury Indicator'].isna()) &  # No injuries
            (df['FPPG'] > 0.1)                 # Has projections
        ].copy()
        
        # Separate pitchers and hitters
        pitchers = viable[
            (viable['Position'] == 'P') &
            (viable['Probable Pitcher'] == 'Yes') &
            (viable['FPPG'] >= 15.0)  # Only strong pitchers for tournaments
        ].copy()
        
        hitters = viable[
            (viable['Position'] != 'P') &
            (viable['FPPG'] >= 5.0)  # Remove terrible projections
        ].copy()
        
        elite_slate = pd.concat([pitchers, hitters], ignore_index=True)
        
        print(f"SUCCESS: Elite slate: {len(elite_slate)} players ({len(pitchers)} elite pitchers, {len(hitters)} viable hitters)")
        
        return elite_slate
    
    def analyze_game_environments(self, slate):
        """Identify the highest-upside game environments for stacking"""
        print(f"\nTARGET: GAME ENVIRONMENT ANALYSIS:")
        
        # Calculate game metrics
        games = slate.groupby('Game').agg({
            'FPPG': ['sum', 'mean', 'count'],
            'Salary': 'mean'
        }).round(1)
        
        games.columns = ['total_projected', 'avg_projected', 'player_count', 'avg_salary']
        games = games.sort_values('total_projected', ascending=False)
        
        # Add game quality score
        games['upside_score'] = (
            games['total_projected'] * 0.6 +
            games['avg_projected'] * 0.4
        )
        
        print(f"   TOP 8 STACKING TARGETS:")
        for game, data in games.head(8).iterrows():
            print(f"     {game:15} | {data['total_projected']:5.1f} total | {data['avg_projected']:4.1f} avg | {data['player_count']:2.0f} players")
        
        return games
    
    def predict_ownership(self, slate):
        """Predict player ownership based on salary, projection, and value"""
        slate = slate.copy()
        
        # Calculate ownership predictors
        slate['value_score'] = slate['FPPG'] / (slate['Salary'] / 1000)
        slate['projection_rank'] = slate.groupby('Position')['FPPG'].rank(ascending=False)
        slate['value_rank'] = slate.groupby('Position')['value_score'].rank(ascending=False)
        
        # Ownership prediction model (simplified)
        slate['predicted_ownership'] = np.where(
            slate['Position'] == 'P',
            # Pitcher ownership
            np.clip(
                (slate['FPPG'] * 0.5 + slate['value_score'] * 0.3 - slate['Salary']/500) * 2.5,
                1.0, 50.0
            ),
            # Hitter ownership  
            np.clip(
                (slate['value_score'] * 0.4 + slate['FPPG'] * 0.3 - slate['Salary']/300) * 3.0,
                0.5, 40.0
            )
        )
        
        # Identify leverage spots (low ownership, high upside)
        slate['leverage_score'] = slate['FPPG'] / (slate['predicted_ownership'] + 1)
        
        return slate
    
    def build_stacked_lineup(self, slate, strategy_config):
        """Build lineup with advanced stacking and correlation"""
        
        strategy_name = strategy_config['name']
        primary_stack = strategy_config.get('primary_stack', 4)
        mini_stack = strategy_config.get('mini_stack', True)
        leverage_focus = strategy_config.get('leverage_focus', False)
        
        print(f"\n Building {strategy_name} with {primary_stack}-man stack...")
        
        # Predict ownership
        slate_with_ownership = self.predict_ownership(slate)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        used_teams = set()
        
        # STEP 1: Select pitcher (avoid stacking team to reduce correlation risk)
        pitchers = slate_with_ownership[
            (slate_with_ownership['Position'] == 'P') &
            (~slate_with_ownership['Id'].isin(used_ids))
        ]
        
        if leverage_focus:
            # Target low-owned, high-upside pitcher
            chosen_pitcher = pitchers.loc[pitchers['leverage_score'].idxmax()]
        else:
            # Target high-projection pitcher
            affordable_pitchers = pitchers[pitchers['Salary'] <= 11000]
            if affordable_pitchers.empty:
                affordable_pitchers = pitchers
            chosen_pitcher = affordable_pitchers.loc[affordable_pitchers['FPPG'].idxmax()]
        
        selected_players.append(chosen_pitcher)
        remaining_budget -= chosen_pitcher['Salary']
        used_ids.add(chosen_pitcher['Id'])
        
        # Avoid pitcher's team for hitting stack (reduce negative correlation)
        pitcher_team = chosen_pitcher['Team']
        
        print(f"  BASEBALL: Pitcher: {chosen_pitcher['First Name']} {chosen_pitcher['Last Name']} (${chosen_pitcher['Salary']:,}, {chosen_pitcher['FPPG']:.1f} FPPG, {chosen_pitcher['predicted_ownership']:.1f}% own)")
        
        # STEP 2: Build primary hitting stack (4+ players from same team)
        hitters = slate_with_ownership[
            (slate_with_ownership['Position'] != 'P') &
            (~slate_with_ownership['Id'].isin(used_ids)) &
            (slate_with_ownership['Team'] != pitcher_team)  # Avoid pitcher's team
        ]
        
        # Find best stacking team
        team_scores = hitters.groupby('Team').agg({
            'FPPG': 'sum',
            'Salary': 'sum',
            'predicted_ownership': 'mean',
            'Id': 'count'
        }).rename(columns={'Id': 'player_count'})
        
        # Filter teams with enough players
        viable_teams = team_scores[team_scores['player_count'] >= primary_stack]
        
        if viable_teams.empty:
            print(f"  ERROR: No teams with {primary_stack}+ players available")
            return None
        
        # Select stacking team based on strategy
        if leverage_focus:
            # Low-owned, high-upside stack
            viable_teams['stack_score'] = viable_teams['FPPG'] / (viable_teams['predicted_ownership'] + 5)
        else:
            # High-projection stack
            viable_teams['stack_score'] = viable_teams['FPPG']
        
        # Ensure we can afford the stack
        affordable_teams = viable_teams[viable_teams['Salary'] <= remaining_budget * 0.8]
        if affordable_teams.empty:
            affordable_teams = viable_teams
        
        stack_team = affordable_teams['stack_score'].idxmax()
        stack_candidates = hitters[hitters['Team'] == stack_team].copy()
        
        print(f"  TARGET: Primary stack: {stack_team} ({len(stack_candidates)} available)")
        
        # Select best stack players by position diversity and value
        stack_candidates['stack_priority'] = (
            stack_candidates['FPPG'] * 0.5 +
            stack_candidates['value_score'] * 0.3 +
            stack_candidates['leverage_score'] * 0.2
        )
        
        # Ensure position diversity in stack
        stack_players = []
        stack_budget = remaining_budget * 0.6  # Reserve budget for stack
        
        # Prioritize different positions
        for pos_priority in ['OF', 'C', '1B', '2B', '3B', 'SS']:
            pos_candidates = stack_candidates[
                (stack_candidates['Roster Position'].str.contains(pos_priority, na=False)) &
                (~stack_candidates['Id'].isin(used_ids)) &
                (stack_candidates['Salary'] <= stack_budget)
            ]
            
            if not pos_candidates.empty and len(stack_players) < primary_stack:
                chosen = pos_candidates.loc[pos_candidates['stack_priority'].idxmax()]
                stack_players.append(chosen)
                stack_budget -= chosen['Salary']
                used_ids.add(chosen['Id'])
                print(f"     {chosen['First Name']} {chosen['Last Name']} ({pos_priority}, ${chosen['Salary']:,}, {chosen['FPPG']:.1f} FPPG)")
        
        # Fill remaining stack spots with best available
        while len(stack_players) < primary_stack:
            remaining_stack = stack_candidates[
                (~stack_candidates['Id'].isin(used_ids)) &
                (stack_candidates['Salary'] <= stack_budget)
            ]
            
            if remaining_stack.empty:
                break
                
            chosen = remaining_stack.loc[remaining_stack['stack_priority'].idxmax()]
            stack_players.append(chosen)
            stack_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
            print(f"     {chosen['First Name']} {chosen['Last Name']} (${chosen['Salary']:,}, {chosen['FPPG']:.1f} FPPG)")
        
        selected_players.extend(stack_players)
        remaining_budget -= sum(p['Salary'] for p in stack_players)
        used_teams.add(stack_team)
        
        # STEP 3: Fill remaining positions
        positions_filled = len(selected_players)
        positions_needed = 9 - positions_filled
        
        print(f"  DATA: Stack complete: {len(stack_players)} players, ${remaining_budget:,} remaining for {positions_needed} spots")
        
        for i in range(positions_needed):
            remaining_candidates = slate_with_ownership[
                (~slate_with_ownership['Id'].isin(used_ids)) &
                (slate_with_ownership['Position'] != 'P')
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
                print(f"  ERROR: No affordable players for spot {i+1}")
                return None
            
            # Mini-stack bonus (same team as existing non-pitcher players)
            if mini_stack:
                for team in used_teams:
                    same_team_bonus = np.where(affordable['Team'] == team, 2.0, 0)
                    affordable.loc[:, 'selection_score'] = (
                        affordable['FPPG'] * 0.4 +
                        affordable['leverage_score'] * 0.3 +
                        affordable['value_score'] * 0.2 +
                        same_team_bonus
                    )
            else:
                affordable.loc[:, 'selection_score'] = (
                    affordable['FPPG'] * 0.5 +
                    affordable['leverage_score'] * 0.3 +
                    affordable['value_score'] * 0.2
                )
            
            chosen = affordable.loc[affordable['selection_score'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
            
            print(f"    TARGET: Spot {i+1}: {chosen['First Name']} {chosen['Last Name']} (${chosen['Salary']:,}, {chosen['FPPG']:.1f} FPPG)")
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            total_ceiling = sum(p['FPPG'] * (1.8 if p['Position'] != 'P' else 1.5) for p in selected_players)
            avg_ownership = np.mean([p['predicted_ownership'] for p in selected_players])
            
            return {
                'players': selected_players,
                'strategy': strategy_name,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'total_ceiling': total_ceiling,
                'avg_ownership': avg_ownership,
                'stack_team': stack_team,
                'stack_size': len(stack_players)
            }
        
        return None
    
    def generate_elite_lineups(self, slate, count=20):
        """Generate elite tournament lineups with diverse stacking strategies"""
        print(f"\nLINEUP: GENERATING {count} ELITE TOURNAMENT LINEUPS")
        print("Target: 250+ FPPG ceiling to dominate tournaments")
        print("="*70)
        
        # Elite stacking strategies
        strategies = [
            {'name': 'Mega_Stack_5', 'primary_stack': 5, 'mini_stack': True, 'leverage_focus': False},
            {'name': 'Power_Stack_4', 'primary_stack': 4, 'mini_stack': True, 'leverage_focus': False},
            {'name': 'Leverage_Stack_4', 'primary_stack': 4, 'mini_stack': True, 'leverage_focus': True},
            {'name': 'Ceiling_Stack_4', 'primary_stack': 4, 'mini_stack': False, 'leverage_focus': False},
            {'name': 'Mini_Stack_3', 'primary_stack': 3, 'mini_stack': True, 'leverage_focus': False},
            {'name': 'Contrarian_Stack', 'primary_stack': 4, 'mini_stack': False, 'leverage_focus': True},
        ]
        
        lineups = []
        strategy_counts = {}
        
        for i in range(count):
            base_strategy = strategies[i % len(strategies)]
            strategy_name = base_strategy['name']
            
            strategy_counts[strategy_name] = strategy_counts.get(strategy_name, 0) + 1
            
            if strategy_counts[strategy_name] > 1:
                base_strategy = base_strategy.copy()
                base_strategy['name'] = f"{strategy_name}_v{strategy_counts[strategy_name]}"
            
            lineup = self.build_stacked_lineup(slate, base_strategy)
            
            if lineup:
                lineup['lineup_id'] = f"ELITE_{i+1:02d}"
                lineups.append(lineup)
                
                ownership_str = f"{lineup['avg_ownership']:.1f}% avg own"
                stack_str = f"{lineup['stack_size']}-man {lineup['stack_team']}"
                
                print(f"SUCCESS: {lineup['lineup_id']} ({lineup['strategy']}): ${lineup['total_salary']:,} | {lineup['total_projected']:.1f} proj | {lineup['total_ceiling']:.1f} ceil | {stack_str} | {ownership_str}")
            else:
                print(f"ERROR: Failed {i+1} ({base_strategy['name']})")
        
        return lineups
    
    def export_elite_lineups(self, lineups):
        """Export elite tournament lineups with advanced analytics"""
        if not lineups:
            print("ERROR: No elite lineups to export")
            return
        
        print(f"\n EXPORTING {len(lineups)} ELITE TOURNAMENT LINEUPS...")
        
        # Prepare advanced export data
        export_data = []
        
        for lineup in lineups:
            row = {
                'Lineup_ID': lineup['lineup_id'],
                'Strategy': lineup['strategy'],
                'Stack_Team': lineup['stack_team'],
                'Stack_Size': lineup['stack_size'],
                'Total_Salary': lineup['total_salary'],
                'Projected_FPPG': lineup['total_projected'],
                'Ceiling_FPPG': lineup['total_ceiling'],
                'Avg_Ownership': lineup['avg_ownership'],
                'Upside_Ratio': lineup['total_ceiling'] / lineup['total_projected']
            }
            
            # Map players to FanDuel positions
            positions_filled = {}
            
            for player in lineup['players']:
                name = f"{player['First Name']} {player['Last Name']}"
                
                if player['Position'] == 'P':
                    row['P'] = name
                else:
                    roster_pos = player['Roster Position']
                    
                    # Smart position assignment
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
        
        # Save elite lineups
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"elite_tournament_lineups_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        df = pd.DataFrame(export_data)
        df.to_csv(filepath, index=False)
        
        print(f"SUCCESS: Elite lineups exported: {filename}")
        
        # Advanced portfolio analysis
        projections = [l['total_projected'] for l in lineups]
        ceilings = [l['total_ceiling'] for l in lineups]
        ownerships = [l['avg_ownership'] for l in lineups]
        
        print(f"\nLINEUP: ELITE PORTFOLIO ANALYSIS:")
        print(f"  DATA: Projected Range: {min(projections):.1f} - {max(projections):.1f} FPPG (avg: {np.mean(projections):.1f})")
        print(f"  START: Ceiling Range: {min(ceilings):.1f} - {max(ceilings):.1f} FPPG (avg: {np.mean(ceilings):.1f})")
        print(f"  OWNERSHIP: Ownership Range: {min(ownerships):.1f}% - {max(ownerships):.1f}% (avg: {np.mean(ownerships):.1f}%)")
        
        # Tournament dominance metrics
        elite_lineups = sum(1 for c in ceilings if c >= 250)
        dominant_lineups = sum(1 for c in ceilings if c >= 280)
        
        print(f"\n TOURNAMENT DOMINANCE:")
        print(f"  TARGET: 250+ ceiling lineups: {elite_lineups}/{len(lineups)} ({elite_lineups/len(lineups)*100:.0f}%)")
        print(f"   280+ ceiling lineups: {dominant_lineups}/{len(lineups)} ({dominant_lineups/len(lineups)*100:.0f}%)")
        
        if dominant_lineups >= len(lineups) * 0.2:
            print(f"  LINEUP: LEGENDARY: Potential tournament domination!")
        elif elite_lineups >= len(lineups) * 0.6:
            print(f"   ELITE: Excellent tournament potential!")
        else:
            print(f"   STRONG: Good tournament chances!")
        
        # Stack analysis
        stack_teams = {}
        for lineup in lineups:
            team = lineup['stack_team']
            stack_teams[team] = stack_teams.get(team, 0) + 1
        
        print(f"\nTARGET: STACKING ANALYSIS:")
        print(f"  DATA: Teams stacked: {len(stack_teams)} different teams")
        for team, count in sorted(stack_teams.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"     {team}: {count} lineups")
        
        # Best lineups showcase
        print(f"\n TOP 5 ELITE LINEUPS:")
        sorted_lineups = sorted(lineups, key=lambda x: x['total_ceiling'], reverse=True)
        
        for i, lineup in enumerate(sorted_lineups[:5], 1):
            ownership_str = f"{lineup['avg_ownership']:.1f}% own"
            stack_str = f"{lineup['stack_size']}-man {lineup['stack_team']}"
            upside = lineup['total_ceiling'] / lineup['total_projected']
            
            print(f"  {i}. {lineup['lineup_id']} ({lineup['strategy']})")
            print(f"     {lineup['total_projected']:.1f} proj  {lineup['total_ceiling']:.1f} ceil ({upside:.1f}x) | {stack_str} | {ownership_str}")
        
        return filepath
    
    def run_elite_optimization(self):
        """Run complete elite tournament optimization"""
        print("LINEUP: ELITE TOURNAMENT OPTIMIZER")
        print("Building stacked lineups to dominate tournaments")
        print("="*80)
        
        try:
            # Load elite slate
            elite_slate = self.load_elite_slate()
            
            if len(elite_slate) < 100:
                print("ERROR: Not enough elite players for optimization")
                return
            
            # Analyze game environments
            game_analysis = self.analyze_game_environments(elite_slate)
            
            # Generate elite lineups
            lineups = self.generate_elite_lineups(elite_slate, count=20)
            
            if lineups:
                # Export lineups
                filepath = self.export_elite_lineups(lineups)
                
                print(f"\nCOMPLETE: ELITE OPTIMIZATION COMPLETE!")
                print(f" Generated {len(lineups)} elite tournament lineups")
                print(f"TARGET: Strategy: Advanced stacking, ownership prediction, correlation analysis")
                print(f"LINEUP: Target: 250+ FPPG ceiling to dominate tournaments")
                print(f" Ready to crush the competition!")
                
            else:
                print("ERROR: Failed to generate elite lineups")
                
        except Exception as e:
            print(f"Error in elite optimization: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("LINEUP: ELITE TOURNAMENT OPTIMIZER")
    print("Advanced stacking and correlation for tournament domination")
    print("="*80)
    
    optimizer = AdvancedTournamentOptimizer()
    optimizer.run_elite_optimization()

if __name__ == "__main__":
    main()
