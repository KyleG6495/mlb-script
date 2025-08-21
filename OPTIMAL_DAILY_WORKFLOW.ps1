# OPTIMAL DAILY MLB DFS WORKFLOW - PowerShell Version
# This script runs your complete DFS pipeline with error handling

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "              OPTIMAL DAILY MLB DFS WORKFLOW" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Current Date: $(Get-Date -Format 'yyyy-MM-dd')"
Write-Host "Current Time: $(Get-Date -Format 'HH:mm:ss')"
Write-Host ""

# Function to check if a command succeeded
function Test-LastCommand {
    param([string]$StepName)
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] $StepName failed with exit code $LASTEXITCODE" -ForegroundColor Red
        Read-Host "Press Enter to continue anyway, or Ctrl+C to exit"
        return $false
    }
    Write-Host "[SUCCESS] $StepName completed successfully" -ForegroundColor Green
    return $true
}

# Step 0: Verify slate freshness
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                   PHASE 0: SLATE VERIFICATION" -ForegroundColor Yellow  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Checking if fd_slate_today.csv is current..."
python PRE_FLIGHT_CHECKER.py
Test-LastCommand "Slate verification"
Write-Host ""

# Navigate to DAILY_RUNNERS
Set-Location "DAILY_RUNNERS"

# Step 1: Data Pipeline
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                    PHASE 1: DATA PIPELINE" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
& .\1_DATA_PIPELINE.bat
Test-LastCommand "Data pipeline"
Write-Host ""

# Step 2: DFS Models  
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                    PHASE 2: DFS MODELS" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
& .\2_DFS_MODELS.bat
Test-LastCommand "DFS models"
Write-Host ""

# Go back to main directory
Set-Location ".."

# Step 3: Ownership Projections
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "               PHASE 3: OWNERSHIP PROJECTIONS" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
python ADVANCED_OWNERSHIP_PROJECTIONS.py
Test-LastCommand "Ownership projections"
Write-Host ""

# Step 4: Stack Optimization
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                PHASE 4: STACK OPTIMIZATION" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
python ADVANCED_STACK_OPTIMIZER.py
Test-LastCommand "Stack optimization"
Write-Host ""

# Step 5: Elite Lineups
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "               PHASE 5: ELITE LINEUPS" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
python ELITE_TOURNAMENT_WITH_OWNERSHIP.py
Test-LastCommand "Elite lineup generation"
Write-Host ""

# Step 6: Enhanced Models (Optional)
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "            PHASE 6: ENHANCED MODELS (OPTIONAL)" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Set-Location "DAILY_RUNNERS"
& .\4_ENHANCED_MODELS.bat
if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] Enhanced models completed" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Enhanced models had issues, but continuing..." -ForegroundColor Yellow
}
Set-Location ".."
Write-Host ""

# Step 7: GPP Stacking Strategy
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                PHASE 7: STACKING STRATEGY" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
python ENHANCED_GPP_STACKING_STRATEGY.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "[SUCCESS] GPP stacking strategy completed" -ForegroundColor Green
} else {
    Write-Host "[WARNING] GPP stacking had issues, but continuing..." -ForegroundColor Yellow
}
Write-Host ""

# Step 8: Launch Dashboard
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                 PHASE 8: LAUNCH DASHBOARD" -ForegroundColor Yellow
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Starting complete elite DFS dashboard with 4-layer stack analysis..."
python COMPLETE_ELITE_DFS_DASHBOARD.py

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "                      WORKFLOW COMPLETE!" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "All phases completed! Your dashboard now includes:" -ForegroundColor White
Write-Host "  • 4-layer stack analysis (Historical + Weather + Pitcher + Park)" -ForegroundColor Cyan
Write-Host "  • Enhanced ownership projections with context factors" -ForegroundColor Cyan  
Write-Host "  • Elite tournament lineups with advanced strategies" -ForegroundColor Cyan
Write-Host "  • Complete weather, park, and pitcher integration" -ForegroundColor Cyan
Write-Host "  • Export-ready lineup files for FanDuel upload" -ForegroundColor Cyan
Write-Host ""
Write-Host "Happy DFS grinding!" -ForegroundColor Yellow
Read-Host "Press Enter to exit"
