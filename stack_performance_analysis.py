import pandas as pd
import os

def analyze_our_projections_vs_actual():
    """Compare our August 15th projections to actual August 15th results"""
    
    # Load our projections for Aug 15 (latest available with actual results)
    proj_file = r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data\advanced_ownership_projections_20250815_175656.csv'
    proj_df = pd.read_csv(proj_file)
    
    # Load actual results from Aug 15 
    actual_file = r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv'
    
    if not os.path.exists(actual_file):
        print(f"⚠️  Actual results file not found: {actual_file}")
        print("Available actual results files:")
        data_dir = r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data'
        actual_files = [f for f in os.listdir(data_dir) if f.startswith('actual_results_')]
        for f in sorted(actual_files)[-10:]:  # Show last 10
            print(f"   {f}")
        return
    
    actual_df = pd.read_csv(actual_file)
    
    print("=== OUR PROJECTIONS vs ACTUAL RESULTS ===")
    print(f"Date: August 15, 2025")
    print(f"Projected players: {len(proj_df)}")
    print(f"Actual results: {len(actual_df)}")
    
    # Get our projected team stacks
    print("\n=== OUR TOP PROJECTED STACKS (Aug 15) ===")
    if 'team' in proj_df.columns and 'projection' in proj_df.columns:
        # Filter hitters only
        hitters = proj_df[~proj_df['position'].str.contains('P', na=False)] if 'position' in proj_df.columns else proj_df
        
        # Group by team and get top 4 players per team
        our_stacks = {}
        for team in hitters['team'].unique():
            team_players = hitters[hitters['team'] == team].nlargest(4, 'projection')
            if len(team_players) >= 4:
                our_stacks[team] = {
                    'players': team_players['player_name'].tolist(),
                    'total_projection': team_players['projection'].sum(),
                    'avg_projection': team_players['projection'].mean()
                }
        
        # Sort by total projection
        sorted_our_stacks = sorted(our_stacks.items(), key=lambda x: x[1]['total_projection'], reverse=True)
        
        for i, (team, data) in enumerate(sorted_our_stacks[:10]):
            print(f"{i+1}. {team} - {data['total_projection']:.1f} total ({data['avg_projection']:.1f} avg)")
            print(f"   Players: {', '.join(data['players'])}")
    
    # Get actual best performing stacks
    print("\n=== ACTUAL BEST PERFORMING STACKS (Aug 20) ===")
    if 'team' in actual_df.columns and 'fanduel_points' in actual_df.columns:
        # Group by team and get top 4 scoring players per team
        actual_stacks = {}
        for team in actual_df['team'].unique():
            team_players = actual_df[actual_df['team'] == team].nlargest(4, 'fanduel_points')
            if len(team_players) >= 4:
                actual_stacks[team] = {
                    'players': team_players['player_name'].tolist(),
                    'total_actual': team_players['fanduel_points'].sum(),
                    'avg_actual': team_players['fanduel_points'].mean()
                }
        
        # Sort by actual performance
        sorted_actual_stacks = sorted(actual_stacks.items(), key=lambda x: x[1]['total_actual'], reverse=True)
        
        for i, (team, data) in enumerate(sorted_actual_stacks[:10]):
            print(f"{i+1}. {team} - {data['total_actual']:.1f} total ({data['avg_actual']:.1f} avg)")
            print(f"   Players: {', '.join(data['players'])}")
    
    # Compare our projections to actual results
    print("\n=== PROJECTION ACCURACY ANALYSIS ===")
    
    # Check how our top projected stacks actually performed
    print("\nHow our TOP 5 projected stacks actually performed:")
    for i, (team, proj_data) in enumerate(sorted_our_stacks[:5]):
        if team in actual_stacks:
            actual_data = actual_stacks[team]
            accuracy = (actual_data['total_actual'] / proj_data['total_projection']) * 100
            print(f"{i+1}. {team}")
            print(f"   Projected: {proj_data['total_projection']:.1f} | Actual: {actual_data['total_actual']:.1f} | Accuracy: {accuracy:.1f}%")
        else:
            print(f"{i+1}. {team} - No actual data found")
    
    # Check if we identified any of the actual top performers
    print(f"\nDid we identify the actual top performers?")
    our_top_5_teams = [team for team, _ in sorted_our_stacks[:5]]
    actual_top_5_teams = [team for team, _ in sorted_actual_stacks[:5]]
    
    overlap = set(our_top_5_teams) & set(actual_top_5_teams)
    print(f"Our top 5: {our_top_5_teams}")
    print(f"Actual top 5: {actual_top_5_teams}")
    print(f"Overlap: {list(overlap)} ({len(overlap)}/5 matches)")

if __name__ == "__main__":
    analyze_our_projections_vs_actual()
