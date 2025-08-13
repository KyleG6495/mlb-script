#!/usr/bin/env python3
"""
🏆 ULTIMATE ML TOURNAMENT STRATEGY
==================================================
Combines your existing ML systems with tournament optimization strategies
for 210+ FPPG tournament domination

Strategy Philosophy:
- Use your ML Game State Enhanced system (157.4 FPPG lineups)
- Apply tournament optimization on ML output
- Combine with injury filtering and slate sanity checks
- Target 220+ FPPG ceiling with 15%+ hit rate

ML Systems Integration:
1. Enhanced ML Volume System (106.9 FPPG with 9 lineups)
2. Game State Enhanced DFS (157.4 FPPG with 20 lineups)
3. Tournament Optimizers (237.4 FPPG ceiling potential)
4. Injury filtering and slate sanity
"""

import pandas as pd
import numpy as np
import logging
import json
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_ml_tournament_arsenal():
    """Load all ML-generated lineups for tournament optimization"""
    logger.info("🚀 LOADING ML TOURNAMENT ARSENAL")
    logger.info("="*60)
    
    arsenal = {}
    data_dir = "../data/"
    
    # 1. Enhanced ML Volume System
    enhanced_ml_files = [f for f in os.listdir(data_dir) if f.startswith('enhanced_ml_dfs_lineups_')]
    if enhanced_ml_files:
        latest_enhanced = sorted(enhanced_ml_files)[-1]
        try:
            arsenal['enhanced_ml'] = pd.read_csv(os.path.join(data_dir, latest_enhanced))
            logger.info(f"✅ Enhanced ML Volume: {len(arsenal['enhanced_ml'])} lineups loaded")
        except Exception as e:
            logger.warning(f"⚠️ Could not load Enhanced ML: {e}")
    
    # 2. Game State Enhanced DFS
    game_state_files = [f for f in os.listdir(data_dir) if f.startswith('game_state_enhanced_lineups_')]
    if game_state_files:
        latest_game_state = sorted(game_state_files)[-1]
        try:
            arsenal['game_state'] = pd.read_csv(os.path.join(data_dir, latest_game_state))
            logger.info(f"✅ Game State Enhanced: {len(arsenal['game_state'])} lineups loaded")
        except Exception as e:
            logger.warning(f"⚠️ Could not load Game State: {e}")
    
    # 3. Tournament Optimizers
    tournament_files = [
        'FIXED_SMART_DFS_BUILDER_output.csv',
        'ADVANCED_TOURNAMENT_OPTIMIZER_output.csv',
        'DIVERSIFIED_TOURNAMENT_BUILDER_output.csv',
        'MASTER_TOURNAMENT_COMBINER_output.csv'
    ]
    
    for file in tournament_files:
        filepath = os.path.join(data_dir, file)
        if os.path.exists(filepath):
            try:
                key = file.replace('_output.csv', '').lower()
                arsenal[key] = pd.read_csv(filepath)
                logger.info(f"✅ {key.title()}: {len(arsenal[key])} lineups loaded")
            except Exception as e:
                logger.warning(f"⚠️ Could not load {file}: {e}")
    
    # 4. Quintuple Tournament Lineups
    quintuple_files = [f for f in os.listdir(data_dir) if f.startswith('quintuple_lineups_combined_')]
    if quintuple_files:
        latest_quintuple = sorted(quintuple_files)[-1]
        try:
            arsenal['quintuple'] = pd.read_csv(os.path.join(data_dir, latest_quintuple))
            logger.info(f"✅ Quintuple Tournament: {len(arsenal['quintuple'])} lineups loaded")
        except Exception as e:
            logger.warning(f"⚠️ Could not load Quintuple: {e}")
    
    logger.info("="*60)
    logger.info(f"🏆 TOTAL ARSENAL: {sum(len(df) for df in arsenal.values())} lineups across {len(arsenal)} systems")
    return arsenal

def analyze_ml_performance(arsenal):
    """Analyze ML system performance for tournament optimization"""
    logger.info("📊 ANALYZING ML PERFORMANCE")
    logger.info("="*50)
    
    performance = {}
    
    for system_name, df in arsenal.items():
        if df.empty:
            continue
            
        # Determine projection column
        proj_col = None
        ceiling_col = None
        
        if 'projected_fppg' in df.columns:
            proj_col = 'projected_fppg'
        elif 'lineup_total_projection' in df.columns:
            proj_col = 'lineup_total_projection'
        elif 'Projected_FPPG' in df.columns:
            proj_col = 'Projected_FPPG'
        elif 'FPPG' in df.columns:
            proj_col = 'FPPG'
        
        if 'ceiling' in df.columns:
            ceiling_col = 'ceiling'
        elif 'lineup_total_ceiling' in df.columns:
            ceiling_col = 'lineup_total_ceiling'
        elif 'Ceiling_FPPG' in df.columns:
            ceiling_col = 'Ceiling_FPPG'
        
        if proj_col:
            # Get lineup-level stats
            if 'lineup_id' in df.columns:
                lineup_stats = df.groupby('lineup_id')[proj_col].sum()
                if ceiling_col in df.columns:
                    ceiling_stats = df.groupby('lineup_id')[ceiling_col].sum()
                else:
                    ceiling_stats = lineup_stats * 1.8  # Estimate ceiling
            else:
                lineup_stats = df[proj_col] if len(df[proj_col]) > 0 else pd.Series([0])
                ceiling_stats = df[ceiling_col] if ceiling_col and ceiling_col in df.columns else lineup_stats * 1.8
            
            performance[system_name] = {
                'lineups': len(lineup_stats),
                'avg_projection': lineup_stats.mean(),
                'max_projection': lineup_stats.max(),
                'min_projection': lineup_stats.min(),
                'avg_ceiling': ceiling_stats.mean(),
                'max_ceiling': ceiling_stats.max(),
                'tournament_ready': (lineup_stats >= 140).sum(),
                'elite_ready': (lineup_stats >= 180).sum(),
                'ceiling_potential': (ceiling_stats >= 220).sum()
            }
            
            logger.info(f"🎯 {system_name.title()}:")
            logger.info(f"   Lineups: {performance[system_name]['lineups']}")
            logger.info(f"   Avg Projection: {performance[system_name]['avg_projection']:.1f} FPPG")
            logger.info(f"   Max Projection: {performance[system_name]['max_projection']:.1f} FPPG")
            logger.info(f"   Avg Ceiling: {performance[system_name]['avg_ceiling']:.1f} FPPG")
            logger.info(f"   Tournament Ready (140+): {performance[system_name]['tournament_ready']}")
            logger.info(f"   Elite Ready (180+): {performance[system_name]['elite_ready']}")
            logger.info(f"   Ceiling Potential (220+): {performance[system_name]['ceiling_potential']}")
            logger.info("")
    
    return performance

def select_elite_ml_lineups(arsenal, performance):
    """Select the best ML lineups for tournament optimization"""
    logger.info("🏆 SELECTING ELITE ML LINEUPS")
    logger.info("="*50)
    
    elite_lineups = []
    
    # Priority 1: Game State Enhanced (157.4 FPPG)
    if 'game_state' in arsenal and not arsenal['game_state'].empty:
        gs_df = arsenal['game_state']
        if 'lineup_total_projection' in gs_df.columns:
            # Get unique lineups with 140+ FPPG
            lineup_totals = gs_df.groupby('lineup_id')['lineup_total_projection'].first()
            elite_lineup_ids = lineup_totals[lineup_totals >= 140].index
            
            for lineup_id in elite_lineup_ids[:10]:  # Top 10
                lineup_data = gs_df[gs_df['lineup_id'] == lineup_id]
                elite_lineups.append({
                    'source': 'game_state_enhanced',
                    'lineup_id': lineup_id,
                    'projection': lineup_totals[lineup_id],
                    'players': lineup_data[['name', 'position', 'team', 'salary', 'projected_fppg']].to_dict('records')
                })
            
            logger.info(f"✅ Selected {len(elite_lineup_ids[:10])} Game State Enhanced lineups")
    
    # Priority 2: Enhanced ML Volume System
    if 'enhanced_ml' in arsenal and not arsenal['enhanced_ml'].empty:
        eml_df = arsenal['enhanced_ml']
        # Add top Enhanced ML lineups
        if len(eml_df) > 0:
            for i in range(min(5, len(eml_df))):
                row = eml_df.iloc[i]
                elite_lineups.append({
                    'source': 'enhanced_ml',
                    'lineup_id': f"eml_{i+1}",
                    'projection': row.get('Projected_FPPG', row.get('FPPG', 100)),
                    'players': [row.to_dict()]
                })
            
            logger.info(f"✅ Selected {min(5, len(eml_df))} Enhanced ML lineups")
    
    # Priority 3: Tournament Optimizers (if they exist)
    tournament_systems = ['master_tournament_combiner', 'advanced_tournament_optimizer', 'diversified_tournament_builder']
    for system in tournament_systems:
        if system in arsenal and not arsenal[system].empty:
            df = arsenal[system]
            for i in range(min(3, len(df))):
                row = df.iloc[i]
                elite_lineups.append({
                    'source': system,
                    'lineup_id': f"{system}_{i+1}",
                    'projection': row.get('Ceiling_FPPG', row.get('FPPG', row.get('projected_fppg', 150))),
                    'players': [row.to_dict()]
                })
            
            logger.info(f"✅ Selected {min(3, len(df))} {system} lineups")
    
    logger.info("="*50)
    logger.info(f"🎯 TOTAL ELITE LINEUPS: {len(elite_lineups)}")
    
    # Sort by projection
    elite_lineups.sort(key=lambda x: x['projection'], reverse=True)
    
    return elite_lineups

def create_tournament_strategy(elite_lineups):
    """Create final tournament strategy recommendations"""
    logger.info("🚀 CREATING TOURNAMENT STRATEGY")
    logger.info("="*50)
    
    strategy = {
        'timestamp': datetime.now().strftime('%Y%m%d_%H%M%S'),
        'total_lineups': len(elite_lineups),
        'avg_projection': np.mean([lineup['projection'] for lineup in elite_lineups]),
        'max_projection': max([lineup['projection'] for lineup in elite_lineups]),
        'contest_allocation': {},
        'recommendations': []
    }
    
    # Contest allocation based on projection levels
    high_ceiling = [l for l in elite_lineups if l['projection'] >= 180]
    tournament_ready = [l for l in elite_lineups if 140 <= l['projection'] < 180]
    cash_game = [l for l in elite_lineups if l['projection'] < 140]
    
    strategy['contest_allocation'] = {
        'large_gpp': len(high_ceiling),
        'small_tournament': len(tournament_ready),
        'cash_game': len(cash_game)
    }
    
    # Strategy recommendations
    if high_ceiling:
        strategy['recommendations'].append({
            'contest_type': 'Large GPP (1000+ entries)',
            'lineups': len(high_ceiling),
            'strategy': 'Use highest ceiling lineups, focus on contrarian plays',
            'projection_range': f"{min([l['projection'] for l in high_ceiling]):.1f} - {max([l['projection'] for l in high_ceiling]):.1f} FPPG"
        })
    
    if tournament_ready:
        strategy['recommendations'].append({
            'contest_type': 'Small Tournament (200-500 entries)',
            'lineups': len(tournament_ready),
            'strategy': 'Balanced approach, moderate contrarian elements',
            'projection_range': f"{min([l['projection'] for l in tournament_ready]):.1f} - {max([l['projection'] for l in tournament_ready]):.1f} FPPG"
        })
    
    if cash_game:
        strategy['recommendations'].append({
            'contest_type': 'Cash Games & Small Leagues',
            'lineups': len(cash_game),
            'strategy': 'High floor, safe plays, avoid contrarian picks',
            'projection_range': f"{min([l['projection'] for l in cash_game]):.1f} - {max([l['projection'] for l in cash_game]):.1f} FPPG"
        })
    
    logger.info("📊 TOURNAMENT ALLOCATION:")
    logger.info(f"   Large GPP (180+ FPPG): {len(high_ceiling)} lineups")
    logger.info(f"   Small Tournament (140-180): {len(tournament_ready)} lineups")
    logger.info(f"   Cash Game (<140): {len(cash_game)} lineups")
    logger.info("")
    logger.info(f"🎯 AVERAGE PROJECTION: {strategy['avg_projection']:.1f} FPPG")
    logger.info(f"🚀 MAX PROJECTION: {strategy['max_projection']:.1f} FPPG")
    
    return strategy, elite_lineups

def save_ultimate_strategy(strategy, elite_lineups):
    """Save the ultimate ML tournament strategy"""
    logger.info("💾 SAVING ULTIMATE STRATEGY")
    logger.info("="*40)
    
    timestamp = strategy['timestamp']
    
    # Save strategy summary
    strategy_file = f"../data/ultimate_ml_tournament_strategy_{timestamp}.json"
    with open(strategy_file, 'w') as f:
        json.dump(strategy, f, indent=2)
    logger.info(f"✅ Strategy saved: {strategy_file}")
    
    # Save elite lineups
    lineups_file = f"../data/ultimate_ml_elite_lineups_{timestamp}.json"
    with open(lineups_file, 'w') as f:
        json.dump(elite_lineups, f, indent=2)
    logger.info(f"✅ Elite lineups saved: {lineups_file}")
    
    # Create readable strategy guide
    guide_file = f"../data/ultimate_ml_strategy_guide_{timestamp}.txt"
    with open(guide_file, 'w') as f:
        f.write("🏆 ULTIMATE ML TOURNAMENT STRATEGY GUIDE\n")
        f.write("="*60 + "\n\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Elite Lineups: {strategy['total_lineups']}\n")
        f.write(f"Average Projection: {strategy['avg_projection']:.1f} FPPG\n")
        f.write(f"Maximum Projection: {strategy['max_projection']:.1f} FPPG\n\n")
        
        f.write("CONTEST RECOMMENDATIONS:\n")
        f.write("-" * 30 + "\n")
        for rec in strategy['recommendations']:
            f.write(f"• {rec['contest_type']}: {rec['lineups']} lineups\n")
            f.write(f"  Range: {rec['projection_range']}\n")
            f.write(f"  Strategy: {rec['strategy']}\n\n")
        
        f.write("TOP 5 ELITE LINEUPS:\n")
        f.write("-" * 25 + "\n")
        for i, lineup in enumerate(elite_lineups[:5]):
            f.write(f"{i+1}. {lineup['source']} - {lineup['projection']:.1f} FPPG\n")
        
        f.write("\nSUCCESS METRICS:\n")
        f.write("-" * 20 + "\n")
        f.write("• Previous disaster: 31.7 FPPG\n")
        f.write("• Tournament winners: 153+ FPPG\n")
        f.write(f"• Our best lineup: {strategy['max_projection']:.1f} FPPG\n")
        f.write(f"• Improvement: {((strategy['max_projection'] - 31.7) / 31.7 * 100):.0f}% vs disaster\n")
        f.write(f"• Tournament competitive: {strategy['max_projection'] >= 153}\n")
    
    logger.info(f"✅ Strategy guide saved: {guide_file}")
    
    return strategy_file, lineups_file, guide_file

def main():
    """Main execution function"""
    logger.info("🚀 ULTIMATE ML TOURNAMENT STRATEGY - STARTING")
    logger.info("="*70)
    
    try:
        # Step 1: Load ML arsenal
        arsenal = load_ml_tournament_arsenal()
        
        if not arsenal:
            logger.error("❌ No ML systems found! Run your .bat files first.")
            return
        
        # Step 2: Analyze performance
        performance = analyze_ml_performance(arsenal)
        
        # Step 3: Select elite lineups
        elite_lineups = select_elite_ml_lineups(arsenal, performance)
        
        if not elite_lineups:
            logger.error("❌ No elite lineups found!")
            return
        
        # Step 4: Create tournament strategy
        strategy, elite_lineups = create_tournament_strategy(elite_lineups)
        
        # Step 5: Save everything
        strategy_file, lineups_file, guide_file = save_ultimate_strategy(strategy, elite_lineups)
        
        logger.info("="*70)
        logger.info("🏆 ULTIMATE ML TOURNAMENT STRATEGY COMPLETE!")
        logger.info("="*70)
        logger.info("📁 FILES CREATED:")
        logger.info(f"   📊 Strategy: {os.path.basename(strategy_file)}")
        logger.info(f"   📋 Lineups: {os.path.basename(lineups_file)}")
        logger.info(f"   📖 Guide: {os.path.basename(guide_file)}")
        logger.info("")
        logger.info("🎯 NEXT STEPS:")
        logger.info("   1. Review strategy guide for contest recommendations")
        logger.info("   2. Use elite lineups in appropriate tournaments")
        logger.info("   3. Monitor performance vs 153+ FPPG winners")
        logger.info("   4. Target Large GPP with highest ceiling lineups")
        logger.info("")
        logger.info(f"💪 TOURNAMENT READINESS: {len([l for l in elite_lineups if l['projection'] >= 153])} lineups above winner threshold")
        
    except Exception as e:
        logger.error(f"❌ Error in Ultimate ML Tournament Strategy: {e}")
        raise

if __name__ == "__main__":
    main()
