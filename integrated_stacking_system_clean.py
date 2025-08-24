#!/usr/bin/env python3
"""
INTEGRATED STACKING SYSTEM - CLEAN VERSION
Connects all your data sources: stack analysis, umpire data, weather, ownership
Generates lineups that consider ALL factors, not just individual optimizations
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import os
import json

class IntegratedStackingSystem:
    def __init__(self):
        self.umpire_impacts = {
            'Angel Hernandez': {'multiplier': 0.85, 'recommendation': 'AVOID', 'reason': 'Inconsistent strike zone hurts both teams'},
            'CB Bucknor': {'multiplier': 1.05, 'recommendation': 'TOURNAMENT_UPSIDE', 'reason': 'High variance umpire creates upside'},
            'Joe West': {'multiplier': 1.08, 'recommendation': 'TARGET', 'reason': 'Hitter-friendly calls'},
            'Ron Kulpa': {'multiplier': 1.0, 'recommendation': 'NEUTRAL', 'reason': 'Average umpire'},
            'Default': {'multiplier': 1.0, 'recommendation': 'NEUTRAL', 'reason': 'No specific data'}
        }
        
        self.weather_impacts = {
            'wind_out': 1.15,      # Wind blowing out
            'wind_in': 0.92,       # Wind blowing in
            'hot_humid': 0.94,     # Heavy air
            'cold': 0.88,          # Ball doesn't carry
            'ideal': 1.08,         # Perfect conditions
            'dome': 1.0            # Neutral conditions
        }
        
    def load_integrated_data(self):
        """Load and integrate all data sources"""
        print("Loading integrated data sources...")
        
        # 1. Load stack analysis (your existing excellent analysis)
        stack_data = self.load_stack_analysis()
        
        # 2. Load ownership data
        ownership_data = self.load_ownership_data()
        
        # 3. Load current slate
        slate_data = self.load_slate_data()
        
        # 4. Get today's games with umpires (simulated for demo)
        game_data = self.get_game_data()
        
        # 5. Integrate everything
        integrated_analysis = self.integrate_all_sources(stack_data, ownership_data, slate_data, game_data)
        
        return integrated_analysis
    
    def load_stack_analysis(self):
        """Load your existing stack analysis"""
        data_dir = "../data"
        stack_files = [f for f in os.listdir(data_dir) if 'team_stack_analysis' in f and f.endswith('.csv')]
        
        if stack_files:
            latest_file = max([os.path.join(data_dir, f) for f in stack_files], key=os.path.getmtime)
            stack_df = pd.read_csv(latest_file)
            print(f"Loaded stack analysis: {os.path.basename(latest_file)}")
            return stack_df
        else:
            print("No stack analysis found")
            return pd.DataFrame()
    
    def load_ownership_data(self):
        """Load ownership projections"""
        data_dir = "../data"
        ownership_files = [f for f in os.listdir(data_dir) if 'ownership_projections' in f and f.endswith('.csv')]
        
        if ownership_files:
            latest_file = max([os.path.join(data_dir, f) for f in ownership_files], key=os.path.getmtime)
            ownership_df = pd.read_csv(latest_file)
            print(f"Loaded ownership data: {os.path.basename(latest_file)}")
            return ownership_df
        else:
            print("No ownership data found")
            return pd.DataFrame()
    
    def load_slate_data(self):
        """Load today's slate"""
        slate_file = "../fd_current_slate/fd_slate_today.csv"
        if os.path.exists(slate_file):
            slate_df = pd.read_csv(slate_file)
            print(f"Loaded slate: {len(slate_df)} players")
            return slate_df
        else:
            print("No slate data found")
            return pd.DataFrame()
    
    def get_game_data(self):
        """Get today's games with umpire assignments (simulate for now)"""
        # This should eventually pull from MLB API or your data source
        # For now, simulate based on what your dashboard shows
        games = {
            'HOU@BAL': {
                'umpire': 'Angel Hernandez',
                'weather': 'ideal',
                'vegas_total': 8.5,
                'temperature': 78
            },
            'WSH@NYM': {
                'umpire': 'CB Bucknor',
                'weather': 'ideal',
                'vegas_total': 8.0,
                'temperature': 75
            },
            'BOS@NYY': {
                'umpire': 'Joe West',
                'weather': 'wind_out',
                'vegas_total': 9.5,
                'temperature': 82
            },
            'STL@SF': {
                'umpire': 'Ron Kulpa',
                'weather': 'wind_in',
                'vegas_total': 7.5,
                'temperature': 68
            },
            'TB@SD': {
                'umpire': 'Default',
                'weather': 'dome',
                'vegas_total': 8.0,
                'temperature': 72
            }
        }
        
        print(f"Game data: {len(games)} games with umpire/weather info")
        return games
    
    def integrate_all_sources(self, stack_df, ownership_df, slate_df, game_data):
        """Integrate all data sources into unified team recommendations"""
        if stack_df.empty:
            print("No stack data to integrate")
            return {}
        
        integrated_teams = {}
        
        for _, stack_row in stack_df.iterrows():
            team = stack_row['team']
            
            # Start with base stack score
            base_score = stack_row.get('stack_value_score', 0)
            opposing_pitcher = stack_row.get('opposing_pitcher', 'Unknown')
            
            # Find the game this team is playing in
            team_game = None
            for game, game_info in game_data.items():
                if team in game:
                    team_game = game
                    break
            
            if team_game:
                game_info = game_data[team_game]
                
                # Apply umpire impact
                umpire = game_info['umpire']
                umpire_impact = self.umpire_impacts.get(umpire, self.umpire_impacts['Default'])
                umpire_multiplier = umpire_impact['multiplier']
                umpire_recommendation = umpire_impact['recommendation']
                
                # Apply weather impact
                weather = game_info['weather']
                weather_multiplier = self.weather_impacts.get(weather, 1.0)
                
                # Calculate integrated score
                integrated_score = base_score * umpire_multiplier * weather_multiplier
                
                # Get ownership data for this team
                team_ownership = self.get_team_ownership(team, ownership_df)
                
                # Determine final recommendation
                final_recommendation = self.determine_recommendation(
                    integrated_score, base_score, umpire_recommendation, 
                    team_ownership, game_info['vegas_total']
                )
                
                integrated_teams[team] = {
                    'base_score': base_score,
                    'integrated_score': integrated_score,
                    'umpire': umpire,
                    'umpire_impact': umpire_multiplier,
                    'umpire_recommendation': umpire_recommendation,
                    'weather': weather,
                    'weather_impact': weather_multiplier,
                    'ownership': team_ownership,
                    'vegas_total': game_info['vegas_total'],
                    'opposing_pitcher': opposing_pitcher,
                    'game': team_game,
                    'final_recommendation': final_recommendation,
                    'reasons': []
                }
                
                # Add specific reasons
                if umpire_multiplier < 0.95:
                    integrated_teams[team]['reasons'].append(f"Umpire concern ({umpire})")
                elif umpire_multiplier > 1.05:
                    integrated_teams[team]['reasons'].append(f"Umpire edge ({umpire})")
                
                if weather_multiplier < 0.95:
                    integrated_teams[team]['reasons'].append(f"Weather concern ({weather})")
                elif weather_multiplier > 1.05:
                    integrated_teams[team]['reasons'].append(f"Weather boost ({weather})")
                
                if team_ownership < 15:
                    integrated_teams[team]['reasons'].append("Low ownership edge")
                elif team_ownership > 25:
                    integrated_teams[team]['reasons'].append("High ownership risk")
        
        return integrated_teams
    
    def get_team_ownership(self, team, ownership_df):
        """Get team ownership percentage"""
        if ownership_df.empty or 'team' not in ownership_df.columns:
            return 20  # Default
        
        team_players = ownership_df[ownership_df['team'] == team]
        if not team_players.empty and 'ownership' in team_players.columns:
            return team_players['ownership'].mean() * 100
        return 20
    
    def determine_recommendation(self, integrated_score, base_score, umpire_rec, ownership, vegas_total):
        """Determine final recommendation based on all factors"""
        
        # Start with umpire recommendation as base
        if umpire_rec == 'AVOID':
            return 'AVOID'
        
        # Strong positive indicators
        if integrated_score > base_score * 1.1 and ownership < 15:
            return 'ELITE_TARGET'
        
        # Good spots
        if integrated_score > base_score * 1.05:
            return 'TARGET'
        
        # Tournament upside
        if umpire_rec == 'TOURNAMENT_UPSIDE' or (ownership < 12 and vegas_total > 8.5):
            return 'TOURNAMENT_UPSIDE'
        
        # Negative indicators
        if integrated_score < base_score * 0.9:
            return 'AVOID'
        
        return 'NEUTRAL'
    
    def print_integrated_summary(self, integrated_data):
        """Print summary of integrated analysis"""
        print(f"\nINTEGRATED STACKING ANALYSIS")
        print(f"=" * 50)
        
        # Sort teams by integrated score
        sorted_teams = sorted(integrated_data.items(), 
                             key=lambda x: x[1]['integrated_score'], reverse=True)
        
        for team, data in sorted_teams[:8]:
            print(f"\n{team} ({data['game']})")
            print(f"   Score: {data['base_score']:.2f} -> {data['integrated_score']:.2f}")
            print(f"   Umpire: {data['umpire']} ({data['umpire_impact']:.2f}x)")
            print(f"   Weather: {data['weather']} ({data['weather_impact']:.2f}x)")
            print(f"   Ownership: {data['ownership']:.1f}%")
            print(f"   Recommendation: {data['final_recommendation']}")
            if data['reasons']:
                print(f"   Reasons: {', '.join(data['reasons'])}")

def main():
    print("INTEGRATED STACKING SYSTEM")
    print("Connecting ALL your data sources for unified decisions")
    print("=" * 60)
    
    system = IntegratedStackingSystem()
    
    # Load and integrate all data
    integrated_data = system.load_integrated_data()
    
    if not integrated_data:
        print("No data available for integration")
        return
    
    # Print summary
    system.print_integrated_summary(integrated_data)
    
    print(f"\nKEY INSIGHTS:")
    print("- Teams with AVOID recommendation should not be stacked")
    print("- ELITE_TARGET teams have multiple positive factors aligned")
    print("- Your dashboard shows these integrations, but lineups don't use them!")
    print("\nNEXT STEP: Connect this analysis to your lineup generators")

if __name__ == "__main__":
    main()
