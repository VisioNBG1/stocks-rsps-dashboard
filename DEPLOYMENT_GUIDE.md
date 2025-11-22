# Render Free Plan Deployment Guide

This dashboard is configured to work with Render's **free plan** using a checkpoint system that saves progress every 14 minutes and automatically resumes on the next deployment.

## How It Works

1. **14-Minute Checkpoint System**: The analysis automatically saves progress at 14 minutes (840 seconds) before Render's 15-minute timeout
2. **Automatic Resume**: On the next deployment, the system automatically resumes from the last checkpoint
3. **Full Stock List**: Includes 300+ stocks across all sectors

## Deployment Steps

### 1. Push to GitHub

```bash
cd "RSPS Stocks System Dashboard Render"
git init
git add .
git commit -m "Initial commit - Render deployment with checkpoint system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

### 2. Deploy on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository: `YOUR_REPO_NAME`
5. Configure:
   - **Name**: `rsps-stocks-dashboard`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn stock_dashboard_backend:app --bind 0.0.0.0:$PORT --workers 1 --timeout 900 --keep-alive 2`
   - **Plan**: **Free**

6. Click **"Create Web Service"**

### 3. Auto-Deployment

- Render will automatically deploy when you push to GitHub
- The `render.yaml` file is configured for auto-deployment
- Each deployment will resume from the last checkpoint

## How the Checkpoint System Works

### Checkpoint Stages

1. **Downloading**: Saves progress every 5 stocks downloaded
2. **Stock Analysis**: Saves checkpoint at 14 minutes, and every 10 stocks processed
3. **Ratio Analysis**: Saves checkpoint before starting
4. **Backtesting**: Saves checkpoint before starting

### Resume Logic

- On startup, the system checks for a checkpoint file
- If found, it resumes from the last completed stage
- Already processed stocks are skipped
- The process continues until complete

### Expected Timeline

With 300+ stocks:
- **First deployment**: Downloads stocks (may timeout, saves checkpoint)
- **Second deployment**: Resumes downloads, starts analysis (may timeout, saves checkpoint)
- **Subsequent deployments**: Continue analysis, ratio analysis, backtesting
- **Final deployment**: Completes and returns results

## Monitoring Progress

1. Check Render logs to see checkpoint saves
2. Look for messages like:
   - `⚠ TIMEOUT APPROACHING: 840.0s elapsed`
   - `💾 Saving checkpoint at stage: stock_analysis`
   - `✓ Checkpoint saved successfully. Exiting gracefully...`
   - `🔄 Next deployment will resume from: stock_analysis`

## Cache Location

- Cache files are saved to `/tmp/analysis_cache.json` (Render free plan)
- Stock data cache: `/tmp/stock_data_cache/` directory
- These persist between deployments on Render

## Troubleshooting

### If deployment keeps timing out:
- Check Render logs for checkpoint saves
- Verify cache is being saved (look for "Cache saved" messages)
- Ensure `render.yaml` has correct timeout settings

### If analysis doesn't resume:
- Check if checkpoint file exists in logs
- Verify `_partial: true` flag in cache
- Check `_stage` field to see which stage to resume from

### To force fresh start:
- Delete the cache file or set `force_refresh=True` in the code
- Or manually delete cache in Render shell

## Notes

- **Free Plan Limitations**: 15-minute timeout, 512MB RAM
- **Checkpoint Frequency**: Every 14 minutes + every 10 stocks during analysis
- **Auto-Restart**: Render auto-deploys on GitHub push, which triggers resume
- **Total Time**: May take 10-20 deployments to complete full analysis with 300+ stocks

## Manual Restart

If needed, you can manually trigger a new deployment:
1. Go to Render dashboard
2. Click on your service
3. Click **"Manual Deploy"** → **"Deploy latest commit"**

This will trigger a new deployment that resumes from the checkpoint.

