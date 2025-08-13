#!/usr/bin/env python3
"""
Daily Enhanced Lineup Selector
Automatically recommends which lineup to use for each contest type
"""

import pandas as pd
import os
from datetime import datetime

def analyze_daily_lineups():
    """Analyze all enhanced lineups and provide recommendations"""
    print("🎯 DAILY ENHANCED LINEUP SELECTOR")
    print("=" * 50)
    
    # Load all enhanced lineups
    lineup_files = []
    data_dir = '../data/'
    
    for file in os.listdir(data_dir):
        if file.startswith('enhanced_lineup_') and file.endswith('.csv'):
            lineup_files.append(file)
    
    if not lineup_files:
        print("❌ No enhanced lineups found!")
        return
    
    lineups = {}
    
    for file in lineup_files:
        try:
            df = pd.read_csv(data_dir + file)
            
            # Extract strategy and lineup number
            parts = file.replace('enhanced_lineup_', '').replace('.csv', '').split('_')
            strategy = parts[0]
            lineup_num = parts[1] if len(parts) > 1 else '1'
            
            # Calculate lineup metrics
            total_salary = df['Salary'].sum()
            total_projection = df['Projected_FPPG'].sum()
            avg_value = df['Value'].mean()
            min_projection = df['Projected_FPPG'].min()
            max_projection = df['Projected_FPPG'].max()
            projection_variance = df['Projected_FPPG'].var()
            
            # Categorize by strategy
            if strategy not in lineups:
                lineups[strategy] = []
            
            lineups[strategy].append({
                'file': file,
                'lineup_num': lineup_num,
                'total_salary': total_salary,
                'total_projection': total_projection,
                'avg_value': avg_value,
                'min_projection': min_projection,
                'max_projection': max_projection,
                'projection_variance': projection_variance,
                'floor_score': min_projection * 9,  # Conservative floor estimate
                'ceiling_score': max_projection * 1.5 * 9,  # Aggressive ceiling estimate
                'players': df
            })
            
        except Exception as e:
            print(f"⚠️ Error reading {file}: {e}")
    
    # Analyze and recommend
    recommendations = {}
    
    for strategy, strategy_lineups in lineups.items():
        if not strategy_lineups:
            continue
            
        # Sort by total projection
        strategy_lineups.sort(key=lambda x: x['total_projection'], reverse=True)
        
        best_lineup = strategy_lineups[0]
        recommendations[strategy] = best_lineup
    
    # Display recommendations
    print("\n🏆 DAILY LINEUP RECOMMENDATIONS")
    print("=" * 50)
    
    # Cash Game Recommendation
    if 'balanced' in recommendations:
        cash_lineup = recommendations['balanced']
        print(f"\n💰 CASH GAMES (50/50s, Double-Ups):")
        print(f"   📁 Use: {cash_lineup['file']}")
        print(f"   💵 Salary: ${cash_lineup['total_salary']:,.0f}")
        print(f"   📈 Projection: {cash_lineup['total_projection']:.1f} FPPG")
        print(f"   🎯 Floor Score: {cash_lineup['floor_score']:.1f} (conservative)")
        print(f"   💎 Value: {cash_lineup['avg_value']:.2f} pts/$1K")
        print(f"   🔒 Why: Balanced approach with solid floor")
    
    # GPP Recommendation  
    if 'gpp' in recommendations:
        gpp_lineup = recommendations['gpp']
        print(f"\n🎰 GPP TOURNAMENTS (Large Field):")
        print(f"   📁 Use: {gpp_lineup['file']}")
        print(f"   💵 Salary: ${gpp_lineup['total_salary']:,.0f}")
        print(f"   📈 Projection: {gpp_lineup['total_projection']:.1f} FPPG")
        print(f"   🚀 Ceiling Score: {gpp_lineup['ceiling_score']:.1f} (upside)")
        print(f"   💎 Value: {gpp_lineup['avg_value']:.2f} pts/$1K")
        print(f"   🔥 Why: High ceiling with tournament upside")
    
    # Show top players for each recommendation
    print(f"\n🌟 TOP PERFORMERS IN TODAY'S LINEUPS:")
    
    all_players = []
    for strategy, lineup_data in recommendations.items():
        players = lineup_data['players']
        for _, player in players.iterrows():
            all_players.append({
                'name': player['Nickname'],
                'position': player['Primary_Position'],
                'salary': player['Salary'],
                'projection': player['Projected_FPPG'],
                'value': player['Value'],
                'strategy': strategy
            })
    
    # Sort by projection and show top 5
    all_players.sort(key=lambda x: x['projection'], reverse=True)
    
    for i, player in enumerate(all_players[:5]):
        print(f"   {i+1}. {player['name']} ({player['position']}) - "
              f"${player['salary']} - {player['projection']:.1f} FPPG - "
              f"{player['value']:.2f} value")
    
    # Multi-entry recommendations
    print(f"\n🎯 MULTI-ENTRY STRATEGY:")
    
    if 'gpp' in lineups and len(lineups['gpp']) >= 3:
        print(f"   🎰 For GPP Multi-Entry (3-5 lineups):")
        for i, lineup in enumerate(lineups['gpp'][:3]):
            print(f"      #{i+1}: {lineup['file']} ({lineup['total_projection']:.1f} FPPG)")
        print(f"   💡 Strategy: Different stacks/pivots for tournament coverage")
    
    if 'balanced' in lineups and len(lineups['balanced']) >= 2:
        print(f"   💰 For Cash Multi-Entry (2-3 lineups):")
        for i, lineup in enumerate(lineups['balanced'][:2]):
            print(f"      #{i+1}: {lineup['file']} ({lineup['total_projection']:.1f} FPPG)")
        print(f"   💡 Strategy: Slight variations for cash game security")
    
    # Weather impact analysis
    print(f"\n🌤️ WEATHER & PARK FACTORS ACTIVE:")
    
    sample_lineup = recommendations.get('gpp', recommendations.get('balanced'))
    if sample_lineup:
        weather_boosted = sample_lineup['players'][
            sample_lineup['players']['Projected_FPPG'] > sample_lineup['players']['FPPG'] * 1.1
        ]
        
        if len(weather_boosted) > 0:
            print(f"   🔥 {len(weather_boosted)} players getting weather boosts today:")
            for _, player in weather_boosted.head(3).iterrows():
                boost = ((player['Projected_FPPG'] / player['FPPG']) - 1) * 100
                print(f"      • {player['Nickname']}: +{boost:.1f}% boost")
    
    print(f"\n📅 Analysis complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return recommendations

if __name__ == "__main__":
    analyze_daily_lineups()
