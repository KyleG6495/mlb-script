#!/usr/bin/env python3
"""
ELITE_DFS_DEBUG - Debug the lineup building issues
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_lineup_building():
    """Debug why lineups aren't building"""
    
    try:
        # Load test data
        df = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        logger.info(f"SUCCESS: Loaded test data: {len(df)} players")
        
        # Check data structure
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Positions: {df['Position'].value_counts()}")
        logger.info(f"Salary range: ${df['Salary'].min()} - ${df['Salary'].max()}")
        
        # Check probable pitchers
        probable_pitchers = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'Yes')]
        logger.info(f"Probable pitchers: {len(probable_pitchers)}")
        
        # Check budget constraints
        min_roster_cost = (
            df[df['Position'] == 'P']['Salary'].nsmallest(2).sum() +  # 2 cheapest pitchers
            df[df['Position'] != 'P']['Salary'].nsmallest(7).sum()    # 7 cheapest hitters
        )
        
        max_roster_cost = (
            df[df['Position'] == 'P']['Salary'].nlargest(2).sum() +   # 2 most expensive pitchers
            df[df['Position'] != 'P']['Salary'].nlargest(7).sum()     # 7 most expensive hitters
        )
        
        logger.info(f"Min possible roster cost: ${min_roster_cost}")
        logger.info(f"Max possible roster cost: ${max_roster_cost}")
        logger.info(f"Salary cap: $60000")
        
        # Check position availability
        for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
            pos_players = df[df['Position'].str.contains(pos)]
            logger.info(f"{pos}: {len(pos_players)} players available")
            
            if len(pos_players) > 0:
                min_sal = pos_players['Salary'].min()
                max_sal = pos_players['Salary'].max()
                logger.info(f"  {pos} salary range: ${min_sal} - ${max_sal}")
        
        # Test simple lineup construction
        logger.info("\nSTEP: TESTING SIMPLE LINEUP CONSTRUCTION")
        
        lineup = {}
        budget = 60000
        
        # Add 2 cheapest probable pitchers
        probable_p = df[(df['Position'] == 'P') & (df['Probable Pitcher'] == 'Yes')].nsmallest(2, 'Salary')
        
        if len(probable_p) >= 2:
            lineup['P1'] = probable_p.iloc[0].to_dict()
            lineup['P2'] = probable_p.iloc[1].to_dict()
            budget -= (probable_p.iloc[0]['Salary'] + probable_p.iloc[1]['Salary'])
            logger.info(f"Added pitchers, remaining budget: ${budget}")
        else:
            logger.warning("Not enough probable pitchers available!")
            return
        
        # Add hitters by position
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
        
        for i, pos in enumerate(positions):
            pos_players = df[df['Position'].str.contains(pos)]
            
            # Remove already used players
            used_ids = [p['Id'] for p in lineup.values()]
            pos_players = pos_players[~pos_players['Id'].isin(used_ids)]
            
            # Filter by budget
            affordable = pos_players[pos_players['Salary'] <= budget]
            
            if len(affordable) > 0:
                # Pick cheapest affordable player for now
                best_player = affordable.nsmallest(1, 'Salary').iloc[0]
                lineup[f"{pos}_{i}"] = best_player.to_dict()
                budget -= best_player['Salary']
                logger.info(f"Added {pos} player: {best_player['First Name']} {best_player['Last Name']} (${best_player['Salary']}), remaining: ${budget}")
            else:
                logger.warning(f"No affordable {pos} players available! Budget: ${budget}")
                break
        
        # Add UTIL player
        if budget > 0:
            hitters = df[df['Position'] != 'P']
            used_ids = [p['Id'] for p in lineup.values()]
            available_hitters = hitters[~hitters['Id'].isin(used_ids)]
            affordable_hitters = available_hitters[available_hitters['Salary'] <= budget]
            
            if len(affordable_hitters) > 0:
                util_player = affordable_hitters.nsmallest(1, 'Salary').iloc[0]
                lineup['UTIL'] = util_player.to_dict()
                budget -= util_player['Salary']
                logger.info(f"Added UTIL player: {util_player['First Name']} {util_player['Last Name']} (${util_player['Salary']}), remaining: ${budget}")
        
        total_cost = sum(p['Salary'] for p in lineup.values())
        logger.info(f"\nSUCCESS: SIMPLE LINEUP CONSTRUCTED:")
        logger.info(f"  Players: {len(lineup)}")
        logger.info(f"  Total cost: ${total_cost}")
        logger.info(f"  Remaining budget: ${60000 - total_cost}")
        
        # Show lineup
        for pos, player in lineup.items():
            logger.info(f"  {pos}: {player['First Name']} {player['Last Name']} (${player['Salary']})")
        
        return lineup
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_lineup_building()
