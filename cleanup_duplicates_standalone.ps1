# PowerShell script to clean up duplicate entries in Supabase stock_data table
# This script uses the Supabase REST API directly, no Flask server needed

$SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
$SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPNhaXm4hyT8f2und08U"

$dateStr = Get-Date -Format "yyyy-MM-dd"

$separator = "=" * 60
Write-Host $separator
Write-Host "CLEANING UP DUPLICATES IN stock_data TABLE"
Write-Host $separator
Write-Host "Date: $dateStr"
Write-Host ""

$headers = @{
    "apikey" = $SUPABASE_KEY
    "Authorization" = "Bearer $SUPABASE_KEY"
    "Content-Type" = "application/json"
    "Prefer" = "return=representation"
}

try {
    # Get all records
    $url = "$SUPABASE_URL/rest/v1/stock_data"
    $params = @{
        "stage" = "eq.downloaded"
        "date_str" = "eq.$dateStr"
        "order" = "id.asc"
        "select" = "ticker,id,created_at"
    }
    
    $queryParts = @()
    foreach ($key in $params.Keys) {
        $value = $params[$key]
        $queryParts += "$key=$value"
    }
    $queryString = $queryParts -join "&"
    $fullUrl = "$url`?$queryString"
    
    Write-Host "Fetching records from Supabase..."
    $response = Invoke-RestMethod -Uri $fullUrl -Method Get -Headers $headers
    
    if ($null -eq $response -or $response.Count -eq 0) {
        Write-Host "No records found" -ForegroundColor Yellow
        exit
    }
    
    Write-Host "Found $($response.Count) total records" -ForegroundColor Green
    
    # Group by ticker to find duplicates
    $tickerGroups = @{}
    foreach ($record in $response) {
        $ticker = $record.ticker
        if (-not $tickerGroups.ContainsKey($ticker)) {
            $tickerGroups[$ticker] = @()
        }
        $tickerGroups[$ticker] += $record
    }
    
    # Find duplicates
    $duplicates = $tickerGroups.GetEnumerator() | Where-Object { $_.Value.Count -gt 1 }
    
    if ($duplicates.Count -eq 0) {
        Write-Host "No duplicates found!" -ForegroundColor Green
        exit
    }
    
    Write-Host ""
    Write-Host "Found $($duplicates.Count) tickers with duplicate entries:" -ForegroundColor Yellow
    $totalDuplicates = 0
    foreach ($dup in $duplicates) {
        $ticker = $dup.Key
        $count = $dup.Value.Count
        $ids = ($dup.Value | ForEach-Object { $_.id }) -join ", "
        Write-Host "  $ticker : $count entries (IDs: $ids)"
        $totalDuplicates += ($count - 1)
    }
    
    Write-Host ""
    Write-Host "Deleting $totalDuplicates duplicate entries (keeping oldest for each ticker)..." -ForegroundColor Cyan
    
    $deletedCount = 0
    foreach ($dup in $duplicates) {
        $ticker = $dup.Key
        $records = $dup.Value | Sort-Object { $_.id }
        $toDelete = $records[1..($records.Count - 1)]  # All except first
        
        foreach ($record in $toDelete) {
            try {
                $deleteUrl = "$SUPABASE_URL/rest/v1/stock_data?id=eq.$($record.id)"
                Invoke-RestMethod -Uri $deleteUrl -Method Delete -Headers $headers | Out-Null
                $deletedCount++
                Write-Host "  [OK] Deleted duplicate $ticker (ID: $($record.id))" -ForegroundColor Green
            } catch {
                Write-Host "  [ERROR] Failed to delete $ticker (ID: $($record.id)): $_" -ForegroundColor Red
            }
        }
    }
    
    Write-Host ""
    Write-Host "Deleted $deletedCount duplicate entries" -ForegroundColor Green
    
    # Get final count
    $finalResponse = Invoke-RestMethod -Uri "$url?stage=eq.downloaded&date_str=eq.$dateStr&select=ticker" -Method Get -Headers $headers
    $uniqueTickers = ($finalResponse | Select-Object -ExpandProperty ticker -Unique).Count
    
    Write-Host ""
    Write-Host "Total unique downloaded stocks after cleanup: $uniqueTickers" -ForegroundColor Cyan
    
    if ($uniqueTickers -eq 334) {
        Write-Host "Perfect! Have exactly 334 stocks as expected" -ForegroundColor Green
    } elseif ($uniqueTickers -gt 334) {
        Write-Host "WARNING: Still have $uniqueTickers stocks, expected 334" -ForegroundColor Yellow
    } else {
        Write-Host "WARNING: Only have $uniqueTickers stocks, expected 334" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host $_.Exception.Message
    Write-Host $_.ScriptStackTrace
}

Write-Host ""
Write-Host $separator
Write-Host "CLEANUP COMPLETE"
Write-Host $separator

