"""Script to clean up duplicate entries in Supabase stock_data table"""
import os
from supabase import create_client, Client
from datetime import datetime
import json

# Get Supabase credentials
SUPABASE_URL = "https://fzuxkphassgtvfiupixv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPNhaXm4hyT8f2und08U"

print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

date_str = datetime.now().strftime("%Y-%m-%d")
print(f"📅 Working with date: {date_str}\n")

# Get all downloaded stocks from stock_data
print("=" * 60)
print("CLEANING UP DUPLICATES IN stock_data TABLE")
print("=" * 60)
try:
    result = supabase.table("stock_data").select("ticker, id, created_at").eq("stage", "downloaded").eq("date_str", date_str).order("id").execute()
    
    if result.data:
        all_records = result.data
        print(f"✅ Found {len(all_records)} total records in stock_data for {date_str}")
        
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
                        supabase.table("stock_data").delete().eq("id", record['id']).execute()
                        deleted_count += 1
                        print(f"   ✓ Deleted duplicate {ticker} (ID: {record['id']})")
                    except Exception as e:
                        print(f"   ❌ Error deleting {ticker} (ID: {record['id']}): {e}")
            
            print(f"\n✅ Deleted {deleted_count} duplicate entries")
        else:
            print("✅ No duplicates found")
        
        # Get unique tickers after cleanup
        result = supabase.table("stock_data").select("ticker").eq("stage", "downloaded").eq("date_str", date_str).execute()
        unique_tickers = list(set([r.get("ticker") for r in result.data if r.get("ticker")]))
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
        
    else:
        print("❌ No records found in stock_data")
        
except Exception as e:
    print(f"❌ Error cleaning up stock_data: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("CLEANUP COMPLETE")
print("=" * 60)



