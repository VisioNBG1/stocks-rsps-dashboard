# Supabase Setup Guide for Checkpoint Persistence

## Why Supabase?

Render's free plan has **ephemeral storage** - files are lost when containers restart. Supabase provides a **free PostgreSQL database** that persists checkpoints across deployments.

## Step 1: Create Supabase Account

1. Go to [https://supabase.com](https://supabase.com)
2. Click **"Start your project"** (free)
3. Sign up with GitHub (recommended) or email
4. Create a new project:
   - **Name**: `rsps-stocks-checkpoints` (or any name)
   - **Database Password**: Choose a strong password (save it!)
   - **Region**: Choose closest to you
   - Click **"Create new project"**
   - Wait 2-3 minutes for setup

## Step 2: Create Checkpoints Table

1. In your Supabase project, go to **"SQL Editor"** (left sidebar)
2. Click **"New query"**
3. Paste this SQL:

```sql
-- Create checkpoints table
CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    data JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    stage TEXT,
    is_partial BOOLEAN DEFAULT false
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_checkpoints_id ON checkpoints(id);

-- Grant access (if needed)
ALTER TABLE checkpoints ENABLE ROW LEVEL SECURITY;
```

4. Click **"Run"** (or press Ctrl+Enter)
5. You should see "Success. No rows returned"

## Step 3: Get API Credentials

1. In Supabase dashboard, go to **"Settings"** (gear icon, bottom left)
2. Click **"API"** in the settings menu
3. You'll see:
   - **Project URL**: Copy this (looks like `https://xxxxx.supabase.co`)
   - **anon/public key**: Copy this (long string starting with `eyJ...`)

## Step 4: Add to Render Environment Variables

1. Go to your Render dashboard
2. Select your **Web Service** (`rsps-stocks-dashboard`)
3. Go to **"Environment"** tab
4. Click **"Add Environment Variable"**
5. Add these two variables:

   **Variable 1:**
   - **Key**: `SUPABASE_URL`
   - **Value**: Your Project URL (from Step 3)
   - Example: `https://abcdefghijklmnop.supabase.co`

   **Variable 2:**
   - **Key**: `SUPABASE_KEY`
   - **Value**: Your anon/public key (from Step 3)
   - Example: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

6. Click **"Save Changes"**
7. Render will automatically redeploy

## Step 5: Verify It Works

1. After redeploy, check Render logs
2. Look for: `✓ Supabase client initialized for checkpoint storage`
3. When checkpoint saves, you should see: `✓ Checkpoint saved to Supabase database`
4. On next deployment, you should see: `✓ Checkpoint loaded from Supabase`

## Troubleshooting

### "Supabase credentials not found"
- Check environment variables are set correctly in Render
- Make sure variable names are exactly: `SUPABASE_URL` and `SUPABASE_KEY`
- Redeploy after adding variables

### "Failed to initialize Supabase"
- Verify your Project URL is correct (should start with `https://`)
- Verify your API key is the **anon/public** key (not service_role)
- Check Supabase project is active (not paused)

### "Failed to save checkpoint to Supabase"
- Check the table was created correctly (go to Table Editor in Supabase)
- Verify RLS (Row Level Security) is configured correctly
- Check Supabase project hasn't exceeded free tier limits

### Table doesn't exist
- Go to SQL Editor in Supabase
- Run the CREATE TABLE command again
- Check "Table Editor" to verify table exists

## Free Tier Limits

Supabase free tier includes:
- ✅ 500 MB database storage
- ✅ 2 GB bandwidth/month
- ✅ Unlimited API requests
- ✅ Perfect for checkpoint storage!

## Security Notes

- The **anon/public key** is safe to use in frontend/backend
- It has limited permissions (only what you configure)
- Never commit your API keys to git (use environment variables)
- The checkpoint data is stored encrypted in Supabase

## Next Steps

Once set up:
1. ✅ Checkpoints will persist across deployments
2. ✅ No more lost progress on Render restarts
3. ✅ Automatic resume from last checkpoint
4. ✅ Works with Render free plan!

## Support

If you have issues:
1. Check Supabase dashboard → Logs
2. Check Render logs for error messages
3. Verify environment variables are set
4. Test Supabase connection in SQL Editor

