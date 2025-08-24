import pandas as pd
from datetime import datetime
from config import FilePaths

def create_betting_action_sheet():
    """Create a clear betting action sheet with recommendations"""
    
    # Load the discrepancies data - this should be parameterized for latest file
    df = pd.read_excel(FilePaths.DATA_DIR / 'line_discrepancies_20250719_172504.xlsx')
    
    # Create betting action recommendations
    betting_actions = []
    
    for _, row in df.iterrows():
        player = row['player_name_uf']
        stat = row['stat_type_uf']
        uf_line = row['line_uf']
        pp_line = row['line_pp']
        difference = row['line_diff']
        higher_book = row['higher_line']
        
        # Determine betting actions
        if higher_book == 'PrizePicks':
            # PrizePicks line is higher - bet UNDER on PP, OVER on UF
            uf_action = f"BET OVER {uf_line}"
            pp_action = f"BET UNDER {pp_line}"
            profit_range = f"{uf_line + 0.5} to {pp_line - 0.5}"
        else:
            # Underdog line is higher - bet UNDER on UF, OVER on PP
            uf_action = f"BET UNDER {uf_line}"
            pp_action = f"BET OVER {pp_line}"
            profit_range = f"{pp_line + 0.5} to {uf_line - 0.5}"
        
        # Calculate profit potential
        if difference >= 2.0:
            priority = " HIGH"
            risk_level = "LOW"
        elif difference >= 1.0:
            priority = " MEDIUM"
            risk_level = "LOW"
        else:
            priority = "DATA: SMALL"
            risk_level = "MEDIUM"
        
        betting_actions.append({
            'Player': player,
            'Stat': stat,
            'UF_Line': uf_line,
            'UF_Action': uf_action,
            'PP_Line': pp_line,
            'PP_Action': pp_action,
            'Line_Difference': difference,
            'Both_Win_Range': profit_range,
            'Priority': priority,
            'Risk_Level': risk_level,
            'Expected_Outcome': 'GUARANTEED PROFIT' if difference >= 1.0 else 'LIKELY PROFIT'
        })
    
    # Create DataFrame
    betting_df = pd.DataFrame(betting_actions)
    
    # Sort by line difference (biggest opportunities first)
    betting_df = betting_df.sort_values('Line_Difference', ascending=False)
    
    return betting_df

def save_betting_sheet(betting_df):
    """Save the betting action sheet"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save Excel file
    excel_file = FilePaths.DATA_DIR / f"BETTING_ACTIONS_{timestamp}.xlsx"
    
    # Create Excel with formatting
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        betting_df.to_excel(writer, sheet_name='Betting Actions', index=False)
        
        # Get the worksheet to apply formatting
        worksheet = writer.sheets['Betting Actions']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    # Save text version for quick reference
    text_file = FilePaths.DATA_DIR / f"BETTING_ACTIONS_{timestamp}.txt"
    
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write("TARGET: MLB ARBITRAGE BETTING ACTIONS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Opportunities: {len(betting_df)}\n\n")
        
        for i, row in betting_df.head(10).iterrows():
            f.write(f"TARGET: OPPORTUNITY #{i+1} - {row['Priority']}\n")
            f.write(f"Player: {row['Player']} - {row['Stat']}\n")
            f.write(f"DATA: UNDERDOG FANTASY: {row['UF_Action']}\n")
            f.write(f"DATA: PRIZEPICKS: {row['PP_Action']}\n")
            f.write(f"MONEY: BOTH WIN IF: {row['Both_Win_Range']}\n")
            f.write(f"PROGRESS: Line Difference: {row['Line_Difference']:.1f}\n")
            f.write(f" Expected: {row['Expected_Outcome']}\n")
            f.write("-" * 50 + "\n\n")
    
    return excel_file, text_file

def main():
    """Create and save the betting action sheet"""
    print("TARGET: Creating Betting Action Sheet...")
    
    try:
        # Create betting recommendations
        betting_df = create_betting_action_sheet()
        
        # Save files
        excel_file, text_file = save_betting_sheet(betting_df)
        
        print(f"SUCCESS: Betting Action Sheet Created!")
        print(f"DATA: Excel: {excel_file}")
        print(f" Text: {text_file}")
        print(f"\n TOP 5 BETTING OPPORTUNITIES:")
        print("=" * 60)
        
        for i, row in betting_df.head(5).iterrows():
            print(f"\n{row['Priority']} {row['Player']} - {row['Stat']}")
            print(f"   Underdog: {row['UF_Action']}")
            print(f"   PrizePicks: {row['PP_Action']}")
            print(f"   MONEY: Both win if: {row['Both_Win_Range']}")
            print(f"   PROGRESS: Difference: {row['Line_Difference']:.1f}")
        
    except Exception as e:
        print(f"ERROR: Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()