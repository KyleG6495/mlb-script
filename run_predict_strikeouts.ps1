# run_predict_strikeouts.ps1
& C:/Users/kgone/AppData/Local/Programs/Python/Python311/python.exe `
  .\predict_prop.py `
  --model .\models\strikeouts\strikeouts_gbr.joblib `
  --features ..\data\pitcher_features_probables.csv `
  --lines 5.5 6.5 7.5 `
  --sigma 1.24 `
  --output .\predictions\strikeouts_today.csv
