$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\.."
$port = if ($env:LVS_BACKEND_PORT) { $env:LVS_BACKEND_PORT } else { "8000" }
Set-Location "$root\backend"
& "$root\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload --host 127.0.0.1 --port $port
