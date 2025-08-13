import pandas as pd
import numpy as np
from datetime import datetime
import glob
import os

def emergency_projection_fixes():
    """
    Apply EMERGENCY fixes to projections based on August 12th learnings
    """
    
    print("=== EMERGENCY PROJECTION FIXES ===")
    print("Applying critical corrections based on August 12th analysis...")
    
    # Check what slate files we have
    data_dir = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    patterns = [
        "vegas_adjusted_slate_*.csv",
        "enhanced_projections_*.csv",
        "fd_slate_today.csv"
    ]
    
    all_files = []
    for pattern in patterns:
        files = glob.glob(os.path.join(data_dir, pattern))
        all_files.extend(files)
    
    # Sort by modification time (newest first)
    all_files = sorted(set(all_files), key=os.path.getmtime, reverse=True)
    
    print(f"Found {len(all_files)} slate files:")
    for i, file in enumerate(all_files[:5]):  # Show first 5
        mtime = os.path.getmtime(file)
        mtime_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{i+1}. {os.path.basename(file)} ({mtime_str})")
    
    if not all_files:
        print("❌ No slate files found! Need to generate today's slate first.")
        return None
    
    # Use the most recent slate
    today_slate = all_files[0]
    print(f"\n📊 Using slate: {os.path.basename(today_slate)}")
    
    slate_df = pd.read_csv(today_slate)
    print(f"Original slate: {len(slate_df)} players")
    
    # Apply emergency corrections based on August 12th learnings
    slate_df['original_fppg'] = slate_df['FPPG'].copy()
    
    # Fix 1: PENALIZE expensive pitchers heavily (they all busted on Aug 12)
    expensive_pitchers = (slate_df['Position'] == 'P') & (slate_df['Salary'] >= 9500)
    slate_df.loc[expensive_pitchers, 'FPPG'] *= 0.6  # Reduce by 40%
    print(f"📉 Penalized {expensive_pitchers.sum()} expensive pitchers ($9.5K+)")
    
    # Fix 2: BOOST value range players ($3K-4K) - where all the explosions were
    value_range = (slate_df['Salary'] >= 3000) & (slate_df['Salary'] <= 4000)
    slate_df.loc[value_range, 'FPPG'] *= 1.3  # Boost by 30%
    print(f"📈 Boosted {value_range.sum()} value players ($3K-4K)")
    
    # Fix 3: BOOST SS/3B positions specifically (Neto, Caminero exploded)
    explosive_positions = slate_df['Position'].str.contains('SS|3B', na=False)
    slate_df.loc[explosive_positions, 'FPPG'] *= 1.2  # Boost by 20%
    print(f"📈 Boosted {explosive_positions.sum()} SS/3B players")
    
    # Fix 4: Target mid-range pitchers ($7K-9K) - Will Warren won here
    mid_pitchers = (slate_df['Position'] == 'P') & (slate_df['Salary'] >= 7000) & (slate_df['Salary'] < 9500)
    slate_df.loc[mid_pitchers, 'FPPG'] *= 1.15  # Boost by 15%
    print(f"📈 Boosted {mid_pitchers.sum()} mid-range pitchers ($7K-9K)")
    
    # Fix 5: Reduce projections for cheap players (usually don't explode)
    cheap_players = slate_df['Salary'] < 3000
    slate_df.loc[cheap_players, 'FPPG'] *= 0.9  # Slight reduction
    print(f"📉 Reduced {cheap_players.sum()} cheap players (<$3K)")
    
    # Fix 6: Position-specific corrections based on August 12th
    position_adjustments = {
        'C': 1.1,      # Catchers undervalued (Salvador Perez 29.1)
        '1B': 0.95,    # First basemen slightly overvalued
        '2B': 1.05,    # Second basemen boost (Brandon Lowe 26.2)
        'OF': 1.02,    # Outfielders slight boost (Roman Anthony 28.9)
        'P': 0.85      # Pitchers overall overvalued
    }
    
    for pos, multiplier in position_adjustments.items():
        pos_mask = slate_df['Position'].str.contains(pos, na=False)
        before_count = pos_mask.sum()
        slate_df.loc[pos_mask, 'FPPG'] *= multiplier
        print(f"🎯 Adjusted {before_count} {pos} players by {multiplier}x")
    
    # Calculate changes
    slate_df['fppg_change'] = slate_df['FPPG'] - slate_df['original_fppg']
    
    # Show top changes
    print("\n=== TOP PROJECTION INCREASES ===")
    increases = slate_df.nlargest(8, 'fppg_change')[['First Name', 'Last Name', 'Position', 'Salary', 'original_fppg', 'FPPG', 'fppg_change']]
    for _, row in increases.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        print(f"{name:20} ({row['Position']:3}) ${row['Salary']:,} | {row['original_fppg']:5.1f} → {row['FPPG']:5.1f} ({row['fppg_change']:+4.1f})")
    
    print("\n=== TOP PROJECTION DECREASES ===")
    decreases = slate_df.nsmallest(8, 'fppg_change')[['First Name', 'Last Name', 'Position', 'Salary', 'original_fppg', 'FPPG', 'fppg_change']]
    for _, row in decreases.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        print(f"{name:20} ({row['Position']:3}) ${row['Salary']:,} | {row['original_fppg']:5.1f} → {row['FPPG']:5.1f} ({row['fppg_change']:+4.1f})")
    
    # Save corrected slate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(data_dir, f"CORRECTED_slate_{timestamp}.csv")
    slate_df.to_csv(output_file, index=False)
    print(f"\n✅ Saved corrected slate to: {os.path.basename(output_file)}")
    
    # Summary statistics
    print("\n=== CORRECTION SUMMARY ===")
    print(f"Original average projection: {slate_df['original_fppg'].mean():.2f}")
    print(f"Corrected average projection: {slate_df['FPPG'].mean():.2f}")
    print(f"Average change: {slate_df['fppg_change'].mean():+.2f}")
    print(f"Players boosted: {(slate_df['fppg_change'] > 0).sum()}")
    print(f"Players reduced: {(slate_df['fppg_change'] < 0).sum()}")
    
    print("\n🚨 CRITICAL TAKEAWAYS FOR TODAY:")
    print("1. AVOID expensive pitchers ($9.5K+) - they busted hard on Aug 12")
    print("2. TARGET $3K-4K players - where all the explosions happened")
    print("3. PRIORITIZE SS/3B positions - they had massive upside")
    print("4. FOCUS on mid-range pitchers ($7K-9K) - better value")
    print("5. Don't overpay for projections - variance is huge")
    
    return output_file

if __name__ == "__main__":
    corrected_file = emergency_projection_fixes()
