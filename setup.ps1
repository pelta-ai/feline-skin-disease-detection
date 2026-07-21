# setup.ps1 - Install all project dependencies (Windows / PowerShell)
#
# Usage:
#   ./setup.ps1              Install Python + Flutter dependencies
#   ./setup.ps1 -Python      Install Python dependencies only
#   ./setup.ps1 -Flutter     Install Flutter dependencies only
#
# Creates a Python virtual environment in .venv and installs requirements.txt,
# then runs `flutter pub get` for the mobile app.

param(
    [switch]$Python,
    [switch]$Flutter
)

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$FlutterDir = Join-Path $RepoRoot "app/final_design"
$VenvDir = Join-Path $RepoRoot ".venv"

# If no target flag is given, do both.
if (-not $Python -and -not $Flutter) {
    $Python = $true
    $Flutter = $true
}

function Write-Step($msg)  { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-Ok($msg)    { Write-Host "    [ok] $msg" -ForegroundColor Green }
function Write-Warn($msg)  { Write-Host "    [!]  $msg" -ForegroundColor Yellow }

function Test-Command($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

# --- Python -----------------------------------------------------------------
function Install-Python {
    Write-Step "Python backend + ML dependencies"

    $py = $null
    foreach ($cand in @("python", "python3", "py")) {
        if (Test-Command $cand) { $py = $cand; break }
    }
    if (-not $py) {
        throw "Python not found. Install Python 3.10+ from https://python.org and re-run."
    }
    Write-Ok "Using interpreter: $py"

    if (-not (Test-Path $VenvDir)) {
        Write-Host "    Creating virtual environment in .venv ..."
        & $py -m venv $VenvDir
    } else {
        Write-Ok "Virtual environment .venv already exists"
    }

    $venvPy = Join-Path $VenvDir "Scripts/python.exe"
    Write-Host "    Upgrading pip ..."
    & $venvPy -m pip install --upgrade pip --quiet
    Write-Host "    Installing requirements.txt ..."
    & $venvPy -m pip install -r (Join-Path $RepoRoot "requirements.txt")
    Write-Ok "Python dependencies installed"
    Write-Host "    Activate with: .\.venv\Scripts\Activate.ps1"
}

# --- Flutter ----------------------------------------------------------------
function Install-Flutter {
    Write-Step "Flutter app dependencies"

    if (-not (Test-Command "flutter")) {
        Write-Warn "Flutter SDK not found. Skipping Flutter dependencies."
        Write-Warn "Install Flutter 3.x from https://docs.flutter.dev/get-started/install"
        return
    }
    if (-not (Test-Path $FlutterDir)) {
        Write-Warn "Flutter project not found at $FlutterDir. Skipping."
        return
    }

    Push-Location $FlutterDir
    try {
        Write-Host "    Running flutter pub get ..."
        flutter pub get
        Write-Ok "Flutter dependencies installed"
    } finally {
        Pop-Location
    }
}

# --- Run --------------------------------------------------------------------
if ($Python)  { Install-Python }
if ($Flutter) { Install-Flutter }

Write-Host "`nDone." -ForegroundColor Green
