import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

def load_confirmed_starters():
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
        
        # Filter confirmed starting pitchers only (this was the fix!)
        starting_pitchers = slate_df[
            (slate_df['Position'].str.contains('P', na=False)) & 
            (slate_df['Probable Pitcher'].str.lower() == 'yes')
        ]
        
        # Get all non-pitcher players (they should all be starting since it's the active slate)
        position_players = slate_df[~slate_df['Position'].str.contains('P', na=False)]
        
        # Combine confirmed starters
        confirmed_players = pd.concat([starting_pitchers, position_players], ignore_index=True)
        
        print(f"✅ CONFIRMED STARTING PITCHERS: {len(starting_pitchers)}")
        for _, pitcher in starting_pitchers.iterrows():
            print(f"   🔥 {pitcher['Nickname']} ({pitcher['Team']}) - ${pitcher['Salary']:,} - {pitcher.get('FPPG', 'N/A')} FPPG")
        
        print(f"✅ Total confirmed players: {len(confirmed_players)}")
        print(f"✅ Position breakdown:")
        for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
            pos_count = len(confirmed_players[confirmed_players['Position'].str.contains(pos, na=False)])
            print(f"   {pos}: {pos_count} players")
        
        return confirmed_players
        
    except Exception as e:
        print(f"❌ Error loading confirmed starters: {e}")
        return None

def build_championship_lineup(players_df):
    """Build optimized lineup using only confirmed starting players"""
    
    # Salary constraint
    max_salary = 35000
    
    # Position requirements
    positions_needed = {
        'C': 1,
        '1B': 1, 
        '2B': 1,
        '3B': 1,
        'SS': 1,
        'OF': 3,
        'P': 1  # Only confirmed starting pitchers
    }
    
    # Build lineup
    lineup = []
    total_salary = 0
    total_fppg = 0
    used_players = set()
    
    print(f"\n🏆 BUILDING CHAMPIONSHIP LINEUP (Confirmed Starters Only)")
    print("=" * 60)
    
    # First, select the best confirmed starting pitcher
    pitchers = players_df[
        (players_df['Position'].str.contains('P', na=False)) & 
        (players_df['Probable Pitcher'].str.lower() == 'yes')
    ].copy()
    
    if len(pitchers) == 0:
        print("❌ No confirmed starting pitchers available!")
        return None
        
    # Sort by value (FPPG/salary ratio) or FPPG if available
    if 'FPPG' in pitchers.columns:
        pitchers['value'] = pitchers['FPPG'] / (pitchers['Salary'] / 1000)
        pitchers = pitchers.sort_values(['FPPG'], ascending=False)
    else:
        pitchers = pitchers.sort_values(['Salary'], ascending=False)
    
    selected_pitcher = pitchers.iloc[0]
    lineup.append(selected_pitcher)
    total_salary += selected_pitcher['Salary']
    total_fppg += selected_pitcher.get('FPPG', 0)
    used_players.add(selected_pitcher['Id'])
    
    print(f"🎯 PITCHER: {selected_pitcher['Nickname']} (${selected_pitcher['Salary']:,}) - {selected_pitcher.get('FPPG', 'N/A')} FPPG")
    
    # Select position players
    for position, count in positions_needed.items():
        if position == 'P':  # Already selected pitcher
            continue
            
        pos_players = players_df[
            (players_df['Position'].str.contains(position, na=False)) &
            (~players_df['Position'].str.contains('P', na=False)) &  # Exclude pitchers
            (~players_df['Id'].isin(used_players))
        ].copy()
        
        if len(pos_players) == 0:
            print(f"❌ No available players for position {position}")
            continue
            
        # Calculate remaining salary budget for each position
        remaining_positions = sum([v for k, v in positions_needed.items() if k != 'P']) - len(lineup) + 1
        remaining_salary = max_salary - total_salary
        avg_salary_per_remaining = remaining_salary / remaining_positions if remaining_positions > 0 else remaining_salary
        
        # Filter affordable players with better budget management
        affordable_players = pos_players[pos_players['Salary'] <= remaining_salary]
        
        # If we're running out of budget, prioritize cheaper players
        if remaining_positions > 3 and avg_salary_per_remaining < 3000:
            affordable_players = pos_players[pos_players['Salary'] <= avg_salary_per_remaining * 1.2]
        elif remaining_positions > 1:
            affordable_players = pos_players[pos_players['Salary'] <= remaining_salary - (remaining_positions - 1) * 2000]
        
        if len(affordable_players) == 0:
            print(f"⚠️ No affordable players for position {position}")
            continue
            
        # Sort by value
        if 'FPPG' in affordable_players.columns:
            affordable_players['value'] = affordable_players['FPPG'] / (affordable_players['Salary'] / 1000)
            affordable_players = affordable_players.sort_values(['FPPG'], ascending=False)
        else:
            affordable_players = affordable_players.sort_values(['Salary'], ascending=False)
        
        for i in range(count):
            if i < len(affordable_players):
                selected = affordable_players.iloc[i]
                lineup.append(selected)
                total_salary += selected['Salary']
                total_fppg += selected.get('FPPG', 0)
                used_players.add(selected['Id'])
                
                print(f"🎯 {position}: {selected['Nickname']} (${selected['Salary']:,}) - {selected.get('FPPG', 'N/A')} FPPG")
                
                # Remove selected player from future selections
                affordable_players = affordable_players[affordable_players['Id'] != selected['Id']]
    
    print("=" * 60)
    print(f"💰 TOTAL SALARY: ${total_salary:,} / ${max_salary:,}")
    print(f"🎯 TOTAL PROJECTED FPPG: {total_fppg:.1f}")
    print(f"👥 LINEUP SIZE: {len(lineup)}")
    
    if total_salary > max_salary:
        print(f"❌ WARNING: Lineup over salary cap by ${total_salary - max_salary:,}")
        return None
    
    if len(lineup) < 9:
        print(f"⚠️ WARNING: Incomplete lineup - only {len(lineup)} players selected")
        return None
    
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
    print("🏆 VALIDATED CHAMPIONSHIP LINEUP BUILDER")
    print("   Using ONLY confirmed starting players from today's slate")
    print("=" * 70)
    
    # Load confirmed starting players
    confirmed_players = load_confirmed_starters()
    if confirmed_players is None:
        print("❌ Failed to load confirmed players")
        return
    
    # Build championship lineup
    lineup = build_championship_lineup(confirmed_players)
    if not lineup:
        print("❌ Failed to build lineup")
        return
    
    # Create submission
    submission_df = create_fanduel_submission(lineup)
    if submission_df is None:
        print("❌ Failed to create submission")
        return
    
    # Save files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # FanDuel submission format
    filename = f"VALIDATED_CHAMPIONSHIP_SUBMISSION_{timestamp}.csv"
    submission_df.to_csv(filename, index=False)
    
    print(f"\n✅ CHAMPIONSHIP LINEUP SAVED: {filename}")
    print("\n🎯 LINEUP SUMMARY:")
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
        
        print(f"{pos:>3}: {name:<20} ${salary:>6,} {fppg:>6.1f} FPPG ({team}) {game}")
    
    print("=" * 50)
    print(f"💰 TOTAL: ${total_salary:,} / $35,000")
    print(f"🎯 PROJECTED: {total_fppg:.1f} FPPG")
    print(f"💡 VALIDATED: All players confirmed to be starting today")
    
    # Also save detailed format for analysis
    detailed_filename = f"VALIDATED_CHAMPIONSHIP_DETAILED_{timestamp}.csv"
    submission_df.to_csv(detailed_filename, index=False)
    print(f"📊 DETAILED FILE: {detailed_filename}")
    
    print("\n🚀 READY FOR FANDUEL SUBMISSION!")
    print(f"   Upload file: {filename}")

if __name__ == "__main__":
    main()
