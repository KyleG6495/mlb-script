#!/usr/bin/env python3
"""
DISPLAY FILTERED LINEUPS - Show your lineups and actual scores
"""

import pandas as pd

def main():
    print('LINEUP: YOUR FILTERED LINEUPS FROM AUGUST 12TH SLATE')
    print('=' * 60)

    # Load the lineup data
    lineup_df = pd.read_csv('FILTERED_LINEUPS_AUG12_20250813_112908.csv')

    strategies = ['Filtered Base', 'Filtered Value Focus', 'Filtered Anti-Chalk', 'Filtered Upside', 'Filtered Balanced']
    actual_scores = [257.4, 232.5, 235.2, 268.7, 247.5]

    for i, strategy in enumerate(strategies):
        strategy_data = lineup_df[lineup_df['Strategy'] == strategy]
        total_salary = strategy_data['Salary'].sum()
        
        print(f'\nTARGET: {strategy.upper()} - {actual_scores[i]:.1f} POINTS')
        print(f'Salary Used: ${total_salary:,} | Remaining: ${35000-total_salary:,}')
        print('-' * 50)
        
        for _, row in strategy_data.iterrows():
            pos = row['Position']
            name = row['Name']
            salary = row['Salary']
            fpts = row['FPTS']
            print(f'  {pos:2}: {name:20} ${salary:,} -> {fpts:5.1f} pts')

    print('\n' + '=' * 60)
    print('DATA: PERFORMANCE RANKING:')
    print('1. Filtered Upside:      268.7 points ')
    print('2. Filtered Base:        257.4 points ')
    print('3. Filtered Balanced:    247.5 points ')
    print('4. Filtered Anti-Chalk:  235.2 points')
    print('5. Filtered Value Focus: 232.5 points')
    print('\nPROGRESS: COMPARISON:')
    print('Tournament Winner:       306.0 points')
    print('Your Best Filtered:      268.7 points (-37.3)')
    print('Your Original Best:      139.9 points')
    print('Improvement:            +128.8 points (+92.1%)')

if __name__ == "__main__":
    main()
