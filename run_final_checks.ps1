$ErrorActionPreference = "Continue"
$root = $PSScriptRoot
$results = @()

Write-Host "`n=== 1/2 BACKEND ACCEPTANCE SUITE ===" -ForegroundColor Cyan
Push-Location "$root\backend"
# Disposable SQLite database only; the configured PostgreSQL DemoDb is untouched.
$env:DATABASE_URL = "sqlite:///./acceptance_test.db"
$env:JWT_SECRET = "local-acceptance-test-secret-only"
$env:CORS_ORIGINS = "http://localhost:5173"
python -m pytest -v tests/test_acceptance.py
$backendExit = $LASTEXITCODE
Pop-Location
$results += [PSCustomObject]@{ Check = "Backend end-to-end acceptance tests"; Result = if ($backendExit -eq 0) { "PASS" } else { "FAIL" } }

Write-Host "`n=== 2/2 FRONTEND PRODUCTION BUILD ===" -ForegroundColor Cyan
Push-Location "$root\frontend"
$frontExit = 0
if (-not (Test-Path "node_modules")) {
    npm install --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { $frontExit = $LASTEXITCODE }
}
if ($frontExit -eq 0) {
    npm run build
    $frontExit = $LASTEXITCODE
}
Pop-Location
$results += [PSCustomObject]@{ Check = "Frontend Vite production build"; Result = if ($frontExit -eq 0) { "PASS" } else { "FAIL" } }

Write-Host "`n=== FINAL CHECK SUMMARY ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize
if ($backendExit -ne 0 -or $frontExit -ne 0) { exit 1 }
Write-Host "All automated checks passed." -ForegroundColor Green
