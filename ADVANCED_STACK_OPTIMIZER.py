"""
DATA: ADVANCED            # Try clean slate first (injured players removed)
            clean_slate_path = '../fd_current_slate/fd_slate_today_clean.csv'
            if os.path.exists(clean_slate_path):
                self.slate = pd.read_csv(clean_slate_path)
                logger.info(f"SUCCESS: Loaded clean slate: {len(self.slate)} players")
            else:
                self.slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
                logger.info(f"SUCCESS: Loaded slate: {len(self.slate)} players")TACKING OPTIMIZER
Identifies optimal team stacks based on multiple factors
"""
import pandas as pd
import numpy as np
import logging
from itertools import combinations
from datetime import datetime

class AdvancedStackOptimizer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def load_stack_data(self):
        """Load data needed for stack optimization"""
        self.logger.info("DATA: LOADING STACK OPTIMIZATION DATA...")
        
        try:
            self.slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
            self.logger.info(f"SUCCESS: Loaded slate: {len(self.slate)} players")
            
            # Try to load Vegas-adjusted data if available
            try:
                import glob
                vegas_files = glob.glob('../data/vegas_adjusted_slate_*.csv')
                if vegas_files:
                    latest_vegas = max(vegas_files)
                    self.slate = pd.read_csv(latest_vegas)
                    self.logger.info(f"SUCCESS: Using Vegas-adjusted data: {latest_vegas}")
            except:
                pass
            
            # Load weather data
            try:
                self.weather = pd.read_csv('../data/weather_today.csv')
                self.logger.info(f"SUCCESS: Loaded weather data: {len(self.weather)} games")
            except:
                self.weather = None
                self.logger.warning("WARNING: No weather data available")
                
            return True
        except Exception as e:
            self.logger.error(f"ERROR: Error loading data: {e}")
            return False
            
    def analyze_opposing_pitchers(self):
        """Analyze quality of opposing pitchers for each team"""
        self.logger.info("TARGET: ANALYZING OPPOSING PITCHERS...")
        
        pitcher_matchups = {}
        
        # Get all starting pitchers
        starting_pitchers = self.slate[
            (self.slate['Position'].str.contains('P', na=False)) & 
            (self.slate['Probable Pitcher'].fillna('').str.lower() == 'yes')
        ]
        
        for _, pitcher in starting_pitchers.iterrows():
            pitcher_team = pitcher['Team']
            opponent = pitcher['Opponent']
            pitcher_fppg = float(pitcher.get('FPPG', 30))
            pitcher_salary = int(pitcher.get('Salary', 8000))
            
            # Calculate pitcher difficulty rating
            if pitcher_fppg > 35 and pitcher_salary > 10000:
                difficulty = 'ELITE'
                stack_multiplier = 0.75  # 25% penalty vs elite
            elif pitcher_fppg > 30 and pitcher_salary > 9000:
                difficulty = 'GOOD'
                stack_multiplier = 0.90  # 10% penalty vs good
            elif pitcher_fppg < 25 or pitcher_salary < 8000:
                difficulty = 'POOR'
                stack_multiplier = 1.25  # 25% bonus vs poor
            else:
                difficulty = 'AVERAGE'
                stack_multiplier = 1.0
                
            pitcher_matchups[opponent] = {
                'opposing_pitcher': pitcher['Nickname'],
                'pitcher_fppg': pitcher_fppg,
                'pitcher_salary': pitcher_salary,
                'difficulty': difficulty,
                'stack_multiplier': stack_multiplier
            }
            
        self.pitcher_matchups = pitcher_matchups
        self.logger.info(f"TARGET: Analyzed {len(pitcher_matchups)} pitcher matchups")
        
    def calculate_team_stack_values(self):
        """Calculate the value of stacking each team"""
        self.logger.info("PROGRESS: CALCULATING TEAM STACK VALUES...")
        
        team_stack_data = {}
        
        # Analyze each team's hitting lineup
        hitters = self.slate[~self.slate['Position'].str.contains('P', na=False)].copy()
        
        for team in hitters['Team'].unique():
            team_hitters = hitters[hitters['Team'] == team].copy()
            
            # Get top 7 hitters by FPPG (typical stack size)
            team_hitters = team_hitters.sort_values('FPPG', ascending=False).head(7)
            
            # Calculate stack metrics
            total_fppg = team_hitters['FPPG'].astype(float).sum()
            avg_fppg = team_hitters['FPPG'].astype(float).mean()
            total_salary = team_hitters['Salary'].astype(int).sum()
            avg_salary = team_hitters['Salary'].astype(int).mean()
            
            # Get Vegas data if available
            team_total = team_hitters['team_total'].iloc[0] if 'team_total' in team_hitters.columns else 4.5
            vegas_mult = team_hitters['vegas_multiplier'].iloc[0] if 'vegas_multiplier' in team_hitters.columns else 1.0
            
            # Apply opposing pitcher multiplier
            pitcher_mult = self.pitcher_matchups.get(team, {}).get('stack_multiplier', 1.0)
            
            # Calculate weather boost
            weather_mult = self.calculate_weather_boost(team)
            
            # Calculate stack value score
            stack_value = (total_fppg * vegas_mult * pitcher_mult * weather_mult) / (total_salary / 1000)
            
            # Get top 4 and 5 hitter combinations for smaller stacks
            top_4_fppg = team_hitters.head(4)['FPPG'].astype(float).sum()
            top_4_salary = team_hitters.head(4)['Salary'].astype(int).sum()
            
            top_5_fppg = team_hitters.head(5)['FPPG'].astype(float).sum()
            top_5_salary = team_hitters.head(5)['Salary'].astype(int).sum()
            
            team_stack_data[team] = {
                'team_total': team_total,
                'vegas_multiplier': vegas_mult,
                'pitcher_multiplier': pitcher_mult,
                'weather_multiplier': weather_mult,
                'opposing_pitcher': self.pitcher_matchups.get(team, {}).get('opposing_pitcher', 'Unknown'),
                'difficulty': self.pitcher_matchups.get(team, {}).get('difficulty', 'AVERAGE'),
                'full_stack_fppg': total_fppg,
                'full_stack_salary': total_salary,
                'stack_value_score': stack_value,
                'top_4_fppg': top_4_fppg,
                'top_4_salary': top_4_salary,
                'top_5_fppg': top_5_fppg,
                'top_5_salary': top_5_salary,
                'avg_fppg': avg_fppg,
                'avg_salary': avg_salary,
                'player_count': len(team_hitters)
            }
            
        self.team_stack_data = team_stack_data
        self.logger.info(f"PROGRESS: Calculated stack values for {len(team_stack_data)} teams")
        
    def calculate_weather_boost(self, team):
        """Calculate weather multiplier for a team"""
        if self.weather is None:
            return 1.0
            
        try:
            # Try home_team column first, then team
            team_weather = self.weather[self.weather['home_team'] == team]
            if team_weather.empty and 'game' in self.weather.columns:
                # Check if team is in the game string (for away teams)
                team_weather = self.weather[self.weather['game'].str.contains(team, na=False)]
                
            if team_weather.empty:
                return 1.0
                
            weather_row = team_weather.iloc[0]
            
            # Weather boost factors
            wind_boost = 1.0
            temp_boost = 1.0
            
            # Wind speed boost (low wind = more home runs)
            if 'wind_speed' in weather_row:
                wind_speed = float(weather_row['wind_speed']) if pd.notna(weather_row['wind_speed']) else 5
                if wind_speed <= 3:
                    wind_boost = 1.1
                elif wind_speed >= 15:
                    wind_boost = 0.9
                    
            # Temperature boost (warmer = more home runs)
            if 'temperature' in weather_row:
                temp = float(weather_row['temperature']) if pd.notna(weather_row['temperature']) else 70
                if temp >= 80:
                    temp_boost = 1.1
                elif temp <= 60:
                    temp_boost = 0.95
                    
            return wind_boost * temp_boost
            
        except Exception as e:
            self.logger.warning(f"WARNING: Error calculating weather boost for {team}: {e}")
            return 1.0
            
    def identify_optimal_stacks(self):
        """Identify the best stacking opportunities"""
        self.logger.info("TARGET: IDENTIFYING OPTIMAL STACKS...")
        
        # Convert to DataFrame for easier analysis
        stack_df = pd.DataFrame.from_dict(self.team_stack_data, orient='index')
        stack_df['team'] = stack_df.index
        
        # Sort by stack value score
        stack_df = stack_df.sort_values('stack_value_score', ascending=False)
        
        # Categorize stacks
        elite_stacks = stack_df[
            (stack_df['team_total'] >= 5.0) | 
            (stack_df['difficulty'] == 'POOR') |
            (stack_df['stack_value_score'] >= stack_df['stack_value_score'].quantile(0.8))
        ].head(5)
        
        value_stacks = stack_df[
            (stack_df['avg_salary'] <= 3200) &
            (stack_df['stack_value_score'] >= stack_df['stack_value_score'].median())
        ].head(3)
        
        contrarian_stacks = stack_df[
            (stack_df['difficulty'] == 'ELITE') &  # Against elite pitchers (low ownership)
            (stack_df['stack_value_score'] >= stack_df['stack_value_score'].quantile(0.4))
        ].head(2)
        
        self.elite_stacks = elite_stacks
        self.value_stacks = value_stacks
        self.contrarian_stacks = contrarian_stacks
        
        self.logger.info(f"TARGET: Identified {len(elite_stacks)} elite stacks, {len(value_stacks)} value stacks, {len(contrarian_stacks)} contrarian stacks")
        
    def generate_stack_lineups(self):
        """Generate optimal lineups using identified stacks"""
        self.logger.info(" GENERATING STACK LINEUPS...")
        
        stack_lineups = []
        
        # Generate lineups for each elite stack
        for _, stack in self.elite_stacks.iterrows():
            team = stack['team']
            lineup = self.build_stack_lineup(team, stack_size=4, strategy='elite')
            if lineup:
                stack_lineups.append(lineup)
                
        # Generate value stack lineups
        for _, stack in self.value_stacks.iterrows():
            team = stack['team']
            lineup = self.build_stack_lineup(team, stack_size=4, strategy='value')
            if lineup:
                stack_lineups.append(lineup)
                
        # Generate contrarian stack lineups
        for _, stack in self.contrarian_stacks.iterrows():
            team = stack['team']
            lineup = self.build_stack_lineup(team, stack_size=3, strategy='contrarian')
            if lineup:
                stack_lineups.append(lineup)
                
        self.stack_lineups = stack_lineups
        self.logger.info(f" Generated {len(stack_lineups)} stack-based lineups")
        
    def build_stack_lineup(self, team, stack_size=4, strategy='balanced'):
        """Build a complete lineup around a team stack"""
        # Get team hitters
        team_hitters = self.slate[
            (self.slate['Team'] == team) & 
            (~self.slate['Position'].str.contains('P', na=False))
        ].copy()
        
        if len(team_hitters) < stack_size:
            return None
            
        # Select stack players
        team_hitters = team_hitters.sort_values('FPPG', ascending=False)
        stack_players = team_hitters.head(stack_size)
        
        # Calculate remaining salary and positions needed
        used_salary = stack_players['Salary'].astype(int).sum()
        remaining_salary = 50000 - used_salary
        
        # Need pitcher + remaining positions
        positions_filled = []
        for _, player in stack_players.iterrows():
            pos = player['Roster Position'].split('/')[0]  # Take first position
            positions_filled.append(pos)
            
        # Simple lineup completion (would be more complex in full system)
        lineup = {
            'team_stack': team,
            'stack_size': stack_size,
            'strategy': strategy,
            'stack_players': stack_players['Nickname'].tolist(),
            'stack_salary': used_salary,
            'stack_fppg': stack_players['FPPG'].astype(float).sum(),
            'remaining_salary': remaining_salary
        }
        
        return lineup
        
    def save_stack_analysis(self):
        """Save stack analysis results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save team stack analysis
        stack_df = pd.DataFrame.from_dict(self.team_stack_data, orient='index')
        stack_df['team'] = stack_df.index
        stack_df = stack_df.sort_values('stack_value_score', ascending=False)
        
        stack_file = f"../data/team_stack_analysis_{timestamp}.csv"
        stack_df.to_csv(stack_file, index=False)
        
        # Save recommended stacks
        recommendations = []
        
        # Add elite stacks
        for _, stack in self.elite_stacks.iterrows():
            recommendations.append({
                'team': stack['team'],
                'category': 'ELITE',
                'team_total': stack['team_total'],
                'opposing_pitcher': stack['opposing_pitcher'],
                'difficulty': stack['difficulty'],
                'stack_value_score': round(stack['stack_value_score'], 2),
                'recommended_size': '4-5 players',
                'strategy': 'Tournament GPP'
            })
            
        # Add value stacks
        for _, stack in self.value_stacks.iterrows():
            recommendations.append({
                'team': stack['team'],
                'category': 'VALUE',
                'team_total': stack['team_total'],
                'opposing_pitcher': stack['opposing_pitcher'],
                'difficulty': stack['difficulty'],
                'stack_value_score': round(stack['stack_value_score'], 2),
                'recommended_size': '3-4 players',
                'strategy': 'Cash games'
            })
            
        # Add contrarian stacks
        for _, stack in self.contrarian_stacks.iterrows():
            recommendations.append({
                'team': stack['team'],
                'category': 'CONTRARIAN',
                'team_total': stack['team_total'],
                'opposing_pitcher': stack['opposing_pitcher'],
                'difficulty': stack['difficulty'],
                'stack_value_score': round(stack['stack_value_score'], 2),
                'recommended_size': '2-3 players',
                'strategy': 'Low ownership GPP'
            })
            
        if recommendations:
            rec_df = pd.DataFrame(recommendations)
            rec_file = f"../data/stack_recommendations_{timestamp}.csv"
            rec_df.to_csv(rec_file, index=False)
            self.logger.info(f"INFO: Saved stack recommendations: {rec_file}")
        
        self.logger.info(f" Saved stack analysis: {stack_file}")
        return stack_file, rec_file if recommendations else None
        
    def run_stack_optimization(self):
        """Run complete stack optimization system"""
        self.logger.info("START: STARTING ADVANCED STACK OPTIMIZATION")
        self.logger.info("="*60)
        
        # Load data
        if not self.load_stack_data():
            return False
            
        # Run analysis
        self.analyze_opposing_pitchers()
        self.calculate_team_stack_values()
        self.identify_optimal_stacks()
        self.generate_stack_lineups()
        
        # Save results
        stack_file, rec_file = self.save_stack_analysis()
        
        # Print summary
        self.logger.info("="*60)
        self.logger.info("TARGET: STACK OPTIMIZATION COMPLETE!")
        self.logger.info(f"DATA: Top 3 Elite Stacks:")
        
        for i, (_, stack) in enumerate(self.elite_stacks.head(3).iterrows(), 1):
            self.logger.info(f"   {i}. {stack['team']} vs {stack['opposing_pitcher']} "
                           f"({stack['difficulty']}) - Score: {stack['stack_value_score']:.2f}")
            
        self.logger.info(f" Results saved: {stack_file}")
        if rec_file:
            self.logger.info(f"INFO: Recommendations: {rec_file}")
            
        return True

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    optimizer = AdvancedStackOptimizer()
    optimizer.run_stack_optimization()
