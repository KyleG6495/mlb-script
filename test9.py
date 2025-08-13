import pandas as pd

# Load both datasets
uf_df = pd.read_csv(r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data\today_pitcher_props_2025-07-19.csv')
pp_df = pd.read_excel(r'C:\Users\kgone\OneDrive\Personal_Information\MLB\data\PP_mlb_picks_20250719_170556.xlsx')

print('✅ PrizePicks file reads successfully!')
print('Shape:', pp_df.shape)
print('Columns:', list(pp_df.columns))

print('\n🔍 PITCHER STRIKEOUTS ANALYSIS:')
print('Pitcher Strikeouts value counts:')
strikeout_counts = pp_df['Pitcher Strikeouts'].value_counts().sort_index()
print(strikeout_counts)

print('\n📋 SEVERINO SPECIFIC DATA:')
severino_data = pp_df[pp_df['player_name'].str.contains('Severino', case=False, na=False)]
if not severino_data.empty:
    print('Severino entries:')
    for _, row in severino_data.iterrows():
        print(f'  {row["player_name"]}: Strikeouts = {row["Pitcher Strikeouts"]}')
else:
    print('No Severino found')

print('\n🎯 SAMPLE OF ACTUAL STRIKEOUT DATA:')
non_null_strikeouts = pp_df[pp_df['Pitcher Strikeouts'].notna()]
print(non_null_strikeouts[['player_name', 'Pitcher Strikeouts']].head(10))

print('\n🔍 SIDE-BY-SIDE COMPARISON:')
print('Underdog Severino: 3.5 strikeouts')
print('PrizePicks Severino: 6.5 strikeouts')
print('Difference: 3.0')
print()
print('🎯 This explains our arbitrage opportunities!')
print('📊 But we need to verify if these are the SAME games/props')