#!/usr/bin/env python3
"""
INTEGRATED ML TOURNAMENT SYSTEM
===============================
Combine your existing ML pipeline output with tournament optimization.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class IntegratedMLTournamentSystem:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_ml_projections(self):
        """Load projections from your existing ML systems"""
        print("🤖 INTEGRATED ML TOURNAMENT SYSTEM")
        print("Combining your ML pipeline with tournament optimization")
        print("="*70)
        
        ml_files = {
            'enhanced_ml': list(self.slate_dir.glob("enhanced_ml_dfs_lineups_*.csv")),
            'ml_powered': list(self.slate_dir.glob("ml_dfs_lineups_*.csv")),
            'unified': list(self.slate_dir.glob("unified_dfs_lineups_*.csv")),
            'quintuple': list(self.slate_dir.glob("quintuple_lineups_combined_*.csv")),
            'enhanced_ceiling': list(self.slate_dir.glob("enhanced_ceiling_lineups_*.csv")),
            'game_state': list(self.slate_dir.glob("*game_state*.csv"))
        }
        
        print(f"📊 ML SYSTEM OUTPUT DETECTED:")
        total_ml_lineups = 0
        available_systems = []
        
        for system, files in ml_files.items():
            if files:
                latest_file = max(files, key=lambda x: x.stat().st_mtime)
                try:
                    df = pd.read_csv(latest_file)
                    total_ml_lineups += len(df)
                    available_systems.append(system)
                    print(f"  ✅ {system.upper()}: {len(df)} lineups from {latest_file.name}")
                except:
                    print(f"  ❌ {system.upper()}: Error reading {latest_file.name}")
            else:
                print(f"  ⏰ {system.upper()}: No files found (may need to run ML pipeline)")
        
        print(f"\n📈 Total ML lineups available: {total_ml_lineups}")
        print(f"🎯 Active ML systems: {len(available_systems)}")
        
        return available_systems, total_ml_lineups
    
    def enhance_with_ml_projections(self):
        """Enhance our tournament lineups with ML projections if available"""
        
        # Check if we have ML hitter/pitcher features from your pipeline
        hitter_features = self.data_dir / "fd_hitter_features_final.csv"
        pitcher_features = self.data_dir / "fd_pitcher_features_final.csv"
        
        if hitter_features.exists() and pitcher_features.exists():
            print(f"\n🎯 ML FEATURE ENHANCEMENT:")
            print(f"  ✅ Found ML hitter features: {hitter_features.name}")
            print(f"  ✅ Found ML pitcher features: {pitcher_features.name}")
            
            # Load your ML-enhanced features
            hitters_ml = pd.read_csv(hitter_features)
            pitchers_ml = pd.read_csv(pitcher_features)
            
            print(f"  📊 ML hitter projections: {len(hitters_ml)} players")
            print(f"  📊 ML pitcher projections: {len(pitchers_ml)} players")
            
            # Check if we have actual ML projections vs just features
            ml_projection_cols = ['predicted_fantasy_points', 'ml_projection', 'enhanced_projection']
            
            has_ml_projections = any(col in hitters_ml.columns for col in ml_projection_cols)
            
            if has_ml_projections:
                print(f"  🤖 ML projections detected - can enhance tournament lineups!")
                return True
            else:
                print(f"  📊 ML features available but need projections - run your ML pipeline first")
                return False
        else:
            print(f"\n⏰ ML FEATURES NOT FOUND:")
            print(f"  📋 Run your 2_DFS_MODELS.bat first to generate ML features")
            return False
    
    def recommend_ml_pipeline_sequence(self):
        """Recommend the optimal sequence for running ML + tournament systems"""
        print(f"\n🚀 RECOMMENDED ML + TOURNAMENT SEQUENCE:")
        print(f"="*60)
        
        print(f"STEP 1: Run Your ML Pipeline")
        print(f"  📋 Execute: 2_DFS_MODELS.bat")
        print(f"  🎯 This generates ML projections and initial lineups")
        print(f"  ⏱️ Time: ~8-12 minutes")
        
        print(f"\nSTEP 2: Run Enhanced Simulation (Optional)")
        print(f"  📋 Execute: 4_ENHANCED_MODELS.bat")
        print(f"  🎯 This adds game state simulation and ceiling optimization")
        print(f"  ⏱️ Time: ~10-15 minutes")
        
        print(f"\nSTEP 3: Run Tournament Optimization")
        print(f"  📋 Execute: python MASTER_TOURNAMENT_COMBINER.py")
        print(f"  🎯 This combines ML lineups with tournament strategies")
        print(f"  ⏱️ Time: ~2-3 minutes")
        
        print(f"\n💡 OPTIMAL APPROACH:")
        print(f"  1. ✅ Your ML systems provide the PROJECTIONS")
        print(f"  2. ✅ Our tournament systems provide the CONSTRUCTION STRATEGY")
        print(f"  3. ✅ Combined = ML-powered tournament lineups")
        
        print(f"\n🎯 WHY THIS WORKS BETTER:")
        print(f"  🤖 Your ML models: Superior player projections")
        print(f"  🏆 Our tournament system: Superior lineup construction")
        print(f"  💥 Combined: Best of both worlds!")
        
    def create_ml_tournament_integration(self):
        """Create integration script for ML + tournament systems"""
        
        integration_script = """#!/usr/bin/env python3
\"\"\"
ML TOURNAMENT INTEGRATION
========================
Run after your ML pipeline to enhance with tournament strategies.
\"\"\"

import pandas as pd
import numpy as np
from pathlib import Path

def integrate_ml_with_tournaments():
    slate_dir = Path(__file__).parent.parent / "fd_current_slate"
    
    # Find latest ML lineups
    ml_files = list(slate_dir.glob("enhanced_ml_dfs_lineups_*.csv"))
    
    if ml_files:
        latest_ml = max(ml_files, key=lambda x: x.stat().st_mtime)
        ml_df = pd.read_csv(latest_ml)
        
        print(f"🤖 Found ML lineups: {len(ml_df)} from {latest_ml.name}")
        
        # Find tournament lineups
        tournament_files = list(slate_dir.glob("MASTER_TOURNAMENT_PORTFOLIO_*.csv"))
        
        if tournament_files:
            latest_tournament = max(tournament_files, key=lambda x: x.stat().st_mtime)
            tournament_df = pd.read_csv(latest_tournament)
            
            print(f"🏆 Found tournament lineups: {len(tournament_df)} from {latest_tournament.name}")
            
            # Create combined portfolio
            combined_lineups = []
            
            # Add top ML lineups (highest projections)
            if 'Projected_FPPG' in ml_df.columns:
                top_ml = ml_df.nlargest(8, 'Projected_FPPG')
                for i, lineup in top_ml.iterrows():
                    lineup['Source'] = 'ML_SYSTEM'
                    lineup['Portfolio_ID'] = f"ML_{i+1}"
                    combined_lineups.append(lineup)
            
            # Add top tournament lineups (highest ceiling)
            if 'Tournament_Score' in tournament_df.columns:
                top_tournament = tournament_df.nlargest(7, 'Tournament_Score')
                for i, lineup in top_tournament.iterrows():
                    lineup['Source'] = 'TOURNAMENT_SYSTEM'
                    lineup['Portfolio_ID'] = f"TOUR_{i+1}"
                    combined_lineups.append(lineup)
            
            # Save integrated portfolio
            if combined_lineups:
                integrated_df = pd.DataFrame(combined_lineups)
                
                timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                filename = f"INTEGRATED_ML_TOURNAMENT_PORTFOLIO_{timestamp}.csv"
                filepath = slate_dir / filename
                
                integrated_df.to_csv(filepath, index=False)
                
                print(f"✅ Integrated portfolio saved: {filename}")
                print(f"📊 Total lineups: {len(integrated_df)}")
                print(f"🤖 ML lineups: {sum(1 for l in combined_lineups if l.get('Source') == 'ML_SYSTEM')}")
                print(f"🏆 Tournament lineups: {sum(1 for l in combined_lineups if l.get('Source') == 'TOURNAMENT_SYSTEM')}")
                
                return filepath
        
    print("⏰ Run your ML pipeline first, then tournament optimization")
    return None

if __name__ == "__main__":
    integrate_ml_with_tournaments()
"""
        
        integration_file = Path(__file__).parent / "ML_TOURNAMENT_INTEGRATION.py"
        with open(integration_file, 'w') as f:
            f.write(integration_script)
        
        print(f"\n✅ Created integration script: {integration_file.name}")
        print(f"📋 Run this after your ML pipeline completes")
        
        return integration_file
    
    def run_analysis(self):
        """Run the complete integration analysis"""
        print("🤖 INTEGRATED ML TOURNAMENT ANALYSIS")
        print("="*70)
        
        # Check current ML system status
        available_systems, total_lineups = self.load_ml_projections()
        
        # Check ML enhancement capability  
        can_enhance = self.enhance_with_ml_projections()
        
        if total_lineups > 0:
            print(f"\n🎉 EXCELLENT! You have {total_lineups} ML lineups ready!")
            print(f"💡 Now run MASTER_TOURNAMENT_COMBINER.py to integrate with tournament strategies")
        else:
            print(f"\n📋 RECOMMENDATION: Run your ML pipeline first")
            self.recommend_ml_pipeline_sequence()
        
        # Create integration helper
        integration_file = self.create_ml_tournament_integration()
        
        print(f"\n🚀 INTEGRATION SUMMARY:")
        print(f"  🤖 Your ML systems: {len(available_systems)} active")
        print(f"  🏆 Tournament optimization: Ready")
        print(f"  🔗 Integration script: {integration_file.name}")
        print(f"  💥 Combined potential: ML projections + Tournament strategies")

def main():
    analyzer = IntegratedMLTournamentSystem()
    analyzer.run_analysis()

if __name__ == "__main__":
    main()
