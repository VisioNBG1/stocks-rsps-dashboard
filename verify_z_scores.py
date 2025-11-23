"""Script to verify z-scores stored in Supabase"""
import os
from supabase import create_client, Client
from datetime import datetime

# Get Supabase credentials from environment or use provided ones
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://fzuxkphassgtvfiupixv.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPNhaXm4hyT8f2und08U")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Supabase credentials not found!")
    exit(1)

print(f"🔗 Connecting to Supabase: {SUPABASE_URL}")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check today's date
date_str = datetime.now().strftime("%Y-%m-%d")
print(f"📅 Checking data for date: {date_str}\n")

# Check stock_data table for z_scored stage
print("=" * 60)
print("CHECKING stock_data TABLE FOR z_scored STAGE")
print("=" * 60)
try:
    result = supabase.table("stock_data").select("ticker, stage, date_str, updated_at").eq("stage", "z_scored").eq("date_str", date_str).execute()
    
    if result.data:
        print(f"✅ Found {len(result.data)} z-scored stocks in stock_data table:")
        print(f"\nFirst 10 records:")
        for i, record in enumerate(result.data[:10], 1):
            print(f"  {i}. {record.get('ticker')} - Updated: {record.get('updated_at')}")
        
        if len(result.data) > 10:
            print(f"  ... and {len(result.data) - 10} more")
        
        # Check a sample record's data structure
        if result.data:
            sample = supabase.table("stock_data").select("*").eq("ticker", result.data[0].get("ticker")).eq("stage", "z_scored").eq("date_str", date_str).execute()
            if sample.data:
                data_sample = sample.data[0].get("data", {})
                print(f"\n📊 Sample data structure for {result.data[0].get('ticker')}:")
                print(f"   Keys: {list(data_sample.keys()) if isinstance(data_sample, dict) else 'Not a dict'}")
                if isinstance(data_sample, dict):
                    print(f"   z_avg: {data_sample.get('z_avg', 'N/A')}")
                    print(f"   avg_score: {data_sample.get('avg_score', 'N/A')}")
    else:
        print("❌ No z-scored stocks found in stock_data table")
except Exception as e:
    print(f"❌ Error querying stock_data table: {e}")
    import traceback
    traceback.print_exc()

# Check all stages in stock_data
print("\n" + "=" * 60)
print("CHECKING ALL STAGES IN stock_data TABLE")
print("=" * 60)
try:
    result = supabase.table("stock_data").select("stage").execute()
    if result.data:
        stages = {}
        for record in result.data:
            stage = record.get("stage", "unknown")
            stages[stage] = stages.get(stage, 0) + 1
        
        print("📊 Stage distribution:")
        for stage, count in sorted(stages.items()):
            print(f"   {stage}: {count} records")
except Exception as e:
    print(f"❌ Error querying stages: {e}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

