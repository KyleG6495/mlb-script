#!/usr/bin/env python3
"""
Quick Team Performance Check - NYM and ATH last night
"""

import pandas as pd
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_team_performance():
    """Check how NYM and ATH performed last night"""
    
    try:
        # Load actual results
        results = pd.read_csv("../data/actual_results_latest.csv")
        logger.info(f"Loaded {len(results)} player performances")
        
        # Filter for position players only
        hitters = results[results['position'] != 'P']
        
        # Calculate team totals
        team_totals = hitters.groupby('team')['fanduel_points'].sum().sort_values(ascending=False)
        
        logger.info(f"\n🏆 TOP TEAM PERFORMANCES LAST NIGHT:")
        for i, (team, total) in enumerate(team_totals.head(10).items(), 1):
            marker = "⭐" if team in ['NYM', 'ATH'] else ""
            logger.info(f"{i:2}. {team} - {total:.1f} points {marker}")
        
        # Specific NYM and ATH analysis
        if 'NYM' in team_totals.index:
            nym_rank = list(team_totals.index).index('NYM') + 1
            nym_total = team_totals['NYM']
            logger.info(f"\n📊 NYM PERFORMANCE:")
            logger.info(f"Rank: #{nym_rank} of {len(team_totals)} teams")
            logger.info(f"Total: {nym_total:.1f} points")
            
            # Show top NYM players
            nym_players = hitters[hitters['team'] == 'NYM'].nlargest(5, 'fanduel_points')
            logger.info(f"Top NYM Players:")
            for _, player in nym_players.iterrows():
                logger.info(f"  {player['name']:20} - {player['fanduel_points']:.1f} pts")
        
        if 'ATH' in team_totals.index:
            ath_rank = list(team_totals.index).index('ATH') + 1
            ath_total = team_totals['ATH']
            logger.info(f"\n📊 ATH PERFORMANCE:")
            logger.info(f"Rank: #{ath_rank} of {len(team_totals)} teams")
            logger.info(f"Total: {ath_total:.1f} points")
            
            # Show top ATH players
            ath_players = hitters[hitters['team'] == 'ATH'].nlargest(5, 'fanduel_points')
            logger.info(f"Top ATH Players:")
            for _, player in ath_players.iterrows():
                logger.info(f"  {player['name']:20} - {player['fanduel_points']:.1f} pts")
        
        # Check if they were good stack candidates
        logger.info(f"\n💡 STACK ANALYSIS:")
        if 'NYM' in team_totals.index and 'ATH' in team_totals.index:
            combined_rank_avg = (nym_rank + ath_rank) / 2
            logger.info(f"NYM + ATH Average Rank: {combined_rank_avg:.1f}")
            
            if nym_rank <= 10 or ath_rank <= 10:
                logger.info(f"✅ At least one team was top-10 - decent stack opportunity")
            else:
                logger.info(f"❌ Neither team was top-10 - poor stack night")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {e}")
        return False

if __name__ == "__main__":
    check_team_performance()
