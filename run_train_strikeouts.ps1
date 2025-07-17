# run_train_strikeouts.ps1
& C:/Users/kgone/AppData/Local/Programs/Python/Python311/python.exe `
  .\train_prop_model.py `
  --category strikeouts `
  --game-log ..\data\pitcher_boxscores_full.csv `
  --features ..\data\pitcher_rolling_5game_features.csv `
  --output-dir .\models\strikeouts
