# Clean up ALL data from Supabase (stock_data, z_scores, ratio_analysis, checkpoints)
$serviceUrl = "https://stocks-rsps-dashboard.onrender.com"
$cleanupUrl = "$serviceUrl/cleanup-all-data"

Write-Host "Cleaning up ALL data from Supabase..." -ForegroundColor Yellow
Write-Host "URL: $cleanupUrl" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $cleanupUrl -Method GET -UseBasicParsing
    $result = $response.Content | ConvertFrom-Json
    
    Write-Host "Cleanup Results:" -ForegroundColor Green
    Write-Host "  Status: $($result.status)" -ForegroundColor Cyan
    Write-Host "  Message: $($result.message)" -ForegroundColor Cyan
    Write-Host "  Total Deleted: $($result.total_deleted)" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Deleted Counts:" -ForegroundColor Yellow
    $result.deleted_counts.PSObject.Properties | ForEach-Object {
        Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor Gray
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host "Response: $($_.Exception.Response)" -ForegroundColor Red
}

