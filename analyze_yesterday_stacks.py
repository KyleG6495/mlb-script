import pandas as pd
import glob
import os

def analyze_team_stacks():
    """Analyze yesterday's team stack performance"""
    
    # Find the most recent actual results file
    data_path = r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data'
    result_files = glob.glob(os.path.join(data_path, 'actual_results_*.csv'))
    
    if not result_files:
        print('No actual results files found')
        return
    
    # Sort by filename (date) to get most recent
    result_files.sort(reverse=True)
    print('Available results files:')
    for i, file in enumerate(result_files[:5]):
        print(f'{i+1}. {os.path.basename(file)}')
    
    latest_file = result_files[0]
    print(f'\nAnalyzing: {os.path.basename(latest_file)}')
    
    try:
        df = pd.read_csv(latest_file)
        print(f'Total players: {len(df)}')
        print(f'Available columns: {list(df.columns)}')
        
        # Find fantasy points column
        fp_col = None
        for col in ['fantasy_points', 'FP', 'points', 'fantasy_pts', 'fanduel_points']:
            if col in df.columns:
                fp_col = col
                break
        
        if not fp_col:
            print('No fantasy points column found')
            return
            
        if 'team' not in df.columns:
            print('No team column found')
            return
            
        print(f'\nUsing "{fp_col}" for fantasy points analysis')
        
        # Filter out pitchers for stack analysis
        pos_col = None
        for col in ['position', 'pos', 'Position']:
            if col in df.columns:
                pos_col = col
                break
        
        if pos_col:
            # Exclude pitchers
            hitters_df = df[~df[pos_col].isin(['P', 'SP', 'RP'])]
            print(f'Analyzing {len(hitters_df)} hitters (excluded pitchers)')
        else:
            hitters_df = df
            print('Position column not found, analyzing all players')
        
        # Team stack analysis - top 4 hitters per team
        print('\n=== TEAM STACK PERFORMANCE (Top 4 Hitters) ===')
        
        team_stacks = []
        for team in hitters_df['team'].unique():
            team_players = hitters_df[hitters_df['team'] == team].nlargest(4, fp_col)
            
            if len(team_players) >= 4:
                stack_total = team_players[fp_col].sum()
                stack_avg = team_players[fp_col].mean()
                
                # Get player names if available
                if 'player_name' in df.columns:
                    players_list = team_players['player_name'].head(4).tolist()
                else:
                    players_list = ['Names not available']
                
                points_list = [round(fp, 1) for fp in team_players[fp_col].head(4).tolist()]
                
                team_stacks.append({
                    'Team': team,
                    'Stack_Total_FP': round(stack_total, 2),
                    'Stack_Avg_FP': round(stack_avg, 2),
                    'Top_Players': players_list,
                    'Individual_FP': points_list
                })
        
        # Sort by stack total and display top performing stacks
        stack_df = pd.DataFrame(team_stacks).sort_values('Stack_Total_FP', ascending=False)
        
        print('\nTOP 10 PERFORMING TEAM STACKS:')
        print('=' * 80)
        
        for i, row in stack_df.head(10).iterrows():
            team = row['Team']
            total = row['Stack_Total_FP']
            avg = row['Stack_Avg_FP']
            players = row['Top_Players']
            points = row['Individual_FP']
            
            print(f'{team:4} | Total: {total:6.1f} | Avg: {avg:5.1f}')
            
            if isinstance(players, list) and 'Names not available' not in players:
                players_str = ', '.join(players)
                points_str = ', '.join([str(p) for p in points])
                print(f'     Players: {players_str}')
                print(f'     Points:  {points_str}')
            print()
        
        # Summary statistics
        best_team = stack_df.iloc[0]['Team']
        best_total = stack_df.iloc[0]['Stack_Total_FP']
        avg_stack_total = stack_df['Stack_Total_FP'].mean()
        min_total = stack_df['Stack_Total_FP'].min()
        max_total = stack_df['Stack_Total_FP'].max()
        
        print(f'\n=== SUMMARY ===')
        print(f'Best stack: {best_team} with {best_total} total points')
        print(f'Average stack total: {avg_stack_total:.1f} points')
        print(f'Stack total range: {min_total:.1f} - {max_total:.1f}')
        
        # Return data for comparison
        return stack_df
        
    except Exception as e:
        print(f'Error analyzing file: {e}')
        return None

if __name__ == '__main__':
    analyze_team_stacks()
