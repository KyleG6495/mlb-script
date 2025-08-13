import pandas as pd

def investigate_shane_bieber():
    """
    Investigate what happened to Shane Bieber on August 12th
    """
    
    print("=== SHANE BIEBER INVESTIGATION ===")
    
    # Load actual results
    actual_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    print("Searching for Shane Bieber in actual results...")
    bieber_results = actual_df[actual_df['name'].str.contains('Bieber', case=False, na=False)]
    
    if len(bieber_results) > 0:
        print("\n🔍 FOUND SHANE BIEBER:")
        for _, row in bieber_results.iterrows():
            print(f"Name: {row['name']}")
            print(f"Position: {row['position']}")
            print(f"Team: {row['team']}")
            print(f"Date: {row['date']}")
            print(f"FanDuel Points: {row['fanduel_points']}")
            print(f"Innings Pitched: {row['innings_pitched']}")
            print(f"Hits Allowed: {row['hits_allowed']}")
            print(f"Earned Runs: {row['earned_runs']}")
            print(f"Wins: {row['wins']}")
            print(f"Losses: {row['losses']}")
    else:
        print("❌ Shane Bieber NOT FOUND in actual results!")
        print("This means he either:")
        print("1. Didn't play on August 12th")
        print("2. Was scratched from the game")
        print("3. Is on IL (Injured List)")
    
    # Check corrected slate
    print("\n=== SHANE BIEBER IN CORRECTED SLATE ===")
    corrected_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\CORRECTED_slate_20250813_072440.csv")
    
    bieber_slate = corrected_df[corrected_df['Last Name'].str.contains('Bieber', case=False, na=False)]
    if len(bieber_slate) > 0:
        for _, row in bieber_slate.iterrows():
            print(f"Name: {row['First Name']} {row['Last Name']}")
            print(f"Position: {row['Position']}")
            print(f"Salary: ${row['Salary']:,}")
            print(f"Corrected FPPG: {row['FPPG']:.1f}")
            print(f"Original FPPG: {row['original_fppg']:.1f}")
            print(f"Game: {row['Game']}")
            print(f"Team: {row['Team']}")
            print(f"Opponent: {row['Opp']}")
            
            # Check if he was on IL
            if 'IL' in str(row.get('Status', '')):
                print("🚨 STATUS: ON INJURED LIST!")
            
    # Check original slate 
    print("\n=== SHANE BIEBER IN ORIGINAL SLATE ===")
    original_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\vegas_adjusted_slate_20250812_135729.csv")
    
    bieber_original = original_df[original_df['Last Name'].str.contains('Bieber', case=False, na=False)]
    if len(bieber_original) > 0:
        for _, row in bieber_original.iterrows():
            print(f"Name: {row['First Name']} {row['Last Name']}")
            print(f"Position: {row['Position']}")
            print(f"Salary: ${row['Salary']:,}")
            print(f"FPPG: {row['FPPG']:.1f}")
            print(f"Game: {row['Game']}")
            print(f"Team: {row['Team']}")
            print(f"Opponent: {row['Opp']}")

def check_expensive_pitcher_performance():
    """
    Check how all expensive pitchers performed on August 12th
    """
    
    print("\n\n=== EXPENSIVE PITCHER PERFORMANCE ANALYSIS ===")
    
    # Load slate and actual results
    slate_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\vegas_adjusted_slate_20250812_135729.csv")
    actual_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    # Find expensive pitchers
    expensive_pitchers = slate_df[(slate_df['Position'] == 'P') & (slate_df['Salary'] >= 9000)].copy()
    
    print(f"Found {len(expensive_pitchers)} pitchers $9K+:")
    print("\nExpensive Pitcher Performance:")
    print("Name | Salary | Projected | Actual")
    print("-" * 45)
    
    # Merge with actual results
    expensive_pitchers['full_name'] = (expensive_pitchers['First Name'] + ' ' + expensive_pitchers['Last Name']).str.strip()
    actual_df['full_name'] = actual_df['name'].str.strip()
    
    merged = expensive_pitchers.merge(
        actual_df[['full_name', 'fanduel_points']], 
        on='full_name', 
        how='left'
    )
    
    total_projected = 0
    total_actual = 0
    pitched_count = 0
    
    for _, row in merged.iterrows():
        actual_points = row['fanduel_points'] if pd.notna(row['fanduel_points']) else 0
        
        name = f"{row['First Name']} {row['Last Name']}"
        print(f"{name:20} | ${row['Salary']:,} | {row['FPPG']:8.1f} | {actual_points:6.1f}")
        
        total_projected += row['FPPG']
        total_actual += actual_points
        if actual_points > 0:
            pitched_count += 1
    
    print(f"\nSUMMARY:")
    print(f"Total expensive pitchers: {len(expensive_pitchers)}")
    print(f"Actually pitched: {pitched_count}")
    print(f"Average projected: {total_projected/len(expensive_pitchers):.1f}")
    print(f"Average actual: {total_actual/len(expensive_pitchers):.1f}")
    print(f"Projection error: {total_actual - total_projected:.1f}")
    
    if total_actual < total_projected * 0.5:
        print("🚨 MASSIVE BUST! Expensive pitchers failed completely!")

if __name__ == "__main__":
    investigate_shane_bieber()
    check_expensive_pitcher_performance()
