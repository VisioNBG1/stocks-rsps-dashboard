# Separate Tables Setup Instructions

## Overview

The system now uses separate tables for different stages of analysis:
- `stock_data` - For downloaded stock price data (DataFrames)
- `z_scores` - For z-score analysis results
- `ratio_analysis` - For individual stock ratio analysis results
- `ratio_analysis_summary` - For the overall ratio analysis summary
- `back_test` - For backtest results

## Step 1: Create the Tables

1. Go to your Supabase project: https://fzuxkphassgtvfiupixv.supabase.co
2. Click on **SQL Editor** in the left sidebar
3. Open the file `CREATE_SEPARATE_TABLES.sql` from this repository
4. Copy the entire contents
5. Paste into the SQL Editor
6. Click **Run** (or press Ctrl+Enter)

This will create:
- `z_scores` table
- `ratio_analysis` table
- `back_test` table
- `ratio_analysis_summary` table

All with proper indexes, RLS policies, and triggers.

## Step 2: Verify Tables Were Created

Run this query in the SQL Editor to verify:

```sql
SELECT 
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'public' 
    AND table_name IN ('z_scores', 'ratio_analysis', 'back_test', 'ratio_analysis_summary')
ORDER BY table_name, ordinal_position;
```

You should see all columns for all 4 tables.

## Step 3: Verify Z-Scores Are Being Saved

After the next deployment, you can verify z-scores are being saved by running:

```sql
SELECT ticker, z_avg, avg_score, sector, updated_at 
FROM z_scores 
WHERE date_str = CURRENT_DATE::text
ORDER BY updated_at DESC
LIMIT 10;
```

## Migration Notes

- The code maintains backward compatibility with the old `stock_data` table structure
- New z-scores will be saved to the `z_scores` table
- The system will check both tables when loading z-scores (new table first, then legacy)
- Old data in `stock_data` with `stage='z_scored'` will still be accessible

## Table Structures

### z_scores
- `ticker` (TEXT) - Stock ticker symbol
- `date_str` (TEXT) - Date string (YYYY-MM-DD)
- `z_avg` (NUMERIC) - Average z-score
- `avg_score` (NUMERIC) - Average score
- `sector` (TEXT) - Sector name
- `analysis_result` (JSONB) - Full analysis result
- Unique constraint: `(ticker, date_str)`

### ratio_analysis
- `ticker` (TEXT) - Stock ticker symbol
- `date_str` (TEXT) - Date string (YYYY-MM-DD)
- `ratio_score` (NUMERIC) - Ratio score
- `num_comparisons` (INTEGER) - Number of comparisons made
- `ratio_z_scores` (JSONB) - Array of ratio z-scores
- Unique constraint: `(ticker, date_str)`

### ratio_analysis_summary
- `date_str` (TEXT) - Date string (YYYY-MM-DD)
- `ratio_analysis` (JSONB) - Full ratio analysis summary
- `timestamp` (TEXT) - Timestamp string
- `total_stocks` (INTEGER) - Total number of stocks analyzed
- Unique constraint: `(date_str)`

### back_test
- `date_str` (TEXT) - Date string (YYYY-MM-DD)
- `backtest_results` (JSONB) - Backtest results
- `ratio_analysis` (JSONB) - Ratio analysis data
- `timestamp` (TEXT) - Timestamp string
- Unique constraint: `(date_str)`

