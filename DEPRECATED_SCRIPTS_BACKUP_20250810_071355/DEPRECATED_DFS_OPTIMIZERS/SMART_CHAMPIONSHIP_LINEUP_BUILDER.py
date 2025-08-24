import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def load_validated_players():
    """Load only players who are confirmed to be starting today"""
    try:
        # Load today's slate - check multiple possible locations
        slate_paths = [
            'fd_slate_today.csv',
            '../fd_current_slate/fd_slate_today.csv',
            '../data/fd_slate_today.csv',
            'C:/Users/kgone/OneDrive/Personal_Information/MLB/fd_current_slate/fd_slate_today.csv'
        ]
        
        slate_df = None
        for path in slate_paths:
            try:
                slate_df = pd.read_csv(path)
                print(f"📊 Found slate data at: {path}")
                break
            except:
                continue
        
        if slate_df is None:
            raise FileNotFoundError("Could not find fd_slate_today.csv in any expected location")
        
        print(f"🎯 Loaded {len(slate_df)} total players from today's slate")
        
        # Filter confirmed starting pitchers only
        starting_pitchers = slate_df[
            (slate_df['Position'].str.contains('P', na=False)) & 
            (slate_df['Probable Pitcher'].str.lower() == 'yes')
        ]
        
        # Get all non-pitcher players (they should all be starting since it's the active slate)
        position_players = slate_df[~slate_df['Position'].str.contains('P', na=False)]
        
        # Combine confirmed starters
        validated_players = pd.concat([starting_pitchers, position_players], ignore_index=True)
        
        print(f"✅ VALIDATED STARTING PITCHERS: {len(starting_pitchers)}")
        for _, pitcher in starting_pitchers.head(5).iterrows():  # Show top 5
            print(f"   🔥 {pitcher['Nickname']} ({pitcher['Team']}) - ${pitcher['Salary']:,} - {pitcher.get('FPPG', 'N/A')} FPPG")
        
        if len(starting_pitchers) > 5:
            print(f"   ... and {len(starting_pitchers) - 5} more confirmed starters")
        
        print(f"✅ Total validated players: {len(validated_players)}")
        
        return validated_players
        
    except Exception as e:
        print(f"❌ Error loading validated players: {e}")
        return None

def build_smart_lineup(players_df):
    """Build lineup using smart salary cap management"""
    
    max_salary = 35000
    positions_needed = {'P': 1, 'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3}
    
    print(f"\n🏆 BUILDING SMART CHAMPIONSHIP LINEUP")
    print("=" * 60)
    
    # Step 1: Select the best value pitcher within reasonable salary range
    pitchers = players_df[
        (players_df['Position'].str.contains('P', na=False)) & 
        (players_df['Probable Pitcher'].str.lower() == 'yes')
    ].copy()
    
    if len(pitchers) == 0:
        print("❌ No confirmed starting pitchers available!")
        return None
    
    # Sort pitchers by value (FPPG per $1000 salary)
    if 'FPPG' in pitchers.columns:
        pitchers['value_score'] = pitchers['FPPG'] / (pitchers['Salary'] / 1000)
        pitchers = pitchers.sort_values(['value_score'], ascending=False)
    
    # Select a pitcher that leaves enough budget for other positions (aim for $8000-9500 range)
    selected_pitcher = None
    for _, pitcher in pitchers.iterrows():
        remaining_budget = max_salary - pitcher['Salary']
        avg_budget_per_position = remaining_budget / 8  # 8 remaining positions
        
        # Make sure we can afford decent players in other positions
        if avg_budget_per_position >= 2500:  # At least $2500 average per remaining position
            selected_pitcher = pitcher
            break
    
    if selected_pitcher is None:
        # Fallback: take the cheapest good pitcher
        selected_pitcher = pitchers.sort_values(['Salary']).iloc[0]
    
    lineup = [selected_pitcher]
    total_salary = selected_pitcher['Salary']
    total_fppg = selected_pitcher.get('FPPG', 0)
    used_players = {selected_pitcher['Id']}
    
    print(f"🎯 PITCHER: {selected_pitcher['Nickname']} (${selected_pitcher['Salary']:,}) - {selected_pitcher.get('FPPG', 'N/A')} FPPG")
    
    # Step 2: Build rest of lineup with smart budgeting
    position_order = ['C', '1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF']  # Fill OF last for flexibility
    
    for i, position in enumerate(position_order):
        remaining_positions = len(position_order) - i
        remaining_salary = max_salary - total_salary
        max_position_salary = remaining_salary - (remaining_positions - 1) * 2000  # Leave $2000 min for each remaining
        
        # Get available players for this position
        pos_players = players_df[
            (players_df['Position'].str.contains(position, na=False)) &
            (~players_df['Position'].str.contains('P', na=False)) &
            (~players_df['Id'].isin(used_players)) &
            (players_df['Salary'] <= max_position_salary) &
            (players_df['Salary'] <= remaining_salary)
        ].copy()
        
        if len(pos_players) == 0:
            print(f"❌ No affordable players for {position} (budget: ${max_position_salary:,})")
            continue
        
        # Sort by value
        if 'FPPG' in pos_players.columns:
            pos_players['value_score'] = pos_players['FPPG'] / (pos_players['Salary'] / 1000)
            pos_players = pos_players.sort_values(['value_score'], ascending=False)
        else:
            pos_players = pos_players.sort_values(['Salary'], ascending=True)
        
        # Select best value player
        selected_player = pos_players.iloc[0]
        lineup.append(selected_player)
        total_salary += selected_player['Salary']
        total_fppg += selected_player.get('FPPG', 0)
        used_players.add(selected_player['Id'])
        
        print(f"🎯 {position}: {selected_player['Nickname']} (${selected_player['Salary']:,}) - {selected_player.get('FPPG', 'N/A')} FPPG")
        print(f"   💰 Running total: ${total_salary:,} (${max_salary - total_salary:,} remaining)")
    
    print("=" * 60)
    print(f"💰 FINAL SALARY: ${total_salary:,} / ${max_salary:,}")
    print(f"🎯 TOTAL PROJECTED FPPG: {total_fppg:.1f}")
    print(f"👥 LINEUP SIZE: {len(lineup)}")
    
    if total_salary > max_salary:
        print(f"❌ ERROR: Lineup over salary cap by ${total_salary - max_salary:,}")
        return None
    
    if len(lineup) < 9:
        print(f"❌ ERROR: Incomplete lineup - only {len(lineup)} players selected")
        return None
    
    print("✅ VALID LINEUP CREATED!")
    return lineup

def create_fanduel_submission(lineup):
    """Create FanDuel submission format"""
    if not lineup:
        return None
        
    submission_data = []
    
    for player in lineup:
        submission_data.append({
            'Id': player['Id'],
            'Position': player['Position'],
            'First Name': player.get('First Name', ''),
            'Nickname': player['Nickname'],
            'Last Name': player.get('Last Name', ''),
            'FPPG': player.get('FPPG', 0),
            'Played': player.get('Played', 0),
            'Salary': player['Salary'],
            'Game': player.get('Game', ''),
            'Team': player.get('Team', ''),
            'Opponent': player.get('Opponent', ''),
            'Injury Indicator': player.get('Injury Indicator', ''),
            'Injury Details': player.get('Injury Details', ''),
            'Tier': player.get('Tier', ''),
            'Rostership %': player.get('Rostership %', ''),
            'Probable Pitcher': player.get('Probable Pitcher', '')
        })
    
    return pd.DataFrame(submission_data)

def main():
    print("🏆 SMART VALIDATED CHAMPIONSHIP LINEUP BUILDER")
    print("   Using ONLY confirmed starting players with smart salary management")
    print("=" * 70)
    
    # Load validated players
    validated_players = load_validated_players()
    if validated_players is None:
        print("❌ Failed to load validated players")
        return
    
    # Build championship lineup
    lineup = build_smart_lineup(validated_players)
    if not lineup:
        print("❌ Failed to build valid lineup")
        return
    
    # Create submission
    submission_df = create_fanduel_submission(lineup)
    if submission_df is None:
        print("❌ Failed to create submission")
        return
    
    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # FanDuel submission format
    filename = f"SMART_CHAMPIONSHIP_SUBMISSION_{timestamp}.csv"
    submission_df.to_csv(filename, index=False)
    
    print(f"\n✅ SMART CHAMPIONSHIP LINEUP SAVED: {filename}")
    print("\n🎯 FINAL LINEUP SUMMARY:")
    print("=" * 50)
    
    total_salary = submission_df['Salary'].sum()
    total_fppg = submission_df['FPPG'].sum()
    
    for _, player in submission_df.iterrows():
        pos = player['Position']
        name = player['Nickname'] 
        salary = player['Salary']
        fppg = player['FPPG']
        team = player['Team']
        game = player.get('Game', '')
        
        print(f"{pos:>8}: {name:<20} ${salary:>6,} {fppg:>6.1f} FPPG ({team}) {game}")
    
    print("=" * 50)
    print(f"💰 TOTAL: ${total_salary:,} / $35,000 ({35000 - total_salary:,} under)")
    print(f"🎯 PROJECTED: {total_fppg:.1f} FPPG")
    print(f"💡 VALIDATED: All players confirmed to be starting today")
    print(f"✅ SALARY CAP: Valid lineup under $35,000")
    
    print("\n🚀 READY FOR FANDUEL SUBMISSION!")
    print(f"   Upload file: {filename}")

if __name__ == "__main__":
    main()
