#!/usr/bin/env python3
"""
FanDuel Submission File Generator
Creates properly formatted FanDuel submission files from enhanced lineups
"""

import pandas as pd
import os
from datetime import datetime
import glob

def load_player_mapping():
    """Load player ID to name mapping from current slate"""
    try:
        # Load the current FanDuel slate
        slate_file = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
        if not os.path.exists(slate_file):
            print(f"❌ Slate file not found: {slate_file}")
            return {}
        
        df = pd.read_csv(slate_file)
        
        # Create mapping of player names to FanDuel ID + Name format
        player_mapping = {}
        for _, row in df.iterrows():
            player_id = str(row['Id'])
            first_name = str(row['First Name']).strip()
            last_name = str(row['Last Name']).strip()
            
            # Handle different name formats
            if 'Nickname' in df.columns and pd.notna(row['Nickname']) and str(row['Nickname']).strip():
                display_name = str(row['Nickname']).strip()
            else:
                display_name = f"{first_name} {last_name}".strip()
            
            # Create FanDuel format: ID:Name
            fd_format = f"{player_id}:{display_name}"
            
            # Map various name formats to FanDuel format
            player_mapping[display_name] = fd_format
            player_mapping[f"{first_name} {last_name}"] = fd_format
            player_mapping[last_name] = fd_format
            
        print(f"✅ Loaded {len(player_mapping)} player mappings")
        return player_mapping
        
    except Exception as e:
        print(f"❌ Error loading player mapping: {e}")
        return {}

def get_player_fd_name(player_id, name, player_mapping):
    """Convert player info to FanDuel format"""
    player_id = str(player_id).strip()
    name = str(name).strip()
    
    # Try direct lookup in mapping
    if name in player_mapping:
        return player_mapping[name]
    
    # Fallback to partial name matching
    for mapped_name, fd_name in player_mapping.items():
        if name.lower() in mapped_name.lower() or mapped_name.lower() in name.lower():
            return fd_name
    
    return ''

def convert_lineup_to_fanduel_format(lineup_df, player_mapping):
    """Convert lineup dataframe to FanDuel submission format"""
    try:
        fd_lineups = []
        
        for _, row in lineup_df.iterrows():
            fd_row = {
                'Lineup_ID': row.get('Lineup_ID', ''),
                'Contest_Type': row.get('Contest_Type', 'tournament'),
                'P': row.get('P', ''),
                'C/1B': row.get('C/1B', ''),
                '2B': row.get('2B', ''),
                '3B': row.get('3B', ''),
                'SS': row.get('SS', ''),
                'OF': row.get('OF', ''),
                'OF2': row.get('OF2', ''),
                'OF3': row.get('OF3', ''),
                'UTIL': row.get('UTIL', ''),
                'Total_Salary': row.get('Total_Salary', ''),
                'Total_Projection': row.get('Total_Projection', '')
            }
            fd_lineups.append(fd_row)
        
        return pd.DataFrame(fd_lineups)
        
    except Exception as e:
        print(f"❌ Error converting lineups: {e}")
        return None

def convert_player_name(player_name, player_mapping):
    """Convert player name to FanDuel ID:Name format"""
    if not player_name or pd.isna(player_name):
        return ''
    
    player_name = str(player_name).strip()
    
    # Check if already in FanDuel format (contains ID:)
    if ':' in player_name and player_name.startswith('118876-'):
        return player_name
    
    # Try to find in mapping
    if player_name in player_mapping:
        return player_mapping[player_name]
    
    # Try partial matches
    for mapped_name, fd_format in player_mapping.items():
        if player_name.lower() in mapped_name.lower() or mapped_name.lower() in player_name.lower():
            return fd_format
    
    print(f"⚠️ Player not found in mapping: {player_name}")
    return player_name

def main():
    print("🚀 Creating FanDuel Submission File...")
    
    # Load player mapping
    player_mapping = load_player_mapping()
    if not player_mapping:
        print("❌ Could not load player mapping - using existing files")
        return
    
    data_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\data"
    fd_dir = r"C:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate"
    
    # Look for enhanced lineup files
    enhanced_files = []
    
    # Check for enhanced ML lineups
    ml_files = glob.glob(os.path.join(data_dir, "enhanced_ml_dfs_lineups_*.csv"))
    if ml_files:
        enhanced_files.extend(sorted(ml_files, key=os.path.getmtime, reverse=True)[:1])
    
    # Check for enhanced ceiling lineups
    ceiling_files = glob.glob(os.path.join(data_dir, "enhanced_ceiling_lineups_*.csv"))
    if ceiling_files:
        enhanced_files.extend(sorted(ceiling_files, key=os.path.getmtime, reverse=True)[:1])
    
    if not enhanced_files:
        print("❌ No enhanced lineup files found")
        return
    
    all_lineups = []
    
    # Process each enhanced file
    for file_path in enhanced_files:
        try:
            print(f"📊 Processing: {os.path.basename(file_path)}")
            df = pd.read_csv(file_path)
            
            if 'Lineup' in df.columns:
                # Ceiling format - group by lineup
                for lineup_name in df['Lineup'].unique():
                    lineup_players = df[df['Lineup'] == lineup_name]
                    
                    if len(lineup_players) >= 9:  # Full lineup
                        lineup_dict = {
                            'Lineup_ID': lineup_name,
                            'Contest_Type': 'tournament' if 'ceiling' in file_path.lower() else 'cash',
                            'P': '',
                            'C/1B': '',
                            '2B': '',
                            '3B': '',
                            'SS': '',
                            'OF': '',
                            'OF2': '',
                            'OF3': '',
                            'UTIL': '',
                            'Total_Salary': '',
                            'Total_Projection': ''
                        }
                        
                        for _, player in lineup_players.iterrows():
                            pos = str(player['Position']).upper()
                            name = str(player['Name'])
                            player_id = str(player.get('Player_ID', ''))
                            
                            # Get FanDuel formatted name
                            fd_name = get_player_fd_name(player_id, name, player_mapping)
                            if not fd_name:
                                continue  # Skip if no mapping found
                            
                            if pos == 'P':
                                lineup_dict['P'] = fd_name
                            elif 'C' in pos:  # Handles C, C/1B
                                if lineup_dict['C/1B'] == '':
                                    lineup_dict['C/1B'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                            elif '1B' in pos and 'C' not in pos:  # Handles 1B, 1B/OF but not C/1B
                                if lineup_dict['C/1B'] == '':
                                    lineup_dict['C/1B'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                            elif '2B' in pos:  # Handles 2B, SS/2B
                                if lineup_dict['2B'] == '':
                                    lineup_dict['2B'] = fd_name
                                elif 'SS' in pos and lineup_dict['SS'] == '':
                                    lineup_dict['SS'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                            elif pos == '3B':
                                lineup_dict['3B'] = fd_name
                            elif 'SS' in pos:  # Handles SS, SS/2B
                                if lineup_dict['SS'] == '':
                                    lineup_dict['SS'] = fd_name
                                elif '2B' in pos and lineup_dict['2B'] == '':
                                    lineup_dict['2B'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                            elif pos == 'OF':
                                if lineup_dict['OF'] == '':
                                    lineup_dict['OF'] = fd_name
                                elif lineup_dict['OF2'] == '':
                                    lineup_dict['OF2'] = fd_name
                                elif lineup_dict['OF3'] == '':
                                    lineup_dict['OF3'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                            else:
                                # Fallback to UTIL for any unhandled positions
                                lineup_dict['UTIL'] = fd_name
                        
                        # Add salary and projection totals for ceiling lineups
                        lineup_dict['Total_Salary'] = lineup_players['Salary'].sum()
                        lineup_dict['Total_Projection'] = round(lineup_players['FPPG'].sum(), 2)
                        
                        all_lineups.append(lineup_dict)
            elif 'lineup_id' in df.columns:
                # ML format - long format with lineup_id
                for lineup_id in df['lineup_id'].unique():
                    lineup_players = df[df['lineup_id'] == lineup_id].sort_values('slot')
                    
                    if len(lineup_players) >= 9:  # Full lineup
                        lineup_dict = {
                            'Lineup_ID': f"ENHANCED_ML_{lineup_id}",
                            'Contest_Type': lineup_players.iloc[0]['contest_type'],
                            'P': '',
                            'C/1B': '',
                            '2B': '',
                            '3B': '',
                            'SS': '',
                            'OF': '',
                            'OF2': '',
                            'OF3': '',
                            'UTIL': '',
                            'Total_Salary': '',
                            'Total_Projection': ''
                        }
                        
                        for _, player in lineup_players.iterrows():
                            pos = str(player['primary_position']).upper()
                            name = str(player['name'])
                            slot = int(player['slot'])
                            player_id = str(player['player_id'])
                            
                            # Get FanDuel formatted name
                            fd_name = get_player_fd_name(player_id, name, player_mapping)
                            
                            if not fd_name:
                                continue  # Skip if no mapping found
                            
                            # Map positions based on slot and position
                            if pos == 'P':
                                lineup_dict['P'] = fd_name
                            elif pos in ['C', '1B']:
                                if lineup_dict['C/1B'] == '':
                                    lineup_dict['C/1B'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                            elif pos in ['2B']:
                                lineup_dict['2B'] = fd_name
                            elif pos == '3B':
                                lineup_dict['3B'] = fd_name
                            elif pos in ['SS']:
                                lineup_dict['SS'] = fd_name
                            elif pos == 'OF':
                                if lineup_dict['OF'] == '':
                                    lineup_dict['OF'] = fd_name
                                elif lineup_dict['OF2'] == '':
                                    lineup_dict['OF2'] = fd_name
                                elif lineup_dict['OF3'] == '':
                                    lineup_dict['OF3'] = fd_name
                                else:
                                    lineup_dict['UTIL'] = fd_name
                        
                        # Add salary and projection info
                        lineup_dict['Total_Salary'] = lineup_players.iloc[0]['lineup_total_salary']
                        lineup_dict['Total_Projection'] = lineup_players.iloc[0]['lineup_total_projection']
                        
                        all_lineups.append(lineup_dict)
            else:
                # Standard format
                all_lineups.extend(df.to_dict('records'))
                
        except Exception as e:
            print(f"⚠️ Error processing {file_path}: {e}")
            continue
    
    if not all_lineups:
        print("❌ No valid lineups found to convert")
        return
    
    # Convert to DataFrame and then to FanDuel format
    lineups_df = pd.DataFrame(all_lineups)
    fd_lineups = convert_lineup_to_fanduel_format(lineups_df, player_mapping)
    
    if fd_lineups is None or len(fd_lineups) == 0:
        print("❌ Failed to convert lineups to FanDuel format")
        return
    
    # Save FanDuel submission file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(fd_dir, f"Enhanced_Lineups_FD_Format_{timestamp}.csv")
    
    try:
        fd_lineups.to_csv(output_file, index=False)
        print(f"✅ FanDuel submission file created: {os.path.basename(output_file)}")
        print(f"📁 Location: {output_file}")
        print(f"📊 Lineups converted: {len(fd_lineups)}")
        
        # Also create a copy with a standard name for easy access
        standard_file = os.path.join(fd_dir, "Enhanced_Lineups_FD_Format.csv")
        fd_lineups.to_csv(standard_file, index=False)
        print(f"✅ Standard file created: Enhanced_Lineups_FD_Format.csv")
        
    except Exception as e:
        print(f"❌ Error saving file: {e}")

if __name__ == "__main__":
    main()
