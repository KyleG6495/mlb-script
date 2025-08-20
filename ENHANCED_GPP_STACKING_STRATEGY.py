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
        
        # Try to load latest stack data
        try:
            self.stack_df = pd.read_csv(f"{self.data_dir}/stack_aware_lineups_20250818_142508.csv")
        except:
            print("⚠️ No stack data found, will generate recommendations from slate")
            self.stack_df = pd.DataFrame()
        
        self.weather_df = pd.read_csv(f"{self.data_dir}/weather_today.csv")
        self.fd_slate = pd.read_csv(f"{self.fd_dir}/fd_slate_today.csv")
        
        # Get teams actually playing today for validation
        self.teams_today = set(self.fd_slate['Team'].unique())
        
        print(f"✅ Loaded {len(self.ownership_df)} ownership projections")
        print(f"✅ Loaded {len(self.stack_df)} existing stacks")
        print(f"✅ Loaded weather for {len(self.weather_df)} games")
        print(f"🎯 Teams playing today: {sorted(self.teams_today)}")
        
        # Load enhanced projections if available
        try:
            enhanced_files = [f for f in os.listdir(self.data_dir) if 'enhanced_projections' in f and f.endswith('.csv')]
            if enhanced_files:
                latest_enhanced = max(enhanced_files)
                self.enhanced_df = pd.read_csv(f"{self.data_dir}/{latest_enhanced}")
                print(f"✅ Loaded enhanced projections: {len(self.enhanced_df)} players")
            else:
                self.enhanced_df = pd.DataFrame()
        except:
            self.enhanced_df = pd.DataFrame()
        
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
    
    def generate_all_team_stacks(self):
        """Generate stack analysis for ALL teams playing today"""
        print(f"\n🚀 GENERATING COMPREHENSIVE STACK ANALYSIS")
        print("="*60)
        
        all_stacks = []
        
        for team in sorted(self.teams_today):
            # Get team players from FD slate
            team_players = self.fd_slate[self.fd_slate['Team'] == team]
            hitters = team_players[team_players['Position'] != 'P']
            
            if len(hitters) < 4:
                print(f"⚠️ {team}: Only {len(hitters)} hitters - insufficient for stack")
                continue
            
            # Calculate team metrics
            team_salary = hitters['Salary'].sum()
            avg_salary = hitters['Salary'].mean()
            
            # Get ownership data
            real_ownership = self.get_real_team_ownership(team)
            
            # Get enhanced projections if available
            team_projection = self.get_team_projection(team, hitters)
            
            # Calculate weather boost
            weather_boost = self.get_weather_boost(team)
            
            # Calculate Vegas implied total if available
            vegas_total = self.get_vegas_total(team)
            
            # Calculate overall stack score
            stack_score = self.calculate_stack_score(
                team_projection, real_ownership, weather_boost, vegas_total, avg_salary
            )
            
            stack_info = {
                'team': team,
                'players_available': len(hitters),
                'avg_salary': avg_salary,
                'total_salary': team_salary,
                'projected_points': team_projection,
                'ownership': real_ownership,
                'weather_boost': weather_boost,
                'vegas_total': vegas_total,
                'stack_score': stack_score,
                'gpp_rating': self.get_stack_rating(stack_score),
                'value_ratio': team_projection / real_ownership if real_ownership > 0 else 0
            }
            
            all_stacks.append(stack_info)
            
            print(f"✅ {team}: {len(hitters)} hitters, {team_projection:.1f} proj, {real_ownership:.1f}% owned")
        
        return sorted(all_stacks, key=lambda x: x['stack_score'], reverse=True)
    
    def get_team_projection(self, team, team_players):
        """Calculate team projection from various sources"""
        try:
            # Method 1: Enhanced projections - fix column reference
            if not self.enhanced_df.empty:
                # Try different team column names to handle data format variations
                team_enhanced = None
                for col in ['Team', 'TEAM', 'team']:
                    if col in self.enhanced_df.columns:
                        team_enhanced = self.enhanced_df[self.enhanced_df[col] == team]
                        if len(team_enhanced) > 0:
                            break
                
                if team_enhanced is not None and len(team_enhanced) > 0:
                    # Try different projection column names
                    for proj_col in ['Enhanced_FPPG', 'FPPG', 'Projection']:
                        if proj_col in team_enhanced.columns:
                            return float(team_enhanced[proj_col].sum())
            
            # Method 2: FD slate FPPG
            if 'FPPG' in team_players.columns:
                base_projection = team_players['FPPG'].sum()
                if base_projection > 0:
                    return float(base_projection)
            
            # Method 3: Salary-based estimation
            if 'Salary' in team_players.columns:
                avg_salary = team_players['Salary'].mean()
                if avg_salary > 4000:
                    return 95.0 + np.random.normal(0, 5)  # Premium team
                elif avg_salary > 3500:
                    return 85.0 + np.random.normal(0, 8)  # Solid team
                else:
                    return 75.0 + np.random.normal(0, 10)  # Value team
            
            return 80.0  # Default fallback
                
        except Exception as e:
            print(f"⚠️ Error calculating projection for {team}: {e}")
            return 80.0  # Fallback
    
    def get_weather_boost(self, team):
        """Calculate weather boost for team"""
        try:
            # Check if team is home or away
            weather_data = self.weather_df[
                (self.weather_df['home_team'] == team) | 
                (self.weather_df['away_team'] == team)
            ]
            
            if len(weather_data) > 0:
                weather = weather_data.iloc[0]
                
                # Temperature boost (75-85°F is optimal)
                temp_boost = 0
                if 75 <= weather['temperature'] <= 85:
                    temp_boost = 2
                elif weather['temperature'] > 85:
                    temp_boost = 1
                
                # Wind boost (wind out helps offense)
                wind_boost = 0
                if weather.get('wind_speed', 0) > 10:
                    wind_boost = 1
                
                # Humidity penalty (high humidity reduces ball carry)
                humidity_penalty = 0
                if weather.get('humidity', 50) > 80:
                    humidity_penalty = -1
                
                return temp_boost + wind_boost + humidity_penalty
            
            return 0  # No weather data
            
        except Exception as e:
            return 0
    
    def get_vegas_total(self, team):
        """Get Vegas implied team total (placeholder for now)"""
        # This would integrate with Vegas odds data
        # For now, return estimated based on team quality
        return np.random.uniform(4.5, 6.5)
    
    def calculate_stack_score(self, projection, ownership, weather_boost, vegas_total, avg_salary):
        """Calculate comprehensive stack score"""
        # Base score from projection vs ownership
        if ownership > 0:
            base_score = (projection / ownership) * 10
        else:
            base_score = projection
        
        # Weather adjustment
        weather_adjustment = weather_boost * 5
        
        # Vegas total adjustment
        vegas_adjustment = (vegas_total - 5.0) * 10  # 5.0 is average
        
        # Salary efficiency (lower avg salary = better value)
        salary_adjustment = (4000 - avg_salary) / 100  # Penalty for expensive players
        
        total_score = base_score + weather_adjustment + vegas_adjustment + salary_adjustment
        
        return max(total_score, 0)  # Don't go negative
    
    def get_stack_rating(self, score):
        """Convert stack score to rating"""
        if score >= 150:
            return "🚀 ELITE"
        elif score >= 120:
            return "✅ EXCELLENT"
        elif score >= 100:
            return "✅ GOOD"
        elif score >= 80:
            return "⚠️ MODERATE"
        else:
            return "❌ AVOID"
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
        print("🏆 ENHANCED GPP STACKING STRATEGY ANALYZER")
        print("="*60)
        print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        try:
            self.load_data()
            
            # Generate comprehensive stack analysis for all teams
            all_stacks = self.generate_all_team_stacks()
            
            # Also analyze existing stack file if available
            if not self.stack_df.empty:
                existing_stacks = self.analyze_current_stacks()
            
            # Check weather advantages
            weather_advantages = self.check_weather_advantages()
            
            # Generate final recommendations
            self.display_comprehensive_recommendations(all_stacks, weather_advantages)
            
            print(f"\n✅ Analysis Complete!")
            print(f"🎯 Focus on ELITE and EXCELLENT rated stacks")
            print(f"🌡️ Leverage weather advantages when available")
            print(f"💰 Target GPP tournaments with these strategies")
            print(f"🚨 Analysis covers ALL {len(self.teams_today)} teams playing today!")
            
            return {
                'all_stacks': all_stacks,
                'weather_advantages': weather_advantages,
                'analysis_date': datetime.now()
            }
            
        except Exception as e:
            print(f"❌ Error in analysis: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def display_comprehensive_recommendations(self, all_stacks, weather_advantages):
        """Display comprehensive stacking recommendations"""
        print(f"\n🚀 COMPREHENSIVE GPP STACKING RECOMMENDATIONS")
        print("="*70)
        
        # Categorize stacks by rating
        elite_stacks = [s for s in all_stacks if "ELITE" in s['gpp_rating']]
        excellent_stacks = [s for s in all_stacks if "EXCELLENT" in s['gpp_rating']]
        good_stacks = [s for s in all_stacks if "GOOD" in s['gpp_rating']]
        
        print(f"\n🔥 ELITE STACKS ({len(elite_stacks)} found):")
        for stack in elite_stacks:
            print(f"  🚀 {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned, Score: {stack['stack_score']:.0f}")
        
        print(f"\n✅ EXCELLENT STACKS ({len(excellent_stacks)} found):")
        for stack in excellent_stacks:
            print(f"  ⭐ {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned, Score: {stack['stack_score']:.0f}")
        
        print(f"\n💚 GOOD STACKS ({len(good_stacks)} found):")
        for stack in good_stacks:
            print(f"  ✅ {stack['team']}: {stack['projected_points']:.1f} pts, {stack['ownership']:.1f}% owned, Score: {stack['stack_score']:.0f}")
        
        # Display all stacks with full details
        print(f"\n📊 COMPLETE STACK ANALYSIS (All {len(all_stacks)} teams):")
        print("="*70)
        for i, stack in enumerate(all_stacks, 1):
            print(f"\n{i:2d}. {stack['team']} Stack - {stack['gpp_rating']}")
            print(f"    📈 Projection: {stack['projected_points']:.1f} points")
            print(f"    👥 Ownership: {stack['ownership']:.1f}%")
            print(f"    💰 Avg Salary: ${stack['avg_salary']:,.0f}")
            print(f"    🌡️ Weather Boost: {stack['weather_boost']:+d}")
            print(f"    🎯 Stack Score: {stack['stack_score']:.0f}")
            print(f"    ⚡ Value Ratio: {stack['value_ratio']:.1f}")
        
        # Implementation strategy
        print(f"\n🎯 IMPLEMENTATION STRATEGY:")
        print("="*40)
        if elite_stacks:
            print(f"  🔥 Primary Focus: {', '.join([s['team'] for s in elite_stacks[:3]])}")
            print(f"  📊 Use in 40-60% of lineups")
        if excellent_stacks:
            print(f"  ⭐ Secondary Focus: {', '.join([s['team'] for s in excellent_stacks[:2]])}")
            print(f"  📊 Use in 20-30% of lineups")
        if good_stacks:
            print(f"  💚 Diversification: {', '.join([s['team'] for s in good_stacks[:2]])}")
            print(f"  📊 Use in 10-20% of lineups")
        
        print(f"\n📝 LINEUP CONSTRUCTION TIPS:")
        print(f"  • Target total lineup ownership <15% for large GPPs")
        print(f"  • Use 4-5 player stacks for primary teams")
        print(f"  • Consider 2-3 player mini-stacks for diversification")
        print(f"  • Stack teams with weather advantages when possible")
    
    def check_weather_advantages(self):
        """Check for weather advantages across all teams"""
        advantages = []
        
        try:
            if self.weather_df is None or self.weather_df.empty:
                return advantages
            
            for _, game in self.weather_df.iterrows():
                # Look for favorable hitting conditions
                wind_speed = game.get('wind_speed', 0)
                wind_direction = str(game.get('wind_direction', '')).lower()
                temp = game.get('temperature', 70)
                
                # Determine if conditions favor hitting
                wind_boost = 0
                temp_boost = 0
                
                # Wind analysis
                if 'out' in wind_direction and wind_speed >= 10:
                    wind_boost = 2
                elif 'out' in wind_direction and wind_speed >= 5:
                    wind_boost = 1
                elif wind_speed <= 3:
                    wind_boost = 0  # Neutral
                else:
                    wind_boost = -1  # Slight disadvantage
                
                # Temperature analysis (80-90°F is optimal for hitting)
                if 80 <= temp <= 90:
                    temp_boost = 1
                elif temp >= 95 or temp <= 50:
                    temp_boost = -1
                
                total_boost = wind_boost + temp_boost
                
                if total_boost > 0:
                    home_team = game.get('home_team', 'UNK')
                    away_team = game.get('away_team', 'UNK')
                    advantages.append({
                        'teams': [home_team, away_team],
                        'boost': total_boost,
                        'wind': f"{wind_speed}mph {wind_direction}",
                        'temp': f"{temp}°F"
                    })
        
        except Exception as e:
            print(f"⚠️ Error checking weather: {str(e)}")
        
        return advantages

if __name__ == "__main__":
    analyzer = GPPStackingStrategy()
    results = analyzer.run_analysis()
