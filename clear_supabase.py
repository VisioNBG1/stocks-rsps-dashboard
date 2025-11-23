#!/usr/bin/env python3
"""
Script to clear Supabase checkpoints and optionally stock_data.
Run this to start fresh with the new Supabase structure.

Usage:
    python clear_supabase.py

Make sure to set SUPABASE_URL and SUPABASE_KEY environment variables.
"""

import os
import sys
from supabase import create_client, Client

# Get Supabase credentials from environment
SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
SUPABASE_KEY = os.environ.get('SUPABASE_KEY', '').strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_KEY must be set")
    print("   Set them as environment variables or in your .env file")
    sys.exit(1)

try:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print(f"✓ Connected to Supabase: {SUPABASE_URL}")
except Exception as e:
    print(f"❌ Failed to connect to Supabase: {e}")
    sys.exit(1)

# Clear checkpoints
print("\n🗑️  Clearing checkpoints table...")
try:
    result = supabase_client.table("checkpoints").delete().neq("id", "never_delete").execute()
    print(f"✓ Cleared all checkpoints")
except Exception as e:
    print(f"⚠ Error clearing checkpoints: {e}")

# Optionally clear stock_data (uncomment if you want to start completely fresh)
# print("\n🗑️  Clearing stock_data table...")
# try:
#     result = supabase_client.table("stock_data").delete().neq("ticker", "never_delete").execute()
#     print(f"✓ Cleared all stock_data")
# except Exception as e:
#     print(f"⚠ Error clearing stock_data: {e}")

print("\n✅ Done! Supabase is now cleared and ready for fresh data.")
print("   Next deployment will start downloading stocks from scratch.")

