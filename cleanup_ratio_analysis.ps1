# Clean up ratio_analysis table data
$serviceUrl = "https://stocks-rsps-dashboard.onrender.com"
$cleanupUrl = "$serviceUrl/cleanup-ratio-analysis?all_dates=true"

Write-Host "Cleaning up ratio_analysis data from ALL dates..." -ForegroundColor Yellow
Write-Host "URL: $cleanupUrl" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $cleanupUrl -Method POST -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "Cleanup Results:" -ForegroundColor Cyan
    Write-Host "  Status: $($result.status)" -ForegroundColor $(if ($result.status -eq "success") { "Green" } else { "Red" })
    Write-Host "  Message: $($result.message)" -ForegroundColor White
    Write-Host "  Date: $($result.date)" -ForegroundColor Gray
    Write-Host "  Deleted Count: $($result.deleted_count)" -ForegroundColor $(if ($result.deleted_count -gt 0) { "Green" } else { "Yellow" })
    
    if ($result.status -eq "success") {
        Write-Host ""
        Write-Host "✓ Ratio analysis cleanup completed successfully!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "✗ Cleanup failed!" -ForegroundColor Red
    }
} catch {
    Write-Host "Error calling cleanup endpoint:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    Write-Host $_.Exception.Response -ForegroundColor Yellow
}

