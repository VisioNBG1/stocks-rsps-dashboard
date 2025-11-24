"""Script to verify actual progress in Supabase vs checkpoint"""
import os
from supabase import create_client, Client
from datetime import datetime

# Get Supabase credentials
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

# 1. Check downloaded stocks in stock_data table
print("=" * 60)
print("1. DOWNLOADED STOCKS (stock_data table)")
print("=" * 60)
try:
    result = supabase.table("stock_data").select("ticker").eq("stage", "downloaded").eq("date_str", date_str).execute()
    if result.data:
        downloaded_tickers = list(set([r.get("ticker") for r in result.data if r.get("ticker")]))
        print(f"✅ Found {len(downloaded_tickers)} downloaded stocks in stock_data table")
        print(f"   Sample: {', '.join(sorted(downloaded_tickers)[:10])}{'...' if len(downloaded_tickers) > 10 else ''}")
    else:
        print("❌ No downloaded stocks found in stock_data table")
        downloaded_tickers = []
except Exception as e:
    print(f"❌ Error querying stock_data: {e}")
    downloaded_tickers = []

# 2. Check z-scored stocks in z_scores table
print("\n" + "=" * 60)
print("2. Z-SCORED STOCKS (z_scores table)")
print("=" * 60)
try:
    result = supabase.table("z_scores").select("ticker").eq("date_str", date_str).execute()
    if result.data:
        z_scored_tickers = list(set([r.get("ticker") for r in result.data if r.get("ticker")]))
        print(f"✅ Found {len(z_scored_tickers)} z-scored stocks in z_scores table")
        print(f"   Sample: {', '.join(sorted(z_scored_tickers)[:10])}{'...' if len(z_scored_tickers) > 10 else ''}")
    else:
        print("❌ No z-scored stocks found in z_scores table")
        z_scored_tickers = []
except Exception as e:
    print(f"❌ Error querying z_scores: {e}")
    z_scored_tickers = []

# 3. Check checkpoint
print("\n" + "=" * 60)
print("3. CHECKPOINT (checkpoints table)")
print("=" * 60)
try:
    checkpoint_id = f"main_checkpoint_{date_str}"
    result = supabase.table("checkpoints").select("*").eq("id", checkpoint_id).execute()
    if result.data and len(result.data) > 0:
        checkpoint = result.data[0]
        stage = checkpoint.get("stage", "unknown")
        is_partial = checkpoint.get("is_partial", False)
        data = checkpoint.get("data", {})
        
        print(f"✅ Checkpoint found: stage={stage}, is_partial={is_partial}")
        
        # Parse checkpoint data
        if isinstance(data, str):
            import json
            try:
                data = json.loads(data)
            except:
                pass
        
        checkpoint_downloaded = data.get("downloaded_stocks", []) if isinstance(data, dict) else []
        if isinstance(checkpoint_downloaded, list):
            print(f"   Checkpoint says {len(checkpoint_downloaded)} downloaded stocks")
            print(f"   Sample: {', '.join(sorted(checkpoint_downloaded)[:10])}{'...' if len(checkpoint_downloaded) > 10 else ''}")
        else:
            print(f"   ⚠ Checkpoint downloaded_stocks is not a list: {type(checkpoint_downloaded)}")
            checkpoint_downloaded = []
    else:
        print("❌ No checkpoint found")
        checkpoint_downloaded = []
except Exception as e:
    print(f"❌ Error querying checkpoint: {e}")
    import traceback
    traceback.print_exc()
    checkpoint_downloaded = []

# 4. Compare
print("\n" + "=" * 60)
print("4. COMPARISON")
print("=" * 60)
print(f"   Downloaded in Supabase: {len(downloaded_tickers)}")
print(f"   Downloaded in checkpoint: {len(checkpoint_downloaded)}")
print(f"   Z-scored in Supabase: {len(z_scored_tickers)}")

if len(downloaded_tickers) != len(checkpoint_downloaded):
    print(f"\n⚠️  MISMATCH: Supabase has {len(downloaded_tickers)} stocks but checkpoint says {len(checkpoint_downloaded)}")
    
    # Find missing in checkpoint
    supabase_set = set(downloaded_tickers)
    checkpoint_set = set(checkpoint_downloaded)
    missing_in_checkpoint = supabase_set - checkpoint_set
    extra_in_checkpoint = checkpoint_set - supabase_set
    
    if missing_in_checkpoint:
        print(f"   Missing in checkpoint ({len(missing_in_checkpoint)}): {', '.join(sorted(list(missing_in_checkpoint))[:20])}{'...' if len(missing_in_checkpoint) > 20 else ''}")
    if extra_in_checkpoint:
        print(f"   Extra in checkpoint ({len(extra_in_checkpoint)}): {', '.join(sorted(list(extra_in_checkpoint))[:20])}{'...' if len(extra_in_checkpoint) > 20 else ''}")
else:
    print("✅ Checkpoint matches Supabase for downloaded stocks")

# 5. Stocks that are downloaded but not z-scored
print("\n" + "=" * 60)
print("5. STOCKS DOWNLOADED BUT NOT Z-SCORED")
print("=" * 60)
downloaded_set = set(downloaded_tickers)
z_scored_set = set(z_scored_tickers)
not_z_scored = downloaded_set - z_scored_set
print(f"   {len(not_z_scored)} stocks downloaded but not yet z-scored")
if not_z_scored:
    print(f"   Sample: {', '.join(sorted(list(not_z_scored))[:20])}{'...' if len(not_z_scored) > 20 else ''}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

