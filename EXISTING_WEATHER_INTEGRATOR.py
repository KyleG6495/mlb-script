"""
🌤️ WEATHER INTEGRATION USING EXISTING SYSTEM
Uses your existing weather.py infrastructure with real data
"""

import pandas as pd
import numpy as np
import os
import sys
from datetime import datetime
import subprocess

# Add your scripts directory to path
sys.path.append(r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts")

class ExistingWeatherIntegrator:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.today = datetime.now().strftime('%Y%m%d')
        
        # Paths to your existing weather files
        self.weather_script = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\19. build_weather_today.py"
        self.weather_merger = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts\20. merge_weather_and_park_factors.py"
        self.weather_data_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\weather_today.csv"
        self.merged_weather_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\merged_weather_park.csv"
    
    def run_existing_weather_system(self):
        """Run your existing weather data collection"""
        print("🌤️ Running your existing weather data system...")
        
        try:
            # Run the weather data collection script
            print("   Building today's weather data...")
            result = subprocess.run([
                'python', self.weather_script
            ], capture_output=True, text=True, cwd=r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts")
            
            if result.returncode == 0:
                print(f"   ✅ Weather data collected successfully")
                if result.stdout:
                    print(f"      {result.stdout.strip()}")
            else:
                print(f"   ❌ Weather collection failed: {result.stderr}")
                return False
            
            # Run the weather and park factor merger
            print("   Merging weather with park factors...")
            result = subprocess.run([
                'python', self.weather_merger
            ], capture_output=True, text=True, cwd=r"C:\Users\kgone\OneDrive\Personal_Information\MLB\Scripts")
            
            if result.returncode == 0:
                print(f"   ✅ Weather and park factors merged successfully")
                if result.stdout:
                    print(f"      {result.stdout.strip()}")
            else:
                print(f"   ❌ Weather merge failed: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            print(f"   ❌ Error running weather system: {e}")
            return False
    
    def integrate_weather_with_projections(self, projections_file: str):
        """Integrate weather data with your projections"""
        print(f"\n🏟️ Integrating weather data with projections...")
        
        # Load projections
        if not os.path.exists(projections_file):
            print(f"❌ Projections file not found: {projections_file}")
            return None
            
        df_proj = pd.read_csv(projections_file)
        
        # Load weather data
        if os.path.exists(self.merged_weather_file):
            df_weather = pd.read_csv(self.merged_weather_file)
            print(f"   Using merged weather and park data: {len(df_weather)} records")
        elif os.path.exists(self.weather_data_file):
            df_weather = pd.read_csv(self.weather_data_file)
            print(f"   Using weather data only: {len(df_weather)} records")
        else:
            print(f"❌ No weather data found. Please run weather collection first.")
            return None
        
        # Check the structure of your weather data
        print(f"   Weather data columns: {list(df_weather.columns)}")
        
        # Map team names for merging
        team_mapping = self._get_team_mapping()
        
        # Standardize team names in projections
        team_col = 'Team' if 'Team' in df_proj.columns else 'team'
        df_proj['team_standard'] = df_proj[team_col].map(team_mapping).fillna(df_proj[team_col])
        
        # Merge weather data - use team_standardized from weather file
        if 'team_standardized' in df_weather.columns:
            weather_merge_col = 'team_standardized'
        elif 'Team' in df_weather.columns:
            weather_merge_col = 'Team'
        elif 'team' in df_weather.columns:
            weather_merge_col = 'team'
        else:
            print(f"   Weather data columns: {list(df_weather.columns)}")
            print("❌ Could not find team column in weather data")
            return None
        
        # Convert both columns to string to avoid type mismatch
        df_proj['team_standard'] = df_proj['team_standard'].astype(str)
        df_weather[weather_merge_col] = df_weather[weather_merge_col].astype(str)
        
        print(f"   Merging on: projections[team_standard] <- weather[{weather_merge_col}]")
        print(f"   Sample projection teams: {df_proj['team_standard'].head().tolist()}")
        print(f"   Sample weather teams: {df_weather[weather_merge_col].head().tolist()}")
        
        # Perform the merge
        enhanced_df = df_proj.merge(
            df_weather, 
            left_on='team_standard', 
            right_on=weather_merge_col, 
            how='left'
        )
        
        print(f"   Merged {len(enhanced_df)} player records with weather data")
        
        # Apply weather adjustments
        enhanced_df = self._apply_weather_adjustments(enhanced_df)
        
        # Save enhanced projections
        output_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\weather_enhanced_projections_{self.timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        print(f"✅ Weather enhanced projections saved: {os.path.basename(output_file)}")
        
        return enhanced_df
    
    def _get_team_mapping(self):
        """Map different team name formats"""
        return {
            'LAA': 'Angels', 'ANA': 'Angels', 'Los Angeles Angels': 'Angels',
            'HOU': 'Astros', 'Houston Astros': 'Astros',
            'OAK': 'Athletics', 'Oakland Athletics': 'Athletics',
            'TOR': 'Blue Jays', 'Toronto Blue Jays': 'Blue Jays',
            'ATL': 'Braves', 'Atlanta Braves': 'Braves',
            'MIL': 'Brewers', 'Milwaukee Brewers': 'Brewers',
            'STL': 'Cardinals', 'St. Louis Cardinals': 'Cardinals',
            'CHC': 'Cubs', 'Chicago Cubs': 'Cubs',
            'ARI': 'Diamondbacks', 'Arizona Diamondbacks': 'Diamondbacks',
            'LAD': 'Dodgers', 'Los Angeles Dodgers': 'Dodgers',
            'SF': 'Giants', 'San Francisco Giants': 'Giants',
            'CLE': 'Guardians', 'Cleveland Guardians': 'Guardians',
            'SEA': 'Mariners', 'Seattle Mariners': 'Mariners',
            'MIA': 'Marlins', 'Miami Marlins': 'Marlins',
            'NYM': 'Mets', 'New York Mets': 'Mets',
            'WSH': 'Nationals', 'WAS': 'Nationals', 'Washington Nationals': 'Nationals',
            'BAL': 'Orioles', 'Baltimore Orioles': 'Orioles',
            'SD': 'Padres', 'San Diego Padres': 'Padres',
            'PHI': 'Phillies', 'Philadelphia Phillies': 'Phillies',
            'PIT': 'Pirates', 'Pittsburgh Pirates': 'Pirates',
            'TEX': 'Rangers', 'Texas Rangers': 'Rangers',
            'TB': 'Rays', 'Tampa Bay Rays': 'Rays',
            'BOS': 'Red Sox', 'Boston Red Sox': 'Red Sox',
            'CIN': 'Reds', 'Cincinnati Reds': 'Reds',
            'COL': 'Rockies', 'Colorado Rockies': 'Rockies',
            'KC': 'Royals', 'Kansas City Royals': 'Royals',
            'DET': 'Tigers', 'Detroit Tigers': 'Tigers',
            'MIN': 'Twins', 'Minnesota Twins': 'Twins',
            'CWS': 'White Sox', 'Chicago White Sox': 'White Sox',
            'NYY': 'Yankees', 'New York Yankees': 'Yankees'
        }
    
    def _apply_weather_adjustments(self, df):
        """Apply weather-based adjustments to projections"""
        print("   Applying weather-based projection adjustments...")
        
        # Get base projection column
        base_fppg_col = None
        for col in ['enhanced_fppg', 'FPPG', 'fppg', 'projection']:
            if col in df.columns:
                base_fppg_col = col
                break
        
        if not base_fppg_col:
            print("   ❌ Could not find projection column")
            return df
        
        # Create weather-adjusted projection
        df['weather_enhanced_fppg'] = df[base_fppg_col].copy()
        df['weather_adjustment'] = 1.0
        
        # Temperature adjustments
        if 'temperature' in df.columns:
            temp_mask = df['temperature'].notna()
            
            # Hot weather boost (>85°F)
            hot_mask = temp_mask & (df['temperature'] > 85)
            df.loc[hot_mask, 'weather_adjustment'] *= 1.06
            
            # Cold weather penalty (<55°F)
            cold_mask = temp_mask & (df['temperature'] < 55)
            df.loc[cold_mask, 'weather_adjustment'] *= 0.94
            
        # Wind adjustments
        if 'wind_speed' in df.columns:
            wind_mask = df['wind_speed'].notna()
            
            # Strong wind penalty (>15 mph)
            strong_wind_mask = wind_mask & (df['wind_speed'] > 15)
            df.loc[strong_wind_mask, 'weather_adjustment'] *= 0.93
            
            # Very strong wind penalty (>25 mph)
            very_strong_wind_mask = wind_mask & (df['wind_speed'] > 25)
            df.loc[very_strong_wind_mask, 'weather_adjustment'] *= 0.85
        
        # Humidity adjustments
        if 'humidity' in df.columns:
            humidity_mask = df['humidity'].notna()
            
            # High humidity boost (>75%)
            high_humidity_mask = humidity_mask & (df['humidity'] > 75)
            df.loc[high_humidity_mask, 'weather_adjustment'] *= 1.03
        
        # Precipitation penalty
        if 'conditions' in df.columns:
            precip_mask = df['conditions'].str.contains('rain|storm|drizzle', case=False, na=False)
            df.loc[precip_mask, 'weather_adjustment'] *= 0.82
        
        # Apply the adjustments
        df['weather_enhanced_fppg'] = df[base_fppg_col] * df['weather_adjustment']
        
        # Calculate improvement
        df['weather_improvement'] = df['weather_enhanced_fppg'] - df[base_fppg_col]
        df['weather_improvement_pct'] = (df['weather_improvement'] / df[base_fppg_col] * 100).round(1)
        
        # Round the enhanced projection
        df['weather_enhanced_fppg'] = df['weather_enhanced_fppg'].round(2)
        df['weather_improvement'] = df['weather_improvement'].round(2)
        
        improved_count = len(df[df['weather_improvement_pct'] > 0])
        hurt_count = len(df[df['weather_improvement_pct'] < 0])
        avg_improvement = df['weather_improvement_pct'].mean()
        
        print(f"   Weather adjustments applied:")
        print(f"      Players helped: {improved_count}")
        print(f"      Players hurt: {hurt_count}")
        print(f"      Average adjustment: {avg_improvement:.1f}%")
        
        return df
    
    def generate_weather_summary(self, enhanced_df):
        """Generate summary of weather impacts"""
        print(f"\n🌤️ WEATHER IMPACT SUMMARY")
        print("="*50)
        
        # Top weather beneficiaries
        top_helped = enhanced_df.nlargest(10, 'weather_improvement_pct')
        print(f"\n🔥 TOP WEATHER BENEFICIARIES:")
        for _, player in top_helped.iterrows():
            name = player.get('name', f"{player.get('First Name', '')} {player.get('Last Name', '')}").strip()
            team = player.get('team_standard', player.get('Team', ''))
            improvement = player.get('weather_improvement_pct', 0)
            conditions = player.get('conditions', 'Unknown')
            temp = player.get('temperature', 'N/A')
            print(f"   {name} ({team}): +{improvement:.1f}% ({conditions}, {temp}°F)")
        
        # Most hurt by weather
        most_hurt = enhanced_df.nsmallest(8, 'weather_improvement_pct')
        print(f"\n❄️ MOST HURT BY WEATHER:")
        for _, player in most_hurt.iterrows():
            name = player.get('name', f"{player.get('First Name', '')} {player.get('Last Name', '')}").strip()
            team = player.get('team_standard', player.get('Team', ''))
            improvement = player.get('weather_improvement_pct', 0)
            conditions = player.get('conditions', 'Unknown')
            print(f"   {name} ({team}): {improvement:.1f}% ({conditions})")
        
        # Team weather summary
        if 'team_standard' in enhanced_df.columns:
            team_weather = enhanced_df.groupby('team_standard').agg({
                'weather_improvement_pct': 'mean',
                'temperature': 'first',
                'conditions': 'first'
            }).sort_values('weather_improvement_pct', ascending=False)
            
            print(f"\n🏟️ TEAM WEATHER CONDITIONS:")
            for team, data in team_weather.head(10).iterrows():
                avg_boost = data['weather_improvement_pct']
                temp = data['temperature'] if pd.notna(data['temperature']) else 'N/A'
                conditions = data['conditions'] if pd.notna(data['conditions']) else 'Unknown'
                print(f"   {team}: {avg_boost:+.1f}% avg boost ({conditions}, {temp}°F)")

def main():
    """Main execution function"""
    print("🌤️ WEATHER INTEGRATION USING YOUR EXISTING SYSTEM")
    print("="*60)
    
    integrator = ExistingWeatherIntegrator()
    
    # Step 1: Run your existing weather system
    weather_success = integrator.run_existing_weather_system()
    
    if not weather_success:
        print("❌ Weather data collection failed. Check your weather scripts.")
        return
    
    # Step 2: Find projections to enhance
    projections_files = [
        "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_20250812_135729.csv",
        f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_{integrator.today}.csv",
        "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\base_hitter_scores.csv"
    ]
    
    input_file = None
    for file_path in projections_files:
        if os.path.exists(file_path):
            input_file = file_path
            break
    
    if not input_file:
        print("❌ No projections file found. Please run your projections first.")
        return
    
    print(f"\n📊 Using projections: {os.path.basename(input_file)}")
    
    # Step 3: Integrate weather with projections
    enhanced_df = integrator.integrate_weather_with_projections(input_file)
    
    if enhanced_df is None:
        print("❌ Weather integration failed.")
        return
    
    # Step 4: Generate summary
    integrator.generate_weather_summary(enhanced_df)
    
    print(f"\n✅ WEATHER INTEGRATION COMPLETE!")
    print(f"   Used your existing weather collection system")
    print(f"   Enhanced {len(enhanced_df)} player projections")
    print(f"   Applied real weather conditions and park factors")
    print(f"   Ready for lineup optimization")

if __name__ == "__main__":
    main()
