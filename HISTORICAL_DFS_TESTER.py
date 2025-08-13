#!/usr/bin/env python3
"""
HISTORICAL DFS LINEUP TESTER
============================
1. Generate lineups using yesterday's slate (no hindsight)
2. Check those lineups against actual results
3. See what would have really happened
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class HistoricalDFSTester:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_historical_slate(self):
        """Load yesterday's slate (what we would have seen)"""
        print("📊 Loading yesterday's slate data (pre-game)...")
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        if not slate_file.exists():
            print("❌ No slate file found")
            return None
            
        slate_df = pd.read_csv(slate_file)
        print(f"✅ Loaded slate with {len(slate_df)} available players")
        
        return slate_df
    
    def load_actual_results(self):
        """Load actual results (what happened after games)"""
        print("🎯 Loading actual game results...")
        
        actual_file = self.data_dir / "actual_results_latest.csv"
        if not actual_file.exists():
            print("❌ No actual results found")
            return None
            
        actual_df = pd.read_csv(actual_file)
        print(f"✅ Loaded actual results for {len(actual_df)} players")
        
        if 'date' in actual_df.columns:
            latest_date = actual_df['date'].max()
            print(f"📅 Results from: {latest_date}")
        
        return actual_df
    
    def calculate_actual_fppg(self, actual_df):
        """Calculate actual FPPG from game results"""
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
    
    def generate_old_system_lineup(self, slate_df):
        """Generate lineup using OLD system (basic validation only)"""
        print("🎯 Generating lineup using OLD validation system...")
        
        # Basic validation only (what we used to do)
        safe_players = slate_df[
            (slate_df['FPPG'] > 1.0) &
            (slate_df['Salary'] >= 2000)
        ].copy()
        
        # Calculate basic value
        safe_players['value'] = safe_players['FPPG'] / (safe_players['Salary'] / 1000)
        
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
                print(f"❌ No affordable {position} players")
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
                'system': 'OLD_VALIDATION'
            }
        
        return None
    
    def generate_filtered_system_lineup(self, slate_df):
        """Generate lineup using NEW filtered system (injury/probable pitcher filtering)"""
        print("🔧 Generating lineup using NEW filtered system...")
        
        # Apply slate-based filtering (our new approach)
        filtered_slate = slate_df.copy()
        
        # Remove injured players
        if 'Injury Indicator' in filtered_slate.columns:
            injured_players = filtered_slate['Injury Indicator'].notna()
            injured_count = injured_players.sum()
            print(f"  🚨 Filtering out {injured_count} injured players")
            filtered_slate = filtered_slate[~injured_players]
        
        # Remove non-probable pitchers
        if 'Probable Pitcher' in filtered_slate.columns:
            pitchers = filtered_slate[filtered_slate['Position'] == 'P']
            non_probable = pitchers['Probable Pitcher'] != 'Yes'
            non_probable_ids = set(pitchers[non_probable]['Id'])
            filtered_slate = filtered_slate[~filtered_slate['Id'].isin(non_probable_ids)]
            print(f"  🎯 Keeping only {(pitchers['Probable Pitcher'] == 'Yes').sum()} probable pitchers")
        
        # Quality filter
        filtered_slate = filtered_slate[
            (filtered_slate['FPPG'] >= 2.0) &
            (filtered_slate['Salary'] >= 2000)
        ]
        
        print(f"  ✅ Working with {len(filtered_slate)} filtered players")
        
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
                'system': 'FILTERED_APPROACH'
            }
        
        return None
    
    def score_lineup_against_actuals(self, lineup, actual_df):
        """Score a generated lineup against actual results"""
        if not lineup:
            return None
        
        print(f"\n📊 Scoring {lineup['system']} lineup against actual results...")
        
        # Create name lookup for actual results
        actual_df['full_name'] = actual_df['name'].str.lower().str.strip()
        actual_lookup = dict(zip(actual_df['full_name'], actual_df['actual_fppg']))
        
        total_actual = 0
        scored_players = []
        
        for player in lineup['players']:
            player_name = f"{player['First Name']} {player['Last Name']}".lower().strip()
            actual_fppg = actual_lookup.get(player_name, 0)
            total_actual += actual_fppg
            
            scored_players.append({
                'name': f"{player['First Name']} {player['Last Name']}",
                'position': player['Roster Position'],
                'salary': player['Salary'],
                'projected': player['FPPG'],
                'actual': actual_fppg,
                'diff': actual_fppg - player['FPPG']
            })
        
        return {
            'system': lineup['system'],
            'players': scored_players,
            'total_salary': lineup['total_salary'],
            'total_projected': lineup['total_projected'],
            'total_actual': total_actual,
            'accuracy': (total_actual / lineup['total_projected']) * 100 if lineup['total_projected'] > 0 else 0
        }
    
    def analyze_lineup_results(self, results):
        """Analyze and compare lineup results"""
        print("\n" + "="*70)
        print("🏆 HISTORICAL LINEUP PERFORMANCE ANALYSIS")
        print("="*70)
        
        for result in results:
            if not result:
                continue
                
            print(f"\n📊 {result['system']}:")
            print(f"  💰 Salary: ${result['total_salary']:,}")
            print(f"  📈 Projected: {result['total_projected']:.1f} FPPG")
            print(f"  🎯 Actual: {result['total_actual']:.1f} FPPG")
            print(f"  🎪 Accuracy: {result['accuracy']:.1f}%")
            
            print(f"  👥 Players:")
            points_scored = 0
            for player in result['players']:
                status = "🔥" if player['actual'] > player['projected'] * 1.2 else "✅" if player['actual'] >= player['projected'] * 0.8 else "❌"
                if player['actual'] > 0:
                    points_scored += 1
                print(f"    {status} {player['name']:20} ({player['position']:4}) ${player['salary']:5,} | Proj: {player['projected']:5.1f} | Actual: {player['actual']:5.1f} | Diff: {player['diff']:+5.1f}")
            
            print(f"  📊 Players who scored points: {points_scored}/9")
        
        # Performance comparison
        if len(results) >= 2:
            old_result = next((r for r in results if r['system'] == 'OLD_VALIDATION'), None)
            new_result = next((r for r in results if r['system'] == 'FILTERED_APPROACH'), None)
            
            if old_result and new_result:
                improvement = ((new_result['total_actual'] - old_result['total_actual']) / old_result['total_actual']) * 100 if old_result['total_actual'] > 0 else 0
                
                print(f"\n🚀 PERFORMANCE COMPARISON:")
                print(f"  🎯 Old System: {old_result['total_actual']:.1f} FPPG")
                print(f"  🔧 New Filtered: {new_result['total_actual']:.1f} FPPG")
                print(f"  📈 Improvement: {improvement:+.1f}%")
                
                if improvement > 100:
                    print(f"  🎉 MASSIVE IMPROVEMENT! New system is {improvement:.0f}% better!")
                elif improvement > 50:
                    print(f"  ✅ SIGNIFICANT IMPROVEMENT! New system is {improvement:.0f}% better!")
                elif improvement > 0:
                    print(f"  ⚡ IMPROVEMENT! New system is {improvement:.0f}% better!")
                else:
                    print(f"  ⚠️  Old system performed better this time")
    
    def run_historical_test(self):
        """Run complete historical test"""
        print("🕐 HISTORICAL DFS LINEUP TEST")
        print("Testing what would have happened with different systems")
        print("="*70)
        
        # Step 1: Load yesterday's slate (what we would have seen)
        slate_df = self.load_historical_slate()
        if slate_df is None:
            return
        
        # Step 2: Generate lineups using different systems (no hindsight)
        print("\n🎯 GENERATING LINEUPS (No hindsight - just slate data)...")
        old_lineup = self.generate_old_system_lineup(slate_df)
        new_lineup = self.generate_filtered_system_lineup(slate_df)
        
        # Step 3: Load actual results
        actual_df = self.load_actual_results()
        if actual_df is None:
            print("❌ Cannot score lineups without actual results")
            return
        
        actual_df = self.calculate_actual_fppg(actual_df)
        
        # Step 4: Score the lineups against actual results
        print("\n🎯 SCORING LINEUPS AGAINST ACTUAL RESULTS...")
        results = []
        
        if old_lineup:
            old_result = self.score_lineup_against_actuals(old_lineup, actual_df)
            if old_result:
                results.append(old_result)
        
        if new_lineup:
            new_result = self.score_lineup_against_actuals(new_lineup, actual_df)
            if new_result:
                results.append(new_result)
        
        # Step 5: Analyze results
        if results:
            self.analyze_lineup_results(results)
            
            print(f"\n🎉 HISTORICAL TEST COMPLETE!")
            print(f"📈 This shows what ACTUALLY would have happened")
            print(f"💡 Generated lineups first, then scored against real results")
        else:
            print("❌ Failed to generate any lineups")

def main():
    print("🕐 HISTORICAL DFS LINEUP TESTER")
    print("Generate lineups first, then check against actual results")
    print("="*70)
    
    tester = HistoricalDFSTester()
    
    try:
        tester.run_historical_test()
    except Exception as e:
        print(f"Error in historical test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
