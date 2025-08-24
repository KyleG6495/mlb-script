#!/usr/bin/env python3
"""
ELITE ADVANCED STACK OPTIMIZER
Integrates all advanced DFS techniques for maximum edge
"""

import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class EliteAdvancedStackOptimizer:
    def __init__(self):
        self.data_dir = "../data"
        self.slate_dir = "../fd_current_slate"
        self.weather_multipliers = self._init_weather_factors()
        self.umpire_database = self._init_umpire_database()
        self.ballpark_factors = self._init_ballpark_factors()
        
    def _init_weather_factors(self):
        """Advanced weather multipliers"""
        return {
            'wind_direction': {
                'out_to_left': 1.15,      # Helps right-handed hitters
                'out_to_right': 1.15,     # Helps left-handed hitters  
                'in_from_left': 0.95,     # Hurts right-handed hitters
                'in_from_right': 0.95,    # Hurts left-handed hitters
                'cross_wind': 1.02        # Slight help to all
            },
            'humidity': {
                'low': 1.08,              # Ball travels further in dry air
                'medium': 1.0,
                'high': 0.94              # Heavy air slows ball down
            },
            'barometric_pressure': {
                'low': 1.12,              # Low pressure = ball flies
                'normal': 1.0,
                'high': 0.92              # High pressure = ball dies
            },
            'temperature_ranges': {
                'cold': {'under_50': 0.85, '50_60': 0.92},
                'ideal': {'70_80': 1.08, '80_85': 1.05},
                'hot': {'85_90': 1.02, 'over_90': 0.98}
            }
        }
    
    def _init_umpire_database(self):
        """Umpire tendencies database"""
        return {
            'Angel Hernandez': {
                'zone_type': 'inconsistent_wide',
                'runs_per_game_impact': 0.92,
                'pitcher_friendly': True,
                'avoid_factor': 0.85
            },
            'Joe West': {
                'zone_type': 'tight_consistent', 
                'runs_per_game_impact': 1.08,
                'hitter_friendly': True,
                'target_factor': 1.12
            },
            'CB Bucknor': {
                'zone_type': 'inconsistent',
                'runs_per_game_impact': 1.05,
                'variance_boost': 1.15,
                'tournament_factor': 1.10
            },
            'Ron Kulpa': {
                'zone_type': 'tight',
                'runs_per_game_impact': 1.06,
                'walk_boost': 1.15,
                'hitter_friendly': True
            }
        }
    
    def _init_ballpark_factors(self):
        """Ballpark-specific edge factors"""
        return {
            'Coors Field': {'altitude_boost': 1.25, 'wind_factor': 1.12},
            'Yankee Stadium': {'short_porch': 1.12, 'lefty_boost': 1.15},
            'Fenway Park': {'green_monster': 1.08, 'righty_boost': 1.10},
            'Minute Maid Park': {'crawford_boxes': 1.18, 'tal_hill': 0.95},
            'Progressive Field': {'underrated_hitter_park': 1.06},
            'Great American Ball Park': {'wind_tunnel': 1.08},
            'Globe Life Field': {'retractable_roof': 1.04},
            'Tropicana Field': {'indoor_advantage': 1.02}
        }

    def load_slate_data(self):
        """Load today's slate data"""
        try:
            # Use clean slate (injured players removed)
            clean_slate_file = f"{self.slate_dir}/fd_slate_today_clean.csv"
            slate_file = f"{self.slate_dir}/fd_slate_today.csv"
            
            if os.path.exists(clean_slate_file):
                slate_path = clean_slate_file
                print(f"✅ Using clean slate: {clean_slate_file}")
            else:
                slate_path = slate_file
                print(f"⚠️ Using original slate: {slate_file}")
            if os.path.exists(slate_file):
                return pd.read_csv(slate_file)
            else:
                print("⚠️ No slate data found - run data pipeline first")
                return None
        except Exception as e:
            print(f"❌ Error loading slate: {e}")
            return None

    def analyze_umpire_edge(self, game_info):
        """Analyze umpire impact for each game"""
        umpire_analysis = {}
        
        # Mock umpire assignments (in production, scrape from MLB.com)
        mock_umps = {
            'BOS @ NYY': 'Joe West',
            'HOU @ BAL': 'Angel Hernandez',
            'WSH @ NYM': 'CB Bucknor', 
            'STL @ SF': 'Ron Kulpa',
            'TB @ SD': 'Default Ump'
        }
        
        for game, umpire in mock_umps.items():
            if umpire in self.umpire_database:
                ump_data = self.umpire_database[umpire]
                umpire_analysis[game] = {
                    'umpire': umpire,
                    'impact_factor': ump_data.get('runs_per_game_impact', 1.0),
                    'pitcher_friendly': ump_data.get('pitcher_friendly', False),
                    'hitter_friendly': ump_data.get('hitter_friendly', False),
                    'variance_boost': ump_data.get('variance_boost', 1.0),
                    'recommendation': self._get_umpire_recommendation(ump_data)
                }
            else:
                umpire_analysis[game] = {
                    'umpire': umpire,
                    'impact_factor': 1.0,
                    'recommendation': 'NEUTRAL'
                }
        
        return umpire_analysis

    def _get_umpire_recommendation(self, ump_data):
        """Get recommendation based on umpire data"""
        if ump_data.get('avoid_factor', 1.0) < 0.9:
            return 'AVOID'
        elif ump_data.get('target_factor', 1.0) > 1.1:
            return 'TARGET'
        elif ump_data.get('variance_boost', 1.0) > 1.1:
            return 'TOURNAMENT_UPSIDE'
        else:
            return 'NEUTRAL'

    def calculate_leverage_scores(self, slate_df):
        """Calculate leverage (ceiling/ownership) for all players"""
        leverage_scores = {}
        
        for _, player in slate_df.iterrows():
            # Mock ownership prediction (in production, use ML model)
            predicted_ownership = self._predict_ownership(player)
            
            # Mock ceiling calculation (in production, use advanced projections)
            ceiling_projection = self._calculate_ceiling(player)
            
            leverage_score = ceiling_projection / predicted_ownership if predicted_ownership > 0 else 0
            
            leverage_scores[player['Nickname']] = {
                'ceiling': ceiling_projection,
                'predicted_ownership': predicted_ownership,
                'leverage_score': leverage_score,
                'recommendation': self._get_leverage_recommendation(leverage_score)
            }
        
        return leverage_scores

    def _predict_ownership(self, player):
        """Predict player ownership percentage"""
        base_ownership = 8.0  # Base ownership
        
        # Adjust for salary (higher salary = lower ownership)
        salary_factor = max(0.3, (12000 - player['Salary']) / 12000)
        
        # Adjust for projection (higher projection = higher ownership)
        projection_factor = min(2.0, player['FPPG'] / 10.0)
        
        # Adjust for team popularity
        popular_teams = ['NYY', 'BOS', 'LAD', 'HOU']
        team_factor = 1.3 if player['Team'] in popular_teams else 1.0
        
        predicted_ownership = base_ownership * salary_factor * projection_factor * team_factor
        return min(25.0, max(2.0, predicted_ownership))

    def _calculate_ceiling(self, player):
        """Calculate player ceiling projection"""
        base_projection = player['FPPG']
        
        # Position-based ceiling multipliers
        position_multipliers = {
            'P': 1.8,   # Pitchers have high ceiling variance
            'C': 1.4,   # Catchers moderate ceiling
            '1B': 1.6,  # Power positions
            '2B': 1.4,  # Contact positions
            '3B': 1.6,  # Power positions
            'SS': 1.5,  # Balanced
            'OF': 1.5   # Balanced
        }
        
        position = player['Position']
        multiplier = position_multipliers.get(position, 1.5)
        
        ceiling = base_projection * multiplier
        return round(ceiling, 1)

    def _get_leverage_recommendation(self, leverage_score):
        """Get recommendation based on leverage score"""
        if leverage_score >= 4.0:
            return 'ELITE_LEVERAGE'
        elif leverage_score >= 2.5:
            return 'GOOD_LEVERAGE'
        elif leverage_score >= 1.8:
            return 'PLAYABLE'
        else:
            return 'AVOID_CHALK'

    def analyze_correlation_opportunities(self, slate_df):
        """Find correlation opportunities"""
        correlations = {}
        
        # Team stacking correlations
        for team in slate_df['Team'].unique():
            team_players = slate_df[slate_df['Team'] == team]
            
            correlations[team] = {
                'players_available': len(team_players),
                'stack_potential': self._calculate_stack_potential(team_players),
                'correlation_factors': self._get_team_correlation_factors(team)
            }
        
        return correlations

    def _calculate_stack_potential(self, team_players):
        """Calculate team stack potential"""
        avg_projection = team_players['FPPG'].mean()
        player_count = len(team_players)
        salary_efficiency = team_players['FPPG'].sum() / team_players['Salary'].sum() * 1000
        
        # Normalize to 1-10 scale
        potential_score = (avg_projection * 0.4 + player_count * 0.3 + salary_efficiency * 0.3) / 2
        return round(min(10.0, max(1.0, potential_score)), 1)

    def _get_team_correlation_factors(self, team):
        """Get team-specific correlation factors"""
        return {
            'offensive_consistency': np.random.uniform(0.8, 1.2),  # Mock data
            'ballpark_boost': self.ballpark_factors.get(f"{team} Home", {}).get('boost', 1.0),
            'recent_form': np.random.uniform(0.9, 1.1)  # Mock data
        }

    def generate_advanced_stack_analysis(self):
        """Generate comprehensive stack analysis with all advanced factors"""
        print("🚀 ELITE ADVANCED STACK OPTIMIZER")
        print("=" * 50)
        
        # Load data
        slate_df = self.load_slate_data()
        if slate_df is None:
            return None
        
        print(f"✅ Loaded slate data: {len(slate_df)} players")
        
        # Analyze umpire edge
        print("\n⚾ UMPIRE ANALYSIS:")
        print("-" * 20)
        umpire_analysis = self.analyze_umpire_edge(slate_df)
        for game, data in umpire_analysis.items():
            rec_icon = "🎯" if data['recommendation'] == 'TARGET' else "⚠️" if data['recommendation'] == 'AVOID' else "📊"
            print(f"{rec_icon} {game}: {data['umpire']} ({data['recommendation']})")
            print(f"   Impact: {data['impact_factor']:.2f}x scoring")
        
        # Calculate leverage scores
        print("\n📊 LEVERAGE ANALYSIS:")
        print("-" * 20)
        leverage_scores = self.calculate_leverage_scores(slate_df)
        
        # Sort by leverage score
        sorted_leverage = sorted(leverage_scores.items(), key=lambda x: x[1]['leverage_score'], reverse=True)
        
        for i, (player, data) in enumerate(sorted_leverage[:10]):
            rec_icon = "🎯" if data['recommendation'] == 'ELITE_LEVERAGE' else "📈" if data['recommendation'] == 'GOOD_LEVERAGE' else "📊"
            print(f"{rec_icon} {player}: {data['leverage_score']:.1f} leverage")
            print(f"   Ceiling: {data['ceiling']} | Ownership: {data['predicted_ownership']:.1f}%")
        
        # Analyze correlations
        print("\n🔗 CORRELATION OPPORTUNITIES:")
        print("-" * 30)
        correlations = self.analyze_correlation_opportunities(slate_df)
        
        sorted_correlations = sorted(correlations.items(), key=lambda x: x[1]['stack_potential'], reverse=True)
        
        for team, data in sorted_correlations[:8]:
            potential_icon = "🔥" if data['stack_potential'] >= 7 else "📈" if data['stack_potential'] >= 5 else "📊"
            print(f"{potential_icon} {team}: {data['stack_potential']}/10 stack potential")
            print(f"   Players: {data['players_available']} | Factors: {len(data['correlation_factors'])}")
        
        # Generate recommendations
        print("\n🎯 TOP RECOMMENDATIONS:")
        print("-" * 25)
        self._generate_final_recommendations(leverage_scores, correlations, umpire_analysis)
        
        return {
            'leverage_scores': leverage_scores,
            'correlations': correlations,
            'umpire_analysis': umpire_analysis
        }

    def _generate_final_recommendations(self, leverage_scores, correlations, umpire_analysis):
        """Generate final recommendations combining all factors"""
        
        # Find top leverage plays
        top_leverage = sorted(leverage_scores.items(), key=lambda x: x[1]['leverage_score'], reverse=True)[:5]
        
        print("💎 ELITE LEVERAGE PLAYS:")
        for player, data in top_leverage:
            if data['recommendation'] in ['ELITE_LEVERAGE', 'GOOD_LEVERAGE']:
                print(f"  • {player} ({data['leverage_score']:.1f} leverage)")
        
        # Find best stacking opportunities
        top_stacks = sorted(correlations.items(), key=lambda x: x[1]['stack_potential'], reverse=True)[:3]
        
        print("\n🔗 ELITE STACK TARGETS:")
        for team, data in top_stacks:
            print(f"  • {team} Stack ({data['stack_potential']}/10 potential)")
        
        # Umpire-based recommendations
        target_games = [game for game, data in umpire_analysis.items() if data['recommendation'] == 'TARGET']
        if target_games:
            print(f"\n⚾ UMPIRE EDGE GAMES:")
            for game in target_games:
                print(f"  • {game} (Umpire edge)")

def main():
    optimizer = EliteAdvancedStackOptimizer()
    results = optimizer.generate_advanced_stack_analysis()
    
    if results:
        # Save results for dashboard integration
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"../data/advanced_stack_analysis_{timestamp}.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {output_file}")
        print("\n🚀 Ready to integrate with your dashboard!")

if __name__ == "__main__":
    main()
