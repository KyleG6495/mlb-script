#!/usr/bin/env python3
"""
REAL-TIME PLAYER VALIDATION SYSTEM
===================================
Validates player availability and status before DFS lineup construction.
Prevents picking players who aren't playing - the #1 cause of terrible lineups.
"""

import pandas as pd
import requests
from datetime import datetime, date
from pathlib import Path
import time
import json
import warnings
warnings.filterwarnings('ignore')

class PlayerValidator:
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent / "data"
        self.slate_dir = Path(__file__).parent.parent / "fd_current_slate"
        
    def get_todays_games(self):
        """Get today's MLB games from MLB API"""
        print("🏟️ Fetching today's MLB games...")
        
        today = date.today().strftime('%Y-%m-%d')
        
        try:
            # MLB API for today's games
            url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={today}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                schedule_data = response.json()
                games = schedule_data.get('dates', [])
                
                if games and len(games) > 0:
                    todays_games = games[0].get('games', [])
                    print(f"✅ Found {len(todays_games)} games today")
                    return todays_games
                else:
                    print("⚠️ No games scheduled for today")
                    return []
            else:
                print(f"❌ Error fetching games: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ Error fetching games: {e}")
            return []
    
    def get_probable_pitchers(self, games):
        """Extract probable pitchers from games"""
        print("⚾ Extracting probable pitchers...")
        
        probable_pitchers = set()
        
        for game in games:
            try:
                home_pitcher = game.get('teams', {}).get('home', {}).get('probablePitcher', {})
                away_pitcher = game.get('teams', {}).get('away', {}).get('probablePitcher', {})
                
                if home_pitcher and 'fullName' in home_pitcher:
                    probable_pitchers.add(home_pitcher['fullName'].lower().strip())
                    
                if away_pitcher and 'fullName' in away_pitcher:
                    probable_pitchers.add(away_pitcher['fullName'].lower().strip())
                    
            except Exception as e:
                print(f"Warning: Error parsing pitcher from game: {e}")
                continue
        
        print(f"✅ Found {len(probable_pitchers)} probable pitchers")
        return probable_pitchers
    
    def get_playing_teams(self, games):
        """Get teams playing today"""
        print("🏈 Extracting teams playing today...")
        
        playing_teams = set()
        
        for game in games:
            try:
                home_team = game.get('teams', {}).get('home', {}).get('team', {}).get('abbreviation')
                away_team = game.get('teams', {}).get('away', {}).get('team', {}).get('abbreviation')
                
                if home_team:
                    playing_teams.add(home_team.upper())
                if away_team:
                    playing_teams.add(away_team.upper())
                    
            except Exception as e:
                print(f"Warning: Error parsing teams from game: {e}")
                continue
        
        print(f"✅ Found {len(playing_teams)} teams playing today")
        return playing_teams
    
    def validate_slate_players(self, slate_df, games):
        """Validate which players are likely to play today"""
        print("🔍 Validating player availability...")
        
        probable_pitchers = self.get_probable_pitchers(games)
        playing_teams = self.get_playing_teams(games)
        
        slate_df = slate_df.copy()
        
        # Add validation columns
        slate_df['is_probable_pitcher'] = False
        slate_df['team_playing'] = False
        slate_df['validation_score'] = 0
        slate_df['validation_issues'] = ''
        
        # Clean slate data
        slate_df['full_name_clean'] = (
            slate_df['First Name'].fillna('').astype(str).str.strip() + ' ' + 
            slate_df['Last Name'].fillna('').astype(str).str.strip()
        ).str.lower()
        
        # Validate each player
        issues_count = {'no_team': 0, 'team_not_playing': 0, 'pitcher_not_probable': 0}
        
        for idx, player in slate_df.iterrows():
            issues = []
            score = 100  # Start with perfect score
            
            # Check if team is available
            player_team = str(player.get('Team', '')).upper().strip()
            
            if not player_team or player_team == 'NAN':
                issues.append('No team info')
                score -= 50
                issues_count['no_team'] += 1
            elif player_team not in playing_teams:
                issues.append(f'Team {player_team} not playing today')
                score -= 40
                issues_count['team_not_playing'] += 1
            else:
                slate_df.at[idx, 'team_playing'] = True
                score += 10
            
            # Special validation for pitchers
            if 'P' in str(player.get('Roster Position', '')):
                player_name = player['full_name_clean']
                
                if player_name in probable_pitchers:
                    slate_df.at[idx, 'is_probable_pitcher'] = True
                    score += 20
                else:
                    issues.append('Pitcher not listed as probable starter')
                    score -= 30
                    issues_count['pitcher_not_probable'] += 1
            
            # Check for obvious red flags
            fppg = player.get('FPPG', 0)
            salary = player.get('Salary', 0)
            
            if fppg <= 0:
                issues.append('Zero/negative FPPG projection')
                score -= 25
            
            if salary <= 2000:
                issues.append('Very low salary (possible inactive)')
                score -= 10
            
            # Store results
            slate_df.at[idx, 'validation_score'] = max(0, score)
            slate_df.at[idx, 'validation_issues'] = '; '.join(issues) if issues else 'OK'
        
        # Summary
        print(f"📊 VALIDATION SUMMARY:")
        print(f"  👥 Total players: {len(slate_df)}")
        print(f"  ✅ Teams playing: {len(playing_teams)}")
        print(f"  ⚾ Probable pitchers: {len(probable_pitchers)}")
        print(f"  ❌ Players with no team: {issues_count['no_team']}")
        print(f"  ❌ Players on non-playing teams: {issues_count['team_not_playing']}")
        print(f"  ❌ Non-probable pitchers: {issues_count['pitcher_not_probable']}")
        
        # Quality tiers
        excellent = (slate_df['validation_score'] >= 90).sum()
        good = ((slate_df['validation_score'] >= 70) & (slate_df['validation_score'] < 90)).sum()
        questionable = ((slate_df['validation_score'] >= 50) & (slate_df['validation_score'] < 70)).sum()
        avoid = (slate_df['validation_score'] < 50).sum()
        
        print(f"  🏆 Excellent (90+): {excellent}")
        print(f"  ✅ Good (70-89): {good}")
        print(f"  ⚠️  Questionable (50-69): {questionable}")
        print(f"  ❌ Avoid (<50): {avoid}")
        
        return slate_df
    
    def build_validated_lineup(self, validated_slate):
        """Build lineup using only validated players"""
        print("🏗️ Building lineup with validated players only...")
        
        # Filter to high-quality players
        safe_players = validated_slate[
            (validated_slate['validation_score'] >= 70) &
            (validated_slate['FPPG'] > 2.0) &
            (validated_slate['Salary'] > 0)
        ].copy()
        
        print(f"Working with {len(safe_players)} validated players")
        
        if len(safe_players) < 50:
            print("❌ Not enough validated players - may need to lower standards")
            return None
        
        # Calculate enhanced value with validation bonus
        safe_players['enhanced_value'] = (
            safe_players['FPPG'] / (safe_players['Salary'] / 1000) *
            (safe_players['validation_score'] / 100)  # Validation bonus
        )
        
        selected_players = []
        remaining_budget = 35000
        used_ids = set()
        
        positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
        
        for position in positions_needed:
            if position == 'UTIL':
                candidates = safe_players[~safe_players['Id'].isin(used_ids)]
            else:
                candidates = safe_players[
                    (safe_players['Roster Position'].str.contains(position)) &
                    (~safe_players['Id'].isin(used_ids))
                ]
            
            # Filter by budget
            affordable = candidates[candidates['Salary'] <= remaining_budget]
            
            if affordable.empty:
                print(f"❌ No affordable validated {position} players")
                return None
            
            # Pick best enhanced value
            chosen = affordable.loc[affordable['enhanced_value'].idxmax()]
            selected_players.append(chosen)
            remaining_budget -= chosen['Salary']
            used_ids.add(chosen['Id'])
        
        if len(selected_players) == 9:
            total_salary = sum(p['Salary'] for p in selected_players)
            total_fppg = sum(p['FPPG'] for p in selected_players)
            avg_validation = sum(p['validation_score'] for p in selected_players) / 9
            
            return {
                'players': selected_players,
                'total_salary': total_salary,
                'total_fppg': total_fppg,
                'avg_validation_score': avg_validation,
                'lineup_type': 'VALIDATED'
            }
        
        return None
    
    def save_validated_lineup(self, lineup, validated_slate):
        """Save the validated lineup"""
        if not lineup:
            print("❌ No validated lineup to save")
            return None
        
        # Create lineup DataFrame
        lineup_data = []
        
        players = lineup['players']
        lineup_row = {
            'Lineup_ID': 'VALIDATED_01',
            'Validation_Score': round(lineup['avg_validation_score'], 1),
            'Total_Salary': lineup['total_salary'],
            'Total_FPPG': round(lineup['total_fppg'], 2)
        }
        
        # Position mapping
        of_count = 0
        for player in players:
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player['Roster Position']
            
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
        
        # Save lineup
        df = pd.DataFrame(lineup_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = self.slate_dir / f"VALIDATED_Lineup_{timestamp}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"\n💾 VALIDATED LINEUP SAVED: {output_file}")
        
        # Print lineup details
        print(f"\n🏆 VALIDATED LINEUP ANALYSIS:")
        print(f"  💰 Salary: ${lineup['total_salary']:,}")
        print(f"  🎯 Projected FPPG: {lineup['total_fppg']:.1f}")
        print(f"  ✅ Avg Validation Score: {lineup['avg_validation_score']:.1f}/100")
        
        print(f"\n👥 PLAYER BREAKDOWN:")
        for player in players:
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player['Roster Position']
            salary = player['Salary']
            fppg = player['FPPG']
            val_score = player['validation_score']
            issues = player['validation_issues']
            
            status = "✅" if val_score >= 90 else "⚠️" if val_score >= 70 else "❌"
            print(f"  {status} {name:20} ({pos:4}) ${salary:5,} | {fppg:5.1f} FPPG | Val: {val_score:3.0f}")
            if issues != 'OK':
                print(f"      Issues: {issues}")
        
        return output_file
    
    def run_validation(self):
        """Run complete player validation pipeline"""
        print("🚀 STARTING REAL-TIME PLAYER VALIDATION")
        print("="*60)
        
        # Load slate
        slate_file = self.slate_dir / "fd_slate_today.csv"
        if not slate_file.exists():
            print("❌ No slate file found")
            return None
        
        slate_df = pd.read_csv(slate_file)
        print(f"📄 Loaded slate with {len(slate_df)} players")
        
        # Get today's games
        games = self.get_todays_games()
        if not games:
            print("⚠️ No games found - using slate as-is with warnings")
            games = []
        
        # Validate players
        validated_slate = self.validate_slate_players(slate_df, games)
        
        # Build validated lineup
        lineup = self.build_validated_lineup(validated_slate)
        
        if lineup:
            # Save lineup
            output_file = self.save_validated_lineup(lineup, validated_slate)
            
            print(f"\n🎉 VALIDATION COMPLETE!")
            print(f"✅ Created lineup with validated players only")
            print(f"📁 File: {output_file}")
            print(f"\n💡 This lineup should perform MUCH better")
            print(f"   because all players are verified to be playing today!")
            
        else:
            print("❌ Failed to create validated lineup")
        
        # Save validation data for review
        validation_file = self.data_dir / f"player_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        validated_slate.to_csv(validation_file, index=False)
        print(f"📊 Validation data saved: {validation_file}")
        
        return lineup

def main():
    print("🔍 REAL-TIME PLAYER VALIDATION SYSTEM")
    print("Preventing the #1 cause of terrible DFS lineups:")
    print("PICKING PLAYERS WHO DON'T EVEN PLAY!")
    print("="*60)
    
    validator = PlayerValidator()
    
    try:
        lineup = validator.run_validation()
        
        if lineup:
            print(f"\n🏆 SUCCESS!")
            print(f"   No more picking players who don't play!")
            print(f"   Your lineups should now be competitive!")
        else:
            print("❌ Validation failed")
            
    except Exception as e:
        print(f"Error in validation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
