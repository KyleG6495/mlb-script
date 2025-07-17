import pandas as pd

def validate(path, name):
    df = pd.read_csv(path, dtype={"game_pk": str})
    sched = pd.read_csv(r"..\data\game_schedules.csv", dtype={"game_pk": str})
    
    # Normalize keys (strip off “.0” if present)
    df["game_pk"] = df["game_pk"].str.replace(r"\.0$", "", regex=True)
    
    u_df   = pd.Series(df["game_pk"].unique()).dropna().tolist()
    u_sched= sched["game_pk"].unique().tolist()
    
    print(f"\n— {name} —")
    print(f"Unique {name.lower()} game_pks:  {len(u_df)}")
    print(f"Unique schedule   game_pks:  {len(u_sched)}\n")
    print(f"Sample {name.lower()} keys: {u_df[:10]}")
    print(f"Sample schedule   keys   : {u_sched[:10]}\n")
    
    merged = df.merge(sched, on="game_pk", how="left", indicator=True)
    hits = (merged["_merge"]=="both").sum()
    print(f"Rows that actually match on game_pk: {hits} of {len(df)} {name.lower()}\n")
    print("Schedule columns brought in:", 
          [c for c in merged.columns if c.endswith("_y")])

if __name__ == "__main__":
    validate(r"..\data\hitter_features_with_schedule.csv",  "Hitters")
    validate(r"..\data\pitcher_features_with_schedule.csv", "Pitchers")
