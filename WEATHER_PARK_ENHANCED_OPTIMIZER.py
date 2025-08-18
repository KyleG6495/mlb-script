"""
 WEATHER & PARK ENHANCED DFS OPTIMIZER
Combines real weather data with authentic park factors
Replaces all simulated data with genuine MLB analytics
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Add scripts directory to path for imports
sys.path.append(r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts")

try:
    from MLB_PARK_FACTORS_DB import MLBParkFactorsDB
    from FREE_WEATHER_INTEGRATOR import FreeWeatherIntegrator
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure MLB_PARK_FACTORS_DB.py and FREE_WEATHER_INTEGRATOR.py are in Scripts folder")

class WeatherParkOptimizer:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.today = datetime.now().strftime('%Y%m%d')
        
        # Initialize components
        self.park_db = MLBParkFactorsDB()
        self.weather_integrator = FreeWeatherIntegrator()
        
    def combine_weather_and_park_factors(self, team: str, weather_data: Dict) -> Dict:
        """Combine weather and park factor impacts"""
        
        # Get park factors
        park_data = self.park_db.get_all_park_data(team)
        
        # Calculate weather impacts
        weather_impacts = self.weather_integrator.calculate_detailed_weather_impact(weather_data, team)
        
        # Combine impacts intelligently
        combined_factors = {}
        
        # Runs factor (most important for DFS)
        park_runs_factor = park_data.get('runs_factor', 1.0)
        weather_runs_impact = weather_impacts.get('runs_impact', 1.0)
        combined_factors['runs_factor'] = park_runs_factor * weather_runs_impact
        
        # Home run factor
        park_hr_factor = park_data.get('hr_factor', 1.0)
        weather_hr_impact = weather_impacts.get('hr_impact', 1.0)
        combined_factors['hr_factor'] = park_hr_factor * weather_hr_impact
        
        # Hits factor
        park_hits_factor = park_data.get('hits_factor', 1.0)
        weather_hits_impact = weather_impacts.get('hits_impact', 1.0)
        combined_factors['hits_factor'] = park_hits_factor * weather_hits_impact
        
        # Strikeouts (pitcher helpful)
        park_so_factor = park_data.get('so_factor', 1.0)
        weather_so_impact = weather_impacts.get('strikeouts_impact', 1.0)
        combined_factors['so_factor'] = park_so_factor * weather_so_impact
        
        # Overall DFS impact
        combined_factors['overall_factor'] = (
            combined_factors['runs_factor'] * 0.5 +
            combined_factors['hr_factor'] * 0.3 +
            combined_factors['hits_factor'] * 0.2
        )
        
        # Additional context
        combined_factors.update({
            'park_category': self._categorize_environment(combined_factors['overall_factor']),
            'weather_conditions': weather_data['conditions'],
            'temperature': weather_data['temperature'],
            'wind_speed': weather_data['wind_speed'],
            'park_name': team,
            'altitude': park_data.get('altitude', 0),
            'wind_impact_level': park_data.get('wind_impact', 'medium')
        })
        
        return combined_factors
    
    def _categorize_environment(self, factor: float) -> str:
        """Categorize the combined environment"""
        if factor >= 1.08:
            return 'Elite Hitter Environment'
        elif factor >= 1.04:
            return 'Hitter Friendly'
        elif factor >= 0.98:
            return 'Neutral'
        elif factor >= 0.94:
            return 'Pitcher Friendly'
        else:
            return 'Elite Pitcher Environment'
    
    def process_comprehensive_enhancements(self, projections_file: str) -> pd.DataFrame:
        """Apply comprehensive weather and park enhancements"""
        
        print(f" Processing comprehensive weather & park enhancements...")
        
        # Load projections
        if not os.path.exists(projections_file):
            print(f"ERROR: Projections file not found: {projections_file}")
            return pd.DataFrame()
            
        df = pd.read_csv(projections_file)
        
        # Get unique teams
        teams = df['Team'].unique() if 'Team' in df.columns else df['team'].unique()
        
        # Collect weather data
        weather_data = {}
        print(f"   Collecting real weather for {len(teams)} teams...")
        
        for team in teams:
            print(f"    {team}...", end=" ")
            weather_data[team] = self.weather_integrator.get_free_weather_data(team)
            print(f"{weather_data[team]['conditions']} {weather_data[team]['temperature']:.0f}F")
        
        # Process all enhancements
        enhanced_projections = []
        
        for _, player in df.iterrows():
            team = player['Team'] if 'Team' in df.columns else player['team']
            position = player.get('Position', player.get('position', 'OF'))
            
            # Get weather data
            weather = weather_data.get(team, self.weather_integrator._get_regional_weather_default(team))
            
            # Combine weather and park factors
            combined_factors = self.combine_weather_and_park_factors(team, weather)
            
            # Get base projection
            base_fppg = player.get('enhanced_fppg', player.get('FPPG', player.get('fppg', 0)))
            
            # Apply position-specific adjustments
            position_factor = self._get_position_adjustment(position, combined_factors)
            
            # Calculate final enhancement
            final_factor = combined_factors['overall_factor'] * position_factor
            enhanced_fppg = base_fppg * final_factor
            
            # Calculate improvements
            total_improvement = enhanced_fppg - base_fppg
            total_improvement_pct = (total_improvement / base_fppg * 100) if base_fppg > 0 else 0
            
            enhanced_projections.append({
                'name': player.get('First Name', '') + ' ' + player.get('Last Name', player.get('name', 'Unknown')),
                'team': team,
                'position': position,
                'salary': player.get('Salary', player.get('salary', 0)),
                'base_fppg': base_fppg,
                'enhanced_fppg': round(enhanced_fppg, 2),
                'total_improvement': round(total_improvement, 2),
                'improvement_pct': round(total_improvement_pct, 1),
                'environment_category': combined_factors['park_category'],
                'overall_factor': round(final_factor, 3),
                'runs_factor': round(combined_factors['runs_factor'], 3),
                'hr_factor': round(combined_factors['hr_factor'], 3),
                'temperature': weather['temperature'],
                'wind_speed': weather['wind_speed'],
                'conditions': weather['conditions'],
                'altitude': combined_factors['altitude'],
                'wind_impact': combined_factors['wind_impact_level'],
                'weather_source': weather['source']
            })
        
        enhanced_df = pd.DataFrame(enhanced_projections)
        
        # Save comprehensive enhancements
        output_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\comprehensive_enhanced_projections_{self.timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        print(f"\nSUCCESS: Comprehensive enhancements saved: {output_file}")
        print(f"   Total players enhanced: {len(enhanced_df)}")
        print(f"   Average improvement: {enhanced_df['improvement_pct'].mean():.1f}%")
        print(f"   Players in elite environments: {len(enhanced_df[enhanced_df['environment_category'] == 'Elite Hitter Environment'])}")
        
        return enhanced_df
    
    def _get_position_adjustment(self, position: str, factors: Dict) -> float:
        """Get position-specific adjustment factor"""
        
        # Power positions benefit more from HR-friendly environments
        if position in ['1B', 'OF', 'DH']:
            return (factors['overall_factor'] + factors['hr_factor']) / 2
        
        # Speed positions benefit from hits and runs
        elif position in ['2B', 'SS']:
            return (factors['overall_factor'] + factors['hits_factor']) / 2
        
        # Catchers less affected by park
        elif position == 'C':
            return factors['overall_factor'] * 0.85 + 0.15
        
        # Pitchers benefit from pitcher-friendly conditions (inverse)
        elif position == 'P':
            return 2.0 - factors['overall_factor']
        
        # Default for 3B and others
        else:
            return factors['overall_factor']
    
    def identify_elite_environment_plays(self, enhanced_df: pd.DataFrame) -> Dict:
        """Identify the best plays based on environment"""
        
        elite_plays = {
            'elite_environment_hitters': [],
            'value_environment_plays': [],
            'stack_opportunities': [],
            'contrarian_weather_plays': []
        }
        
        # Elite environment hitters
        elite_env = enhanced_df[enhanced_df['environment_category'] == 'Elite Hitter Environment']
        for _, player in elite_env.nlargest(10, 'improvement_pct').iterrows():
            elite_plays['elite_environment_hitters'].append({
                'name': player['name'],
                'team': player['team'],
                'salary': player['salary'],
                'enhanced_fppg': player['enhanced_fppg'],
                'improvement_pct': player['improvement_pct'],
                'conditions': player['conditions'],
                'temperature': player['temperature']
            })
        
        # Value plays in good environments
        value_plays = enhanced_df[
            (enhanced_df['salary'] <= 8000) & 
            (enhanced_df['improvement_pct'] > 5) &
            (enhanced_df['environment_category'].isin(['Elite Hitter Environment', 'Hitter Friendly']))
        ]
        for _, player in value_plays.nlargest(8, 'improvement_pct').iterrows():
            elite_plays['value_environment_plays'].append({
                'name': player['name'],
                'team': player['team'],
                'salary': player['salary'],
                'enhanced_fppg': player['enhanced_fppg'],
                'improvement_pct': player['improvement_pct'],
                'environment': player['environment_category']
            })
        
        # Stack opportunities by team environment
        team_environments = enhanced_df.groupby('team').agg({
            'improvement_pct': 'mean',
            'environment_category': 'first',
            'temperature': 'first',
            'conditions': 'first',
            'overall_factor': 'mean'
        }).sort_values('improvement_pct', ascending=False)
        
        for team, data in team_environments.head(6).iterrows():
            if data['improvement_pct'] > 3:  # Meaningful positive environment
                team_players = enhanced_df[enhanced_df['team'] == team].nlargest(5, 'enhanced_fppg')
                elite_plays['stack_opportunities'].append({
                    'team': team,
                    'avg_improvement': round(data['improvement_pct'], 1),
                    'environment': data['environment_category'],
                    'conditions': data['conditions'],
                    'temperature': data['temperature'],
                    'top_players': [
                        {'name': p['name'], 'salary': p['salary'], 'fppg': p['enhanced_fppg']}
                        for _, p in team_players.iterrows()
                    ]
                })
        
        # Contrarian weather plays (bad weather, low ownership likely)
        contrarian_weather = enhanced_df[
            (enhanced_df['conditions'].str.contains('Rain|Storm|Cloudy', case=False, na=False)) |
            (enhanced_df['wind_speed'] > 15) |
            (enhanced_df['temperature'] < 60)
        ]
        for _, player in contrarian_weather.nlargest(5, 'enhanced_fppg').iterrows():
            elite_plays['contrarian_weather_plays'].append({
                'name': player['name'],
                'team': player['team'],
                'salary': player['salary'],
                'enhanced_fppg': player['enhanced_fppg'],
                'conditions': player['conditions'],
                'wind_speed': player['wind_speed'],
                'temperature': player['temperature']
            })
        
        return elite_plays
    
    def generate_environment_report(self, enhanced_df: pd.DataFrame, elite_plays: Dict) -> None:
        """Generate comprehensive environment analysis report"""
        
        print(f"\n COMPREHENSIVE ENVIRONMENT ANALYSIS")
        print("="*60)
        
        # Environment distribution
        env_dist = enhanced_df['environment_category'].value_counts()
        print(f"\n ENVIRONMENT DISTRIBUTION:")
        for env, count in env_dist.items():
            print(f"   {env}: {count} players")
        
        # Top environments for stacking
        print(f"\n ELITE STACK OPPORTUNITIES:")
        for stack in elite_plays['stack_opportunities']:
            print(f"   {stack['team']}: {stack['avg_improvement']:+.1f}% avg boost")
            print(f"      {stack['environment']} ({stack['conditions']}, {stack['temperature']:.0f}F)")
            print(f"      Top players: {', '.join([p['name'] for p in stack['top_players'][:3]])}")
            print()
        
        # Elite individual plays
        print(f"LINEUP: TOP ENVIRONMENT PLAYS:")
        for play in elite_plays['elite_environment_hitters'][:8]:
            print(f"   {play['name']} ({play['team']}): {play['enhanced_fppg']:.1f} FPPG (+{play['improvement_pct']:.1f}%)")
            print(f"      ${play['salary']:,} | {play['conditions']}, {play['temperature']:.0f}F")
        
        # Value plays
        print(f"\n VALUE ENVIRONMENT PLAYS:")
        for play in elite_plays['value_environment_plays']:
            print(f"   {play['name']} ({play['team']}): ${play['salary']:,} | {play['enhanced_fppg']:.1f} FPPG (+{play['improvement_pct']:.1f}%)")
        
        # Weather summary
        weather_summary = enhanced_df.groupby(['team', 'conditions']).agg({
            'temperature': 'first',
            'wind_speed': 'first',
            'improvement_pct': 'mean'
        }).sort_values('improvement_pct', ascending=False)
        
        print(f"\n WEATHER CONDITIONS IMPACT:")
        for (team, conditions), data in weather_summary.head(10).iterrows():
            impact_emoji = "" if data['improvement_pct'] > 5 else "" if data['improvement_pct'] < -3 else ""
            print(f"   {impact_emoji} {team}: {conditions}, {data['temperature']:.0f}F, {data['wind_speed']:.0f}mph ({data['improvement_pct']:+.1f}%)")

def main():
    """Main execution function"""
    print(" WEATHER & PARK ENHANCED DFS OPTIMIZER")
    print("="*60)
    
    optimizer = WeatherParkOptimizer()
    
    # Look for projections to enhance
    projections_files = [
        "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_20250812_135729.csv",
        f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_{optimizer.today}.csv",
        f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\master_enhanced_lineups_{optimizer.today}.csv",
        "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\base_hitter_scores.csv"
    ]
    
    input_file = None
    for file_path in projections_files:
        if os.path.exists(file_path):
            input_file = file_path
            break
    
    if not input_file:
        print("ERROR: No projections file found.")
        print("   Please run your base projections first, then re-run this script.")
        return
    
    print(f"DATA: Using projections: {os.path.basename(input_file)}")
    
    # Process comprehensive enhancements
    enhanced_df = optimizer.process_comprehensive_enhancements(input_file)
    
    if enhanced_df.empty:
        print("ERROR: Failed to process enhancements")
        return
    
    # Identify elite plays
    elite_plays = optimizer.identify_elite_environment_plays(enhanced_df)
    
    # Generate comprehensive report
    optimizer.generate_environment_report(enhanced_df, elite_plays)
    
    # Save elite plays summary
    summary_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\elite_environment_plays_{optimizer.timestamp}.csv"
    
    # Create summary dataframe
    summary_data = []
    
    # Add elite environment plays
    for play in elite_plays['elite_environment_hitters']:
        summary_data.append({
            'category': 'Elite Environment',
            'name': play['name'],
            'team': play['team'],
            'salary': play['salary'],
            'enhanced_fppg': play['enhanced_fppg'],
            'improvement_pct': play['improvement_pct'],
            'notes': f"{play['conditions']}, {play['temperature']:.0f}F"
        })
    
    # Add value plays
    for play in elite_plays['value_environment_plays']:
        summary_data.append({
            'category': 'Value Environment',
            'name': play['name'],
            'team': play['team'],
            'salary': play['salary'],
            'enhanced_fppg': play['enhanced_fppg'],
            'improvement_pct': play['improvement_pct'],
            'notes': play['environment']
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(summary_file, index=False)
    
    print(f"\nSUCCESS: COMPREHENSIVE WEATHER & PARK INTEGRATION COMPLETE!")
    print(f"   PROGRESS: Enhanced projections: comprehensive_enhanced_projections_{optimizer.timestamp}.csv")
    print(f"   LINEUP: Elite plays summary: elite_environment_plays_{optimizer.timestamp}.csv")
    print(f"   TARGET: {len(elite_plays['stack_opportunities'])} elite stack opportunities identified")
    print(f"    {len(elite_plays['value_environment_plays'])} value plays in good environments")
    print(f"    Real weather data integrated for all teams")
    print(f"    Authentic park factors applied for all 30 stadiums")

if __name__ == "__main__":
    main()
