#!/usr/bin/env python3
"""
EXPORT SELECTED LINEUPS
Takes recommendations from ELITE_LINEUP_SELECTOR and exports actual FanDuel-ready CSV files
"""

import pandas as pd
import os
from datetime import datetime
import json

class LineupExporter:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.fd_dir = os.path.join(os.path.dirname(self.base_dir), 'fd_current_slate')
        
    def export_recommended_lineups(self):
        """Export the lineups recommended by ELITE_LINEUP_SELECTOR"""
        print("🎯 EXPORTING RECOMMENDED LINEUPS FOR CONTEST ENTRY")
        print("=" * 60)
        
        try:
            # First run the lineup selector to get recommendations
            from ELITE_LINEUP_SELECTOR import EliteLineupSelector
            
            selector = EliteLineupSelector()
            
            # Load generated lineups
            lineups_file = '../fd_current_slate/Enhanced_Lineups_FD_Format.csv'
            if not os.path.exists(lineups_file):
                # Try the most recent file
                enhanced_files = [f for f in os.listdir(self.fd_dir) if 'Enhanced_Lineups_FD_Format' in f and f.endswith('.csv')]
                if enhanced_files:
                    enhanced_files.sort(reverse=True)  # Most recent first
                    lineups_file = os.path.join(self.fd_dir, enhanced_files[0])
                    print(f"📁 Using lineup file: {enhanced_files[0]}")
                else:
                    print("❌ No Enhanced_Lineups_FD_Format files found!")
                    return
            
            lineups_df = pd.read_csv(lineups_file)
            print(f"✅ Loaded {len(lineups_df)} generated lineups")
            
            # Get recommendations
            recommendations = selector.select_optimal_lineups()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Export each contest type
            for contest_type, lineup_list in recommendations.items():
                if lineup_list:  # Check if there are lineups for this contest type
                    # Get the top lineup for each contest type
                    top_lineup = lineup_list[0]
                    lineup_id = top_lineup['lineup_id']
                    characteristics = top_lineup['characteristics']
                    
                    # Find the lineup in the dataframe
                    if 'lineup_id' in lineups_df.columns:
                        lineup_row = lineups_df[lineups_df['lineup_id'] == lineup_id]
                    elif 'Lineup' in lineups_df.columns:
                        # Try to match by lineup number
                        lineup_num = lineup_id.split('_')[-1] if '_' in lineup_id else lineup_id
                        try:
                            lineup_row = lineups_df[lineups_df['Lineup'] == int(lineup_num)]
                        except:
                            lineup_row = lineups_df.iloc[[0]]  # Fallback to first row
                    else:
                        # Use row index as fallback
                        try:
                            row_idx = int(lineup_id.split('_')[-1]) - 1 if '_' in lineup_id else 0
                            lineup_row = lineups_df.iloc[[row_idx]]
                        except:
                            lineup_row = lineups_df.iloc[[0]]
                    
                    if not lineup_row.empty:
                        # Export filename
                        contest_clean = contest_type.replace(' ', '_').replace('(', '').replace(')', '')
                        filename = f"RECOMMENDED_{contest_clean}_{lineup_id}_{timestamp}.csv"
                        filepath = os.path.join(self.fd_dir, filename)
                        
                        # Export the lineup
                        lineup_row.to_csv(filepath, index=False)
                        
                        print(f"\n📊 {contest_type.replace('_', ' ').title()}:")
                        print(f"   💾 Exported: {filename}")
                        print(f"   🎯 Lineup ID: {lineup_id}")
                        print(f"   🏆 Ceiling: {characteristics['ceiling_score']}")
                        print(f"   🛡️ Floor: {characteristics['floor_score']}")
                        print(f"   📈 Suitability: {characteristics['contest_suitability'][contest_type]:.1f}%")
                    
            # Also create a summary file
            summary_file = f"LINEUP_RECOMMENDATIONS_SUMMARY_{timestamp}.txt"
            summary_path = os.path.join(self.fd_dir, summary_file)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write("🎯 ELITE LINEUP RECOMMENDATIONS\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for contest_type, lineup_list in recommendations.items():
                    if lineup_list:
                        top_lineup = lineup_list[0]
                        f.write(f"{contest_type.replace('_', ' ').title()}:\n")
                        f.write(f"  Lineup: {top_lineup['lineup_id']}\n")
                        f.write(f"  Ceiling: {top_lineup['characteristics']['ceiling_score']}\n")
                        f.write(f"  Floor: {top_lineup['characteristics']['floor_score']}\n")
                        f.write(f"  Suitability: {top_lineup['characteristics']['contest_suitability'][contest_type]:.1f}%\n")
                        f.write(f"  Strategy: {top_lineup['characteristics'].get('stack_type', 'N/A')}\n\n")
            
            print(f"\n✅ EXPORT COMPLETE!")
            print(f"📋 Summary saved: {summary_file}")
            print(f"📁 All files in: {self.fd_dir}")
            
            return recommendations
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def export_specific_lineup(self, lineup_id, contest_type="Custom"):
        """Export a specific lineup by ID"""
        try:
            # Load the lineups file
            lineups_file = '../fd_current_slate/Enhanced_Lineups_FD_Format.csv'
            if not os.path.exists(lineups_file):
                enhanced_files = [f for f in os.listdir(self.fd_dir) if 'Enhanced_Lineups_FD_Format' in f and f.endswith('.csv')]
                if enhanced_files:
                    enhanced_files.sort(reverse=True)
                    lineups_file = os.path.join(self.fd_dir, enhanced_files[0])
                else:
                    print("❌ No lineup files found!")
                    return False
            
            lineups_df = pd.read_csv(lineups_file)
            
            # Find the specific lineup
            if 'lineup_id' in lineups_df.columns:
                lineup_row = lineups_df[lineups_df['lineup_id'] == lineup_id]
            else:
                # Try by index
                row_idx = int(lineup_id.split('_')[-1]) - 1 if '_' in lineup_id else int(lineup_id) - 1
                lineup_row = lineups_df.iloc[[row_idx]]
            
            if not lineup_row.empty:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"EXPORT_{contest_type}_{lineup_id}_{timestamp}.csv"
                filepath = os.path.join(self.fd_dir, filename)
                
                lineup_row.to_csv(filepath, index=False)
                print(f"✅ Exported {lineup_id} as {filename}")
                return True
            else:
                print(f"❌ Lineup {lineup_id} not found!")
                return False
                
        except Exception as e:
            print(f"❌ Export error: {e}")
            return False

if __name__ == "__main__":
    exporter = LineupExporter()
    exporter.export_recommended_lineups()
