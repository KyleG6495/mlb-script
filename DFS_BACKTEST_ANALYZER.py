#!/usr/bin/env python3
"""
DFS LINEUP BACKTESTING SYSTEM
=============================
Test our DFS strategies against yesterday's actual results
to see how well we would have performed and optimize for higher scores.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class DFSBacktester:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_actual_results(self):
        """Load yesterday's actual fantasy results"""
        print("DATA: Loading yesterday's ACTUAL results...")
        
        actual_file = self.data_dir / "actual_results_latest.csv"
        if not actual_file.exists():
            print("ERROR: No actual results found - run collect_actual_results.py first")
            return None
            
        actual_df = pd.read_csv(actual_file)
        print(f"SUCCESS: Loaded {len(actual_df)} player results from yesterday")
        
        # Check date
        if 'date' in actual_df.columns:
            latest_date = actual_df['date'].max()
            print(f" Results from: {latest_date}")
        
        return actual_df
    
    def load_yesterday_slate(self):
        """Load the slate we would have used yesterday"""
        print("TARGET: Loading yesterday's slate data...")
        
        # For now, use current slate as proxy for yesterday's
        # In production, you'd save daily slates with timestamps
        slate_file = self.slate_dir / "fd_slate_today.csv"
        
        if not slate_file.exists():
            print("ERROR: No slate file found")
            return None
            
        slate_df = pd.read_csv(slate_file)
        print(f"SUCCESS: Loaded slate with {len(slate_df)} players")
        
        return slate_df
    
    def calculate_actual_fppg(self, actual_df):
        """Calculate actual FPPG from yesterday's results"""
        print(" Calculating actual FPPG scores...")
        
        actual_df = actual_df.copy()
        
        # FanDuel scoring system
        actual_df['calculated_fppg'] = (
            actual_df.get('at_bats', 0) * 0 +           # No points for AB
            actual_df.get('hits', 0) * 3 +              # 3 pts per hit
            actual_df.get('runs', 0) * 3.2 +            # 3.2 pts per run
            actual_df.get('rbis', 0) * 3.5 +            # 3.5 pts per RBI
            actual_df.get('home_runs', 0) * 12 +        # 12 pts per HR
            actual_df.get('stolen_bases', 0) * 6 +      # 6 pts per SB
            actual_df.get('walks', 0) * 3 +             # 3 pts per walk
            actual_df.get('doubles', 0) * 6 +           # 6 pts per double
            actual_df.get('triples', 0) * 12 +          # 12 pts per triple
            # Pitcher scoring
            actual_df.get('innings_pitched', 0) * 3.5 + # 3.5 pts per IP
            actual_df.get('wins', 0) * 12 +             # 12 pts per win
            actual_df.get('earned_runs', 0) * -3        # -3 pts per ER
        )
        
        # Use fanduel_points if available, otherwise calculated
        if 'fanduel_points' in actual_df.columns:
            actual_df['actual_fppg'] = actual_df['fanduel_points'].fillna(actual_df['calculated_fppg'])
        else:
            actual_df['actual_fppg'] = actual_df['calculated_fppg']
        
        print(f"PROGRESS: FPPG range: {actual_df['actual_fppg'].min():.1f} - {actual_df['actual_fppg'].max():.1f}")
        
        return actual_df
    
    def merge_slate_with_actual(self, slate_df, actual_df):
        """Merge slate projections with actual results"""
        print(" Merging slate projections with actual results...")
        
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
        
        matched = merged['actual_fppg'].notna().sum()
        print(f"SUCCESS: Matched {matched}/{len(slate_df)} players ({matched/len(slate_df)*100:.1f}%)")
        
        return merged
    
    def build_optimal_lineup_actual(self, enhanced_slate):
        """Build the OPTIMAL lineup using actual results (what we wish we built)"""
        print("LINEUP: Building OPTIMAL lineup with actual results...")
        
        # Filter players with actual results and salary info
        available = enhanced_slate[
            (enhanced_slate['actual_fppg'] > 0) & 
            (enhanced_slate['Salary'].notna()) &
            (enhanced_slate['Salary'] > 0)
        ].copy()
        
        if len(available) < 20:
            print(f"ERROR: Only {len(available)} players with actual results")
            return None
        
        # Simple greedy optimal selection
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = available[~available['Id'].isin(used_ids)]
            else:
                candidates = available[
                    (available['Roster Position'].str.contains(position)) &
                    (~available['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"ERROR: No affordable {position} players")
                return None
            
            # Pick highest actual FPPG
            chosen = affordable.loc[affordable['actual_fppg'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_actual = sum(p['actual_fppg'] for p in selected_players)
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_actual_fppg': total_actual,
                'lineup_type': 'OPTIMAL_ACTUAL'
            }
        
        return None
    
    def build_value_lineup_actual(self, enhanced_slate):
        """Build value-based lineup using actual results"""
        print("MONEY: Building VALUE lineup with actual results...")
        
        available = enhanced_slate[
            (enhanced_slate['actual_fppg'] >= 0) & 
            (enhanced_slate['Salary'].notna()) &
            (enhanced_slate['Salary'] > 0)
        ].copy()
        
        # Calculate value using actual results
        available['actual_value'] = available['actual_fppg'] / (available['Salary'] / 1000)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = available[~available['Id'].isin(used_ids)]
            else:
                candidates = available[
                    (available['Roster Position'].str.contains(position)) &
                    (~available['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"ERROR: No affordable {position} players")
                return None
            
            # Pick highest actual value
            if affordable['actual_value'].max() > 0:
                chosen = affordable.loc[affordable['actual_value'].idxmax()]
            else:
                chosen = affordable.loc[affordable['actual_fppg'].idxmax()]
                
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_actual = sum(p['actual_fppg'] for p in selected_players)
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_actual_fppg': total_actual,
                'lineup_type': 'VALUE_ACTUAL'
            }
        
        return None
    
    def build_projection_lineup(self, enhanced_slate):
        """Build lineup using original projections (what we actually would have built)"""
        print("TARGET: Building PROJECTION lineup (what we would have built)...")
        
        available = enhanced_slate[
            (enhanced_slate['FPPG'] > 2.0) & 
            (enhanced_slate['Salary'].notna())
        ].copy()
        
        available['proj_value'] = available['FPPG'] / (available['Salary'] / 1000)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = available[~available['Id'].isin(used_ids)]
            else:
                candidates = available[
                    (available['Roster Position'].str.contains(position)) &
                    (~available['Id'].isin(used_ids))
                ]
            
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"ERROR: No affordable {position} players")
                return None
            
            # Pick highest projected value
            chosen = affordable.loc[affordable['proj_value'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            total_actual = sum(p.get('actual_fppg', 0) for p in selected_players)
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_projected_fppg': total_projected,
                'total_actual_fppg': total_actual,
                'lineup_type': 'PROJECTION_BASED'
            }
        
        return None
    
    def analyze_backtest_results(self, lineups):
        """Analyze backtest performance"""
        if not lineups:
            print("ERROR: No lineups to analyze")
            return
        
        print("\n" + "="*60)
        print(" DFS BACKTEST ANALYSIS")
        print("="*60)
        
        for lineup in lineups:
            if not lineup:
                continue
                
            lineup_type = lineup['lineup_type']
            total_salary = lineup['total_salary']
            actual_fppg = lineup['total_actual_fppg']
            
            print(f"\nDATA: {lineup_type}:")
            print(f"  MONEY: Salary: ${total_salary:,}")
            print(f"  TARGET: Actual FPPG: {actual_fppg:.1f}")
            
            if 'total_projected_fppg' in lineup:
                proj_fppg = lineup['total_projected_fppg']
                accuracy = (actual_fppg / proj_fppg) * 100 if proj_fppg > 0 else 0
                print(f"  PROGRESS: Projected FPPG: {proj_fppg:.1f}")
                print(f"   Accuracy: {accuracy:.1f}%")
            
            print(f"  OWNERSHIP: Players:")
            for player in lineup['players']:
                name = f"{player['First Name']} {player['Last Name']}"
                pos = player['Roster Position']
                salary = player['Salary']
                projected = player.get('FPPG', 0)
                actual = player.get('actual_fppg', 0)
                print(f"    {name:20} ({pos:4}) ${salary:5,} | Proj: {projected:5.1f} | Actual: {actual:5.1f}")
        
        # Performance comparison
        if len(lineups) >= 2:
            print(f"\nLINEUP: PERFORMANCE COMPARISON:")
            optimal_actual = next((l['total_actual_fppg'] for l in lineups if l and l['lineup_type'] == 'OPTIMAL_ACTUAL'), 0)
            proj_actual = next((l['total_actual_fppg'] for l in lineups if l and l['lineup_type'] == 'PROJECTION_BASED'), 0)
            
            if optimal_actual > 0 and proj_actual > 0:
                gap = optimal_actual - proj_actual
                gap_pct = (gap / optimal_actual) * 100
                print(f"  TARGET: Optimal (hindsight): {optimal_actual:.1f} FPPG")
                print(f"  DATA: Our projection: {proj_actual:.1f} FPPG")
                print(f"   Gap: {gap:.1f} points ({gap_pct:.1f}%)")
                
                if gap_pct < 20:
                    print(f"  SUCCESS: GOOD: Less than 20% gap!")
                elif gap_pct < 35:
                    print(f"  WARNING:  OKAY: 20-35% gap - room for improvement")
                else:
                    print(f"  ERROR: POOR: 35%+ gap - projections need work")
    
    def run_backtest(self):
        """Run complete DFS backtest"""
        print("START: STARTING DFS BACKTEST ANALYSIS")
        print("="*50)
        
        # Load data
        actual_df = self.load_actual_results()
        if actual_df is None:
            return
        
        slate_df = self.load_yesterday_slate()
        if slate_df is None:
            return
        
        # Calculate actual FPPG
        actual_df = self.calculate_actual_fppg(actual_df)
        
        # Merge data
        enhanced_slate = self.merge_slate_with_actual(slate_df, actual_df)
        
        # Build different lineup strategies
        lineups = []
        
        optimal_lineup = self.build_optimal_lineup_actual(enhanced_slate)
        if optimal_lineup:
            lineups.append(optimal_lineup)
        
        value_lineup = self.build_value_lineup_actual(enhanced_slate)
        if value_lineup:
            lineups.append(value_lineup)
        
        projection_lineup = self.build_projection_lineup(enhanced_slate)
        if projection_lineup:
            lineups.append(projection_lineup)
        
        # Analyze results
        self.analyze_backtest_results(lineups)
        
        return lineups

def main():
    print("DATA: DFS LINEUP BACKTESTING SYSTEM")
    print("Testing our strategies against yesterday's actual results")
    print("="*60)
    
    backtester = DFSBacktester()
    
    try:
        lineups = backtester.run_backtest()
        
        if lineups:
            print(f"\nCOMPLETE: BACKTEST COMPLETE!")
            print(f"PROGRESS: Analyzed {len([l for l in lineups if l])} different lineup strategies")
            print(f"TIP: Use these insights to improve future DFS builds!")
        else:
            print("ERROR: Backtest failed - check data availability")
            
    except Exception as e:
        print(f"Error in backtest: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
