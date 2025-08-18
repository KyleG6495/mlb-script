#!/usr/bin/env python3
"""
ELITE TOURNAMENT OPTIMIZER WITH ADVANCED OWNERSHIP
Integrate advanced ownership projections into tournament lineup building
"""

import pandas as pd
import numpy as np
import logging
from itertools import combinations
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EliteTournamentBuilder:
    """Elite tournament lineup builder with advanced ownership integration"""
    
    def __init__(self, projections_df, ownership_df):
        self.projections = projections_df
        self.ownership = ownership_df
        self.lineups = []
        
        # Merge projections with ownership
        self.players = self._merge_data()
        
        # Tournament scoring weights
        self.weights = {
            'projection': 0.40,      # Base projection still important
            'ceiling': 0.25,         # Ceiling for upside
            'leverage': 0.20,        # Leverage (proj/ownership) for differentiation
            'value': 0.10,           # Value (proj per $1000)
            'correlation': 0.05      # Team correlation bonus
        }
        
    def _merge_data(self):
        """Merge projections with ownership data"""
        
        # Create player keys for matching
        self.projections['player_key'] = (
            self.projections['First Name'] + ' ' + self.projections['Last Name']
        ).str.strip()
        
        self.ownership['player_key'] = self.ownership['player_name'].str.strip()
        
        # Merge data
        merged = self.projections.merge(
            self.ownership[['player_key', 'ownership', 'leverage_score', 'ownership_tier']],
            on='player_key',
            how='left'
        )
        
        # Fill missing ownership with estimates
        merged['ownership'] = merged['ownership'].fillna(0.15)  # Default 15%
        merged['leverage_score'] = merged['leverage_score'].fillna(
            merged['enhanced_fppg'] / (merged['ownership'] * 100 + 1)
        )
        merged['ownership_tier'] = merged['ownership_tier'].fillna('Medium')
        
        logger.info(f"SUCCESS: Merged {len(merged)} players with ownership data")
        logger.info(f"DATA: Ownership coverage: {(~merged['ownership'].isna()).mean():.1%}")
        
        return merged
    
    def calculate_tournament_score(self, player_row):
        """Calculate comprehensive tournament score for player"""
        
        # Base metrics
        projection = player_row['enhanced_fppg']
        ceiling = projection * 1.8  # Estimate ceiling
        leverage = player_row['leverage_score']
        value = projection / (player_row['Salary'] / 1000)
        
        # Team correlation bonus (same team as other high-leverage plays)
        correlation_bonus = 0
        if player_row['Team'] in ['HOU', 'TOR', 'ATL', 'BOS', 'MIA', 'LAD']:  # Top teams
            correlation_bonus = 2
        
        # Calculate weighted score
        tournament_score = (
            projection * self.weights['projection'] +
            ceiling * self.weights['ceiling'] +
            leverage * self.weights['leverage'] +
            value * self.weights['value'] +
            correlation_bonus * self.weights['correlation']
        )
        
        return tournament_score
    
    def identify_core_plays(self):
        """Identify core tournament plays across ownership tiers"""
        
        logger.info("TARGET: IDENTIFYING CORE TOURNAMENT PLAYS")
        logger.info("=" * 50)
        
        # Calculate tournament scores
        self.players['tournament_score'] = self.players.apply(
            self.calculate_tournament_score, axis=1
        )
        
        core_plays = {
            'chalk': [],      # High ownership, must-play
            'leverage': [],   # Medium ownership, high leverage
            'contrarian': [], # Low ownership, pivot plays
            'punt': []        # Value plays for salary relief
        }
        
        # Chalk plays (high ownership, good scores)
        chalk_candidates = self.players[
            (self.players['ownership'] >= 0.20) &
            (self.players['enhanced_fppg'] >= 15)
        ].nlargest(15, 'tournament_score')
        
        core_plays['chalk'] = chalk_candidates
        
        # Leverage plays (medium/low ownership, high scores)
        leverage_candidates = self.players[
            (self.players['ownership'] < 0.20) &
            (self.players['leverage_score'] >= 2.0) &
            (self.players['enhanced_fppg'] >= 10)
        ].nlargest(20, 'leverage_score')
        
        core_plays['leverage'] = leverage_candidates
        
        # Contrarian plays (very low ownership, decent scores)
        contrarian_candidates = self.players[
            (self.players['ownership'] < 0.05) &
            (self.players['enhanced_fppg'] >= 8)
        ].nlargest(15, 'tournament_score')
        
        core_plays['contrarian'] = contrarian_candidates
        
        # Punt plays (cheap, efficient)
        punt_candidates = self.players[
            (self.players['Salary'] <= 5000) &
            (self.players['enhanced_fppg'] >= 6)
        ].nlargest(10, 'tournament_score')
        
        core_plays['punt'] = punt_candidates
        
        # Log core plays
        for play_type, players in core_plays.items():
            logger.info(f"\n {play_type.upper()} PLAYS ({len(players)}):")
            for idx, player in players.head(5).iterrows():
                logger.info(f"  {player['player_key']} ({player['Position']}) - "
                           f"${player['Salary']} | {player['enhanced_fppg']:.1f} proj | "
                           f"{player['ownership']:.1%} own | {player['tournament_score']:.1f} score")
        
        return core_plays
    
    def build_leverage_stacks(self, core_plays):
        """Build team stacks focusing on leverage opportunities"""
        
        logger.info("\n BUILDING LEVERAGE STACKS")
        logger.info("=" * 30)
        
        # Get hitters only for stacking
        hitters = self.players[self.players['Position'] != 'P'].copy()
        
        # Identify best stacking teams based on leverage
        team_leverage = hitters.groupby('Team').agg({
            'leverage_score': 'mean',
            'enhanced_fppg': 'sum',
            'ownership': 'mean',
            'tournament_score': 'sum'
        }).reset_index()
        
        team_leverage['stack_score'] = (
            team_leverage['leverage_score'] * 0.4 +
            team_leverage['enhanced_fppg'] * 0.01 +  # Scale down projection sum
            (1 - team_leverage['ownership']) * 50 +   # Lower ownership is better
            team_leverage['tournament_score'] * 0.01  # Scale down tournament score sum
        )
        
        top_stack_teams = team_leverage.nlargest(8, 'stack_score')
        
        logger.info("TARGET: Top stacking teams by leverage:")
        for idx, team in top_stack_teams.iterrows():
            logger.info(f"  {team['Team']}: {team['stack_score']:.1f} score | "
                       f"{team['leverage_score']:.2f} avg leverage | "
                       f"{team['ownership']:.1%} avg ownership")
        
        stack_lineups = []
        
        # Build stacks for top teams
        for idx, team_row in top_stack_teams.head(6).iterrows():
            team = team_row['Team']
            team_hitters = hitters[hitters['Team'] == team].nlargest(8, 'tournament_score')
            
            if len(team_hitters) < 4:
                continue
                
            # Try different stack combinations
            for stack_size in [4, 3]:  # 4-man and 3-man stacks
                for combo in combinations(team_hitters.index, stack_size):
                    
                    lineup = self._build_lineup_around_stack(list(combo), core_plays)
                    if lineup:
                        stack_lineups.append(lineup)
                        if len([l for l in stack_lineups if l['stack_team'] == team]) >= 2:  # Limit stacks per team
                            break
                if len(stack_lineups) >= 8:  # Allow more team stacks, fewer contrarian
                    break
        
        return stack_lineups
    
    def _build_lineup_around_stack(self, stack_indices, core_plays):
        """Build complete lineup around team stack"""
        
        lineup_players = []
        used_positions = set()
        used_salary = 0
        
        # Add stack players
        for idx in stack_indices:
            player = self.players.loc[idx]
            lineup_players.append(player)
            used_positions.add(player['Position'])
            used_salary += player['Salary']
        
        # Determine remaining positions needed
        all_positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        remaining_positions = all_positions.copy()
        
        # Remove positions we already have
        for pos in used_positions:
            if pos in remaining_positions:
                remaining_positions.remove(pos)
        
        # Fill remaining positions
        remaining_salary = 35000 - used_salary
        used_teams = [p['Team'] for p in lineup_players]
        
        for pos in remaining_positions:
            
            # Get available players for position
            available = self.players[
                (self.players['Position'] == pos) &
                (~self.players.index.isin([p.name for p in lineup_players])) &
                (self.players['Salary'] <= remaining_salary)  # Remove 0.8 constraint
            ].copy()
            
            if len(available) == 0:
                return None  # Can't complete lineup
            
            # Prefer chalk/leverage plays if available
            chalk_available = available[available['ownership'] >= 0.15]
            leverage_available = available[available['leverage_score'] >= 2.0]
            
            if len(chalk_available) > 0 and remaining_salary > 8000:
                best_player = chalk_available.nlargest(1, 'tournament_score').iloc[0]
            elif len(leverage_available) > 0:
                best_player = leverage_available.nlargest(1, 'tournament_score').iloc[0]
            else:
                best_player = available.nlargest(1, 'tournament_score').iloc[0]
            
            lineup_players.append(best_player)
            used_salary += best_player['Salary']
            remaining_salary = 35000 - used_salary
        
        # Validate lineup
        if len(lineup_players) != 9 or used_salary > 35000:
            return None
            
        # Calculate lineup metrics
        lineup_metrics = {
            'players': lineup_players,
            'total_salary': used_salary,
            'total_projection': sum(p['enhanced_fppg'] for p in lineup_players),
            'total_ceiling': sum(p['enhanced_fppg'] * 1.8 for p in lineup_players),
            'avg_ownership': np.mean([p['ownership'] for p in lineup_players]),
            'leverage_score': sum(p['leverage_score'] for p in lineup_players),
            'tournament_score': sum(p['tournament_score'] for p in lineup_players),
            'stack_team': self.players.loc[stack_indices[0]]['Team'] if stack_indices else 'None',
            'stack_size': len(stack_indices)
        }
        
        return lineup_metrics
    
    def build_contrarian_lineups(self, core_plays):
        """Build low-ownership contrarian lineups"""
        
        logger.info("\n BUILDING CONTRARIAN LINEUPS")
        logger.info("=" * 30)
        
        contrarian_lineups = []
        
        # Focus on players under 5% ownership
        contrarian_pool = self.players[
            (self.players['ownership'] < 0.05) &
            (self.players['enhanced_fppg'] >= 6)
        ].copy()
        
        # Build lineups focusing on low ownership
        for attempt in range(15):  # Try 15 contrarian builds for better diversity
            
            lineup_players = []
            used_salary = 0
            used_positions = set()
            
            # Randomize starting approach for diversity
            start_with_pitcher = np.random.random() < 0.7  # 70% start with pitcher
            
            if start_with_pitcher:
                # Start with contrarian pitcher
                contrarian_pitchers = contrarian_pool[contrarian_pool['Position'] == 'P']
                if len(contrarian_pitchers) > 0:
                    # Add randomness to pitcher selection (top 3)
                    top_pitchers = contrarian_pitchers.nlargest(3, 'tournament_score')
                    pitcher = top_pitchers.sample(1).iloc[0]
                    lineup_players.append(pitcher)
                    used_salary += pitcher['Salary']
                    used_positions.add('P')
            
            # Fill remaining positions with more randomness
            remaining_positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
            if not start_with_pitcher:
                remaining_positions.insert(0, 'P')
                
            np.random.shuffle(remaining_positions)  # Randomize position fill order
            remaining_salary = 35000 - used_salary
            
            for pos in remaining_positions:
                
                # Prefer contrarian plays, fall back to leverage/chalk
                pos_pool = self.players[
                    (self.players['Position'] == pos) &
                    (~self.players.index.isin([p.name for p in lineup_players])) &
                    (self.players['Salary'] <= remaining_salary * 0.9)
                ]
                
                if len(pos_pool) == 0:
                    break
                
                # 50% chance to use contrarian, 30% leverage, 20% value plays
                rand_val = np.random.random()
                if rand_val < 0.5:
                    contrarian_pos = pos_pool[pos_pool['ownership'] < 0.08]
                    if len(contrarian_pos) > 0:
                        # Select from top 3 contrarian options for diversity
                        top_contrarian = contrarian_pos.nlargest(3, 'tournament_score')
                        best_player = top_contrarian.sample(1).iloc[0]
                    else:
                        best_player = pos_pool.nlargest(1, 'tournament_score').iloc[0]
                elif rand_val < 0.8:
                    # Leverage plays
                    leverage_pos = pos_pool.nlargest(5, 'leverage_score')
                    best_player = leverage_pos.sample(1).iloc[0]
                else:
                    # Value plays (salary efficiency)
                    pos_pool['value_score'] = pos_pool['enhanced_fppg'] / (pos_pool['Salary'] / 1000)
                    value_pos = pos_pool.nlargest(5, 'value_score')
                    best_player = value_pos.sample(1).iloc[0]
                
                lineup_players.append(best_player)
                used_salary += best_player['Salary']
                remaining_salary = 35000 - used_salary
            
            # Validate and add lineup
            if len(lineup_players) == 9 and used_salary <= 35000:
                lineup_metrics = {
                    'players': lineup_players,
                    'total_salary': used_salary,
                    'total_projection': sum(p['enhanced_fppg'] for p in lineup_players),
                    'avg_ownership': np.mean([p['ownership'] for p in lineup_players]),
                    'leverage_score': sum(p['leverage_score'] for p in lineup_players),
                    'tournament_score': sum(p['tournament_score'] for p in lineup_players),
                    'stack_team': 'No Stack',  # Clearer - these aren't team stacks
                    'stack_size': 0
                }
                
                contrarian_lineups.append(lineup_metrics)
        
        return contrarian_lineups
    
    def optimize_tournament_lineups(self):
        """Main function to build elite tournament lineups"""
        
        logger.info("START: ELITE TOURNAMENT OPTIMIZER STARTING")
        logger.info("=" * 60)
        
        # Step 1: Identify core plays
        core_plays = self.identify_core_plays()
        
        # Step 2: Build leverage stacks
        stack_lineups = self.build_leverage_stacks(core_plays)
        
        # Step 3: Build contrarian lineups
        contrarian_lineups = self.build_contrarian_lineups(core_plays)
        
        # Combine all lineups
        all_lineups = stack_lineups + contrarian_lineups
        
        # Remove duplicates by comparing player combinations
        unique_lineups = []
        seen_combinations = set()
        
        for lineup in all_lineups:
            # Create a signature for this lineup based on player names
            player_names = sorted([p['player_key'] for p in lineup['players']])
            lineup_signature = tuple(player_names)
            
            if lineup_signature not in seen_combinations:
                seen_combinations.add(lineup_signature)
                unique_lineups.append(lineup)
        
        # Sort by tournament score
        unique_lineups.sort(key=lambda x: x['tournament_score'], reverse=True)
        
        logger.info(f"\nSUCCESS: Built {len(unique_lineups)} unique elite tournament lineups (removed {len(all_lineups) - len(unique_lineups)} duplicates)")
        
        # Log top lineups
        logger.info("\nLINEUP: TOP TOURNAMENT LINEUPS:")
        for i, lineup in enumerate(unique_lineups[:5]):
            logger.info(f"\nLineup #{i+1} - {lineup['stack_team']} Stack:")
            logger.info(f"  MONEY: Salary: ${lineup['total_salary']:,}")
            logger.info(f"  PROGRESS: Projection: {lineup['total_projection']:.1f}")
            logger.info(f"  OWNERSHIP: Avg Ownership: {lineup['avg_ownership']:.1%}")
            logger.info(f"   Leverage: {lineup['leverage_score']:.1f}")
            logger.info(f"  TARGET: Tournament Score: {lineup['tournament_score']:.1f}")
            
            for player in lineup['players']:
                logger.info(f"    {player['player_key']} ({player['Position']}) - "
                           f"${player['Salary']} | {player['enhanced_fppg']:.1f} | "
                           f"{player['ownership']:.1%}")
        
        return unique_lineups
    
    def export_lineups(self, lineups, filename=None):
        """Export lineups to CSV for FanDuel"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../data/elite_tournament_lineups_{timestamp}.csv"
        
        export_data = []
        
        for i, lineup in enumerate(lineups[:20]):  # Top 20 lineups
            
            # Create position mapping
            positions = {'P': None, 'C': None, '1B': None, '2B': None, 
                        '3B': None, 'SS': None, 'OF1': None, 'OF2': None, 'OF3': None}
            
            of_count = 0
            for player in lineup['players']:
                pos = player['Position']
                if pos == 'OF':
                    of_count += 1
                    pos = f'OF{of_count}'
                
                if positions[pos] is None:
                    positions[pos] = player['player_key']
            
            export_data.append({
                'Lineup': i + 1,
                'P': positions['P'],
                'C': positions['C'],
                '1B': positions['1B'],
                '2B': positions['2B'],
                '3B': positions['3B'],
                'SS': positions['SS'],
                'OF1': positions['OF1'],
                'OF2': positions['OF2'],
                'OF3': positions['OF3'],
                'Total_Salary': lineup['total_salary'],
                'Projected_Points': round(lineup['total_projection'], 1),
                'Avg_Ownership': round(lineup['avg_ownership'] * 100, 1),
                'Leverage_Score': round(lineup['leverage_score'], 1),
                'Tournament_Score': round(lineup['tournament_score'], 1),
                'Stack_Team': lineup['stack_team']
            })
        
        export_df = pd.DataFrame(export_data)
        export_df.to_csv(filename, index=False)
        
        logger.info(f" Exported {len(export_data)} lineups to {filename}")
        
        return filename

def main():
    """Main execution function"""
    
    try:
        # Use dynamic current date
        current_date = datetime.now().strftime("%Y%m%d")
        
        # Load projections and ownership data with dynamic dates
        import glob
        
        # Find today's enhanced projections
        enhanced_files = glob.glob(f"../data/enhanced_projections_{current_date}_*.csv")
        if enhanced_files:
            projections_file = enhanced_files[-1]
            logger.info(f"DATA: Using projections: {projections_file}")
        else:
            projections_file = "../fd_current_slate/fd_slate_today.csv"
            logger.info(f"DATA: Using fallback slate: {projections_file}")
        
        # Find today's ownership projections
        ownership_files = glob.glob(f"../data/advanced_ownership_projections_{current_date}_*.csv")
        if ownership_files:
            ownership_file = ownership_files[-1]
            logger.info(f"PROGRESS: Using ownership: {ownership_file}")
        else:
            logger.error("ERROR: No ownership projections found for today!")
            return None
        
        projections = pd.read_csv(projections_file)
        ownership = pd.read_csv(ownership_file)
        
        # COLUMN MAPPING: Handle different data sources
        if 'FPPG' in projections.columns and 'enhanced_fppg' not in projections.columns:
            projections['enhanced_fppg'] = projections['FPPG']
            logger.info("MAPPING: Mapped FPPG -> enhanced_fppg for fd_slate compatibility")
        
        logger.info(f"SUCCESS: Loaded {len(projections)} projections and {len(ownership)} ownership records")
        
        # CRITICAL: Apply the same filtering as the main system
        logger.info("FILTER: Applying injury and probable pitcher filters...")
        original_count = len(projections)
        
        # Filter out injured players (IL, O, DTD)
        if 'Injury Indicator' in projections.columns:
            projections = projections[
                (projections['Injury Indicator'].isna()) | 
                (projections['Injury Indicator'] == '') |
                (projections['Injury Indicator'] == ' ')
            ]
            logger.info(f" Filtered out {original_count - len(projections)} injured players")
        
        # For pitchers: Keep only probable pitchers (marked "Yes")
        if 'Probable Pitcher' in projections.columns:
            pitcher_mask = projections['Position'] == 'P'
            prob_pitchers = projections[pitcher_mask & (projections['Probable Pitcher'] == 'Yes')]
            non_pitchers = projections[projections['Position'] != 'P']
            projections = pd.concat([prob_pitchers, non_pitchers], ignore_index=True)
            logger.info(f"BASEBALL: Kept {len(prob_pitchers)} probable pitchers only")
        
        # For hitters: Keep only starting lineup players (Batting Order > 0)
        if 'Batting Order' in projections.columns:
            hitter_mask = projections['Position'] != 'P'
            starting_hitters = projections[hitter_mask & (projections['Batting Order'] > 0)]
            pitchers = projections[projections['Position'] == 'P']
            projections = pd.concat([pitchers, starting_hitters], ignore_index=True)
            logger.info(f" Kept {len(starting_hitters)} starting hitters only")
        
        logger.info(f"SUCCESS: Final filtered players: {len(projections)} (removed {original_count - len(projections)} unplayable)")
        
        # Initialize elite tournament builder
        builder = EliteTournamentBuilder(projections, ownership)
        
        # Build elite lineups
        elite_lineups = builder.optimize_tournament_lineups()
        
        # Export results
        export_file = builder.export_lineups(elite_lineups)
        
        logger.info(f"\nCOMPLETE: ELITE TOURNAMENT OPTIMIZATION COMPLETE!")
        logger.info(f" Results saved to: {export_file}")
        
        return elite_lineups
        
    except Exception as e:
        logger.error(f"ERROR: Error in elite tournament optimization: {str(e)}")
        raise

if __name__ == "__main__":
    elite_results = main()
