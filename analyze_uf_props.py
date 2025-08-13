#!/usr/bin/env python3
"""
Underdog Fantasy Analyzer
Analyzes current UF props and finds best opportunities
"""

import pandas as pd
import numpy as np
from datetime import datetime

def analyze_uf_props():
    """Analyze Underdog Fantasy props"""
    print("🎲 UNDERDOG FANTASY PROP ANALYZER")
    print("=" * 45)
    
    try:
        # Load UF data
        df = pd.read_excel('../data/uf_mlb_picks.xlsx')
        print(f"✅ Loaded {len(df)} Underdog Fantasy props")
        
        # Show available stats
        stat_columns = [col for col in df.columns if col not in ['player_name', 'source']]
        print(f"\n📊 Available Prop Types:")
        
        for stat in stat_columns:
            non_null = df[stat].notna().sum()
            if non_null > 0:
                print(f"   • {stat}: {non_null} props")
        
        # Analyze each prop type
        print(f"\n🎯 UNDERDOG FANTASY OPPORTUNITIES:")
        print("-" * 40)
        
        opportunities = []
        
        for stat in stat_columns:
            stat_df = df[df[stat].notna()].copy()
            if len(stat_df) == 0:
                continue
                
            print(f"\n{stat.upper()} PROPS ({len(stat_df)} available):")
            
            # Sort by line value to find interesting spots
            stat_df = stat_df.sort_values(stat)
            
            # Show lowest and highest lines
            if len(stat_df) >= 5:
                print(f"   Lowest lines:")
                for _, row in stat_df.head(3).iterrows():
                    print(f"      {row['player_name']}: {row[stat]}")
                
                print(f"   Highest lines:")
                for _, row in stat_df.tail(2).iterrows():
                    print(f"      {row['player_name']}: {row[stat]}")
            else:
                print(f"   All props:")
                for _, row in stat_df.iterrows():
                    print(f"      {row['player_name']}: {row[stat]}")
        
        # Find potential correlations with our models
        print(f"\n🔗 CORRELATION OPPORTUNITIES:")
        print("-" * 30)
        
        # Look for players that appear in both UF and our enhanced lineups
        try:
            # Check if we have enhanced lineup data
            import os
            lineup_files = [f for f in os.listdir('../data/') 
                          if f.startswith('enhanced_lineup_') and f.endswith('.csv')]
            
            if lineup_files:
                # Load our enhanced lineups
                all_players = set()
                for file in lineup_files:
                    lineup_df = pd.read_csv(f'../data/{file}')
                    all_players.update(lineup_df['Nickname'].tolist())
                
                # Find overlapping players
                uf_players = set(df['player_name'].tolist())
                overlap = all_players.intersection(uf_players)
                
                if overlap:
                    print(f"   🎯 {len(overlap)} players in both UF and enhanced lineups:")
                    for player in sorted(list(overlap))[:5]:
                        # Show their UF props
                        player_props = df[df['player_name'] == player]
                        if len(player_props) > 0:
                            props = []
                            for stat in stat_columns:
                                if not pd.isna(player_props.iloc[0][stat]):
                                    props.append(f"{stat}: {player_props.iloc[0][stat]}")
                            if props:
                                print(f"      {player}: {', '.join(props[:2])}")
                else:
                    print(f"   ⚠️ No player overlap found")
            else:
                print(f"   ⚠️ No enhanced lineups found")
                
        except Exception as e:
            print(f"   ⚠️ Could not check correlations: {e}")
        
        # Summary stats
        print(f"\n📈 SUMMARY:")
        print(f"   Total props: {len(df)}")
        print(f"   Unique players: {df['player_name'].nunique()}")
        print(f"   Prop types: {len([col for col in stat_columns if df[col].notna().sum() > 0])}")
        
        # EV ANALYSIS - The key missing piece!
        print(f"\n🎯 EXPECTED VALUE ANALYSIS:")
        print("=" * 50)
        
        try:
            # Load our ML predictions - USE TODAY'S DATA ONLY (NOT HISTORICAL)
            predictions_file = '../data/today_hitter_features.csv'  # Changed from massive historical file
            if os.path.exists(predictions_file):
                pred_df = pd.read_csv(predictions_file)
                print(f"✅ Loaded ML predictions for {len(pred_df)} players (TODAY ONLY)")
                
                # Load the actual ML model predictions if available
                model_predictions = {}
                
                # Load individual model predictions 
                model_files = {
                    'home_runs': '../Scripts/models/home_runs/predictions_home_runs.csv',
                    'hits': '../Scripts/models/hits/predictions_hits.csv', 
                    'total_bases': '../Scripts/models/total_bases/predictions_total_bases.csv',
                    'runs': '../Scripts/models/runs/predictions_runs.csv',
                    'rbi': '../Scripts/models/rbi/predictions_rbi.csv'
                }
                
                for stat, model_file in model_files.items():
                    if os.path.exists(model_file):
                        model_df = pd.read_csv(model_file)
                        
                        # Get most recent prediction for each player
                        if 'date' in model_df.columns:
                            model_df['date'] = pd.to_datetime(model_df['date'])
                            model_df = model_df.sort_values('date').groupby('name').tail(1)
                        
                        print(f"✅ Loaded {len(model_df)} {stat} ML predictions")
                        
                        for _, row in model_df.iterrows():
                            player_name = row.get('name', '')
                            if player_name:
                                if player_name not in model_predictions:
                                    model_predictions[player_name] = {}
                                model_predictions[player_name][stat] = row.get('predicted', 0)
                
                # Calculate EV for key stats
                ev_opportunities = []
                
                for _, row in df.iterrows():
                    player_name = row['player_name']
                    
                    # Try to find matching player in predictions
                    pred_row = None
                    ml_predictions = {}
                    
                    # First try exact match in model predictions
                    if player_name in model_predictions:
                        ml_predictions = model_predictions[player_name]
                    
                    # Also try partial name match in the feature dataframe for backup stats
                    name_parts = player_name.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        
                        matches = pred_df[
                            (pred_df['First Name'].str.contains(first_name, case=False, na=False)) &
                            (pred_df['Last Name'].str.contains(last_name, case=False, na=False))
                        ]
                        
                        if len(matches) > 0:
                            pred_row = matches.iloc[0].to_dict()
                    
                    if not ml_predictions and pred_row is None:
                        continue
                    
                    # Analyze key props vs our predictions/stats
                    stat_analyses = []
                    
                    # Home Runs analysis - prioritize ML model predictions
                    if not pd.isna(row.get('Home Runs')):
                        line = float(row['Home Runs'])
                        
                        if 'home_runs' in ml_predictions:
                            prediction = ml_predictions['home_runs']
                            source = "ML Model"
                        elif pred_row:
                            # Fallback to season stats calculation
                            season_hrs = pred_row.get('homeRuns', 0)
                            season_abs = pred_row.get('atBats', 1)
                            if season_abs > 50:
                                hr_rate = season_hrs / season_abs
                                prediction = hr_rate * 4.0
                                source = "Season Stats"
                            else:
                                prediction = 0.05
                                source = "Default"
                        else:
                            continue
                        
                        if abs(prediction - line) > 0.05:
                            if prediction > line:
                                edge = ((prediction - line) / max(line, 0.1)) * 100
                                rec = 'OVER'
                            else:
                                edge = ((line - prediction) / max(line, 0.1)) * 100
                                rec = 'UNDER'
                            
                            if edge > 15 and edge < 80:
                                stat_analyses.append({
                                    'stat': 'Home Runs',
                                    'line': line,
                                    'prediction': round(prediction, 3),
                                    'edge': round(edge, 1),
                                    'recommendation': rec,
                                    'source': source
                                })
                    
                    # Hits analysis - prioritize ML model predictions
                    if not pd.isna(row.get('Hits')):
                        line = float(row['Hits'])
                        
                        if 'hits' in ml_predictions:
                            prediction = ml_predictions['hits']
                            source = "ML Model"
                        elif pred_row:
                            season_hits = pred_row.get('hits', 0)
                            season_abs = pred_row.get('atBats', 1)
                            if season_abs > 50:
                                avg = season_hits / season_abs
                                prediction = avg * 4.0
                                source = "Season Stats"
                            else:
                                prediction = 1.0
                                source = "Default"
                        else:
                            continue
                        
                        if abs(prediction - line) > 0.1:
                            if prediction > line:
                                edge = ((prediction - line) / max(line, 0.1)) * 100
                                rec = 'OVER'
                            else:
                                edge = ((line - prediction) / max(line, 0.1)) * 100
                                rec = 'UNDER'
                            
                            if edge > 15 and edge < 60:
                                stat_analyses.append({
                                    'stat': 'Hits',
                                    'line': line,
                                    'prediction': round(prediction, 2),
                                    'edge': round(edge, 1),
                                    'recommendation': rec,
                                    'source': source
                                })
                    
                    # Total Bases analysis - prioritize ML model predictions
                    if not pd.isna(row.get('Total Bases')):
                        line = float(row['Total Bases'])
                        
                        if 'total_bases' in ml_predictions:
                            prediction = ml_predictions['total_bases']
                            source = "ML Model"
                        elif pred_row:
                            # Calculate from season stats
                            season_hits = pred_row.get('hits', 0)
                            season_doubles = pred_row.get('doubles', 0)
                            season_triples = pred_row.get('triples', 0)
                            season_hrs = pred_row.get('homeRuns', 0)
                            season_abs = pred_row.get('atBats', 1)
                            
                            if season_abs > 50:
                                singles = season_hits - season_doubles - season_triples - season_hrs
                                total_bases = singles + (season_doubles * 2) + (season_triples * 3) + (season_hrs * 4)
                                tb_rate = total_bases / season_abs
                                prediction = tb_rate * 4.0
                                source = "Season Stats"
                            else:
                                prediction = 1.5
                                source = "Default"
                        else:
                            continue
                        
                        if abs(prediction - line) > 0.15:
                            if prediction > line:
                                edge = ((prediction - line) / max(line, 0.1)) * 100
                                rec = 'OVER'
                            else:
                                edge = ((line - prediction) / max(line, 0.1)) * 100
                                rec = 'UNDER'
                            
                            if edge > 12 and edge < 70:
                                stat_analyses.append({
                                    'stat': 'Total Bases',
                                    'line': line,
                                    'prediction': round(prediction, 2),
                                    'edge': round(edge, 1),
                                    'recommendation': rec,
                                    'source': source
                                })
                    
                    # Add significant opportunities
                    for analysis in stat_analyses:
                        if analysis['edge'] > 15 and analysis['edge'] < 100:  # Realistic edge range
                            ev_opportunities.append({
                                'player': player_name,
                                **analysis,
                                'confidence': 'HIGH' if analysis['edge'] > 40 else 'MEDIUM'
                            })
                
                # Display top EV opportunities
                if ev_opportunities:
                    ev_df = pd.DataFrame(ev_opportunities)
                    ev_df = ev_df.sort_values('edge', ascending=False)
                    
                    print(f"\n🔥 TOP UNDERDOG FANTASY EV PLAYS:")
                    print("-" * 60)
                    
                    for i, opp in enumerate(ev_df.head(15).to_dict('records')):
                        conf_emoji = "🔥" if opp['confidence'] == 'HIGH' else "⚡"
                        source_emoji = "🤖" if opp.get('source') == 'ML Model' else "📊" if opp.get('source') == 'Season Stats' else "⚠️"
                        print(f"{i+1:2d}. {opp['player']:<20} {opp['stat']:<12} {opp['recommendation']:<5} {opp['line']}")
                        print(f"    {conf_emoji} Pred: {opp['prediction']} | Edge: {opp['edge']}% | {source_emoji} {opp.get('source', 'Unknown')}")
                        print()
                    
                    # Save detailed EV analysis
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
                    ev_file = f'../data/uf_ev_analysis_{timestamp}.csv'
                    ev_df.to_csv(ev_file, index=False)
                    print(f"💾 Detailed EV analysis saved: {ev_file}")
                    
                    # Show correlation with enhanced lineups
                    try:
                        lineup_files = [f for f in os.listdir('../data/') 
                                      if f.startswith('enhanced_lineup_') and f.endswith('.csv')]
                        
                        if lineup_files:
                            lineup_df = pd.read_csv(f'../data/{lineup_files[0]}')
                            lineup_players = set(lineup_df['Nickname'].tolist())
                            
                            lineup_props = ev_df[ev_df['player'].isin(lineup_players)]
                            if len(lineup_props) > 0:
                                print(f"\n🎯 EV PROPS FOR YOUR ENHANCED LINEUP PLAYERS:")
                                print("-" * 50)
                                for _, prop in lineup_props.head(5).iterrows():
                                    print(f"✅ {prop['player']}: {prop['stat']} {prop['recommendation']} {prop['line']} ({prop['edge']}% edge)")
                    except:
                        pass
                        
                else:
                    print("⚠️ No significant EV opportunities found with current thresholds")
                    print("💡 Try checking Fantasy Points props or lowering edge requirements")
                    
            else:
                print("⚠️ ML predictions file not found - run enhanced pipeline first")
                
        except Exception as e:
            print(f"⚠️ Could not perform EV analysis: {e}")
            import traceback
            traceback.print_exc()
        
        # Create simple recommendations
        print(f"\n💡 STRATEGY RECOMMENDATIONS:")
        print(f"   1. Focus on high-edge opportunities above (>25% edge)")
        print(f"   2. Cross-reference with your enhanced lineup players") 
        print(f"   3. Consider UF Fantasy Points props for pitchers")
        print(f"   4. Look for low lines on power hitters (HR, Total Bases)")
        
    except Exception as e:
        print(f"❌ Error analyzing UF props: {e}")
        import traceback
        traceback.print_exc()
        
    except Exception as e:
        print(f"❌ Error analyzing UF props: {e}")
        print(f"   Make sure uf_mlb_picks.xlsx exists and is readable")

if __name__ == "__main__":
    analyze_uf_props()
