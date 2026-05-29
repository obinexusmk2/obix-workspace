# PowerShell wrapper for TypeScript dependency updater
# Usage: .\update-typescript-deps.ps1 [--dry-run] [--verbose] [--install]

param(
    [switch]$DryRun,
    [switch]$Verbose,
    [switch]$Install
)

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptPath "update-typescript-deps.py"

if (-not (Test-Path $PythonScript)) {
    Write-Host "Error: update-typescript-deps.py not found at $PythonScript" -ForegroundColor Red
    exit 1
}

# Build arguments
$Args = @()

if ($DryRun) {
    $Args += "--dry-run"
    Write-Host "[DRY RUN MODE] Changes will be reported but not applied" -ForegroundColor Yellow
}

if ($Verbose) {
    $Args += "--verbose"
}

# Run the Python script
Write-Host "Starting OBINexus TypeScript Dependency Updater..." -ForegroundColor Cyan
python $PythonScript @Args

if ($LASTEXITCODE -ne 0) {
    Write-Host "Script failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}

# Optionally run full workspace install
if ($Install) {
    Write-Host "`nRunning full workspace npm install..." -ForegroundColor Cyan
    npm install --legacy-peer-deps
}
