#!/usr/bin/env python3
"""
PRODUCTION DFS SYSTEM TESTER
============================
Test your actual production DFS systems against yesterday's results:
1. Run your real ENHANCED_ML_DFS_SYSTEM.py (what your .bat files use)
2. Run SLATE_BASED_FILTER.py (our new filtered approach)
3. Score both against actual results
4. See which system would have won
"""

import pandas as pd
import numpy as np
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class ProductionDFSTester:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.scripts_dir = Path(__file__).parent
        
    def load_actual_results(self):
        """Load actual results for scoring"""
        print("TARGET: Loading actual game results...")
        
        actual_file = self.data_dir / "actual_results_latest.csv"
        if not actual_file.exists():
            print("ERROR: No actual results found")
            return None
            
        actual_df = pd.read_csv(actual_file)
        print(f"SUCCESS: Loaded actual results for {len(actual_df)} players")
        
        if 'date' in actual_df.columns:
            latest_date = actual_df['date'].max()
            print(f" Results from: {latest_date}")
        
        return actual_df
    
    def calculate_actual_fppg(self, actual_df):
        """Calculate actual FPPG from game results"""
        print(" Calculating actual FPPG scores...")
        
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
        
        print(f"PROGRESS: Actual FPPG range: {actual_df['actual_fppg'].min():.1f} - {actual_df['actual_fppg'].max():.1f}")
        
        return actual_df
    
    def run_enhanced_ml_dfs_system(self):
        """Run your production Enhanced ML DFS system"""
        print("\nSTART: Running ENHANCED_ML_DFS_SYSTEM.py (your production system)...")
        
        try:
            # Run the enhanced ML DFS system
            result = subprocess.run([
                sys.executable, 'ENHANCED_ML_DFS_SYSTEM.py'
            ], 
            cwd=self.scripts_dir,
            capture_output=True, 
            text=True, 
            timeout=300
            )
            
            if result.returncode == 0:
                print("SUCCESS: Enhanced ML DFS system completed successfully")
                return True
            else:
                print(f"ERROR: Enhanced ML DFS system failed:")
                print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("ERROR: Enhanced ML DFS system timed out")
            return False
        except Exception as e:
            print(f"ERROR: Error running Enhanced ML DFS system: {e}")
            return False
    
    def run_slate_based_filter(self):
        """Run our new filtered approach"""
        print("\nSTEP: Running SLATE_BASED_FILTER.py (our new filtered approach)...")
        
        try:
            # Run the slate-based filter system
            result = subprocess.run([
                sys.executable, 'SLATE_BASED_FILTER.py'
            ], 
            cwd=self.scripts_dir,
            capture_output=True, 
            text=True, 
            timeout=300
            )
            
            if result.returncode == 0:
                print("SUCCESS: Slate-based filter system completed successfully")
                return True
            else:
                print(f"ERROR: Slate-based filter system failed:")
                print(f"Error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("ERROR: Slate-based filter system timed out")
            return False
        except Exception as e:
            print(f"ERROR: Error running slate-based filter system: {e}")
            return False
    
    def find_latest_lineup_files(self):
        """Find the latest generated lineup files"""
        print("\n Searching for generated lineup files...")
        
        lineup_files = {}
        
        # Look for Enhanced ML DFS outputs
        enhanced_patterns = [
            'enhanced_ml_dfs_lineups_*.csv',
            'fanduel_submission_*.csv',
            'ranked_lineups_*.csv'
        ]
        
        for pattern in enhanced_patterns:
            files = list(self.data_dir.glob(pattern))
            if files:
                # Get the most recent file
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                lineup_files[f'enhanced_{pattern.split("_")[0]}'] = latest_file
                print(f"SUCCESS: Found Enhanced ML output: {latest_file.name}")
        
        # Look for Filtered outputs
        filtered_patterns = [
            'filtered_dfs_lineup_*.csv',
            'slate_filtered_lineup_*.csv'
        ]
        
        for pattern in filtered_patterns:
            files = list(self.data_dir.glob(pattern))
            if files:
                latest_file = max(files, key=lambda f: f.stat().st_mtime)
                lineup_files[f'filtered_{pattern.split("_")[0]}'] = latest_file
                print(f"SUCCESS: Found Filtered output: {latest_file.name}")
        
        return lineup_files
    
    def load_and_score_lineup(self, lineup_file, system_name, actual_df):
        """Load a lineup file and score it against actual results"""
        print(f"\nDATA: Scoring {system_name} lineup...")
        
        try:
            lineup_df = pd.read_csv(lineup_file)
            print(f"SUCCESS: Loaded lineup with {len(lineup_df)} players")
            
            # Create name lookup for actual results
            actual_df['full_name'] = actual_df['name'].str.lower().str.strip()
            actual_lookup = dict(zip(actual_df['full_name'], actual_df['actual_fppg']))
            
            total_actual = 0
            total_projected = 0
            total_salary = 0
            scored_players = []
            points_scorers = 0
            
            for _, player in lineup_df.iterrows():
                # Try different name formats
                if 'Name' in player:
                    player_name = player['Name'].lower().strip()
                elif 'Player' in player:
                    player_name = player['Player'].lower().strip()
                else:
                    # Try to construct name from first/last
                    first_name = player.get('First Name', player.get('first_name', ''))
                    last_name = player.get('Last Name', player.get('last_name', ''))
                    player_name = f"{first_name} {last_name}".lower().strip()
                
                actual_fppg = actual_lookup.get(player_name, 0)
                projected_fppg = player.get('FPPG', player.get('fppg', player.get('Projected', 0)))
                salary = player.get('Salary', player.get('salary', 0))
                position = player.get('Position', player.get('position', player.get('Roster Position', '')))
                
                total_actual += actual_fppg
                total_projected += projected_fppg
                total_salary += salary
                
                if actual_fppg > 0:
                    points_scorers += 1
                
                scored_players.append({
                    'name': player_name.title(),
                    'position': position,
                    'salary': salary,
                    'projected': projected_fppg,
                    'actual': actual_fppg,
                    'diff': actual_fppg - projected_fppg
                })
            
            return {
                'system': system_name,
                'file': lineup_file.name,
                'players': scored_players,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'total_actual': total_actual,
                'accuracy': (total_actual / total_projected) * 100 if total_projected > 0 else 0,
                'points_scorers': points_scorers
            }
            
        except Exception as e:
            print(f"ERROR: Error scoring {system_name} lineup: {e}")
            return None
    
    def analyze_system_results(self, results):
        """Analyze and compare system results"""
        print("\n" + "="*70)
        print("LINEUP: PRODUCTION SYSTEM PERFORMANCE ANALYSIS")
        print("="*70)
        
        for result in results:
            if not result:
                continue
                
            print(f"\nDATA: {result['system'].upper()}:")
            print(f"   File: {result['file']}")
            print(f"  MONEY: Salary: ${result['total_salary']:,}")
            print(f"  PROGRESS: Projected: {result['total_projected']:.1f} FPPG")
            print(f"  TARGET: Actual: {result['total_actual']:.1f} FPPG")
            print(f"   Accuracy: {result['accuracy']:.1f}%")
            print(f"  OWNERSHIP: Players who scored: {result['points_scorers']}/9")
            
            print(f"  TARGET: Top Performers:")
            # Show top 3 performers
            top_performers = sorted(result['players'], key=lambda x: x['actual'], reverse=True)[:3]
            for i, player in enumerate(top_performers, 1):
                status = "" if player['actual'] > 0 else "ERROR:"
                print(f"    {i}. {status} {player['name']:20} {player['actual']:5.1f} FPPG")
        
        # Performance comparison
        if len(results) >= 2:
            enhanced_result = next((r for r in results if 'enhanced' in r['system'].lower()), None)
            filtered_result = next((r for r in results if 'filtered' in r['system'].lower()), None)
            
            if enhanced_result and filtered_result:
                improvement = ((filtered_result['total_actual'] - enhanced_result['total_actual']) / enhanced_result['total_actual']) * 100 if enhanced_result['total_actual'] > 0 else 0
                
                print(f"\nSTART: SYSTEM COMPARISON:")
                print(f"  START: Enhanced ML System: {enhanced_result['total_actual']:.1f} FPPG")
                print(f"  STEP: Filtered System: {filtered_result['total_actual']:.1f} FPPG")
                print(f"  PROGRESS: Performance Gap: {improvement:+.1f}%")
                
                if improvement > 50:
                    print(f"  COMPLETE: FILTERED SYSTEM DOMINATES! {improvement:.0f}% better!")
                elif improvement > 10:
                    print(f"  SUCCESS: FILTERED SYSTEM WINS! {improvement:.0f}% better!")
                elif improvement > 0:
                    print(f"   FILTERED SYSTEM EDGE! {improvement:.0f}% better!")
                elif improvement > -10:
                    print(f"   SYSTEMS ARE CLOSE! Within {abs(improvement):.0f}%")
                else:
                    print(f"  WARNING:  ENHANCED SYSTEM WINS! {abs(improvement):.0f}% better")
                
                print(f"\nTIP: RECOMMENDATION:")
                if improvement > 20:
                    print(f"  TARGET: USE FILTERED SYSTEM - Significantly better results!")
                elif improvement > 0:
                    print(f"  STEP: SLIGHT EDGE TO FILTERED SYSTEM")
                else:
                    print(f"  START: ENHANCED SYSTEM PERFORMED BETTER THIS TIME")
    
    def run_production_test(self):
        """Run complete production system test"""
        print(" PRODUCTION DFS SYSTEM TESTER")
        print("Testing your real production systems against actual results")
        print("="*70)
        
        # Load actual results first
        actual_df = self.load_actual_results()
        if actual_df is None:
            print("ERROR: Cannot run test without actual results")
            return
        
        actual_df = self.calculate_actual_fppg(actual_df)
        
        # Run both systems
        print("\nTARGET: RUNNING PRODUCTION DFS SYSTEMS...")
        enhanced_success = self.run_enhanced_ml_dfs_system()
        filtered_success = self.run_slate_based_filter()
        
        if not enhanced_success and not filtered_success:
            print("ERROR: Both systems failed to run")
            return
        
        # Find and score lineup files
        lineup_files = self.find_latest_lineup_files()
        
        if not lineup_files:
            print("ERROR: No lineup files found")
            return
        
        # Score all found lineups
        results = []
        for system_name, lineup_file in lineup_files.items():
            result = self.load_and_score_lineup(lineup_file, system_name, actual_df)
            if result:
                results.append(result)
        
        # Analyze results
        if results:
            self.analyze_system_results(results)
            
            print(f"\nCOMPLETE: PRODUCTION TEST COMPLETE!")
            print(f"PROGRESS: This shows how your real systems would have performed")
        else:
            print("ERROR: Failed to score any lineups")

def main():
    print(" PRODUCTION DFS SYSTEM TESTER")
    print("Run your real DFS systems and score against actual results")
    print("="*70)
    
    tester = ProductionDFSTester()
    
    try:
        tester.run_production_test()
    except Exception as e:
        print(f"Error in production test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
