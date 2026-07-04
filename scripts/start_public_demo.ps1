# Start FastAPI + Cloudflare quick tunnel for a public demo URL.
# Usage: .\scripts\start_public_demo.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$venvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Error "Virtual env not found. Run: python -m venv .venv && .\.venv\Scripts\pip install -r requirements.txt"
}

# Load CORS for GitHub Pages if not set in .env
if (-not $env:CORS_ORIGINS) {
    $env:CORS_ORIGINS = "https://ankitashok15.github.io,http://localhost:5173"
}

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    $fallback = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
    if (Test-Path $fallback) { $cloudflared = Get-Item $fallback }
}
if (-not $cloudflared) {
    Write-Host ""
    Write-Host "cloudflared not found. Install with:" -ForegroundColor Yellow
    Write-Host "  winget install Cloudflare.cloudflared" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Then restart PowerShell and run this script again." -ForegroundColor Yellow
    exit 1
}

Write-Host "Starting API on http://localhost:8000 ..." -ForegroundColor Green
$apiJob = Start-Job -ScriptBlock {
    param($Root)
    Set-Location $Root
    & "$Root\.venv\Scripts\python.exe" -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000
} -ArgumentList $ProjectRoot

Start-Sleep -Seconds 4

Write-Host "Starting Cloudflare tunnel ..." -ForegroundColor Green
Write-Host "Waiting for public URL (copy the https://....trycloudflare.com line below):" -ForegroundColor Cyan
Write-Host ""

try {
    if ($cloudflared -is [System.IO.FileInfo]) {
        & $cloudflared.FullName tunnel --url http://localhost:8000
    } else {
        & cloudflared tunnel --url http://localhost:8000
    }
}
finally {
    Stop-Job $apiJob -ErrorAction SilentlyContinue
    Remove-Job $apiJob -Force -ErrorAction SilentlyContinue
}
