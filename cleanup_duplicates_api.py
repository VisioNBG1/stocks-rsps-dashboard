"""Script to clean up duplicate entries in Supabase stock_data table using REST API"""
import requests
import json
from datetime import datetime

# Supabase credentials
SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPNhaXm4hyT8f2und08U"

date_str = datetime.now().strftime("%Y-%m-%d")
print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")
print(f"📅 Working with date: {date_str}\n")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

# Get all downloaded stocks from stock_data
print("=" * 60)
print("CLEANING UP DUPLICATES IN stock_data TABLE")
print("=" * 60)

try:
    # Query all records
    url = f"{SUPABASE_URL}/rest/v1/stock_data"
    params = {
        "stage": "eq.downloaded",
        "date_str": f"eq.{date_str}",
        "order": "id.asc",
        "select": "ticker,id,created_at"
    }
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    
    all_records = response.json()
    print(f"✅ Found {len(all_records)} total records in stock_data for {date_str}")
    
    if not all_records:
        print("❌ No records found")
    else:
        # Group by ticker to find duplicates
        ticker_counts = {}
        for record in all_records:
            ticker = record.get("ticker")
            if ticker not in ticker_counts:
                ticker_counts[ticker] = []
            ticker_counts[ticker].append(record)
        
        # Find duplicates
        duplicates = {t: records for t, records in ticker_counts.items() if len(records) > 1}
        
        if duplicates:
            print(f"\n⚠️  Found {len(duplicates)} tickers with duplicate entries:")
            total_duplicates = 0
            for ticker, records in duplicates.items():
                print(f"   {ticker}: {len(records)} entries (IDs: {[r['id'] for r in records]})")
                total_duplicates += len(records) - 1
            
            print(f"\n🗑️  Deleting {total_duplicates} duplicate entries (keeping the oldest for each ticker)...")
            
            # Delete duplicates (keep the one with the smallest ID, which should be oldest)
            deleted_count = 0
            for ticker, records in duplicates.items():
                # Sort by ID, keep first (oldest), delete rest
                sorted_records = sorted(records, key=lambda x: x['id'])
                to_delete = sorted_records[1:]  # All except the first
                
                for record in to_delete:
                    try:
                        delete_url = f"{SUPABASE_URL}/rest/v1/stock_data"
                        delete_params = {"id": f"eq.{record['id']}"}
                        delete_response = requests.delete(delete_url, headers=headers, params=delete_params)
                        delete_response.raise_for_status()
                        deleted_count += 1
                        print(f"   ✓ Deleted duplicate {ticker} (ID: {record['id']})")
                    except Exception as e:
                        print(f"   ❌ Error deleting {ticker} (ID: {record['id']}): {e}")
            
            print(f"\n✅ Deleted {deleted_count} duplicate entries")
        else:
            print("✅ No duplicates found")
        
        # Get unique tickers after cleanup
        response = requests.get(url, headers=headers, params={**params, "select": "ticker"})
        response.raise_for_status()
        all_tickers_data = response.json()
        unique_tickers = list(set([r.get("ticker") for r in all_tickers_data if r.get("ticker")]))
        print(f"\n📊 Total unique downloaded stocks after cleanup: {len(unique_tickers)}")
        
        # Verify we have exactly 334 stocks (KO should be the last one)
        if len(unique_tickers) > 334:
            print(f"\n⚠️  WARNING: Still have {len(unique_tickers)} stocks, expected 334")
            print(f"   This might indicate there are stocks beyond KO that need to be removed")
        elif len(unique_tickers) < 334:
            print(f"\n⚠️  WARNING: Only have {len(unique_tickers)} stocks, expected 334")
        else:
            print(f"\n✅ Perfect! Have exactly 334 stocks as expected")
        
        print(f"\n   Sample tickers: {', '.join(sorted(unique_tickers)[:20])}{'...' if len(unique_tickers) > 20 else ''}")
        if "KO" in unique_tickers:
            ko_index = sorted(unique_tickers).index("KO")
            print(f"\n   KO is at position {ko_index + 1} in sorted list")
        
except Exception as e:
    print(f"❌ Error cleaning up stock_data: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("CLEANUP COMPLETE")
print("=" * 60)



