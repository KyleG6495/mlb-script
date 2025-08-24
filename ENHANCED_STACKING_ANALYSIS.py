"""
Enhanced Stacking System for MLB DFS
Combines weather, park factors, and team correlation for optimal stacking
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_stack_opportunities():
    """Analyze current stack opportunities with weather/park integration"""
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), "data")
        
        # Load current projections with weather/park factors
        projections_file = None
        today = datetime.now().strftime("%Y%m%d")
        
        # Try to find enhanced projections with weather/park data
        import glob
        enhanced_files = glob.glob(os.path.join(data_dir, f"game_state_enhanced_projections_{today}_*.csv"))
        if enhanced_files:
            projections_file = max(enhanced_files, key=os.path.getmtime)
            logger.info(f"🌦️  Using weather-enhanced projections: {os.path.basename(projections_file)}")
        
        if not projections_file:
            logger.warning("No enhanced projections found - using basic slate")
            return []
            
        df = pd.read_csv(projections_file)
        
        # Load weather data
        weather_file = os.path.join(data_dir, "weather_today.csv")
        weather_df = pd.read_csv(weather_file) if os.path.exists(weather_file) else pd.DataFrame()
        
        # Create weather/park context for each team
        team_contexts = {}
        if not weather_df.empty:
            for _, game in weather_df.iterrows():
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                
                # Hitter-friendly conditions
                temp = game.get('temperature', 75)
                wind_speed = game.get('wind_speed', 5) 
                wind_direction = game.get('wind_direction', '')
                humidity = game.get('humidity', 50)
                
                # Calculate hitter favorability score
                hitter_score = 0
                
                # Temperature factor (warmer = better for hitters)
                if temp >= 80: hitter_score += 2
                elif temp >= 75: hitter_score += 1
                elif temp < 65: hitter_score -= 1
                
                # Wind factor 
                if 'out' in wind_direction.lower() and wind_speed >= 10:
                    hitter_score += 3  # Strong tailwind
                elif 'out' in wind_direction.lower() and wind_speed >= 5:
                    hitter_score += 1  # Light tailwind
                elif 'in' in wind_direction.lower() and wind_speed >= 10:
                    hitter_score -= 2  # Strong headwind
                
                # Humidity (lower is better for carry)
                if humidity < 40: hitter_score += 1
                elif humidity > 70: hitter_score -= 1
                
                team_contexts[home_team] = {
                    'weather_score': hitter_score,
                    'temp': temp,
                    'wind': f"{wind_speed}mph {wind_direction}",
                    'humidity': humidity,
                    'is_home': True
                }
                
                team_contexts[away_team] = {
                    'weather_score': hitter_score,
                    'temp': temp, 
                    'wind': f"{wind_speed}mph {wind_direction}",
                    'humidity': humidity,
                    'is_home': False
                }
        
        # Filter to hitters only
        hitters_df = df[df['Position'] != 'P'].copy()
        
        # Calculate stack opportunities for each team
        stack_opportunities = []
        
        for team in hitters_df['Team'].unique():
            team_players = hitters_df[hitters_df['Team'] == team].copy()
            
            if len(team_players) < 3:
                continue
                
            # Get top 4-5 hitters for potential stack
            top_hitters = team_players.nlargest(5, 'FPPG')
            
            # Calculate stack metrics
            total_projection = top_hitters['FPPG'].sum()
            total_salary = top_hitters['Salary'].sum()
            avg_ownership = top_hitters.get('ownership', pd.Series([12] * len(top_hitters))).mean()
            
            # Weather/park context
            context = team_contexts.get(team, {'weather_score': 0, 'temp': 75, 'wind': 'calm', 'humidity': 50})
            
            # Stack scoring formula
            base_score = total_projection * 0.7  # Projection weight
            ownership_bonus = max(0, (15 - avg_ownership) * 0.3)  # Reward low ownership
            weather_bonus = context['weather_score'] * 1.5  # Weather factor
            value_bonus = (total_projection / (total_salary / 1000) - 2.5) * 2  # Value factor
            
            final_score = base_score + ownership_bonus + weather_bonus + value_bonus
            
            stack_info = {
                'team': team,
                'projection': round(total_projection, 1),
                'salary': total_salary,
                'ownership': round(avg_ownership, 1),
                'stack_score': round(final_score, 1),
                'weather_score': context['weather_score'],
                'conditions': f"{context['temp']}°F, {context['wind']}, {context['humidity']}% humidity",
                'players': top_hitters['Nickname'].tolist()[:4],
                'value': round(total_projection / (total_salary / 1000), 2),
                'recommendation': 'ELITE' if final_score >= 25 else 'GOOD' if final_score >= 20 else 'CONSIDER'
            }
            
            stack_opportunities.append(stack_info)
        
        # Sort by stack score
        stack_opportunities.sort(key=lambda x: x['stack_score'], reverse=True)
        
        logger.info(f"⚡ STACK ANALYSIS COMPLETE")
        logger.info(f"📊 Found {len(stack_opportunities)} stack opportunities")
        
        # Show top 5 stacks
        logger.info(f"\n🏆 TOP 5 STACK OPPORTUNITIES:")
        for i, stack in enumerate(stack_opportunities[:5], 1):
            logger.info(f"{i}. {stack['team']} - Score: {stack['stack_score']}")
            logger.info(f"   Projection: {stack['projection']} | Ownership: {stack['ownership']}%")
            logger.info(f"   Weather: {stack['conditions']} (Score: {stack['weather_score']})")
            logger.info(f"   Players: {', '.join(stack['players'])}")
            logger.info(f"   Recommendation: {stack['recommendation']}")
            logger.info("")
        
        return stack_opportunities
        
    except Exception as e:
        logger.error(f"Error analyzing stacks: {e}")
        return []

def fix_dashboard_stack_detection():
    """Fix the dashboard to properly detect stacks from our lineups"""
    
    logger.info("🔧 FIXING DASHBOARD STACK DETECTION")
    
    # The issue is that the dashboard looks for stacks in projection files
    # instead of actual lineup files. We need to analyze our lineup files
    # and detect the team stacking patterns within them.
    
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(os.path.dirname(script_dir), "data")
        
        # Find today's lineup files
        today = datetime.now().strftime("%Y%m%d") 
        
        import glob
        lineup_files = glob.glob(os.path.join(data_dir, f"*lineup*{today}_*.csv"))
        
        if not lineup_files:
            logger.warning("No lineup files found for today")
            return
            
        # Check the elite tournament lineups specifically
        elite_files = [f for f in lineup_files if 'elite_tournament' in f]
        if elite_files:
            elite_file = max(elite_files, key=os.path.getmtime)
            logger.info(f"📋 Analyzing: {os.path.basename(elite_file)}")
            
            df = pd.read_csv(elite_file)
            
            # Analyze each lineup for stacking patterns
            positions = ['C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']
            stack_analysis = []
            
            for idx, row in df.iterrows():
                teams = []
                players = []
                
                for pos in positions:
                    if pos in df.columns:
                        player = str(row[pos])
                        players.append(player)
                        
                        # Try to extract team from player name
                        # Look for team in parentheses or from our roster data
                        if '(' in player and ')' in player:
                            team = player.split('(')[-1].replace(')', '').strip()
                            teams.append(team)
                
                # Count team occurrences
                from collections import Counter
                team_counts = Counter(teams)
                
                # Determine stack
                stack_team = "No Stack"
                max_count = 0
                
                if team_counts:
                    max_team, max_count = team_counts.most_common(1)[0]
                    if max_count >= 3:  # 3+ players from same team = stack
                        stack_team = f"{max_team} ({max_count}-stack)"
                
                stack_analysis.append({
                    'lineup': idx + 1,
                    'stack_team': stack_team,
                    'max_team_count': max_count,
                    'team_breakdown': dict(team_counts)
                })
            
            # Show results
            logger.info(f"\n📊 LINEUP STACK ANALYSIS:")
            stack_counts = {}
            for analysis in stack_analysis:
                stack = analysis['stack_team']
                stack_counts[stack] = stack_counts.get(stack, 0) + 1
                
            for stack, count in stack_counts.items():
                logger.info(f"   {stack}: {count} lineups")
                
            # If we found stacks, update the lineup file
            if any(analysis['max_team_count'] >= 3 for analysis in stack_analysis):
                logger.info(f"✅ Found actual stacks in lineups!")
                
                # Update the Stack_Team column with correct data
                df['Stack_Team'] = [analysis['stack_team'] for analysis in stack_analysis]
                df.to_csv(elite_file, index=False)
                logger.info(f"💾 Updated {os.path.basename(elite_file)} with correct stack information")
            else:
                logger.warning("❌ No 3+ stacks detected in lineups - stacking logic may need improvement")
        
    except Exception as e:
        logger.error(f"Error fixing dashboard: {e}")

if __name__ == "__main__":
    print("🏟️  ENHANCED STACKING ANALYSIS")
    print("=" * 50)
    
    # 1. Analyze stack opportunities with weather/park factors
    stack_opportunities = analyze_stack_opportunities()
    
    print("\n" + "=" * 50)
    
    # 2. Fix dashboard stack detection
    fix_dashboard_stack_detection()
    
    print("\n✅ Stack analysis complete!")
