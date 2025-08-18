import pandas as pd

def investigate_shane_baz():
    """
    Investigate what happened to Shane Baz on August 12th
    """
    
    print("=== SHANE BAZ AUGUST 12TH INVESTIGATION ===")
    print()
    
    # Load slate data
    import glob
    filtered_files = glob.glob(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\FILTERED_CORRECTED_slate_*.csv")
    slate_df = pd.read_csv(filtered_files[-1])
    
    # Find Shane Baz
    baz = slate_df[slate_df['Last Name'].str.contains('Baz', na=False)]
    if len(baz) > 0:
        print("DATA: SHANE BAZ SLATE DATA:")
        for col in ['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'Game', 'Team', 'Opponent', 'Injury Indicator', 'Tier']:
            if col in baz.columns:
                print(f"{col}: {baz.iloc[0][col]}")
        print()
    
    # Load actual results
    try:
        actual_df = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
        
        # Find Shane Baz in actuals
        baz_actual = actual_df[actual_df['name'].str.contains('Baz', na=False, case=False)]
        
        print("TARGET: SHANE BAZ ACTUAL RESULTS:")
        if len(baz_actual) > 0:
            print(f"Name: {baz_actual.iloc[0]['name']}")
            print(f"FanDuel Points: {baz_actual.iloc[0]['fanduel_points']}")
            if 'team' in baz_actual.columns:
                print(f"Team: {baz_actual.iloc[0]['team']}")
            if 'opponent' in baz_actual.columns:
                print(f"Opponent: {baz_actual.iloc[0]['opponent']}")
            print()
            
            # Check if he actually played
            if baz_actual.iloc[0]['fanduel_points'] == 0:
                print("ERROR: Shane Baz scored 0 points - likely didn't pitch")
                print(" This suggests he was probable but scratched last minute")
        else:
            print("ERROR: Shane Baz not found in actual results")
            print(" This suggests he didn't play at all")
        
    except Exception as e:
        print(f"Error loading actuals: {e}")
    
    print()
    print("=== TOP PERFORMING PITCHERS ON AUGUST 12TH ===")
    
    try:
        # Show top actual pitchers
        pitcher_actuals = actual_df[actual_df['position'] == 'P'].copy()
        pitcher_actuals = pitcher_actuals.sort_values('fanduel_points', ascending=False)
        
        print("Top 10 Actual Pitcher Performances:")
        for i in range(min(10, len(pitcher_actuals))):
            pitcher = pitcher_actuals.iloc[i]
            print(f"{i+1:2}. {pitcher['name']:20} | {pitcher['fanduel_points']:6.1f} pts")
            
        print()
        
        # Cross-reference with our slate
        print("TARGET: Which top pitchers were in our FILTERED slate?")
        top_pitchers = pitcher_actuals.head(10)
        
        for _, pitcher in top_pitchers.iterrows():
            pitcher_name = pitcher['name'].strip()
            
            # Try to find in slate (match by last name since formats differ)
            last_name = pitcher_name.split()[-1]
            slate_match = slate_df[slate_df['Last Name'].str.contains(last_name, na=False, case=False)]
            
            if len(slate_match) > 0:
                salary = slate_match.iloc[0]['Salary']
                fppg = slate_match.iloc[0]['FPPG']
                print(f"SUCCESS: {pitcher_name:20} | {pitcher['fanduel_points']:6.1f} pts | ${salary:,} | {fppg:5.1f} proj")
            else:
                print(f"ERROR: {pitcher_name:20} | {pitcher['fanduel_points']:6.1f} pts | NOT IN SLATE")
                
    except Exception as e:
        print(f"Error analyzing pitchers: {e}")

if __name__ == "__main__":
    investigate_shane_baz()
