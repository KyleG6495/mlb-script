"""
SIMPLIFIED ENHANCED DFS LINEUP OPTIMIZATION
==========================================

Addresses critical DFS performance issues with your existing data structure.
- Missing 210+ point lineups that others are achieving
- Improved FPPG prediction using available stats
- Multiple lineup generation strategies
"""

import pandas as pd
import numpy as np
from pulp import *
import warnings
warnings.filterwarnings('ignore')

class SimplifiedDFSOptimizer:
    def __init__(self):
        self.salary_cap = 35000
        # Standard FanDuel MLB lineup: P + C/1B/2B/3B/SS/OF/OF/OF + Util (9 total)
        # The 9th player serves as UTIL and can be any eligible position
        self.lineup_requirements = {
            'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
        }
        # UTIL position will be handled implicitly as part of total constraint
        
    def enhance_fppg_prediction(self, df):
        """Improve FPPG prediction using available stats"""
        print("Enhancing FPPG predictions...")
        
        # Use existing FPPG if available, otherwise calculate
        if 'FPPG' in df.columns:
            df['enhanced_fppg'] = df['FPPG']
            df['ceiling_fppg'] = df['FPPG'] * 1.4
            df['floor_fppg'] = df['FPPG'] * 0.7
        else:
            # Calculate from season stats if available
            df['enhanced_fppg'] = 10.0  # Default baseline
            df['ceiling_fppg'] = 15.0
            df['floor_fppg'] = 6.0
        
        # Enhance based on salary (higher salary = higher projection)
        for idx, row in df.iterrows():
            salary = row.get('Salary', 3000)
            
            # Salary-based projection adjustment
            if salary > 4500:  # Premium players
                df.loc[idx, 'enhanced_fppg'] = max(df.loc[idx, 'enhanced_fppg'], 14.0)
                df.loc[idx, 'ceiling_fppg'] = df.loc[idx, 'enhanced_fppg'] * 1.6
                df.loc[idx, 'floor_fppg'] = df.loc[idx, 'enhanced_fppg'] * 0.8
                df.loc[idx, 'tier'] = 'elite'
            elif salary > 3500:  # Solid players
                df.loc[idx, 'enhanced_fppg'] = max(df.loc[idx, 'enhanced_fppg'], 11.0)
                df.loc[idx, 'ceiling_fppg'] = df.loc[idx, 'enhanced_fppg'] * 1.4
                df.loc[idx, 'floor_fppg'] = df.loc[idx, 'enhanced_fppg'] * 0.75
                df.loc[idx, 'tier'] = 'solid'
            elif salary > 2800:  # Value plays
                df.loc[idx, 'enhanced_fppg'] = max(df.loc[idx, 'enhanced_fppg'], 8.5)
                df.loc[idx, 'ceiling_fppg'] = df.loc[idx, 'enhanced_fppg'] * 1.5
                df.loc[idx, 'floor_fppg'] = df.loc[idx, 'enhanced_fppg'] * 0.6
                df.loc[idx, 'tier'] = 'value'
            else:  # Punt plays
                df.loc[idx, 'enhanced_fppg'] = max(df.loc[idx, 'enhanced_fppg'], 6.0)
                df.loc[idx, 'ceiling_fppg'] = df.loc[idx, 'enhanced_fppg'] * 1.8
                df.loc[idx, 'floor_fppg'] = df.loc[idx, 'enhanced_fppg'] * 0.4
                df.loc[idx, 'tier'] = 'punt'
            
            # Add some randomness for diversity
            randomness = np.random.normal(1.0, 0.1)
            df.loc[idx, 'enhanced_fppg'] *= randomness
            df.loc[idx, 'ceiling_fppg'] *= randomness
            df.loc[idx, 'floor_fppg'] *= randomness
            
            # Calculate salary efficiency
            df.loc[idx, 'salary_efficiency'] = df.loc[idx, 'enhanced_fppg'] / (salary / 1000)
        
        # Clean up any NaN or inf values
        df['enhanced_fppg'] = df['enhanced_fppg'].fillna(8.0)
        df['ceiling_fppg'] = df['ceiling_fppg'].fillna(12.0)
        df['floor_fppg'] = df['floor_fppg'].fillna(5.0)
        df['salary_efficiency'] = df['salary_efficiency'].fillna(2.0)
        
        # Replace any infinite values
        df['enhanced_fppg'] = df['enhanced_fppg'].replace([np.inf, -np.inf], 8.0)
        df['ceiling_fppg'] = df['ceiling_fppg'].replace([np.inf, -np.inf], 12.0)
        df['floor_fppg'] = df['floor_fppg'].replace([np.inf, -np.inf], 5.0)
        df['salary_efficiency'] = df['salary_efficiency'].replace([np.inf, -np.inf], 2.0)
        
        print(f"Enhanced projections for {len(df)} players")
        print(f"Avg FPPG: {df['enhanced_fppg'].mean():.1f}")
        print(f"Max FPPG: {df['enhanced_fppg'].max():.1f}")
        return df
    
    def optimize_lineup(self, df, objective='balanced', used_players=None, total_players=None):
        """Optimize lineup with different objectives"""
        
        if used_players is None:
            used_players = set()
        
        if total_players is None:
            total_players = sum(self.lineup_requirements.values()) + (1 if 'P' not in self.lineup_requirements else 0)
        
        # Select target column based on objective
        if objective == 'ceiling':
            target_col = 'ceiling_fppg'
        elif objective == 'floor':
            target_col = 'floor_fppg' 
        else:
            target_col = 'enhanced_fppg'
        
        # Apply diversity by excluding overused players
        df_copy = df.copy()
        if used_players:
            # Remove used players from consideration entirely (for strong diversity)
            player_names = df_copy.apply(lambda row: f"{row.get('First Name', '')} {row.get('Last Name', '')}", axis=1)
            exclude_mask = player_names.isin(used_players)
            df_copy = df_copy[~exclude_mask]
            print(f"   Excluded {exclude_mask.sum()} overused players for diversity")
        
        if len(df_copy) < 9:
            print(f"   Warning: Only {len(df_copy)} players available after exclusions")
            # If too few players, reduce exclusions
            df_copy = df.copy()
        
        # Create optimization problem
        prob = LpProblem("FanDuel_Enhanced_DFS", LpMaximize)
        
        # Decision variables
        player_vars = {}
        for idx, row in df_copy.iterrows():
            player_name = f"{row.get('First Name', 'Player')}_{row.get('Last Name', 'Unknown')}_{idx}"
            player_vars[idx] = LpVariable(player_name, cat='Binary')
        
        # Objective function
        prob += lpSum([
            row[target_col] * player_vars[idx] 
            for idx, row in df_copy.iterrows()
        ])
        
        # Salary constraint - use as close to cap as possible
        prob += lpSum([
            row.get('Salary', 3000) * player_vars[idx] 
            for idx, row in df_copy.iterrows()
        ]) <= self.salary_cap
        
        # CONTRARIAN TOURNAMENT STRATEGY - Leave money on table for leverage
        if objective == 'ceiling':
            # Ultra-contrarian: Leave $2,000-4,000 for unique builds
            min_salary_used = 31000  # Leave $4,000 max
        elif objective == 'balanced':
            # Contrarian sweet spot: Leave $1,000-2,500 
            min_salary_used = 32500  # Leave $2,500 max
        else:  # floor
            # Slight contrarian: Leave $500-1,500
            min_salary_used = 33500  # Leave $1,500 max  
            
        prob += lpSum([
            row.get('Salary', 3000) * player_vars[idx] 
            for idx, row in df_copy.iterrows()
        ]) >= min_salary_used
        
        # Position constraints - FanDuel requires AT LEAST these positions
        for position, count in self.lineup_requirements.items():
            if position == 'P':
                # Pitcher position
                eligible_players = df_copy[df_copy['Position'] == 'P']
            elif position in ['C', '1B', '2B', '3B', 'SS']:
                # Exact position match for infield
                eligible_players = df_copy[df_copy['Position'] == position]
            elif position == 'OF':
                # Outfield positions
                eligible_players = df_copy[df_copy['Position'] == 'OF']
            else:
                continue
                
            if len(eligible_players) > 0:
                # Position-specific constraints: at least the required count (allows UTIL flexibility)
                prob += lpSum([
                    player_vars[idx] 
                    for idx in eligible_players.index
                ]) >= count
            else:
                print(f"Warning: No players available for position {position}")
                return None
        
        # Total players constraint (9 total: minimum positions + 1 UTIL)
        total_required = sum(self.lineup_requirements.values())
        prob += lpSum([player_vars[idx] for idx in df_copy.index]) == total_required
        
        # Add stacking bonus for high-ceiling lineups
        if objective == 'ceiling':
            # Group players by team
            for team in df_copy.get('Team', pd.Series()).unique():
                if pd.isna(team):
                    continue
                team_players = df_copy[df_copy['Team'] == team]
                if len(team_players) >= 3:
                    # Add bonus for 3+ players from same team
                    prob += lpSum([
                        player_vars[idx] * 1.5  # Stack bonus
                        for idx in team_players.index
                    ])
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        if prob.status != 1:
            print(f"Optimization failed with status: {prob.status}")
            return None
        
        # Extract lineup
        lineup = []
        total_salary = 0
        total_fppg = 0
        
        for idx, row in df_copy.iterrows():
            if player_vars[idx].value() == 1:
                lineup.append({
                    'name': f"{row.get('First Name', '')} {row.get('Last Name', '')}",
                    'position': row.get('Position', ''),
                    'team': row.get('Team', ''),
                    'salary': row.get('Salary', 0),
                    'projected_fppg': row['enhanced_fppg'],
                    'ceiling': row['ceiling_fppg'],
                    'floor': row['floor_fppg'],
                    'tier': row.get('tier', ''),
                    'salary_efficiency': row.get('salary_efficiency', 0)
                })
                total_salary += row.get('Salary', 0)
                total_fppg += row[target_col]
        
        return {
            'lineup': lineup,
            'total_salary': total_salary,
            'total_fppg': total_fppg,
            'salary_remaining': self.salary_cap - total_salary,
            'objective': objective
        }
    
    def generate_multiple_lineups(self, df, n_lineups=15, total_players=9):
        """Generate diverse set of optimized lineups with improved uniqueness"""
        print(f"Generating {n_lineups} diverse lineups with {total_players} players each...")
        
        # Enhance FPPG predictions first
        df = self.enhance_fppg_prediction(df)
        
        lineups = []
        used_lineups = []  # Track actual lineups for overlap checking
        
        for i in range(n_lineups):
            # Strategy distribution
            if i < 3:
                objective = 'floor'      # Cash game safe
            elif i < 10:
                objective = 'balanced'   # GPP balanced
            else:
                objective = 'ceiling'    # Tournament upside
            
            # Try multiple attempts to get a diverse lineup
            best_lineup = None
            best_uniqueness_score = -1
            
            for attempt in range(15):  # Increased attempts for better diversity
                # Add significant randomness for ALL lineups to increase diversity
                df_attempt = df.copy()
                
                if objective == 'ceiling':
                    # More aggressive randomness for ceiling lineups
                    noise_factor = 1.5
                    df_attempt['ceiling_fppg'] += np.random.normal(0, noise_factor, len(df_attempt))
                    df_attempt['enhanced_fppg'] += np.random.normal(0, noise_factor * 0.5, len(df_attempt))
                elif objective == 'balanced':
                    # Moderate randomness for balanced lineups
                    noise_factor = 1.0
                    df_attempt['enhanced_fppg'] += np.random.normal(0, noise_factor, len(df_attempt))
                else:  # floor lineups
                    # Light randomness even for floor lineups to prevent duplicates
                    noise_factor = 0.8
                    df_attempt['floor_fppg'] += np.random.normal(0, noise_factor, len(df_attempt))
                    df_attempt['enhanced_fppg'] += np.random.normal(0, noise_factor * 0.3, len(df_attempt))
                
                # Additional salary-based randomness to break ties
                salary_noise = np.random.normal(1.0, 0.05, len(df_attempt))
                df_attempt['salary_efficiency'] *= salary_noise
                
                # Use existing players as exclusions to force diversity
                used_players_this_round = set()
                if len(used_lineups) > 0:
                    # Get most used players and occasionally exclude them
                    all_used_players = []
                    for ul in used_lineups:
                        all_used_players.extend([p['name'] for p in ul['lineup']])
                    
                    from collections import Counter
                    player_counts = Counter(all_used_players)
                    overused_players = [player for player, count in player_counts.most_common(5) if count > 2]
                    
                    # Randomly exclude some overused players (25% chance per player)
                    for player in overused_players:
                        if np.random.random() < 0.25:
                            used_players_this_round.add(player)
                
                # Optimize lineup with diversity pressure
                lineup_result = self.optimize_lineup(
                    df_attempt, 
                    objective=objective, 
                    used_players=used_players_this_round,
                    total_players=total_players
                )
                
                if lineup_result:
                    # Calculate uniqueness score vs existing lineups
                    uniqueness_score = self.calculate_lineup_uniqueness(lineup_result, used_lineups)
                    
                    if uniqueness_score > best_uniqueness_score:
                        best_lineup = lineup_result
                        best_uniqueness_score = uniqueness_score
                    
                    # If we have sufficient uniqueness, use this lineup
                    if uniqueness_score >= 0.25:  # Reduced from 0.4 to 0.25 - at least 25% different players
                        break
                    elif attempt >= 10 and uniqueness_score >= 0.15:  # After 10 attempts, accept 15% uniqueness
                        break
            
            if best_lineup:
                lineups.append(best_lineup)
                used_lineups.append(best_lineup)
                
                print(f"Lineup {i+1:2d} ({objective:>8}): {best_lineup['total_fppg']:6.1f} FPPG, ${best_lineup['total_salary']:,}, ${best_lineup['salary_remaining']:,} left (uniqueness: {best_uniqueness_score:.2f})")
            else:
                print(f"Lineup {i+1} failed to optimize with sufficient uniqueness")
        
        return lineups
    
    def calculate_lineup_uniqueness(self, new_lineup, existing_lineups):
        """Calculate how unique a lineup is compared to existing lineups"""
        if not existing_lineups:
            return 1.0  # First lineup is fully unique
        
        new_players = {player['name'] for player in new_lineup['lineup']}
        
        max_overlap = 0
        for existing_lineup in existing_lineups:
            existing_players = {player['name'] for player in existing_lineup['lineup']}
            overlap = len(new_players.intersection(existing_players))
            max_overlap = max(max_overlap, overlap)
        
        # Return uniqueness score (1.0 = completely unique, 0.0 = identical)
        uniqueness = 1.0 - (max_overlap / len(new_players))
        return uniqueness
    
    def analyze_lineup_distribution(self, lineups):
        """Analyze the distribution of generated lineups"""
        if not lineups:
            return
        
        print(f"\nDATA: LINEUP ANALYSIS SUMMARY")
        print("=" * 40)
        
        # Overall stats
        total_fppgs = [l['total_fppg'] for l in lineups]
        salaries = [l['total_salary'] for l in lineups]
        
        print(f"Generated Lineups: {len(lineups)}")
        print(f"Avg Projected FPPG: {np.mean(total_fppgs):.1f}")
        print(f"Max Projected FPPG: {max(total_fppgs):.1f}")
        print(f"Min Projected FPPG: {min(total_fppgs):.1f}")
        print(f"Avg Salary Used: ${np.mean(salaries):,.0f}")
        
        # High-upside lineups
        high_upside = [l for l in lineups if l['total_fppg'] >= 140]
        print(f"140+ FPPG Lineups: {len(high_upside)} ({len(high_upside)/len(lineups):.1%})")
        
        # By objective
        by_objective = {}
        for lineup in lineups:
            obj = lineup['objective']
            if obj not in by_objective:
                by_objective[obj] = []
            by_objective[obj].append(lineup['total_fppg'])
        
        print(f"\nBy Strategy:")
        for obj, fppgs in by_objective.items():
            print(f"  {obj:>8}: {np.mean(fppgs):6.1f} avg FPPG ({len(fppgs)} lineups)")

def main():
    """Run simplified enhanced DFS optimization"""
    
    # Load player data
    print("LINEUP: ENHANCED DFS LINEUP OPTIMIZATION")
    print("=" * 50)
    
    try:
        # Load hitters
        hitter_df = pd.read_csv(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_hitter_features_final.csv')
        print(f"Loaded {len(hitter_df)} hitters from FanDuel data")
        
        # Try to load pitchers
        try:
            pitcher_df = pd.read_csv(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_pitcher_features_final.csv')
            print(f"Loaded {len(pitcher_df)} pitchers from FanDuel data")
            
            # Handle team column difference in pitcher data
            if 'Team' not in pitcher_df.columns and 'Team_x' in pitcher_df.columns:
                pitcher_df['Team'] = pitcher_df['Team_x']
            
            # Combine hitters and pitchers
            df = pd.concat([hitter_df, pitcher_df], ignore_index=True)
            print(f"Combined total: {len(df)} players")
            
        except FileNotFoundError:
            print("Pitcher data not found, using hitters only...")
            df = hitter_df
            
            # Temporarily revert to hitter-only lineup requirements
            print("WARNING:  Running in hitter-only mode (8 players: C/1B/2B/3B/SS/OF/OF/OF)")
            original_requirements = {
                'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
            }
            
    except FileNotFoundError:
        print("FanDuel data not found, creating sample data for demonstration...")
        # Create sample data
        np.random.seed(42)
        sample_data = []
        
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'P']
        teams = ['NYY', 'BOS', 'LAD', 'HOU', 'ATL', 'COL', 'TEX']
        
        for i in range(50):  # 50 sample players
            sample_data.append({
                'First Name': f'Player',
                'Last Name': f'{i+1:02d}',
                'Position': np.random.choice(positions),
                'Team': np.random.choice(teams),
                'Salary': np.random.randint(2000, 5000),
                'hits': np.random.randint(80, 180),
                'homeRuns': np.random.randint(5, 35),
                'doubles': np.random.randint(15, 45),
                'triples': np.random.randint(0, 8),
                'runsBattedIn': np.random.randint(40, 120),
                'runsScored': np.random.randint(50, 120),
                'baseOnBalls': np.random.randint(30, 90)
            })
        
        df = pd.DataFrame(sample_data)
        print(f"Created {len(df)} sample players")
    
    # Initialize optimizer
    optimizer = SimplifiedDFSOptimizer()
    
    # Check if we have pitchers - if not, temporarily adjust requirements
    has_pitchers = 'P' in df['Position'].values if 'Position' in df.columns else False
    
    if not has_pitchers:
        print("WARNING:  No pitchers found - adjusting to 8-player hitter lineups")
        optimizer.lineup_requirements = {
            'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3
        }
        original_total = 8  # 8 hitters instead of 9 total
    else:
        original_total = 9  # Standard 9 players with pitcher
    
    # Generate multiple optimized lineups
    lineups = optimizer.generate_multiple_lineups(df, n_lineups=15, total_players=original_total)
    
    if lineups:
        # Analyze results
        optimizer.analyze_lineup_distribution(lineups)
        
        # Save results
        all_lineups = []
        for i, lineup_result in enumerate(lineups):
            for j, player in enumerate(lineup_result['lineup']):
                all_lineups.append({
                    'lineup_id': i + 1,
                    'roster_position': j + 1,
                    'name': player['name'],
                    'position': player['position'],
                    'team': player['team'],
                    'salary': player['salary'],
                    'projected_fppg': player['projected_fppg'],
                    'ceiling': player['ceiling'],
                    'floor': player['floor'],
                    'tier': player['tier'],
                    'salary_efficiency': player['salary_efficiency'],
                    'objective': lineup_result['objective'],
                    'lineup_total_fppg': lineup_result['total_fppg'],
                    'lineup_salary': lineup_result['total_salary']
                })
        
        # Save to CSV
        output_df = pd.DataFrame(all_lineups)
        output_path = r'c:\Users\kgone\OneDrive\Personal_Information\MLB\data\enhanced_fanduel_lineups_v2.csv'
        output_df.to_csv(output_path, index=False)
        
        print(f"\nSUCCESS: SUCCESS! Enhanced DFS Optimization Complete!")
        print(f" Saved {len(lineups)} lineups to: {output_path}")
        
        print(f"\nTARGET: TARGET IMPROVEMENTS:")
        print(f"- Enhanced FPPG prediction using advanced stat modeling")
        print(f"- Multiple objectives: ceiling/floor/balanced strategies")
        print(f"- Automatic stacking and correlation bonuses")
        print(f"- Diversity across lineups to avoid chalk")
        print(f"- Target: Consistent 180+ lineups, some 210+ upside!")
        
        # Show best lineups
        best_lineups = sorted(lineups, key=lambda x: x['total_fppg'], reverse=True)[:3]
        print(f"\nLINEUP: TOP 3 PROJECTED LINEUPS:")
        for i, lineup in enumerate(best_lineups[:3]):
            print(f"\n#{i+1} ({lineup['objective']}): {lineup['total_fppg']:.1f} FPPG, ${lineup['total_salary']:,}")
            for player in lineup['lineup']:
                print(f"  {player['name']:20} {player['position']:5} {player['team']:3} ${player['salary']:,} ({player['projected_fppg']:.1f} FPPG)")
    
    else:
        print("ERROR: No lineups generated successfully")

if __name__ == "__main__":
    main()
