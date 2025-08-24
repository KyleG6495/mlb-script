#!/usr/bin/env python3
"""
CEILING LINEUP OPTIMIZER
========================
Specialized DFS optimizer designed to generate high-ceiling lineups for 210+ point targets.

Key Features:
1. Variance-focused player selection
2. Correlation stacking strategies
3. Ownership fade optimization
4. Game environment weighting
5. Boom-or-bust player targeting
"""

import pandas as pd
import numpy as np
from pulp import LpMaximize, LpProblem, LpVariable, lpSum, PULP_CBC_CMD
import warnings
warnings.filterwarnings('ignore')

class CeilingLineupOptimizer:
    def __init__(self):
        self.salary_cap = 35000
        self.min_players = 9
        self.position_requirements = {
            'P': (1, 1), 'C': (1, 1), '1B': (1, 1), '2B': (1, 1), 
            '3B': (1, 1), 'SS': (1, 1), 'OF': (3, 3)
        }
        
    def calculate_ceiling_scores(self, df):
        """Calculate ceiling projections focusing on upside scenarios"""
        print("🎯 Calculating ceiling-focused projections...")
        
        # Base ceiling = 90th percentile of recent performance
        df['ceiling_projection'] = df['projected_fppg'] * 1.4  # 40% upside boost
        
        # Variance indicators (higher = more ceiling potential)
        df['recent_variance'] = df.get('recent_variance', df['projected_fppg'] * 0.3)
        df['upside_factor'] = 1 + (df['recent_variance'] / df['projected_fppg'].max())
        
        # Weather/park boosts for ceiling
        weather_boost = df.get('weather_boost', 1.0)
        park_boost = df.get('park_factor', 1.0)
        df['ceiling_projection'] *= weather_boost * park_boost
        
        # Position-specific ceiling adjustments
        position_multipliers = {
            'P': 1.2,   # Pitchers have high variance
            'C': 0.9,   # Catchers more consistent
            '1B': 1.1,  # Power positions
            '3B': 1.1,
            'OF': 1.15, # Most variance in OF
            '2B': 1.0,
            'SS': 1.0
        }
        
        for pos, mult in position_multipliers.items():
            mask = df['Position'].str.contains(pos, na=False)
            df.loc[mask, 'ceiling_projection'] *= mult
        
        return df
    
    def calculate_ownership_weights(self, df):
        """Calculate anti-ownership weights for contrarian plays"""
        print("📊 Calculating ownership fade weights...")
        
        # Estimate ownership based on salary and projection
        salary_pct = df['Salary'] / df['Salary'].max()
        proj_pct = df['projected_fppg'] / df['projected_fppg'].max()
        
        # Higher salary + projection = higher estimated ownership
        estimated_ownership = (salary_pct * 0.4 + proj_pct * 0.6) * 100
        
        # Fade factor (prefer lower owned players for ceiling)
        max_ownership = estimated_ownership.max()
        df['ownership_fade'] = 1.2 - (estimated_ownership / max_ownership)
        
        # Boost very low ownership players significantly
        df.loc[estimated_ownership < 5, 'ownership_fade'] *= 1.5
        
        return df
    
    def create_correlation_groups(self, df):
        """Create game-based correlation groups for stacking"""
        print("🎲 Creating correlation stacking groups...")
        
        # Group by game
        game_groups = {}
        for game in df['game_id'].unique():
            if pd.isna(game):
                continue
            game_players = df[df['game_id'] == game]
            if len(game_players) >= 2:
                game_groups[game] = game_players.index.tolist()
        
        # Create mini-stacks (2-3 players from same game)
        correlation_bonuses = {}
        for game, players in game_groups.items():
            if len(players) >= 2:
                # Bonus for stacking players from the same game
                for i, p1 in enumerate(players):
                    for p2 in players[i+1:]:
                        correlation_bonuses[(p1, p2)] = 5.0  # +5 points for correlation
        
        return correlation_bonuses
    
    def generate_ceiling_lineup(self, df, lineup_type='high_variance'):
        """Generate a single ceiling-focused lineup"""
        
        # Calculate all ceiling metrics
        df = self.calculate_ceiling_scores(df)
        df = self.calculate_ownership_weights(df)
        correlation_bonuses = self.create_correlation_groups(df)
        
        # Create optimization problem
        prob = LpProblem("CeilingLineup", LpMaximize)
        
        # Decision variables
        player_vars = {}
        for idx in df.index:
            player_vars[idx] = LpVariable(f"player_{idx}", cat='Binary')
        
        # Objective function based on lineup type
        if lineup_type == 'high_variance':
            # Focus on ceiling projection and ownership fade
            objective = lpSum([
                player_vars[idx] * (
                    df.loc[idx, 'ceiling_projection'] * 
                    df.loc[idx, 'ownership_fade'] * 
                    1.1  # Variance boost
                ) for idx in df.index
            ])
        elif lineup_type == 'game_stack':
            # Focus on correlation bonuses
            objective = lpSum([
                player_vars[idx] * df.loc[idx, 'ceiling_projection'] for idx in df.index
            ])
            # Add correlation bonuses
            for (p1, p2), bonus in correlation_bonuses.items():
                if p1 in player_vars and p2 in player_vars:
                    objective += player_vars[p1] * player_vars[p2] * bonus
        else:
            # Balanced ceiling approach
            objective = lpSum([
                player_vars[idx] * (
                    df.loc[idx, 'ceiling_projection'] * 
                    (1 + df.loc[idx, 'ownership_fade'] * 0.3)
                ) for idx in df.index
            ])
        
        prob += objective
        
        # Constraints
        # Salary cap
        prob += lpSum([
            player_vars[idx] * df.loc[idx, 'Salary'] for idx in df.index
        ]) <= self.salary_cap
        
        # Exactly 9 players
        prob += lpSum([player_vars[idx] for idx in df.index]) == 9
        
        # Position requirements
        for pos, (min_req, max_req) in self.position_requirements.items():
            pos_players = df[df['Position'].str.contains(pos, na=False)].index
            if len(pos_players) > 0:
                prob += lpSum([player_vars[idx] for idx in pos_players]) >= min_req
                prob += lpSum([player_vars[idx] for idx in pos_players]) <= max_req
        
        # Solve
        prob.solve(PULP_CBC_CMD(msg=0))
        
        # Extract lineup
        lineup = []
        for idx in df.index:
            if player_vars[idx].value() == 1:
                player_name = f"{df.loc[idx, 'First Name']} {df.loc[idx, 'Last Name']}"
                lineup.append({
                    'Name': player_name,
                    'Position': df.loc[idx, 'Position'],
                    'Salary': df.loc[idx, 'Salary'],
                    'Projected': df.loc[idx, 'projected_fppg'],
                    'Ceiling': df.loc[idx, 'ceiling_projection'],
                    'Ownership_Fade': df.loc[idx, 'ownership_fade']
                })
        
        return pd.DataFrame(lineup)
    
    def generate_ceiling_lineups(self, df, num_lineups=10):
        """Generate multiple ceiling-focused lineups with different strategies"""
        print(f"🚀 Generating {num_lineups} ceiling-focused lineups...")
        
        all_lineups = []
        
        lineup_strategies = [
            'high_variance', 'game_stack', 'balanced', 'contrarian'
        ]
        
        for i in range(num_lineups):
            strategy = lineup_strategies[i % len(lineup_strategies)]
            
            # Add some randomization to prevent identical lineups
            temp_df = df.copy()
            noise = np.random.normal(0, 0.05, len(temp_df))
            temp_df['projected_fppg'] *= (1 + noise)
            
            try:
                lineup = self.generate_ceiling_lineup(temp_df, strategy)
                if len(lineup) == 9:
                    lineup['lineup_id'] = f"ceiling_{i+1}"
                    lineup['strategy'] = strategy
                    lineup['total_salary'] = lineup['Salary'].sum()
                    lineup['total_projected'] = lineup['Projected'].sum()
                    lineup['total_ceiling'] = lineup['Ceiling'].sum()
                    all_lineups.append(lineup)
                    
                    print(f"   ✅ Lineup {i+1} ({strategy}): {lineup['total_ceiling'].sum():.1f} ceiling, ${lineup['total_salary'].sum()}")
                    
            except Exception as e:
                print(f"   ⚠️ Failed to generate lineup {i+1}: {e}")
        
        if all_lineups:
            combined_df = pd.concat(all_lineups, ignore_index=True)
            return combined_df
        else:
            print("❌ Failed to generate any ceiling lineups")
            return pd.DataFrame()

def optimize_for_ceiling(slate_file=None, output_file=None):
    """Main function to run ceiling optimization"""
    print("🎯 CEILING LINEUP OPTIMIZER")
    print("=" * 50)
    print("Targeting 210+ point lineups with high-variance strategies")
    print()
    
    if not slate_file:
        slate_file = "../fd_current_slate/fd_slate_today.csv"
    
    try:
        # Load slate
        df = pd.read_csv(slate_file)
        print(f"📊 Loaded {len(df)} players from slate")
        
        # Add projected FPPG if missing
        if 'projected_fppg' not in df.columns:
            # Use FPPG column if available, otherwise estimate from salary
            if 'FPPG' in df.columns:
                df['projected_fppg'] = df['FPPG']
            else:
                df['projected_fppg'] = (df['Salary'] / 1000) * 2.8
        
        # Add game_id if missing
        if 'game_id' not in df.columns:
            df['game_id'] = df.get('Game', 'GAME_' + df.index.astype(str))
        
        # Initialize optimizer
        optimizer = CeilingLineupOptimizer()
        
        # Generate ceiling lineups
        ceiling_lineups = optimizer.generate_ceiling_lineups(df, num_lineups=15)
        
        if len(ceiling_lineups) > 0:
            if not output_file:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"../data/ceiling_lineups_{timestamp}.csv"
            
            ceiling_lineups.to_csv(output_file, index=False)
            
            print(f"\n💾 Saved {len(ceiling_lineups)} players in ceiling lineups to: {output_file}")
            
            # Summary stats
            lineups_count = ceiling_lineups['lineup_id'].nunique()
            avg_ceiling = ceiling_lineups.groupby('lineup_id')['total_ceiling'].first().mean()
            max_ceiling = ceiling_lineups.groupby('lineup_id')['total_ceiling'].first().max()
            
            print(f"📊 Generated {lineups_count} unique ceiling lineups")
            print(f"🎯 Average ceiling projection: {avg_ceiling:.1f} FPPG")
            print(f"💥 Maximum ceiling projection: {max_ceiling:.1f} FPPG")
            print("🚀 These lineups are optimized for tournament upside!")
            
        else:
            print("❌ Failed to generate ceiling lineups")
            
    except Exception as e:
        print(f"❌ Error in ceiling optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    optimize_for_ceiling()
