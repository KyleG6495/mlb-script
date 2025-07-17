# run_train_all_props.ps1

# List of hitter props and the shared hitter files
$hitter_props = @(
  "hits","total_bases","runs","rbi",
  "home_runs","hrr","stolen_bases","hr_binary"
)
$hitter_log  = "..\data\hitter_boxscores_full.csv"
$hitter_feat = "..\data\hitter_rolling_5game_features.csv"

# Train all hitter models
foreach ($cat in $hitter_props) {
  $out = ".\models\$cat"
  Write-Host "Training $cat (hitters)…"
  & C:/Users/kgone/AppData/Local/Programs/Python/Python311/python.exe `
    .\train_prop_model.py `
      --category $cat `
      --game-log  $hitter_log `
      --features  $hitter_feat `
      --output-dir $out
}

# List of pitcher props and the shared pitcher files
$pitcher_props = @(
  "strikeouts","outs","win_binary"
)
$pitcher_log  = "..\data\pitcher_boxscores_full.csv"
$pitcher_feat = "..\data\pitcher_rolling_5game_features.csv"

# Train all pitcher models
foreach ($cat in $pitcher_props) {
  $out = ".\models\$cat"
  Write-Host "Training $cat (pitchers)…"
  & C:/Users/kgone/AppData/Local/Programs/Python/Python311/python.exe `
    .\train_prop_model.py `
      --category $cat `
      --game-log  $pitcher_log `
      --features  $pitcher_feat `
      --output-dir $out
}
