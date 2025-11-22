# Auto-Redeploy Setup (Optional)

## Current Status

✅ **Checkpoints are saving to Supabase** - This is working!
⚠️ **Auto-redeploy requires manual trigger** - You need to click "Manual Deploy" in Render

## Option 1: Manual Redeploy (Current - Works Now)

After checkpoint saves:
1. Go to Render Dashboard
2. Click your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**
4. System will automatically resume from Supabase checkpoint

## Option 2: Auto-Redeploy via Render API (Optional)

To enable automatic redeploy after checkpoint saves:

### Step 1: Get Render API Key

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click your profile (top right) → **"Account Settings"**
3. Go to **"API Keys"** section
4. Click **"Create API Key"**
5. Name it: `auto-redeploy-key`
6. **Copy the key** (you'll only see it once!)

### Step 2: Get Service ID

1. Go to your Web Service in Render
2. Look at the URL: `https://dashboard.render.com/web/[SERVICE_ID]`
3. Or go to **"Settings"** → **"Service Details"** → Copy the **Service ID**

### Step 3: Add to Render Environment Variables

1. Go to your service → **"Environment"** tab
2. Add these variables:

   **Variable 1:**
   - **Key**: `RENDER_API_KEY`
   - **Value**: Your API key from Step 1

   **Variable 2:**
   - **Key**: `RENDER_SERVICE_ID`
   - **Value**: Your service ID from Step 2

3. Click **"Save Changes"**
4. **Manually redeploy** once (to load the new variables)

### Step 4: Verify

After next checkpoint save, you should see in logs:
```
✅ Auto-redeploy triggered via Render API (Deploy ID: xxxxx)
🔄 Render will redeploy automatically in a few moments...
```

## Important Notes

- **Manual redeploy works fine** - Auto-redeploy is optional
- **Checkpoints are already persistent** in Supabase
- **Auto-redeploy just saves you a click** - not required for functionality
- **API key is sensitive** - Don't commit it to git (use environment variables)

## Current Behavior

Without API key:
- ✅ Checkpoint saves to Supabase
- ✅ Manual redeploy resumes from checkpoint
- ⚠️ You need to click "Manual Deploy"

With API key:
- ✅ Checkpoint saves to Supabase
- ✅ Auto-redeploy triggers automatically
- ✅ System resumes without manual intervention

## Recommendation

**For now, manual redeploy is fine!** The checkpoint system is working perfectly with Supabase. Auto-redeploy is just a convenience feature.

