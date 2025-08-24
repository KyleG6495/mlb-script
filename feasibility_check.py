import pandas as pd

# Load slate
slate = pd.read_csv('../fd_current_slate/fd_slate_today.csv')
slate = slate[slate['FPPG'] > 1.0]
slate = slate.dropna(subset=['Salary', 'FPPG', 'Roster Position'])

print('Basic feasibility check:')
print('Can we build a lineup manually?')

# Find cheapest player for each position
positions = ['P', 'C/1B', '2B', '3B', 'SS', 'OF', 'UTIL']

total_min_salary = 0
for pos in positions:
    if pos == 'OF':
        of_players = slate[slate['Roster Position'].str.contains('OF', na=False)]
        if len(of_players) >= 3:
            cheapest_3 = of_players.nsmallest(3, 'Salary')
            min_salary = cheapest_3['Salary'].sum()
            print(f'  {pos} (3 players): ${min_salary}')
            total_min_salary += min_salary
        else:
            print(f'  {pos}: NOT ENOUGH PLAYERS')
    else:
        eligible = slate[slate['Roster Position'].str.contains(pos, na=False)]
        if len(eligible) > 0:
            min_salary = eligible['Salary'].min()
            print(f'  {pos}: ${min_salary} ({len(eligible)} available)')
            total_min_salary += min_salary
        else:
            print(f'  {pos}: NO PLAYERS FOUND')

print(f'Minimum possible salary: ${total_min_salary}')
print(f'Salary cap: $35,000')
print(f'Feasible: {"YES" if total_min_salary <= 35000 else "NO"}')
