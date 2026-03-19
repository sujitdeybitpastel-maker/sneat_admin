$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPath = Join-Path $root ".venv"
$pythonExe = Join-Path $venvPath "Scripts\\python.exe"

if (-not (Test-Path $venvPath)) {
  python -m venv $venvPath
}

& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install -r (Join-Path $root "requirements.txt")

if (-not (Test-Path (Join-Path $root "instance"))) {
  New-Item -ItemType Directory -Path (Join-Path $root "instance") | Out-Null
}

$env:FLASK_APP = "run.py"
$env:FLASK_ENV = "development"

Write-Host ""
Write-Host "Starting Flask app on http://127.0.0.1:5000" -ForegroundColor Green
Write-Host "Demo admin login: admin / admin123" -ForegroundColor Yellow
Write-Host ""

& $pythonExe (Join-Path $root "run.py")
