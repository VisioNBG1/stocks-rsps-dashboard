# Diagnostic script to check what's in the database
$serviceUrl = "https://stocks-rsps-dashboard.onrender.com"

Write-Host "Diagnosing stock_data table..." -ForegroundColor Yellow
Write-Host ""

# Check health endpoint first
Write-Host "1. Checking service health..." -ForegroundColor Cyan
try {
    $health = Invoke-WebRequest -Uri "$serviceUrl/health" -Method GET -UseBasicParsing
    Write-Host "   ✅ Service is online" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Service is offline or unreachable" -ForegroundColor Red
    exit
}

Write-Host ""
Write-Host "2. Checking Supabase directly via API..." -ForegroundColor Cyan
Write-Host "   (This requires checking the actual database structure)" -ForegroundColor Gray
Write-Host ""

# Since we can't directly query Supabase from here, let's add a diagnostic endpoint
Write-Host "To diagnose the issue, we need to:" -ForegroundColor Yellow
Write-Host "  1. Check if there are duplicate tickers within the same date_str" -ForegroundColor White
Write-Host "  2. Check if date_str is being set correctly" -ForegroundColor White
Write-Host "  3. Check the actual count of records per ticker" -ForegroundColor White
Write-Host ""
Write-Host "The cleanup endpoint found 0 duplicates, which means:" -ForegroundColor Yellow
Write-Host "  - Either duplicates were already cleaned" -ForegroundColor White
Write-Host "  - Or duplicates exist but aren't being detected (different date_str?)" -ForegroundColor White
Write-Host "  - Or the 884 rows were from a different table or different stage" -ForegroundColor White
Write-Host ""

Write-Host "Current status:" -ForegroundColor Cyan
Write-Host "  - Total records: 664 (332 per date for 2025-11-23 and 2025-11-24)" -ForegroundColor White
Write-Host "  - Expected: 334 unique stocks per date" -ForegroundColor White
Write-Host "  - Missing: 2 stocks per date (334 - 332 = 2)" -ForegroundColor Yellow
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Check Render logs to see which stocks failed to download" -ForegroundColor White
Write-Host "  2. Verify the stock list has exactly 334 stocks" -ForegroundColor White
Write-Host "  3. Check if any stocks were removed from the list (like 'X')" -ForegroundColor White

