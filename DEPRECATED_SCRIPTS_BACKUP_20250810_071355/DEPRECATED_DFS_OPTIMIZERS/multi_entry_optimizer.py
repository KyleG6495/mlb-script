#!/usr/bin/env python3
"""
Multi-Entry Lineup Generator
Creates correlated lineup sets for quintuple/multi-entry strategies
"""

import pandas as pd
import numpy as np
from itertools import combinations
import os

class MultiEntryGenerator:
    def __init__(self):
        self.lineups = []
        self.player_exposures = {}
        
    def load_enhanced_lineups(self):
        """Load all enhanced lineups"""
        data_dir = '../data/'
        lineup_files = [f for f in os.listdir(data_dir) if f.startswith('enhanced_lineup_') and f.endswith('.csv')]
        
        for file in lineup_files:
            df = pd.read_csv(data_dir + file)
            strategy = 'gpp' if 'gpp' in file else 'balanced' if 'balanced' in file else 'cash'
            
            self.lineups.append({
                'filename': file,
                'strategy': strategy,
                'players': df,
                'projection': df['Projected_FPPG'].sum(),
                'salary': df['Salary'].sum()
            })
        
        print(f"✅ Loaded {len(self.lineups)} enhanced lineups")
        
    def calculate_player_exposures(self):
        """Calculate how often each player appears across lineups"""
        all_players = {}
        
        for lineup in self.lineups:
            for _, player in lineup['players'].iterrows():
                name = player['Nickname']
                if name not in all_players:
                    all_players[name] = {
                        'count': 0,
                        'total_lineups': len(self.lineups),
                        'avg_projection': 0,
                        'avg_salary': 0,
                        'positions': set(),
                        'teams': set()
                    }
                
                all_players[name]['count'] += 1
                all_players[name]['avg_projection'] += player['Projected_FPPG']
                all_players[name]['avg_salary'] += player['Salary']
                all_players[name]['positions'].add(player['Primary_Position'])
                all_players[name]['teams'].add(player['Team'])
        
        # Calculate averages and exposure rates
        for name, data in all_players.items():
            data['exposure_rate'] = data['count'] / data['total_lineups']
            data['avg_projection'] /= data['count']
            data['avg_salary'] /= data['count']
        
        self.player_exposures = all_players
        
    def generate_quintuple_strategy(self):
        """Generate optimized 5-lineup strategy for GPP"""
        print("\n🎯 QUINTUPLE STRATEGY GENERATOR")
        print("=" * 40)
        
        # Filter to GPP lineups
        gpp_lineups = [l for l in self.lineups if l['strategy'] == 'gpp']
        
        if len(gpp_lineups) < 3:
            print("❌ Need at least 3 GPP lineups for quintuple strategy")
            return
        
        # Use top 3 GPP lineups + create 2 variations
        base_lineups = sorted(gpp_lineups, key=lambda x: x['projection'], reverse=True)[:3]
        
        print("📋 RECOMMENDED QUINTUPLE LINEUP SET:")
        print("-" * 40)
        
        for i, lineup in enumerate(base_lineups):
            print(f"Lineup {i+1}: {lineup['filename']}")
            print(f"  💰 ${lineup['salary']:,} | 📈 {lineup['projection']:.1f} FPPG")
            
            # Show key players
            top_players = lineup['players'].nlargest(3, 'Projected_FPPG')
            stars = ", ".join([f"{row['Nickname']} ({row['Primary_Position']})" 
                              for _, row in top_players.iterrows()])
            print(f"  ⭐ Stars: {stars}")
            print()
        
        # Create 2 contrarian variations
        print("🎲 CONTRARIAN VARIATIONS:")
        print("-" * 25)
        
        # Find lower-owned players for contrarian plays
        contrarian_candidates = []
        for name, data in self.player_exposures.items():
            if data['exposure_rate'] <= 0.33 and data['avg_projection'] >= 10:  # Low exposure, decent projection
                contrarian_candidates.append((name, data))
        
        contrarian_candidates.sort(key=lambda x: x[1]['avg_projection'], reverse=True)
        
        print("Lineup 4: Contrarian Stack")
        print("  🎯 Strategy: Fade chalk, target low-owned stack")
        if contrarian_candidates:
            top_contrarian = contrarian_candidates[:3]
            for name, data in top_contrarian:
                print(f"    • {name}: {data['avg_projection']:.1f} proj, {data['exposure_rate']:.0%} owned")
        
        print("\nLineup 5: Pivot Play")
        print("  🎯 Strategy: Different game stack from main lineups")
        
        return base_lineups
    
    def generate_cash_multi_entry(self):
        """Generate 2-3 lineup strategy for cash games"""
        print("\n💰 CASH GAME MULTI-ENTRY")
        print("=" * 30)
        
        # Filter to balanced lineups (best for cash)
        cash_lineups = [l for l in self.lineups if l['strategy'] == 'balanced']
        
        if len(cash_lineups) < 2:
            print("❌ Need at least 2 balanced lineups for cash multi-entry")
            return
        
        # Use top 2-3 balanced lineups
        best_cash = sorted(cash_lineups, key=lambda x: x['projection'], reverse=True)[:3]
        
        print("📋 RECOMMENDED CASH LINEUP SET:")
        print("-" * 35)
        
        for i, lineup in enumerate(best_cash):
            print(f"Lineup {i+1}: {lineup['filename']}")
            print(f"  💰 ${lineup['salary']:,} | 📈 {lineup['projection']:.1f} FPPG")
            
            # Calculate floor score (conservative)
            min_proj = lineup['players']['Projected_FPPG'].min()
            floor_estimate = min_proj * 9 * 0.8  # Conservative floor
            print(f"  🔒 Est. Floor: {floor_estimate:.1f} FPPG")
            print()
        
        return best_cash
    
    def analyze_correlation_opportunities(self):
        """Find optimal stack combinations across lineups"""
        print("\n🔗 CORRELATION ANALYSIS")
        print("=" * 25)
        
        # Find teams with multiple players across lineups
        team_exposures = {}
        
        for lineup in self.lineups:
            for _, player in lineup['players'].iterrows():
                team = player['Team']
                if team not in team_exposures:
                    team_exposures[team] = {
                        'players': set(),
                        'total_projection': 0,
                        'count': 0
                    }
                
                team_exposures[team]['players'].add(player['Nickname'])
                team_exposures[team]['total_projection'] += player['Projected_FPPG']
                team_exposures[team]['count'] += 1
        
        # Find best stacking opportunities
        best_stacks = []
        for team, data in team_exposures.items():
            if data['count'] >= 6:  # Team appears in multiple lineups/positions
                avg_proj = data['total_projection'] / data['count']
                best_stacks.append((team, len(data['players']), avg_proj))
        
        best_stacks.sort(key=lambda x: x[2], reverse=True)
        
        print("🏟️ TOP STACKING OPPORTUNITIES:")
        for team, unique_players, avg_proj in best_stacks[:5]:
            print(f"  {team}: {unique_players} unique players, {avg_proj:.1f} avg proj")
    
    def generate_exposure_report(self):
        """Generate player exposure report for multi-entry"""
        print("\n📊 PLAYER EXPOSURE REPORT")
        print("=" * 30)
        
        # Sort by projection and show key players
        sorted_players = sorted(
            self.player_exposures.items(), 
            key=lambda x: x[1]['avg_projection'], 
            reverse=True
        )
        
        print("🌟 CORE PLAYS (High Exposure):")
        for name, data in sorted_players[:8]:
            if data['exposure_rate'] >= 0.5:  # 50%+ exposure
                print(f"  {name}: {data['exposure_rate']:.0%} exposure, "
                      f"{data['avg_projection']:.1f} proj, ${data['avg_salary']:.0f}")
        
        print("\n🎯 PIVOT PLAYS (Medium Exposure):")
        for name, data in sorted_players:
            if 0.2 <= data['exposure_rate'] < 0.5 and data['avg_projection'] >= 12:
                print(f"  {name}: {data['exposure_rate']:.0%} exposure, "
                      f"{data['avg_projection']:.1f} proj, ${data['avg_salary']:.0f}")
        
        print("\n🎲 CONTRARIAN PLAYS (Low Exposure, High Upside):")
        for name, data in sorted_players:
            if data['exposure_rate'] <= 0.33 and data['avg_projection'] >= 10:
                print(f"  {name}: {data['exposure_rate']:.0%} exposure, "
                      f"{data['avg_projection']:.1f} proj, ${data['avg_salary']:.0f}")
                
    def run_multi_entry_analysis(self):
        """Run complete multi-entry analysis"""
        print("🎯 MULTI-ENTRY LINEUP OPTIMIZER")
        print("=" * 45)
        
        self.load_enhanced_lineups()
        self.calculate_player_exposures()
        
        # Generate strategies
        self.generate_quintuple_strategy()
        self.generate_cash_multi_entry()
        self.analyze_correlation_opportunities()
        self.generate_exposure_report()
        
        print(f"\n✅ Multi-entry analysis complete!")
        print(f"💡 Use the recommended lineup sets for optimal coverage")

if __name__ == "__main__":
    generator = MultiEntryGenerator()
    generator.run_multi_entry_analysis()
