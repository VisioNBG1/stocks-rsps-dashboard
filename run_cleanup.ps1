# PowerShell script to run cleanup duplicates endpoint
# Replace YOUR_SERVICE_URL with your actual Render service URL

Write-Host "Finding your Render service URL..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Option 1: Check your Render Dashboard" -ForegroundColor Cyan
Write-Host "  1. Go to https://dashboard.render.com" -ForegroundColor White
Write-Host "  2. Click on your 'stocks-rsps-dashboard' service" -ForegroundColor White
Write-Host "  3. Your URL will be shown at the top (e.g., https://stocks-rsps-dashboard.onrender.com)" -ForegroundColor White
Write-Host ""
Write-Host "Option 2: Try common URL pattern" -ForegroundColor Cyan
Write-Host "  Trying: https://stocks-rsps-dashboard.onrender.com" -ForegroundColor White
Write-Host ""

$serviceUrl = "https://stocks-rsps-dashboard.onrender.com"
$cleanupUrl = "$serviceUrl/cleanup-duplicates"

Write-Host "Attempting to call cleanup endpoint..." -ForegroundColor Yellow
Write-Host "URL: $cleanupUrl" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $cleanupUrl -Method POST -UseBasicParsing
    
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Cyan
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 10
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "If you got 'Not Found', your service URL might be different." -ForegroundColor Yellow
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Go to https://dashboard.render.com" -ForegroundColor White
    Write-Host "  2. Find your service and copy its URL" -ForegroundColor White
    Write-Host "  3. Run this command with your actual URL:" -ForegroundColor White
    Write-Host "     Invoke-WebRequest -Uri 'https://YOUR-ACTUAL-URL.onrender.com/cleanup-duplicates' -Method POST" -ForegroundColor Cyan
}

