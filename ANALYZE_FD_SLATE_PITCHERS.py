import pandas as pd

def analyze_fd_slate_pitchers():
    """
    Analyze the FanDuel slate pitchers to identify issues
    """
    
    print("=== FANDUEL SLATE PITCHER ANALYSIS ===")
    print()
    
    # Load the slate
    df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv")
    
    # Filter to pitchers only
    pitchers = df[df['Position'] == 'P'].copy()
    
    print(f"Total pitchers in slate: {len(pitchers)}")
    print()
    
    # Analyze injury status
    print("=== INJURY ANALYSIS ===")
    injured_pitchers = pitchers[pitchers['Injury Indicator'].notna()]
    print(f"Pitchers with injuries: {len(injured_pitchers)}")
    
    if len(injured_pitchers) > 0:
        print("\nINJURED PITCHERS:")
        print("Name | Salary | Injury | Details")
        print("-" * 50)
        for _, row in injured_pitchers.iterrows():
            name = f"{row['First Name']} {row['Last Name']}"
            print(f"{name:20} | ${row['Salary']:,} | {row['Injury Indicator']:2} | {row['Injury Details']}")
    
    # Analyze probable pitcher status
    print(f"\n=== PROBABLE PITCHER ANALYSIS ===")
    probable_pitchers = pitchers[pitchers['Probable Pitcher'] == 'Yes']
    print(f"Probable pitchers: {len(probable_pitchers)}")
    
    if len(probable_pitchers) > 0:
        print(f"\nPROBABLE PITCHERS:")
        print("Name | Salary | FPPG")
        print("-" * 40)
        for _, row in probable_pitchers.iterrows():
            name = f"{row['First Name']} {row['Last Name']}"
            print(f"{name:20} | ${row['Salary']:,} | {row['FPPG']:5.1f}")
    
    # Analyze expensive pitchers
    print(f"\n=== EXPENSIVE PITCHER ANALYSIS ($9K+) ===")
    expensive_pitchers = pitchers[pitchers['Salary'] >= 9000]
    print(f"Expensive pitchers ($9K+): {len(expensive_pitchers)}")
    
    # Count how many expensive pitchers have issues
    expensive_injured = expensive_pitchers[expensive_pitchers['Injury Indicator'].notna()]
    expensive_not_probable = expensive_pitchers[expensive_pitchers['Probable Pitcher'] != 'Yes']
    
    print(f"Expensive pitchers with injuries: {len(expensive_injured)}")
    print(f"Expensive pitchers NOT probable: {len(expensive_not_probable)}")
    
    print(f"\nEXPENSIVE PITCHERS WITH PROBLEMS:")
    print("Name | Salary | FPPG | Injury | Probable")
    print("-" * 60)
    
    for _, row in expensive_pitchers.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        injury = row['Injury Indicator'] if pd.notna(row['Injury Indicator']) else "Healthy"
        probable = row['Probable Pitcher'] if pd.notna(row['Probable Pitcher']) else "No"
        
        # Mark problematic ones
        problem = ""
        if pd.notna(row['Injury Indicator']) or row['Probable Pitcher'] != 'Yes':
            problem = " ERROR:"
        
        print(f"{name:20} | ${row['Salary']:,} | {row['FPPG']:5.1f} | {injury:8} | {probable:8}{problem}")
    
    # Show the clean, playable expensive pitchers
    print(f"\n=== CLEAN EXPENSIVE PITCHERS (No injury, Probable) ===")
    clean_expensive = expensive_pitchers[
        (expensive_pitchers['Injury Indicator'].isna()) & 
        (expensive_pitchers['Probable Pitcher'] == 'Yes')
    ]
    
    if len(clean_expensive) > 0:
        print("Name | Salary | FPPG")
        print("-" * 40)
        for _, row in clean_expensive.iterrows():
            name = f"{row['First Name']} {row['Last Name']}"
            print(f"{name:20} | ${row['Salary']:,} | {row['FPPG']:5.1f}")
    else:
        print("ERROR: NO CLEAN EXPENSIVE PITCHERS AVAILABLE!")
    
    # Value pitcher analysis
    print(f"\n=== VALUE PITCHER ANALYSIS ($6K-8K) ===")
    value_pitchers = pitchers[
        (pitchers['Salary'] >= 6000) & 
        (pitchers['Salary'] < 9000) &
        (pitchers['Injury Indicator'].isna()) & 
        (pitchers['Probable Pitcher'] == 'Yes')
    ]
    
    print(f"Clean value pitchers: {len(value_pitchers)}")
    if len(value_pitchers) > 0:
        print("Name | Salary | FPPG")
        print("-" * 40)
        for _, row in value_pitchers.head(10).iterrows():  # Top 10
            name = f"{row['First Name']} {row['Last Name']}"
            print(f"{name:20} | ${row['Salary']:,} | {row['FPPG']:5.1f}")

if __name__ == "__main__":
    analyze_fd_slate_pitchers()
