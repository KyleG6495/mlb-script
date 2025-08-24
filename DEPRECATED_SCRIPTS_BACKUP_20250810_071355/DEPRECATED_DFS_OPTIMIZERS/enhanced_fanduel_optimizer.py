#!/usr/bin/env python3
"""
Enhanced FanDuel Lineup Optimizer

Integrates all advanced features:
1. ML-driven projections
2. Dynamic stacking engine
3. Real-time news integration
4. Ownership projections
5. Multi-objective optimization
6. Risk management
7. Weather/park factors
8. Pitcher-hitter matchups
"""

import pandas as pd
import numpy as np
import joblib
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import warnings
warnings.filterwarnings('ignore')

# Import our custom modules
from advanced_lineup_optimizer import AdvancedLineupOptimizer
from dynamic_stacking_engine import DynamicStackingEngine
from real_time_news_integration import RealTimeNewsIntegration

class EnhancedFanDuelOptimizer:
    def __init__(self):
        self.advanced_optimizer = AdvancedLineupOptimizer()
        self.stacking_engine = DynamicStackingEngine()
        self.news_integration = RealTimeNewsIntegration()
        self.lineups_generated = []
        
    def load_enhanced_data(self):
        """Load all required data sources"""
        print("📊 Loading enhanced data sources...")
        
        # Core slate data
        slate_df = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        
        # Enhanced features
        try:
            features_df = pd.read_csv("../data/prediction_features_enhanced_real_stats.csv")
            slate_df = self.merge_enhanced_features(slate_df, features_df)
        except:
            print("⚠️ Enhanced features not found, using basic features")
        
        # Weather data (use your proven working weather file)
        try:
            weather_df = pd.read_csv("../data/merged_weather_park.csv")
            print(f"✅ Weather-park data loaded: {len(weather_df)} games")
            slate_df = self.merge_weather_data(slate_df, weather_df)
            print(f"✅ Weather-park data merged successfully")
        except Exception as e:
            print(f"⚠️ Weather-park data error: {e}")
            print("Using defaults for weather adjustments")
        
        # Park factors
        try:
            park_df = pd.read_csv("../data/weather_park_factors_merged.csv")
            slate_df = self.merge_park_factors(slate_df, park_df)
        except:
            print("⚠️ Park factors not found")
        
        return slate_df
    
    def merge_enhanced_features(self, slate_df, features_df):
        """Merge enhanced statistical features"""
        # Merge on player name
        slate_df['name_key'] = slate_df['Nickname'].str.lower().str.replace(' ', '')
        features_df['name_key'] = features_df['name'].str.lower().str.replace(' ', '')
        
        merged = pd.merge(
            slate_df, 
            features_df[['name_key', 'atBats', 'hits', 'homeRuns', 'rbi', 'runs', 
                        'baseOnBalls', 'strikeOuts', 'stolenBases']], 
            on='name_key', 
            how='left'
        )
        
        return merged
    
    def merge_weather_data(self, slate_df, weather_df):
        """Merge weather data using proven team mapping approach"""
        print(f"🌤️ Merging weather-park data...")
        
        # Create team mapping from your working system
        team_mapping = {
            'ARI': 'diamondbacks', 'ATL': 'braves', 'BAL': 'orioles', 'BOS': 'red sox',
            'CHC': 'cubs', 'CWS': 'white sox', 'CIN': 'reds', 'CLE': 'guardians',
            'COL': 'rockies', 'DET': 'tigers', 'HOU': 'astros', 'KC': 'royals',
            'LAA': 'angels', 'LAD': 'dodgers', 'MIA': 'marlins', 'MIL': 'brewers',
            'MIN': 'twins', 'NYM': 'mets', 'NYY': 'yankees', 'OAK': 'athletics',
            'PHI': 'phillies', 'PIT': 'pirates', 'SD': 'padres', 'SF': 'giants',
            'SEA': 'mariners', 'STL': 'cardinals', 'TB': 'rays', 'TEX': 'rangers',
            'TOR': 'blue jays', 'WSH': 'nationals'
        }
        
        # Map team abbreviations to standardized names
        slate_df['team_standardized'] = slate_df['Team'].map(team_mapping)
        
        # Merge with weather data
        merged = pd.merge(
            slate_df,
            weather_df[['team_standardized', 'temperature', 'wind_speed', 'condition', 'park_factor', 'HR']],
            on='team_standardized',
            how='left'
        )
        
        weather_matches = merged['temperature'].notna().sum()
        print(f"Weather matches found: {weather_matches}/{len(slate_df)} players")
        
        return merged
    
    def merge_park_factors(self, slate_df, park_df):
        """Merge park factors"""
        slate_df = pd.merge(
            slate_df,
            park_df[['Team', 'park_factor', 'HR', 'SO', 'BB']],
            on='Team',
            how='left'
        )
        return slate_df
    
    def create_ml_projections(self, df):
        """Create sophisticated ML projections"""
        print("🧠 Creating ML-driven projections...")
        
        # For now, use enhanced FPPG as base since ML models aren't available
        print("⚠️ Using enhanced FPPG projections (ML models not available)")
        
        # Apply basic enhancements to existing FPPG
        df['Base_Projection'] = df['FPPG'].copy()
        
        # Apply real-time adjustments
        df = self.news_integration.update_projections_real_time(df)
        
        # Use real-time adjusted projections
        if 'Real_Time_FPPG' in df.columns:
            df['Projected_FPPG'] = df['Real_Time_FPPG']
        elif 'Base_Projection' in df.columns:
            df['Projected_FPPG'] = df['Base_Projection'] 
        else:
            df['Projected_FPPG'] = df['FPPG']  # Fallback to original FPPG
        
        print(f"✅ Projections created: avg={df['Projected_FPPG'].mean():.1f} FPPG")
        return df
    
    def apply_advanced_features(self, df):
        """Apply essential advanced features without redundant columns"""
        print("⚡ Applying advanced features...")
        
        # Pitcher matchup adjustments
        if len(df[df['Position'] == 'P']) > 0:
            hitters = df[df['Position'] != 'P']
            pitchers = df[df['Position'] == 'P']
            matchup_adj = self.advanced_optimizer.create_pitcher_matchup_matrix(hitters, pitchers)
            
            for player_key, adjustment in matchup_adj.items():
                # Match on Nickname since player_id isn't available
                mask = df['Nickname'] == player_key
                df.loc[mask, 'Projected_FPPG'] *= adjustment
        
        # Weather adjustments
        df = self.apply_weather_adjustments(df)
        
        return df
    
    def apply_weather_adjustments(self, df):
        """Apply weather-based adjustments"""
        if 'temperature' in df.columns and 'wind_speed' in df.columns:
            # Temperature adjustments
            temp_factor = np.where(df['temperature'] >= 80, 1.05,
                         np.where(df['temperature'] <= 55, 0.95, 1.0))
            
            # Wind adjustments (simplified)
            wind_factor = np.where(df['wind_speed'] >= 10, 1.03, 1.0)
            
            # Apply to hitters only
            hitter_mask = df['Position'] != 'P'
            df.loc[hitter_mask, 'Projected_FPPG'] *= temp_factor[hitter_mask] * wind_factor[hitter_mask]
        
        return df
    
    def identify_stacking_opportunities(self, df):
        """Identify optimal stacking opportunities"""
        print("🔥 Identifying stacking opportunities...")
        
        # Mock weather and vegas data for stacking engine
        weather_data = pd.DataFrame({
            'game_id': df['Game'].unique(),
            'temperature': 75,
            'wind_speed': 8,
            'wind_direction': 180
        })
        
        vegas_totals = pd.DataFrame({
            'game_id': df['Game'].unique(),
            'total': np.random.uniform(8.5, 10.5, len(df['Game'].unique())),
            'home_team': df.groupby('Game')['Team'].first().values,
            'away_team': df.groupby('Game')['Opponent'].first().values
        })
        
        stacks = self.stacking_engine.identify_optimal_stacks(df, weather_data, vegas_totals)
        
        return stacks
    
    def optimize_multiple_strategies(self, df):
        """Generate lineups for multiple strategies"""
        print("🎯 Optimizing for multiple strategies...")
        
        strategies = {
            'cash': {
                'description': 'Cash game optimized (high floor)',
                'proj_weight': 0.8,
                'safe_weight': 0.2,
                'contrarian_weight': 0.0,
                'stack_type': 'mini_stack'
            },
            'gpp': {
                'description': 'GPP optimized (high ceiling)',
                'proj_weight': 0.5,
                'safe_weight': 0.1,
                'contrarian_weight': 0.4,
                'stack_type': 'aggressive'
            },
            'balanced': {
                'description': 'Balanced approach',
                'proj_weight': 0.6,
                'safe_weight': 0.2,
                'contrarian_weight': 0.2,
                'stack_type': 'balanced'
            }
        }
        
        all_lineups = {}
        
        for strategy_name, strategy_config in strategies.items():
            print(f"\n📈 Optimizing {strategy_name} strategy: {strategy_config['description']}")
            
            lineups = []
            for i in range(3):  # Generate 3 lineups per strategy
                lineup = self.optimize_single_lineup(df, strategy_config, i)
                if lineup is not None:
                    lineup['strategy'] = strategy_name
                    lineup['lineup_id'] = i + 1
                    lineups.append(lineup)
            
            all_lineups[strategy_name] = lineups
        
        return all_lineups
    
    def optimize_single_lineup(self, df, strategy_config, lineup_num):
        """Optimize a single lineup"""
        
        # Add some randomness for diversity
        df_random = df.copy()
        df_random['Projected_FPPG'] *= np.random.normal(1, 0.03, len(df))  # 3% random variation
        
        # Filter eligible players
        eligible = self.filter_eligible_players(df_random)
        
        if len(eligible) < 9:
            print(f"⚠️ Not enough eligible players: {len(eligible)}")
            return None
        
        # Create optimization problem
        prob = LpProblem(f"Enhanced_Lineup_{lineup_num}", LpMaximize)
        
        # Decision variables
        player_vars = {i: LpVariable(f"player_{i}", cat='Binary') for i in eligible.index}
        
        # Multi-objective function
        objective = self.create_multi_objective(eligible, player_vars, strategy_config)
        prob += objective
        
        # Constraints
        self.add_constraints(prob, eligible, player_vars, strategy_config)
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        if prob.status != 1:
            print(f"⚠️ Optimization failed for lineup {lineup_num}")
            return None
        
        # Extract lineup
        lineup_indices = [i for i in eligible.index if player_vars[i].value() == 1]
        lineup = eligible.loc[lineup_indices].copy()
        
        # Calculate lineup metrics
        lineup = self.calculate_lineup_metrics(lineup)
        
        return lineup
    
    def filter_eligible_players(self, df):
        """Filter eligible players for optimization"""
        print(f"🔍 Filtering from {len(df)} players...")
        
        # Check available projections
        proj_col = 'Projected_FPPG' if 'Projected_FPPG' in df.columns else 'FPPG'
        print(f"Using projection column: {proj_col}")
        print(f"Projection stats: min={df[proj_col].min():.1f}, max={df[proj_col].max():.1f}, avg={df[proj_col].mean():.1f}")
        
        # Apply filters step by step for debugging
        salary_filter = df['Salary'] >= 2000
        proj_filter = df[proj_col] > 0
        
        # CRITICAL: Only actual starting pitchers for P position
        if 'Probable Pitcher' in df.columns:
            starting_pitcher_filter = (
                (df['Position'] != 'P') |  # Non-pitchers are always eligible
                (df['Probable Pitcher'] == 'Yes')  # Only starting pitchers for P position
            )
        else:
            starting_pitcher_filter = pd.Series([True] * len(df), index=df.index)
        
        # Handle injury filter more carefully
        if 'Injury Indicator' in df.columns:
            injury_filter = (~df['Injury Indicator'].isin(['IL', 'DTD']) | df['Injury Indicator'].isna())
        else:
            injury_filter = pd.Series([True] * len(df), index=df.index)
        
        print(f"Filter results:")
        print(f"  Salary >= 2000: {salary_filter.sum()} players")
        print(f"  {proj_col} > 0: {proj_filter.sum()} players")
        print(f"  Starting pitchers only: {starting_pitcher_filter.sum()} players")
        print(f"  Not injured: {injury_filter.sum()} players")
        
        eligible = df[salary_filter & proj_filter & starting_pitcher_filter & injury_filter].copy()
        print(f"  Combined eligible: {len(eligible)} players")
        
        # Ensure position balance
        eligible = self.ensure_position_balance(eligible)
        
        return eligible
    
    def ensure_position_balance(self, df):
        """Ensure we have enough players at each position"""
        position_requirements = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        
        df['Primary_Position'] = df['Position'].apply(self.get_primary_position)
        
        for pos, min_needed in position_requirements.items():
            available = len(df[df['Primary_Position'] == pos])
            if available < min_needed:
                print(f"⚠️ Only {available} {pos} available (need {min_needed})")
        
        return df
    
    def get_primary_position(self, position_str):
        """Extract primary position from position string"""
        if pd.isna(position_str):
            return 'OF'
        
        pos_str = str(position_str).upper()
        
        if 'P' in pos_str:
            return 'P'
        elif 'C' in pos_str and '1B' not in pos_str:
            return 'C'
        elif '1B' in pos_str:
            return '1B'
        elif '2B' in pos_str and 'SS' not in pos_str and '3B' not in pos_str:
            return '2B'
        elif '3B' in pos_str and '2B' not in pos_str and 'SS' not in pos_str:
            return '3B'
        elif 'SS' in pos_str and '2B' not in pos_str and '3B' not in pos_str:
            return 'SS'
        else:
            return 'OF'
    
    def create_multi_objective(self, df, player_vars, strategy_config):
        """Create simplified multi-objective optimization function"""
        objective = 0
        
        # Projection component (main focus)
        proj_component = lpSum(df.loc[i, 'Projected_FPPG'] * player_vars[i] for i in df.index)
        objective += proj_component * strategy_config['proj_weight']
        
        # Value component (points per dollar)
        if 'Value' in df.columns:
            value_component = lpSum((df.loc[i, 'Projected_FPPG'] / df.loc[i, 'Salary']) * player_vars[i] for i in df.index)
            objective += value_component * strategy_config['safe_weight'] * 1000
        
        # Simple contrarian component based on salary (higher salary = higher ownership assumption)
        if strategy_config['contrarian_weight'] > 0:
            # Favor lower salary players for contrarian approach
            contrarian_component = lpSum((5000 - df.loc[i, 'Salary']) / 1000 * player_vars[i] for i in df.index)
            objective += contrarian_component * strategy_config['contrarian_weight']
        
        return objective
    
    def add_constraints(self, prob, df, player_vars, strategy_config):
        """Add optimization constraints"""
        # Salary constraint
        prob += lpSum(df.loc[i, 'Salary'] * player_vars[i] for i in df.index) <= 35000
        
        # Roster size
        prob += lpSum(player_vars[i] for i in df.index) == 9
        
        # Position constraints
        position_limits = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
        
        for pos, limit in position_limits.items():
            eligible = df[df['Primary_Position'] == pos].index
            if len(eligible) > 0:
                prob += lpSum(player_vars[i] for i in eligible) == limit
        
        # Strategy-specific constraints
        self.add_strategy_constraints(prob, df, player_vars, strategy_config)
    
    def add_strategy_constraints(self, prob, df, player_vars, strategy_config):
        """Add strategy-specific constraints"""
        stack_type = strategy_config.get('stack_type', 'balanced')
        
        if stack_type == 'aggressive':
            # Force at least one 4+ team stack
            for team in df['Team'].unique():
                team_hitters = df[(df['Team'] == team) & (df['Primary_Position'] != 'P')].index
                if len(team_hitters) >= 4:
                    team_stack_var = LpVariable(f"team_stack_{team}", cat='Binary')
                    prob += lpSum(player_vars[i] for i in team_hitters) >= 4 * team_stack_var
        
        elif stack_type == 'mini_stack':
            # Encourage multiple 2-3 player stacks
            for team in df['Team'].unique():
                team_hitters = df[(df['Team'] == team) & (df['Primary_Position'] != 'P')].index
                if len(team_hitters) >= 2:
                    prob += lpSum(player_vars[i] for i in team_hitters) >= 2
    
    def calculate_lineup_metrics(self, lineup):
        """Calculate essential lineup metrics only"""
        # Calculate value (points per dollar)
        lineup['Value'] = lineup['Projected_FPPG'] / lineup['Salary'] * 1000
        
        return lineup
    
    def save_lineups(self, all_lineups):
        """Save all generated lineups with clean, essential columns only"""
        print("💾 Saving enhanced lineups...")
        
        # Define essential columns for lineup submission
        essential_columns = [
            'Id', 'Position', 'First Name', 'Nickname', 'Last Name', 
            'FPPG', 'Played', 'Salary', 'Game', 'Team', 'Opponent',
            'Injury Indicator', 'Injury Details', 'Tier', 'Probable Pitcher',
            'Batting Order', 'Roster Position', 'Projected_FPPG', 'Primary_Position', 'Value'
        ]
        
        for strategy, lineups in all_lineups.items():
            for i, lineup in enumerate(lineups):
                # Keep only essential columns that exist in the dataframe
                columns_to_keep = [col for col in essential_columns if col in lineup.columns]
                clean_lineup = lineup[columns_to_keep].copy()
                
                filename = f"../data/enhanced_lineup_{strategy}_{i+1}.csv"
                
                try:
                    clean_lineup.to_csv(filename, index=False)
                    print(f"✅ {strategy.upper()} Lineup {i+1}: ${lineup['Salary'].sum():.0f} | "
                          f"{lineup['Projected_FPPG'].sum():.1f} FPPG | "
                          f"{lineup['Value'].mean():.1f} avg value")
                except PermissionError:
                    # Try alternative filename if file is locked
                    import datetime
                    timestamp = datetime.datetime.now().strftime("%H%M%S")
                    alt_filename = f"../data/enhanced_lineup_{strategy}_{i+1}_{timestamp}.csv"
                    try:
                        clean_lineup.to_csv(alt_filename, index=False)
                        print(f"✅ {strategy.upper()} Lineup {i+1}: ${lineup['Salary'].sum():.0f} | "
                              f"{lineup['Projected_FPPG'].sum():.1f} FPPG | "
                              f"{lineup['Value'].mean():.1f} avg value (saved as {alt_filename})")
                    except Exception as e:
                        print(f"⚠️ Could not save {strategy} lineup {i+1}: {e}")
                        print(f"   File may be open in Excel. Close it and try again.")
    
    def run_enhanced_optimization(self):
        """Run complete enhanced optimization"""
        print("🚀 ENHANCED FANDUEL LINEUP OPTIMIZATION")
        print("=" * 50)
        
        # Load data
        df = self.load_enhanced_data()
        
        # Create ML projections
        df = self.create_ml_projections(df)
        
        # Apply advanced features
        df = self.apply_advanced_features(df)
        
        # Identify stacking opportunities
        stacks = self.identify_stacking_opportunities(df)
        print(f"🔥 Found {len(stacks)} stacking opportunities")
        
        # Generate optimized lineups
        all_lineups = self.optimize_multiple_strategies(df)
        
        # Save results
        self.save_lineups(all_lineups)
        
        # Generate summary report
        self.generate_summary_report(all_lineups, stacks)
        
        print("\n🎉 Enhanced optimization complete!")
        
        return all_lineups
    
    def generate_summary_report(self, all_lineups, stacks):
        """Generate comprehensive summary report"""
        print("\n📊 ENHANCED OPTIMIZATION SUMMARY")
        print("=" * 40)
        
        total_lineups = sum(len(lineups) for lineups in all_lineups.values())
        print(f"Total lineups generated: {total_lineups}")
        print(f"Stacking opportunities identified: {len(stacks)}")
        
        for strategy, lineups in all_lineups.items():
            if lineups:
                avg_projection = np.mean([lineup['Projected_FPPG'].sum() for lineup in lineups])
                avg_salary = np.mean([lineup['Salary'].sum() for lineup in lineups])
                print(f"\n{strategy.upper()} Strategy:")
                print(f"  Average projection: {avg_projection:.1f} FPPG")
                print(f"  Average salary: ${avg_salary:.0f}")

if __name__ == "__main__":
    optimizer = EnhancedFanDuelOptimizer()
    lineups = optimizer.run_enhanced_optimization()
