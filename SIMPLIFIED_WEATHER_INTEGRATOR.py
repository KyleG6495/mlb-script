"""
🌤️ SIMPLIFIED WEATHER INTEGRATOR
Uses your existing weather data with direct game_pk mapping
"""

import pandas as pd
import numpy as np
import os
from datetime import datetime

class SimplifiedWeatherIntegrator:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.weather_data_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data\weather_today.csv"
        
        # Game mapping from today's games (need to get this from projections)
        self.game_to_teams = {
            776769: {'home': 'HOU', 'away': 'BOS'},  # BOS@HOU
            776764: {'home': 'TEX', 'away': 'ARI'},  # ARI@TEX  
            776763: {'home': 'LAA', 'away': 'LAD'},  # LAD@LAA
            776767: {'home': 'SF', 'away': 'SD'},   # SD@SF
            776762: {'home': 'OAK', 'away': 'TB'},   # TB@OAK
            776774: {'home': 'NYY', 'away': 'MIN'},  # MIN@NYY
            776773: {'home': 'CWS', 'away': 'DET'},  # DET@CWS
            776771: {'home': 'MIL', 'away': 'PIT'},  # PIT@MIL
            776775: {'home': 'STL', 'away': 'COL'},  # COL@STL
            776770: {'home': 'KC', 'away': 'WSH'},   # WSH@KC
            776768: {'home': 'TOR', 'away': 'CHC'},  # CHC@TOR
            776772: {'home': 'NYM', 'away': 'ATL'},  # ATL@NYM
            776777: {'home': 'CIN', 'away': 'PHI'},  # PHI@CIN
            776778: {'home': 'CLE', 'away': 'MIA'},  # MIA@CLE
            776776: {'home': 'BAL', 'away': 'SEA'}   # SEA@BAL
        }
        
        # Team abbreviation mapping
        self.team_abbrev_map = {
            'HOU': 'Astros', 'BOS': 'Red Sox', 'ARI': 'Diamondbacks', 'TEX': 'Rangers',
            'LAD': 'Dodgers', 'LAA': 'Angels', 'SF': 'Giants', 'SD': 'Padres',
            'OAK': 'Athletics', 'TB': 'Rays', 'NYY': 'Yankees', 'MIN': 'Twins',
            'CWS': 'White Sox', 'DET': 'Tigers', 'MIL': 'Brewers', 'PIT': 'Pirates',
            'STL': 'Cardinals', 'COL': 'Rockies', 'KC': 'Royals', 'WSH': 'Nationals',
            'TOR': 'Blue Jays', 'CHC': 'Cubs', 'NYM': 'Mets', 'ATL': 'Braves',
            'CIN': 'Reds', 'PHI': 'Phillies', 'CLE': 'Guardians', 'MIA': 'Marlins',
            'BAL': 'Orioles', 'SEA': 'Mariners'
        }
    
    def apply_weather_to_projections(self, projections_file: str):
        """Apply weather data directly to projections using team mapping"""
        print(f"🌤️ Applying weather data to projections...")
        
        # Load projections
        if not os.path.exists(projections_file):
            print(f"❌ Projections file not found: {projections_file}")
            return None
            
        df_proj = pd.read_csv(projections_file)
        print(f"   Loaded {len(df_proj)} projections")
        
        # Load weather data
        if not os.path.exists(self.weather_data_file):
            print(f"❌ Weather data not found: {self.weather_data_file}")
            return None
            
        df_weather = pd.read_csv(self.weather_data_file)
        print(f"   Loaded weather for {len(df_weather)} games")
        
        # Create team to weather mapping
        team_weather_map = {}
        
        for _, weather_row in df_weather.iterrows():
            game_pk_raw = weather_row['game_pk']
            
            # Skip rows with NaN game_pk
            if pd.isna(game_pk_raw):
                continue
                
            game_pk = int(game_pk_raw)
            
            if game_pk in self.game_to_teams:
                home_team = self.game_to_teams[game_pk]['home']
                away_team = self.game_to_teams[game_pk]['away']
                
                # Both teams get the same weather (same stadium)
                weather_data = {
                    'temperature': weather_row['temperature'],
                    'humidity': weather_row['humidity'],
                    'wind_speed': weather_row['wind_speed'],
                    'wind_deg': weather_row['wind_deg'],
                    'condition': weather_row['condition'],
                    'game_pk': game_pk
                }
                
                # Map to full team names
                if home_team in self.team_abbrev_map:
                    team_weather_map[self.team_abbrev_map[home_team]] = weather_data
                if away_team in self.team_abbrev_map:
                    team_weather_map[self.team_abbrev_map[away_team]] = weather_data
        
        print(f"   Mapped weather for {len(team_weather_map)} teams")
        
        # Apply weather to projections
        enhanced_projections = []
        
        for _, player in df_proj.iterrows():
            # Get team
            team = player.get('Team', player.get('team', ''))
            
            # Get base projection
            base_fppg = player.get('enhanced_fppg', player.get('FPPG', player.get('fppg', 0)))
            
            # Get weather data for team
            weather_data = team_weather_map.get(team, {})
            
            # Apply weather adjustments
            weather_factor = self._calculate_weather_factor(weather_data)
            
            # Calculate enhanced projection
            weather_enhanced_fppg = base_fppg * weather_factor
            improvement = weather_enhanced_fppg - base_fppg
            improvement_pct = (improvement / base_fppg * 100) if base_fppg > 0 else 0
            
            # Player name
            name = player.get('name', f"{player.get('First Name', '')} {player.get('Last Name', '')}").strip()
            if not name or name == ' ':
                name = f"Player_{player.get('Id', 'Unknown')}"
            
            enhanced_projections.append({
                'name': name,
                'team': team,
                'position': player.get('Position', player.get('position', '')),
                'salary': player.get('Salary', player.get('salary', 0)),
                'base_fppg': round(base_fppg, 2),
                'weather_enhanced_fppg': round(weather_enhanced_fppg, 2),
                'weather_improvement': round(improvement, 2),
                'weather_improvement_pct': round(improvement_pct, 1),
                'temperature': weather_data.get('temperature', 'N/A'),
                'humidity': weather_data.get('humidity', 'N/A'),
                'wind_speed': weather_data.get('wind_speed', 'N/A'),
                'condition': weather_data.get('condition', 'No Data'),
                'weather_factor': round(weather_factor, 3),
                'has_weather_data': bool(weather_data)
            })
        
        enhanced_df = pd.DataFrame(enhanced_projections)
        
        # Save enhanced projections
        output_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\weather_enhanced_projections_{self.timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        weather_count = len(enhanced_df[enhanced_df['has_weather_data']])
        improved_count = len(enhanced_df[enhanced_df['weather_improvement_pct'] > 0])
        hurt_count = len(enhanced_df[enhanced_df['weather_improvement_pct'] < 0])
        
        print(f"\n✅ Weather enhanced projections saved: {os.path.basename(output_file)}")
        print(f"   Players with weather data: {weather_count}/{len(enhanced_df)}")
        print(f"   Players helped by weather: {improved_count}")
        print(f"   Players hurt by weather: {hurt_count}")
        print(f"   Average improvement: {enhanced_df['weather_improvement_pct'].mean():.1f}%")
        
        return enhanced_df
    
    def _calculate_weather_factor(self, weather_data: dict) -> float:
        """Calculate weather adjustment factor"""
        if not weather_data:
            return 1.0
        
        factor = 1.0
        
        # Temperature effects
        temp = weather_data.get('temperature', 75)
        if temp > 85:
            factor *= 1.06  # Hot weather helps hitting
        elif temp > 75:
            factor *= 1.02  # Warm weather slightly helps
        elif temp < 55:
            factor *= 0.92  # Cold weather hurts hitting
        elif temp < 65:
            factor *= 0.97  # Cool weather slightly hurts
        
        # Wind effects
        wind_speed = weather_data.get('wind_speed', 8)
        if wind_speed > 20:
            factor *= 0.88  # Strong wind hurts offense
        elif wind_speed > 15:
            factor *= 0.93  # Moderate wind hurts slightly
        elif wind_speed > 12:
            factor *= 0.97  # Light wind minimal impact
        
        # Humidity effects
        humidity = weather_data.get('humidity', 50)
        if humidity > 75:
            factor *= 1.02  # High humidity helps ball carry
        elif humidity < 35:
            factor *= 0.98  # Low humidity hurts ball carry
        
        # Condition effects
        condition = weather_data.get('condition', '').lower()
        if 'rain' in condition or 'storm' in condition:
            factor *= 0.85  # Rain/storms hurt offense significantly
        elif 'cloud' in condition and 'broken' in condition:
            factor *= 0.98  # Heavy clouds slightly hurt
        
        return max(0.8, min(1.2, factor))  # Cap between 80% and 120%
    
    def generate_weather_report(self, enhanced_df: pd.DataFrame):
        """Generate weather impact report"""
        print(f"\n🌤️ WEATHER IMPACT REPORT")
        print("="*50)
        
        # Players with weather data
        with_weather = enhanced_df[enhanced_df['has_weather_data']]
        
        if len(with_weather) == 0:
            print("❌ No players have weather data")
            return
        
        # Top weather beneficiaries
        top_helped = with_weather.nlargest(10, 'weather_improvement_pct')
        print(f"\n🔥 TOP WEATHER BENEFICIARIES:")
        for _, player in top_helped.iterrows():
            print(f"   {player['name']} ({player['team']}): +{player['weather_improvement_pct']:.1f}%")
            print(f"      ${player['salary']:,} | {player['condition']}, {player['temperature']}°F")
        
        # Most hurt by weather
        most_hurt = with_weather.nsmallest(5, 'weather_improvement_pct')
        print(f"\n❄️ MOST HURT BY WEATHER:")
        for _, player in most_hurt.iterrows():
            print(f"   {player['name']} ({player['team']}): {player['weather_improvement_pct']:.1f}%")
            print(f"      {player['condition']}, {player['temperature']}°F, {player['wind_speed']}mph wind")
        
        # Team weather summary
        team_weather = with_weather.groupby('team').agg({
            'weather_improvement_pct': 'mean',
            'temperature': 'first',
            'condition': 'first',
            'wind_speed': 'first'
        }).sort_values('weather_improvement_pct', ascending=False)
        
        print(f"\n🏟️ TEAM WEATHER CONDITIONS:")
        for team, data in team_weather.iterrows():
            avg_boost = data['weather_improvement_pct']
            temp = data['temperature']
            condition = data['condition']
            wind = data['wind_speed']
            
            impact_emoji = "🔥" if avg_boost > 3 else "❄️" if avg_boost < -3 else "⚖️"
            print(f"   {impact_emoji} {team}: {avg_boost:+.1f}% avg | {condition}, {temp}°F, {wind}mph")
        
        # Weather condition breakdown
        print(f"\n🌤️ CONDITIONS BREAKDOWN:")
        condition_summary = with_weather.groupby('condition').agg({
            'weather_improvement_pct': 'mean',
            'name': 'count'
        }).sort_values('weather_improvement_pct', ascending=False)
        
        for condition, data in condition_summary.iterrows():
            player_count = data['name']
            avg_impact = data['weather_improvement_pct']
            print(f"   {condition}: {avg_impact:+.1f}% avg impact ({player_count} players)")

def main():
    """Main execution function"""
    print("🌤️ SIMPLIFIED WEATHER INTEGRATOR")
    print("="*50)
    
    integrator = SimplifiedWeatherIntegrator()
    
    # Find projections file
    projections_files = [
        "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_20250812_135729.csv",
        f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_{integrator.timestamp[:8]}.csv"
    ]
    
    input_file = None
    for file_path in projections_files:
        if os.path.exists(file_path):
            input_file = file_path
            break
    
    if not input_file:
        print("❌ No projections file found")
        return
    
    print(f"📊 Using projections: {os.path.basename(input_file)}")
    
    # Apply weather data
    enhanced_df = integrator.apply_weather_to_projections(input_file)
    
    if enhanced_df is not None:
        # Generate report
        integrator.generate_weather_report(enhanced_df)
        
        print(f"\n✅ WEATHER INTEGRATION COMPLETE!")
        print(f"   Applied real weather conditions to {len(enhanced_df)} players")
        print(f"   Used your existing weather data collection system")
        print(f"   Ready for lineup optimization")

if __name__ == "__main__":
    main()
