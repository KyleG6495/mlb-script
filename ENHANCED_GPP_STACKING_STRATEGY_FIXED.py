#!/usr/bin/env python3
"""
ENHANCED GPP STACKING STRATEGY - FIXED VERSION
Implements optimal stacking for large GPP tournaments based on:
- Real ownership projections
- Weather factors  
- Park factors
- Projected value
- Current slate validation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os

class GPPStackingStrategy:
    def __init__(self):
        self.data_dir = "../data"
        self.fd_dir = "../fd_current_slate"
        
    def load_data(self):
        """Load all necessary data files"""
        print("🔄 Loading data...")
        
        # Core data files
        self.ownership_df = pd.read_csv(f"{self.data_dir}/advanced_ownership_projections_20250818_103048.csv")
        self.stack_df = pd.read_csv(f"{self.data_dir}/stack_aware_lineups_20250818_142508.csv")
        self.weather_df = pd.read_csv(f"{self.data_dir}/weather_today.csv")
        self.fd_slate = pd.read_csv(f"{self.fd_dir}/fd_slate_today.csv")
        
        # Get teams actually playing today for validation
        self.teams_today = set(self.fd_slate['Team'].unique())
        
        print(f"✅ Loaded {len(self.ownership_df)} ownership projections")
        print(f"✅ Loaded {len(self.stack_df)} existing stacks")
        print(f"✅ Loaded weather for {len(self.weather_df)} games")
        print(f"🎯 Teams playing today: {sorted(self.teams_today)}")
        
    def get_real_team_ownership(self, team):
        """Get real team ownership from individual player data"""
        try:
            team_players = self.ownership_df[self.ownership_df['team'].str.upper() == team.upper()]
            if len(team_players) > 0:
                # Get average ownership for hitters (exclude pitchers)
                hitters = team_players[team_players['position'] != 'P']
                if len(hitters) > 0:
                    avg_ownership = hitters['ownership'].mean() * 100  # Convert to percentage
                    # Stack ownership is typically 40-60% of individual average
                    stack_ownership = avg_ownership * 0.5
                    return max(stack_ownership, 0.5)  # Minimum 0.5%
            
            return 3.0  # More realistic fallback if no data
        except Exception as e:
            print(f"⚠️ Error calculating ownership for {team}: {e}")
            return 3.0
        
    def analyze_current_stacks(self):
        """Analyze existing stacks for GPP viability"""
        print("\n🎯 STACK ANALYSIS FOR GPP TOURNAMENTS")
        print("="*50)
        
        stack_recommendations = []
        
        for idx, lineup in self.stack_df.iterrows():
            stack_team = lineup['Stack_Team'].split('(')[0].strip()
            projected = lineup['Projected_Points']
            
            # FILTER OUT TEAMS NOT PLAYING TODAY
            if stack_team not in self.teams_today:
                print(f"\n❌ {stack_team} Stack: NOT PLAYING TODAY - SKIPPING")
                continue
            
            # Calculate real ownership from individual player data
            real_ownership = self.get_real_team_ownership(stack_team)
            
            # Calculate GPP viability score
            if pd.isna(projected):
                viability_score = 0
                gpp_rating = "❌ SKIP (No projection)"
                value_ratio = 0
            else:
                # Score based on projection/ownership ratio
                if real_ownership > 0:
                    value_ratio = projected / real_ownership
                else:
                    value_ratio = projected / 1  # Avoid division by zero
                
                if real_ownership < 5 and projected > 100:
                    viability_score = 10
                    gpp_rating = "🚀 ELITE"
                elif real_ownership < 8 and projected > 95:
                    viability_score = 8
                    gpp_rating = "✅ EXCELLENT" 
                elif real_ownership < 12 and projected > 90:
                    viability_score = 6
                    gpp_rating = "✅ GOOD"
                elif real_ownership < 15:
                    viability_score = 4
                    gpp_rating = "⚠️ MODERATE"
                else:
                    viability_score = 2
                    gpp_rating = "❌ AVOID"
            
            stack_info = {
                'team': stack_team,
                'projected_points': projected,
                'ownership': real_ownership,
                'viability_score': viability_score,
                'gpp_rating': gpp_rating,
                'value_ratio': value_ratio
            }
            stack_recommendations.append(stack_info)
            
            print(f"\n✅ {stack_team} Stack (VALID TODAY):")
            print(f"  Projection: {projected:.1f} points" if not pd.isna(projected) else "  Projection: Unknown")
            print(f"  Real Ownership: {real_ownership:.1f}%")
            print(f"  Value Ratio: {value_ratio:.1f}")
            print(f"  GPP Rating: {gpp_rating}")
            
        return sorted(stack_recommendations, key=lambda x: x['viability_score'], reverse=True)
    
    def check_weather_advantages(self):
        """Check for weather-based stacking opportunities"""
        print(f"\n🌡️ WEATHER ANALYSIS")
        print("="*30)
        
        # Find games with offensive weather conditions
        good_weather = self.weather_df[
            (self.weather_df['temperature'] > 70) | 
            (self.weather_df['humidity'] < 60)
        ]
        
        print(f"Games with good hitting weather: {len(good_weather)}")
        
        weather_teams = []
        for _, game in good_weather.iterrows():
            temp = game['temperature']
            humidity = game['humidity']
            home_team = game.get('home_team', 'Unknown')
            
            # Only include teams actually playing today
            if pd.notna(home_team) and home_team in self.teams_today:
                weather_score = 0
                if temp > 75: weather_score += 2
                if temp > 80: weather_score += 1
                if humidity < 50: weather_score += 1
                
                weather_teams.append({
                    'team': home_team,
                    'temperature': temp,
                    'humidity': humidity,
                    'weather_score': weather_score
                })
                
                print(f"  {home_team}: {temp:.0f}°F, {humidity:.0f}% humidity (Score: {weather_score}/4)")
        
        return sorted(weather_teams, key=lambda x: x['weather_score'], reverse=True)
    
    def generate_gpp_recommendations(self):
        """Generate final GPP stacking recommendations"""
        print(f"\n🏆 FINAL GPP STACKING RECOMMENDATIONS")
        print("="*50)
        
        # Get stack analysis
        stack_rankings = self.analyze_current_stacks()
        weather_advantages = self.check_weather_advantages()
        
        if not stack_rankings:
            print("❌ No valid stacks found for today's slate!")
            return {'elite_stacks': [], 'good_stacks': [], 'weather_teams': weather_advantages}
        
        # Find top stacks
        elite_stacks = [s for s in stack_rankings if s['viability_score'] >= 8]
        good_stacks = [s for s in stack_rankings if s['viability_score'] >= 6]
        
        print(f"\n🚀 ELITE STACKS (Use in 40-50% of lineups):")
        if elite_stacks:
            for stack in elite_stacks:
                team = stack['team']
                proj = stack['projected_points']
                own = stack['ownership']
                if not pd.isna(proj):
                    print(f"  ✅ {team}: {proj:.1f} pts, {own:.1f}% owned")
        else:
            print("  ⚠️ No elite stacks found")
        
        print(f"\n✅ GOOD STACKS (Use in 20-30% of lineups):")
        good_but_not_elite = [s for s in good_stacks if s not in elite_stacks]
        if good_but_not_elite:
            for stack in good_but_not_elite:
                team = stack['team']
                proj = stack['projected_points']
                own = stack['ownership']
                if not pd.isna(proj):
                    print(f"  ✅ {team}: {proj:.1f} pts, {own:.1f}% owned")
        else:
            print("  ⚠️ No additional good stacks found")
        
        # Weather boost recommendations
        if weather_advantages:
            print(f"\n🌡️ WEATHER BOOST TEAMS:")
            for team_info in weather_advantages[:3]:
                team = team_info['team']
                temp = team_info['temperature']
                score = team_info['weather_score']
                print(f"  🔥 {team}: {temp:.0f}°F (Score: {score}/4)")
        
        # Final strategy based on actual data
        if elite_stacks:
            primary = elite_stacks[0]['team']
            primary_proj = elite_stacks[0]['projected_points']
            primary_own = elite_stacks[0]['ownership']
            
            print(f"\n💡 IMPLEMENTATION STRATEGY:")
            print(f"  1. Primary Focus: {primary} ({primary_proj:.1f} pts, {primary_own:.1f}% owned)")
            
            if len(elite_stacks) > 1:
                secondary = elite_stacks[1]['team']
                secondary_proj = elite_stacks[1]['projected_points']
                secondary_own = elite_stacks[1]['ownership']
                print(f"  2. Secondary Focus: {secondary} ({secondary_proj:.1f} pts, {secondary_own:.1f}% owned)")
            
            print(f"  3. Stack Size: 4-5 players for primary, 2-3 for mini")
            print(f"  4. Target Ownership: <12% total lineup ownership")
            
            print(f"\n📊 LINEUP CONSTRUCTION:")
            print(f"  • 40% {primary} heavy lineups")
            if len(elite_stacks) > 1:
                print(f"  • 30% {elite_stacks[1]['team']} heavy lineups")
            print(f"  • 20% contrarian lineups")
            print(f"  • 10% mini-stack diversification")
        
        return {
            'elite_stacks': elite_stacks,
            'good_stacks': good_stacks,
            'weather_teams': weather_advantages
        }
    
    def run_analysis(self):
        """Run complete GPP stacking analysis"""
        print("🏆 GPP STACKING STRATEGY ANALYZER - FIXED")
        print("="*50)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        try:
            self.load_data()
            recommendations = self.generate_gpp_recommendations()
            
            print(f"\n✅ Analysis Complete!")
            print(f"🎯 Focus on low-owned, high-projection stacks")
            print(f"🌡️ Leverage weather advantages when available")
            print(f"💰 Target GPP tournaments with these strategies")
            print(f"🚨 Only teams playing TODAY are included!")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Error in analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

if __name__ == "__main__":
    analyzer = GPPStackingStrategy()
    results = analyzer.run_analysis()
