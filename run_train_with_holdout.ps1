param(
    [string]$PythonExe = "C:/Users/kgone/AppData/Local/Programs/Python/Python311/python.exe",
    [switch]$Tune,
    [datetime]$CutoffDate = "2025-07-10"
)

# Define your log & feature files
$hittersLog   = "..\data\hitter_boxscores_full.csv"
$hittersFeat  = "..\data\hitter_rolling_5game_features.csv"
$pitchersLog  = "..\data\pitcher_boxscores_full.csv"
$pitchersFeat = "..\data\pitcher_rolling_5game_features.csv"

# Output base directory
$outputBase = ".\models"

# Categories to train
$categories = @(
    "hits","total_bases","runs","rbi",
    "home_runs","hrr","stolen_bases",
    "hr_binary","strikeouts","outs","win_binary"
)

foreach ($cat in $categories) {
    Write-Host "`n=== Training $cat (with holdout, cutoff=$($CutoffDate.ToString('yyyy-MM-dd'))) ==="

    if ($cat -in "strikeouts","outs","win_binary") {
        $gameLog  = $pitchersLog
        $features = $pitchersFeat
    } else {
        $gameLog  = $hittersLog
        $features = $hittersFeat
    }

    $outDir = Join-Path $outputBase $cat

    # Build argument list for Python script
    $argsList = @(
        ".\Train Prop Model With Holdout.py",
        "--category",    $cat,
        "--game-log",    $gameLog,
        "--features",    $features,
        "--output-dir",  $outDir,
        "--cutoff-date", $CutoffDate.ToString("yyyy-MM-dd")
    )

    if ($Tune) {
        $argsList += "--tune"
    }

    & $PythonExe @argsList
}

Write-Host "`nAll done!"

