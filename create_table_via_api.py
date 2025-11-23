#!/usr/bin/env python3
"""
Script to create stock_data table in Supabase.
Since DDL commands require SQL Editor access, this script will:
1. Check if the table exists
2. Provide the SQL to run if it doesn't exist
"""

import requests

SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "sbp_756767befba9e92c366b39649444303b66ad39d4"

print("🔍 Checking if stock_data table exists in Supabase...\n")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Try to query the table to see if it exists
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker&limit=1",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ stock_data table EXISTS!")
        print("   The table is ready to use.\n")
    elif response.status_code == 406 or "PGRST205" in response.text:
        print("❌ stock_data table does NOT exist\n")
        print("="*70)
        print("📋 ACTION REQUIRED - Run this SQL in Supabase SQL Editor:")
        print("="*70)
        print("\nGo to: https://fzuxkphassgtvfiupixv.supabase.co")
        print("Click: SQL Editor (left sidebar)")
        print("Paste the SQL below and click 'Run':\n")
        print("-"*70)
        
        sql = """CREATE TABLE IF NOT EXISTS stock_data (
    id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    date_str VARCHAR(10) NOT NULL,
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(ticker, stage, date_str)
);

CREATE INDEX IF NOT EXISTS idx_stock_data_lookup ON stock_data(ticker, stage, date_str);
CREATE INDEX IF NOT EXISTS idx_stock_data_date ON stock_data(date_str);

ALTER TABLE stock_data ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all operations on stock_data" ON stock_data;
CREATE POLICY "Allow all operations on stock_data" ON stock_data
    FOR ALL
    USING (true)
    WITH CHECK (true);

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_stock_data_updated_at ON stock_data;
CREATE TRIGGER update_stock_data_updated_at
    BEFORE UPDATE ON stock_data
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();"""
        
        print(sql)
        print("-"*70)
        print("\nAfter running the SQL, the table will be ready!")
    else:
        print(f"⚠ Unexpected response: {response.status_code}")
        print(f"   {response.text[:200]}\n")
        print("Please check your Supabase credentials and try again.")
        
except Exception as e:
    print(f"❌ Error: {e}\n")
    print("Please run the SQL manually in Supabase SQL Editor.")

