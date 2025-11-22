# Important: Cache Persistence on Render Free Plan

## The Problem

Render's **free plan** has **ephemeral storage** - files are lost when the container restarts. This means:
- Cache files in `/tmp` are **lost** on restart
- Cache files in app directory may also be lost
- Checkpoints won't persist between deployments automatically

## Current Solution

The code now:
1. ✅ Saves cache to `.cache/` directory (in app directory) - more persistent than `/tmp`
2. ✅ Tries multiple cache locations on load
3. ⚠️ **Still may not persist** on free plan due to ephemeral storage

## Better Solutions

### Option 1: Use Render Disk (Paid Plan)
- Upgrade to a paid plan with persistent disk
- Mount disk at `/data`
- Cache will persist automatically

### Option 2: Use External Database (Free)
- Use a free database service (Supabase, MongoDB Atlas free tier)
- Store checkpoint data in database
- Persists across deployments

### Option 3: Commit Checkpoint to Git
- Save checkpoint to a file in the repo
- Commit and push it
- Next deployment loads from git
- **Requires manual commit** (can't auto-commit from Render)

### Option 4: Use Render Environment Variables
- Store small checkpoint data in environment variables
- Limited size, but persists

## Current Workaround

For now, the system will:
1. Save checkpoint before timeout
2. Log checkpoint location
3. **You need to manually redeploy** to continue
4. On next deployment, it will try to load cache from multiple locations

## Recommendation

For production use with 300+ stocks:
- **Upgrade to Render paid plan** with persistent disk, OR
- **Use external database** to store checkpoints

The checkpoint system works, but **cache persistence requires paid plan or external storage**.

