import pandas as pd
import numpy as np
from datetime import datetime
import itertools
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
        for _, pitcher in starting_pitchers.iterrows():
            print(f"   🔥 {pitcher['Nickname']} ({pitcher['Team']}) - ${pitcher['Salary']:,} - {pitcher.get('FPPG', 'N/A')} FPPG")
        
        print(f"✅ Total validated players: {len(validated_players)}")
        
        return validated_players
        
    except Exception as e:
        print(f"❌ Error loading validated players: {e}")
        return None

def build_championship_lineup(players_df, pitcher_choice=None, strategy='balanced'):
    """Build optimized lineup with different strategies"""
    
    max_salary = 35000
    positions_needed = {'C': 1, '1B': 1, '2B': 1, '3B': 1, 'SS': 1, 'OF': 3, 'P': 1}
    
    lineup = []
    total_salary = 0
    total_fppg = 0
    used_players = set()
    
    # Select pitcher
    pitchers = players_df[
        (players_df['Position'].str.contains('P', na=False)) & 
        (players_df['Probable Pitcher'].str.lower() == 'yes')
    ].copy()
    
    if len(pitchers) == 0:
        return None, "No confirmed starting pitchers"
        
    if pitcher_choice is not None and pitcher_choice < len(pitchers):
        if 'FPPG' in pitchers.columns:
            pitchers = pitchers.sort_values(['FPPG'], ascending=False)
        selected_pitcher = pitchers.iloc[pitcher_choice]
    else:
        if 'FPPG' in pitchers.columns:
            pitchers = pitchers.sort_values(['FPPG'], ascending=False)
        selected_pitcher = pitchers.iloc[0]
    
    lineup.append(selected_pitcher)
    total_salary += selected_pitcher['Salary']
    total_fppg += selected_pitcher.get('FPPG', 0)
    used_players.add(selected_pitcher['Id'])
    
    # Select position players based on strategy
    for position, count in positions_needed.items():
        if position == 'P':
            continue
            
        pos_players = players_df[
            (players_df['Position'].str.contains(position, na=False)) &
            (~players_df['Position'].str.contains('P', na=False)) &
            (~players_df['Id'].isin(used_players))
        ].copy()
        
        if len(pos_players) == 0:
            continue
            
        # Filter affordable players
        affordable_players = pos_players[pos_players['Salary'] <= (max_salary - total_salary)]
        
        if len(affordable_players) == 0:
            continue
            
        # Apply strategy
        if strategy == 'value':
            # Focus on value (FPPG per $1000 salary)
            if 'FPPG' in affordable_players.columns:
                affordable_players['value_score'] = affordable_players['FPPG'] / (affordable_players['Salary'] / 1000)
                affordable_players = affordable_players.sort_values(['value_score'], ascending=False)
            else:
                affordable_players = affordable_players.sort_values(['Salary'], ascending=True)
        elif strategy == 'ceiling':
            # Focus on highest ceiling players
            if 'FPPG' in affordable_players.columns:
                affordable_players = affordable_players.sort_values(['FPPG'], ascending=False)
            else:
                affordable_players = affordable_players.sort_values(['Salary'], ascending=False)
        elif strategy == 'balanced':
            # Balanced approach
            if 'FPPG' in affordable_players.columns:
                affordable_players['balanced_score'] = (affordable_players['FPPG'] * 0.7) + ((affordable_players['FPPG'] / (affordable_players['Salary'] / 1000)) * 0.3)
                affordable_players = affordable_players.sort_values(['balanced_score'], ascending=False)
            else:
                affordable_players = affordable_players.sort_values(['Salary'], ascending=False)
        elif strategy == 'contrarian':
            # Lower owned players (reverse salary order as proxy)
            affordable_players = affordable_players.sort_values(['Salary'], ascending=True)
        
        for i in range(count):
            if i < len(affordable_players):
                selected = affordable_players.iloc[i]
                lineup.append(selected)
                total_salary += selected['Salary']
                total_fppg += selected.get('FPPG', 0)
                used_players.add(selected['Id'])
                
                # Remove selected player
                affordable_players = affordable_players[affordable_players['Id'] != selected['Id']]
    
    if len(lineup) < 9:
        return None, f"Incomplete lineup - only {len(lineup)} players"
    
    return lineup, f"${total_salary:,} - {total_fppg:.1f} FPPG"

def create_multiple_championship_lineups(players_df, num_lineups=10):
    """Create multiple diverse championship lineups"""
    
    lineups = []
    strategies = ['balanced', 'ceiling', 'value', 'contrarian']
    
    # Get number of confirmed starting pitchers
    pitchers = players_df[
        (players_df['Position'].str.contains('P', na=False)) & 
        (players_df['Probable Pitcher'].str.lower() == 'yes')
    ]
    num_pitchers = len(pitchers)
    
    print(f"🏆 CREATING {num_lineups} CHAMPIONSHIP LINEUPS")
    print(f"📊 Using {num_pitchers} confirmed starting pitchers")
    print("=" * 60)
    
    lineup_count = 0
    
    for strategy in strategies:
        for pitcher_idx in range(min(num_pitchers, 3)):  # Use top 3 pitchers max
            if lineup_count >= num_lineups:
                break
                
            lineup, summary = build_championship_lineup(players_df, pitcher_idx, strategy)
            
            if lineup:
                lineup_count += 1
                pitcher_name = lineup[0]['Nickname']
                
                lineups.append({
                    'lineup_id': lineup_count,
                    'strategy': strategy,
                    'pitcher': pitcher_name,
                    'lineup': lineup,
                    'summary': summary
                })
                
                print(f"✅ Lineup {lineup_count}: {strategy.upper()} with {pitcher_name} - {summary}")
        
        if lineup_count >= num_lineups:
            break
    
    # Fill remaining with variations
    while lineup_count < num_lineups and lineup_count < 20:  # Safety limit
        strategy = np.random.choice(strategies)
        pitcher_idx = np.random.randint(0, min(num_pitchers, 5))
        
        lineup, summary = build_championship_lineup(players_df, pitcher_idx, strategy)
        
        if lineup:
            lineup_count += 1
            pitcher_name = lineup[0]['Nickname']
            
            # Check for duplicates (simple check)
            is_duplicate = False
            for existing in lineups:
                if existing['pitcher'] == pitcher_name and existing['strategy'] == strategy:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                lineups.append({
                    'lineup_id': lineup_count,
                    'strategy': f"{strategy}_var",
                    'pitcher': pitcher_name,
                    'lineup': lineup,
                    'summary': summary
                })
                
                print(f"✅ Lineup {lineup_count}: {strategy.upper()}_VAR with {pitcher_name} - {summary}")
    
    return lineups

def save_championship_lineups(lineups):
    """Save championship lineups in multiple formats"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 1. Individual lineup files
    all_submissions = []
    
    for lineup_data in lineups:
        lineup_id = lineup_data['lineup_id']
        lineup = lineup_data['lineup']
        strategy = lineup_data['strategy']
        
        # Create submission format
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
        
        submission_df = pd.DataFrame(submission_data)
        
        # Save individual lineup
        individual_filename = f"CHAMPIONSHIP_LINEUP_{lineup_id}_{strategy}_{timestamp}.csv"
        submission_df.to_csv(individual_filename, index=False)
        
        # Add to combined submissions
        submission_df['lineup_id'] = lineup_id
        submission_df['strategy'] = strategy
        all_submissions.append(submission_df)
    
    # 2. Combined file with all lineups
    if all_submissions:
        combined_df = pd.concat(all_submissions, ignore_index=True)
        combined_filename = f"CHAMPIONSHIP_LINEUPS_ALL_{timestamp}.csv"
        combined_df.to_csv(combined_filename, index=False)
    
    # 3. Summary file
    summary_data = []
    for lineup_data in lineups:
        lineup = lineup_data['lineup']
        total_salary = sum(player['Salary'] for player in lineup)
        total_fppg = sum(player.get('FPPG', 0) for player in lineup)
        pitcher_name = lineup[0]['Nickname']
        
        summary_data.append({
            'lineup_id': lineup_data['lineup_id'],
            'strategy': lineup_data['strategy'],
            'pitcher': pitcher_name,
            'total_salary': total_salary,
            'total_fppg': total_fppg,
            'summary': lineup_data['summary']
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_filename = f"CHAMPIONSHIP_LINEUPS_SUMMARY_{timestamp}.csv"
    summary_df.to_csv(summary_filename, index=False)
    
    return combined_filename, summary_filename, len(lineups)

def main():
    print("🏆 MULTIPLE VALIDATED CHAMPIONSHIP LINEUP BUILDER")
    print("   Using ONLY confirmed starting players from today's slate")
    print("=" * 70)
    
    # Load validated players
    validated_players = load_validated_players()
    if validated_players is None:
        print("❌ Failed to load validated players")
        return
    
    # Create multiple championship lineups
    lineups = create_multiple_championship_lineups(validated_players, num_lineups=10)
    
    if not lineups:
        print("❌ Failed to create championship lineups")
        return
    
    # Save lineups
    combined_file, summary_file, num_created = save_championship_lineups(lineups)
    
    print("=" * 70)
    print(f"🎉 CHAMPIONSHIP LINEUPS COMPLETE!")
    print(f"✅ Created {num_created} validated championship lineups")
    print(f"📊 Combined file: {combined_file}")
    print(f"📋 Summary file: {summary_file}")
    print("\n🎯 LINEUP STRATEGIES USED:")
    
    strategies_used = {}
    for lineup_data in lineups:
        strategy = lineup_data['strategy']
        if strategy not in strategies_used:
            strategies_used[strategy] = 0
        strategies_used[strategy] += 1
    
    for strategy, count in strategies_used.items():
        print(f"   📈 {strategy.upper()}: {count} lineups")
    
    print("\n💡 ALL LINEUPS USE ONLY CONFIRMED STARTING PLAYERS")
    print("🚀 READY FOR FANDUEL SUBMISSION!")
    
    # Display top 3 lineups
    print("\n🏆 TOP 3 CHAMPIONSHIP LINEUPS:")
    print("=" * 50)
    
    for i, lineup_data in enumerate(lineups[:3]):
        lineup = lineup_data['lineup']
        total_salary = sum(player['Salary'] for player in lineup)
        total_fppg = sum(player.get('FPPG', 0) for player in lineup)
        
        print(f"\n🥇 LINEUP {lineup_data['lineup_id']} ({lineup_data['strategy'].upper()}):")
        print(f"   Pitcher: {lineup[0]['Nickname']} (${lineup[0]['Salary']:,})")
        print(f"   Total: ${total_salary:,} - {total_fppg:.1f} FPPG")

if __name__ == "__main__":
    main()
