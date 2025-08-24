#!/usr/bin/env python3
"""
ELITE LINEUP SELECTOR
Uses advanced techniques to select optimal lineups for different contest types
"""

import pandas as pd
import numpy as np
import json
import os
from datetime import datetime

class EliteLineupSelector:
    def __init__(self):
        self.data_dir = "../data"
        self.slate_dir = "../fd_current_slate"
        self.lineups_analyzed = []
        
    def load_generated_lineups(self):
        """Load all your generated lineups"""
        lineup_files = [
            "Enhanced_Lineups_FD_Format_20250821_135239.csv",
            "Enhanced_Lineups_FD_Format_20250821_134036.csv",
            # Add other lineup files you've generated
        ]
        
        all_lineups = []
        for file in lineup_files:
            file_path = f"{self.slate_dir}/{file}"
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                for _, lineup in df.iterrows():
                    all_lineups.append({
                        'source_file': file,
                        'lineup_id': lineup['Lineup_ID'],
                        'contest_type': lineup.get('Contest_Type', 'unknown'),
                        'total_salary': lineup['Total_Salary'],
                        'total_projection': lineup['Total_Projection'],
                        'lineup_data': lineup
                    })
        
        print(f"✅ Loaded {len(all_lineups)} generated lineups")
        return all_lineups

    def analyze_lineup_characteristics(self, lineup_data):
        """Analyze each lineup's characteristics for contest selection"""
        
        # Extract players from FD format
        positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF2', 'OF3', 'UTIL']
        players = []
        
        for pos in positions:
            if pd.notna(lineup_data[pos]) and lineup_data[pos] != '':
                player_info = lineup_data[pos].split(':')
                if len(player_info) == 2:
                    players.append(player_info[1])  # Player name
        
        # Load slate data for analysis
        slate_df = pd.read_csv(f"{self.slate_dir}/fd_slate_today.csv")
        
        characteristics = {
            'ceiling_score': self._calculate_ceiling_score(players, slate_df),
            'floor_score': self._calculate_floor_score(players, slate_df),
            'variance_score': 0,  # Will calculate
            'chalk_percentage': self._calculate_chalk_percentage(players, slate_df),
            'contrarian_score': self._calculate_contrarian_score(players, slate_df),
            'correlation_strength': self._calculate_correlation_strength(players, slate_df),
            'stack_type': self._identify_stack_type(players, slate_df),
            'leverage_score': 0,  # Will calculate
            'contest_suitability': {}
        }
        
        # Calculate variance and leverage
        characteristics['variance_score'] = characteristics['ceiling_score'] - characteristics['floor_score']
        characteristics['leverage_score'] = characteristics['ceiling_score'] / max(characteristics['chalk_percentage'], 5.0)
        
        # Determine contest suitability
        characteristics['contest_suitability'] = self._determine_contest_suitability(characteristics)
        
        return characteristics

    def _calculate_ceiling_score(self, players, slate_df):
        """Calculate lineup ceiling potential"""
        total_ceiling = 0
        for player in players:
            player_row = slate_df[slate_df['Nickname'].str.contains(player, case=False, na=False)]
            if len(player_row) > 0:
                base_proj = player_row.iloc[0]['FPPG']
                # Apply position-based ceiling multipliers
                position = player_row.iloc[0]['Position']
                multipliers = {'P': 2.2, 'C': 1.6, '1B': 1.8, '2B': 1.5, '3B': 1.8, 'SS': 1.6, 'OF': 1.7}
                ceiling_mult = multipliers.get(position, 1.6)
                total_ceiling += base_proj * ceiling_mult
        return round(total_ceiling, 1)

    def _calculate_floor_score(self, players, slate_df):
        """Calculate lineup floor (worst-case scenario)"""
        total_floor = 0
        for player in players:
            player_row = slate_df[slate_df['Nickname'].str.contains(player, case=False, na=False)]
            if len(player_row) > 0:
                base_proj = player_row.iloc[0]['FPPG']
                # Floor is typically 40-60% of projection
                floor_mult = 0.5
                total_floor += base_proj * floor_mult
        return round(total_floor, 1)

    def _calculate_chalk_percentage(self, players, slate_df):
        """Estimate how chalky this lineup is"""
        chalk_scores = []
        
        # Load ownership data if available
        ownership_files = [f for f in os.listdir(self.data_dir) if 'ownership' in f.lower()]
        if ownership_files:
            ownership_df = pd.read_csv(f"{self.data_dir}/{ownership_files[-1]}")
            
            for player in players:
                player_ownership = ownership_df[ownership_df['player_name'].str.contains(player, case=False, na=False)]
                if len(player_ownership) > 0:
                    chalk_scores.append(player_ownership.iloc[0]['ownership'] * 100)  # Convert to percentage
                else:
                    chalk_scores.append(8.0)  # Default ownership
        else:
            # Estimate based on salary and projection
            for player in players:
                player_row = slate_df[slate_df['Nickname'].str.contains(player, case=False, na=False)]
                if len(player_row) > 0:
                    salary = player_row.iloc[0]['Salary']
                    projection = player_row.iloc[0]['FPPG']
                    # Higher salary + projection = higher ownership
                    estimated_ownership = min(25.0, (projection * salary) / 500)
                    chalk_scores.append(estimated_ownership)
        
        return round(np.mean(chalk_scores), 1)

    def _calculate_contrarian_score(self, players, slate_df):
        """How contrarian is this lineup"""
        return max(0, 20 - self._calculate_chalk_percentage(players, slate_df))

    def _calculate_correlation_strength(self, players, slate_df):
        """Measure how well players correlate"""
        # Count team stacks
        teams = []
        for player in players:
            player_row = slate_df[slate_df['Nickname'].str.contains(player, case=False, na=False)]
            if len(player_row) > 0:
                teams.append(player_row.iloc[0]['Team'])
        
        # Calculate correlation based on team stacking
        team_counts = pd.Series(teams).value_counts()
        max_stack = team_counts.max() if len(team_counts) > 0 else 1
        
        # Score: 1-10 based on largest stack
        correlation_scores = {1: 1, 2: 3, 3: 5, 4: 7, 5: 9, 6: 10}
        return correlation_scores.get(max_stack, 10)

    def _identify_stack_type(self, players, slate_df):
        """Identify the primary stacking strategy"""
        teams = []
        for player in players:
            player_row = slate_df[slate_df['Nickname'].str.contains(player, case=False, na=False)]
            if len(player_row) > 0:
                teams.append(player_row.iloc[0]['Team'])
        
        team_counts = pd.Series(teams).value_counts()
        max_stack = team_counts.max()
        
        if max_stack >= 5:
            return f"Full Stack ({team_counts.index[0]})"
        elif max_stack >= 4:
            return f"4-Man Stack ({team_counts.index[0]})"
        elif max_stack >= 3:
            return f"3-Man Stack ({team_counts.index[0]})"
        else:
            return "Balanced/Stars & Scrubs"

    def _determine_contest_suitability(self, characteristics):
        """Determine which contest types this lineup is best for"""
        suitability = {}
        
        # Cash Game Suitability (50/50s, Double-ups)
        cash_score = 0
        if characteristics['floor_score'] >= 60:  # High floor
            cash_score += 30
        if characteristics['variance_score'] <= 40:  # Low variance
            cash_score += 25
        if characteristics['chalk_percentage'] <= 15:  # Not too chalky
            cash_score += 20
        if characteristics['correlation_strength'] >= 6:  # Good correlation
            cash_score += 25
        
        suitability['cash_games'] = min(100, cash_score)
        
        # Small Tournament Suitability (Single Entry, Small Field)
        small_tournament_score = 0
        if characteristics['ceiling_score'] >= 120:  # High ceiling
            small_tournament_score += 30
        if 10 <= characteristics['chalk_percentage'] <= 20:  # Moderate chalk
            small_tournament_score += 25
        if characteristics['leverage_score'] >= 2.5:  # Good leverage
            small_tournament_score += 25
        if characteristics['correlation_strength'] >= 5:  # Decent correlation
            small_tournament_score += 20
        
        suitability['small_tournaments'] = min(100, small_tournament_score)
        
        # Large Tournament Suitability (Milly Maker, etc.)
        large_tournament_score = 0
        if characteristics['ceiling_score'] >= 140:  # Very high ceiling
            large_tournament_score += 35
        if characteristics['contrarian_score'] >= 10:  # Contrarian enough
            large_tournament_score += 30
        if characteristics['leverage_score'] >= 4.0:  # High leverage
            large_tournament_score += 35
        
        suitability['large_tournaments'] = min(100, large_tournament_score)
        
        return suitability

    def select_optimal_lineups(self, max_lineups_per_contest=5):
        """Select optimal lineups for each contest type"""
        
        all_lineups = self.load_generated_lineups()
        
        analyzed_lineups = []
        
        print("🔍 Analyzing lineup characteristics...")
        for lineup in all_lineups:
            characteristics = self.analyze_lineup_characteristics(lineup['lineup_data'])
            
            analyzed_lineups.append({
                **lineup,
                'characteristics': characteristics
            })
        
        # Sort lineups by contest type suitability
        selections = {
            'cash_games': sorted(analyzed_lineups, 
                               key=lambda x: x['characteristics']['contest_suitability']['cash_games'], 
                               reverse=True)[:max_lineups_per_contest],
            
            'small_tournaments': sorted(analyzed_lineups, 
                                      key=lambda x: x['characteristics']['contest_suitability']['small_tournaments'], 
                                      reverse=True)[:max_lineups_per_contest],
            
            'large_tournaments': sorted(analyzed_lineups, 
                                      key=lambda x: x['characteristics']['contest_suitability']['large_tournaments'], 
                                      reverse=True)[:max_lineups_per_contest]
        }
        
        return selections

    def display_lineup_recommendations(self, selections):
        """Display the recommended lineups for each contest type"""
        
        print("\n🎯 ELITE LINEUP SELECTION RECOMMENDATIONS")
        print("=" * 55)
        
        for contest_type, lineups in selections.items():
            print(f"\n🏆 {contest_type.upper().replace('_', ' ')}:")
            print("-" * 40)
            
            for i, lineup in enumerate(lineups, 1):
                char = lineup['characteristics']
                suit = char['contest_suitability'][contest_type]
                
                # Rating icons
                if suit >= 80:
                    icon = "🔥 ELITE"
                elif suit >= 65:
                    icon = "⭐ GREAT"
                elif suit >= 50:
                    icon = "📊 GOOD"
                else:
                    icon = "⚠️ OKAY"
                
                print(f"{icon} #{i} {lineup['lineup_id']}")
                print(f"   Suitability: {suit}% | Ceiling: {char['ceiling_score']}")
                print(f"   Floor: {char['floor_score']} | Chalk: {char['chalk_percentage']}%")
                print(f"   Strategy: {char['stack_type']}")
                print(f"   Leverage: {char['leverage_score']:.1f}")
                print()
        
        # Overall strategy recommendations
        print("💡 CONTEST STRATEGY RECOMMENDATIONS:")
        print("-" * 35)
        
        best_cash = selections['cash_games'][0] if selections['cash_games'] else None
        best_small = selections['small_tournaments'][0] if selections['small_tournaments'] else None
        best_large = selections['large_tournaments'][0] if selections['large_tournaments'] else None
        
        if best_cash:
            print(f"💰 Cash Games: Focus on {best_cash['lineup_id']} (High floor: {best_cash['characteristics']['floor_score']})")
        
        if best_small:
            print(f"🎯 Small Tournaments: {best_small['lineup_id']} (Balanced ceiling: {best_small['characteristics']['ceiling_score']})")
        
        if best_large:
            print(f"🚀 Large Tournaments: {best_large['lineup_id']} (Max ceiling: {best_large['characteristics']['ceiling_score']})")

def main():
    selector = EliteLineupSelector()
    
    print("🎯 ELITE LINEUP SELECTOR")
    print("=" * 30)
    print("Selecting optimal lineups from your generated pool...")
    
    # Select optimal lineups
    selections = selector.select_optimal_lineups(max_lineups_per_contest=3)
    
    # Display recommendations
    selector.display_lineup_recommendations(selections)
    
    # Save selections for easy reference
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"../data/lineup_selections_{timestamp}.json"
    
    # Convert to serializable format
    serializable_selections = {}
    for contest_type, lineups in selections.items():
        serializable_selections[contest_type] = []
        for lineup in lineups:
            serializable_selections[contest_type].append({
                'lineup_id': lineup['lineup_id'],
                'suitability_score': lineup['characteristics']['contest_suitability'][contest_type],
                'ceiling': lineup['characteristics']['ceiling_score'],
                'floor': lineup['characteristics']['floor_score'],
                'chalk_percentage': lineup['characteristics']['chalk_percentage'],
                'stack_type': lineup['characteristics']['stack_type'],
                'leverage': lineup['characteristics']['leverage_score']
            })
    
    with open(output_file, 'w') as f:
        json.dump(serializable_selections, f, indent=2)
    
    print(f"\n💾 Selections saved to: {output_file}")
    print("\n🏆 Ready to enter optimal lineups in contests!")

if __name__ == "__main__":
    main()
