#!/usr/bin/env python3
"""
ENHANCED ML VOLUME SYSTEM
========================
Generate 20+ diverse lineups using Enhanced ML core to hit 150+ FPPG scores.

Key Strategy:
- Use proven Enhanced ML system as BASE (avoids disasters)
- Generate 20+ different lineup variations 
- Target different game environments and player combinations
- Some lineups target ceiling, others target floor
- Volume approach to hit 150+ winning scores

Performance Target: Beat 153.45 FPPG winning threshold
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class EnhancedMLVolumeSystem:
    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_enhanced_slate(self):
        """Load slate with Enhanced ML proven filtering"""
        print("🚀 ENHANCED ML VOLUME SYSTEM - Loading slate...")
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        if not slate_file.exists():
            print("❌ No slate file found")
            return None
            
        slate_df = pd.read_csv(slate_file)
        print(f"✅ Loaded slate with {len(slate_df)} players")
        
        # Apply PROVEN injury filtering (prevents disasters)
        original_count = len(slate_df)
        
        # Remove injured players
        if 'Injury Indicator' in slate_df.columns:
            injured_players = slate_df['Injury Indicator'].notna()
            injured_count = injured_players.sum()
            print(f"🔧 Removing {injured_count} injured players (disaster prevention)")
            slate_df = slate_df[~injured_players]
        
        # Remove non-probable pitchers
        if 'Probable Pitcher' in slate_df.columns:
            pitchers = slate_df[slate_df['Position'] == 'P']
            non_probable = pitchers['Probable Pitcher'] != 'Yes'
            non_probable_ids = set(pitchers[non_probable]['Id'])
            slate_df = slate_df[~slate_df['Id'].isin(non_probable_ids)]
            probable_count = (pitchers['Probable Pitcher'] == 'Yes').sum()
            print(f"⚾ Keeping only {probable_count} probable pitchers")
        
        filtered_count = len(slate_df)
        print(f"📊 Filtered: {original_count} → {filtered_count} players ({filtered_count/original_count*100:.1f}% remaining)")
        
        return slate_df
    
    def enhance_player_analysis(self, slate_df):
        """Add enhanced analytics for volume lineup generation"""
        print("🔍 Enhancing player analysis for volume generation...")
        
        slate_df = slate_df.copy()
        
        # Calculate value metrics
        slate_df['value_score'] = slate_df['FPPG'] / (slate_df['Salary'] / 1000)
        
        # Ceiling estimation (conservative but realistic)
        slate_df['estimated_ceiling'] = slate_df['FPPG'] * np.where(
            slate_df['Position'] == 'P',
            1.4,  # Pitchers: 40% ceiling upside
            1.6   # Hitters: 60% ceiling upside  
        )
        
        # Floor estimation 
        slate_df['estimated_floor'] = slate_df['FPPG'] * 0.7  # 70% of projection as floor
        
        # Player tier classification
        slate_df['salary_tier'] = pd.cut(
            slate_df['Salary'], 
            bins=[0, 2500, 3500, 4500, 15000], 
            labels=['Min', 'Value', 'Mid', 'Premium']
        )
        
        # Position scarcity (affects strategy)
        position_counts = slate_df['Position'].value_counts()
        slate_df['position_scarcity'] = slate_df['Position'].map(position_counts)
        
        # Game environment
        if 'Game' in slate_df.columns:
            # Team totals proxy (higher FPPG sum = better offense)
            team_totals = slate_df.groupby('Team')['FPPG'].sum()
            slate_df['team_total_proxy'] = slate_df['Team'].map(team_totals)
            
            # Game totals proxy
            game_totals = slate_df.groupby('Game')['FPPG'].sum()
            slate_df['game_total_proxy'] = slate_df['Game'].map(game_totals)
        else:
            slate_df['team_total_proxy'] = slate_df['FPPG']
            slate_df['game_total_proxy'] = slate_df['FPPG']
        
        print(f"📈 Enhanced analytics complete:")
        print(f"  Value scores: {slate_df['value_score'].min():.1f} - {slate_df['value_score'].max():.1f}")
        print(f"  Ceiling range: {slate_df['estimated_ceiling'].min():.1f} - {slate_df['estimated_ceiling'].max():.1f}")
        
        return slate_df
    
    def build_enhanced_ml_lineup(self, enhanced_slate, strategy_config):
        """Build single lineup using Enhanced ML principles with strategy variation"""
        
        strategy_name = strategy_config['name']
        pitcher_approach = strategy_config['pitcher_approach']
        salary_distribution = strategy_config['salary_distribution']
        value_weight = strategy_config['value_weight']
        ceiling_weight = strategy_config['ceiling_weight']
        stack_emphasis = strategy_config.get('stack_emphasis', 0.0)
        
        print(f"🏗️ Building {strategy_name} lineup...")
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        # 1. SELECT PITCHER based on strategy
        pitcher_candidates = enhanced_slate[
            (enhanced_slate['Position'] == 'P') &
            (~enhanced_slate['Id'].isin(used_ids))
        ]
        
        if pitcher_approach == 'premium':
            # High-salary, high-ceiling pitcher
            target_pitchers = pitcher_candidates[
                (pitcher_candidates['Salary'] >= 9000) &
                (pitcher_candidates['Salary'] <= remaining_budget - 20000)
            ]
            if not target_pitchers.empty:
                chosen = target_pitchers.loc[target_pitchers['estimated_ceiling'].idxmax()]
            else:
                chosen = pitcher_candidates.loc[pitcher_candidates['value_score'].idxmax()]
        
        elif pitcher_approach == 'value':
            # Mid-range value pitcher
            target_pitchers = pitcher_candidates[
                (pitcher_candidates['Salary'] >= 6000) &
                (pitcher_candidates['Salary'] <= 8500) &
                (pitcher_candidates['Salary'] <= remaining_budget - 18000)
            ]
            if not target_pitchers.empty:
                chosen = target_pitchers.loc[target_pitchers['value_score'].idxmax()]
            else:
                chosen = pitcher_candidates.loc[pitcher_candidates['value_score'].idxmax()]
        
        else:  # 'punt'
            # Low-salary, high-value pitcher
            target_pitchers = pitcher_candidates[
                (pitcher_candidates['Salary'] <= 7000) &
                (pitcher_candidates['Salary'] <= remaining_budget - 16000)
            ]
            if not target_pitchers.empty:
                chosen = target_pitchers.loc[target_pitchers['value_score'].idxmax()]
            else:
                return None
        
        selected_players.append(chosen)
        remaining_budget -= chosen['Salary']
        used_ids.add(chosen['Id'])
        positions_needed.remove('P')
        
        # 2. FILL POSITIONS with strategy-specific approach
        for position in positions_needed:
            if position == 'UTIL':
                candidates = enhanced_slate[~enhanced_slate['Id'].isin(used_ids)]
            else:
                candidates = enhanced_slate[
                    (enhanced_slate['Roster Position'].str.contains(position, na=False)) &
                    (~enhanced_slate['Id'].isin(used_ids))
                ]
            
            # Budget management
            positions_left = len(positions_needed) - positions_needed.index(position) - 1
            if positions_left > 0:
                min_budget_needed = positions_left * 2000
                max_spend = remaining_budget - min_budget_needed
            else:
                max_spend = remaining_budget
            
            affordable = candidates[
                (candidates['Salary'] <= max_spend) &
                (candidates['Salary'] >= 2000)
            ]
            
            if affordable.empty:
                affordable = candidates[candidates['Salary'] <= max_spend]
                if affordable.empty:
                    return None
            
            # Apply salary distribution preference
            if salary_distribution == 'balanced':
                # Target mid-range salaries
                preferred = affordable[
                    (affordable['Salary'] >= 2500) &
                    (affordable['Salary'] <= max_spend * 0.8)
                ]
                if preferred.empty:
                    preferred = affordable
            
            elif salary_distribution == 'stars_and_scrubs':
                # Prefer high or low salaries
                high_salary = affordable[affordable['Salary'] >= max_spend * 0.7]
                low_salary = affordable[affordable['Salary'] <= 2500]
                
                if not high_salary.empty and np.random.random() < 0.6:
                    preferred = high_salary
                elif not low_salary.empty:
                    preferred = low_salary
                else:
                    preferred = affordable
            
            else:  # 'value_heavy'
                preferred = affordable
            
            # Calculate selection score based on strategy weights
            preferred['selection_score'] = (
                preferred['value_score'] * value_weight +
                preferred['estimated_ceiling'] * ceiling_weight +
                preferred['FPPG'] * (1 - value_weight - ceiling_weight)
            )
            
            # Add stacking bonus if applicable
            if stack_emphasis > 0 and 'game_total_proxy' in preferred.columns:
                top_games = preferred['game_total_proxy'].quantile(0.7)
                stack_bonus = np.where(preferred['game_total_proxy'] >= top_games, stack_emphasis, 0)
                preferred['selection_score'] += stack_bonus
            
            chosen = preferred.loc[preferred['selection_score'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            total_ceiling = sum(p['estimated_ceiling'] for p in selected_players)
            total_floor = sum(p['estimated_floor'] for p in selected_players)
            
            return {
                'players': selected_players,
                'strategy': strategy_name,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'total_ceiling': total_ceiling,
                'total_floor': total_floor,
                'upside_multiplier': total_ceiling / total_projected if total_projected > 0 else 0
            }
        
        return None
    
    def generate_volume_lineups(self, enhanced_slate, target_count=25):
        """Generate diverse volume lineups targeting 150+ FPPG"""
        print(f"🎯 Generating {target_count} volume lineups targeting 150+ FPPG...")
        
        # Define strategy configurations for diversity
        strategies = [
            # Premium pitcher strategies
            {
                'name': 'Premium_Balanced',
                'pitcher_approach': 'premium',
                'salary_distribution': 'balanced',
                'value_weight': 0.4,
                'ceiling_weight': 0.3
            },
            {
                'name': 'Premium_Stars_Scrubs',
                'pitcher_approach': 'premium', 
                'salary_distribution': 'stars_and_scrubs',
                'value_weight': 0.2,
                'ceiling_weight': 0.5
            },
            # Value pitcher strategies
            {
                'name': 'Value_Ceiling',
                'pitcher_approach': 'value',
                'salary_distribution': 'balanced',
                'value_weight': 0.3,
                'ceiling_weight': 0.4,
                'stack_emphasis': 0.1
            },
            {
                'name': 'Value_Stars_Scrubs',
                'pitcher_approach': 'value',
                'salary_distribution': 'stars_and_scrubs', 
                'value_weight': 0.3,
                'ceiling_weight': 0.4
            },
            {
                'name': 'Value_Stack',
                'pitcher_approach': 'value',
                'salary_distribution': 'balanced',
                'value_weight': 0.3,
                'ceiling_weight': 0.2,
                'stack_emphasis': 0.2
            },
            # Punt pitcher strategies (more salary for hitters)
            {
                'name': 'Punt_Superstar',
                'pitcher_approach': 'punt',
                'salary_distribution': 'stars_and_scrubs',
                'value_weight': 0.2,
                'ceiling_weight': 0.5
            },
            {
                'name': 'Punt_Balanced',
                'pitcher_approach': 'punt',
                'salary_distribution': 'balanced',
                'value_weight': 0.4,
                'ceiling_weight': 0.3
            },
            {
                'name': 'Punt_Stack',
                'pitcher_approach': 'punt',
                'salary_distribution': 'value_heavy',
                'value_weight': 0.3,
                'ceiling_weight': 0.2,
                'stack_emphasis': 0.3
            }
        ]
        
        lineups = []
        strategy_index = 0
        
        for i in range(target_count):
            strategy = strategies[strategy_index % len(strategies)]
            
            # Add some randomization for more diversity
            if i > len(strategies):
                strategy = strategy.copy()
                strategy['value_weight'] += np.random.uniform(-0.1, 0.1)
                strategy['ceiling_weight'] += np.random.uniform(-0.1, 0.1)
                strategy['name'] += f"_Var{i-len(strategies)+1}"
            
            lineup = self.build_enhanced_ml_lineup(enhanced_slate, strategy)
            
            if lineup:
                lineup['lineup_id'] = f"VOLUME_ML_{i+1}"
                lineups.append(lineup)
                print(f"  ✅ {lineup['lineup_id']} ({lineup['strategy']}): ${lineup['total_salary']:,} | Proj: {lineup['total_projected']:.1f} | Ceil: {lineup['total_ceiling']:.1f}")
            else:
                print(f"  ❌ Failed lineup {i+1} ({strategy['name']})")
            
            strategy_index += 1
        
        print(f"\n📊 Generated {len(lineups)} diverse lineups")
        return lineups
    
    def export_volume_lineups(self, lineups):
        """Export volume lineups for submission"""
        if not lineups:
            print("❌ No lineups to export")
            return
        
        print("📄 Exporting volume lineup portfolio...")
        
        # Create detailed lineup data
        lineup_data = []
        
        for lineup in lineups:
            for player in lineup['players']:
                lineup_data.append({
                    'Lineup_ID': lineup['lineup_id'],
                    'Strategy': lineup['strategy'],
                    'Player_Name': f"{player['First Name']} {player['Last Name']}",
                    'Position': player['Roster Position'],
                    'Salary': player['Salary'],
                    'FPPG': player['FPPG'],
                    'Value_Score': player['value_score'],
                    'Estimated_Ceiling': player['estimated_ceiling'],
                    'Team': player.get('Team', ''),
                    'Game': player.get('Game', '')
                })
        
        lineup_df = pd.DataFrame(lineup_data)
        
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_ml_volume_lineups_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        lineup_df.to_csv(filepath, index=False)
        print(f"✅ Volume lineups exported: {filename}")
        
        # Portfolio analysis
        print(f"\n🏆 VOLUME PORTFOLIO ANALYSIS:")
        
        projections = [l['total_projected'] for l in lineups]
        ceilings = [l['total_ceiling'] for l in lineups]
        
        print(f"  📊 Projected Range: {min(projections):.1f} - {max(projections):.1f} FPPG")
        print(f"  🚀 Ceiling Range: {min(ceilings):.1f} - {max(ceilings):.1f} FPPG")
        print(f"  📈 Average Projected: {np.mean(projections):.1f} FPPG")
        print(f"  🎯 Average Ceiling: {np.mean(ceilings):.1f} FPPG")
        
        # Tournament readiness analysis
        target_score = 153.45
        ceiling_hits = sum(1 for c in ceilings if c >= target_score)
        projection_hits = sum(1 for p in projections if p >= target_score * 0.85)  # 85% of target
        
        print(f"\n🏆 TOURNAMENT READINESS (vs 153.45 FPPG target):")
        print(f"  🎯 Lineups with 153+ ceiling: {ceiling_hits}/{len(lineups)} ({ceiling_hits/len(lineups)*100:.1f}%)")
        print(f"  📊 Lineups with 130+ projection: {projection_hits}/{len(lineups)} ({projection_hits/len(lineups)*100:.1f}%)")
        
        if ceiling_hits >= len(lineups) * 0.5:
            print(f"  ✅ EXCELLENT: Portfolio has strong tournament upside!")
        elif ceiling_hits >= len(lineups) * 0.3:
            print(f"  ⚠️  GOOD: Decent tournament potential")
        else:
            print(f"  🔧 FAIR: May need more upside optimization")
        
        # Best lineups summary
        print(f"\n🌟 TOP 5 VOLUME LINEUPS:")
        sorted_lineups = sorted(lineups, key=lambda x: x['total_ceiling'], reverse=True)
        
        for i, lineup in enumerate(sorted_lineups[:5], 1):
            print(f"  {i}. {lineup['lineup_id']} ({lineup['strategy']}): {lineup['total_projected']:.1f} proj, {lineup['total_ceiling']:.1f} ceil, {lineup['upside_multiplier']:.1f}x")
        
        return filepath
    
    def run_volume_optimization(self):
        """Run complete Enhanced ML volume system"""
        print("🚀 ENHANCED ML VOLUME SYSTEM")
        print("Generate 25 diverse lineups targeting 150+ FPPG tournament scores")
        print("="*80)
        
        # Load slate with proven filtering
        slate_df = self.load_enhanced_slate()
        if slate_df is None:
            return
        
        # Enhance player analysis
        enhanced_slate = self.enhance_player_analysis(slate_df)
        
        # Generate volume lineups
        lineups = self.generate_volume_lineups(enhanced_slate, target_count=25)
        
        if lineups:
            # Export lineups
            filepath = self.export_volume_lineups(lineups)
            
            print(f"\n🎉 VOLUME OPTIMIZATION COMPLETE!")
            print(f"🎯 Generated {len(lineups)} diverse Enhanced ML lineups")
            print(f"📈 Target: Beat 153.45 FPPG winning threshold")
            print(f"💡 Strategy: Volume + diversity using proven Enhanced ML core")
            print(f"🏆 Ready for tournament submission!")
            
        else:
            print("❌ Failed to generate volume lineups")

def main():
    print("🎯 ENHANCED ML VOLUME SYSTEM")
    print("Generate winning tournament lineups targeting 153+ FPPG")
    print("="*80)
    
    optimizer = EnhancedMLVolumeSystem()
    
    try:
        optimizer.run_volume_optimization()
    except Exception as e:
        print(f"Error in volume optimization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
