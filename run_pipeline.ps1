# run_pipeline.ps1
Param(
    [string]$LogFile = "..\data\pipeline.log"
)

# ensure log directory exists
$logDir = Split-Path $LogFile
if (!(Test-Path $logDir)) { New-Item -ItemType Directory -Path $logDir | Out-Null }

function Invoke-Step {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Command
    )
    "`n===== $Name =====" | Tee-Object -FilePath $LogFile -Append
    Invoke-Expression $Command 2>&1 | Tee-Object -FilePath $LogFile -Append
}

# 0. generate initial player lists (prerequisite step)
Invoke-Step -Name "Generate Hitter Games"     -Command "python '1. generate_hitter_games.py'"
Invoke-Step -Name "Generate Pitcher Games"    -Command "python '4. generate_pitcher_games.py'"

# 1. map hitters & pitchers to game_pk
Invoke-Step -Name "Assign Hitter Game PKs"   -Command "python '3. assign_hitter_game_pk.py'"
Invoke-Step -Name "Assign Pitcher Game PKs"  -Command "python '6. assign_pitcher_game_pk.py'"

# 2. generate hitter & pitcher team maps
Invoke-Step -Name "Generate Hitter Team Map"  -Command "python '17. generate_hitter_team_map.py'"
Invoke-Step -Name "Generate Pitcher Team Map" -Command "python '18. generate_pitcher_team_map.py'"

# 3. filter FD slates & enrich features
Invoke-Step -Name "Filter FD Hitters"          -Command "python 'filter_fd_hitters.py'"
Invoke-Step -Name "Aggregate Hitter Stats"     -Command "python '(99)aggregate_hitter_stats.py'"
Invoke-Step -Name "Merge Hitter Features"      -Command "python '15. merge_hitter_features.py'"

Invoke-Step -Name "Filter FD Pitchers"         -Command "python '(17.5)filter_fd_pitchers.py'"
Invoke-Step -Name "Aggregate Pitcher Stats"    -Command "python '10. aggregate_pitcher_stats.py'"
Invoke-Step -Name "Merge Pitcher Features"     -Command "python '16. merge_pitcher_features.py'"

# 4. build today’s feature files
Invoke-Step -Name "Build Today Hitter Features"  -Command "python '14. build_today_hitter_features.py'"
Invoke-Step -Name "Build Today Pitcher Features" -Command "python '11. build_today_pitcher_features.py'"

# 5. pull schedule & merge
Invoke-Step -Name "Pull Game Schedules"       -Command "python 'Pull the schedule for each game_pk.py'"
Invoke-Step -Name "Merge Stats with Schedule" -Command "python 'merge_stats_with_schedule.py'"

"`nPipeline complete! Logs at $LogFile" | Tee-Object -FilePath $LogFile -Append
