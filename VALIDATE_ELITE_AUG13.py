#!/usr/bin/env python3
"""
VALIDATE ELITE LINEUPS vs AUGUST 13 ACTUAL RESULTS
Compare our new elite lineups vs what actually happened
"""

import pandas as pd
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_elite_vs_actual():
    """Validate our elite lineups against August 13th actual results"""
    
    logger.info(" ELITE LINEUP VALIDATION vs AUGUST 13 ACTUALS")
    logger.info("=" * 60)
    
    try:
        # Load elite lineups
        elite_lineups = pd.read_csv("../fd_current_slate/SIMPLIFIED_ELITE_LINEUPS_20250814_125913.csv")
        logger.info(f"SUCCESS: Loaded {len(elite_lineups)} elite lineups")
        
        # Load actual results
        actual_results = pd.read_csv("../data/actual_results_20250813.csv")
        logger.info(f"SUCCESS: Loaded {len(actual_results)} actual results")
        
        # Load projections for player mapping
        projections = pd.read_csv("../data/enhanced_projections_20250813_175916.csv")
        logger.info(f"SUCCESS: Loaded {len(projections)} projections for mapping")
        
        # Create player mapping from projections to actual results
        player_mapping = create_player_mapping(projections, actual_results)
        logger.info(f"SUCCESS: Created mapping for {len(player_mapping)} players")
        
        # Validate each elite lineup
        logger.info(f"\nDATA: ELITE LINEUP VALIDATION RESULTS:")
        logger.info("=" * 45)
        
        elite_scores = []
        
        for idx, lineup_row in elite_lineups.iterrows():
            actual_score = calculate_lineup_actual_score(lineup_row, player_mapping, actual_results)
            projected_score = lineup_row.get('Total_Projection', 0)
            ceiling_score = lineup_row.get('Total_Ceiling', 0)
            avg_ownership = lineup_row.get('Avg_Ownership', 0)
            
            elite_scores.append({
                'lineup_id': idx + 1,
                'projected': projected_score,
                'ceiling': ceiling_score,
                'actual': actual_score,
                'ownership': avg_ownership,
                'accuracy': (actual_score / projected_score * 100) if projected_score > 0 else 0
            })
            
            logger.info(f"\nElite Lineup {idx + 1}:")
            logger.info(f"   PROGRESS: Projected: {projected_score:.1f} points")
            logger.info(f"   START: Ceiling: {ceiling_score:.1f} points")
            logger.info(f"   LINEUP: Actual: {actual_score:.1f} points")
            logger.info(f"   OWNERSHIP: Avg Ownership: {avg_ownership:.1f}%")
            logger.info(f"   DATA: Accuracy: {(actual_score / projected_score * 100):.1f}%" if projected_score > 0 else "   DATA: Accuracy: N/A")
            
            # Check if this would have cashed/won
            if actual_score >= 271:
                logger.info(f"    WOULD HAVE WON TOURNAMENT!")
            elif actual_score >= 200:
                logger.info(f"   MONEY: WOULD HAVE CASHED!")
            else:
                logger.info(f"   ERROR: Would not have cashed")
        
        # Summary analysis
        elite_df = pd.DataFrame(elite_scores)
        
        logger.info(f"\nLINEUP: ELITE SYSTEM PERFORMANCE SUMMARY:")
        logger.info("=" * 40)
        
        best_score = elite_df['actual'].max()
        avg_score = elite_df['actual'].mean()
        cash_count = sum(1 for score in elite_df['actual'] if score >= 200)
        win_count = sum(1 for score in elite_df['actual'] if score >= 271)
        
        logger.info(f"   TARGET: Best Score: {best_score:.1f} points")
        logger.info(f"   DATA: Average Score: {avg_score:.1f} points")
        logger.info(f"   MONEY: Lineups that would cash: {cash_count}/{len(elite_df)} ({cash_count/len(elite_df)*100:.1f}%)")
        logger.info(f"   LINEUP: Lineups that would win: {win_count}/{len(elite_df)} ({win_count/len(elite_df)*100:.1f}%)")
        logger.info(f"   PROGRESS: Average accuracy: {elite_df['accuracy'].mean():.1f}%")
        
        # Compare to our original system
        logger.info(f"\n COMPARISON TO ORIGINAL SYSTEM:")
        logger.info("=" * 35)
        logger.info(f"   Original: 0 Miami lineups, 81.3 max projection, 0% cash rate")
        logger.info(f"   Elite: {len(elite_df)} lineups, {best_score:.1f} max actual, {cash_count/len(elite_df)*100:.1f}% cash rate")
        
        improvement = (best_score - 81.3) / 81.3 * 100
        logger.info(f"   PROGRESS: Performance improvement: {improvement:.1f}%")
        
        # Show top performing lineups
        logger.info(f"\n TOP PERFORMING ELITE LINEUPS:")
        logger.info("=" * 35)
        
        top_lineups = elite_df.nlargest(3, 'actual')
        for _, lineup in top_lineups.iterrows():
            logger.info(f"   Lineup {lineup['lineup_id']}: {lineup['actual']:.1f} actual pts ({lineup['ownership']:.1f}% avg own)")
        
        return elite_scores
        
    except Exception as e:
        logger.error(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

def create_player_mapping(projections, actual_results):
    """Create mapping between projection names and actual result names"""
    
    mapping = {}
    
    for _, proj_player in projections.iterrows():
        proj_name = f"{proj_player.get('Nickname', '')} {proj_player.get('Last Name', '')}".strip()
        proj_team = proj_player.get('Team', '')
        proj_id = proj_player.get('Id', '')
        
        # Try to find matching actual result
        for _, actual_player in actual_results.iterrows():
            actual_name = actual_player.get('name', '')
            actual_team = actual_player.get('team', '')
            
            # Match by name and team
            if (proj_name.lower() == actual_name.lower() or 
                actual_name.lower() in proj_name.lower() or
                proj_name.lower() in actual_name.lower()) and proj_team == actual_team:
                
                mapping[proj_id] = {
                    'actual_name': actual_name,
                    'team': actual_team,
                    'fanduel_points': actual_player.get('fanduel_points', 0)
                }
                break
    
    return mapping

def calculate_lineup_actual_score(lineup_row, player_mapping, actual_results):
    """Calculate actual score for an elite lineup"""
    
    total_score = 0.0
    
    # Check each position in the lineup
    positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF.1', 'OF.2', 'UTIL']
    
    for pos in positions:
        if pos in lineup_row and pd.notna(lineup_row[pos]):
            player_id = str(lineup_row[pos])
            
            if player_id in player_mapping:
                actual_points = player_mapping[player_id]['fanduel_points']
                total_score += actual_points
            else:
                # Player not found in mapping, use 0
                total_score += 0.0
    
    return total_score

if __name__ == "__main__":
    validate_elite_vs_actual()
