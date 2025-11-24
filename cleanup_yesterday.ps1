# Clean up duplicates from yesterday (2025-11-23)
$serviceUrl = "https://stocks-rsps-dashboard.onrender.com"
$cleanupUrl = "$serviceUrl/cleanup-duplicates?date=2025-11-23"

Write-Host "Cleaning up duplicates from 2025-11-23..." -ForegroundColor Yellow
Write-Host "URL: $cleanupUrl" -ForegroundColor Gray
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $cleanupUrl -Method POST -UseBasicParsing
    
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host ""
    $result = $response.Content | ConvertFrom-Json
    Write-Host "Results:" -ForegroundColor Cyan
    Write-Host "  Date: $($result.date)" -ForegroundColor White
    Write-Host "  Total records before: $($result.total_records_before)" -ForegroundColor White
    Write-Host "  Duplicates found: $($result.duplicates_found)" -ForegroundColor White
    Write-Host "  Duplicates deleted: $($result.duplicates_deleted)" -ForegroundColor Green
    Write-Host "  Unique stocks after: $($result.unique_stocks)" -ForegroundColor White
    Write-Host "  Expected: $($result.expected_stocks)" -ForegroundColor White
    Write-Host "  Status: $($result.status_check)" -ForegroundColor $(if ($result.status_check -eq "perfect") { "Green" } else { "Yellow" })
    
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Response:" -ForegroundColor Yellow
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        $reader.DiscardBufferedData()
        $responseBody = $reader.ReadToEnd()
        Write-Host $responseBody
    }
}

