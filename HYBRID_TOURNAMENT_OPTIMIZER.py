import pandas as pd
import numpy as np
import pulp
from itertools import combinations

def build_hybrid_tournament_optimizer():
    """
    Build a HYBRID optimizer that learns from August 12th results
    Balances ceiling studs with proven value plays
    """
    
    print("=== HYBRID TOURNAMENT OPTIMIZER ===")
    print("Learning from August 12th failures to build the perfect strategy...")
    print()
    
    # Load August 12th slate and actual results for analysis
    slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\vegas_adjusted_slate_20250812_135729.csv"
    slate_df = pd.read_csv(slate_file)
    
    actual_results = pd.read_csv(r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\actual_results_latest.csv")
    
    # Merge for analysis
    actual_results['full_name'] = actual_results['name'].str.strip()
    slate_df['full_name'] = (slate_df['First Name'] + ' ' + slate_df['Last Name']).str.strip()
    
    merged_data = slate_df.merge(
        actual_results[['full_name', 'fanduel_points']], 
        on='full_name', 
        how='left'
    )
    merged_data['actual_fppg'] = merged_data['fanduel_points'].fillna(0)
    
    print("=== ANALYZING WINNING PATTERNS ===")
    
    # Analyze what made the top performers successful
    top_performers = merged_data[merged_data['actual_fppg'] >= 25].copy()
    
    print(f"Found {len(top_performers)} elite performers (25+ points):")
    print(top_performers[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'actual_fppg']].to_string(index=False))
    
    # Analyze salary vs performance patterns
    top_performers['value_delivered'] = top_performers['actual_fppg'] / (top_performers['Salary'] / 1000)
    top_performers['projection_accuracy'] = top_performers['actual_fppg'] / top_performers['FPPG']
    
    print("\n=== WINNING PLAYER PATTERNS ===")
    
    # Pattern 1: Salary ranges of top performers
    salary_analysis = top_performers.groupby(pd.cut(top_performers['Salary'], bins=[0, 3000, 4000, 6000, 12000]))['actual_fppg'].agg(['count', 'mean', 'max'])
    print("Performance by salary range:")
    print(salary_analysis)
    
    # Pattern 2: Position analysis
    position_analysis = top_performers.groupby('Position')['actual_fppg'].agg(['count', 'mean', 'max'])
    print("\nPerformance by position:")
    print(position_analysis)
    
    # Pattern 3: Projection accuracy
    print(f"\nProjection accuracy for top performers:")
    print(f"Average actual/projected ratio: {top_performers['projection_accuracy'].mean():.2f}")
    print(f"Players who exceeded projections: {len(top_performers[top_performers['projection_accuracy'] > 1.5])}")
    
    # Build the HYBRID strategy based on these patterns
    print("\n=== BUILDING HYBRID STRATEGY ===")
    
    def calculate_hybrid_score(row):
        """Calculate hybrid tournament score based on learned patterns"""
        base_score = row['FPPG']
        salary = row['Salary']
        position = row['Position']
        
        # Start with base projection
        hybrid_score = base_score
        
        # LESSON 1: Don't over-penalize expensive players if they have ceiling
        # Top performers included $3300+ players, not just cheap ones
        if salary >= 3000 and salary <= 4000 and base_score >= 11:
            hybrid_score *= 1.15  # Modest boost for mid-range ceiling
        
        # LESSON 2: Boost proven ceiling positions
        # SS and 3B had multiple top performers
        if position in ['SS', '3B'] and base_score >= 10:
            hybrid_score *= 1.1
        
        # LESSON 3: Be more selective with pitchers
        # Expensive pitcher busts killed us, but mid-range pitchers performed
        if position == 'P':
            if salary >= 10500:
                hybrid_score *= 0.85  # Penalize expensive pitchers more
            elif 7000 <= salary <= 9000 and base_score >= 20:
                hybrid_score *= 1.2   # Boost mid-range pitchers with upside
        
        # LESSON 4: Value plays need minimum projection threshold
        # Don't chase cheap players with low projections
        if salary <= 2500 and base_score < 8:
            hybrid_score *= 0.7  # Penalize low-projection value traps
        
        # LESSON 5: Boost players with proven upside (high projection relative to salary)
        value_ratio = base_score / (salary / 1000)
        if value_ratio >= 4.5 and base_score >= 10:
            hybrid_score *= 1.1
        
        return hybrid_score
    
    # Apply hybrid scoring to current slate
    current_slate_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\fd_current_slate\fd_slate_today.csv"
    try:
        current_slate = pd.read_csv(current_slate_file)
        print(f"Loaded {len(current_slate)} players from today's slate")
        
        # Apply hybrid scoring
        current_slate = current_slate.fillna(0)  # Handle any NaN values
        current_slate['hybrid_score'] = current_slate.apply(calculate_hybrid_score, axis=1)
        current_slate['value_score'] = current_slate['hybrid_score'] / (current_slate['Salary'] / 1000)
        
        # Ensure no inf or NaN values
        current_slate['hybrid_score'] = current_slate['hybrid_score'].replace([np.inf, -np.inf], 0)
        current_slate['value_score'] = current_slate['value_score'].replace([np.inf, -np.inf], 0)
        current_slate = current_slate.fillna(0)
        
        print("\nTop 10 HYBRID value plays for today:")
        top_hybrid = current_slate.nlargest(10, 'value_score')
        print(top_hybrid[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'hybrid_score', 'value_score']].to_string(index=False))
        
        print("\nTop 10 HYBRID ceiling plays for today:")
        top_ceiling = current_slate.nlargest(10, 'hybrid_score')
        print(top_ceiling[['First Name', 'Last Name', 'Position', 'Salary', 'FPPG', 'hybrid_score', 'value_score']].to_string(index=False))
        
        # Generate optimal lineup using hybrid approach
        print("\n=== GENERATING HYBRID LINEUP ===")
        
        # Multiple lineup generation with different strategies
        lineups = []
        
        # Strategy 1: Pure hybrid optimization
        lineup1 = optimize_hybrid_lineup(current_slate, strategy="balanced")
        if lineup1:
            lineups.append(("Balanced Hybrid", lineup1))
        
        # Strategy 2: Ceiling-focused
        lineup2 = optimize_hybrid_lineup(current_slate, strategy="ceiling")
        if lineup2:
            lineups.append(("Ceiling Focus", lineup2))
        
        # Strategy 3: Value-focused but with minimums
        lineup3 = optimize_hybrid_lineup(current_slate, strategy="value")
        if lineup3:
            lineups.append(("Smart Value", lineup3))
        
        # Display all lineups
        for strategy_name, lineup in lineups:
            print(f"\n=== {strategy_name.upper()} LINEUP ===")
            total_salary = sum(p['Salary'] for p in lineup)
            total_projection = sum(p['hybrid_score'] for p in lineup)
            
            print("Position | Player | Salary | Original | Hybrid | Value")
            print("-" * 65)
            
            for player in lineup:
                print(f"{player['Position']:8} | {player['First Name']} {player['Last Name']:15} | ${player['Salary']:5} | {player['FPPG']:8.1f} | {player['hybrid_score']:6.1f} | {player['value_score']:5.1f}")
            
            print(f"\nTotal: ${total_salary:,} ({total_salary/35000:.1%} usage) | Projection: {total_projection:.1f}")
        
        # Save best lineups
        save_hybrid_lineups(lineups)
        
        return lineups
        
    except Exception as e:
        print(f"Error loading current slate: {e}")
        return None

def optimize_hybrid_lineup(slate_df, strategy="balanced"):
    """Optimize lineup using hybrid approach with different strategies"""
    
    # Filter available players and clean data
    available_players = slate_df[slate_df['Salary'] > 0].copy().reset_index(drop=True)
    available_players = available_players.fillna(0)
    
    # Ensure all numeric columns are clean
    numeric_cols = ['Salary', 'FPPG', 'hybrid_score', 'value_score']
    for col in numeric_cols:
        if col in available_players.columns:
            available_players[col] = pd.to_numeric(available_players[col], errors='coerce').fillna(0)
            available_players[col] = available_players[col].replace([np.inf, -np.inf], 0)
    
    # Adjust hybrid scores based on strategy
    if strategy == "ceiling":
        # Boost high-projection players more
        available_players.loc[available_players['FPPG'] >= 15, 'hybrid_score'] *= 1.2
    elif strategy == "value":
        # Boost value plays but maintain minimums
        available_players.loc[available_players['value_score'] >= 4, 'hybrid_score'] *= 1.15
    
    # Set up optimization
    prob = pulp.LpProblem(f"Hybrid_{strategy}", pulp.LpMaximize)
    
    # Decision variables
    player_vars = [pulp.LpVariable(f"player_{i}", cat='Binary') for i in range(len(available_players))]
    
    # Objective: maximize hybrid score
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'hybrid_score'] for i in range(len(available_players))])
    
    # Salary constraints
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'Salary'] for i in range(len(available_players))]) <= 35000
    prob += pulp.lpSum([player_vars[i] * available_players.loc[i, 'Salary'] for i in range(len(available_players))]) >= 34000
    
    # Position constraints
    def can_play_position(player_pos, needed_pos):
        if needed_pos == 'UTIL':
            return any(pos in str(player_pos) for pos in ['C', '1B', '2B', '3B', 'SS', 'OF', 'DH'])
        elif needed_pos == 'C/1B':
            return any(pos in str(player_pos) for pos in ['C', '1B'])
        else:
            return needed_pos in str(player_pos)
    
    # Position requirements
    positions_needed = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'OF', 'OF', 'UTIL']
    
    for pos in positions_needed:
        eligible_indices = [i for i in range(len(available_players)) 
                          if can_play_position(available_players.loc[i, 'Position'], pos)]
        if eligible_indices:
            prob += pulp.lpSum([player_vars[i] for i in eligible_indices]) >= 1
    
    # Solve
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    
    if prob.status == 1:  # Optimal
        selected_players = []
        
        for i in range(len(available_players)):
            if player_vars[i].value() == 1:
                player = available_players.loc[i].to_dict()
                selected_players.append(player)
        
        return selected_players
    
    return None

def save_hybrid_lineups(lineups):
    """Save hybrid lineups to CSV for FanDuel submission"""
    
    if not lineups:
        return
    
    # Convert to FanDuel format
    lineup_data = []
    
    for i, (strategy_name, lineup) in enumerate(lineups):
        entry = {
            'Strategy': strategy_name,
            'P': '',
            'C/1B': '',
            '2B': '',
            '3B': '', 
            'SS': '',
            'OF1': '',
            'OF2': '',
            'OF3': '',
            'UTIL': ''
        }
        
        # Fill positions
        of_count = 0
        for player in lineup:
            name = f"{player['First Name']} {player['Last Name']}"
            pos = player['Position']
            
            if pos == 'P':
                entry['P'] = name
            elif 'C' in pos or '1B' in pos:
                entry['C/1B'] = name
            elif pos == '2B':
                entry['2B'] = name
            elif pos == '3B':
                entry['3B'] = name
            elif pos == 'SS':
                entry['SS'] = name
            elif 'OF' in pos:
                if of_count == 0:
                    entry['OF1'] = name
                elif of_count == 1:
                    entry['OF2'] = name
                elif of_count == 2:
                    entry['OF3'] = name
                else:
                    entry['UTIL'] = name
                of_count += 1
            else:
                entry['UTIL'] = name
        
        lineup_data.append(entry)
    
    # Save to CSV
    df = pd.DataFrame(lineup_data)
    output_file = r"c:\Users\kgone\OneDrive\Personal_Information\MLB\data\hybrid_tournament_lineups.csv"
    df.to_csv(output_file, index=False)
    print(f"\nSaved {len(lineups)} hybrid lineups to: {output_file}")

if __name__ == "__main__":
    lineups = build_hybrid_tournament_optimizer()
