#!/usr/bin/env python3
"""
GENERATE 25 FILTERED LINEUPS - Create diverse lineups using only slate data
"""

import pandas as pd
import numpy as np
import random
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_and_filter_slate():
    """Load August 12th slate and apply proper filtering"""
    slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    
    try:
        df = pd.read_csv(slate_file)
        logger.info(f"Original slate size: {len(df)} players")
        
        # Step 1: Filter out injured players
        injury_indicators = ['IL', 'DTD', 'O']
        injured_players = df[df['Injury Indicator'].isin(injury_indicators)]
        logger.info(f"Players with injury indicators: {len(injured_players)}")
        
        healthy_df = df[~df['Injury Indicator'].isin(injury_indicators)]
        logger.info(f"Healthy players remaining: {len(healthy_df)}")
        
        # Step 2: Filter pitchers to probable only
        pitchers = healthy_df[healthy_df['Position'] == 'P']
        probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
        logger.info(f"Probable pitchers: {len(probable_pitchers)}")
        
        # Combine non-pitchers + probable pitchers
        non_pitchers = healthy_df[healthy_df['Position'] != 'P']
        filtered_df = pd.concat([non_pitchers, probable_pitchers], ignore_index=True)
        
        logger.info(f"FINAL FILTERED SLATE: {len(filtered_df)} players")
        logger.info(f"REMOVED: {len(df) - len(filtered_df)} unplayable players ({(len(df) - len(filtered_df))/len(df)*100:.1f}%)")
        
        return filtered_df
        
    except Exception as e:
        logger.error(f"Error loading slate: {e}")
        return None

def optimize_lineup(df, strategy_name, iteration=1, max_attempts=5000):
    """Generate a single optimized lineup using only projections"""
    
    # Different strategies for diversity
    strategies = {
        'Value_Heavy': {'salary_weight': 0.3, 'projection_weight': 0.7, 'min_salary_range': (2000, 4000)},
        'Balanced': {'salary_weight': 0.5, 'projection_weight': 0.5, 'min_salary_range': (2500, 6000)},
        'Star_Power': {'salary_weight': 0.7, 'projection_weight': 0.3, 'min_salary_range': (3000, 12000)},
        'Contrarian': {'salary_weight': 0.2, 'projection_weight': 0.8, 'min_salary_range': (2000, 5000)},
        'Upside': {'salary_weight': 0.4, 'projection_weight': 0.6, 'min_salary_range': (2200, 8000)}
    }
    
    # Cycle through strategies
    strategy_keys = list(strategies.keys())
    strategy = strategies[strategy_keys[iteration % len(strategy_keys)]]
    
    best_lineup = None
    best_score = 0
    
    for attempt in range(max_attempts):
        lineup = {}
        total_salary = 0
        total_projection = 0
        
        # Required positions
        positions_needed = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'P']
        
        used_players = []
        valid_lineup = True
        
        for pos in positions_needed:
            if pos == 'OF' and len([p for p in lineup.values() if p['Position'] == 'OF']) >= 3:
                continue
                
            # Get available players for position
            if pos == 'OF':
                available = df[df['Position'].str.contains('OF', na=False)]
            else:
                available = df[df['Position'].str.contains(pos, na=False)]
            
            # Remove already used players
            available = available[~available.index.isin(used_players)]
            
            if available.empty:
                valid_lineup = False
                break
            
            # Filter by salary range for strategy
            min_sal, max_sal = strategy['min_salary_range']
            available = available[
                (available['Salary'] >= min_sal) & 
                (available['Salary'] <= max_sal)
            ]
            
            if available.empty:
                available = df[df['Position'].str.contains('OF' if pos == 'OF' else pos, na=False)]
                available = available[~available.index.isin(used_players)]
            
            if available.empty:
                valid_lineup = False
                break
            
            # Calculate scores for selection
            available = available.copy()
            available['selection_score'] = (
                strategy['projection_weight'] * available['FPPG'] / available['FPPG'].max() +
                strategy['salary_weight'] * (available['Salary'].max() - available['Salary']) / available['Salary'].max()
            )
            
            # Add randomness for diversity
            available['selection_score'] += np.random.normal(0, 0.1, len(available))
            
            # Select player (weighted random from top candidates)
            top_candidates = available.nlargest(min(10, len(available)), 'selection_score')
            weights = top_candidates['selection_score'].values
            weights = weights - weights.min() + 0.1  # Ensure positive weights
            
            selected_idx = np.random.choice(top_candidates.index, p=weights/weights.sum())
            selected_player = df.loc[selected_idx]
            
            # Check salary constraint
            if total_salary + selected_player['Salary'] > 35000:
                continue
            
            # Add to lineup
            pos_key = f"{pos}_{len([p for p in lineup.values() if p['Position'] == pos]) + 1}" if pos == 'OF' else pos
            lineup[pos_key] = {
                'Name': f"{selected_player['First Name']} {selected_player['Last Name']}",
                'Position': selected_player['Position'],
                'Salary': selected_player['Salary'],
                'FPPG': selected_player['FPPG']
            }
            
            total_salary += selected_player['Salary']
            total_projection += selected_player['FPPG']
            used_players.append(selected_idx)
        
        # Check if we have a complete valid lineup
        if valid_lineup and len(lineup) == 9 and total_salary <= 35000:
            if total_projection > best_score:
                best_score = total_projection
                best_lineup = lineup.copy()
                best_lineup['total_salary'] = total_salary
                best_lineup['projected_score'] = total_projection
    
    return best_lineup, best_score

def main():
    logger.info("TARGET: GENERATING 25 DIVERSE FILTERED LINEUPS")
    logger.info("=" * 60)
    
    # Load and filter slate
    filtered_df = load_and_filter_slate()
    if filtered_df is None:
        return
    
    logger.info(f"Generating 25 lineups from {len(filtered_df)} filtered players...")
    
    all_lineups = []
    
    for i in range(25):
        lineup, score = optimize_lineup(filtered_df, f"Strategy_{i+1}", iteration=i)
        
        if lineup:
            lineup['Strategy'] = f"Filtered_Lineup_{i+1:02d}"
            all_lineups.append(lineup)
            logger.info(f"Generated lineup {i+1:2d}: {score:.1f} projected points (${lineup['total_salary']:,})")
        else:
            logger.warning(f"Failed to generate lineup {i+1}")
    
    # Save lineups for evaluation
    lineup_data = []
    for lineup in all_lineups:
        strategy = lineup['Strategy']
        positions = ['C', '1B', '2B', '3B', 'SS', 'OF_1', 'OF_2', 'OF_3', 'P']
        
        for pos in positions:
            if pos in lineup:
                lineup_data.append({
                    'Strategy': strategy,
                    'Position': pos.replace('_', ''),
                    'Name': lineup[pos]['Name'],
                    'Salary': lineup[pos]['Salary'],
                    'FPPG': lineup[pos]['FPPG']
                })
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"25_FILTERED_LINEUPS_AUG12_{timestamp}.csv"
    pd.DataFrame(lineup_data).to_csv(filename, index=False)
    
    logger.info(f"SUCCESS: Generated {len(all_lineups)} lineups")
    logger.info(f" Saved to: {filename}")
    
    print(f"\nNext step: Evaluate these lineups against actual August 12th results")
    print(f"These lineups were generated using ONLY slate projections, not actual scores!")

if __name__ == "__main__":
    main()
