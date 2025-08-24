#!/usr/bin/env python3
"""
Advanced Contrarian Lineup Builder - Target 230+ Point Range
Based on analysis of 7/29 winners and ownership patterns
"""

import pandas as pd
import numpy as np
import logging
import itertools
from datetime import datetime
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AdvancedContrarianBuilder:
    def __init__(self):
        self.players_df = None
        self.ownership_df = None
        self.optimal_lineups = []
        
    def load_current_data(self):
        """Load the most recent data available"""
        try:
            # Load enhanced projections (most recent)
            proj_files = [f for f in os.listdir("../data") if f.startswith("enhanced_projections_")]
            if proj_files:
                latest_proj = sorted(proj_files)[-1]
                self.players_df = pd.read_csv(f"../data/{latest_proj}")
                logger.info(f"✅ Loaded {len(self.players_df)} players from {latest_proj}")
            
            # Load ownership (most recent)
            own_files = [f for f in os.listdir("../data") if f.startswith("advanced_ownership_projections_")]
            if own_files:
                latest_own = sorted(own_files)[-1]
                ownership_raw = pd.read_csv(f"../data/{latest_own}")
                
                # Create ownership lookup
                ownership_lookup = {}
                for _, row in ownership_raw.iterrows():
                    player_name = row['player_name']
                    ownership_lookup[player_name] = row['ownership'] * 100 if row['ownership'] < 1 else row['ownership']
                
                # Merge ownership into players
                self.players_df['ownership'] = 0.0
                for idx, player in self.players_df.iterrows():
                    player_name = f"{player.get('First Name', '')} {player.get('Last Name', '')}".strip()
                    nickname = player.get('Nickname', '')
                    
                    # Try multiple name matching strategies
                    for lookup_name, ownership in ownership_lookup.items():
                        if (player_name.lower() in lookup_name.lower() or 
                            lookup_name.lower() in player_name.lower() or
                            nickname.lower() in lookup_name.lower()):
                            self.players_df.at[idx, 'ownership'] = ownership
                            break
                    
                    # Default ownership for unmatched players
                    if self.players_df.at[idx, 'ownership'] == 0.0:
                        self.players_df.at[idx, 'ownership'] = 8.0  # Medium ownership default
                
                logger.info(f"✅ Merged ownership data from {latest_own}")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading data: {e}")
            return False
    
    def identify_contrarian_opportunities(self):
        """Find specific contrarian opportunities targeting 230+ points"""
        
        contrarian_spots = []
        
        # Filter to position players only
        hitters = self.players_df[self.players_df['Position'] != 'P'].copy()
        
        logger.info(f"\n🎯 ANALYZING {len(hitters)} POSITION PLAYERS FOR CONTRARIAN EDGE")
        
        # Define contrarian criteria based on winning analysis
        for _, player in hitters.iterrows():
            
            # Contrarian Profile: High projection + Low ownership
            projection = player.get('enhanced_fppg', player.get('FPPG', 0))
            ownership = player.get('ownership', 10.0)
            salary = player.get('Salary', 0)
            
            # Calculate value metrics
            value_per_dollar = projection / salary * 1000 if salary > 0 else 0
            leverage_score = projection * (15 - ownership) / 15  # Higher score for lower ownership
            
            # Contrarian thresholds (based on 230+ analysis)
            if (projection >= 12.0 and ownership <= 8.0 and salary >= 6000):  # High-end contrarian
                contrarian_spots.append({
                    'name': player.get('Nickname', ''),
                    'team': player.get('Team', ''),
                    'position': player.get('Position', ''),
                    'salary': salary,
                    'projection': projection,
                    'ownership': ownership,
                    'value': value_per_dollar,
                    'leverage': leverage_score,
                    'tier': 'ELITE_CONTRARIAN'
                })
            elif (projection >= 10.0 and ownership <= 5.0):  # Ultra-low owned
                contrarian_spots.append({
                    'name': player.get('Nickname', ''),
                    'team': player.get('Team', ''),
                    'position': player.get('Position', ''),
                    'salary': salary,
                    'projection': projection,
                    'ownership': ownership,
                    'value': value_per_dollar,
                    'leverage': leverage_score,
                    'tier': 'ULTRA_CONTRARIAN'
                })
        
        # Sort by leverage score
        contrarian_spots = sorted(contrarian_spots, key=lambda x: x['leverage'], reverse=True)
        
        logger.info(f"\n🏆 FOUND {len(contrarian_spots)} CONTRARIAN OPPORTUNITIES:")
        for i, spot in enumerate(contrarian_spots[:15]):
            logger.info(f"{i+1:2}. {spot['name']:15} ({spot['team']}) - {spot['projection']:.1f}pts, {spot['ownership']:.1f}% own, ${spot['salary']:,}")
        
        return contrarian_spots
    
    def build_contrarian_lineups(self, contrarian_spots, num_lineups=10):
        """Build lineups targeting 230+ points using contrarian insights"""
        
        logger.info(f"\n🚀 BUILDING {num_lineups} CONTRARIAN LINEUPS TARGETING 230+ POINTS")
        
        # Get all position players
        hitters = self.players_df[self.players_df['Position'] != 'P'].copy()
        pitchers = self.players_df[self.players_df['Position'] == 'P'].copy()
        
        lineups = []
        
        for lineup_num in range(num_lineups):
            
            try:
                lineup = []
                total_salary = 0
                total_projection = 0
                total_ownership = 0
                
                # 1. Start with contrarian cornerstone (top contrarian player)
                if contrarian_spots:
                    cornerstone = contrarian_spots[lineup_num % len(contrarian_spots)]
                    cornerstone_player = hitters[
                        (hitters['Nickname'] == cornerstone['name']) & 
                        (hitters['Team'] == cornerstone['team'])
                    ]
                    
                    if not cornerstone_player.empty:
                        player = cornerstone_player.iloc[0]
                        lineup.append({
                            'name': player['Nickname'],
                            'position': player['Position'],
                            'team': player['Team'],
                            'salary': player['Salary'],
                            'projection': player.get('enhanced_fppg', player['FPPG']),
                            'ownership': player.get('ownership', 5.0),
                            'role': 'CONTRARIAN_CORNERSTONE'
                        })
                        total_salary += player['Salary']
                        total_projection += player.get('enhanced_fppg', player['FPPG'])
                        total_ownership += player.get('ownership', 5.0)
                
                # 2. Add elite pitcher (salary permitting)
                remaining_salary = 50000 - total_salary
                affordable_pitchers = pitchers[pitchers['Salary'] <= remaining_salary]
                
                if not affordable_pitchers.empty:
                    # Prefer high projection, reasonable ownership
                    best_pitcher = affordable_pitchers.loc[affordable_pitchers['enhanced_fppg'].idxmax()]
                    lineup.append({
                        'name': best_pitcher['Nickname'],
                        'position': best_pitcher['Position'],
                        'team': best_pitcher['Team'],
                        'salary': best_pitcher['Salary'],
                        'projection': best_pitcher.get('enhanced_fppg', best_pitcher['FPPG']),
                        'ownership': best_pitcher.get('ownership', 15.0),
                        'role': 'ACE_PITCHER'
                    })
                    total_salary += best_pitcher['Salary']
                    total_projection += best_pitcher.get('enhanced_fppg', best_pitcher['FPPG'])
                    total_ownership += best_pitcher.get('ownership', 15.0)
                
                # 3. Fill remaining spots with value/contrarian mix
                positions_needed = ['C', 'SS', 'OF', 'OF', 'OF', '1B', '2B', '3B']  # 8 position players total
                used_players = [p['name'] for p in lineup]
                
                for pos in positions_needed:
                    if len(lineup) >= 9:  # 1 pitcher + 8 position players = 9 total
                        break
                    
                    remaining_salary = 50000 - total_salary
                    available_players = hitters[
                        (hitters['Position'].str.contains(pos)) &
                        (~hitters['Nickname'].isin(used_players)) &
                        (hitters['Salary'] <= remaining_salary)
                    ]
                    
                    if not available_players.empty:
                        # Bias toward lower ownership when possible
                        available_players['selection_score'] = (
                            available_players.get('enhanced_fppg', available_players['FPPG']) * 2 +
                            (15 - available_players.get('ownership', 10)) * 0.5  # Bonus for low ownership
                        )
                        
                        best_player = available_players.loc[available_players['selection_score'].idxmax()]
                        lineup.append({
                            'name': best_player['Nickname'],
                            'position': best_player['Position'],
                            'team': best_player['Team'],
                            'salary': best_player['Salary'],
                            'projection': best_player.get('enhanced_fppg', best_player['FPPG']),
                            'ownership': best_player.get('ownership', 8.0),
                            'role': 'VALUE_PLAY'
                        })
                        total_salary += best_player['Salary']
                        total_projection += best_player.get('enhanced_fppg', best_player['FPPG'])
                        total_ownership += best_player.get('ownership', 8.0)
                        used_players.append(best_player['Nickname'])
                
                # Only keep lineups that meet basic requirements
                if len(lineup) == 9 and total_salary <= 50000 and total_projection >= 45:
                    lineup_summary = {
                        'lineup_id': f"CONTRARIAN_{lineup_num+1}",
                        'players': lineup,
                        'total_salary': total_salary,
                        'total_projection': total_projection,
                        'avg_ownership': total_ownership / len(lineup),
                        'contrarian_score': total_projection * (100 - total_ownership/len(lineup)) / 100
                    }
                    lineups.append(lineup_summary)
                    
                    logger.info(f"✅ Built lineup {lineup_num+1}: {total_projection:.1f}pts, {total_ownership/len(lineup):.1f}% avg own")
                
            except Exception as e:
                logger.warning(f"❌ Failed to build lineup {lineup_num+1}: {e}")
                continue
        
        self.optimal_lineups = lineups
        return lineups
    
    def export_contrarian_lineups(self):
        """Export contrarian lineups in FanDuel format"""
        
        if not self.optimal_lineups:
            logger.warning("No lineups to export")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"../data/CONTRARIAN_TOURNAMENT_LINEUPS_{timestamp}.csv"
        
        export_data = []
        
        for lineup in self.optimal_lineups:
            row = {
                'P': '',
                'C/1B': '',
                'SS': '',
                'OF': '',
                'OF ': '',
                'OF  ': '', 
                '1B': '',
                '2B': '',
                '3B': ''
            }
            
            # Map players to FanDuel positions
            position_map = {
                'P': 'P',
                'C': 'C/1B',
                'SS': 'SS', 
                '1B': '1B',
                '2B': '2B',
                '3B': '3B'
            }
            
            of_count = 0
            of_positions = ['OF', 'OF ', 'OF  ']
            
            for player in lineup['players']:
                pos = player['position']
                name = player['name']
                
                if pos == 'OF':
                    if of_count < 3:
                        row[of_positions[of_count]] = name
                        of_count += 1
                elif pos in position_map:
                    row[position_map[pos]] = name
            
            export_data.append(row)
        
        export_df = pd.DataFrame(export_data)
        export_df.to_csv(filename, index=False)
        
        logger.info(f"📁 EXPORTED {len(self.optimal_lineups)} CONTRARIAN LINEUPS TO: {filename}")
        
        # Show summary
        logger.info(f"\n📊 CONTRARIAN LINEUP SUMMARY:")
        for lineup in self.optimal_lineups:
            logger.info(f"{lineup['lineup_id']:20} | {lineup['total_projection']:6.1f}pts | {lineup['avg_ownership']:5.1f}% avg own | Contrarian Score: {lineup['contrarian_score']:.1f}")

def main():
    logger.info("🏆 ADVANCED CONTRARIAN LINEUP BUILDER - TARGETING 230+ POINTS")
    logger.info("=" * 70)
    
    builder = AdvancedContrarianBuilder()
    
    # Load data
    if not builder.load_current_data():
        logger.error("Failed to load data")
        return
    
    # Find contrarian opportunities
    contrarian_spots = builder.identify_contrarian_opportunities()
    
    # Build lineups
    lineups = builder.build_contrarian_lineups(contrarian_spots, num_lineups=15)
    
    # Export results
    builder.export_contrarian_lineups()
    
    logger.info(f"\n🎯 CONTRARIAN STRATEGY COMPLETE!")
    logger.info(f"Generated {len(lineups)} lineups targeting tournament wins")
    logger.info(f"Focus: Low ownership + High upside = 230+ point potential")

if __name__ == "__main__":
    main()
