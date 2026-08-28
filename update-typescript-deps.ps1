# PowerShell wrapper for the OBINexus TypeScript dependency updater.
#
# Usage examples:
#   .\update-typescript-deps.ps1 -DryRun
#   .\update-typescript-deps.ps1 -VerboseOutput
#   .\update-typescript-deps.ps1 -Install -LegacyPeerDeps
#   .\update-typescript-deps.ps1 -Workspace .\obix -TypeScriptVersion 5.4.0

param(
    [switch]$DryRun,
    [Alias("Verbose", "v")]
    [switch]$VerboseOutput,
    [switch]$Install,
    [switch]$LegacyPeerDeps,
    [string]$Workspace,
    [string]$TypeScriptVersion = "5.4.0",
    [int]$NpmTimeout = 600
)

$ErrorActionPreference = "Stop"
$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonScript = Join-Path $ScriptPath "update-typescript-deps.py"

if (-not (Test-Path -LiteralPath $PythonScript -PathType Leaf)) {
    Write-Host "Error: update-typescript-deps.py not found at $PythonScript" -ForegroundColor Red
    exit 1
}

# Prefer the Windows Python launcher when available, then fall back to python.
$PythonCommand = $null
$PythonPrefix = @()

if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = "py"
    $PythonPrefix = @("-3")
}
elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = "python"
}
elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $PythonCommand = "python3"
}
else {
    Write-Host "Error: Python 3 was not found in PATH." -ForegroundColor Red
    exit 1
}

$UpdaterArgs = @()

if ($DryRun) {
    $UpdaterArgs += "--dry-run"
    Write-Host "[DRY RUN MODE] Changes will be reported but not applied" -ForegroundColor Yellow
}

if ($VerboseOutput) {
    $UpdaterArgs += "--verbose"
}

if ($Install) {
    $UpdaterArgs += "--install"
}

if ($LegacyPeerDeps) {
    $UpdaterArgs += "--legacy-peer-deps"
}

if ($Workspace) {
    $UpdaterArgs += @("--workspace", $Workspace)
}

$UpdaterArgs += @("--typescript-version", $TypeScriptVersion)
$UpdaterArgs += @("--npm-timeout", $NpmTimeout.ToString())

Write-Host "Starting OBINexus TypeScript Dependency Updater..." -ForegroundColor Cyan
& $PythonCommand @PythonPrefix $PythonScript @UpdaterArgs
$ExitCode = $LASTEXITCODE

if ($ExitCode -ne 0) {
    Write-Host "Script failed with exit code $ExitCode" -ForegroundColor Red
    exit $ExitCode
}

Write-Host "Done!" -ForegroundColor Green
exit 0
