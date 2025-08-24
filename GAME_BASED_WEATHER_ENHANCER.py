"""
 GAME-BASED WEATHER & PARK ENHANCER
Uses game_pk mapping to connect weather data to players
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class GameBasedWeatherEnhancer:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def enhance_with_real_weather_park(self):
        """Enhance projections using game_pk mapping for weather/park data"""
        
        print(" GAME-BASED WEATHER & PARK ENHANCER")
        print("="*50)
        
        # Load weather data
        weather_file = "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\weather_today.csv"
        if not os.path.exists(weather_file):
            print("ERROR: Weather data not found. Run: python '19. build_weather_today.py'")
            return
        
        weather_df = pd.read_csv(weather_file)
        print(f"SUCCESS: Loaded weather data: {len(weather_df)} games")
        
        # Load game_pk mapping for hitters
        game_pk_file = "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\hitter_games_with_game_pk.csv"
        if not os.path.exists(game_pk_file):
            print("ERROR: Game PK mapping not found")
            return
            
        game_pk_df = pd.read_csv(game_pk_file)
        print(f"SUCCESS: Loaded game PK mapping: {len(game_pk_df)} players")
        
        # Load enhanced projections
        projections_file = "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_20250812_135729.csv"
        if not os.path.exists(projections_file):
            print("ERROR: Enhanced projections not found")
            return
            
        df = pd.read_csv(projections_file)
        print(f"SUCCESS: Loaded projections: {len(df)} players")
        
        # Create name mapping for projections
        df['player_name'] = df['First Name'].fillna('') + ' ' + df['Last Name'].fillna('')
        df['player_name'] = df['player_name'].str.strip()
        
        # Apply weather enhancements
        enhanced_projections = []
        weather_applied = 0
        
        for _, player in df.iterrows():
            player_name = player['player_name']
            player_id = player.get('player_id')
            
            # Try to find game_pk for this player by player_id first, then by name
            player_game = None
            
            if pd.notna(player_id):
                player_game = game_pk_df[game_pk_df['player_id'] == player_id]
            
            if player_game is None or player_game.empty:
                # Try by name matching
                player_game = game_pk_df[game_pk_df['target_name'] == player_name]
            
            if player_game is None or player_game.empty:
                # Try partial name matching
                first_name = player.get('First Name', '').strip()
                last_name = player.get('Last Name', '').strip()
                if first_name and last_name:
                    player_game = game_pk_df[
                        (game_pk_df['target_name'].str.contains(first_name, case=False, na=False)) &
                        (game_pk_df['target_name'].str.contains(last_name, case=False, na=False))
                    ]
            
            if not player_game.empty:
                game_pk = player_game.iloc[0]['game_pk']
                
                # Find weather for this game_pk
                game_weather = weather_df[weather_df['game_pk'] == game_pk]
                
                if not game_weather.empty:
                    weather_data = game_weather.iloc[0]
                    
                    # Calculate weather impact
                    temp = weather_data.get('temperature', 75)
                    wind = weather_data.get('wind_speed', 8)
                    humidity = weather_data.get('humidity', 50)
                    conditions = weather_data.get('condition', 'Clear')
                    
                    weather_impact = self.calculate_weather_impact(temp, wind, humidity, conditions)
                    weather_applied += 1
                    
                    temperature = temp
                    wind_speed = wind
                    weather_conditions = conditions
                else:
                    # No weather data for this game
                    weather_impact = 1.0
                    temperature = 75
                    wind_speed = 8
                    weather_conditions = 'Clear'
            else:
                # No game_pk mapping found
                weather_impact = 1.0
                temperature = 75
                wind_speed = 8
                weather_conditions = 'Clear'
            
            # Apply park factors based on team
            park_impact = self.get_park_factor(player['Team'])
            
            # Calculate combined impact
            position = player.get('Position', 'OF')
            if position == 'P':
                # Pitchers benefit from pitcher-friendly conditions
                combined_impact = (2.0 - park_impact) * (2.0 - weather_impact)
            else:
                # Hitters benefit from hitter-friendly conditions
                combined_impact = park_impact * weather_impact
            
            # Apply enhancement
            base_fppg = player.get('enhanced_fppg', player.get('FPPG', 0))
            enhanced_fppg = base_fppg * combined_impact
            
            # Calculate improvement
            improvement = enhanced_fppg - base_fppg
            improvement_pct = (improvement / base_fppg * 100) if base_fppg > 0 else 0
            
            enhanced_projections.append({
                'name': player_name,
                'team': player['Team'],
                'position': position,
                'salary': player.get('Salary', 0),
                'base_fppg': base_fppg,
                'enhanced_fppg': round(enhanced_fppg, 2),
                'improvement': round(improvement, 2),
                'improvement_pct': round(improvement_pct, 1),
                'temperature': temperature,
                'wind_speed': wind_speed,
                'conditions': weather_conditions,
                'park_factor': round(park_impact, 3),
                'weather_impact': round(weather_impact, 3),
                'combined_impact': round(combined_impact, 3),
                'has_real_weather': weather_applied > 0
            })
        
        enhanced_df = pd.DataFrame(enhanced_projections)
        
        # Save enhanced projections
        output_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\real_weather_enhanced_{self.timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        print(f"\nSUCCESS: Real weather enhanced projections saved: {output_file}")
        print(f"   Players with real weather data: {weather_applied}")
        print(f"   Average improvement: {enhanced_df['improvement_pct'].mean():.1f}%")
        
        # Generate insights
        self.generate_insights(enhanced_df)
        
        return enhanced_df
    
    def calculate_weather_impact(self, temp, wind, humidity, conditions):
        """Calculate weather impact on offensive production"""
        impact = 1.0
        
        # Temperature impact (more aggressive for real data)
        if temp > 90:
            impact += 0.08  # Very hot weather really helps
        elif temp > 80:
            impact += 0.05  # Hot weather helps
        elif temp > 70:
            impact += 0.02  # Warm weather slightly helps
        elif temp < 50:
            impact -= 0.08  # Cold weather really hurts
        elif temp < 60:
            impact -= 0.04  # Cool weather hurts
        
        # Wind impact
        if wind > 20:
            impact -= 0.10  # Very strong wind significantly hurts
        elif wind > 15:
            impact -= 0.06  # Strong wind hurts
        elif wind > 12:
            impact -= 0.03  # Moderate wind slightly hurts
        
        # Humidity impact
        if humidity > 80:
            impact += 0.03  # High humidity helps ball carry
        elif humidity < 30:
            impact -= 0.02  # Dry air hurts ball carry
        
        # Condition impact
        conditions_lower = str(conditions).lower()
        if 'rain' in conditions_lower:
            impact -= 0.12  # Rain significantly hurts
        elif 'storm' in conditions_lower:
            impact -= 0.15  # Storms really hurt
        elif any(word in conditions_lower for word in ['overcast', 'cloud']):
            impact -= 0.02  # Clouds slightly hurt
        elif 'clear' in conditions_lower:
            impact += 0.01  # Clear skies slightly help
        
        return max(0.80, min(1.20, impact))  # Cap between 80% and 120%
    
    def get_park_factor(self, team):
        """Get park factor for team (simplified but realistic)"""
        park_factors = {
            'COL': 1.15,  # Coors Field - extreme hitter friendly
            'TEX': 1.08,  # Globe Life Field - hitter friendly
            'BOS': 1.07,  # Fenway - hitter friendly
            'NYY': 1.06,  # Yankee Stadium - hitter friendly
            'LAA': 1.05,  # Angel Stadium - slightly hitter friendly
            'ARI': 1.05,  # Chase Field - hitter friendly
            'CHC': 1.04,  # Wrigley - variable but generally hitter friendly
            'CIN': 1.04,  # Great American Ballpark - hitter friendly
            'PHI': 1.03,  # Citizens Bank Park - slightly hitter friendly
            'ATL': 1.03,  # Truist Park - slightly hitter friendly
            'MIL': 1.02,  # American Family Field - neutral+
            'MIN': 1.02,  # Target Field - slightly hitter friendly
            'KC': 1.01,   # Kauffman Stadium - neutral+
            'DET': 1.01,  # Comerica Park - neutral+
            'STL': 1.00,  # Busch Stadium - neutral
            'WSH': 1.00,  # Nationals Park - neutral
            'NYM': 1.00,  # Citi Field - neutral
            'BAL': 1.00,  # Oriole Park - neutral
            'CWS': 0.99,  # Guaranteed Rate - slightly pitcher friendly
            'CLE': 0.98,  # Progressive Field - slightly pitcher friendly
            'TB': 0.97,   # Tropicana Field - pitcher friendly
            'PIT': 0.97,  # PNC Park - pitcher friendly
            'LAD': 0.96,  # Dodger Stadium - pitcher friendly
            'MIA': 0.96,  # loanDepot park - pitcher friendly
            'HOU': 0.95,  # Minute Maid Park - pitcher friendly
            'SEA': 0.95,  # T-Mobile Park - pitcher friendly
            'SD': 0.94,   # Petco Park - pitcher friendly
            'TOR': 0.94,  # Rogers Centre - pitcher friendly
            'SF': 0.92,   # Oracle Park - pitcher friendly
            'OAK': 0.90   # Oakland Coliseum - very pitcher friendly
        }
        
        return park_factors.get(team, 1.0)
    
    def generate_insights(self, enhanced_df):
        """Generate weather and park insights"""
        
        print(f"\n REAL WEATHER & PARK INSIGHTS")
        print("="*45)
        
        # Players with real weather data
        real_weather_players = enhanced_df[enhanced_df['has_real_weather'] == True]
        print(f"   Players with real weather: {len(real_weather_players)}")
        
        # Top weather beneficiaries
        top_helped = enhanced_df.nlargest(10, 'improvement_pct')
        print(f"\n TOP WEATHER/PARK BENEFICIARIES:")
        for _, player in top_helped.iterrows():
            weather_emoji = "" if player['has_real_weather'] else "DATA:"
            print(f"   {weather_emoji} {player['name']} ({player['team']}): +{player['improvement_pct']:.1f}%")
            print(f"      {player['conditions']}, {player['temperature']:.0f}F, {player['wind_speed']:.0f}mph wind")
        
        # Weather conditions breakdown
        weather_breakdown = enhanced_df.groupby('conditions').agg({
            'improvement_pct': 'mean',
            'temperature': 'mean',
            'wind_speed': 'mean'
        }).sort_values('improvement_pct', ascending=False)
        
        print(f"\n WEATHER CONDITIONS IMPACT:")
        for condition, data in weather_breakdown.iterrows():
            if not pd.isna(data['improvement_pct']):
                print(f"   {condition}: {data['improvement_pct']:+.1f}% avg | {data['temperature']:.0f}F, {data['wind_speed']:.0f}mph")
        
        # Team environments
        team_summary = enhanced_df.groupby('team').agg({
            'improvement_pct': 'mean',
            'park_factor': 'first',
            'temperature': 'mean',
            'conditions': lambda x: x.mode().iloc[0] if not x.empty else 'Clear'
        }).sort_values('improvement_pct', ascending=False)
        
        print(f"\n BEST TEAM ENVIRONMENTS:")
        for team, data in team_summary.head(10).iterrows():
            if data['improvement_pct'] > 1:
                print(f"   {team}: {data['improvement_pct']:+.1f}% avg | Park: {data['park_factor']:.3f} | {data['conditions']}")
        
        # Value spots
        value_spots = enhanced_df[
            (enhanced_df['salary'] <= 8000) & 
            (enhanced_df['improvement_pct'] > 2)
        ].nlargest(8, 'improvement_pct')
        
        if not value_spots.empty:
            print(f"\n VALUE SPOTS IN GOOD ENVIRONMENTS:")
            for _, player in value_spots.iterrows():
                print(f"   {player['name']} ({player['team']}): ${player['salary']:,} | +{player['improvement_pct']:.1f}%")

def main():
    enhancer = GameBasedWeatherEnhancer()
    enhancer.enhance_with_real_weather_park()

if __name__ == "__main__":
    main()
