# Fly.io Free Tier Limitations

## Problem: Auto-Stopping Machines

Fly.io's **free tier** will auto-stop machines even with `auto_stop_machines = false` when it detects "excess capacity" (low traffic). This is a hard limitation of the free tier.

## Solutions

### Option 1: Upgrade to Fly.io Paid Plan (Recommended)
- **Cost**: ~$5-10/month
- **Benefits**:
  - Machines won't auto-stop
  - Persistent storage (volumes)
  - Better resource allocation
  - More reliable for long-running processes

**Steps to upgrade:**
1. Go to https://fly.io/dashboard
2. Upgrade to a paid plan
3. Create a persistent volume:
   ```bash
   fly volumes create cache_data --size 1 --region fra
   ```
4. Uncomment the `[[mounts]]` section in `fly.toml`
5. Redeploy: `fly deploy`

### Option 2: Use External Storage (Free)
Use a free external storage service to persist cache:
- **Redis** (Upstash free tier)
- **PostgreSQL** (Supabase free tier)
- **S3-compatible** (Backblaze B2 free tier)

This requires modifying the code to use external storage instead of local files.

### Option 3: Accept the Limitation
- Analysis will restart from beginning if machine stops
- Checkpoint saving helps but cache is lost on restart (ephemeral storage)
- You can manually restart and wait for completion

## Current Status

The code includes:
- ✅ Checkpoint saving (after stock analysis, after ratio analysis)
- ✅ Resume logic (if cache exists)
- ⚠️ Cache is ephemeral on free tier (lost on restart)

## Recommendation

For reliable long-running analysis, **upgrade to Fly.io paid plan** or use a **VPS** (DigitalOcean, Linode) for ~$5/month with full control.

