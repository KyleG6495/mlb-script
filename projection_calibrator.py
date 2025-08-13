#!/usr/bin/env python3
"""
PROJECTION CALIBRATION SYSTEM
Fine-tunes projections based on backtest insights
"""

import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

class ProjectionCalibrator:
    """Calibrate projections based on actual performance"""
    
    def __init__(self):
        self.position_factors = {}
        self.salary_factors = {}
        self.team_factors = {}
        self.global_factor = 1.0
        
    def analyze_projection_accuracy(self, lineups_df, actual_df):
        """Analyze how far off projections are by various factors"""
        
        print("📊 PROJECTION ACCURACY ANALYSIS")
        print("=" * 40)
        
        # Enhanced player matching for analysis
        from enhanced_player_matcher import EnhancedPlayerMatcher
        matcher = EnhancedPlayerMatcher()
        actual_names = actual_df['name'].tolist()
        
        analysis_data = []
        
        for _, player in lineups_df.iterrows():
            # Find matching actual player
            best_match, score = matcher.find_best_match(
                player['player_name'], actual_names, min_similarity=0.7
            )
            
            if best_match and score >= 0.7:
                actual_player = actual_df[actual_df['name'] == best_match].iloc[0]
                
                analysis_data.append({
                    'player_name': player['player_name'],
                    'position': player['position'],
                    'team': player['team'],
                    'salary': player['salary'],
                    'projected_fppg': player['projected_fppg'],
                    'actual_fppg': actual_player['fanduel_points'],
                    'projection_error': player['projected_fppg'] - actual_player['fanduel_points'],
                    'projection_ratio': player['projected_fppg'] / max(actual_player['fanduel_points'], 0.1)
                })
        
        if not analysis_data:
            print("❌ No matching players found for analysis")
            return None
            
        df = pd.DataFrame(analysis_data)
        print(f"✅ Analyzed {len(df)} matched players")
        
        return df
    
    def calculate_calibration_factors(self, analysis_df):
        """Calculate calibration factors by position, salary, team"""
        
        print("\n🔧 CALCULATING CALIBRATION FACTORS")
        print("-" * 40)
        
        # Global calibration factor
        overall_projected = analysis_df['projected_fppg'].mean()
        overall_actual = analysis_df['actual_fppg'].mean()
        self.global_factor = overall_actual / overall_projected if overall_projected > 0 else 1.0
        
        print(f"📊 Overall Stats:")
        print(f"   Average Projected: {overall_projected:.1f} FPPG")
        print(f"   Average Actual: {overall_actual:.1f} FPPG")
        print(f"   Global Factor: {self.global_factor:.3f}")
        
        # Position-based factors
        print(f"\n🏈 Position Calibration:")
        position_stats = analysis_df.groupby('position').agg({
            'projected_fppg': 'mean',
            'actual_fppg': 'mean',
            'player_name': 'count'
        }).round(2)
        
        for pos in position_stats.index:
            if position_stats.loc[pos, 'projected_fppg'] > 0:
                factor = position_stats.loc[pos, 'actual_fppg'] / position_stats.loc[pos, 'projected_fppg']
                self.position_factors[pos] = factor
                count = position_stats.loc[pos, 'player_name']
                print(f"   {pos}: {factor:.3f} (n={count})")
        
        # Salary-based factors (create tiers)
        analysis_df['salary_tier'] = pd.cut(analysis_df['salary'], 
                                          bins=[0, 3000, 5000, 8000, 12000], 
                                          labels=['Low', 'Mid', 'High', 'Elite'])
        
        print(f"\n💰 Salary Tier Calibration:")
        salary_stats = analysis_df.groupby('salary_tier').agg({
            'projected_fppg': 'mean',
            'actual_fppg': 'mean',
            'player_name': 'count'
        }).round(2)
        
        for tier in salary_stats.index:
            if pd.notna(tier) and salary_stats.loc[tier, 'projected_fppg'] > 0:
                factor = salary_stats.loc[tier, 'actual_fppg'] / salary_stats.loc[tier, 'projected_fppg']
                self.salary_factors[tier] = factor
                count = salary_stats.loc[tier, 'player_name']
                print(f"   {tier}: {factor:.3f} (n={count})")
        
        # Team performance factors
        print(f"\n⚾ Team Performance Factors:")
        team_stats = analysis_df.groupby('team').agg({
            'projected_fppg': 'mean',
            'actual_fppg': 'mean',
            'player_name': 'count'
        }).round(2)
        
        # Only show teams with 2+ players
        significant_teams = team_stats[team_stats['player_name'] >= 2]
        for team in significant_teams.index:
            if significant_teams.loc[team, 'projected_fppg'] > 0:
                factor = significant_teams.loc[team, 'actual_fppg'] / significant_teams.loc[team, 'projected_fppg']
                self.team_factors[team] = factor
                count = significant_teams.loc[team, 'player_name']
                print(f"   {team}: {factor:.3f} (n={count})")
        
        return analysis_df
    
    def apply_calibration(self, player_data):
        """Apply calibration factors to a player's projection"""
        
        calibrated_projection = player_data['projected_fppg']
        
        # Apply global factor
        calibrated_projection *= self.global_factor
        
        # Apply position factor
        if player_data['position'] in self.position_factors:
            calibrated_projection *= self.position_factors[player_data['position']]
        
        # Apply salary tier factor
        salary = player_data['salary']
        if salary <= 3000:
            tier = 'Low'
        elif salary <= 5000:
            tier = 'Mid'
        elif salary <= 8000:
            tier = 'High'
        else:
            tier = 'Elite'
            
        if tier in self.salary_factors:
            calibrated_projection *= self.salary_factors[tier]
        
        # Apply team factor
        if player_data['team'] in self.team_factors:
            calibrated_projection *= self.team_factors[player_data['team']]
        
        return max(calibrated_projection, 0.1)  # Minimum 0.1 FPPG
    
    def save_calibration_model(self, filename=None):
        """Save calibration factors for future use"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/projection_calibration_{timestamp}.csv"
        
        calibration_data = {
            'type': [],
            'category': [],
            'factor': []
        }
        
        # Global factor
        calibration_data['type'].append('global')
        calibration_data['category'].append('all')
        calibration_data['factor'].append(self.global_factor)
        
        # Position factors
        for pos, factor in self.position_factors.items():
            calibration_data['type'].append('position')
            calibration_data['category'].append(pos)
            calibration_data['factor'].append(factor)
        
        # Salary factors
        for tier, factor in self.salary_factors.items():
            calibration_data['type'].append('salary')
            calibration_data['category'].append(tier)
            calibration_data['factor'].append(factor)
        
        # Team factors
        for team, factor in self.team_factors.items():
            calibration_data['type'].append('team')
            calibration_data['category'].append(team)
            calibration_data['factor'].append(factor)
        
        calibration_df = pd.DataFrame(calibration_data)
        calibration_df.to_csv(filename, index=False)
        print(f"\n💾 Calibration model saved: {filename}")
        
        return filename

def run_projection_calibration():
    """Run the complete projection calibration process"""
    
    print("🎯 PROJECTION CALIBRATION SYSTEM")
    print("=" * 50)
    
    # Load data
    lineup_file = "../data/final_tournament_lineups_details_20250809_121538.csv"
    results_file = "../data/actual_results_20250809.csv"
    
    lineups_df = pd.read_csv(lineup_file)
    actual_df = pd.read_csv(results_file)
    
    # Initialize calibrator
    calibrator = ProjectionCalibrator()
    
    # Analyze projections
    analysis_df = calibrator.analyze_projection_accuracy(lineups_df, actual_df)
    
    if analysis_df is not None:
        # Calculate calibration factors
        calibrator.calculate_calibration_factors(analysis_df)
        
        # Save calibration model
        model_file = calibrator.save_calibration_model()
        
        # Test calibration on sample players
        print(f"\n🧪 TESTING CALIBRATED PROJECTIONS:")
        print("-" * 40)
        
        sample_players = analysis_df.head(5)
        for _, player in sample_players.iterrows():
            original = player['projected_fppg']
            calibrated = calibrator.apply_calibration(player)
            actual = player['actual_fppg']
            
            print(f"{player['player_name']:20} | "
                  f"Orig: {original:5.1f} | "
                  f"Cal: {calibrated:5.1f} | "
                  f"Act: {actual:5.1f} | "
                  f"Err: {abs(calibrated - actual):4.1f}")
        
        # Calculate improvement metrics
        original_mae = np.mean(np.abs(analysis_df['projected_fppg'] - analysis_df['actual_fppg']))
        calibrated_projections = analysis_df.apply(calibrator.apply_calibration, axis=1)
        calibrated_mae = np.mean(np.abs(calibrated_projections - analysis_df['actual_fppg']))
        
        improvement = ((original_mae - calibrated_mae) / original_mae) * 100
        
        print(f"\n📈 CALIBRATION IMPROVEMENT:")
        print(f"   Original MAE: {original_mae:.2f}")
        print(f"   Calibrated MAE: {calibrated_mae:.2f}")
        print(f"   Improvement: {improvement:.1f}%")
        
        return calibrator, model_file
    
    return None, None

if __name__ == "__main__":
    run_projection_calibration()
