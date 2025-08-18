#!/usr/bin/env python3
"""
ML-ENHANCED TOURNAMENT SYSTEM
============================
Combine machine learning projections with tournament optimization.
Use ML models to enhance projections, then build optimal tournament lineups.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class MLEnhancedTournamentSystem:
    def __init__(self):
        self.scripts_dir = Path(__file__).parent
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def run_ml_prediction_pipeline(self):
        """Run the ML prediction pipeline to get enhanced projections"""
        print(" ML-ENHANCED TOURNAMENT SYSTEM")
        print("Running machine learning predictions + tournament optimization")
        print("="*80)
        
        print(f"\n STEP 1: MACHINE LEARNING PREDICTIONS")
        print("Running ML models to enhance player projections...")
        
        # Import and run ML prediction steps
        try:
            # Run hitter ML projections
            print(f"   Running hitter ML projections...")
            import subprocess
            import sys
            
            result = subprocess.run([
                sys.executable, str(self.scripts_dir / "(23)project_base_hitter_scores.py")
            ], capture_output=True, text=True, cwd=str(self.scripts_dir))
            
            if result.returncode == 0:
                print(f"  SUCCESS: Hitter ML projections complete")
            else:
                print(f"  WARNING: Hitter ML warning: {result.stderr[:200]}")
            
            # Run pitcher ML projections  
            print(f"  BASEBALL: Running pitcher ML projections...")
            result = subprocess.run([
                sys.executable, str(self.scripts_dir / "(24)project_base_pitcher_scores.py")
            ], capture_output=True, text=True, cwd=str(self.scripts_dir))
            
            if result.returncode == 0:
                print(f"  SUCCESS: Pitcher ML projections complete")
            else:
                print(f"  WARNING: Pitcher ML warning: {result.stderr[:200]}")
            
            # Run enhanced projections
            print(f"  START: Running enhanced ML projections...")
            result = subprocess.run([
                sys.executable, str(self.scripts_dir / "(26)project_hitter_scores.py")
            ], capture_output=True, text=True, cwd=str(self.scripts_dir))
            
            if result.returncode == 0:
                print(f"  SUCCESS: Enhanced hitter projections complete")
            else:
                print(f"  WARNING: Enhanced hitter warning: {result.stderr[:200]}")
            
            result = subprocess.run([
                sys.executable, str(self.scripts_dir / "(27)project_pitcher_scores.py")
            ], capture_output=True, text=True, cwd=str(self.scripts_dir))
            
            if result.returncode == 0:
                print(f"  SUCCESS: Enhanced pitcher projections complete")
            else:
                print(f"  WARNING: Enhanced pitcher warning: {result.stderr[:200]}")
            
            print(f"  TARGET: ML prediction pipeline complete!")
            return True
            
        except Exception as e:
            print(f"  ERROR: Error in ML pipeline: {e}")
            return False
    
    def load_ml_projections(self):
        """Load the ML-generated projections"""
        print(f"\nDATA: STEP 2: LOADING ML PROJECTIONS")
        
        try:
            # Look for ML projection files
            hitter_files = list(self.data_dir.glob("*hitter*projection*.csv"))
            pitcher_files = list(self.data_dir.glob("*pitcher*projection*.csv"))
            
            print(f"   Found {len(hitter_files)} hitter projection files")
            print(f"   Found {len(pitcher_files)} pitcher projection files")
            
            # Load most recent projections
            if hitter_files:
                hitter_file = max(hitter_files, key=lambda x: x.stat().st_mtime)
                hitter_projections = pd.read_csv(hitter_file)
                print(f"  SUCCESS: Loaded hitter projections: {len(hitter_projections)} players from {hitter_file.name}")
            else:
                print(f"  WARNING: No hitter projection files found")
                hitter_projections = None
            
            if pitcher_files:
                pitcher_file = max(pitcher_files, key=lambda x: x.stat().st_mtime)
                pitcher_projections = pd.read_csv(pitcher_file)
                print(f"  SUCCESS: Loaded pitcher projections: {len(pitcher_projections)} players from {pitcher_file.name}")
            else:
                print(f"  WARNING: No pitcher projection files found")
                pitcher_projections = None
            
            return hitter_projections, pitcher_projections
            
        except Exception as e:
            print(f"  ERROR: Error loading ML projections: {e}")
            return None, None
    
    def enhance_slate_with_ml(self, hitter_projections, pitcher_projections):
        """Enhance FanDuel slate with ML projections"""
        print(f"\n STEP 3: ENHANCING SLATE WITH ML PROJECTIONS")
        
        # Load FanDuel slate
        slate_file = self.slate_dir / "fd_slate_today.csv"
        if not slate_file.exists():
            print(f"  ERROR: FanDuel slate not found: {slate_file}")
            return None
        
        slate = pd.read_csv(slate_file)
        print(f"  DATA: FanDuel slate loaded: {len(slate)} players")
        
        # Create enhanced slate
        enhanced_slate = slate.copy()
        
        # Add ML projections for hitters
        if hitter_projections is not None:
            # Merge hitter projections
            hitter_slate = enhanced_slate[enhanced_slate['Position'] != 'P'].copy()
            
            # Try different merge strategies
            merge_columns = []
            if 'Name' in hitter_projections.columns:
                merge_columns.append('Name')
            if 'Player' in hitter_projections.columns:
                merge_columns.append('Player')
            if 'player_name' in hitter_projections.columns:
                merge_columns.append('player_name')
            
            if merge_columns:
                # Create full name for slate
                hitter_slate['Full_Name'] = hitter_slate['First Name'] + ' ' + hitter_slate['Last Name']
                
                # Try merging with each available name column
                merged_hitters = None
                for col in merge_columns:
                    try:
                        temp_merge = hitter_slate.merge(
                            hitter_projections, 
                            left_on='Full_Name', 
                            right_on=col, 
                            how='left'
                        )
                        if temp_merge['ML_Projection'].notna().sum() > 0:  # If we got matches
                            merged_hitters = temp_merge
                            print(f"  SUCCESS: Hitter ML merge successful with {col}: {temp_merge['ML_Projection'].notna().sum()} matches")
                            break
                    except:
                        continue
                
                if merged_hitters is not None:
                    # Update FPPG with ML projections where available
                    merged_hitters['Original_FPPG'] = merged_hitters['FPPG']
                    merged_hitters['FPPG'] = np.where(
                        merged_hitters['ML_Projection'].notna(),
                        merged_hitters['ML_Projection'],
                        merged_hitters['FPPG']
                    )
                    
                    # Update enhanced slate
                    enhanced_slate.loc[enhanced_slate['Position'] != 'P'] = merged_hitters
                else:
                    print(f"  WARNING: Could not merge hitter projections")
            else:
                print(f"  WARNING: No suitable name column found in hitter projections")
        
        # Add ML projections for pitchers
        if pitcher_projections is not None:
            # Similar process for pitchers
            pitcher_slate = enhanced_slate[enhanced_slate['Position'] == 'P'].copy()
            
            merge_columns = []
            if 'Name' in pitcher_projections.columns:
                merge_columns.append('Name')
            if 'Player' in pitcher_projections.columns:
                merge_columns.append('Player')
            if 'player_name' in pitcher_projections.columns:
                merge_columns.append('player_name')
            
            if merge_columns:
                pitcher_slate['Full_Name'] = pitcher_slate['First Name'] + ' ' + pitcher_slate['Last Name']
                
                merged_pitchers = None
                for col in merge_columns:
                    try:
                        temp_merge = pitcher_slate.merge(
                            pitcher_projections,
                            left_on='Full_Name',
                            right_on=col,
                            how='left'
                        )
                        if temp_merge['ML_Projection'].notna().sum() > 0:
                            merged_pitchers = temp_merge
                            print(f"  SUCCESS: Pitcher ML merge successful with {col}: {temp_merge['ML_Projection'].notna().sum()} matches")
                            break
                    except:
                        continue
                
                if merged_pitchers is not None:
                    merged_pitchers['Original_FPPG'] = merged_pitchers['FPPG']
                    merged_pitchers['FPPG'] = np.where(
                        merged_pitchers['ML_Projection'].notna(),
                        merged_pitchers['ML_Projection'],
                        merged_pitchers['FPPG']
                    )
                    
                    enhanced_slate.loc[enhanced_slate['Position'] == 'P'] = merged_pitchers
                else:
                    print(f"  WARNING: Could not merge pitcher projections")
            else:
                print(f"  WARNING: No suitable name column found in pitcher projections")
        
        # Summary of ML enhancement
        ml_enhanced_count = 0
        if 'Original_FPPG' in enhanced_slate.columns:
            ml_enhanced_count = (enhanced_slate['FPPG'] != enhanced_slate['Original_FPPG']).sum()
        
        print(f"  TARGET: ML Enhancement Summary:")
        print(f"    DATA: Total players: {len(enhanced_slate)}")
        print(f"     ML-enhanced projections: {ml_enhanced_count}")
        print(f"    PROGRESS: Enhancement rate: {ml_enhanced_count/len(enhanced_slate)*100:.1f}%")
        
        return enhanced_slate
    
    def run_ml_tournament_optimization(self, enhanced_slate):
        """Run tournament optimization with ML-enhanced projections"""
        print(f"\nLINEUP: STEP 4: ML-ENHANCED TOURNAMENT OPTIMIZATION")
        
        # Filter to viable players
        viable_slate = enhanced_slate[
            (enhanced_slate['Injury Indicator'].isna()) &
            (enhanced_slate['FPPG'] > 0.1)
        ].copy()
        
        # Filter pitchers to probable starters
        pitchers = viable_slate[
            (viable_slate['Position'] == 'P') &
            (viable_slate['Probable Pitcher'] == 'Yes') &
            (viable_slate['FPPG'] >= 15.0)
        ].copy()
        
        hitters = viable_slate[viable_slate['Position'] != 'P'].copy()
        
        ml_slate = pd.concat([pitchers, hitters], ignore_index=True)
        
        print(f"  DATA: ML-Enhanced Tournament Slate:")
        print(f"    TARGET: Total viable players: {len(ml_slate)}")
        print(f"    BASEBALL: Elite pitchers: {len(pitchers)}")
        print(f"     Viable hitters: {len(hitters)}")
        
        if 'Original_FPPG' in ml_slate.columns:
            ml_improved = ml_slate[ml_slate['FPPG'] > ml_slate['Original_FPPG']]
            print(f"    PROGRESS: Players with ML improvement: {len(ml_improved)}")
            if len(ml_improved) > 0:
                avg_improvement = (ml_improved['FPPG'] - ml_improved['Original_FPPG']).mean()
                print(f"    START: Average ML improvement: +{avg_improvement:.2f} FPPG")
        
        return ml_slate
    
    def build_ml_tournament_lineups(self, ml_slate, count=15):
        """Build tournament lineups using ML-enhanced slate"""
        print(f"\n STEP 5: BUILDING ML-ENHANCED LINEUPS")
        print(f"Generating {count} lineups with ML projections")
        
        # Enhanced metrics with ML consideration
        ml_slate = ml_slate.copy()
        ml_slate['value_score'] = ml_slate['FPPG'] / (ml_slate['Salary'] / 1000)
        ml_slate['ml_ceiling'] = ml_slate['FPPG'] * np.where(ml_slate['Position'] == 'P', 1.6, 1.9)
        
        # ML confidence bonus
        if 'Original_FPPG' in ml_slate.columns:
            ml_slate['ml_confidence'] = np.where(
                ml_slate['FPPG'] > ml_slate['Original_FPPG'], 0.1, 0
            )
        else:
            ml_slate['ml_confidence'] = 0
        
        lineups = []
        
        # Generate diverse ML lineups
        strategies = [
            {'name': 'ML_Premium', 'pitcher_tier': 'premium', 'ml_focus': True},
            {'name': 'ML_Value', 'pitcher_tier': 'value', 'ml_focus': True},
            {'name': 'ML_Balanced', 'pitcher_tier': 'balanced', 'ml_focus': True},
            {'name': 'ML_Ceiling', 'pitcher_tier': 'premium', 'ml_focus': False},
            {'name': 'ML_Stack', 'pitcher_tier': 'balanced', 'ml_focus': True}
        ]
        
        for i in range(count):
            strategy = strategies[i % len(strategies)]
            lineup = self.build_single_ml_lineup(ml_slate, strategy, i)
            
            if lineup:
                lineup['lineup_id'] = f"ML_{i+1:02d}"
                lineups.append(lineup)
                print(f"  SUCCESS: {lineup['lineup_id']} ({lineup['strategy']}): ${lineup['total_salary']:,} | {lineup['total_projected']:.1f} proj | {lineup['ml_ceiling']:.1f} ceil")
            else:
                print(f"  ERROR: Failed ML lineup {i+1}")
        
        return lineups
    
    def build_single_ml_lineup(self, ml_slate, strategy_config, iteration):
        """Build single ML-enhanced lineup"""
        
        strategy_name = strategy_config['name']
        pitcher_tier = strategy_config['pitcher_tier']
        ml_focus = strategy_config.get('ml_focus', True)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        # Select pitcher
        pitchers = ml_slate[ml_slate['Position'] == 'P']
        
        if pitcher_tier == 'premium':
            target_pitchers = pitchers[pitchers['Salary'] >= 8500]
            if target_pitchers.empty:
                target_pitchers = pitchers.nlargest(3, 'FPPG')
        elif pitcher_tier == 'value':
            target_pitchers = pitchers[pitchers['Salary'] <= 8000]
            if target_pitchers.empty:
                target_pitchers = pitchers.nsmallest(3, 'Salary')
        else:  # balanced
            target_pitchers = pitchers[
                (pitchers['Salary'] >= 7000) & 
                (pitchers['Salary'] <= 9500)
            ]
            if target_pitchers.empty:
                target_pitchers = pitchers
        
        # ML-enhanced selection
        if ml_focus and 'ml_confidence' in target_pitchers.columns:
            target_pitchers['selection_score'] = (
                target_pitchers['FPPG'] * 0.6 +
                target_pitchers['value_score'] * 0.2 +
                target_pitchers['ml_confidence'] * 10  # Boost ML-improved players
            )
        else:
            target_pitchers['selection_score'] = target_pitchers['FPPG']
        
        chosen_pitcher = target_pitchers.loc[target_pitchers['selection_score'].idxmax()]
        selected_players.append(chosen_pitcher)
        remaining_budget -= chosen_pitcher['Salary']
        used_ids.add(chosen_pitcher['Id'])
        
        # Fill hitter positions
        positions_needed = 8
        
        for i in range(positions_needed):
            hitter_candidates = ml_slate[
                (~ml_slate['Id'].isin(used_ids)) &
                (ml_slate['Position'] != 'P')
            ]
            
            positions_left = positions_needed - i
            if positions_left > 1:
                max_spend = (remaining_budget - (positions_left-1) * 2000)
            else:
                max_spend = remaining_budget
            
            affordable = hitter_candidates[
                (hitter_candidates['Salary'] <= max_spend) &
                (hitter_candidates['Salary'] >= 2000)
            ]
            
            if affordable.empty:
                return None
            
            # ML-enhanced hitter selection
            if ml_focus and 'ml_confidence' in affordable.columns:
                affordable['hitter_score'] = (
                    affordable['FPPG'] * 0.5 +
                    affordable['value_score'] * 0.3 +
                    affordable['ml_ceiling'] * 0.1 +
                    affordable['ml_confidence'] * 5  # ML improvement bonus
                )
            else:
                affordable['hitter_score'] = (
                    affordable['FPPG'] * 0.6 +
                    affordable['value_score'] * 0.4
                )
            
            # Add some randomness for diversity
            if iteration > 0:
                affordable['hitter_score'] += np.random.uniform(-0.5, 0.5, len(affordable))
            
            chosen = affordable.loc[affordable['hitter_score'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_projected = sum(p['FPPG'] for p in selected_players)
            ml_ceiling = sum(p['ml_ceiling'] for p in selected_players)
            
            return {
                'players': selected_players,
                'strategy': strategy_name,
                'total_salary': total_salary,
                'total_projected': total_projected,
                'ml_ceiling': ml_ceiling
            }
        
        return None
    
    def export_ml_lineups(self, lineups):
        """Export ML-enhanced lineups"""
        if not lineups:
            print("ERROR: No ML lineups to export")
            return
        
        print(f"\n EXPORTING {len(lineups)} ML-ENHANCED LINEUPS...")
        
        # Prepare export data
        export_data = []
        
        for lineup in lineups:
            row = {
                'Lineup_ID': lineup['lineup_id'],
                'Strategy': lineup['strategy'],
                'Total_Salary': lineup['total_salary'],
                'ML_Projected_FPPG': lineup['total_projected'],
                'ML_Ceiling_FPPG': lineup['ml_ceiling'],
                'ML_Upside_Ratio': lineup['ml_ceiling'] / lineup['total_projected']
            }
            
            # Map players to positions
            positions_filled = {}
            
            for player in lineup['players']:
                name = f"{player['First Name']} {player['Last Name']}"
                
                if player['Position'] == 'P':
                    row['P'] = name
                else:
                    roster_pos = player['Roster Position']
                    
                    if 'C' in roster_pos and 'C' not in positions_filled:
                        row['C'] = name
                        positions_filled['C'] = True
                    elif '1B' in roster_pos and '1B' not in positions_filled:
                        row['1B'] = name
                        positions_filled['1B'] = True
                    elif '2B' in roster_pos and '2B' not in positions_filled:
                        row['2B'] = name
                        positions_filled['2B'] = True
                    elif '3B' in roster_pos and '3B' not in positions_filled:
                        row['3B'] = name
                        positions_filled['3B'] = True
                    elif 'SS' in roster_pos and 'SS' not in positions_filled:
                        row['SS'] = name
                        positions_filled['SS'] = True
                    elif 'OF' in roster_pos:
                        if 'OF' not in positions_filled:
                            row['OF'] = name
                            positions_filled['OF'] = True
                        elif 'OF2' not in positions_filled:
                            row['OF2'] = name
                            positions_filled['OF2'] = True
                        elif 'OF3' not in positions_filled:
                            row['OF3'] = name
                            positions_filled['OF3'] = True
                        else:
                            row['UTIL'] = name
                    else:
                        row['UTIL'] = name
            
            export_data.append(row)
        
        # Save ML lineups
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ML_ENHANCED_TOURNAMENT_LINEUPS_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        df = pd.DataFrame(export_data)
        df.to_csv(filepath, index=False)
        
        print(f"SUCCESS: ML lineups exported: {filename}")
        
        # Analysis
        projections = [l['total_projected'] for l in lineups]
        ceilings = [l['ml_ceiling'] for l in lineups]
        
        print(f"\n ML-ENHANCED PORTFOLIO ANALYSIS:")
        print(f"  DATA: ML Projected: {min(projections):.1f} - {max(projections):.1f} FPPG (avg: {np.mean(projections):.1f})")
        print(f"  START: ML Ceiling: {min(ceilings):.1f} - {max(ceilings):.1f} FPPG (avg: {np.mean(ceilings):.1f})")
        
        elite_ml_lineups = sum(1 for c in ceilings if c >= 240)
        competitive_ml_lineups = sum(1 for c in ceilings if c >= 225)
        
        print(f"\nTARGET: ML TOURNAMENT POTENTIAL:")
        print(f"   240+ ML ceiling lineups: {elite_ml_lineups}/{len(lineups)} ({elite_ml_lineups/len(lineups)*100:.0f}%)")
        print(f"   225+ ML ceiling lineups: {competitive_ml_lineups}/{len(lineups)} ({competitive_ml_lineups/len(lineups)*100:.0f}%)")
        
        return filepath
    
    def run_complete_ml_tournament_system(self):
        """Run the complete ML-enhanced tournament system"""
        print(" ML-ENHANCED TOURNAMENT SYSTEM")
        print("Combining machine learning with tournament optimization")
        print("="*80)
        
        try:
            # Step 1: Run ML predictions
            ml_success = self.run_ml_prediction_pipeline()
            
            # Step 2: Load ML projections
            hitter_proj, pitcher_proj = self.load_ml_projections()
            
            # Step 3: Enhance slate with ML
            enhanced_slate = self.enhance_slate_with_ml(hitter_proj, pitcher_proj)
            
            if enhanced_slate is None:
                print("ERROR: Failed to enhance slate with ML projections")
                return
            
            # Step 4: Run ML tournament optimization
            ml_slate = self.run_ml_tournament_optimization(enhanced_slate)
            
            # Step 5: Build ML lineups
            ml_lineups = self.build_ml_tournament_lineups(ml_slate, count=15)
            
            if ml_lineups:
                # Step 6: Export ML lineups
                filepath = self.export_ml_lineups(ml_lineups)
                
                print(f"\nCOMPLETE: ML TOURNAMENT SYSTEM COMPLETE!")
                print(f" Generated {len(ml_lineups)} ML-enhanced tournament lineups")
                print(f"TARGET: Strategy: Machine learning + tournament optimization")
                print(f"LINEUP: Ready for ML-powered tournament domination!")
                
                return filepath
            else:
                print("ERROR: Failed to generate ML lineups")
                
        except Exception as e:
            print(f"Error in ML tournament system: {e}")
            import traceback
            traceback.print_exc()

def main():
    print(" ML-ENHANCED TOURNAMENT SYSTEM")
    print("Combining machine learning with tournament optimization")
    print("="*80)
    
    ml_system = MLEnhancedTournamentSystem()
    ml_system.run_complete_ml_tournament_system()

if __name__ == "__main__":
    main()
