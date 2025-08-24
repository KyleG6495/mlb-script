import pandas as pd

def analyze_august_12_slate():
    """
    Complete analysis of August 12th FanDuel slate
    """
    
    # Load the August 12th slate
    df = pd.read_csv(r'c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv')
    
    print("=== AUGUST 12TH FANDUEL SLATE COMPLETE ANALYSIS ===")
    print(f"Total players: {len(df)}")
    print()
    
    # Position breakdown
    print("=== POSITION BREAKDOWN ===")
    print(df['Position'].value_counts())
    print()
    
    # Injury analysis
    print("=== INJURY ANALYSIS ===")
    injured = df[df['Injury Indicator'].notna()]
    print(f"Total injured players: {len(injured)}")
    if len(injured) > 0:
        print("Injury types:")
        print(injured['Injury Indicator'].value_counts())
        print()
        print("Injury details:")
        print(injured['Injury Details'].value_counts())
    print()
    
    # Pitcher analysis
    pitchers = df[df['Position'] == 'P']
    print(f"=== PITCHER ANALYSIS ({len(pitchers)} total) ===")
    
    # Probable pitchers
    probable = pitchers[pitchers['Probable Pitcher'] == 'Yes']
    print(f"Probable pitchers: {len(probable)}")
    
    # Injured pitchers
    injured_pitchers = pitchers[pitchers['Injury Indicator'].notna()]
    print(f"Injured pitchers: {len(injured_pitchers)}")
    print()
    
    if len(injured_pitchers) > 0:
        print("ALL INJURED PITCHERS:")
        print("Name | Salary | Injury | Details")
        print("-" * 60)
        for _, row in injured_pitchers.iterrows():
            name = f"{row['First Name']} {row['Last Name']}"
            injury = row['Injury Indicator'] if pd.notna(row['Injury Indicator']) else ""
            details = row['Injury Details'] if pd.notna(row['Injury Details']) else ""
            print(f"{name:25} | ${row['Salary']:,} | {injury:2} | {details}")
    
    print()
    
    # Show all expensive pitchers ($9K+) with status
    expensive_pitchers = pitchers[pitchers['Salary'] >= 9000].sort_values('Salary', ascending=False)
    print(f"EXPENSIVE PITCHERS ($9K+): {len(expensive_pitchers)}")
    print("Name | Salary | FPPG | Injury | Probable")
    print("-" * 65)
    for _, row in expensive_pitchers.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        injury = row['Injury Indicator'] if pd.notna(row['Injury Indicator']) else "Healthy"
        probable = "Yes" if row['Probable Pitcher'] == 'Yes' else "No"
        print(f"{name:20} | ${row['Salary']:,} | {row['FPPG']:5.1f} | {injury:8} | {probable}")
    
    print()
    
    # Show the CLEAN probable pitchers
    clean_pitchers = pitchers[
        (pitchers['Injury Indicator'].isna()) & 
        (pitchers['Probable Pitcher'] == 'Yes')
    ].sort_values('Salary', ascending=False)
    
    print(f"CLEAN PROBABLE PITCHERS (No injury, Probable=Yes): {len(clean_pitchers)}")
    print("Name | Salary | FPPG")
    print("-" * 45)
    for _, row in clean_pitchers.iterrows():
        name = f"{row['First Name']} {row['Last Name']}"
        print(f"{name:25} | ${row['Salary']:,} | {row['FPPG']:5.1f}")
    
    print()
    
    # Show position players with injuries
    position_players = df[df['Position'] != 'P']
    injured_position = position_players[position_players['Injury Indicator'].notna()]
    
    print(f"INJURED POSITION PLAYERS: {len(injured_position)}")
    if len(injured_position) > 0:
        print("Name | Position | Salary | Injury")
        print("-" * 50)
        for _, row in injured_position.head(20).iterrows():  # Show top 20
            name = f"{row['First Name']} {row['Last Name']}"
            injury = row['Injury Indicator'] if pd.notna(row['Injury Indicator']) else ""
            print(f"{name:20} | {row['Position']:8} | ${row['Salary']:,} | {injury}")

if __name__ == "__main__":
    analyze_august_12_slate()
