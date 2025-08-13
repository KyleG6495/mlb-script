#!/usr/bin/env python3
"""
PROPER VALIDATION REPORT
========================
Shows actual fantasy points vs projections + prop bet validation
"""

import pandas as pd
import numpy as np
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_fanduel_points(row):
    """Calculate FanDuel points from actual stats"""
    if row['position'] == 'P':
        # Pitcher scoring
        points = (
            row.get('innings_pitched', 0) * 3 +  # 3 pts per IP
            row.get('wins', 0) * 6 +             # 6 pts per win
            row.get('strikeouts', 0) * 3 -       # 3 pts per K
            row.get('hits_allowed', 0) * 0.6 -   # -0.6 per hit
            row.get('earned_runs', 0) * 3        # -3 per ER
        )
    else:
        # Hitter scoring
        points = (
            row.get('hits', 0) * 3 +             # 3 pts per hit
            row.get('runs', 0) * 3.2 +           # 3.2 pts per run
            row.get('rbis', 0) * 3.5 +           # 3.5 pts per RBI
            row.get('home_runs', 0) * 10 +       # 10 pts per HR
            row.get('stolen_bases', 0) * 6 +     # 6 pts per SB
            row.get('walks', 0) * 3 +            # 3 pts per walk
            row.get('doubles', 0) * 6 +          # 6 pts per 2B  
            row.get('triples', 0) * 12           # 12 pts per 3B
        )
    return max(0, points)

def load_validation_data():
    """Load our lineups and actual results"""
    
    # Load our prop decisions
    try:
        props_df = pd.read_csv("../data/prop_summary_20250808_101556.csv")
        logger.info(f"✅ Loaded {len(props_df)} prop decisions")
    except:
        props_df = None
        logger.warning("❌ No prop decisions found")
    
    # Load our generated lineups
    try:
        lineups_df = pd.read_csv("../data/prop_based_lineups_20250808_101556.csv")
        logger.info(f"✅ Loaded {len(lineups_df)} lineups")
    except:
        logger.error("❌ No prop-based lineups found")
        return None, None, None
    
    # Load actual results from 8/7
    try:
        actual_df = pd.read_csv("../data/actual_results_20250807.csv")
        actual_df['actual_fppg'] = actual_df.apply(calculate_fanduel_points, axis=1)
        logger.info(f"✅ Loaded {len(actual_df)} actual results")
    except:
        logger.error("❌ No actual results found")
        return None, None, None
    
    return props_df, lineups_df, actual_df

def validate_prop_bets(props_df, actual_df):
    """Check if our prop bets were correct"""
    
    if props_df is None or len(props_df) == 0:
        return None
    
    prop_results = []
    
    for _, prop in props_df.iterrows():
        player_name = prop['player_name']
        prop_type = prop['prop_type'].lower()
        line = prop['line']
        pick = prop['my_pick'].upper()
        confidence = prop['confidence']
        
        # Find player in actual results
        player_matches = actual_df[
            actual_df['name'].str.contains(player_name, case=False, na=False)
        ]
        
        if len(player_matches) > 0:
            player_data = player_matches.iloc[0]
            
            # Get actual stat based on prop type
            if 'walk' in prop_type:
                actual_stat = player_data.get('walks', 0)
            elif 'hit' in prop_type:
                actual_stat = player_data.get('hits', 0)
            elif 'home_run' in prop_type or 'hr' in prop_type:
                actual_stat = player_data.get('home_runs', 0)
            elif 'run' in prop_type and 'home' not in prop_type:
                actual_stat = player_data.get('runs', 0)
            elif 'rbi' in prop_type:
                actual_stat = player_data.get('rbis', 0)
            elif 'strikeout' in prop_type:
                actual_stat = player_data.get('strikeouts', 0)
            else:
                actual_stat = None
            
            if actual_stat is not None:
                # Determine if prop was correct
                if pick == 'OVER':
                    prop_correct = actual_stat > line
                else:  # UNDER
                    prop_correct = actual_stat < line
                
                prop_results.append({
                    'player_name': player_name,
                    'prop_type': prop_type,
                    'line': line,
                    'my_pick': pick,
                    'confidence': confidence,
                    'actual_stat': actual_stat,
                    'prop_correct': prop_correct,
                    'actual_fppg': player_data['actual_fppg']
                })
            else:
                prop_results.append({
                    'player_name': player_name,
                    'prop_type': prop_type,
                    'line': line,
                    'my_pick': pick,
                    'confidence': confidence,
                    'actual_stat': 'STAT_NOT_FOUND',
                    'prop_correct': False,
                    'actual_fppg': 0
                })
        else:
            prop_results.append({
                'player_name': player_name,
                'prop_type': prop_type,
                'line': line,
                'my_pick': pick,
                'confidence': confidence,
                'actual_stat': 'PLAYER_NOT_FOUND',
                'prop_correct': False,
                'actual_fppg': 0
            })
    
    return pd.DataFrame(prop_results)

def validate_lineup_performance(lineups_df, actual_df):
    """Check actual vs projected performance for our lineups"""
    
    lineup_results = []
    
    for _, lineup in lineups_df.iterrows():
        lineup_name = lineup['Lineup']
        total_salary = lineup['Total_Salary']
        projected_fppg = lineup['Projected_FPPG']
        
        # Extract players from lineup
        players = []
        actual_total = 0
        players_found = 0
        
        for pos in ['P', 'C', '1B', '2B', '3B', 'SS', 'OF1', 'OF2', 'OF3']:
            if pos in lineup and pd.notna(lineup[pos]):
                player_info = lineup[pos]
                if '(' in player_info:
                    player_name = player_info.split('(')[0].strip()
                    team = player_info.split('(')[1].replace(')', '').strip()
                else:
                    player_name = player_info.strip()
                    team = 'UNK'
                
                # Find in actual results
                player_matches = actual_df[
                    actual_df['name'].str.contains(player_name, case=False, na=False)
                ]
                
                if len(player_matches) > 0:
                    actual_points = player_matches.iloc[0]['actual_fppg']
                    players_found += 1
                    players.append({
                        'name': player_name,
                        'position': pos,
                        'team': team,
                        'actual_fppg': actual_points,
                        'found': True
                    })
                    actual_total += actual_points
                else:
                    players.append({
                        'name': player_name,
                        'position': pos,
                        'team': team,
                        'actual_fppg': 0,
                        'found': False
                    })
        
        accuracy = (actual_total / projected_fppg * 100) if projected_fppg > 0 else 0
        
        lineup_results.append({
            'lineup_name': lineup_name,
            'total_salary': total_salary,
            'projected_fppg': projected_fppg,
            'actual_fppg': actual_total,
            'difference': actual_total - projected_fppg,
            'accuracy_pct': accuracy,
            'players_found': players_found,
            'total_players': len(players),
            'players': players
        })
    
    return lineup_results

def create_validation_report(prop_results, lineup_results):
    """Create comprehensive validation report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("\n" + "="*80)
    print("🎯 PROPER VALIDATION REPORT")
    print("="*80)
    
    # Prop Bet Results
    if prop_results is not None and len(prop_results) > 0:
        print("\n📊 PROP BET VALIDATION:")
        print("-" * 50)
        
        for _, prop in prop_results.iterrows():
            result_emoji = "✅" if prop['prop_correct'] else "❌"
            print(f"{result_emoji} {prop['player_name']} {prop['prop_type'].title()}")
            print(f"   Line: {prop['line']} | Pick: {prop['my_pick']} | Confidence: {prop['confidence']}/5")
            print(f"   Actual: {prop['actual_stat']} | Result: {'CORRECT' if prop['prop_correct'] else 'INCORRECT'}")
            print(f"   Player FPPG: {prop['actual_fppg']:.1f}")
            print()
        
        prop_accuracy = prop_results['prop_correct'].mean() * 100
        print(f"🎯 PROP BET ACCURACY: {prop_accuracy:.1f}%")
        print(f"📊 Props Correct: {prop_results['prop_correct'].sum()}/{len(prop_results)}")
    else:
        print("\n⚠️ No prop bet data to validate")
    
    # Lineup Performance
    print("\n🏆 LINEUP PERFORMANCE VALIDATION:")
    print("-" * 50)
    
    best_lineup = max(lineup_results, key=lambda x: x['actual_fppg'])
    avg_accuracy = np.mean([l['accuracy_pct'] for l in lineup_results])
    avg_players_found = np.mean([l['players_found'] for l in lineup_results])
    
    print(f"📊 Average Accuracy: {avg_accuracy:.1f}%")
    print(f"🏆 Best Lineup: {best_lineup['lineup_name']} ({best_lineup['actual_fppg']:.1f} FPPG)")
    print(f"👥 Avg Players Found: {avg_players_found:.1f}/9")
    
    print(f"\n📋 LINEUP-BY-LINEUP BREAKDOWN:")
    for lineup in lineup_results:
        print(f"\n🎯 {lineup['lineup_name']}:")
        print(f"   💰 Salary: ${lineup['total_salary']:,}")
        print(f"   🎯 Projected: {lineup['projected_fppg']:.1f} FPPG")
        print(f"   ✅ Actual: {lineup['actual_fppg']:.1f} FPPG")
        print(f"   📊 Accuracy: {lineup['accuracy_pct']:.1f}%")
        print(f"   👥 Players Found: {lineup['players_found']}/9")
        
        print(f"   📋 Player Breakdown:")
        for player in lineup['players']:
            status = "✅" if player['found'] else "❌"
            print(f"      {status} {player['name']} ({player['position']}) - {player['actual_fppg']:.1f} FPPG")
    
    # Save detailed CSV
    if prop_results is not None:
        prop_file = f"../data/prop_validation_{timestamp}.csv"
        prop_results.to_csv(prop_file, index=False)
        print(f"\n💾 Prop validation saved: {prop_file}")
    
    lineup_summary = []
    for lineup in lineup_results:
        lineup_summary.append({
            'lineup_name': lineup['lineup_name'],
            'projected_fppg': lineup['projected_fppg'],
            'actual_fppg': lineup['actual_fppg'],
            'accuracy_pct': lineup['accuracy_pct'],
            'players_found': lineup['players_found']
        })
    
    lineup_file = f"../data/lineup_validation_{timestamp}.csv"
    pd.DataFrame(lineup_summary).to_csv(lineup_file, index=False)
    print(f"💾 Lineup validation saved: {lineup_file}")
    
    print("\n" + "="*80)

def main():
    """Main validation function"""
    
    logger.info("🎯 Starting proper validation...")
    
    # Load data
    props_df, lineups_df, actual_df = load_validation_data()
    
    if lineups_df is None:
        logger.error("❌ Cannot validate without lineup data")
        return
    
    # Validate prop bets
    prop_results = validate_prop_bets(props_df, actual_df)
    
    # Validate lineup performance
    lineup_results = validate_lineup_performance(lineups_df, actual_df)
    
    # Create report
    create_validation_report(prop_results, lineup_results)
    
    logger.info("✅ Validation complete!")

if __name__ == "__main__":
    main()
