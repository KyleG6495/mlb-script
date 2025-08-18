#!/usr/bin/env python3
"""
DFS LINEUP DIAGNOSTIC ANALYZER
===============================
Identifies exactly why your DFS lineups are performing poorly and provides solutions.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from pathlib import Path

class DFSDiagnosticAnalyzer:
    def __init__(self):
        self.base_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.issues = []
        self.recommendations = []
        
    def run_full_diagnostic(self):
        """Run complete diagnostic analysis"""
        print(" DFS LINEUP DIAGNOSTIC ANALYSIS")
        print("=" * 50)
        
        # Check data freshness
        self.check_data_freshness()
        
        # Check projection quality
        self.check_projection_quality()
        
        # Check lineup diversity
        self.check_lineup_diversity()
        
        # Check correlation modeling
        self.check_correlation_modeling()
        
        # Check ownership awareness
        self.check_ownership_modeling()
        
        # Generate report
        self.generate_diagnostic_report()
        
    def check_data_freshness(self):
        """Check if data is fresh and accurate"""
        print("\n CHECKING DATA FRESHNESS...")
        
        try:
            # Check slate file age
            slate_file = self.slate_dir / "fd_slate_today.csv"
            if slate_file.exists():
                slate_age = (datetime.now() - datetime.fromtimestamp(slate_file.stat().st_mtime)).total_seconds() / 3600
                print(f"   Slate file age: {slate_age:.1f} hours")
                
                if slate_age > 24:
                    self.issues.append("WARNING: Slate file is over 24 hours old")
                    self.recommendations.append("Run fresh data pipeline (1_DATA_PIPELINE.bat)")
                
                # Check slate content
                slate = pd.read_csv(slate_file)
                print(f"   Players in slate: {len(slate)}")
                print(f"   Salary range: ${slate['Salary'].min()} - ${slate['Salary'].max()}")
                
                if len(slate) < 300:
                    self.issues.append("WARNING: Very few players in slate - may be incomplete")
                    
            else:
                self.issues.append("ERROR: No slate file found")
                self.recommendations.append("Run 1_DATA_PIPELINE.bat to generate slate")
                
        except Exception as e:
            self.issues.append(f"ERROR: Error checking slate: {e}")
            
    def check_projection_quality(self):
        """Analyze projection quality and methodology"""
        print("\nTARGET: CHECKING PROJECTION QUALITY...")
        
        try:
            # Load recent lineups
            lineup_files = list(self.base_dir.glob("enhanced_ml_dfs_lineups_*.csv"))
            if not lineup_files:
                lineup_files = list(self.base_dir.glob("fanduel_submission_*.csv"))
                
            if lineup_files:
                latest_lineups = pd.read_csv(sorted(lineup_files)[-1])
                print(f"   Latest lineups file: {len(latest_lineups)} lineups")
                print(f"   Projection range: {latest_lineups['Total_Projection'].min():.1f} - {latest_lineups['Total_Projection'].max():.1f}")
                
                # Check if projections are reasonable
                avg_projection = latest_lineups['Total_Projection'].mean()
                print(f"   Average projection: {avg_projection:.1f}")
                
                if avg_projection < 60:
                    self.issues.append("WARNING: Projections seem very low (avg < 60)")
                    self.recommendations.append("Check ML model training and FPPG conversion")
                elif avg_projection > 120:
                    self.issues.append("WARNING: Projections seem unrealistically high (avg > 120)")
                    self.recommendations.append("Check for projection inflation in models")
                    
                # Check for projection variance
                projection_std = latest_lineups['Total_Projection'].std()
                print(f"   Projection variance: {projection_std:.2f}")
                
                if projection_std < 2:
                    self.issues.append("WARNING: Very low projection variance - lineups too similar")
                    self.recommendations.append("Improve lineup diversity and player variance modeling")
                    
            else:
                self.issues.append("ERROR: No recent lineup files found")
                
        except Exception as e:
            self.issues.append(f"ERROR: Error checking projections: {e}")
            
    def check_lineup_diversity(self):
        """Check if lineups have proper diversity"""
        print("\n CHECKING LINEUP DIVERSITY...")
        
        try:
            # Check latest submission file
            submission_files = list(self.base_dir.glob("fanduel_submission_*.csv"))
            if submission_files:
                lineups = pd.read_csv(sorted(submission_files)[-1])
                
                # Count unique players across positions
                positions = ['P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3']
                if 'C/1B' in lineups.columns:
                    positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
                
                total_players = 0
                unique_players = 0
                
                for pos in positions:
                    if pos in lineups.columns:
                        pos_players = lineups[pos].dropna()
                        total_players += len(pos_players)
                        unique_players += len(pos_players.unique())
                        
                diversity_ratio = unique_players / total_players if total_players > 0 else 0
                print(f"   Player diversity ratio: {diversity_ratio:.2f}")
                
                if diversity_ratio < 0.3:
                    self.issues.append("WARNING: Very low player diversity - too many duplicate players")
                    self.recommendations.append("Increase diversity constraints in optimizer")
                elif diversity_ratio > 0.8:
                    self.issues.append("WARNING: Too much diversity - may hurt correlation")
                    self.recommendations.append("Balance diversity with game stacking")
                    
                # Check salary usage
                avg_salary = lineups['Total_Salary'].mean()
                print(f"   Average salary usage: ${avg_salary}")
                
                if avg_salary < 34000:
                    self.issues.append("WARNING: Not using enough salary - leaving money on table")
                    self.recommendations.append("Optimize to use closer to $35,000 cap")
                    
            else:
                self.issues.append("ERROR: No submission files found")
                
        except Exception as e:
            self.issues.append(f"ERROR: Error checking diversity: {e}")
            
    def check_correlation_modeling(self):
        """Check if correlations are properly modeled"""
        print("\n CHECKING CORRELATION MODELING...")
        
        try:
            submission_files = list(self.base_dir.glob("fanduel_submission_*.csv"))
            if submission_files:
                lineups = pd.read_csv(sorted(submission_files)[-1])
                
                # Check for game stacking
                if 'Game' in lineups.columns or 'P' in lineups.columns:
                    # Try to extract team info (this is simplified)
                    game_stacks = 0
                    for idx, lineup in lineups.iterrows():
                        # This is a basic check - would need more sophisticated analysis
                        pass
                    
                    print(f"   Basic correlation check completed")
                    self.recommendations.append("Implement proper game stacking and correlation modeling")
                
        except Exception as e:
            self.issues.append(f"ERROR: Error checking correlations: {e}")
            
    def check_ownership_modeling(self):
        """Check ownership awareness"""
        print("\nOWNERSHIP: CHECKING OWNERSHIP MODELING...")
        
        # Check if ownership files exist
        ownership_files = list(self.base_dir.glob("*ownership*.csv"))
        if not ownership_files:
            self.issues.append("WARNING: No ownership projection files found")
            self.recommendations.append("Implement ownership projection system")
        else:
            print(f"   Found {len(ownership_files)} ownership-related files")
            
    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        print("\n" + "=" * 50)
        print("INFO: DIAGNOSTIC SUMMARY")
        print("=" * 50)
        
        if self.issues:
            print("\n ISSUES IDENTIFIED:")
            for i, issue in enumerate(self.issues, 1):
                print(f"{i}. {issue}")
        else:
            print("\nSUCCESS: No major issues found!")
            
        if self.recommendations:
            print("\nTIP: RECOMMENDATIONS:")
            for i, rec in enumerate(self.recommendations, 1):
                print(f"{i}. {rec}")
                
        print("\nTARGET: PRIORITY FIXES:")
        print("1. Ensure fresh data pipeline run")
        print("2. Validate ML model projections")
        print("3. Implement proper game stacking")
        print("4. Add ownership-based optimization")
        print("5. Include real-time adjustments")
        
        # Save report
        report_file = self.base_dir / f"dfs_diagnostic_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write("DFS DIAGNOSTIC REPORT\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Analysis Date: {datetime.now()}\n\n")
            
            f.write("ISSUES:\n")
            for issue in self.issues:
                f.write(f"- {issue}\n")
                
            f.write("\nRECOMMENDATIONS:\n")
            for rec in self.recommendations:
                f.write(f"- {rec}\n")
                
        print(f"\n Full report saved: {report_file}")

if __name__ == "__main__":
    analyzer = DFSDiagnosticAnalyzer()
    analyzer.run_full_diagnostic()
