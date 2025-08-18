#!/usr/bin/env python3
"""
CONTRARIAN LINEUP BACKTEST - Test the contrarian lineups against actual results
"""

import pandas as pd
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_actual_results():
    """Load the actual results from yesterday"""
    try:
        # Try to find the most recent actual results
        results_files = [f for f in os.listdir("../data") if f.startswith("actual_results_") and f.endswith(".csv")]
        if results_files:
            latest_results = sorted(results_files)[-1]
            results_df = pd.read_csv(f"../data/{latest_results}")
            logger.info(f"✅ Loaded actual results from {latest_results}")
            logger.info(f"Found {len(results_df)} player performances")
            return results_df, latest_results
        else:
            logger.error("❌ No actual results files found")
            return None, None
            
    except Exception as e:
        logger.error(f"Error loading actual results: {e}")
        return None, None

def load_contrarian_lineups():
    """Load the contrarian lineups we just generated"""
    try:
        # Find the most recent contrarian lineup file
        contrarian_files = [f for f in os.listdir("../data") if f.startswith("CONTRARIAN_TOURNAMENT_LINEUPS_")]
        if contrarian_files:
            latest_contrarian = sorted(contrarian_files)[-1]
            lineups_df = pd.read_csv(f"../data/{latest_contrarian}")
            logger.info(f"✅ Loaded contrarian lineups from {latest_contrarian}")
            logger.info(f"Found {len(lineups_df)} contrarian lineups")
            return lineups_df, latest_contrarian
        else:
            logger.error("❌ No contrarian lineup files found")
            return None, None
            
    except Exception as e:
        logger.error(f"Error loading contrarian lineups: {e}")
        return None, None

def create_player_lookup(results_df):
    """Create a lookup dictionary for player scores"""
    player_lookup = {}
    
    for _, player in results_df.iterrows():
        # Try multiple name formats
        full_name = player.get('name', '')
        player_id = player.get('player_id', '')
        fanduel_points = player.get('fanduel_points', 0)
        
        # Add to lookup with different key formats
        if full_name:
            # Full name
            player_lookup[full_name.lower()] = fanduel_points
            # Last name only
            if ' ' in full_name:
                last_name = full_name.split()[-1]
                if last_name.lower() not in player_lookup:
                    player_lookup[last_name.lower()] = fanduel_points
        
        # Player ID lookup
        if player_id:
            player_lookup[str(player_id)] = fanduel_points
    
    logger.info(f"✅ Created player lookup with {len(player_lookup)} entries")
    return player_lookup

def score_lineup(lineup_row, player_lookup):
    """Score a single lineup against actual results"""
    total_score = 0
    players_found = 0
    missing_players = []
    
    # Check each position in the lineup
    positions = ['P', 'C/1B', 'SS', 'OF', 'OF ', 'OF  ', '1B', '2B', '3B']
    
    for pos in positions:
        player_name = lineup_row.get(pos, '')
        if pd.isna(player_name) or player_name == '':
            continue
            
        player_name_clean = str(player_name).strip()
        
        # Try to find player score
        score = None
        
        # Try different lookup strategies
        lookup_keys = [
            player_name_clean.lower(),
            player_name_clean.lower().replace(' ', ''),
        ]
        
        # Try last name only
        if ' ' in player_name_clean:
            last_name = player_name_clean.split()[-1]
            lookup_keys.append(last_name.lower())
        
        for key in lookup_keys:
            if key in player_lookup:
                score = player_lookup[key]
                break
        
        if score is not None:
            total_score += score
            players_found += 1
        else:
            missing_players.append(player_name_clean)
    
    return total_score, players_found, missing_players

def main():
    logger.info("🔍 CONTRARIAN LINEUP BACKTEST")
    logger.info("=" * 50)
    logger.info("Testing contrarian lineups against actual results...")
    
    # Load data
    results_df, results_file = load_actual_results()
    if results_df is None:
        return
    
    lineups_df, lineups_file = load_contrarian_lineups()
    if lineups_df is None:
        return
    
    # Create player lookup
    player_lookup = create_player_lookup(results_df)
    
    # Score each contrarian lineup
    lineup_scores = []
    
    logger.info(f"\n🏆 SCORING {len(lineups_df)} CONTRARIAN LINEUPS:")
    
    for idx, lineup in lineups_df.iterrows():
        score, found, missing = score_lineup(lineup, player_lookup)
        
        lineup_scores.append({
            'lineup_num': idx + 1,
            'total_score': score,
            'players_found': found,
            'missing_players': missing
        })
        
        logger.info(f"Lineup {idx+1}: {score:.1f} pts ({found}/9 players found)")
        if missing:
            logger.info(f"  Missing: {', '.join(missing[:3])}{'...' if len(missing) > 3 else ''}")
    
    # Sort by score
    lineup_scores.sort(key=lambda x: x['total_score'], reverse=True)
    
    # Summary
    logger.info(f"\n📊 CONTRARIAN LINEUP PERFORMANCE:")
    logger.info(f"Data Source: {results_file}")
    logger.info(f"Lineups Tested: {len(lineup_scores)}")
    
    if lineup_scores:
        best_score = lineup_scores[0]['total_score']
        avg_score = sum([ls['total_score'] for ls in lineup_scores]) / len(lineup_scores)
        
        logger.info(f"\n🏆 TOP 5 CONTRARIAN LINEUPS:")
        for i, ls in enumerate(lineup_scores[:5]):
            logger.info(f"  {i+1}. Lineup {ls['lineup_num']:2}: {ls['total_score']:6.1f} pts ({ls['players_found']}/9 players)")
        
        logger.info(f"\n📈 PERFORMANCE SUMMARY:")
        logger.info(f"Best Contrarian Score: {best_score:.1f} points")
        logger.info(f"Average Contrarian Score: {avg_score:.1f} points")
        
        # Compare to previous best
        logger.info(f"\n🎯 CONTRARIAN vs PREVIOUS BEST:")
        logger.info(f"Previous Best (Elite Tournament): 193.9 points")
        logger.info(f"Best Contrarian: {best_score:.1f} points")
        
        if best_score > 193.9:
            logger.info(f"✅ IMPROVEMENT: +{best_score - 193.9:.1f} points!")
        else:
            logger.info(f"❌ Gap: -{193.9 - best_score:.1f} points")
        
        # Check for 230+ scores (tournament winning range)
        winners = [ls for ls in lineup_scores if ls['total_score'] >= 230]
        if winners:
            logger.info(f"\n🏆 TOURNAMENT WINNERS (230+ pts): {len(winners)} lineups!")
            for w in winners:
                logger.info(f"  🥇 Lineup {w['lineup_num']}: {w['total_score']:.1f} pts")
        else:
            logger.info(f"\n⚠️  No lineups reached 230+ tournament winning threshold")
            logger.info(f"Highest: {best_score:.1f} points")
    
    logger.info(f"\n💡 ANALYSIS COMPLETE")

if __name__ == "__main__":
    main()
