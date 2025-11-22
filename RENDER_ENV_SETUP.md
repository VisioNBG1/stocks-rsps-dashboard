# Add Supabase Credentials to Render

## Your Supabase Credentials

✅ **Project URL**: `https://fzuxkphassgtvfiupixv.supabase.co`
✅ **API Key (anon)**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPnhaXm4hyT8f2und08U`

## Steps to Add to Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your **Web Service** (`rsps-stocks-dashboard` or similar)
3. Go to **"Environment"** tab (left sidebar)
4. Click **"Add Environment Variable"** button

### Add First Variable:
- **Key**: `SUPABASE_URL`
- **Value**: `https://fzuxkphassgtvfiupixv.supabase.co`
- Click **"Save"**

### Add Second Variable:
- **Key**: `SUPABASE_KEY`
- **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPnhaXm4hyT8f2und08U`
- Click **"Save"**

5. Render will automatically **redeploy** your service
6. Check the logs to verify:
   - Look for: `✓ Supabase client initialized for checkpoint storage`

## Verify It's Working

After redeploy, check Render logs for:
- ✅ `✓ Supabase client initialized for checkpoint storage`
- ✅ When checkpoint saves: `✓ Checkpoint saved to Supabase database`
- ✅ On next deployment: `✓ Checkpoint loaded from Supabase`

## Troubleshooting

If you see:
- `⚠ Supabase credentials not found` → Check environment variables are saved
- `⚠ Failed to initialize Supabase` → Verify URL and key are correct
- `⚠ Failed to save checkpoint` → Check table exists in Supabase

