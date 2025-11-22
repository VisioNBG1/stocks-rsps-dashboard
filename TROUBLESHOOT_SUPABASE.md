# Troubleshooting Supabase Connection

## Problem: Environment Variables Not Detected

If you see in logs:
```
⚠ Supabase credentials not found in environment variables
```

## Solution Steps

### Step 1: Verify Environment Variables in Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click your **Web Service** (`rsps-stocks-dashboard`)
3. Click **"Environment"** tab (left sidebar)
4. **Verify these exact variables exist:**

   ✅ `SUPABASE_URL` = `https://fzuxkphassgtvfiupixv.supabase.co`
   ✅ `SUPABASE_KEY` = `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPnhaXm4hyT8f2und08U`

### Step 2: If Variables Don't Exist - Add Them

1. Click **"Add Environment Variable"**
2. **First Variable:**
   - **Key**: `SUPABASE_URL` (exactly this, case-sensitive)
   - **Value**: `https://fzuxkphassgtvfiupixv.supabase.co`
   - Click **"Save Changes"**
3. **Second Variable:**
   - **Key**: `SUPABASE_KEY` (exactly this, case-sensitive)
   - **Value**: `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ6dXhrcGhhc3NndHZmaXVwaXh2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM4NDY4NjMsImV4cCI6MjA3OTQyMjg2M30.gt4vbdRtXy-m9w2UCLfPQ86MPnhaXm4hyT8f2und08U`
   - Click **"Save Changes"**

### Step 3: Manual Redeploy

After adding/saving variables:
1. Go to **"Events"** tab
2. Click **"Manual Deploy"** → **"Deploy latest commit"**
3. This ensures the new environment variables are loaded

### Step 4: Verify in Logs

After redeploy, check logs for:
- ✅ `✓ Supabase client initialized for checkpoint storage`
- ❌ NOT: `⚠ Supabase credentials not found`

## Common Issues

### Issue 1: Variables Not Saved
- Make sure you click **"Save Changes"** after adding each variable
- Don't just type and close the tab

### Issue 2: Wrong Variable Names
- Must be exactly: `SUPABASE_URL` and `SUPABASE_KEY`
- Case-sensitive, no spaces, no typos

### Issue 3: Variables Added But Not Loaded
- **Solution**: Manual redeploy after adding variables
- Render auto-redeploys on code changes, but environment variable changes need manual redeploy

### Issue 4: Typo in Values
- Double-check the URL: `https://fzuxkphassgtvfiupixv.supabase.co`
- Double-check the key starts with `eyJ...`

## Quick Test

After setting variables and redeploying, you should see in logs:
```
✓ Supabase client initialized for checkpoint storage
```

If you still see the warning, the variables aren't being detected. Check:
1. Variable names are exact (case-sensitive)
2. Values are correct (no extra spaces)
3. You clicked "Save Changes"
4. You manually redeployed after saving

