"""Script to fix Supabase data structure and clean up duplicates"""
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

# 1. Get all downloaded stocks from stock_data
print("=" * 60)
print("1. ANALYZING stock_data TABLE")
print("=" * 60)
try:
    result = supabase.table("stock_data").select("ticker, id, created_at").eq("stage", "downloaded").eq("date_str", date_str).order("id").execute()
    
    if result.data:
        all_records = result.data
        print(f"✅ Found {len(all_records)} records in stock_data for {date_str}")
        
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
            
            print(f"\n🗑️  Will delete {total_duplicates} duplicate entries (keeping the oldest for each ticker)...")
            
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
        print(f"\n📊 Total unique downloaded stocks: {len(unique_tickers)}")
        print(f"   Sample: {', '.join(sorted(unique_tickers)[:20])}{'...' if len(unique_tickers) > 20 else ''}")
        
    else:
        print("❌ No records found in stock_data")
        unique_tickers = []
        
except Exception as e:
    print(f"❌ Error analyzing stock_data: {e}")
    import traceback
    traceback.print_exc()
    unique_tickers = []

# 2. Check z_scores table
print("\n" + "=" * 60)
print("2. ANALYZING z_scores TABLE")
print("=" * 60)
try:
    result = supabase.table("z_scores").select("ticker, id, created_at").eq("date_str", date_str).order("id").execute()
    
    if result.data:
        all_z_records = result.data
        print(f"✅ Found {len(all_z_records)} records in z_scores for {date_str}")
        
        # Group by ticker to find duplicates
        z_ticker_counts = {}
        for record in all_z_records:
            ticker = record.get("ticker")
            if ticker not in z_ticker_counts:
                z_ticker_counts[ticker] = []
            z_ticker_counts[ticker].append(record)
        
        # Find duplicates
        z_duplicates = {t: records for t, records in z_ticker_counts.items() if len(records) > 1}
        
        if z_duplicates:
            print(f"\n⚠️  Found {len(z_duplicates)} tickers with duplicate z-score entries:")
            for ticker, records in z_duplicates.items():
                print(f"   {ticker}: {len(records)} entries (IDs: {[r['id'] for r in records]})")
            
            # Delete duplicates
            deleted_z_count = 0
            for ticker, records in z_duplicates.items():
                sorted_records = sorted(records, key=lambda x: x['id'])
                to_delete = sorted_records[1:]
                
                for record in to_delete:
                    try:
                        supabase.table("z_scores").delete().eq("id", record['id']).execute()
                        deleted_z_count += 1
                        print(f"   ✓ Deleted duplicate z-score {ticker} (ID: {record['id']})")
                    except Exception as e:
                        print(f"   ❌ Error deleting z-score {ticker} (ID: {record['id']}): {e}")
            
            print(f"\n✅ Deleted {deleted_z_count} duplicate z-score entries")
        else:
            print("✅ No duplicate z-scores found")
        
        # Get unique z-scored tickers
        result = supabase.table("z_scores").select("ticker").eq("date_str", date_str).execute()
        z_scored_tickers = list(set([r.get("ticker") for r in result.data if r.get("ticker")]))
        print(f"\n📊 Total unique z-scored stocks: {len(z_scored_tickers)}")
        print(f"   Sample: {', '.join(sorted(z_scored_tickers)[:20])}{'...' if len(z_scored_tickers) > 20 else ''}")
        
    else:
        print("❌ No z-scores found")
        z_scored_tickers = []
        
except Exception as e:
    print(f"❌ Error analyzing z_scores: {e}")
    import traceback
    traceback.print_exc()
    z_scored_tickers = []

# 3. Delete X stock if it exists
print("\n" + "=" * 60)
print("3. REMOVING DELISTED STOCK 'X'")
print("=" * 60)
try:
    # Delete from stock_data
    result = supabase.table("stock_data").delete().eq("ticker", "X").eq("date_str", date_str).execute()
    print(f"✅ Deleted X from stock_data")
    
    # Delete from z_scores
    result = supabase.table("z_scores").delete().eq("ticker", "X").eq("date_str", date_str).execute()
    print(f"✅ Deleted X from z_scores")
    
    # Delete from ratio_analysis
    result = supabase.table("ratio_analysis").delete().eq("ticker", "X").eq("date_str", date_str).execute()
    print(f"✅ Deleted X from ratio_analysis")
    
except Exception as e:
    print(f"⚠️  Error deleting X: {e}")

print("\n" + "=" * 60)
print("CLEANUP COMPLETE")
print("=" * 60)
print(f"   Downloaded stocks: {len(unique_tickers)}")
print(f"   Z-scored stocks: {len(z_scored_tickers)}")

