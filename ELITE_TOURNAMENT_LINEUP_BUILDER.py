#!/usr/bin/env python3
"""
ELITE_TOURNAMENT_LINEUP_BUILDER - Advanced tournament optimizer
Uses ownership modeling + correlation matrix + leverage scoring for elite lineups
"""

import pandas as pd
import numpy as np
from datetime import datetime
import itertools
import logging
from ELITE_DFS_OPTIMIZER import EliteDFSOptimizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class EliteTournamentBuilder:
    def __init__(self):
        self.optimizer = EliteDFSOptimizer()
        self.salary_cap = 60000
        self.lineup_constraints = {
            'P': 2,
            'C': 1, 
            '1B': 1,
            '2B': 1,
            '3B': 1,
            'SS': 1,
            'OF': 3,
            'UTIL': 1  # Any hitter
        }
        
    def build_elite_lineups(self, df, num_lineups=20, tournament_mode='GPP'):
        """Build elite tournament lineups using advanced optimization"""
        
        logger.info("LINEUP: ELITE TOURNAMENT LINEUP BUILDER")
        logger.info("=" * 55)
        
        # Enhance data with elite features
        df_elite = self.optimizer.enhance_with_elite_features(df)
        
        # Get stack recommendations
        stack_analysis = self.optimizer.identify_elite_stacks(df_elite)
        
        elite_lineups = []
        
        if tournament_mode == 'GPP':
            # GPP Strategy: Max leverage + contrarian stacks
            elite_lineups = self.build_gpp_lineups(df_elite, stack_analysis, num_lineups)
        elif tournament_mode == 'CASH':
            # Cash Strategy: High floor + safe ownership
            elite_lineups = self.build_cash_lineups(df_elite, num_lineups)
        else:
            # Mixed Strategy
            gpp_lineups = self.build_gpp_lineups(df_elite, stack_analysis, num_lineups//2)
            cash_lineups = self.build_cash_lineups(df_elite, num_lineups//2)
            elite_lineups = gpp_lineups + cash_lineups
        
        logger.info(f"SUCCESS: Built {len(elite_lineups)} elite tournament lineups")
        
        return elite_lineups, df_elite
    
    def build_gpp_lineups(self, df, stack_analysis, num_lineups):
        """Build GPP lineups focused on leverage and stacking"""
        
        logger.info("TARGET: BUILDING GPP LEVERAGE LINEUPS")
        
        lineups = []
        
        # Get top stacking teams (use top 4-5 teams for variety)
        top_stack_teams = stack_analysis.head(5)['team'].tolist()
        
        for lineup_num in range(num_lineups):
            lineup = self.build_single_gpp_lineup(df, top_stack_teams, lineup_num)
            if lineup:
                lineups.append(lineup)
        
        return lineups
    
    def build_single_gpp_lineup(self, df, stack_teams, lineup_num):
        """Build a single GPP lineup using elite strategies"""
        
        lineup = {}
        remaining_salary = self.salary_cap
        
        # STRATEGY: Target one major stack + leverage plays
        
        # Choose stack team (rotate through top teams)
        stack_team = stack_teams[lineup_num % len(stack_teams)]
        
        # 1. BUILD THE STACK (3-4 hitters from same team)
        stack_players = self.select_team_stack(df, stack_team, remaining_salary)
        
        for pos, player in stack_players.items():
            lineup[pos] = player
            remaining_salary -= player['Salary']
        
        # 2. SELECT CONTRARIAN PITCHERS (High leverage)
        pitcher_budget = min(22000, remaining_salary * 0.4)  # ~40% budget for pitchers
        pitchers = self.select_elite_pitchers(df, pitcher_budget, stack_team)
        
        positions_needed = ['P', 'P']
        for i, pos in enumerate(positions_needed):
            if pos not in lineup and i < len(pitchers):
                lineup[pos] = pitchers[i]
                remaining_salary -= pitchers[i]['Salary']
        
        # 3. FILL REMAINING POSITIONS WITH VALUE/LEVERAGE PLAYS
        remaining_positions = []
        for pos, count in self.lineup_constraints.items():
            if pos == 'P':  # Already handled pitchers
                continue
            filled = sum(1 for p in lineup.keys() if p.startswith(pos))
            for _ in range(count - filled):
                if pos == 'UTIL':
                    remaining_positions.append('UTIL')
                else:
                    remaining_positions.append(pos)
        
        # Fill with best leverage/value plays
        for pos in remaining_positions:
            best_player = self.select_best_remaining_player(df, pos, remaining_salary, lineup, stack_team)
            if best_player is not None:
                # Handle position assignment
                if pos == 'UTIL':
                    # Find first available hitting position
                    for util_pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
                        util_key = f"UTIL({util_pos})"
                        if util_key not in lineup:
                            lineup[util_key] = best_player
                            break
                else:
                    # Count existing players at this position
                    existing_count = sum(1 for k in lineup.keys() if k.startswith(pos))
                    if existing_count == 0:
                        lineup[pos] = best_player
                    else:
                        lineup[f"{pos}{existing_count+1}"] = best_player
                
                remaining_salary -= best_player['Salary']
        
        # Validate lineup
        if self.is_valid_lineup(lineup, remaining_salary):
            return lineup
        else:
            return None
    
    def select_team_stack(self, df, team, budget):
        """Select 3-4 players from the same team for stacking"""
        
        team_players = df[(df['Team'] == team) & (df['Position'] != 'P')].copy()
        team_players = team_players.sort_values('leverage_score', ascending=False)
        
        stack = {}
        stack_budget = min(budget * 0.6, 25000)  # Don't use more than 60% budget on stack
        
        # Prioritize key positions with high leverage
        positions_priority = ['OF', '1B', '3B', 'SS', '2B', 'C']
        
        for pos in positions_priority:
            pos_players = team_players[team_players['Position'].str.contains(pos)]
            
            if len(pos_players) > 0:
                best_player = pos_players.iloc[0]
                
                if best_player['Salary'] <= stack_budget:
                    if pos == 'OF':
                        # Handle multiple OF spots
                        of_count = sum(1 for k in stack.keys() if k.startswith('OF'))
                        if of_count < 3:
                            stack[f"OF{of_count+1}"] = best_player.to_dict()
                            stack_budget -= best_player['Salary']
                    else:
                        if pos not in stack:
                            stack[pos] = best_player.to_dict()
                            stack_budget -= best_player['Salary']
                
                if len(stack) >= 3:  # Got enough for good stack
                    break
        
        return stack
    
    def select_elite_pitchers(self, df, budget, avoid_team):
        """Select pitchers with highest leverage scores"""
        
        pitchers = df[df['Position'] == 'P'].copy()
        
        # Filter out pitchers facing our stack team (negative correlation)
        # This would require opponent data - for now just select best leverage
        
        pitchers = pitchers.sort_values('leverage_score', ascending=False)
        
        selected = []
        remaining_budget = budget
        
        for _, pitcher in pitchers.iterrows():
            if pitcher['Salary'] <= remaining_budget and len(selected) < 2:
                # Prefer probable pitchers with high leverage
                if pitcher.get('Probable Pitcher') == 'Yes' or len(selected) == 1:
                    selected.append(pitcher.to_dict())
                    remaining_budget -= pitcher['Salary']
        
        return selected
    
    def select_best_remaining_player(self, df, position, budget, current_lineup, stack_team):
        """Select best remaining player for position based on leverage"""
        
        # Get players already in lineup
        used_players = set()
        for player in current_lineup.values():
            # Create unique identifier
            player_id = f"{player['First Name']} {player['Last Name']}"
            used_players.add(player_id)
        
        # Filter available players
        # Create name column for filtering
        df_temp = df.copy()
        df_temp['full_name'] = df_temp['First Name'] + ' ' + df_temp['Last Name']
        
        if position == 'UTIL':
            # UTIL can be any hitter
            available = df_temp[(df_temp['Position'] != 'P') & 
                          (~df_temp['full_name'].isin(used_players)) &
                          (df_temp['Salary'] <= budget)].copy()
        else:
            available = df_temp[(df_temp['Position'].str.contains(position)) & 
                          (~df_temp['full_name'].isin(used_players)) &
                          (df_temp['Salary'] <= budget)].copy()
        
        if len(available) == 0:
            return None
        
        # Sort by elite scoring system
        available['elite_score'] = (
            available['leverage_score'] * 0.4 +          # Leverage (40%)
            available['ceiling_proj'] * 0.3 +            # Ceiling (30%)
            available['points_per_dollar'] * 10 * 0.2 +  # Value (20%)
            available['correlation_score'] * 20           # Correlation bonus (10%)
        )
        
        # Small bonus for same-team correlation
        available.loc[available['Team'] == stack_team, 'elite_score'] *= 1.1
        
        best_player = available.sort_values('elite_score', ascending=False).iloc[0]
        return best_player.to_dict()
    
    def build_cash_lineups(self, df, num_lineups):
        """Build cash game lineups focused on floor and consistency"""
        
        logger.info("MONEY: BUILDING CASH GAME LINEUPS")
        
        lineups = []
        
        for lineup_num in range(num_lineups):
            lineup = self.build_single_cash_lineup(df, lineup_num)
            if lineup:
                lineups.append(lineup)
        
        return lineups
    
    def build_single_cash_lineup(self, df, lineup_num):
        """Build single cash lineup using floor projections"""
        
        lineup = {}
        remaining_salary = self.salary_cap
        
        # Cash strategy: Maximize floor * points per dollar
        df_cash = df.copy()
        df_cash['cash_score'] = (
            df_cash['floor_proj'] * 0.5 +           # Floor projection (50%)
            df_cash['FPPG'] * 0.3 +                  # Base projection (30%)
            df_cash['points_per_dollar'] * 10 * 0.2  # Value (20%)
        )
        
        # Build lineup position by position
        for position, count in self.lineup_constraints.items():
            for i in range(count):
                if position == 'P':
                    available = df_cash[(df_cash['Position'] == 'P') & 
                                       (df_cash['Salary'] <= remaining_salary)]
                elif position == 'UTIL':
                    available = df_cash[(df_cash['Position'] != 'P') & 
                                       (df_cash['Salary'] <= remaining_salary)]
                else:
                    available = df_cash[(df_cash['Position'].str.contains(position)) & 
                                       (df_cash['Salary'] <= remaining_salary)]
                
                # Remove already selected players
                used_names = [f"{p['First Name']} {p['Last Name']}" for p in lineup.values()]
                available['full_name'] = available['First Name'] + ' ' + available['Last Name']
                available = available[~available['full_name'].isin(used_names)]
                
                if len(available) > 0:
                    best_player = available.sort_values('cash_score', ascending=False).iloc[0]
                    
                    # Position key handling
                    if i == 0:
                        pos_key = position
                    else:
                        pos_key = f"{position}{i+1}"
                    
                    lineup[pos_key] = best_player.to_dict()
                    remaining_salary -= best_player['Salary']
        
        if self.is_valid_lineup(lineup, remaining_salary):
            return lineup
        else:
            return None
    
    def is_valid_lineup(self, lineup, remaining_salary):
        """Validate lineup meets all constraints"""
        
        if remaining_salary < 0:
            return False
        
        if len(lineup) < 9:  # Need 9 players minimum
            return False
        
        # Check position requirements
        positions = [p['Position'] for p in lineup.values()]
        pitcher_count = sum(1 for p in positions if p == 'P')
        
        if pitcher_count != 2:
            return False
        
        return True
    
    def export_lineups_for_fanduel(self, lineups, df_elite, filename=None):
        """Export lineups in FanDuel format"""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"../fd_current_slate/ELITE_TOURNAMENT_LINEUPS_{timestamp}.csv"
        
        fanduel_lineups = []
        
        for i, lineup in enumerate(lineups):
            fd_lineup = {'Lineup': i + 1}
            
            # Map positions to FanDuel format
            position_map = {
                'P': 'P',
                'C': 'C', 
                '1B': '1B',
                '2B': '2B', 
                '3B': '3B',
                'SS': 'SS',
                'OF': 'OF',
                'UTIL': 'Util'
            }
            
            for pos_key, player in lineup.items():
                # Extract base position
                base_pos = pos_key.split('(')[0].rstrip('123456789')
                
                if base_pos in position_map:
                    fd_pos = position_map[base_pos]
                    player_id = player.get('Id', '')
                    
                    # Handle multiple positions
                    if fd_pos == 'P':
                        if 'P' not in fd_lineup:
                            fd_lineup['P'] = player_id
                        else:
                            fd_lineup['P/DH'] = player_id
                    elif fd_pos == 'OF':
                        if 'OF' not in fd_lineup:
                            fd_lineup['OF'] = player_id
                        elif 'OF2' not in fd_lineup:
                            fd_lineup['OF2'] = player_id
                        else:
                            fd_lineup['OF3'] = player_id
                    else:
                        fd_lineup[fd_pos] = player_id
            
            # Calculate lineup metrics
            total_salary = sum(player['Salary'] for player in lineup.values())
            total_proj = sum(player['FPPG'] for player in lineup.values())
            total_ceiling = sum(player['ceiling_proj'] for player in lineup.values())
            avg_ownership = sum(player['ownership_proj'] for player in lineup.values()) / len(lineup)
            
            fd_lineup.update({
                'Total_Salary': total_salary,
                'Projected_Points': round(total_proj, 1),
                'Ceiling_Projection': round(total_ceiling, 1),
                'Avg_Ownership': round(avg_ownership, 1),
                'Tournament_Score': round(total_ceiling - (avg_ownership * 2), 1)
            })
            
            fanduel_lineups.append(fd_lineup)
        
        # Export to CSV
        df_export = pd.DataFrame(fanduel_lineups)
        df_export.to_csv(filename, index=False)
        
        logger.info(f"SUCCESS: Exported {len(fanduel_lineups)} elite lineups to {filename}")
        
        # Show summary
        avg_proj = df_export['Projected_Points'].mean()
        avg_ceiling = df_export['Ceiling_Projection'].mean()
        avg_ownership = df_export['Avg_Ownership'].mean()
        
        logger.info(f"DATA: LINEUP SUMMARY:")
        logger.info(f"  Average Projection: {avg_proj:.1f}")
        logger.info(f"  Average Ceiling: {avg_ceiling:.1f}")
        logger.info(f"  Average Ownership: {avg_ownership:.1f}%")
        
        return filename

def test_elite_tournament_builder():
    """Test the elite tournament lineup builder"""
    
    try:
        # Load test data
        df = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        logger.info(f"SUCCESS: Loaded test data: {len(df)} players")
        
        # Initialize builder
        builder = EliteTournamentBuilder()
        
        # Build elite lineups
        lineups, df_elite = builder.build_elite_lineups(df, num_lineups=10, tournament_mode='GPP')
        
        # Export for FanDuel
        export_file = builder.export_lineups_for_fanduel(lineups, df_elite)
        
        logger.info(f"\nLINEUP: ELITE TOURNAMENT BUILDER TEST COMPLETE")
        logger.info(f"Generated {len(lineups)} tournament-optimized lineups!")
        
        return lineups, df_elite
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_elite_tournament_builder()
