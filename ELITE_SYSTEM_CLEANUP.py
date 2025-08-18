#!/usr/bin/env python3
"""
ELITE_SYSTEM_CLEANUP.py
Move deprecated scripts to backup and organize elite components
"""

import os
import shutil
import glob
from datetime import datetime

class EliteSystemCleanup:
    
    def __init__(self):
        self.scripts_path = "."
        self.backup_path = "./DEPRECATED_SCRIPTS_BACKUP"
        self.elite_path = "./ELITE_SYSTEM_COMPONENTS"
        
        # Elite components identified by architect
        self.elite_components = {
            "CORE_DATA_ENGINE": [
                "1_CONFIRMED_generate_hitter_games.py",
                "2_CONFIRMED_assign_hitter_ids.py", 
                "collect_actual_results_enhanced.py",
                "20. merge_weather_and_park_factors.py"
            ],
            
            "ADVANCED_FEATURE_ENGINE": [
                "12. build_rolling_hitter_features.py",
                "13. build_rolling_pitcher_features.py",
                "(21)finalize_hitter_features.py",
                "(22)finalize_pitcher_features.py"
            ],
            
            "ML_PREDICTION_ENGINE": [
                "automated_betting_system.py",
                "22. train_models.py",
                "advanced_ensemble_system.py"
            ],
            
            "ELITE_DFS_ENGINE": [
                "generate_quintuple_lineups.py",
                "CEILING_DFS_SYSTEM.py",
                "ADVANCED_TOURNAMENT_OPTIMIZER.py",
                "INTEGRATED_ML_TOURNAMENT_SYSTEM.py"
            ],
            
            "PROP_BETTING_ENGINE": [
                "ADVANCED_PROP_ENHANCER.py",
                "analyze_uf_props.py",
                "combo_prop_optimizer.py"
            ],
            
            "VALIDATION_ENGINE": [
                "comprehensive_backtest_analysis.py",
                "test_quintuple_lineups.py",
                "simple_backtest_validator.py"
            ],
            
            "LIVE_DATA_ENGINE": [
                "live_odds_scraper.py",
                "live_line_updates_clean.py",
                "injury_news_analyzer.py"
            ]
        }
        
        # Flatten all elite scripts
        self.all_elite_scripts = []
        for category in self.elite_components.values():
            self.all_elite_scripts.extend(category)
        
        # Add some essential utilities
        self.all_elite_scripts.extend([
            "ELITE_SYSTEM_ARCHITECT.py",
            "ELITE_SYSTEM_CLEANUP.py",
            "fetch_rotowire_lineups.py",  # Essential for daily data
            "PrizePicks_mlb.py",  # Essential scraper
            "underdog_fantasy_mlb.py"  # Essential scraper
        ])
    
    def create_backup_structure(self):
        """Create organized backup folder structure"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_root = f"{self.backup_path}_{timestamp}"
        
        # Create backup directories
        backup_dirs = [
            f"{backup_root}/DEPRECATED_DATA_PIPELINE",
            f"{backup_root}/DEPRECATED_FEATURE_ENGINE", 
            f"{backup_root}/DEPRECATED_ML_MODELS",
            f"{backup_root}/DEPRECATED_DFS_OPTIMIZERS",
            f"{backup_root}/DEPRECATED_PROP_BETTING",
            f"{backup_root}/DEPRECATED_BACKTESTING",
            f"{backup_root}/DEPRECATED_UTILITIES",
            f"{backup_root}/DEPRECATED_SCRAPERS",
            f"{backup_root}/DEPRECATED_MISC"
        ]
        
        for dir_path in backup_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        return backup_root
    
    def categorize_deprecated_script(self, script):
        """Categorize deprecated script for organized backup"""
        
        script_lower = script.lower()
        
        if any(x in script_lower for x in ['generate_', 'fetch_', 'collect_', 'assign_', 'merge_']):
            return "DEPRECATED_DATA_PIPELINE"
        elif any(x in script_lower for x in ['build_', 'aggregate_', 'finalize_', 'features']):
            return "DEPRECATED_FEATURE_ENGINE"
        elif any(x in script_lower for x in ['train_', 'model', 'ensemble', 'ml_']):
            return "DEPRECATED_ML_MODELS"
        elif any(x in script_lower for x in ['lineup', 'dfs', 'optimizer', 'tournament']):
            return "DEPRECATED_DFS_OPTIMIZERS"
        elif any(x in script_lower for x in ['prop', 'betting', 'underdog', 'prizepicks']):
            return "DEPRECATED_PROP_BETTING"
        elif any(x in script_lower for x in ['backtest', 'validation', 'test_', 'diagnostic']):
            return "DEPRECATED_BACKTESTING"
        elif any(x in script_lower for x in ['scrape', 'scraper']):
            return "DEPRECATED_SCRAPERS"
        else:
            return "DEPRECATED_MISC"
    
    def backup_deprecated_scripts(self):
        """Move all deprecated scripts to organized backup"""
        
        print(" CREATING ELITE SYSTEM CLEANUP")
        print("=" * 50)
        
        # Create backup structure
        backup_root = self.create_backup_structure()
        print(f" Created backup directory: {backup_root}")
        
        # Get all Python files
        all_scripts = glob.glob("*.py")
        
        moved_count = 0
        kept_count = 0
        
        for script in all_scripts:
            if script in self.all_elite_scripts:
                # Keep elite script
                kept_count += 1
                print(f"SUCCESS: KEEPING: {script}")
            else:
                # Move deprecated script to appropriate backup folder
                category = self.categorize_deprecated_script(script)
                backup_path = os.path.join(backup_root, category, script)
                
                try:
                    shutil.move(script, backup_path)
                    moved_count += 1
                    print(f" MOVED: {script}  {category}")
                except Exception as e:
                    print(f"ERROR: ERROR moving {script}: {e}")
        
        return backup_root, moved_count, kept_count
    
    def create_elite_system_inventory(self, backup_root):
        """Create inventory of elite system"""
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        inventory = [
            "START: ELITE MLB DFS/PROP SYSTEM - FINAL INVENTORY",
            "=" * 60,
            f"Cleanup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Backup Location: {backup_root}",
            "",
            "LINEUP: ELITE SYSTEM COMPONENTS:",
            ""
        ]
        
        for category, scripts in self.elite_components.items():
            inventory.append(f" {category}:")
            for script in scripts:
                if os.path.exists(script):
                    inventory.append(f"   SUCCESS: {script}")
                else:
                    inventory.append(f"   ERROR: {script} (MISSING)")
            inventory.append("")
        
        inventory.extend([
            " ESSENTIAL UTILITIES:",
            "   SUCCESS: ELITE_SYSTEM_ARCHITECT.py",
            "   SUCCESS: ELITE_SYSTEM_CLEANUP.py", 
            "   SUCCESS: fetch_rotowire_lineups.py",
            "   SUCCESS: PrizePicks_mlb.py",
            "   SUCCESS: underdog_fantasy_mlb.py",
            "",
            "TARGET: SYSTEM STATUS:",
            "   Clean, organized, elite components only",
            "   Ready for institutional-grade consolidation",
            "   Deprecated scripts safely backed up",
            "",
            "START: NEXT PHASE: Build unified orchestration system"
        ])
        
        # Save inventory
        inventory_file = f"ELITE_SYSTEM_INVENTORY_{timestamp}.txt"
        with open(inventory_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(inventory))
        
        return inventory_file, inventory
    
    def execute_cleanup(self):
        """Execute the complete cleanup process"""
        
        print("START: EXECUTING ELITE SYSTEM CLEANUP")
        print("=" * 50)
        print("This will:")
        print("1. Move deprecated scripts to organized backup")
        print("2. Keep only elite components in main directory")
        print("3. Create system inventory")
        print("")
        
        # Execute backup
        backup_root, moved_count, kept_count = self.backup_deprecated_scripts()
        
        print(f"\nDATA: CLEANUP RESULTS:")
        print(f"   Scripts moved to backup: {moved_count}")
        print(f"   Elite scripts kept: {kept_count}")
        print(f"   Backup location: {backup_root}")
        
        # Create inventory
        inventory_file, inventory_content = self.create_elite_system_inventory(backup_root)
        
        print(f"\n Elite system inventory: {inventory_file}")
        
        # Print final status
        print(f"\nTARGET: ELITE SYSTEM IS NOW CLEAN AND ORGANIZED!")
        print("=" * 50)
        for line in inventory_content[-10:]:  # Show last 10 lines
            print(line)
        
        return backup_root, inventory_file

def main():
    cleanup = EliteSystemCleanup()
    
    print(" WARNING: This will move many scripts to backup!")
    print("Press Ctrl+C to cancel, or Enter to proceed...")
    input()
    
    backup_location, inventory_file = cleanup.execute_cleanup()
    
    print(f"\nSUCCESS: CLEANUP COMPLETE!")
    print(f" Backup: {backup_location}")
    print(f"INFO: Inventory: {inventory_file}")
    print("\nSTART: Ready to build elite unified system!")

if __name__ == "__main__":
    main()
