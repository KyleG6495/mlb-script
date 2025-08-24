import pandas as pd
import numpy as np
from itertools import combinations
import pulp

def tournament_crusher_optimizer():
    """
    New optimizer built fro            print(f"Total: ${salary:,} ({salary/35000:.1%} usage) | Projection: {projection:.1f}") lessons learned from yesterday's perfect hindsight analysis:
    1. SPEND FULL SALARY - No more leaving $17K on table
    2. VALUE + STUDS strategy - Cheap gems + expensive ceiling plays  
    3. AVOID PITCHER TRAPS - Don't overpay for "safe" pitchers
    4. TARGET CEILING - Focus on tournament upside over cash game safety
    """
    
    print("=== TOURNAMENT CRUSHER OPTIMIZER ===")
    print("Built from yesterday's perfect hindsight analysis")
    print("Targeting 280+ point ceiling lineups for tournament play")
    print()
    
    # Load today's slate
    slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\fd_slate_today.csv"
    try:
        slate_df = pd.read_csv(slate_file)
        
        # Clean data - handle NaN values
        slate_df['FPPG'] = slate_df['FPPG'].fillna(0)
        slate_df['Salary'] = slate_df['Salary'].fillna(3000)
        
        # Remove players with 0 or negative salary/projection
        slate_df = slate_df[(slate_df['FPPG'] > 0) & (slate_df['Salary'] > 0)]
        
        print(f"Loaded {len(slate_df)} players from today's slate")
    except:
        print("ERROR: Could not load today's slate data")
        return
    
    # LESSON 1: TOURNAMENT CEILING ADJUSTMENTS
    # Boost projections for high-upside players based on yesterday's lessons
    slate_df['tournament_projection'] = slate_df['FPPG'].copy()
    
    # Boost cheap players with high upside (like Max Muncy $2500 → 29.7 pts)
    cheap_high_upside = (slate_df['Salary'] <= 3000) & (slate_df['FPPG'] >= 8)
    slate_df.loc[cheap_high_upside, 'tournament_projection'] *= 1.3
    
    # Boost middle-tier players with ceiling potential
    mid_tier_upside = (slate_df['Salary'] >= 3000) & (slate_df['Salary'] <= 4000) & (slate_df['FPPG'] >= 10)
    slate_df.loc[mid_tier_upside, 'tournament_projection'] *= 1.2
    
    # LESSON 2: PITCHER STRATEGY - Avoid expensive "safe" pitchers
    # Boost mid-tier pitchers (like Will Warren $8700 → 33.2 pts)
    expensive_pitchers = (slate_df['Position'] == 'P') & (slate_df['Salary'] >= 10000)
    slate_df.loc[expensive_pitchers, 'tournament_projection'] *= 0.8  # Penalize expensive pitchers
    
    mid_tier_pitchers = (slate_df['Position'] == 'P') & (slate_df['Salary'] >= 7000) & (slate_df['Salary'] < 10000)
    slate_df.loc[mid_tier_pitchers, 'tournament_projection'] *= 1.15  # Boost mid-tier pitchers
    
    print("Applied tournament ceiling adjustments:")
    print(f"- Boosted {cheap_high_upside.sum()} cheap high-upside players")
    print(f"- Boosted {mid_tier_upside.sum()} mid-tier ceiling players")
    print(f"- Penalized {expensive_pitchers.sum()} expensive pitchers")
    print(f"- Boosted {mid_tier_pitchers.sum()} mid-tier pitchers")
    print()
    
    # LESSON 3: VALUE-POINTS-PER-DOLLAR metric for tournament play
    slate_df['value_score'] = slate_df['tournament_projection'] / (slate_df['Salary'] / 1000)
    
    # Handle any remaining NaN or inf values
    slate_df['value_score'] = slate_df['value_score'].replace([np.inf, -np.inf], 0).fillna(0)
    slate_df['tournament_projection'] = slate_df['tournament_projection'].fillna(0)
    
    print("Top 10 VALUE plays (points per $1K):")
    top_value = slate_df.nlargest(10, 'value_score')
    print(top_value[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'tournament_projection', 'value_score']].to_string(index=False))
    print()
    
    print("Top 10 CEILING plays (raw projection):")
    top_ceiling = slate_df.nlargest(10, 'tournament_projection')
    print(top_ceiling[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'tournament_projection', 'value_score']].to_string(index=False))
    print()
    
    # OPTIMIZATION FUNCTION
    def optimize_tournament_lineup(players_df, salary_cap=35000, target_salary_usage=0.98):
        """
        Build optimal tournament lineup using lessons from yesterday
        """
        # Create decision variables
        player_vars = {}
        for idx, player in players_df.iterrows():
            player_vars[idx] = pulp.LpVariable(f"player_{idx}", cat='Binary')
        
        # Create the problem
        prob = pulp.LpProblem("Tournament_Crusher", pulp.LpMaximize)
        
        # Objective: Maximize tournament projections
        prob += pulp.lpSum([player_vars[idx] * row['tournament_projection'] for idx, row in players_df.iterrows()])
        
        # Salary constraint - MUST use at least 98% of salary cap (LESSON FROM YESTERDAY)
        prob += pulp.lpSum([player_vars[idx] * row['Salary'] for idx, row in players_df.iterrows()]) <= salary_cap
        prob += pulp.lpSum([player_vars[idx] * row['Salary'] for idx, row in players_df.iterrows()]) >= salary_cap * target_salary_usage
        
        # Position constraints
        prob += pulp.lpSum([player_vars[idx] for idx, row in players_df.iterrows() if 'P' in row['Position']]) == 1
        prob += pulp.lpSum([player_vars[idx] for idx, row in players_df.iterrows() if any(pos in row['Position'] for pos in ['C', '1B'])]) >= 1
        prob += pulp.lpSum([player_vars[idx] for idx, row in players_df.iterrows() if '2B' in row['Position']]) >= 1
        prob += pulp.lpSum([player_vars[idx] for idx, row in players_df.iterrows() if '3B' in row['Position']]) >= 1
        prob += pulp.lpSum([player_vars[idx] for idx, row in players_df.iterrows() if 'SS' in row['Position']]) >= 1
        prob += pulp.lpSum([player_vars[idx] for idx, row in players_df.iterrows() if 'OF' in row['Position']]) >= 3
        
        # Total 9 players
        prob += pulp.lpSum([player_vars[idx] for idx in player_vars]) == 9
        
        # Solve
        prob.solve(pulp.PULP_CBC_CMD(msg=0))
        
        # Extract solution
        selected_players = []
        total_salary = 0
        total_projection = 0
        
        for idx, player in players_df.iterrows():
            if player_vars[idx].value() == 1:
                selected_players.append({
                    'name': f"{player['First Name']} {player['Last Name']}",
                    'position': player['Position'],
                    'team': player.get('Team', 'N/A'),
                    'salary': player['Salary'],
                    'original_proj': player['FPPG'],
                    'tournament_proj': player['tournament_projection'],
                    'value_score': player['value_score']
                })
                total_salary += player['Salary']
                total_projection += player['tournament_projection']
        
        return selected_players, total_salary, total_projection
    
    # Generate multiple tournament lineups
    print("=== GENERATING TOURNAMENT LINEUPS ===")
    
    lineups = []
    for i in range(10):  # Generate 10 different lineups
        print(f"\nGenerating lineup {i+1}...")
        
        # Add some randomness for diversity
        slate_copy = slate_df.copy()
        if i > 0:
            # Add random variance to projections for diversity
            variance = np.random.normal(0, 0.1, len(slate_copy))
            slate_copy['tournament_projection'] *= (1 + variance)
        
        selected, salary, projection = optimize_tournament_lineup(slate_copy)
        
        if selected:
            lineups.append({
                'lineup_num': i+1,
                'players': selected,
                'total_salary': salary,
                'total_projection': projection,
                'salary_usage': salary / 35000
            })
            
            print(f"Lineup {i+1}:")
            print("Position | Player | Team | Salary | Orig | Tourney | Value")
            print("-" * 70)
            for player in selected:
                print(f"{player['position']:8} | {player['name']:20} | {player['team']:4} | ${player['salary']:5} | {player['original_proj']:5.1f} | {player['tournament_proj']:7.1f} | {player['value_score']:5.1f}")
            print(f"Total: ${salary:,} ({salary/50000:.1%} usage) | Projection: {projection:.1f}")
        else:
            print(f"Failed to generate lineup {i+1}")
    
    # Save best lineups to CSV
    if lineups:
        print(f"\n=== BEST TOURNAMENT LINEUPS ===")
        lineups.sort(key=lambda x: x['total_projection'], reverse=True)
        
        # Create FanDuel format CSV
        fd_lineups = []
        for lineup in lineups[:10]:
            fd_lineup = {'Lineup': lineup['lineup_num']}
            
            # Map positions for FanDuel format
            position_map = {'P': 'P', 'C': 'C/1B', '1B': 'C/1B', '2B': '2B', '3B': '3B', 'SS': 'SS'}
            of_count = 0
            util_filled = False
            
            for player in lineup['players']:
                pos = player['position']
                name = player['name']
                
                if 'P' in pos:
                    fd_lineup['P'] = name
                elif any(p in pos for p in ['C', '1B']) and 'C/1B' not in fd_lineup:
                    fd_lineup['C/1B'] = name
                elif '2B' in pos and '2B' not in fd_lineup:
                    fd_lineup['2B'] = name
                elif '3B' in pos and '3B' not in fd_lineup:
                    fd_lineup['3B'] = name
                elif 'SS' in pos and 'SS' not in fd_lineup:
                    fd_lineup['SS'] = name
                elif 'OF' in pos and of_count < 3:
                    fd_lineup[f'OF{of_count+1}' if of_count > 0 else 'OF'] = name
                    of_count += 1
                elif not util_filled:
                    fd_lineup['UTIL'] = name
                    util_filled = True
            
            fd_lineup['Salary'] = lineup['total_salary']
            fd_lineup['Projection'] = lineup['total_projection']
            fd_lineups.append(fd_lineup)
        
        # Save to CSV
        output_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\tournament_crusher_lineups.csv"
        pd.DataFrame(fd_lineups).to_csv(output_file, index=False)
        print(f"Saved {len(fd_lineups)} tournament lineups to: {output_file}")
        
        # Show top 3 lineups
        for i, lineup in enumerate(lineups[:3]):
            print(f"\nTOP LINEUP #{i+1}:")
            print(f"Projection: {lineup['total_projection']:.1f} points")
            print(f"Salary: ${lineup['total_salary']:,} ({lineup['salary_usage']:.1%} usage)")
            print("Key Players:")
            sorted_players = sorted(lineup['players'], key=lambda x: x['tournament_proj'], reverse=True)
            for player in sorted_players[:5]:
                print(f"  {player['name']} ({player['position']}) - ${player['salary']} → {player['tournament_proj']:.1f} pts")
    
    return lineups

if __name__ == "__main__":
    tournament_lineups = tournament_crusher_optimizer()
