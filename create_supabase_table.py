#!/usr/bin/env python3
"""
Script to create the stock_data table in Supabase using the REST API.
"""

import requests
import json

# Supabase credentials
SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "sbp_756767befba9e92c366b39649444303b66ad39d4"

print("🔧 Creating stock_data table in Supabase...")
print(f"   URL: {SUPABASE_URL}\n")

# The complete SQL to create the table
sql = """
CREATE TABLE IF NOT EXISTS stock_data (
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
    EXECUTE FUNCTION update_updated_at_column();
"""

# Try to execute via Supabase REST API
# Note: DDL commands typically require service_role key, but let's try

try:
    # Supabase doesn't expose a direct SQL execution endpoint via REST API
    # We need to use the SQL Editor or a database function
    # However, we can verify if the table exists by trying to query it
    
    print("⚠ Note: Supabase REST API cannot execute DDL commands (CREATE TABLE)")
    print("   These must be run in the Supabase SQL Editor.\n")
    
    # Verify if table exists by trying to query it
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    print("🔍 Checking if stock_data table exists...")
    check_url = f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker&limit=1"
    response = requests.get(check_url, headers=headers, timeout=10)
    
    if response.status_code == 200:
        print("✓ stock_data table EXISTS and is accessible!")
        print("   The table is ready to use.")
    elif response.status_code == 404 or "PGRST205" in response.text:
        print("❌ stock_data table does NOT exist")
        print("\n" + "="*70)
        print("📋 ACTION REQUIRED:")
        print("="*70)
        print("1. Go to: https://fzuxkphassgtvfiupixv.supabase.co")
        print("2. Click 'SQL Editor' in the left sidebar")
        print("3. Copy the SQL below and paste it into the editor:")
        print("4. Click 'Run' (or press Ctrl+Enter)")
        print("\n" + "-"*70)
        print("SQL TO RUN:")
        print("-"*70)
        print(sql)
        print("-"*70)
    else:
        print(f"⚠ Unexpected response: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.exceptions.RequestException as e:
    print(f"❌ Error connecting to Supabase: {e}")
    print("\n📋 Please run the SQL manually in Supabase SQL Editor:")
    print("   https://fzuxkphassgtvfiupixv.supabase.co")
    print("\nSQL:")
    print(sql)
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📋 Please run the SQL manually in Supabase SQL Editor:")
    print("   https://fzuxkphassgtvfiupixv.supabase.co")
    print("\nSQL:")
    print(sql)

print("\n✅ Script complete!")

