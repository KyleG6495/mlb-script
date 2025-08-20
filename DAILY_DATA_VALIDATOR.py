#!/usr/bin/env python3
"""
🔍 DAILY DATA VALIDATOR 🔍
Comprehensive audit system to ensure all files are current and complete
"""

import pandas as pd
from pathlib import Path
import os
from datetime import datetime, timedelta
import json

class DailyDataValidator:
    def __init__(self):
        self.today = datetime.now().strftime('%Y%m%d')
        self.scripts_path = Path('c:/Users/kgone/OneDrive/Personal_Information/MLB/Scripts')
        self.data_path = Path('c:/Users/kgone/OneDrive/Personal_Information/MLB/data')
        self.fd_path = Path('c:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate')
        
        # Define critical files needed for daily operations
        self.critical_files = {
            'INPUT_FILES': {
                'fd_slate_today.csv': {
                    'path': self.fd_path,
                    'description': 'Today\'s FanDuel slate',
                    'max_age_hours': 24,
                    'required': True
                }
            },
            'DFS_OUTPUT_FILES': {
                'Enhanced_Lineups_FD_Format_*.csv': {
                    'path': self.fd_path,
                    'description': 'Enhanced DFS lineups',
                    'max_age_hours': 12,
                    'required': True
                },
                'enhanced_ml_dfs_lineups_*.csv': {
                    'path': self.fd_path,
                    'description': 'ML DFS lineups',
                    'max_age_hours': 12,
                    'required': False
                }
            },
            'PROPS_OUTPUT_FILES': {
                'enhanced_prop_predictions_*.csv': {
                    'path': self.data_path,
                    'description': 'Prop predictions',
                    'max_age_hours': 12,
                    'required': True
                },
                'betting_opportunities_*.csv': {
                    'path': self.data_path,
                    'description': 'Betting opportunities',
                    'max_age_hours': 12,
                    'required': False
                }
            },
            'OWNERSHIP_FILES': {
                'advanced_ownership_projections_*.csv': {
                    'path': self.data_path,
                    'description': 'Ownership projections',
                    'max_age_hours': 12,
                    'required': True
                }
            },
            'STACK_FILES': {
                'team_stack_analysis_*.csv': {
                    'path': self.data_path,
                    'description': 'Team stack analysis',
                    'max_age_hours': 12,
                    'required': True
                },
                'stack_recommendations_*.csv': {
                    'path': self.data_path,
                    'description': 'Stack recommendations',
                    'max_age_hours': 12,
                    'required': True
                }
            }
        }
        
        # Define the daily pipeline scripts and their dependencies
        self.pipeline_scripts = {
            '1. DATA_COLLECTION': {
                'scripts': ['1_CONFIRMED_generate_hitter_games.py'],
                'inputs': ['fd_slate_today.csv'],
                'outputs': ['hitter_games_*.csv'],
                'description': 'Collect and process raw data'
            },
            '2. DFS_OPTIMIZATION': {
                'scripts': ['2_DFS_MODELS.bat', '2B_ENHANCED_DFS.bat'],
                'inputs': ['hitter_games_*.csv', 'fd_slate_today.csv'],
                'outputs': ['Enhanced_Lineups_FD_Format_*.csv'],
                'description': 'Generate optimized DFS lineups'
            },
            '3. PROPS_ANALYSIS': {
                'scripts': ['3_PROP_MODELS.bat'],
                'inputs': ['hitter_games_*.csv'],
                'outputs': ['enhanced_prop_predictions_*.csv'],
                'description': 'Generate prop predictions'
            },
            '4. OWNERSHIP_ANALYSIS': {
                'scripts': ['ownership_analysis.py'],
                'inputs': ['Enhanced_Lineups_FD_Format_*.csv'],
                'outputs': ['advanced_ownership_projections_*.csv'],
                'description': 'Calculate ownership projections'
            },
            '5. STACK_OPTIMIZATION': {
                'scripts': ['ADVANCED_STACK_OPTIMIZER.py'],
                'inputs': ['Enhanced_Lineups_FD_Format_*.csv'],
                'outputs': ['team_stack_analysis_*.csv', 'stack_recommendations_*.csv'],
                'description': 'Optimize stacking strategies'
            }
        }

    def get_latest_file(self, pattern, search_path):
        """Get the latest file matching pattern"""
        files = list(search_path.glob(pattern))
        return max(files, key=os.path.getctime) if files else None

    def check_file_freshness(self, file_path, max_age_hours):
        """Check if file is fresh enough"""
        if not file_path or not file_path.exists():
            return False, "File not found"
        
        file_age = datetime.now() - datetime.fromtimestamp(file_path.stat().st_mtime)
        age_hours = file_age.total_seconds() / 3600
        
        if age_hours > max_age_hours:
            return False, f"File is {age_hours:.1f} hours old (max: {max_age_hours})"
        
        return True, f"Fresh ({age_hours:.1f} hours old)"

    def validate_all_files(self):
        """Validate all critical files"""
        print("🔍 DAILY DATA VALIDATION REPORT")
        print("=" * 70)
        
        validation_results = {}
        overall_status = True
        
        for category, files in self.critical_files.items():
            print(f"\n📁 {category}")
            print("-" * 50)
            
            category_results = {}
            
            for pattern, config in files.items():
                file_path = self.get_latest_file(pattern, config['path'])
                is_fresh, status_msg = self.check_file_freshness(file_path, config['max_age_hours'])
                
                if file_path:
                    file_name = file_path.name
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
                else:
                    file_name = "NOT FOUND"
                    file_time = "N/A"
                
                status_icon = "✅" if is_fresh else ("❌" if config['required'] else "⚠️")
                required_text = "REQUIRED" if config['required'] else "OPTIONAL"
                
                print(f"{status_icon} {pattern}")
                print(f"   File: {file_name}")
                print(f"   Time: {file_time}")
                print(f"   Status: {status_msg} [{required_text}]")
                print(f"   Description: {config['description']}")
                print()
                
                category_results[pattern] = {
                    'file_name': file_name,
                    'file_time': file_time,
                    'is_fresh': is_fresh,
                    'status': status_msg,
                    'required': config['required'],
                    'description': config['description']
                }
                
                if config['required'] and not is_fresh:
                    overall_status = False
            
            validation_results[category] = category_results
        
        return validation_results, overall_status

    def check_pipeline_readiness(self):
        """Check if daily pipeline is ready to run"""
        print("\n🚀 DAILY PIPELINE READINESS CHECK")
        print("=" * 70)
        
        pipeline_status = {}
        
        for stage, config in self.pipeline_scripts.items():
            print(f"\n{stage}: {config['description']}")
            print("-" * 50)
            
            # Check inputs
            input_status = True
            missing_inputs = []
            
            for input_file in config['inputs']:
                found = False
                for category, files in self.critical_files.items():
                    if input_file in files or any(input_file.replace('*', '') in pattern for pattern in files.keys()):
                        found = True
                        break
                
                if not found:
                    # Check if file exists directly
                    if self.get_latest_file(input_file, self.data_path) or self.get_latest_file(input_file, self.fd_path):
                        found = True
                
                if not found:
                    input_status = False
                    missing_inputs.append(input_file)
            
            status_icon = "✅" if input_status else "❌"
            print(f"{status_icon} Inputs: {', '.join(config['inputs'])}")
            
            if missing_inputs:
                print(f"   Missing: {', '.join(missing_inputs)}")
            
            print(f"📄 Scripts: {', '.join(config['scripts'])}")
            print(f"📤 Outputs: {', '.join(config['outputs'])}")
            
            pipeline_status[stage] = {
                'ready': input_status,
                'missing_inputs': missing_inputs,
                'scripts': config['scripts'],
                'outputs': config['outputs']
            }
        
        return pipeline_status

    def generate_daily_checklist(self):
        """Generate a daily checklist for manual verification"""
        print("\n📋 DAILY OPERATIONS CHECKLIST")
        print("=" * 70)
        
        checklist = [
            "☐ 1. Check fd_slate_today.csv is downloaded and current",
            "☐ 2. Run data collection scripts (1_CONFIRMED_generate_hitter_games.py)",
            "☐ 3. Run DFS optimization (2_DFS_MODELS.bat, 2B_ENHANCED_DFS.bat)",
            "☐ 4. Run prop models (3_PROP_MODELS.bat)",
            "☐ 5. Generate ownership projections",
            "☐ 6. Run stack optimizer (ADVANCED_STACK_OPTIMIZER.py)",
            "☐ 7. Validate all outputs with this script",
            "☐ 8. Check dashboard loads correctly (real_data_dashboard.py)",
            "☐ 9. Verify no old players (like Shane Bieber) in lineups",
            "☐ 10. Export final lineups for submission"
        ]
        
        for item in checklist:
            print(item)
        
        return checklist

    def run_full_validation(self):
        """Run complete validation suite"""
        print("🏆 COMPREHENSIVE DATA VALIDATION SUITE")
        print("=" * 70)
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Today's target: {self.today}")
        print()
        
        # File validation
        file_results, files_ok = self.validate_all_files()
        
        # Pipeline validation  
        pipeline_results = self.check_pipeline_readiness()
        
        # Generate checklist
        checklist = self.generate_daily_checklist()
        
        # Overall status
        print(f"\n🎯 OVERALL STATUS")
        print("=" * 70)
        
        if files_ok:
            print("✅ ALL CRITICAL FILES ARE CURRENT AND READY")
        else:
            print("❌ SOME CRITICAL FILES ARE MISSING OR STALE")
            print("   👆 Fix the issues above before proceeding")
        
        print(f"\n💾 Report saved to: daily_validation_{self.today}.json")
        
        # Save detailed report
        report = {
            'timestamp': datetime.now().isoformat(),
            'target_date': self.today,
            'file_validation': file_results,
            'pipeline_status': pipeline_results,
            'overall_status': files_ok,
            'checklist': checklist
        }
        
        report_path = self.scripts_path / f"daily_validation_{self.today}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

if __name__ == "__main__":
    validator = DailyDataValidator()
    validator.run_full_validation()
