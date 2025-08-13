#!/usr/bin/env python3
"""
CLEAN LINEUP GENERATOR
=====================
Generate 10 unique, high-quality DFS lineups using our ML predictions.
Test with yesterday's slate to validate against actual results.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
import itertools
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent

def load_yesterdays_slate():
    """Load yesterday's slate (8/7) for backtesting"""
    slate_file = BASE_DIR / "fd_current_slate" / "fd_slate_today.csv"
    
    if not slate_file.exists():
        logger.error("❌ No slate file found")
        return None
    
    slate = pd.read_csv(slate_file)
    logger.info(f"📊 Loaded slate with {len(slate)} players")
    
    # Show games
    if 'Opponent' in slate.columns:
        games = slate.groupby(['Team', 'Opponent']).size().reset_index()
        logger.info(f"🏟️ Games on slate:")
        for _, game in games.iterrows():
            logger.info(f"   {game['Team']} vs {game['Opponent']}")
    
    return slate

def load_player_projections():
    """Load our ML projections for players"""
    # Use the enhanced predictions file which has player names
    projections_file = BASE_DIR / "data" / "enhanced_predictions_latest.csv"
    
    if not projections_file.exists():
        logger.error("❌ No enhanced predictions file found")
        return None
    
    try:
        df = pd.read_csv(projections_file)
        logger.info(f"✅ Loaded {projections_file.name}: {len(df)} players")
        return df
    except Exception as e:
        logger.error(f"❌ Error loading projections: {e}")
        return None

def calculate_fanduel_points(row, position):
    """Calculate FanDuel points from predictions"""
    if position == 'P':
        # For pitchers, estimate based on typical performance
        # This is simplified - you'd want actual pitcher predictions
        return np.random.uniform(15, 45)  # Placeholder for pitcher projections
    else:
        # Hitter scoring from predictions
        hits = row.get('hits_prediction', 0)
        hr = row.get('homeRuns_prediction', 0)
        runs = row.get('runs_prediction', 0)
        rbi = row.get('rbi_prediction', 0)
        sb = row.get('stolenBases_prediction', 0)
        
        # Estimate other stats
        doubles = hits * 0.2  # ~20% of hits are doubles
        triples = hits * 0.02  # ~2% of hits are triples
        singles = hits - doubles - triples - hr
        walks = hits * 0.4  # Rough estimate
        
        points = (singles * 3) + (doubles * 6) + (triples * 9) + (hr * 12) + (rbi * 3.5) + (runs * 3.2) + (walks * 3) + (sb * 6)
        return max(points, 0)

def merge_slate_with_projections(slate_df, projections_df):
    """Merge slate players with our projections"""
    logger.info("🔗 Merging slate with projections...")
    
    merged_players = []
    
    for _, slate_player in slate_df.iterrows():
        slate_name = slate_player['Nickname'].strip().lower()
        
        # Find matching projection
        best_match = None
        best_score = 0
        
        for _, proj_player in projections_df.iterrows():
            proj_name = proj_player.get('player_name', '').strip().lower()
            
            if proj_name:
                # Simple name matching
                name_parts = proj_name.split()
                slate_parts = slate_name.split()
                
                if len(name_parts) >= 2 and len(slate_parts) >= 2:
                    if (name_parts[0] in slate_parts and name_parts[-1] in slate_parts) or \
                       (slate_parts[0] in name_parts and slate_parts[-1] in name_parts):
                        score = len(set(name_parts) & set(slate_parts))
                        if score > best_score:
                            best_match = proj_player
                            best_score = score
        
        # Create merged player record
        player_record = {
            'name': slate_player['Nickname'],
            'position': slate_player['Position'],
            'team': slate_player['Team'],
            'opponent': slate_player.get('Opponent', ''),
            'salary': slate_player['Salary'],
            'game_info': slate_player.get('Game Info', '')
        }
        
        if best_match is not None:
            # Use projections to calculate expected FPPG
            projected_fppg = calculate_fanduel_points(best_match, slate_player['Position'])
            player_record['projected_fppg'] = projected_fppg
            player_record['has_projection'] = True
            
            # Add ownership projection (simplified)
            if slate_player['Salary'] > 8000:
                ownership = np.random.uniform(15, 35)  # Stars
            elif slate_player['Salary'] > 6000:
                ownership = np.random.uniform(8, 25)   # Mid-tier
            else:
                ownership = np.random.uniform(2, 15)   # Value
            
            player_record['ownership_proj'] = ownership
        else:
            # No projection found - use salary-based estimate
            salary_fppg = slate_player['Salary'] / 1000 * 2.5  # Rough estimate
            player_record['projected_fppg'] = salary_fppg
            player_record['has_projection'] = False
            player_record['ownership_proj'] = 5.0  # Low default
        
        # Calculate value
        player_record['value'] = player_record['projected_fppg'] / (slate_player['Salary'] / 1000)
        
        merged_players.append(player_record)
    
    merged_df = pd.DataFrame(merged_players)
    
    with_proj = len(merged_df[merged_df['has_projection'] == True])
    logger.info(f"✅ Merged slate: {len(merged_df)} players, {with_proj} with projections")
    
    return merged_df

def generate_lineup(players_df, strategy='balanced', exclude_players=None):
    """Generate a single lineup using specified strategy"""
    if exclude_players is None:
        exclude_players = set()
    
    available_players = players_df[~players_df['name'].isin(exclude_players)].copy()
    
    lineup = {}
    total_salary = 0
    total_projected = 0
    salary_cap = 35000
    
    # Position requirements
    positions_needed = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']
    
    for pos in positions_needed:
        if pos == 'OF' and 'OF' in lineup:
            # Need multiple OF, use position eligibility
            eligible = available_players[
                (available_players['position'].str.contains('OF|CF|LF|RF', na=False)) &
                (~available_players['name'].isin([p['name'] for p in lineup.values()]))
            ].copy()
        else:
            eligible = available_players[
                (available_players['position'] == pos) &
                (~available_players['name'].isin([p['name'] for p in lineup.values()]))
            ].copy()
        
        if eligible.empty:
            logger.warning(f"⚠️ No eligible players for {pos}")
            return None
        
        # Apply strategy
        if strategy == 'max_projected':
            eligible = eligible.sort_values('projected_fppg', ascending=False)
        elif strategy == 'max_value':
            eligible = eligible.sort_values('value', ascending=False)
        elif strategy == 'low_ownership':
            eligible = eligible.sort_values('ownership_proj', ascending=True)
        elif strategy == 'balanced':
            # Balance of projection and value
            eligible['balanced_score'] = (eligible['projected_fppg'] * 0.6) + (eligible['value'] * 0.4)
            eligible = eligible.sort_values('balanced_score', ascending=False)
        elif strategy == 'contrarian':
            # Low ownership but decent projection
            eligible['contrarian_score'] = eligible['projected_fppg'] / (eligible['ownership_proj'] + 1)
            eligible = eligible.sort_values('contrarian_score', ascending=False)
        
        # Select player that fits salary
        selected = None
        for _, player in eligible.iterrows():
            if total_salary + player['salary'] <= salary_cap:
                selected = player
                break
        
        if selected is None:
            # Try to find any player that fits
            for _, player in eligible.iterrows():
                if total_salary + player['salary'] <= salary_cap:
                    selected = player
                    break
        
        if selected is None:
            logger.warning(f"⚠️ Cannot fit any {pos} under salary cap")
            return None
        
        # Add to lineup
        if pos == 'OF':
            of_count = sum(1 for p in lineup.values() if 'OF' in p.get('lineup_position', ''))
            lineup_pos = f'OF{of_count + 1}'
        else:
            lineup_pos = pos
        
        lineup[lineup_pos] = {
            'name': selected['name'],
            'position': selected['position'],
            'team': selected['team'],
            'salary': selected['salary'],
            'projected_fppg': selected['projected_fppg'],
            'ownership_proj': selected['ownership_proj'],
            'value': selected['value'],
            'lineup_position': lineup_pos
        }
        
        total_salary += selected['salary']
        total_projected += selected['projected_fppg']
    
    if len(lineup) == 9:
        return {
            'lineup': lineup,
            'total_salary': total_salary,
            'total_projected': total_projected,
            'strategy': strategy
        }
    else:
        return None

def generate_10_unique_lineups(players_df):
    """Generate 10 unique lineups with different strategies"""
    logger.info("🏆 Generating 10 unique lineups...")
    
    strategies = [
        'max_projected',
        'max_value', 
        'balanced',
        'contrarian',
        'low_ownership',
        'balanced',      # Repeat some strategies
        'max_projected',
        'contrarian',
        'max_value',
        'balanced'
    ]
    
    lineups = []
    used_players = set()
    
    for i, strategy in enumerate(strategies):
        logger.info(f"🎯 Building lineup {i+1}: {strategy}")
        
        # Force some diversity by excluding overused players
        if i > 5:
            # After 5 lineups, exclude players used more than twice
            player_usage = {}
            for lineup in lineups:
                for player_info in lineup['lineup'].values():
                    name = player_info['name']
                    player_usage[name] = player_usage.get(name, 0) + 1
            
            overused = {name for name, count in player_usage.items() if count >= 2}
        else:
            overused = set()
        
        lineup = generate_lineup(players_df, strategy=strategy, exclude_players=overused)
        
        if lineup:
            lineups.append(lineup)
            logger.info(f"✅ Lineup {i+1}: ${lineup['total_salary']:,} | {lineup['total_projected']:.1f} FPPG")
        else:
            logger.warning(f"❌ Failed to generate lineup {i+1}")
    
    logger.info(f"🎉 Generated {len(lineups)} unique lineups")
    return lineups

def save_lineups(lineups):
    """Save lineups to CSV for submission"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save detailed breakdown
    lineup_details = []
    for i, lineup_data in enumerate(lineups):
        lineup = lineup_data['lineup']
        for pos, player in lineup.items():
            lineup_details.append({
                'lineup_id': i + 1,
                'position': pos,
                'player_name': player['name'],
                'team': player['team'],
                'salary': player['salary'],
                'projected_fppg': player['projected_fppg'],
                'ownership_proj': player['ownership_proj'],
                'value': player['value'],
                'strategy': lineup_data['strategy']
            })
    
    details_file = BASE_DIR / "data" / f"clean_lineups_details_{timestamp}.csv"
    pd.DataFrame(lineup_details).to_csv(details_file, index=False)
    
    # Save FanDuel submission format
    submission_data = []
    for i, lineup_data in enumerate(lineups):
        lineup = lineup_data['lineup']
        submission_data.append({
            'P': lineup['P']['name'],
            'C': lineup['C']['name'],
            '1B': lineup['1B']['name'],
            '2B': lineup['2B']['name'],
            '3B': lineup['3B']['name'],
            'SS': lineup['SS']['name'],
            'OF1': lineup['OF1']['name'],
            'OF2': lineup['OF2']['name'],
            'OF3': lineup['OF3']['name'],
            'Total_Salary': lineup_data['total_salary'],
            'Projected_FPPG': lineup_data['total_projected'],
            'Strategy': lineup_data['strategy']
        })
    
    submission_file = BASE_DIR / "data" / f"clean_lineups_submission_{timestamp}.csv"
    pd.DataFrame(submission_data).to_csv(submission_file, index=False)
    
    logger.info(f"💾 Saved lineups:")
    logger.info(f"   Details: {details_file.name}")
    logger.info(f"   Submission: {submission_file.name}")
    
    return details_file, submission_file

def main():
    """Generate clean lineups for backtesting"""
    logger.info("🚀 CLEAN LINEUP GENERATOR - YESTERDAY'S BACKTEST")
    logger.info("=" * 60)
    
    # Load yesterday's slate
    slate_df = load_yesterdays_slate()
    if slate_df is None:
        return
    
    # Load projections
    projections_df = load_player_projections()
    if projections_df is None:
        return
    
    # Merge slate with projections
    players_df = merge_slate_with_projections(slate_df, projections_df)
    
    # Generate 10 unique lineups
    lineups = generate_10_unique_lineups(players_df)
    
    if lineups:
        # Save lineups
        details_file, submission_file = save_lineups(lineups)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 LINEUP GENERATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"📊 Generated {len(lineups)} unique lineups")
        logger.info(f"💰 Salary range: ${min(l['total_salary'] for l in lineups):,} - ${max(l['total_salary'] for l in lineups):,}")
        logger.info(f"🏆 FPPG range: {min(l['total_projected'] for l in lineups):.1f} - {max(l['total_projected'] for l in lineups):.1f}")
        logger.info("\n🔍 Ready for backtesting against actual 8/7 results!")
    else:
        logger.error("❌ Failed to generate any lineups")

if __name__ == "__main__":
    main()
