#!/usr/bin/env python3
"""
Script to create the stock_data table in Supabase using the API.
This will set up the new table structure for storing stock data per stage.
"""

import os
import sys
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "sbp_756767befba9e92c366b39649444303b66ad39d4"

print("🔧 Setting up Supabase stock_data table...")
print(f"   URL: {SUPABASE_URL}")

try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Connected to Supabase")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    sys.exit(1)

# SQL commands to create the table
sql_commands = [
    """
    -- Create stock_data table to store actual stock data per stage
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
    """,
    """
    -- Create index for faster lookups
    CREATE INDEX IF NOT EXISTS idx_stock_data_lookup ON stock_data(ticker, stage, date_str);
    """,
    """
    -- Create index for date lookups
    CREATE INDEX IF NOT EXISTS idx_stock_data_date ON stock_data(date_str);
    """,
    """
    -- Enable Row Level Security (RLS)
    ALTER TABLE stock_data ENABLE ROW LEVEL SECURITY;
    """,
    """
    -- Drop existing policy if it exists, then create new one
    DROP POLICY IF EXISTS "Allow all operations on stock_data" ON stock_data;
    CREATE POLICY "Allow all operations on stock_data" ON stock_data
        FOR ALL
        USING (true)
        WITH CHECK (true);
    """,
    """
    -- Create function to automatically update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    """,
    """
    -- Create trigger to automatically update updated_at
    DROP TRIGGER IF EXISTS update_stock_data_updated_at ON stock_data;
    CREATE TRIGGER update_stock_data_updated_at
        BEFORE UPDATE ON stock_data
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """
]

# Execute SQL commands using Supabase RPC (if available) or direct SQL execution
# Note: Supabase Python client doesn't directly support raw SQL execution
# We'll need to use the REST API directly for this

import requests

print("\n📝 Executing SQL commands...")

for i, sql in enumerate(sql_commands, 1):
    sql_clean = sql.strip()
    if not sql_clean or sql_clean.startswith('--'):
        continue
    
    print(f"   [{i}/{len(sql_commands)}] Executing SQL command...")
    
    try:
        # Use Supabase REST API to execute SQL
        # Note: This requires using the service_role key or a function
        # For now, we'll try using the PostgREST API directly
        
        # Alternative: Use Supabase's SQL execution endpoint (if available)
        # This might require service_role key, but let's try with the provided key
        
        # Actually, the best approach is to use Supabase's database functions
        # But for table creation, we need to use the management API or SQL editor
        
        # Since we can't execute DDL via the REST API with anon key,
        # we'll provide instructions and verify the table exists
        print(f"      ⚠ Note: DDL commands (CREATE TABLE) must be run in Supabase SQL Editor")
        print(f"      ℹ Please run the SQL commands manually in Supabase SQL Editor")
        
    except Exception as e:
        print(f"      ⚠ Could not execute via API: {e}")

print("\n" + "="*60)
print("⚠ IMPORTANT: The Supabase Python client cannot execute DDL")
print("   commands (CREATE TABLE) via the REST API.")
print("\n📋 Please do the following:")
print("   1. Go to: https://fzuxkphassgtvfiupixv.supabase.co")
print("   2. Click 'SQL Editor' in the left sidebar")
print("   3. Copy and paste the SQL from SUPABASE_NEW_STRUCTURE.sql")
print("   4. Click 'Run' to execute")
print("="*60)

# Try to verify if table exists (this will work)
print("\n🔍 Checking if stock_data table exists...")
try:
    # Try to query the table (this will fail if it doesn't exist)
    result = supabase_client.table("stock_data").select("ticker").limit(1).execute()
    print("✓ stock_data table exists!")
except Exception as e:
    error_msg = str(e)
    if "Could not find the table" in error_msg or "PGRST205" in error_msg:
        print("❌ stock_data table does NOT exist yet")
        print("   Please run the SQL commands in Supabase SQL Editor")
    else:
        print(f"⚠ Error checking table: {e}")

print("\n✅ Setup script complete!")
print("   Once you've run the SQL in Supabase SQL Editor, the table will be ready.")

