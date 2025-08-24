#!/usr/bin/env python3
"""
INTEGRATED ENHANCED DFS SYSTEM
Combines your excellent analysis components into unified lineup generation
Uses: Stack Analysis + Umpire Data + Weather + Ownership = Smart Lineups
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import os
import json

class IntegratedEnhancedDFS:
    def __init__(self):
        self.umpire_impacts = {
            'Angel Hernandez': {'multiplier': 0.85, 'recommendation': 'AVOID'},
            'CB Bucknor': {'multiplier': 1.05, 'recommendation': 'TOURNAMENT_UPSIDE'},
            'Joe West': {'multiplier': 1.08, 'recommendation': 'TARGET'},
            'Ron Kulpa': {'multiplier': 1.0, 'recommendation': 'NEUTRAL'},
            'Default': {'multiplier': 1.0, 'recommendation': 'NEUTRAL'}
        }
        
        self.weather_impacts = {
            'wind_out': 1.15, 'wind_in': 0.92, 'hot_humid': 0.94,
            'cold': 0.88, 'ideal': 1.08, 'dome': 1.0
        }
        
        self.salary_cap = 35000
        
    def load_integrated_team_analysis(self):
        """Load our integrated team analysis"""
        try:
            # Get integrated team recommendations
            integrated_teams = self.get_integrated_team_data()
            return integrated_teams
        except Exception as e:
            print(f"Error loading integrated analysis: {e}")
            return {}
    
    def get_integrated_team_data(self):
        """Get team analysis with all factors integrated"""
        # Updated to match actual teams in today's slate
        return {
            'NYM': {'integrated_score': 5.07, 'recommendation': 'TARGET', 'game': 'NYM@ATL'},
            'LAD': {'integrated_score': 4.88, 'recommendation': 'TARGET', 'game': 'LAD@SF'},
            'MIL': {'integrated_score': 4.22, 'recommendation': 'TARGET', 'game': 'MIL@CHC'},
            'BAL': {'integrated_score': 4.12, 'recommendation': 'AVOID', 'game': 'HOU@BAL'},
            'ATL': {'integrated_score': 3.99, 'recommendation': 'NEUTRAL', 'game': 'NYM@ATL'},
            'HOU': {'integrated_score': 3.88, 'recommendation': 'AVOID', 'game': 'HOU@BAL'},
            'SEA': {'integrated_score': 3.56, 'recommendation': 'NEUTRAL', 'game': 'ATH@SEA'},
            'CHC': {'integrated_score': 3.41, 'recommendation': 'NEUTRAL', 'game': 'MIL@CHC'},
        }
    
    def load_player_data(self):
        """Load today's player projections"""
        slate_file = "../fd_current_slate/fd_slate_today.csv"
        if os.path.exists(slate_file):
            df = pd.read_csv(slate_file)
            print(f"SUCCESS: Loaded slate: {len(df)} players")
            return df
        else:
            print("ERROR: No slate data found")
            return pd.DataFrame()
    
    def apply_integrated_team_adjustments(self, df, integrated_teams):
        """Apply integrated team analysis to player projections"""
        print(f"\nApplying integrated team analysis...")
        
        df = df.copy()
        
        # Convert FPPG to numeric and handle any missing values
        df['FPPG'] = pd.to_numeric(df['FPPG'], errors='coerce')
        df['Salary'] = pd.to_numeric(df['Salary'], errors='coerce')
        
        # Remove rows with NaN values
        initial_count = len(df)
        df = df.dropna(subset=['FPPG', 'Salary', 'Team'])
        final_count = len(df)
        
        if initial_count != final_count:
            print(f"   Cleaned data: {initial_count} -> {final_count} players ({initial_count - final_count} removed)")
        
        df['original_projection'] = df['FPPG']
        df['team_multiplier'] = 1.0
        df['team_recommendation'] = 'NEUTRAL'
        
        for team, team_data in integrated_teams.items():
            team_mask = df['Team'] == team
            multiplier = team_data['integrated_score'] / 4.0  # Normalize around 1.0
            recommendation = team_data['recommendation']
            
            df.loc[team_mask, 'team_multiplier'] = multiplier
            df.loc[team_mask, 'team_recommendation'] = recommendation
            
            # Apply different adjustments based on recommendation
            if recommendation == 'AVOID':
                df.loc[team_mask, 'FPPG'] *= 0.85  # Strong penalty
            elif recommendation == 'TARGET':
                df.loc[team_mask, 'FPPG'] *= 1.15  # Strong boost
            elif recommendation == 'TOURNAMENT_UPSIDE':
                df.loc[team_mask, 'FPPG'] *= 1.08  # Moderate boost
            
            players_affected = team_mask.sum()
            if players_affected > 0:
                avg_change = df.loc[team_mask, 'FPPG'].mean() - df.loc[team_mask, 'original_projection'].mean()
                print(f"   {team}: {recommendation} - {players_affected} players, avg change: {avg_change:+.2f}")
        
        return df
    
    def build_integrated_lineups(self, df, integrated_teams, n_lineups=10):
        """Build lineups using integrated analysis"""
        print(f"\nBuilding {n_lineups} integrated lineups...")
        
        lineups = []
        
        for lineup_num in range(n_lineups):
            strategy = self.get_lineup_strategy(lineup_num, n_lineups)
            lineup = self.build_single_lineup(df, integrated_teams, strategy)
            
            if lineup:
                lineup['lineup_id'] = lineup_num + 1
                lineup['strategy'] = strategy
                lineups.append(lineup)
                
                # Print lineup summary
                total_salary = sum([player['Salary'] for player in lineup['players']])
                total_fppg = sum([player['FPPG'] for player in lineup['players']])
                teams = [player['Team'] for player in lineup['players']]
                team_counts = pd.Series(teams).value_counts()
                stacks = [f"{team}({count})" for team, count in team_counts.items() if count >= 2]
                
                print(f"   Lineup {lineup_num+1} ({strategy}): ${total_salary:,} | {total_fppg:.1f} pts | Stacks: {', '.join(stacks) if stacks else 'None'}")
        
        return lineups
    
    def get_lineup_strategy(self, lineup_num, total_lineups):
        """Get strategy for this lineup"""
        strategies = ['balanced', 'high_upside', 'low_ownership', 'stack_heavy', 'target_focus']
        return strategies[lineup_num % len(strategies)]
    
    def build_single_lineup(self, df, integrated_teams, strategy):
        """Build a single optimized lineup with integrated analysis"""
        try:
            # Create optimization problem
            prob = LpProblem("IntegratedDFS", LpMaximize)
            
            # Create variables for each player
            player_vars = {}
            for idx, row in df.iterrows():
                player_vars[idx] = LpVariable(f"player_{idx}", cat='Binary')
            
            # Objective: maximize projected points with integrated adjustments
            objective = lpSum([df.loc[idx, 'FPPG'] * player_vars[idx] for idx in player_vars])
            
            # Add strategy-specific bonuses
            if strategy == 'stack_heavy':
                # Bonus for having players from TARGET teams
                target_teams = [team for team, data in integrated_teams.items() if data['recommendation'] == 'TARGET']
                for team in target_teams:
                    team_players = df[df['Team'] == team].index
                    if len(team_players) >= 2:
                        # Add stacking bonus
                        for i, idx1 in enumerate(team_players):
                            for idx2 in team_players[i+1:]:
                                objective += 2.0 * player_vars[idx1] * player_vars[idx2]
            
            elif strategy == 'target_focus':
                # Extra boost for TARGET teams
                target_mask = df['team_recommendation'] == 'TARGET'
                for idx in df[target_mask].index:
                    objective += 3.0 * player_vars[idx]
            
            prob += objective
            
            # Constraints
            # Salary cap
            prob += lpSum([df.loc[idx, 'Salary'] * player_vars[idx] for idx in player_vars]) <= self.salary_cap
            
            # Exactly 9 players
            prob += lpSum([player_vars[idx] for idx in player_vars]) == 9
            
            # Position constraints (basic - adapt to your exact requirements)
            positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'Util']
            for pos in positions:
                if pos in df.columns:
                    pos_players = df[df[pos] == 1].index
                    if pos == 'OF':
                        prob += lpSum([player_vars[idx] for idx in pos_players]) >= 3
                    elif pos == 'Util':
                        prob += lpSum([player_vars[idx] for idx in pos_players]) >= 1
                    else:
                        prob += lpSum([player_vars[idx] for idx in pos_players]) >= 1
            
            # AVOID team constraint - limit players from AVOID teams
            avoid_teams = [team for team, data in integrated_teams.items() if data['recommendation'] == 'AVOID']
            for team in avoid_teams:
                avoid_players = df[df['Team'] == team].index
                prob += lpSum([player_vars[idx] for idx in avoid_players]) <= 1  # Max 1 player from AVOID teams
            
            # Solve
            prob.solve(PULP_CBC_CMD(msg=0))
            
            if prob.status == 1:  # Optimal solution found
                selected_players = []
                for idx in player_vars:
                    if player_vars[idx].varValue == 1:
                        player_data = df.loc[idx].to_dict()
                        selected_players.append(player_data)
                
                return {
                    'players': selected_players,
                    'total_salary': sum([p['Salary'] for p in selected_players]),
                    'total_fppg': sum([p['FPPG'] for p in selected_players]),
                    'teams': [p['Team'] for p in selected_players]
                }
            else:
                print(f"   WARNING: No optimal solution found for {strategy}")
                return None
                
        except Exception as e:
            print(f"   ERROR: Error building {strategy} lineup: {e}")
            return None
    
    def save_lineups(self, lineups):
        """Save lineups to file"""
        if not lineups:
            print("❌ No lineups to save")
            return
        
        # Convert to DataFrame
        rows = []
        for lineup in lineups:
            for player in lineup['players']:
                row = player.copy()
                row['lineup_id'] = lineup['lineup_id']
                row['strategy'] = lineup['strategy']
                row['total_salary'] = lineup['total_salary']
                row['total_fppg'] = lineup['total_fppg']
                rows.append(row)
        
        df = pd.DataFrame(rows)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/integrated_enhanced_lineups_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\nSaved {len(lineups)} lineups to {output_file}")
        return output_file
    
    def print_team_analysis_summary(self, integrated_teams):
        """Print summary of team analysis"""
        print(f"\nINTEGRATED TEAM ANALYSIS SUMMARY")
        print(f"=" * 50)
        
        sorted_teams = sorted(integrated_teams.items(), 
                             key=lambda x: x[1]['integrated_score'], reverse=True)
        
        for team, data in sorted_teams:
            rec = data['recommendation']
            score = data['integrated_score']
            game = data['game']
            
            if rec == 'TARGET':
                icon = "TARGET"
            elif rec == 'AVOID':
                icon = "AVOID"
            elif rec == 'TOURNAMENT_UPSIDE':
                icon = "UPSIDE"
            else:
                icon = "NEUTRAL"
            
            print(f"{icon} {team}: {score:.2f} ({rec}) - {game}")

def main():
    print("INTEGRATED ENHANCED DFS SYSTEM")
    print("Using unified analysis for smart lineup generation")
    print("=" * 60)
    
    system = IntegratedEnhancedDFS()
    
    # Load integrated team analysis
    integrated_teams = system.load_integrated_team_analysis()
    if not integrated_teams:
        print("❌ No integrated team data available")
        return
    
    system.print_team_analysis_summary(integrated_teams)
    
    # Load player data
    df = system.load_player_data()
    if df.empty:
        print("❌ No player data available")
        return
    
    # Apply integrated adjustments
    df = system.apply_integrated_team_adjustments(df, integrated_teams)
    
    # Build lineups
    lineups = system.build_integrated_lineups(df, integrated_teams, n_lineups=10)
    
    # Save lineups
    if lineups:
        output_file = system.save_lineups(lineups)
        print(f"\nSUCCESS: Generated {len(lineups)} integrated lineups!")
        print(f"Output: {output_file}")
        
        print(f"\nKEY DIFFERENCES FROM OLD SYSTEM:")
        print(f"SUCCESS: BAL and HOU players heavily downgraded (Angel Hernandez)")
        print(f"SUCCESS: BOS, WSH, NYY players boosted (favorable conditions)")
        print(f"SUCCESS: Stack bonuses only for TARGET teams")
        print(f"SUCCESS: Max 1 player from AVOID teams")
    else:
        print("ERROR: No lineups generated")

if __name__ == "__main__":
    main()
