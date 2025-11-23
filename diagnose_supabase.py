"""
Diagnostic script to check Supabase stock_data table and fix any issues.
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

print("🔍 Diagnosing Supabase stock_data table...\n")

# 1. Check if table exists
print("1. Checking table access...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker,stage,date_str&limit=1",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        print("   ✅ Table exists and is accessible")
    else:
        print(f"   ❌ Table issue: {response.status_code}")
        print(f"   Response: {response.text[:300]}")
        exit(1)
except Exception as e:
    print(f"   ❌ Error: {e}")
    exit(1)

# 2. Get a sample record to check data structure
print("\n2. Checking data structure...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=*&limit=1",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        records = response.json()
        if records:
            record = records[0]
            ticker = record.get("ticker")
            data = record.get("data", {})
            
            print(f"   Sample ticker: {ticker}")
            print(f"   Data type: {type(data)}")
            
            if isinstance(data, dict):
                print(f"   Data keys: {list(data.keys())}")
                if "columns" in data:
                    print(f"   Columns: {data['columns']} ({len(data['columns'])} columns)")
                if "data" in data:
                    data_rows = data.get("data", [])
                    print(f"   Data rows: {len(data_rows)}")
                    if data_rows:
                        first_row = data_rows[0]
                        print(f"   First row: {first_row} ({len(first_row) if isinstance(first_row, list) else 'N/A'} values)")
                        if len(data.get("columns", [])) != len(first_row):
                            print(f"   ⚠ MISMATCH: {len(data.get('columns', []))} columns but {len(first_row)} values in first row!")
                if "index" in data:
                    print(f"   Index length: {len(data.get('index', []))}")
        else:
            print("   ℹ No records found in table")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 3. Count records
print("\n3. Counting records...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        records = response.json()
        print(f"   Total records: {len(records)}")
        
        # Count by stage
        stages = {}
        for record in records:
            stage = record.get("stage", "unknown")
            stages[stage] = stages.get(stage, 0) + 1
        
        for stage, count in stages.items():
            print(f"   - {stage}: {count} records")
except Exception as e:
    print(f"   ⚠ Error: {e}")

# 4. Check for problematic records
print("\n4. Checking for data structure issues...")
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/stock_data?select=ticker,data",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        records = response.json()
        problematic = []
        
        for record in records:
            ticker = record.get("ticker")
            data = record.get("data", {})
            
            if isinstance(data, dict) and "columns" in data and "data" in data:
                cols = len(data.get("columns", []))
                rows = data.get("data", [])
                if rows and len(rows[0]) != cols:
                    problematic.append({
                        "ticker": ticker,
                        "cols": cols,
                        "row_cols": len(rows[0]) if rows else 0
                    })
        
        if problematic:
            print(f"   ⚠ Found {len(problematic)} problematic records:")
            for p in problematic[:10]:
                print(f"      - {p['ticker']}: {p['cols']} columns but {p['row_cols']} values in data")
            print(f"\n   💡 These records need to be fixed or deleted")
        else:
            print("   ✅ All records have correct structure")
except Exception as e:
    print(f"   ⚠ Error: {e}")

print("\n✅ Diagnosis complete!")

