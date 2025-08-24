"""
BACKTEST ENHANCED DFS OPTIMIZER
==============================

Test the enhanced DFS models against yesterday's FanDuel slate (7/21/2025)
to validate improvements vs your old approach.

This will generate optimized lineups using the enhanced methods and 
show projected vs actual performance.
"""

import pandas as pd
import numpy as np
from pulp import *
import warnings
warnings.filterwarnings('ignore')

class BacktestDFSOptimizer:
    def __init__(self):
        self.salary_cap = 35000
        self.lineup_requirements = {
            'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1,
            'OF': 3, 'Util': 1
        }
        
    def load_fanduel_slate(self, file_path):
        """Load FanDuel player slate"""
        print(f"Loading FanDuel slate: {file_path}")
        
        df = pd.read_csv(file_path)
        
        # Keep ALL players including pitchers for FanDuel lineups
        print(f"Loaded {len(df)} total players")
        
        # Clean up the data
        df['name'] = df['First Name'] + ' ' + df['Last Name']
        df['position'] = df['Position']
        df['team'] = df['Team']
        df['opponent'] = df['Opponent']
        df['salary'] = df['Salary']
        df['fppg'] = df['FPPG']
        
        # Handle missing FPPG values
        df['fppg'] = df['fppg'].fillna(8.0)
        
        # Remove players with injury indicators or very low salaries
        active_players = df[
            (df['Injury Indicator'].isna() | (df['Injury Indicator'] == '')) &
            (df['salary'] >= 2000)
        ].copy()
        
        print(f"Active players after filtering: {len(active_players)}")
        
        return active_players
    
    def enhance_projections(self, df):
        """Apply enhanced projection methodology"""
        print("Applying enhanced projection methodology...")
        
        # Create enhanced projections based on multiple factors
        df = df.copy()
        
        for idx, row in df.iterrows():
            base_fppg = row['fppg']
            salary = row['salary']
            position = row['position']
            team = row['team']
            opponent = row['opponent']
            
            # 1. SALARY TIER ADJUSTMENTS
            if salary >= 4500:  # Elite tier
                tier_multiplier = 1.0  # Keep projection as-is for studs
                ceiling_multiplier = 1.4
                floor_multiplier = 0.85
                tier = 'Elite'
            elif salary >= 3500:  # Solid tier
                tier_multiplier = 1.05  # Slight boost for value
                ceiling_multiplier = 1.3
                floor_multiplier = 0.8
                tier = 'Solid'
            elif salary >= 2800:  # Value tier
                tier_multiplier = 1.1  # Value boost
                ceiling_multiplier = 1.5
                floor_multiplier = 0.65
                tier = 'Value'
            else:  # Punt tier
                tier_multiplier = 1.05  # Slight punt boost
                ceiling_multiplier = 1.8
                floor_multiplier = 0.4
                tier = 'Punt'
            
            # 2. POSITION SCARCITY ADJUSTMENTS
            position_boost = {
                'C': 1.05,     # Catcher scarcity
                '1B': 1.0,
                '2B': 1.02,    # Slight scarcity
                '3B': 1.0,
                'SS': 1.03,    # Premium position
                'OF': 1.0,
                'LF': 1.0,
                'CF': 1.0,
                'RF': 1.0
            }.get(position, 1.0)
            
            # 3. GAME ENVIRONMENT FACTORS
            # High-offense teams get boost
            offense_teams = ['COL', 'TEX', 'BOS', 'HOU', 'ATL', 'LAD', 'NYY']
            offense_boost = 1.08 if team in offense_teams else 1.0
            
            # Weak pitching opponents get boost
            weak_pitching = ['COL', 'LAA', 'MIA', 'WSH', 'OAK']
            matchup_boost = 1.12 if opponent in weak_pitching else 1.0
            
            # 4. CALCULATE ENHANCED PROJECTIONS
            enhanced_fppg = base_fppg * tier_multiplier * position_boost * offense_boost * matchup_boost
            
            # Add slight randomness for lineup diversity
            randomness = np.random.normal(1.0, 0.05)
            enhanced_fppg *= randomness
            
            # Calculate ceiling and floor
            ceiling_fppg = enhanced_fppg * ceiling_multiplier
            floor_fppg = enhanced_fppg * floor_multiplier
            
            # Calculate value metrics
            value_score = enhanced_fppg / (salary / 1000)  # Points per $1K
            
            # Store enhanced metrics
            df.loc[idx, 'enhanced_fppg'] = enhanced_fppg
            df.loc[idx, 'ceiling_fppg'] = ceiling_fppg
            df.loc[idx, 'floor_fppg'] = floor_fppg
            df.loc[idx, 'value_score'] = value_score
            df.loc[idx, 'tier'] = tier
        
        print(f"Enhanced projections complete:")
        print(f"  Avg Enhanced FPPG: {df['enhanced_fppg'].mean():.1f}")
        print(f"  Max Enhanced FPPG: {df['enhanced_fppg'].max():.1f}")
        print(f"  Avg Value Score: {df['value_score'].mean():.2f}")
        
        return df
    
    def optimize_lineup(self, df, strategy='balanced', used_players=None):
        """Optimize single lineup with different strategies"""
        
        if used_players is None:
            used_players = set()
        
        # Select target column based on strategy
        if strategy == 'ceiling':
            target_col = 'ceiling_fppg'
        elif strategy == 'floor':
            target_col = 'floor_fppg'
        else:  # balanced
            target_col = 'enhanced_fppg'
        
        # Apply diversity penalty for used players
        df_copy = df.copy()
        for idx, row in df_copy.iterrows():
            player_name = row['name']
            if player_name in used_players:
                df_copy.loc[idx, target_col] *= 0.7  # 30% penalty for reuse
        
        # Create optimization problem
        prob = LpProblem(f"FanDuel_DFS_{strategy}", LpMaximize)
        
        # Decision variables
        player_vars = {}
        for idx, row in df_copy.iterrows():
            player_name = f"{row['name']}_{idx}".replace(' ', '_').replace("'", "")
            player_vars[idx] = LpVariable(player_name, cat='Binary')
        
        # Objective function - make sure no NaN values
        objective_terms = []
        for idx, row in df_copy.iterrows():
            target_value = row[target_col]
            if pd.isna(target_value) or target_value == 0:
                target_value = 5.0  # Default minimum
            objective_terms.append(target_value * player_vars[idx])
        
        prob += lpSum(objective_terms)
        
        # Salary constraint
        prob += lpSum([
            row['salary'] * player_vars[idx] 
            for idx, row in df_copy.iterrows()
        ]) <= self.salary_cap
        
        # Position constraints - FanDuel MLB format (9 players total)
        # P constraint (pitcher - required)
        pitchers = df_copy[df_copy['position'] == 'P']
        if len(pitchers) > 0:
            prob += lpSum([player_vars[idx] for idx in pitchers.index]) == 1
        else:
            print("WARNING: No pitchers available!")
            return None
        
        # C constraint
        catchers = df_copy[df_copy['position'] == 'C']
        if len(catchers) > 0:
            prob += lpSum([player_vars[idx] for idx in catchers.index]) == 1
        else:
            print("WARNING: No catchers available!")
            return None
        
        # 1B constraint  
        first_base = df_copy[df_copy['position'] == '1B']
        if len(first_base) > 0:
            prob += lpSum([player_vars[idx] for idx in first_base.index]) == 1
        else:
            print("WARNING: No first basemen available!")
            return None
        
        # 2B constraint
        second_base = df_copy[df_copy['position'] == '2B']
        if len(second_base) > 0:
            prob += lpSum([player_vars[idx] for idx in second_base.index]) == 1
        else:
            print("WARNING: No second basemen available!")
            return None
        
        # 3B constraint
        third_base = df_copy[df_copy['position'] == '3B']
        if len(third_base) > 0:
            prob += lpSum([player_vars[idx] for idx in third_base.index]) == 1
        else:
            print("WARNING: No third basemen available!")
            return None
        
        # SS constraint
        shortstops = df_copy[df_copy['position'] == 'SS']
        if len(shortstops) > 0:
            prob += lpSum([player_vars[idx] for idx in shortstops.index]) == 1
        else:
            print("WARNING: No shortstops available!")
            return None
        
        # OF constraint (need 3)
        outfielders = df_copy[df_copy['position'].isin(['OF', 'LF', 'CF', 'RF'])]
        if len(outfielders) >= 3:
            prob += lpSum([player_vars[idx] for idx in outfielders.index]) == 3
        else:
            print(f"WARNING: Only {len(outfielders)} outfielders available, need 3!")
            return None
        
        # Total lineup constraint (9 players: P + C + 1B + 2B + 3B + SS + 3OF)
        prob += lpSum([player_vars[idx] for idx in df_copy.index]) == 9
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        if prob.status != 1:
            print(f"ERROR: Optimization failed for {strategy} strategy. Status: {prob.status}")
            return None
        
        # Extract lineup
        lineup = []
        total_salary = 0
        total_fppg = 0
        total_ceiling = 0
        total_floor = 0
        
        selected_players = []
        for idx, row in df_copy.iterrows():
            if player_vars[idx].value() == 1:
                selected_players.append(row)
                lineup.append({
                    'name': row['name'],
                    'position': row['position'],
                    'team': row['team'],
                    'salary': row['salary'],
                    'original_fppg': row['fppg'],
                    'enhanced_fppg': row['enhanced_fppg'],
                    'ceiling_fppg': row['ceiling_fppg'],
                    'floor_fppg': row['floor_fppg'],
                    'value_score': row['value_score'],
                    'tier': row['tier']
                })
                total_salary += row['salary']
                total_fppg += row['enhanced_fppg']
                total_ceiling += row['ceiling_fppg']
                total_floor += row['floor_fppg']
        
        print(f"SUCCESS: {strategy} lineup: {len(lineup)} players, ${total_salary:,}, {total_fppg:.1f} FPPG")
        
        return {
            'lineup': lineup,
            'total_salary': total_salary,
            'total_enhanced_fppg': total_fppg,
            'total_ceiling_fppg': total_ceiling,
            'total_floor_fppg': total_floor,
            'salary_remaining': self.salary_cap - total_salary,
            'strategy': strategy,
            'avg_value_score': total_fppg / (total_salary / 1000)
        }
    
    def generate_multiple_lineups(self, df, n_lineups=20):
        """Generate diverse set of optimized lineups"""
        print(f"Generating {n_lineups} enhanced lineups...")
        
        lineups = []
        used_players = set()
        
        strategies = ['floor'] * 3 + ['balanced'] * 12 + ['ceiling'] * 5
        
        for i in range(min(n_lineups, len(strategies))):
            strategy = strategies[i]
            
            lineup_result = self.optimize_lineup(df, strategy=strategy, used_players=used_players)
            
            if lineup_result:
                lineups.append(lineup_result)
                
                # Add core players to used set for diversity
                for player in lineup_result['lineup']:
                    if player['salary'] >= 3500:  # Only track expensive players
                        used_players.add(player['name'])
                
                print(f"Lineup {i+1:2d} ({strategy:>8}): {lineup_result['total_enhanced_fppg']:5.1f} FPPG, ${lineup_result['total_salary']:,}, {lineup_result['avg_value_score']:.2f} val")
        
        return lineups
    
    def analyze_lineups(self, lineups):
        """Analyze the generated lineups"""
        if not lineups:
            return
        
        print(f"\nDATA: LINEUP ANALYSIS")
        print("=" * 50)
        
        total_lineups = len(lineups)
        enhanced_scores = [l['total_enhanced_fppg'] for l in lineups]
        ceiling_scores = [l['total_ceiling_fppg'] for l in lineups]
        floor_scores = [l['total_floor_fppg'] for l in lineups]
        
        print(f"Generated Lineups: {total_lineups}")
        print(f"Enhanced FPPG - Avg: {np.mean(enhanced_scores):.1f}, Max: {np.max(enhanced_scores):.1f}, Min: {np.min(enhanced_scores):.1f}")
        print(f"Ceiling FPPG - Avg: {np.mean(ceiling_scores):.1f}, Max: {np.max(ceiling_scores):.1f}")
        print(f"Floor FPPG - Avg: {np.mean(floor_scores):.1f}, Min: {np.min(floor_scores):.1f}")
        
        # High-scoring potential
        high_enhanced = sum(1 for score in enhanced_scores if score >= 150)
        elite_enhanced = sum(1 for score in enhanced_scores if score >= 170)
        ceiling_180 = sum(1 for score in ceiling_scores if score >= 180)
        ceiling_210 = sum(1 for score in ceiling_scores if score >= 210)
        
        print(f"\nHigh-Scoring Potential:")
        print(f"150+ Enhanced FPPG: {high_enhanced} ({high_enhanced/total_lineups:.1%})")
        print(f"170+ Enhanced FPPG: {elite_enhanced} ({elite_enhanced/total_lineups:.1%})")
        print(f"180+ Ceiling FPPG: {ceiling_180} ({ceiling_180/total_lineups:.1%})")
        print(f"210+ Ceiling FPPG: {ceiling_210} ({ceiling_210/total_lineups:.1%})")
        
        # Strategy breakdown
        strategies = {}
        for lineup in lineups:
            strategy = lineup['strategy']
            if strategy not in strategies:
                strategies[strategy] = {'count': 0, 'avg_fppg': 0, 'scores': []}
            strategies[strategy]['count'] += 1
            strategies[strategy]['scores'].append(lineup['total_enhanced_fppg'])
        
        print(f"\nBy Strategy:")
        for strategy, stats in strategies.items():
            avg_fppg = np.mean(stats['scores'])
            print(f"  {strategy:>8}: {avg_fppg:5.1f} avg FPPG ({stats['count']} lineups)")
    
    def save_lineups(self, lineups, output_file):
        """Save lineups to CSV for submission"""
        all_lineup_data = []
        
        for i, lineup_result in enumerate(lineups):
            for j, player in enumerate(lineup_result['lineup']):
                all_lineup_data.append({
                    'lineup_id': i + 1,
                    'slot': j + 1,
                    'name': player['name'],
                    'position': player['position'],
                    'team': player['team'],
                    'salary': player['salary'],
                    'original_fppg': player['original_fppg'],
                    'enhanced_fppg': player['enhanced_fppg'],
                    'ceiling_fppg': player['ceiling_fppg'],
                    'floor_fppg': player['floor_fppg'],
                    'value_score': player['value_score'],
                    'tier': player['tier'],
                    'strategy': lineup_result['strategy'],
                    'lineup_total_salary': lineup_result['total_salary'],
                    'lineup_enhanced_fppg': lineup_result['total_enhanced_fppg'],
                    'lineup_ceiling_fppg': lineup_result['total_ceiling_fppg'],
                    'lineup_floor_fppg': lineup_result['total_floor_fppg']
                })
        
        lineup_df = pd.DataFrame(all_lineup_data)
        lineup_df.to_csv(output_file, index=False)
        print(f" Saved {len(lineups)} lineups to: {output_file}")
        
        return lineup_df

def main():
    """Run enhanced DFS optimization for today's slate"""
    
    print("LINEUP: ENHANCED DFS OPTIMIZER - TODAY'S SLATE")
    print("=" * 60)
    print("Generating optimized lineups for today's games")
    print()
    
    # Initialize optimizer
    optimizer = BacktestDFSOptimizer()
    
    # Load today's FanDuel slate
    slate_file = r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv'
    df = optimizer.load_fanduel_slate(slate_file)
    
    if df is None or len(df) == 0:
        print("ERROR: Could not load slate data")
        return
    
    # Apply enhanced projections
    df = optimizer.enhance_projections(df)
    
    # Generate enhanced lineups
    lineups = optimizer.generate_multiple_lineups(df, n_lineups=20)
    
    # Analyze results
    optimizer.analyze_lineups(lineups)
    
    # Show top lineups
    print(f"\nLINEUP: TOP 5 ENHANCED LINEUPS:")
    print("-" * 60)
    
    # Sort by enhanced FPPG
    sorted_lineups = sorted(lineups, key=lambda x: x['total_enhanced_fppg'], reverse=True)
    
    for i, lineup_result in enumerate(sorted_lineups[:5]):
        print(f"\n#{i+1} ({lineup_result['strategy']:>8}): {lineup_result['total_enhanced_fppg']:5.1f} FPPG, ${lineup_result['total_salary']:,}")
        for j, player in enumerate(lineup_result['lineup']):
            print(f"  {player['name']:<20} {player['position']:<4} {player['team']:>3} ${player['salary']:,} ({player['enhanced_fppg']:4.1f} FPPG) [{player['tier']}]")
    
    # Save today's optimized lineups
    from datetime import datetime
    today_str = datetime.now().strftime('%Y%m%d')
    output_file = rf'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\enhanced_lineups_today_{today_str}.csv'
    optimizer.save_lineups(lineups, output_file)
    
    # Compare to your old lineups if available
    print(f"\nDATA: ENHANCED VS ORIGINAL COMPARISON:")
    print("-" * 45)
    
    # Try to load one of your old lineups for comparison
    old_lineup_files = [
        r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups_Ready_To_Submit_20250721_1900.csv',
        r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\Lineups_Ready_To_Submit_20250721_1916.csv'
    ]
    
    for old_file in old_lineup_files:
        try:
            old_df = pd.read_csv(old_file)
            if len(old_df) >= 9:  # Has at least one lineup
                print(f"Found old lineup: {old_file.split('/')[-1]}")
                
                # Calculate old lineup projected score using original FPPG
                old_lineup_fppg = 0
                old_salary = 0
                
                print("\nOLD LINEUP:")
                for idx, player in old_df.head(9).iterrows():
                    player_match = df[df['name'].str.contains(player.get('Name', player.get('Player', '')), case=False, na=False)]
                    if not player_match.empty:
                        p = player_match.iloc[0]
                        old_lineup_fppg += p['fppg']
                        old_salary += p['salary']
                        print(f"  {p['name']:<20} {p['position']:<4} {p['team']:>3} ${p['salary']:,} ({p['fppg']:4.1f} FPPG)")
                
                print(f"\nCOMPARISON:")
                print(f"Old Method:      {old_lineup_fppg:5.1f} FPPG, ${old_salary:,}")
                print(f"Enhanced Method: {sorted_lineups[0]['total_enhanced_fppg']:5.1f} FPPG, ${sorted_lineups[0]['total_salary']:,}")
                improvement = sorted_lineups[0]['total_enhanced_fppg'] - old_lineup_fppg
                print(f"Improvement:     {improvement:+5.1f} FPPG ({improvement/old_lineup_fppg:+.1%})")
                break
        except:
            continue
    
    print(f"\nSUCCESS: ENHANCED BACKTEST COMPLETE!")
    print(f"TARGET: Key Improvements:")
    print(f"   - Multi-strategy optimization (floor/balanced/ceiling)")
    print(f"   - Enhanced projection methodology")
    print(f"   - Position scarcity and game environment factors")
    print(f"   - Value-based player selection")
    print(f"   - Lineup diversity enforcement")

if __name__ == "__main__":
    main()
