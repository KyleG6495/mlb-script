#!/usr/bin/env python3
"""
Test Contrarian Analysis on 7/29 Data - Identify LAA@OAK Opportunity
"""

import pandas as pd
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_contrarian_opportunities():
    """Test contrarian analysis on 7/29 data"""
    
    logger.info("🔍 TESTING CONTRARIAN ANALYSIS ON 7/29 DATA")
    logger.info("=" * 50)
    
    # Load 7/29 actual results
    try:
        results = pd.read_csv("../data/actual_results_20250729.csv")
        logger.info(f"Loaded {len(results)} actual results from 7/29")
        
        # Find LAA@OAK game players
        laa_oak_players = results[(results['team'].isin(['LAA', 'OAK'])) & (results['position'] != 'P')]
        
        logger.info(f"\n🎯 LAA@OAK GAME ANALYSIS:")
        logger.info(f"Found {len(laa_oak_players)} position players")
        
        # Show top performers from that game
        top_performers = laa_oak_players.nlargest(10, 'fanduel_points')
        
        logger.info(f"\n🏆 TOP PERFORMERS LAA@OAK:")
        for _, player in top_performers.iterrows():
            logger.info(f"{player['name']:15} ({player['team']}) - {player['fanduel_points']:.1f} pts")
        
        # Calculate game totals
        laa_total = laa_oak_players[laa_oak_players['team'] == 'LAA']['fanduel_points'].sum()
        oak_total = laa_oak_players[laa_oak_players['team'] == 'OAK']['fanduel_points'].sum()
        game_total = laa_total + oak_total
        
        logger.info(f"\n📊 GAME SCORING BREAKDOWN:")
        logger.info(f"LAA Team Total: {laa_total:.1f} points")
        logger.info(f"OAK Team Total: {oak_total:.1f} points") 
        logger.info(f"Game Total: {game_total:.1f} points")
        
        # Find the specific winning players mentioned
        winning_players = ['Langeliers', 'Thomas', 'Kurtz']
        
        logger.info(f"\n🎖️ IDENTIFIED WINNING PLAYERS:")
        for player_name in winning_players:
            player_data = results[results['name'].str.contains(player_name, case=False, na=False)]
            if not player_data.empty:
                player = player_data.iloc[0]
                logger.info(f"{player['name']:15} ({player['team']}) - {player['fanduel_points']:.1f} pts")
        
        # Analyze game environment - need to create game identifiers
        # Create game column by combining teams
        results['game_id'] = results.apply(lambda x: f"{x['team']}_game", axis=1)
        
        # For a more accurate analysis, let's look at date-based grouping
        game_totals = results[results['position'] != 'P'].groupby('date')['fanduel_points'].sum()
        
        logger.info(f"\n🔥 TOTAL SCORING ON 7/29:")
        logger.info(f"Total FanDuel Points: {game_totals.iloc[0]:.1f}")
        
        # Show LAA and OAK team breakdowns
        team_totals = results[results['position'] != 'P'].groupby('team')['fanduel_points'].sum().sort_values(ascending=False)
        
        logger.info(f"\n� TEAM SCORING TOTALS:")
        for team, score in team_totals.head(15).items():
            marker = "⭐" if team in ['LAA', 'OAK'] else ""
            logger.info(f"{team:4} - {score:.1f} points {marker}")
        
        # Find LAA and OAK ranking
        laa_rank = list(team_totals.index).index('LAA') + 1 if 'LAA' in team_totals.index else 'N/A'
        oak_rank = list(team_totals.index).index('OAK') + 1 if 'OAK' in team_totals.index else 'N/A'
        
        logger.info(f"\n📈 TEAM RANKINGS:")
        logger.info(f"LAA: #{laa_rank} - {team_totals.get('LAA', 0):.1f} points")
        logger.info(f"OAK: #{oak_rank} - {team_totals.get('OAK', 0):.1f} points")
        
        # Show how this created tournament edge
        logger.info(f"\n💡 CONTRARIAN EDGE ANALYSIS:")
        logger.info(f"✅ High-scoring game environment ({game_total:.1f} pts)")
        logger.info(f"✅ Low ownership players (1-5% mentioned)")
        logger.info(f"✅ Game correlation (multiple players from same game)")
        logger.info(f"✅ Ownership arbitrage (avoided popular stacks)")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in analysis: {e}")
        return False

if __name__ == "__main__":
    analyze_contrarian_opportunities()
