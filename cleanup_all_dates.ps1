# Clean up duplicates from ALL dates
$serviceUrl = "https://stocks-rsps-dashboard.onrender.com"
$cleanupUrl = "$serviceUrl/cleanup-duplicates?all_dates=true"

Write-Host "Cleaning up duplicates from ALL dates..." -ForegroundColor Yellow
Write-Host "URL: $cleanupUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "⚠️  This will clean duplicates across all dates in the database" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $cleanupUrl -Method POST -UseBasicParsing
    
    Write-Host "✅ SUCCESS!" -ForegroundColor Green
    Write-Host ""
    $result = $response.Content | ConvertFrom-Json
    Write-Host "Results:" -ForegroundColor Cyan
    Write-Host "  Date(s) cleaned: $($result.date)" -ForegroundColor White
    if ($result.cleaned_dates) {
        Write-Host "  Dates: $($result.cleaned_dates -join ', ')" -ForegroundColor Gray
    }
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



