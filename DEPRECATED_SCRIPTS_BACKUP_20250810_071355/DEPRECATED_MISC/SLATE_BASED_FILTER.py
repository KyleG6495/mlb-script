#!/usr/bin/env python3
"""
SLATE-BASED PLAYER FILTER
==========================
Use the injury indicators, game info, and other slate data 
to filter out players who shouldn't be picked for today's slate.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class SlateBasedFilter:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def load_and_analyze_slate(self):
        """Load slate and analyze what data we have"""
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"📊 Loading and analyzing today's slate ({today})...")
        
        slate_file = self.slate_dir / "fd_slate_today.csv"
        slate_df = pd.read_csv(slate_file)
        
        print(f"✅ Loaded {len(slate_df)} players from slate")
        
        # Analyze available columns
        print(f"📋 Available columns: {list(slate_df.columns)}")
        
        # Check injury status
        if 'Injury Indicator' in slate_df.columns:
            injured = slate_df['Injury Indicator'].notna().sum()
            print(f"🏥 Players with injury indicators: {injured}")
            
        # Check games
        if 'Game' in slate_df.columns:
            unique_games = slate_df['Game'].nunique()
            print(f"⚾ Unique games in slate: {unique_games}")
            
        # Check probable pitchers
        if 'Probable Pitcher' in slate_df.columns:
            probable = (slate_df['Probable Pitcher'] == 'Yes').sum()
            print(f"🎯 Probable pitchers marked: {probable}")
            
        return slate_df
    
    def filter_injured_players(self, slate_df):
        """Remove players marked as injured"""
        print("🏥 Filtering out injured players...")
        
        if 'Injury Indicator' not in slate_df.columns:
            print("⚠️ No injury indicator column found")
            return slate_df
        
        # Count injured players
        injured_players = slate_df['Injury Indicator'].notna()
        injured_count = injured_players.sum()
        
        if injured_count > 0:
            print(f"❌ Removing {injured_count} injured players:")
            injured_list = slate_df[injured_players][['First Name', 'Last Name', 'Injury Indicator', 'Injury Details']]
            for _, player in injured_list.head(10).iterrows():  # Show first 10
                name = f"{player['First Name']} {player['Last Name']}"
                injury = f"{player['Injury Indicator']}"
                details = player.get('Injury Details', '')
                print(f"  • {name}: {injury} {details}")
            
            if injured_count > 10:
                print(f"  ... and {injured_count - 10} more")
        
        # Filter out injured players
        clean_slate = slate_df[~injured_players].copy()
        print(f"✅ {len(clean_slate)} players remaining after injury filter")
        
        return clean_slate
    
    def filter_non_probable_pitchers(self, slate_df):
        """Remove pitchers who aren't probable starters"""
        print("⚾ Filtering non-probable pitchers...")
        
        if 'Probable Pitcher' not in slate_df.columns:
            print("⚠️ No probable pitcher column found")
            return slate_df
        
        # Get pitchers
        pitchers = slate_df[slate_df['Position'] == 'P'].copy()
        
        if len(pitchers) == 0:
            return slate_df
        
        # Check probable status
        probable_pitchers = pitchers['Probable Pitcher'] == 'Yes'
        non_probable = pitchers[~probable_pitchers]
        
        print(f"📊 Pitcher analysis:")
        print(f"  Total pitchers: {len(pitchers)}")
        print(f"  Probable starters: {probable_pitchers.sum()}")
        print(f"  Non-probable: {len(non_probable)}")
        
        if len(non_probable) > 0:
            print(f"❌ Removing {len(non_probable)} non-probable pitchers:")
            for _, pitcher in non_probable.head(10).iterrows():
                name = f"{pitcher['First Name']} {pitcher['Last Name']}"
                game = pitcher.get('Game', 'N/A')
                print(f"  • {name} ({game})")
        
        # Remove non-probable pitchers
        non_probable_ids = set(non_probable['Id'])
        clean_slate = slate_df[~slate_df['Id'].isin(non_probable_ids)].copy()
        
        print(f"✅ {len(clean_slate)} players remaining after pitcher filter")
        
        return clean_slate
    
    def filter_low_quality_projections(self, slate_df):
        """Remove players with obviously bad projections"""
        print("📊 Filtering low quality projections...")
        
        before_count = len(slate_df)
        
        # Remove players with very low/suspicious projections
        filtered = slate_df[
            (slate_df['FPPG'] >= 2.0) &  # At least 2 FPPG
            (slate_df['FPPG'] <= 60.0) &  # Max 60 FPPG (sanity check)
            (slate_df['Salary'] >= 2000)  # At least $2000 salary
        ].copy()
        
        removed = before_count - len(filtered)
        print(f"❌ Removed {removed} players with poor projections")
        print(f"✅ {len(filtered)} quality players remaining")
        
        return filtered
    
    def analyze_filtered_slate(self, filtered_slate):
        """Analyze the cleaned slate"""
        print("\n📈 FILTERED SLATE ANALYSIS:")
        print("="*50)
        
        print(f"👥 Total players: {len(filtered_slate)}")
        
        # Position breakdown
        if 'Position' in filtered_slate.columns:
            pos_counts = filtered_slate['Position'].value_counts()
            print(f"📊 Position breakdown:")
            for pos, count in pos_counts.items():
                print(f"  {pos}: {count}")
        
        # FPPG stats
        fppg_stats = filtered_slate['FPPG'].describe()
        print(f"🎯 FPPG statistics:")
        print(f"  Range: {fppg_stats['min']:.1f} - {fppg_stats['max']:.1f}")
        print(f"  Average: {fppg_stats['mean']:.1f}")
        print(f"  Median: {fppg_stats['50%']:.1f}")
        
        # Salary stats
        salary_stats = filtered_slate['Salary'].describe()
        print(f"💰 Salary statistics:")
        print(f"  Range: ${salary_stats['min']:,.0f} - ${salary_stats['max']:,.0f}")
        print(f"  Average: ${salary_stats['mean']:,.0f}")
        
        return filtered_slate
    
    def build_filtered_lineup(self, filtered_slate):
        """Build lineup using properly filtered slate"""
        print("\n🏗️ Building lineup with filtered slate...")
        
        # Calculate value
        filtered_slate['value'] = filtered_slate['FPPG'] / (filtered_slate['Salary'] / 1000)
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = filtered_slate[~filtered_slate['Id'].isin(used_ids)]
            else:
                candidates = filtered_slate[
                    (filtered_slate['Roster Position'].str.contains(position, na=False)) &
                    (~filtered_slate['Id'].isin(used_ids))
                ]
            
            # Budget management
            positions_left = len(positions_needed) - len(selected_players) - 1
            min_budget_needed = positions_left * 2000
            max_spend = remaining_budget - min_budget_needed
            
            affordable = candidates[candidates['Salary'] <= max_spend]
            
            if affordable.empty:
                print(f"❌ No affordable {position} players (need <${max_spend})")
                return None
            
            # Pick best value
            chosen = affordable.loc[affordable['value'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
            
            print(f"  ✅ {position}: {chosen['First Name']} {chosen['Last Name']} (${chosen['Salary']}, {chosen['FPPG']:.1f} FPPG)")
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_fppg = sum(p['FPPG'] for p in selected_players)
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_fppg': total_fppg,
                'lineup_type': 'FILTERED_SLATE'
            }
        
        return None
    
    def save_filtered_lineup(self, lineup):
        """Save the filtered lineup"""
        if not lineup:
            print("❌ No lineup to save")
            return None
        
        # Create lineup
        lineup_data = []
        players = lineup['players']
        
        lineup_row = {
            'Lineup_ID': 'FILTERED_01',
            'Type': 'Slate_Filtered',
            'Total_Salary': lineup['total_salary'],
            'Total_FPPG': round(lineup['total_fppg'], 2)
        }
        
        # Map positions
        of_count = 0
        for player in players:
            name = f"{player['First Name']} {player['Last Name']}"
            pos = str(player['Roster Position'])
            
            if 'P' in pos and 'P' not in lineup_row:
                lineup_row['P'] = name
            elif 'C/1B' in pos and 'C/1B' not in lineup_row:
                lineup_row['C/1B'] = name
            elif '2B' in pos and '2B' not in lineup_row:
                lineup_row['2B'] = name
            elif '3B' in pos and '3B' not in lineup_row:
                lineup_row['3B'] = name
            elif 'SS' in pos and 'SS' not in lineup_row:
                lineup_row['SS'] = name
            elif 'OF' in pos and of_count == 0:
                lineup_row['OF'] = name
                of_count += 1
            elif 'OF' in pos and of_count == 1:
                lineup_row['OF2'] = name
                of_count += 1
            elif 'OF' in pos and of_count == 2:
                lineup_row['OF3'] = name
                of_count += 1
            else:
                lineup_row['UTIL'] = name
        
        lineup_data.append(lineup_row)
        
        # Save
        df = pd.DataFrame(lineup_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.slate_dir / f"FILTERED_Lineup_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n💾 FILTERED LINEUP SAVED: {output_file}")
        print(f"💰 Salary: ${lineup['total_salary']:,}")
        print(f"🎯 Projected FPPG: {lineup['total_fppg']:.1f}")
        
        return output_file
    
    def run_slate_filtering(self):
        """Run complete slate-based filtering"""
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"🚀 SLATE-BASED PLAYER FILTERING FOR TODAY ({today})")
        print("Using injury indicators and game data from the slate itself")
        print("="*70)
        
        # Load slate
        slate_df = self.load_and_analyze_slate()
        
        # Apply filters
        print("\n🔧 APPLYING FILTERS:")
        filtered_slate = self.filter_injured_players(slate_df)
        filtered_slate = self.filter_non_probable_pitchers(filtered_slate)
        filtered_slate = self.filter_low_quality_projections(filtered_slate)
        
        # Analyze results
        filtered_slate = self.analyze_filtered_slate(filtered_slate)
        
        # Build lineup
        lineup = self.build_filtered_lineup(filtered_slate)
        
        if lineup:
            output_file = self.save_filtered_lineup(lineup)
            
            print(f"\n🎉 SUCCESS!")
            print(f"📁 Filtered lineup: {output_file}")
            print(f"💡 This should perform MUCH better by excluding:")
            print(f"  ❌ Injured players (marked in slate)")
            print(f"  ❌ Non-probable pitchers")
            print(f"  ❌ Players with poor projections")
            
            return lineup
        else:
            print("❌ Failed to build filtered lineup")
            return None

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"🔍 SLATE-BASED FILTERING FOR TODAY ({today})")
    print("Using the slate's own data to filter out bad picks")
    print("="*70)
    
    filter_system = SlateBasedFilter()
    
    try:
        lineup = filter_system.run_slate_filtering()
        
        if lineup:
            print(f"\n🏆 FILTERED LINEUP READY!")
            print(f"   This should crush the previous terrible lineups!")
        else:
            print("❌ Filtering failed")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
