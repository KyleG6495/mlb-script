#!/usr/bin/env python3
"""
GAME STACK ANALYZER - Identify Today's Blowout Games
Based on August 13th analysis: MIA@CLE (13-4) and ATL@NYM (11-6) were key
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def analyze_todays_games():
    """Analyze today's slate for game stacking opportunities"""
    logger.info("TARGET: ANALYZING TODAY'S GAME STACKING OPPORTUNITIES")
    logger.info("=" * 60)
    
    # Load today's slate
    try:
        slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
        logger.info(f"SUCCESS: Loaded {len(slate)} players from today's slate")
    except Exception as e:
        logger.error(f"ERROR: Error loading slate: {e}")
        return
    
    # Get unique games
    games = slate['Game'].dropna().unique()
    logger.info(f"DATA: Found {len(games)} games today")
    
    game_analysis = []
    
    for game in games:
        game_players = slate[slate['Game'] == game]
        
        # Get teams
        teams = game_players['Team'].unique()
        if len(teams) != 2:
            continue
            
        team1, team2 = teams[0], teams[1]
        
        # Analyze each team
        team1_players = game_players[game_players['Team'] == team1]
        team2_players = game_players[game_players['Team'] == team2]
        
        # Get starting hitters only
        team1_hitters = team1_players[
            (team1_players['Position'] != 'P') & 
            (team1_players['Batting Order'] > 0)
        ]
        team2_hitters = team2_players[
            (team2_players['Position'] != 'P') & 
            (team2_players['Batting Order'] > 0)
        ]
        
        # Calculate team metrics
        team1_avg_fppg = team1_hitters['FPPG'].mean() if len(team1_hitters) > 0 else 0
        team2_avg_fppg = team2_hitters['FPPG'].mean() if len(team2_hitters) > 0 else 0
        
        total_avg_fppg = (team1_avg_fppg + team2_avg_fppg) / 2
        
        # Get stack-able players (3+ from same team)
        team1_stackable = len(team1_hitters)
        team2_stackable = len(team2_hitters)
        
        # Calculate value concentration
        team1_value_players = len(team1_hitters[team1_hitters['Salary'] < 3500])
        team2_value_players = len(team2_hitters[team2_hitters['Salary'] < 3500])
        
        game_info = {
            'game': game,
            'team1': team1,
            'team2': team2,
            'total_avg_fppg': total_avg_fppg,
            'team1_avg_fppg': team1_avg_fppg,
            'team2_avg_fppg': team2_avg_fppg,
            'team1_stackable': team1_stackable,
            'team2_stackable': team2_stackable,
            'team1_value': team1_value_players,
            'team2_value': team2_value_players,
            'total_players': len(game_players)
        }
        
        game_analysis.append(game_info)
    
    # Sort by total average FPPG (proxy for scoring)
    game_analysis.sort(key=lambda x: x['total_avg_fppg'], reverse=True)
    
    # Display results
    logger.info(" TOP GAME STACKING TARGETS (by projected scoring):")
    logger.info("=" * 70)
    
    for i, game in enumerate(game_analysis[:5]):
        logger.info(f"#{i+1} - {game['game']}")
        logger.info(f"  DATA: Total Avg FPPG: {game['total_avg_fppg']:.1f}")
        logger.info(f"   {game['team1']}: {game['team1_avg_fppg']:.1f} avg, {game['team1_stackable']} stackable, {game['team1_value']} value")
        logger.info(f"   {game['team2']}: {game['team2_avg_fppg']:.1f} avg, {game['team2_stackable']} stackable, {game['team2_value']} value")
        logger.info("")
    
    # Identify best stacking teams
    logger.info("TARGET: BEST TEAM STACKING OPPORTUNITIES:")
    logger.info("=" * 50)
    
    all_teams = []
    for game in game_analysis:
        all_teams.append({
            'team': game['team1'],
            'game': game['game'],
            'avg_fppg': game['team1_avg_fppg'],
            'stackable': game['team1_stackable'],
            'value_players': game['team1_value']
        })
        all_teams.append({
            'team': game['team2'],
            'game': game['game'],
            'avg_fppg': game['team2_avg_fppg'],
            'stackable': game['team2_stackable'],
            'value_players': game['team2_value']
        })
    
    # Sort by avg FPPG
    all_teams.sort(key=lambda x: x['avg_fppg'], reverse=True)
    
    for i, team in enumerate(all_teams[:8]):
        if team['stackable'] >= 4:  # Need at least 4 stackable players
            logger.info(f"#{i+1} {team['team']} ({team['game']})")
            logger.info(f"  DATA: Avg FPPG: {team['avg_fppg']:.1f}")
            logger.info(f"   Stackable players: {team['stackable']}")
            logger.info(f"  MONEY: Value plays: {team['value_players']}")
            logger.info("")
    
    return game_analysis

def identify_contrarian_gems():
    """Identify low-salary, high-upside players like Jakob Marsee"""
    logger.info(" IDENTIFYING CONTRARIAN GEMS")
    logger.info("=" * 40)
    
    try:
        slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    except Exception as e:
        logger.error(f"ERROR: Error loading slate: {e}")
        return
    
    # Focus on hitters only
    hitters = slate[
        (slate['Position'] != 'P') & 
        (slate['Batting Order'] > 0)
    ].copy()
    
    # Identify contrarian gems: Low salary + High projection
    contrarian_gems = hitters[
        (hitters['Salary'] <= 3000) & 
        (hitters['FPPG'] >= 12.0)
    ].copy()
    
    if len(contrarian_gems) > 0:
        contrarian_gems = contrarian_gems.nlargest(10, 'FPPG')
        
        logger.info(" TOP CONTRARIAN GEMS ($3K salary, 12 FPPG):")
        for _, player in contrarian_gems.iterrows():
            name = f"{player['Nickname']} {player['Last Name']}"
            logger.info(f"  {name:<20} ({player['Team']}) - ${player['Salary']}, {player['FPPG']:.1f} FPPG")
    
    # Also find mid-range values
    value_plays = hitters[
        (hitters['Salary'] <= 3500) & 
        (hitters['FPPG'] >= 15.0)
    ].copy()
    
    if len(value_plays) > 0:
        value_plays = value_plays.nlargest(10, 'FPPG')
        
        logger.info("")
        logger.info("MONEY: TOP VALUE PLAYS ($3.5K salary, 15 FPPG):")
        for _, player in value_plays.iterrows():
            name = f"{player['Nickname']} {player['Last Name']}"
            logger.info(f"  {name:<20} ({player['Team']}) - ${player['Salary']}, {player['FPPG']:.1f} FPPG")

def analyze_pitcher_strategy():
    """Analyze pitcher salary allocation strategy"""
    logger.info("BASEBALL: PITCHER SALARY ALLOCATION ANALYSIS")
    logger.info("=" * 45)
    
    try:
        slate = pd.read_csv("../fd_current_slate/fd_slate_today.csv")
    except Exception as e:
        logger.error(f"ERROR: Error loading slate: {e}")
        return
    
    # Get probable pitchers only
    pitchers = slate[
        (slate['Position'] == 'P') & 
        (slate['Probable Pitcher'] == 'Yes')
    ].copy()
    
    if len(pitchers) == 0:
        logger.warning("WARNING: No probable pitchers found")
        return
    
    # Analyze by salary tiers
    studs = pitchers[pitchers['Salary'] >= 10000]
    mid_tier = pitchers[(pitchers['Salary'] >= 7000) & (pitchers['Salary'] < 10000)]
    value = pitchers[pitchers['Salary'] < 7000]
    
    logger.info("TARGET: PITCHER TIERS:")
    logger.info(f"   Studs ($10K+): {len(studs)} pitchers")
    if len(studs) > 0:
        top_stud = studs.nlargest(1, 'FPPG').iloc[0]
        logger.info(f"    Top: {top_stud['Nickname']} {top_stud['Last Name']} - ${top_stud['Salary']}, {top_stud['FPPG']:.1f} FPPG")
    
    logger.info(f"  BASEBALL: Mid-tier ($7K-$10K): {len(mid_tier)} pitchers")
    if len(mid_tier) > 0:
        top_mid = mid_tier.nlargest(1, 'FPPG').iloc[0]
        logger.info(f"    Top: {top_mid['Nickname']} {top_mid['Last Name']} - ${top_mid['Salary']}, {top_mid['FPPG']:.1f} FPPG")
    
    logger.info(f"  MONEY: Value (<$7K): {len(value)} pitchers")
    if len(value) > 0:
        top_value = value.nlargest(1, 'FPPG').iloc[0]
        logger.info(f"    Top: {top_value['Nickname']} {top_value['Last Name']} - ${top_value['Salary']}, {top_value['FPPG']:.1f} FPPG")
    
    # Calculate salary savings strategy
    logger.info("")
    logger.info("TIP: SALARY ALLOCATION STRATEGY:")
    if len(mid_tier) > 0 and len(studs) > 0:
        best_mid = mid_tier.nlargest(1, 'FPPG').iloc[0]
        best_stud = studs.nlargest(1, 'FPPG').iloc[0]
        savings = best_stud['Salary'] - best_mid['Salary']
        projection_loss = best_stud['FPPG'] - best_mid['FPPG']
        
        logger.info(f"  Using {best_mid['Nickname']} {best_mid['Last Name']} vs {best_stud['Nickname']} {best_stud['Last Name']}:")
        logger.info(f"  MONEY: Salary savings: ${savings}")
        logger.info(f"   Projection loss: {projection_loss:.1f} FPPG")
        logger.info(f"  TARGET: Strategy: Use savings for {savings // 1000:.0f}K+ hitter upgrade")

def main():
    """Main analysis function"""
    logger.info("TARGET: GAME STACK & CONTRARIAN ANALYSIS")
    logger.info("Identifying today's blowout games and value plays")
    logger.info("=" * 60)
    
    # Analyze games
    analyze_todays_games()
    logger.info("")
    
    # Find contrarian gems
    identify_contrarian_gems()
    logger.info("")
    
    # Analyze pitchers
    analyze_pitcher_strategy()
    
    logger.info("")
    logger.info("SUCCESS: GAME STACK ANALYSIS COMPLETE!")
    logger.info("Use this data to build tournament stacks targeting blowout games")

if __name__ == "__main__":
    main()
