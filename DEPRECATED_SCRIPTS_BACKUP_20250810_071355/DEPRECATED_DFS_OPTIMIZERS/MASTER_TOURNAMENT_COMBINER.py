#!/usr/bin/env python3
"""
MASTER TOURNAMENT COMBINER
==========================
Combine the best lineups from all tournament systems into the ultimate portfolio.
Select top lineups based on ceiling, diversity, and tournament potential.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
from collections import defaultdict
warnings.filterwarnings('ignore')

class MasterTournamentCombiner:
    def __init__(self):
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        self.data_dir = Path(__file__).parent.parent / "data"
        
    def load_all_tournament_lineups(self):
        """Load lineups from all tournament systems"""
        print("🏆 MASTER TOURNAMENT COMBINER")
        print("Selecting the ultimate tournament portfolio")
        print("="*80)
        
        all_lineups = []
        
        # Find all tournament lineup files
        lineup_files = list(self.slate_dir.glob("*tournament_lineups_*.csv"))
        
        print(f"📊 Found {len(lineup_files)} tournament lineup files:")
        
        for file in lineup_files:
            try:
                df = pd.read_csv(file)
                
                # Identify system type
                if "elite" in file.name:
                    system_type = "ELITE_STACKING"
                elif "diversified" in file.name:
                    system_type = "DIVERSIFIED_STACKS"
                elif "tournament" in file.name and "elite" not in file.name:
                    system_type = "SMART_FOUNDATION"
                else:
                    system_type = "UNKNOWN"
                
                df['System_Type'] = system_type
                df['Source_File'] = file.name
                
                all_lineups.append(df)
                print(f"  ✅ {system_type}: {len(df)} lineups from {file.name}")
                
            except Exception as e:
                print(f"  ❌ Error loading {file.name}: {e}")
        
        if not all_lineups:
            print("❌ No tournament lineup files found!")
            return None
        
        # Combine all lineups
        combined_df = pd.concat(all_lineups, ignore_index=True)
        print(f"\n📊 Total tournament lineups loaded: {len(combined_df)}")
        
        return combined_df
    
    def analyze_lineup_quality(self, df):
        """Analyze and score all lineups for tournament potential"""
        print(f"\n🎯 ANALYZING LINEUP QUALITY:")
        
        # Calculate quality metrics
        df['Ceiling_Score'] = df['Ceiling_FPPG'] / 250  # Target 250+ ceiling
        df['Projection_Score'] = df['Projected_FPPG'] / 140  # Target 140+ projection
        df['Upside_Ratio'] = df['Ceiling_FPPG'] / df['Projected_FPPG']
        df['Salary_Efficiency'] = (35000 - df['Total_Salary']) / 35000  # Bonus for leaving salary
        
        # Diversity bonuses
        df['Stack_Diversity_Bonus'] = np.where(
            df.groupby('Stack_Team')['Stack_Team'].transform('count') <= 3, 0.1, 0
        )  # Bonus for unique team stacks
        
        # Tournament readiness score
        df['Tournament_Score'] = (
            df['Ceiling_Score'] * 0.4 +           # 40% ceiling potential
            df['Projection_Score'] * 0.25 +       # 25% projected floor
            df['Upside_Ratio'] * 0.15 +          # 15% upside potential
            df['Salary_Efficiency'] * 0.1 +       # 10% salary efficiency
            df['Stack_Diversity_Bonus'] * 0.1     # 10% diversity bonus
        )
        
        # System type bonuses
        system_bonuses = {
            'ELITE_STACKING': 0.05,      # Slight bonus for advanced stacking
            'DIVERSIFIED_STACKS': 0.03,  # Small bonus for diversification
            'SMART_FOUNDATION': 0.02     # Base foundation bonus
        }
        
        for system, bonus in system_bonuses.items():
            df.loc[df['System_Type'] == system, 'Tournament_Score'] += bonus
        
        print(f"  📊 Lineup scoring complete")
        print(f"  🎯 Top tournament scores: {df['Tournament_Score'].max():.3f} - {df['Tournament_Score'].min():.3f}")
        
        return df
    
    def select_master_portfolio(self, df, target_lineups=15):
        """Select the ultimate tournament portfolio"""
        print(f"\n🏆 SELECTING MASTER TOURNAMENT PORTFOLIO:")
        print(f"Target: {target_lineups} elite lineups for maximum tournament potential")
        
        selected_lineups = []
        used_teams = defaultdict(int)
        used_strategies = defaultdict(int)
        
        # Sort by tournament score
        df_sorted = df.sort_values('Tournament_Score', ascending=False)
        
        print(f"\n🎯 SELECTION CRITERIA:")
        print(f"  1. Tournament Score (ceiling, projection, upside)")
        print(f"  2. Stack Diversity (max 3 per team)")
        print(f"  3. System Representation")
        print(f"  4. Strategy Balance")
        
        print(f"\n🔍 LINEUP SELECTION PROCESS:")
        
        for idx, lineup in df_sorted.iterrows():
            if len(selected_lineups) >= target_lineups:
                break
            
            team = lineup['Stack_Team']
            system = lineup['System_Type']
            
            # Diversity constraints
            max_per_team = 3 if target_lineups >= 15 else 2
            max_per_system = target_lineups // 2  # Allow half from any system
            
            # Check constraints
            if used_teams[team] >= max_per_team:
                continue  # Too many from this team
            
            if used_strategies[system] >= max_per_system:
                continue  # Too many from this system
            
            # Select this lineup
            selected_lineups.append(lineup)
            used_teams[team] += 1
            used_strategies[system] += 1
            
            print(f"  ✅ #{len(selected_lineups):2d}: {lineup['Lineup_ID']} ({system}) | {lineup['Stack_Team']} stack | {lineup['Tournament_Score']:.3f} score")
        
        print(f"\n📊 PORTFOLIO COMPOSITION:")
        print(f"  📋 Total lineups selected: {len(selected_lineups)}")
        
        # System breakdown
        print(f"  🎯 System representation:")
        for system, count in used_strategies.items():
            percentage = count / len(selected_lineups) * 100
            print(f"    {system}: {count} lineups ({percentage:.1f}%)")
        
        # Team breakdown
        print(f"  🏈 Team stack diversity:")
        for team, count in sorted(used_teams.items(), key=lambda x: x[1], reverse=True):
            print(f"    {team}: {count} lineups")
        
        return selected_lineups
    
    def create_master_export(self, selected_lineups):
        """Create the master tournament export"""
        print(f"\n📄 CREATING MASTER TOURNAMENT EXPORT:")
        
        # Convert to DataFrame
        master_df = pd.DataFrame(selected_lineups)
        
        # Reorder columns for better readability
        column_order = [
            'Lineup_ID', 'System_Type', 'Strategy', 'Stack_Team', 'Stack_Size',
            'Tournament_Score', 'Ceiling_FPPG', 'Projected_FPPG', 'Upside_Ratio',
            'Total_Salary', 'P', 'C', '1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL'
        ]
        
        # Ensure all columns exist
        for col in column_order:
            if col not in master_df.columns:
                master_df[col] = ''
        
        master_df = master_df[column_order]
        
        # Save master file
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"MASTER_TOURNAMENT_PORTFOLIO_{timestamp}.csv"
        filepath = self.slate_dir / filename
        
        master_df.to_csv(filepath, index=False)
        print(f"✅ Master portfolio exported: {filename}")
        
        return master_df, filepath
    
    def analyze_master_portfolio(self, master_df):
        """Analyze the final master portfolio"""
        print(f"\n🏆 MASTER PORTFOLIO ANALYSIS:")
        
        # Performance metrics
        ceiling_scores = master_df['Ceiling_FPPG'].values
        projection_scores = master_df['Projected_FPPG'].values
        tournament_scores = master_df['Tournament_Score'].values
        
        print(f"  📊 PERFORMANCE METRICS:")
        print(f"    🚀 Ceiling Range: {ceiling_scores.min():.1f} - {ceiling_scores.max():.1f} FPPG")
        print(f"    📈 Projection Range: {projection_scores.min():.1f} - {projection_scores.max():.1f} FPPG")
        print(f"    🎯 Average Ceiling: {ceiling_scores.mean():.1f} FPPG")
        print(f"    📊 Average Projection: {projection_scores.mean():.1f} FPPG")
        
        # Tournament competitiveness
        elite_lineups = sum(1 for c in ceiling_scores if c >= 235)
        competitive_lineups = sum(1 for c in ceiling_scores if c >= 225)
        total_lineups = len(ceiling_scores)
        
        print(f"\n🎯 TOURNAMENT COMPETITIVENESS:")
        print(f"    ⭐ 235+ ceiling lineups: {elite_lineups}/{total_lineups} ({elite_lineups/total_lineups*100:.0f}%)")
        print(f"    💪 225+ ceiling lineups: {competitive_lineups}/{total_lineups} ({competitive_lineups/total_lineups*100:.0f}%)")
        
        # Diversity analysis
        unique_teams = master_df['Stack_Team'].nunique()
        unique_systems = master_df['System_Type'].nunique()
        
        print(f"\n📊 PORTFOLIO DIVERSITY:")
        print(f"    🏈 Team stacks: {unique_teams} different teams")
        print(f"    🎯 System types: {unique_systems} different systems")
        
        # Risk assessment
        avg_upside = master_df['Upside_Ratio'].mean()
        
        print(f"\n⚡ UPSIDE POTENTIAL:")
        print(f"    🚀 Average upside ratio: {avg_upside:.1f}x")
        print(f"    💥 Ceiling potential: {ceiling_scores.mean():.1f} FPPG average")
        
        # Tournament readiness rating
        if elite_lineups >= total_lineups * 0.6:
            rating = "LEGENDARY 👑"
        elif competitive_lineups >= total_lineups * 0.8:
            rating = "ELITE ⭐"
        elif competitive_lineups >= total_lineups * 0.6:
            rating = "STRONG 💪"
        else:
            rating = "GOOD ✅"
        
        print(f"\n🏆 TOURNAMENT READINESS: {rating}")
        
        # Top 5 lineups showcase
        print(f"\n🌟 TOP 5 MASTER LINEUPS:")
        top_lineups = master_df.nlargest(5, 'Tournament_Score')
        
        for i, (_, lineup) in enumerate(top_lineups.iterrows(), 1):
            print(f"  {i}. {lineup['Lineup_ID']} ({lineup['System_Type']})")
            print(f"     {lineup['Projected_FPPG']:.1f} proj → {lineup['Ceiling_FPPG']:.1f} ceil | {lineup['Stack_Team']} stack | Score: {lineup['Tournament_Score']:.3f}")
        
        return {
            'avg_ceiling': ceiling_scores.mean(),
            'avg_projection': projection_scores.mean(),
            'elite_lineups': elite_lineups,
            'competitive_lineups': competitive_lineups,
            'total_lineups': total_lineups,
            'unique_teams': unique_teams,
            'tournament_rating': rating
        }
    
    def run_master_combination(self):
        """Run the complete master tournament combination"""
        print("🏆 MASTER TOURNAMENT COMBINER")
        print("Selecting the ultimate tournament portfolio from all systems")
        print("="*80)
        
        try:
            # Load all tournament lineups
            all_lineups_df = self.load_all_tournament_lineups()
            
            if all_lineups_df is None or len(all_lineups_df) == 0:
                print("❌ No tournament lineups found to combine!")
                return
            
            # Analyze lineup quality
            analyzed_df = self.analyze_lineup_quality(all_lineups_df)
            
            # Select master portfolio
            selected_lineups = self.select_master_portfolio(analyzed_df, target_lineups=15)
            
            if not selected_lineups:
                print("❌ Failed to select master portfolio!")
                return
            
            # Create master export
            master_df, filepath = self.create_master_export(selected_lineups)
            
            # Analyze final portfolio
            portfolio_stats = self.analyze_master_portfolio(master_df)
            
            print(f"\n🎉 MASTER COMBINATION COMPLETE!")
            print(f"🏆 Created ultimate tournament portfolio: {len(selected_lineups)} lineups")
            print(f"🎯 Tournament Rating: {portfolio_stats['tournament_rating']}")
            print(f"📊 Average Ceiling: {portfolio_stats['avg_ceiling']:.1f} FPPG")
            print(f"⚡ Ready to dominate tournaments!")
            
            return filepath
            
        except Exception as e:
            print(f"Error in master combination: {e}")
            import traceback
            traceback.print_exc()

def main():
    print("🏆 MASTER TOURNAMENT COMBINER")
    print("Creating the ultimate tournament portfolio")
    print("="*80)
    
    combiner = MasterTournamentCombiner()
    combiner.run_master_combination()

if __name__ == "__main__":
    main()
