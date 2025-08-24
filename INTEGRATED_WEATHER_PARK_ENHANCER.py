"""
 INTEGRATED WEATHER & PARK ENHANCER
Uses your existing weather.py and park factor systems
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class IntegratedWeatherParkEnhancer:
    def __init__(self):
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
    def enhance_projections_with_weather_park(self):
        """Enhance projections using existing weather and park data"""
        
        print(" INTEGRATED WEATHER & PARK ENHANCER")
        print("="*50)
        
        # Load weather and park data (from your pipeline)
        weather_park_file = "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\merged_weather_park.csv"
        
        if not os.path.exists(weather_park_file):
            print("ERROR: Weather/park data not found. Run the data pipeline first:")
            print("   1. python '19. build_weather_today.py'")
            print("   2. python '20. merge_weather_and_park_factors.py'")
            return
            
        weather_park_df = pd.read_csv(weather_park_file)
        print(f"SUCCESS: Loaded weather/park data: {len(weather_park_df)} games")
        
        # Load projections
        projections_file = "C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\enhanced_projections_20250812_135729.csv"
        
        if not os.path.exists(projections_file):
            print("ERROR: Enhanced projections not found")
            return
            
        df = pd.read_csv(projections_file)
        print(f"SUCCESS: Loaded projections: {len(df)} players")
        
        # Create team mapping for your system
        team_mapping = {
            'Angels': 'LAA', 'Orioles': 'BAL', 'Red Sox': 'BOS', 'White Sox': 'CWS',
            'Guardians': 'CLE', 'Tigers': 'DET', 'Royals': 'KC', 'Twins': 'MIN',
            'Yankees': 'NYY', 'Athletics': 'OAK', 'Mariners': 'SEA', 'Rays': 'TB',
            'Rangers': 'TEX', 'Blue Jays': 'TOR', 'Diamondbacks': 'ARI', 'Braves': 'ATL',
            'Cubs': 'CHC', 'Reds': 'CIN', 'Rockies': 'COL', 'Marlins': 'MIA',
            'Astros': 'HOU', 'Dodgers': 'LAD', 'Brewers': 'MIL', 'Nationals': 'WSH',
            'Mets': 'NYM', 'Phillies': 'PHI', 'Pirates': 'PIT', 'Cardinals': 'STL',
            'Padres': 'SD', 'Giants': 'SF'
        }
        
        reverse_mapping = {v: k for k, v in team_mapping.items()}
        
        # Apply weather and park enhancements
        enhanced_projections = []
        
        for _, player in df.iterrows():
            player_team = player['Team']
            
            # Map to your team format
            team_key = reverse_mapping.get(player_team, player_team)
            
            # Find weather/park data for this team
            team_weather_park = None
            
            # Try to find by direct team match in park factors
            team_weather_park = weather_park_df[
                weather_park_df['Team'].fillna('').str.contains(team_key, na=False)
            ]
            
            if team_weather_park.empty:
                # Use default neutral conditions
                weather_impact = 1.0
                park_impact = 1.0
                temperature = 75
                wind_speed = 8
                conditions = 'Clear'
                park_factor = 1.0
            else:
                # Get first match
                weather_park_data = team_weather_park.iloc[0]
                
                # Calculate weather impact
                temp = weather_park_data.get('temperature', 75)
                wind = weather_park_data.get('wind_speed', 8)
                humidity = weather_park_data.get('humidity', 50)
                conditions = weather_park_data.get('condition', 'Clear')
                
                weather_impact = self.calculate_weather_impact(temp, wind, humidity, conditions)
                
                # Get park factor
                park_factor = weather_park_data.get('park_factor', 1.0)
                if pd.isna(park_factor):
                    park_factor = 1.0
                    
                park_impact = park_factor
                temperature = temp
                wind_speed = wind
            
            # Calculate combined impact
            position = player.get('Position', 'OF')
            if position == 'P':
                # Pitchers benefit from pitcher-friendly conditions (inverse)
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
                'name': f"{player.get('First Name', '')} {player.get('Last Name', '')}".strip(),
                'team': player_team,
                'position': position,
                'salary': player.get('Salary', 0),
                'base_fppg': base_fppg,
                'enhanced_fppg': round(enhanced_fppg, 2),
                'improvement': round(improvement, 2),
                'improvement_pct': round(improvement_pct, 1),
                'temperature': temperature,
                'wind_speed': wind_speed,
                'conditions': conditions,
                'park_factor': round(park_factor, 3),
                'weather_impact': round(weather_impact, 3),
                'combined_impact': round(combined_impact, 3)
            })
        
        enhanced_df = pd.DataFrame(enhanced_projections)
        
        # Save enhanced projections
        output_file = f"C:\\Users\\kgone\\OneDrive\\Personal_Information\\MLB\\data\\weather_park_enhanced_{self.timestamp}.csv"
        enhanced_df.to_csv(output_file, index=False)
        
        print(f"\nSUCCESS: Weather & park enhanced projections saved: {output_file}")
        print(f"   Players enhanced: {len(enhanced_df)}")
        print(f"   Average improvement: {enhanced_df['improvement_pct'].mean():.1f}%")
        
        # Generate insights
        self.generate_insights(enhanced_df)
        
        return enhanced_df
    
    def calculate_weather_impact(self, temp, wind, humidity, conditions):
        """Calculate weather impact on offensive production"""
        impact = 1.0
        
        # Temperature impact
        if temp > 85:
            impact += 0.06  # Hot weather helps
        elif temp > 75:
            impact += 0.03
        elif temp < 55:
            impact -= 0.05  # Cold weather hurts
        elif temp < 65:
            impact -= 0.02
        
        # Wind impact
        if wind > 15:
            impact -= 0.04  # Strong wind hurts
        elif wind > 20:
            impact -= 0.08  # Very strong wind
        
        # Humidity impact
        if humidity > 75:
            impact += 0.02  # High humidity helps ball carry
        elif humidity < 35:
            impact -= 0.01
        
        # Condition impact
        conditions_lower = str(conditions).lower()
        if any(word in conditions_lower for word in ['rain', 'storm', 'drizzle']):
            impact -= 0.10  # Rain significantly hurts
        elif any(word in conditions_lower for word in ['cloud', 'overcast']):
            impact -= 0.01  # Clouds slightly hurt
        
        return max(0.85, min(1.15, impact))  # Cap between 85% and 115%
    
    def generate_insights(self, enhanced_df):
        """Generate weather and park insights"""
        
        print(f"\n WEATHER & PARK INSIGHTS")
        print("="*40)
        
        # Top beneficiaries
        top_helped = enhanced_df.nlargest(10, 'improvement_pct')
        print(f"\n TOP WEATHER/PARK BENEFICIARIES:")
        for _, player in top_helped.iterrows():
            print(f"   {player['name']} ({player['team']}): +{player['improvement_pct']:.1f}%")
            print(f"      {player['conditions']}, {player['temperature']:.0f}F, Park: {player['park_factor']:.3f}")
        
        # Team environments
        team_summary = enhanced_df.groupby('team').agg({
            'improvement_pct': 'mean',
            'temperature': 'first',
            'conditions': 'first',
            'park_factor': 'first'
        }).sort_values('improvement_pct', ascending=False)
        
        print(f"\n BEST TEAM ENVIRONMENTS:")
        for team, data in team_summary.head(8).iterrows():
            if data['improvement_pct'] > 0:
                print(f"   {team}: {data['improvement_pct']:+.1f}% avg | {data['conditions']}, {data['temperature']:.0f}F")
        
        # Value spots
        value_spots = enhanced_df[
            (enhanced_df['salary'] <= 8000) & 
            (enhanced_df['improvement_pct'] > 3)
        ].nlargest(8, 'improvement_pct')
        
        print(f"\n VALUE SPOTS IN GOOD ENVIRONMENTS:")
        for _, player in value_spots.iterrows():
            print(f"   {player['name']} ({player['team']}): ${player['salary']:,} | +{player['improvement_pct']:.1f}%")

def main():
    enhancer = IntegratedWeatherParkEnhancer()
    enhancer.enhance_projections_with_weather_park()

if __name__ == "__main__":
    main()
