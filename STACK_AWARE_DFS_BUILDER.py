"""
Stack-Aware DFS Lineup Builder
Integrates weather, park factors, and team correlation for optimal stacking
"""

import pandas as pd
import numpy as np
from datetime import datetime
import os
import logging
from itertools import combinations
import random

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StackAwareDFSBuilder:
    
    def __init__(self):
        self.salary_cap = 35000
        self.positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        
    def load_data(self):
        """Load enhanced projections and weather data"""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), "data")
            
            # Load enhanced projections
            today = datetime.now().strftime("%Y%m%d")
            import glob
            enhanced_files = glob.glob(os.path.join(data_dir, f"game_state_enhanced_projections_{today}_*.csv"))
            
            if enhanced_files:
                proj_file = max(enhanced_files, key=os.path.getmtime)
                self.players_df = pd.read_csv(proj_file)
                logger.info(f"📊 Loaded {len(self.players_df)} enhanced projections")
            else:
                # Fallback to FD slate
                fd_file = os.path.join(data_dir, "..", "fd_current_slate", "fd_slate_today.csv")
                self.players_df = pd.read_csv(fd_file)
                # Add basic enhanced FPPG column
                self.players_df['enhanced_fppg'] = self.players_df['FPPG'] 
                logger.info(f"📊 Loaded {len(self.players_df)} players from FD slate")
            
            # Load weather data
            weather_file = os.path.join(data_dir, "weather_today.csv")
            if os.path.exists(weather_file):
                self.weather_df = pd.read_csv(weather_file)
                logger.info(f"🌦️  Loaded weather data for {len(self.weather_df)} games")
            else:
                self.weather_df = pd.DataFrame()
                logger.warning("No weather data found")
                
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def analyze_stack_opportunities(self):
        """Find the best stacking opportunities with weather/park context"""
        
        # Get hitters only
        hitters = self.players_df[self.players_df['Position'] != 'P'].copy()
        
        # Create weather context
        team_weather = {}
        if not self.weather_df.empty:
            for _, game in self.weather_df.iterrows():
                home_team = game.get('home_team', '')
                away_team = game.get('away_team', '')
                
                # Hitter favorability
                temp = game.get('temperature', 75)
                wind_speed = game.get('wind_speed', 5)
                wind_direction = game.get('wind_direction', '')
                
                hitter_boost = 0
                if temp >= 80: hitter_boost += 1.5
                if 'out' in wind_direction.lower() and wind_speed >= 8: hitter_boost += 2.0
                if wind_speed <= 3: hitter_boost += 0.5  # Calm conditions
                
                team_weather[home_team] = hitter_boost
                team_weather[away_team] = hitter_boost
        
        # Find best stack opportunities
        stack_opportunities = []
        
        for team in hitters['Team'].unique():
            team_hitters = hitters[hitters['Team'] == team].copy()
            
            if len(team_hitters) < 3:
                continue
            
            # Get top hitters by enhanced projection
            proj_col = 'enhanced_fppg' if 'enhanced_fppg' in team_hitters.columns else 'FPPG'
            top_hitters = team_hitters.nlargest(5, proj_col)
            
            # Calculate stack metrics
            total_proj = top_hitters[proj_col].sum()
            total_salary = top_hitters['Salary'].sum()
            
            # Get ownership (use default if missing)
            if 'ownership' in top_hitters.columns:
                avg_ownership = top_hitters['ownership'].mean()
            else:
                # Estimate ownership based on salary/projection
                avg_ownership = 8 + (total_salary / len(top_hitters) / 1000) * 2
            
            # Weather boost
            weather_boost = team_weather.get(team, 0)
            
            # Stack score calculation
            base_score = total_proj
            ownership_bonus = max(0, (12 - avg_ownership) * 0.5)  # Reward low ownership
            weather_bonus = weather_boost * 2.0
            value_bonus = max(0, (total_proj / (total_salary / 1000) - 2.8) * 3)
            
            stack_score = base_score + ownership_bonus + weather_bonus + value_bonus
            
            stack_info = {
                'team': team,
                'players': top_hitters,
                'total_projection': round(total_proj, 1),
                'total_salary': total_salary,
                'avg_ownership': round(avg_ownership, 1),
                'weather_boost': weather_boost,
                'stack_score': round(stack_score, 1),
                'top_4_players': top_hitters.head(4)
            }
            
            stack_opportunities.append(stack_info)
        
        # Sort by stack score
        stack_opportunities.sort(key=lambda x: x['stack_score'], reverse=True)
        
        logger.info(f"⚡ Found {len(stack_opportunities)} stack opportunities")
        
        # Show top 5
        for i, stack in enumerate(stack_opportunities[:5], 1):
            logger.info(f"{i}. {stack['team']}: {stack['stack_score']} pts")
            logger.info(f"   Proj: {stack['total_projection']} | Own: {stack['avg_ownership']}% | Weather: +{stack['weather_boost']}")
        
        return stack_opportunities
    
    def build_stack_lineup(self, stack_info, lineup_id):
        """Build a lineup around a team stack"""
        
        try:
            # Start with 4 players from the stack team
            stack_players = stack_info['top_4_players'].copy()
            
            lineup = {
                'lineup_id': lineup_id,
                'stack_team': stack_info['team'],
                'players': [],
                'total_salary': 0,
                'total_projection': 0
            }
            
            # Add stack players to lineup
            for _, player in stack_players.iterrows():
                proj_col = 'enhanced_fppg' if 'enhanced_fppg' in player.index else 'FPPG'
                
                # Handle different name column formats
                if 'Nickname' in player.index:
                    player_name = player['Nickname']
                elif 'Name' in player.index:
                    player_name = player['Name']
                elif 'First Name' in player.index and 'Last Name' in player.index:
                    player_name = f"{player['First Name']} {player['Last Name']}"
                else:
                    player_name = "Unknown Player"
                
                lineup['players'].append({
                    'name': player_name,
                    'position': player['Position'],
                    'team': player['Team'],
                    'salary': player['Salary'],
                    'projection': player[proj_col],
                    'role': 'STACK'
                })
                
                lineup['total_salary'] += player['Salary']
                lineup['total_projection'] += player[proj_col]
            
            # Fill remaining positions
            remaining_salary = self.salary_cap - lineup['total_salary']
            used_names = [p['name'] for p in lineup['players']]
            
            # Helper function to get player name
            def get_player_name(player):
                if 'Nickname' in player.index:
                    return player['Nickname']
                elif 'Name' in player.index:
                    return player['Name']
                elif 'First Name' in player.index and 'Last Name' in player.index:
                    return f"{player['First Name']} {player['Last Name']}"
                else:
                    return "Unknown Player"
            
            # Get remaining players (exclude stack team to diversify)
            other_players = self.players_df[
                (self.players_df['Team'] != stack_info['team'])
            ].copy()
            
            # Filter out already used players
            other_players = other_players[
                ~other_players.apply(lambda x: get_player_name(x) in used_names, axis=1)
            ]
            
            # Fill remaining spots with best available value
            positions_filled = {'P': 0, 'C': 0, '1B': 0, '2B': 0, '3B': 0, 'SS': 0, 'OF': 0}
            
            # Count stack positions
            for player in lineup['players']:
                pos = player['position']
                if pos in positions_filled:
                    positions_filled[pos] += 1
                elif pos in ['LF', 'CF', 'RF']:  # Outfield variants
                    positions_filled['OF'] += 1
            
            # Add remaining players
            proj_col = 'enhanced_fppg' if 'enhanced_fppg' in other_players.columns else 'FPPG'
            
            # Sort by value (projection per 1K salary)
            other_players['value'] = other_players[proj_col] / (other_players['Salary'] / 1000)
            other_players = other_players.sort_values('value', ascending=False)
            
            for _, player in other_players.iterrows():
                if len(lineup['players']) >= 9:  # 9 total players
                    break
                    
                if lineup['total_salary'] + player['Salary'] > self.salary_cap:
                    continue
                
                # Check position needs
                pos = player['Position']
                can_add = False
                
                if pos in positions_filled and positions_filled[pos] < self.positions_needed.get(pos, 0):
                    can_add = True
                elif pos in ['LF', 'CF', 'RF'] and positions_filled['OF'] < 3:
                    can_add = True
                    pos = 'OF'  # Normalize to OF
                
                if can_add:
                    lineup['players'].append({
                        'name': get_player_name(player),
                        'position': player['Position'],
                        'team': player['Team'],
                        'salary': player['Salary'],
                        'projection': player[proj_col],
                        'role': 'COMPLEMENT'
                    })
                    
                    lineup['total_salary'] += player['Salary']
                    lineup['total_projection'] += player[proj_col]
                    positions_filled[pos] += 1
            
            return lineup
            
        except Exception as e:
            logger.error(f"Error building stack lineup: {e}")
            return None
    
    def generate_stack_lineups(self, num_lineups=15):
        """Generate multiple lineups with different stacking strategies"""
        
        logger.info(f"🏗️  BUILDING {num_lineups} STACK-AWARE LINEUPS")
        
        stack_opportunities = self.analyze_stack_opportunities()
        
        if not stack_opportunities:
            logger.warning("No stack opportunities found")
            return []
        
        lineups = []
        
        # Build lineups with top stacks
        for i in range(min(num_lineups, len(stack_opportunities))):
            stack = stack_opportunities[i]
            lineup = self.build_stack_lineup(stack, i + 1)
            
            if lineup and len(lineup['players']) >= 8:  # Valid lineup
                lineups.append(lineup)
                logger.info(f"✅ Lineup {i+1}: {stack['team']} stack ({len(lineup['players'])} players)")
        
        return lineups
    
    def save_lineups(self, lineups):
        """Save lineups in tournament format"""
        
        if not lineups:
            logger.warning("No lineups to save")
            return
        
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(script_dir), "data")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"stack_aware_lineups_{timestamp}.csv"
            filepath = os.path.join(data_dir, filename)
            
            # Convert to tournament format
            tournament_lineups = []
            
            for lineup in lineups:
                # Create position mapping
                positions = {'P': '', 'C': '', '1B': '', '2B': '', '3B': '', 'SS': '', 'OF1': '', 'OF2': '', 'OF3': ''}
                of_count = 0
                
                for player in lineup['players']:
                    pos = player['position']
                    name = player['name']
                    
                    if pos in positions and positions[pos] == '':
                        positions[pos] = name
                    elif pos in ['LF', 'CF', 'RF', 'OF']:
                        if of_count < 3:
                            positions[f'OF{of_count + 1}'] = name
                            of_count += 1
                
                # Calculate metrics
                total_salary = sum(p['salary'] for p in lineup['players'])
                total_projection = sum(p['projection'] for p in lineup['players'])
                avg_ownership = 8.0  # Default
                
                tournament_lineups.append({
                    'Lineup': lineup['lineup_id'],
                    'P': positions['P'],
                    'C': positions['C'],
                    '1B': positions['1B'],
                    '2B': positions['2B'],
                    '3B': positions['3B'],
                    'SS': positions['SS'],
                    'OF1': positions['OF1'],
                    'OF2': positions['OF2'],
                    'OF3': positions['OF3'],
                    'Total_Salary': total_salary,
                    'Projected_Points': round(total_projection, 1),
                    'Avg_Ownership': avg_ownership,
                    'Leverage_Score': round(total_projection * 0.3, 1),
                    'Tournament_Score': round(total_projection * 0.9, 1),
                    'Stack_Team': f"{lineup['stack_team']} (4-stack)"
                })
            
            # Save to CSV
            df = pd.DataFrame(tournament_lineups)
            df.to_csv(filepath, index=False)
            
            logger.info(f"💾 Saved {len(tournament_lineups)} stack-aware lineups: {filename}")
            
            # Show stack summary
            stack_counts = df['Stack_Team'].value_counts()
            logger.info(f"📊 STACK SUMMARY:")
            for stack, count in stack_counts.items():
                logger.info(f"   {stack}: {count} lineups")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error saving lineups: {e}")
            return None

def main():
    """Main execution"""
    print("🏗️  STACK-AWARE DFS LINEUP BUILDER")
    print("=" * 50)
    
    builder = StackAwareDFSBuilder()
    
    # Load data
    if not builder.load_data():
        print("❌ Failed to load data")
        return
    
    # Generate stack-aware lineups
    lineups = builder.generate_stack_lineups(15)
    
    if lineups:
        # Save lineups
        filepath = builder.save_lineups(lineups)
        
        if filepath:
            print(f"\n✅ SUCCESS!")
            print(f"📁 Stack-aware lineups saved: {os.path.basename(filepath)}")
            print(f"🎯 Ready for tournament play with proper team stacking!")
        else:
            print("❌ Failed to save lineups")
    else:
        print("❌ No valid lineups generated")

if __name__ == "__main__":
    main()
