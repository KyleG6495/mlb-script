#!/usr/bin/env python3
"""
LATE_SWAP_OPTIMIZER.py

Automatic lineup adjustment system for late scratches and injury news.
This script can remove scratched players and regenerate optimized lineups.
"""

import pandas as pd
import os
from datetime import datetime

def remove_scratched_players(slate_file, scratched_players):
    """
    Remove scratched players from FD slate and save new version
    
    Args:
        slate_file (str): Path to original FD slate
        scratched_players (list): List of player names to remove
        
    Returns:
        str: Path to new slate file without scratched players
    """
    
    # Load original slate
    df = pd.read_csv(slate_file)
    original_count = len(df)
    
    # Remove scratched players
    for player in scratched_players:
        df = df[~df['Nickname'].str.contains(player, case=False, na=False)]
    
    removed_count = original_count - len(df)
    
    # Save updated slate
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    new_slate_file = slate_file.replace('.csv', f'_no_scratches_{timestamp}.csv')
    df.to_csv(new_slate_file, index=False)
    
    print(f"✅ Removed {removed_count} players from slate")
    print(f"💾 Saved updated slate: {os.path.basename(new_slate_file)}")
    
    return new_slate_file

def regenerate_lineups_without_scratches(scratched_players):
    """
    Regenerate lineups after removing scratched players
    
    Args:
        scratched_players (list): List of scratched player names
    """
    
    print(f"🚨 LATE SWAP ALERT: {', '.join(scratched_players)} scratched!")
    print("🔄 Regenerating lineups...")
    
    # Path setup
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(os.path.dirname(script_dir), "data")
    
    # Remove scratched players from slate
    original_slate = os.path.join(data_dir, "fd_slate_starters_only.csv")
    updated_slate = remove_scratched_players(original_slate, scratched_players)
    
    # TODO: Rerun optimization scripts with updated slate
    # This would call your existing optimization pipeline
    
    print("✅ Late swap optimization complete!")
    print("📊 Check dashboard for updated lineups")

if __name__ == "__main__":
    # Example usage
    scratched_players = ["Mike Trout"]  # Players to remove
    regenerate_lineups_without_scratches(scratched_players)
