"""
Script to check Supabase stock_data table structure and verify it's set up correctly.
"""

import requests
import json

SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "sbp_756767befba9e92c366b39649444303b66ad39d4"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("🔍 Checking Supabase stock_data table...\n")

# 1. Check if table exists and is accessible
print("1. Testing table access...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker,stage,date_str&limit=5",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Table exists and is accessible!")
        print(f"   📊 Found {len(data)} records")
        if data:
            print(f"   Sample records:")
            for record in data[:3]:
                print(f"      - {record.get('ticker')} ({record.get('stage')}, {record.get('date_str')})")
    elif response.status_code == 406 or "PGRST205" in response.text:
        print("   ❌ Table does NOT exist")
        print("   📋 Run the SQL in RUN_THIS_SQL.sql")
    else:
        print(f"   ⚠ Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 2. Check table structure by trying to insert a test record
print("\n2. Testing table structure...")
test_record = {
    "ticker": "_TEST_",
    "stage": "downloaded",
    "date_str": "2025-11-23",
    "data": {
        "columns": ["Open", "High", "Low", "Close", "Volume"],
        "index": ["2025-01-01", "2025-01-02"],
        "data": [[100, 105, 99, 103, 1000000], [103, 107, 102, 106, 1100000]]
    }
}

try:
    # Try to insert (will fail if table structure is wrong)
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/stock_data",
        headers=headers,
        json=test_record,
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        print("   ✅ Table structure is correct!")
        # Delete test record
        requests.delete(
            f"{SUPABASE_URL}/rest/v1/stock_data?ticker=eq._TEST_&stage=eq.downloaded&date_str=eq.2025-11-23",
            headers=headers,
            timeout=10
        )
    elif response.status_code == 409:
        print("   ✅ Table structure is correct (test record already exists)")
    else:
        print(f"   ⚠ Status: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 3. Count records by stage
print("\n3. Checking existing records...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker,stage",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        records = response.json()
        stages = {}
        for record in records:
            stage = record.get("stage", "unknown")
            stages[stage] = stages.get(stage, 0) + 1
        
        print(f"   📊 Total records: {len(records)}")
        for stage, count in stages.items():
            print(f"      - {stage}: {count} records")
        
        # Get unique tickers for "downloaded" stage
        downloaded_tickers = set()
        for record in records:
            if record.get("stage") == "downloaded":
                downloaded_tickers.add(record.get("ticker"))
        
        print(f"   📈 Unique downloaded stocks: {len(downloaded_tickers)}")
        if downloaded_tickers:
            print(f"   Sample: {', '.join(sorted(list(downloaded_tickers))[:10])}")
    else:
        print(f"   ⚠ Could not count records: {response.status_code}")
except Exception as e:
    print(f"   ⚠ Error: {e}")

print("\n✅ Check complete!")

