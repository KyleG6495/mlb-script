#!/usr/bin/env python3
"""
DFS BACKTESTING WITH VALIDATION
================================
Test our validated DFS system against yesterday's actual results.
Shows how much better validated lineups perform vs random selection.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class DFSBacktestValidator:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_yesterday_data(self):
        """Load yesterday's slate and actual results"""
        print("📊 Loading yesterday's data for backtesting...")
        
        # Load slate (yesterday's available players)
        slate_file = self.slate_dir / "fd_slate_today.csv"
        if not slate_file.exists():
            print("❌ No slate file found")
            return None, None
            
        slate_df = pd.read_csv(slate_file)
        print(f"✅ Loaded slate with {len(slate_df)} available players")
        
        # Load actual results
        actual_file = self.data_dir / "actual_results_latest.csv"
        if not actual_file.exists():
            print("❌ No actual results found - run collect_actual_results.py first")
            return slate_df, None
            
        actual_df = pd.read_csv(actual_file)
        print(f"✅ Loaded actual results for {len(actual_df)} players")
        
        if 'date' in actual_df.columns:
            latest_date = actual_df['date'].max()
            print(f"📅 Results from: {latest_date}")
        
        return slate_df, actual_df
    
    def calculate_actual_fppg(self, actual_df):
        """Calculate actual FPPG from yesterday's performance"""
        print("🔢 Calculating actual FPPG scores...")
        
        actual_df = actual_df.copy()
        
        # FanDuel scoring
        actual_df['actual_fppg'] = (
            actual_df.get('hits', 0) * 3 +              # 3 pts per hit
            actual_df.get('runs', 0) * 3.2 +            # 3.2 pts per run
            actual_df.get('rbis', 0) * 3.5 +            # 3.5 pts per RBI
            actual_df.get('home_runs', 0) * 12 +        # 12 pts per HR (includes hit + RBI)
            actual_df.get('stolen_bases', 0) * 6 +      # 6 pts per SB
            actual_df.get('walks', 0) * 3 +             # 3 pts per walk
            actual_df.get('doubles', 0) * 6 +           # 6 pts per double (includes hit)
            actual_df.get('triples', 0) * 12 +          # 12 pts per triple (includes hit)
            # Pitcher scoring
            actual_df.get('innings_pitched', 0) * 3.5 + # 3.5 pts per IP
            actual_df.get('wins', 0) * 12 +             # 12 pts per win
            actual_df.get('earned_runs', 0) * -3        # -3 pts per ER
        )
        
        # Use provided fanduel_points if available
        if 'fanduel_points' in actual_df.columns:
            actual_df['actual_fppg'] = actual_df['fanduel_points'].fillna(actual_df['actual_fppg'])
        
        print(f"📈 Actual FPPG range: {actual_df['actual_fppg'].min():.1f} - {actual_df['actual_fppg'].max():.1f}")
        
        return actual_df
    
    def merge_slate_with_actual(self, slate_df, actual_df):
        """Merge slate projections with actual results"""
        print("🔗 Merging projections with actual performance...")
        
        # Clean names for matching
        slate_df['full_name'] = (slate_df['First Name'].str.strip() + ' ' + 
                                slate_df['Last Name'].str.strip()).str.lower()
        actual_df['full_name'] = actual_df['name'].str.lower().str.strip()
        
        # Merge on name
        merged = slate_df.merge(
            actual_df[['full_name', 'actual_fppg', 'position', 'team']],
            on='full_name',
            how='left'
        )
        
        # Fill missing actuals with 0 (didn't play)
        merged['actual_fppg'] = merged['actual_fppg'].fillna(0)
        
        matched = (merged['actual_fppg'] > 0).sum()
        print(f"✅ Found actual results for {matched}/{len(slate_df)} players ({matched/len(slate_df)*100:.1f}%)")
        
        return merged
    
    def validate_backtest_slate(self, merged_df):
        """Apply validation to yesterday's slate"""
        print("🔍 Applying validation to yesterday's slate...")
        
        merged_df = merged_df.copy()
        
        # Initialize validation
        merged_df['validation_score'] = 100
        merged_df['validation_issues'] = ''
        
        issues_count = {'low_salary': 0, 'bad_fppg': 0, 'missing_data': 0}
        
        for idx, player in merged_df.iterrows():
            issues = []
            score = 100
            
            # Salary validation
            salary = player.get('Salary', 0)
            if salary < 2000:
                issues.append(f'Low salary (${salary})')
                score -= 15
                issues_count['low_salary'] += 1
            
            # FPPG validation
            fppg = player.get('FPPG', 0)
            if fppg < 1.0:
                issues.append(f'Very low projected FPPG ({fppg})')
                score -= 20
                issues_count['bad_fppg'] += 1
            
            # Missing essential data
            if pd.isna(player.get('Team')) or str(player.get('Team', '')).strip() == '':
                issues.append('Missing team info')
                score -= 25
                issues_count['missing_data'] += 1
            
            # Position validation
            if pd.isna(player.get('Roster Position')):
                issues.append('Missing position')
                score -= 30
            
            merged_df.at[idx, 'validation_score'] = max(0, score)
            merged_df.at[idx, 'validation_issues'] = '; '.join(issues) if issues else 'OK'
        
        validated = (merged_df['validation_score'] >= 70).sum()
        print(f"✅ {validated}/{len(merged_df)} players passed validation (70+ score)")
        
        return merged_df
    
    def build_optimal_hindsight_lineup(self, validated_slate):
        """Build optimal lineup using actual results (perfect hindsight)"""
        print("🏆 Building OPTIMAL lineup using actual results (hindsight)...")
        
        # Filter to players who actually played and have results
        played_players = validated_slate[
            (validated_slate['actual_fppg'] > 0) &
            (validated_slate['Salary'] > 0)
        ].copy()
        
        if len(played_players) < 20:
            print(f"❌ Only {len(played_players)} players actually played")
            return None
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = played_players[~played_players['Id'].isin(used_ids)]
            else:
                candidates = played_players[
                    (played_players['Roster Position'].str.contains(position, na=False)) &
                    (~played_players['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"❌ No affordable {position} players who played")
                return None
            
            # Pick highest actual FPPG
            chosen = affordable.loc[affordable['actual_fppg'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            return {
                'players': selected_players,
                'total_salary': sum(p['Salary'] for p in selected_players),
                'total_projected': sum(p['FPPG'] for p in selected_players),
                'total_actual': sum(p['actual_fppg'] for p in selected_players),
                'lineup_type': 'OPTIMAL_HINDSIGHT'
            }
        
        return None
    
    def build_validated_projection_lineup(self, validated_slate):
        """Build lineup using validated projection approach (what we would have built)"""
        print("🎯 Building VALIDATED projection lineup (realistic approach)...")
        
        # Filter to validated players
        safe_players = validated_slate[
            (validated_slate['validation_score'] >= 70) &
            (validated_slate['FPPG'] > 1.0) &
            (validated_slate['Salary'] >= 2000)
        ].copy()
        
        if len(safe_players) < 50:
            print(f"⚠️ Only {len(safe_players)} validated players - may struggle")
        
        # Calculate enhanced value
        safe_players['enhanced_value'] = (
            safe_players['FPPG'] / (safe_players['Salary'] / 1000) *
            (safe_players['validation_score'] / 100)
        )
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = safe_players[~safe_players['Id'].isin(used_ids)]
            else:
                candidates = safe_players[
                    (safe_players['Roster Position'].str.contains(position, na=False)) &
                    (~safe_players['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"❌ No affordable validated {position} players")
                return None
            
            # Pick best enhanced value
            chosen = affordable.loc[affordable['enhanced_value'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            return {
                'players': selected_players,
                'total_salary': sum(p['Salary'] for p in selected_players),
                'total_projected': sum(p['FPPG'] for p in selected_players),
                'total_actual': sum(p['actual_fppg'] for p in selected_players),
                'lineup_type': 'VALIDATED_PROJECTION'
            }
        
        return None
    
    def build_filtered_lineup(self, validated_slate):
        """Build lineup using filtered approach (injury/probable pitcher filtering)"""
        print("🔧 Building FILTERED lineup (injury/probable pitcher filtered)...")
        
        # Apply slate-based filtering
        filtered_slate = validated_slate.copy()
        
        # Remove injured players
        if 'Injury Indicator' in filtered_slate.columns:
            injured_players = filtered_slate['Injury Indicator'].notna()
            injured_count = injured_players.sum()
            print(f"  Removing {injured_count} injured players")
            filtered_slate = filtered_slate[~injured_players]
        
        # Remove non-probable pitchers
        if 'Probable Pitcher' in filtered_slate.columns:
            pitchers = filtered_slate[filtered_slate['Position'] == 'P']
            non_probable = pitchers['Probable Pitcher'] != 'Yes'
            non_probable_ids = set(pitchers[non_probable]['Id'])
            filtered_slate = filtered_slate[~filtered_slate['Id'].isin(non_probable_ids)]
            print(f"  Keeping only {(pitchers['Probable Pitcher'] == 'Yes').sum()} probable pitchers")
        
        # Quality filter
        filtered_slate = filtered_slate[
            (filtered_slate['FPPG'] >= 2.0) &
            (filtered_slate['Salary'] >= 2000)
        ]
        
        print(f"  Working with {len(filtered_slate)} filtered players")
        
        if len(filtered_slate) < 50:
            print("❌ Not enough filtered players")
            return None
        
        # Calculate value
        filtered_slate['value'] = filtered_slate['FPPG'] / (filtered_slate['Salary'] / 1000)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = filtered_slate[~filtered_slate['Id'].isin(used_ids)]
            else:
                candidates = filtered_slate[
                    (filtered_slate['Roster Position'].str.contains(position, na=False)) &
                    (~filtered_slate['Id'].isin(used_ids))
                ]
            
            # Budget management
            positions_left = len(positions_needed) - len(selected_players) - 1
            min_budget_needed = positions_left * 2000
            max_spend = remaining_budget - min_budget_needed
            
            affordable = candidates[candidates['Salary'] <= max_spend]
            
            if affordable.empty:
                print(f"❌ No affordable filtered {position} players")
                return None
            
            # Pick best value
            chosen = affordable.loc[affordable['value'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            return {
                'players': selected_players,
                'total_salary': sum(p['Salary'] for p in selected_players),
                'total_projected': sum(p['FPPG'] for p in selected_players),
                'total_actual': sum(p['actual_fppg'] for p in selected_players),
                'lineup_type': 'FILTERED_SLATE'
            }
        
        return None

    def build_random_baseline_lineup(self, validated_slate):
        """Build random lineup for comparison baseline"""
        print("🎲 Building RANDOM baseline lineup (for comparison)...")
        
        available = validated_slate[
            (validated_slate['FPPG'] > 0) &
            (validated_slate['Salary'] >= 2000)
        ].copy()
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = available[~available['Id'].isin(used_ids)]
            else:
                candidates = available[
                    (available['Roster Position'].str.contains(position, na=False)) &
                    (~available['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                return None
            
            # Pick randomly
            chosen = affordable.sample(1).iloc[0]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            return {
                'players': selected_players,
                'total_salary': sum(p['Salary'] for p in selected_players),
                'total_projected': sum(p['FPPG'] for p in selected_players),
                'total_actual': sum(p['actual_fppg'] for p in selected_players),
                'lineup_type': 'RANDOM_BASELINE'
            }
        
        return None
    
    def analyze_backtest_performance(self, lineups):
        """Analyze and compare lineup performance"""
        if not lineups:
            print("❌ No lineups to analyze")
            return
        
        print("\n" + "="*70)
        print("🔍 DFS BACKTESTING RESULTS")
        print("="*70)
        
        performance_summary = {}
        
        for lineup in lineups:
            if not lineup:
                continue
                
            lineup_type = lineup['lineup_type']
            performance_summary[lineup_type] = {
                'salary': lineup['total_salary'],
                'projected': lineup['total_projected'],
                'actual': lineup['total_actual'],
                'accuracy': (lineup['total_actual'] / lineup['total_projected']) * 100 if lineup['total_projected'] > 0 else 0
            }
            
            print(f"\n📊 {lineup_type}:")
            print(f"  💰 Salary: ${lineup['total_salary']:,}")
            print(f"  📈 Projected: {lineup['total_projected']:.1f} FPPG")
            print(f"  🎯 Actual: {lineup['total_actual']:.1f} FPPG")
            print(f"  🎪 Accuracy: {performance_summary[lineup_type]['accuracy']:.1f}%")
            
            print(f"  👥 Players:")
            for player in lineup['players']:
                name = f"{player['First Name']} {player['Last Name']}"
                pos = player['Roster Position']
                salary = player['Salary']
                projected = player.get('FPPG', 0)
                actual = player.get('actual_fppg', 0)
                diff = actual - projected
                
                status = "🔥" if actual > projected * 1.2 else "✅" if actual >= projected * 0.8 else "❌"
                print(f"    {status} {name:20} ({pos:4}) ${salary:5,} | Proj: {projected:5.1f} | Actual: {actual:5.1f} | Diff: {diff:+5.1f}")
        
        # Performance comparison
        print(f"\n🏆 PERFORMANCE COMPARISON:")
        
        if 'OPTIMAL_HINDSIGHT' in performance_summary:
            optimal = performance_summary['OPTIMAL_HINDSIGHT']['actual']
            print(f"  🥇 Optimal (hindsight): {optimal:.1f} FPPG")
            
            # Compare all approaches to optimal
            for approach in ['FILTERED_SLATE', 'VALIDATED_PROJECTION', 'RANDOM_BASELINE']:
                if approach in performance_summary:
                    score = performance_summary[approach]['actual']
                    efficiency = (score / optimal) * 100 if optimal > 0 else 0
                    
                    if approach == 'FILTERED_SLATE':
                        print(f"  🔧 Filtered approach: {score:.1f} FPPG ({efficiency:.1f}% of optimal)")
                    elif approach == 'VALIDATED_PROJECTION':
                        print(f"  🎯 Old validation: {score:.1f} FPPG ({efficiency:.1f}% of optimal)")
                    elif approach == 'RANDOM_BASELINE':
                        print(f"  🎲 Random baseline: {score:.1f} FPPG ({efficiency:.1f}% of optimal)")
            
            # Best realistic approach
            realistic_scores = {}
            for approach in ['FILTERED_SLATE', 'VALIDATED_PROJECTION']:
                if approach in performance_summary:
                    realistic_scores[approach] = performance_summary[approach]['actual']
            
            if realistic_scores:
                best_approach = max(realistic_scores, key=realistic_scores.get)
                best_score = realistic_scores[best_approach]
                
                print(f"\n💪 BEST REALISTIC APPROACH:")
                if best_approach == 'FILTERED_SLATE':
                    print(f"  🏆 FILTERED SLATE: {best_score:.1f} FPPG")
                    print(f"      ✅ Uses injury indicators and probable pitchers")
                else:
                    print(f"  🏆 VALIDATED PROJECTION: {best_score:.1f} FPPG")
                    print(f"      ⚠️  Basic validation only")
                
                efficiency = (best_score / optimal) * 100 if optimal > 0 else 0
                if efficiency >= 80:
                    print(f"  ✅ EXCELLENT: {efficiency:.1f}% efficiency!")
                elif efficiency >= 60:
                    print(f"  ⚠️  GOOD: {efficiency:.1f}% efficiency")
                elif efficiency >= 30:
                    print(f"  ❌ FAIR: {efficiency:.1f}% efficiency - needs work")
                else:
                    print(f"  💥 POOR: {efficiency:.1f}% efficiency - major issues")
        
        return performance_summary
    
    def run_backtest(self):
        """Run complete DFS backtest with validation"""
        print("🚀 DFS BACKTESTING WITH VALIDATION")
        print("Testing how well our validation approach would have performed")
        print("="*70)
        
        # Load data
        slate_df, actual_df = self.load_yesterday_data()
        if slate_df is None:
            return
        
        if actual_df is not None:
            actual_df = self.calculate_actual_fppg(actual_df)
            enhanced_slate = self.merge_slate_with_actual(slate_df, actual_df)
        else:
            print("⚠️ No actual results - simulation mode only")
            enhanced_slate = slate_df.copy()
            enhanced_slate['actual_fppg'] = 0
        
        # Apply validation
        validated_slate = self.validate_backtest_slate(enhanced_slate)
        
        # Build different lineups
        lineups = []
        
        if actual_df is not None:
            # Optimal with hindsight
            optimal = self.build_optimal_hindsight_lineup(validated_slate)
            if optimal:
                lineups.append(optimal)
            
            # Random baseline
            random_lineup = self.build_random_baseline_lineup(validated_slate)
            if random_lineup:
                lineups.append(random_lineup)
        
        # Filtered approach (our new method)
        filtered = self.build_filtered_lineup(validated_slate)
        if filtered:
            lineups.append(filtered)
        
        # Validated projection approach (old method)
        validated = self.build_validated_projection_lineup(validated_slate)
        if validated:
            lineups.append(validated)
        
        # Analyze results
        if lineups:
            performance = self.analyze_backtest_performance(lineups)
            
            print(f"\n🎉 BACKTEST COMPLETE!")
            print(f"📈 Analyzed {len(lineups)} different approaches")
            
            if actual_df is not None:
                print(f"💡 KEY INSIGHT: Validation approach shows how well")
                print(f"   you could realistically perform vs perfect hindsight")
            else:
                print(f"💡 Ready to use validation approach on today's slate")
        else:
            print("❌ Failed to build lineups for backtest")

def main():
    print("📊 DFS BACKTESTING WITH VALIDATION")
    print("See how our validation system performs against actual results")
    print("="*70)
    
    backtester = DFSBacktestValidator()
    
    try:
        backtester.run_backtest()
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
