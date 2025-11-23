"""
Quick script to verify if stock_data table exists in Supabase.
Run: python verify_table.py
"""

import requests

SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "sbp_756767befba9e92c366b39649444303b66ad39d4"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("🔍 Checking stock_data table...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker&limit=1",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("✅ Table EXISTS! Ready to use.")
    else:
        print(f"❌ Table does NOT exist (Status: {response.status_code})")
        print("\n📋 Run the SQL in RUN_THIS_SQL.sql in Supabase SQL Editor")
except Exception as e:
    print(f"❌ Error: {e}")
    print("\n📋 Run the SQL in RUN_THIS_SQL.sql in Supabase SQL Editor")

