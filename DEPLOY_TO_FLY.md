# Deploy to Fly.io

Fly.io has a free tier that supports long-running processes and doesn't have the same limitations as Render or Vercel.

## Prerequisites

1. Install Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Sign up for a free account: https://fly.io/app/sign-up

## Deployment Steps

1. **Login to Fly.io:**
   ```bash
   fly auth login
   ```

2. **Initialize your app (if not already done):**
   ```bash
   fly launch
   ```
   - When prompted, say "no" to copying configuration (we already have fly.toml)
   - Choose a region close to you (e.g., `iad` for US East)
   - Don't deploy yet

3. **Deploy:**
   ```bash
   fly deploy
   ```

4. **Open your app:**
   ```bash
   fly open
   ```

## Important Notes

- **Free tier includes:** 3 shared-cpu-1x VMs with 256MB RAM each
- **For this app:** We're using 1 VM with 1GB RAM (may require paid plan)
- **Auto-scaling:** The app will auto-start when accessed
- **No execution time limits:** Unlike Render/Vercel, Fly.io doesn't kill long-running processes

## If you need more resources

The current `fly.toml` uses 1GB RAM. If you need more:
- Upgrade to Fly.io paid plan ($5-10/month)
- Or reduce memory usage in the code

## Troubleshooting

- Check logs: `fly logs`
- SSH into VM: `fly ssh console`
- Scale resources: Edit `fly.toml` and redeploy

