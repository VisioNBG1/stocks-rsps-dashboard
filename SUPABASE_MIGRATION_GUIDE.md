# Supabase Migration Guide

## Overview

The system has been restructured to store stock data directly in Supabase instead of relying on ephemeral local cache files. This ensures data persistence across Render deployments.

## New Structure

### 1. New Table: `stock_data`

This table stores actual stock data for each stage:
- **ticker**: Stock symbol (e.g., "AAPL")
- **stage**: Processing stage ("downloaded", "z_scored", "ratio_analyzed", "backtested")
- **date_str**: Date in "YYYY-MM-DD" format
- **data**: JSONB column containing the actual stock data (DataFrame serialized as JSON)

### 2. Existing Table: `checkpoints`

Still used for tracking overall progress, but now works in conjunction with `stock_data`.

## Setup Instructions

### Step 1: Create the New Table

1. Go to your Supabase project: https://fzuxkphassgtvfiupixv.supabase.co
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `SUPABASE_NEW_STRUCTURE.sql`
4. Click **Run** to execute

### Step 2: Clear Old Checkpoints (Optional)

If you want to start fresh:

**Option A: Using the Python script**
```bash
export SUPABASE_URL=https://fzuxkphassgtvfiupixv.supabase.co
export SUPABASE_KEY=your_api_key_here
python clear_supabase.py
```

**Option B: Using Supabase SQL Editor**
```sql
DELETE FROM checkpoints;
```

### Step 3: Deploy Updated Code

The code has been updated to:
- Save stock data to Supabase when downloaded
- Load stock data from Supabase when resuming
- Use Supabase as the source of truth for downloaded stocks

Just push to GitHub and Render will auto-deploy.

## How It Works

### Downloading Stage
1. When a stock is downloaded, it's saved to Supabase `stock_data` table with `stage='downloaded'`
2. The checkpoint is updated with the list of downloaded stock symbols
3. On resume, the system loads stock data from Supabase instead of local cache files

### Other Stages
- Z-scoring: Save results with `stage='z_scored'`
- Ratio Analysis: Save results with `stage='ratio_analyzed'`
- Backtesting: Save results with `stage='backtested'`

## Benefits

1. **Persistent Storage**: Stock data survives Render deployments
2. **No Re-downloading**: Stocks are only downloaded once per day
3. **Faster Resumes**: Can resume from any stage without re-downloading
4. **Better Tracking**: Each stock's progress is tracked individually

## Removed Stocks

The following delisted stocks have been removed from the analysis:
- SPLK (Splunk - acquired)
- MRO (Marathon Oil - merged)
- HTA (Healthcare Trust of America - merged)
- ETFC (E*TRADE - acquired)

## Troubleshooting

### Issue: "Table stock_data does not exist"
**Solution**: Run the SQL from `SUPABASE_NEW_STRUCTURE.sql` in your Supabase SQL Editor

### Issue: "RLS policy violation"
**Solution**: The SQL script includes RLS policies. Make sure you ran the complete script.

### Issue: Still re-downloading stocks
**Solution**: 
1. Check that stock data is being saved (look for "💾 Saved X to Supabase" in logs)
2. Verify the `stock_data` table exists and has data
3. Check that `get_downloaded_stocks_from_supabase()` is working

