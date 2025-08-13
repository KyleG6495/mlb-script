# run_daily_betting_pipeline.ps1
# Complete daily betting pipeline - trains models if needed, then finds opportunities

param(
    [string]$Date = (Get-Date -Format "yyyy-MM-dd"),
    [double]$MinEdge = 0.05,
    [switch]$RetrainModels,
    [switch]$TuneModels
)

$PythonExe = "C:/Users/kgone/AppData/Local/Programs/Python/Python311/python.exe"

Write-Host "MLB AUTOMATED BETTING PIPELINE" -ForegroundColor Green
Write-Host "Date: $Date | Min Edge: $($MinEdge * 100)%" -ForegroundColor Cyan
Write-Host "=" * 60

# Step 1: Check if models exist or retrain
$modelsExist = $false
$modelCategories = @("hits", "total_bases", "runs", "rbi", "home_runs", "strikeouts")

Write-Host "Checking for existing models..." -ForegroundColor Cyan
foreach ($cat in $modelCategories) {
    $modelPath1 = ".\models\$cat\$cat" + "_model.pkl"
    $modelPath2 = ".\models\$cat\$cat" + "_pipeline.joblib"
    
    $model1Exists = Test-Path $modelPath1
    $model2Exists = Test-Path $modelPath2
    
    Write-Host "  $cat`: pkl=$model1Exists, joblib=$model2Exists" -ForegroundColor Gray
    
    if ($model1Exists -or $model2Exists) {
        $modelsExist = $true
    }
}

if (-not $modelsExist -or $RetrainModels) {
    Write-Host "Training/Retraining models..." -ForegroundColor Yellow
    
    if ($TuneModels) {
        Write-Host "Running with hyperparameter tuning..." -ForegroundColor Magenta
        & .\run_train_with_holdout.ps1 -Tune -CutoffDate (Get-Date $Date).AddDays(-7)
    } else {
        Write-Host "Running fast training..." -ForegroundColor Cyan
        & .\run_train_all_props.ps1
    }
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Model training failed!" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Model training complete!" -ForegroundColor Green
} else {
    Write-Host "Using existing models" -ForegroundColor Green
}

# Step 2: Run automated betting analysis
Write-Host "`nAnalyzing betting opportunities..." -ForegroundColor Yellow

$analysisArgs = @(
    ".\automated_betting_system.py",
    "--date", $Date,
    "--min-edge", $MinEdge,
    "--models-dir", ".\models",
    "--output-dir", ".\betting_analysis"
)

& $PythonExe @analysisArgs

if ($LASTEXITCODE -eq 0) {
    Write-Host "Betting analysis complete!" -ForegroundColor Green
    
    # Show latest report if exists
    $reportDir = ".\betting_analysis"
    if (Test-Path $reportDir) {
        $latestReport = Get-ChildItem $reportDir -Filter "betting_report_*.txt" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if ($latestReport) {
            Write-Host "`nLATEST BETTING REPORT:" -ForegroundColor Magenta
            Write-Host "-" * 40
            Get-Content $latestReport.FullName | Select-Object -First 30
            Write-Host "`nFull report: $($latestReport.FullName)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "Betting analysis failed!" -ForegroundColor Red
    exit 1
}

Write-Host "`nPipeline complete!" -ForegroundColor Green
