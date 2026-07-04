# Pack a minimal Hugging Face Space (fixes monorepo / build timeout issues)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Out = Join-Path $Root "dist\hf-space"

if (Test-Path $Out) { Remove-Item $Out -Recurse -Force }
New-Item -ItemType Directory -Path $Out | Out-Null

$copy = @(
    "Dockerfile", "requirements.txt", "alembic.ini",
    "src", "config", "alembic", "scripts"
)
foreach ($item in $copy) {
    $src = Join-Path $Root $item
    if (Test-Path $src) {
        Copy-Item $src (Join-Path $Out $item) -Recurse -Force
    }
}

Copy-Item (Join-Path $Root "deploy\huggingface\README.md") (Join-Path $Out "README.md") -Force

Write-Host "Packed HF Space to: $Out" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Create HF Space (Docker, CPU basic) at https://huggingface.co/new-space"
Write-Host "2. Clone the Space git repo"
Write-Host "3. Copy all files from dist/hf-space/ into the clone"
Write-Host "4. git add . && git commit -m 'Deploy API' && git push"
Write-Host "5. Add Secrets in Space Settings (DATABASE_URL, GOOGLE_API_KEY, etc.)"
