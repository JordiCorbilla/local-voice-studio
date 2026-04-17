$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\.."
Set-Location $root

if (-not (Test-Path ".venv")) {
  python -m venv .venv
}

& "$root\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$root\.venv\Scripts\python.exe" -m pip install -e ".\backend[dev]"

Push-Location "$root\frontend"
npm.cmd install
Pop-Location

Write-Host "Setup complete."
