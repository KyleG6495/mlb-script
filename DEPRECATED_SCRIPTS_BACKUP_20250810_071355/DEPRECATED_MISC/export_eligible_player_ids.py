import pandas as pd
import os

def export_eligible_player_ids():
    slate_path = '../fd_current_slate/fd_slate_today.csv'
    output_path = '../fd_current_slate/eligible_player_ids.csv'
    if not os.path.exists(slate_path):
        print(f"❌ Slate file not found: {slate_path}")
        return
    slate_df = pd.read_csv(slate_path)
    eligibility_col = slate_df.columns[-2]
    valid = slate_df[(slate_df['Played'] > 0) & ~slate_df[eligibility_col].astype(str).isin(['0', 'O', 'o']) & (slate_df[eligibility_col] != 0)]
    valid[['Id', 'First Name', 'Last Name', 'Team', 'Primary_Position']].to_csv(output_path, index=False)
    print(f"✅ Exported {len(valid)} eligible player IDs to {output_path}")

if __name__ == "__main__":
    export_eligible_player_ids()
