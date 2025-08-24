import pandas as pd
from pathlib import Path

# Load slate
slate_file = Path(__file__).parent.parent / "fd_current_slate" / "fd_slate_today.csv"
df = pd.read_csv(slate_file)

print(f"Total players: {len(df)}")

# Filter to viable players
viable = df[
    (df['Injury Indicator'].isna()) &
    (df['FPPG'] > 0.5)
]

print(f"Viable players: {len(viable)}")

# Check OF players specifically
of_players = viable[viable['Roster Position'].str.contains('OF', na=False)]
print(f"Viable OF players: {len(of_players)}")

if len(of_players) > 0:
    print(f"OF salary range: ${of_players['Salary'].min():,} - ${of_players['Salary'].max():,}")
    print(f"Cheapest 10 OF players:")
    cheap_of = of_players.nsmallest(10, 'Salary')[['First Name', 'Last Name', 'Salary', 'FPPG']]
    for _, p in cheap_of.iterrows():
        name = f"{p['First Name']} {p['Last Name']}"
        print(f"  {name}: ${p['Salary']:,} ({p['FPPG']:.1f} FPPG)")

# Check all position availability
print(f"\nPosition breakdown:")
for pos in ['C', '1B', '2B', '3B', 'SS', 'OF']:
    pos_players = viable[viable['Roster Position'].str.contains(pos, na=False)]
    if len(pos_players) > 0:
        avg_salary = pos_players['Salary'].mean()
        min_salary = pos_players['Salary'].min()
        print(f"  {pos}: {len(pos_players)} players, min: ${min_salary:,}, avg: ${avg_salary:,.0f}")
    else:
        print(f"  {pos}: 0 players - PROBLEM!")
