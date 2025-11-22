# RSPS Stocks System Dashboard - Render Deployment Version

This is the **Render deployment version** with checkpoint system for free plan deployment.

## Features

- ✅ **Full Stock List**: 300+ stocks across all sectors
- ✅ **14-Minute Checkpoint System**: Automatically saves progress before timeout
- ✅ **Auto-Resume**: Automatically resumes from last checkpoint on next deployment
- ✅ **Render Free Plan Compatible**: Works within 15-minute timeout limit

## Quick Start

1. **Push to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Deploy on Render**:
   - Connect GitHub repo
   - Use `render.yaml` for auto-configuration
   - Plan: **Free**

3. **Monitor Progress**:
   - Check Render logs for checkpoint saves
   - Each deployment resumes from last checkpoint
   - May take 10-20 deployments to complete full analysis

## Checkpoint System

The system automatically:
- Saves checkpoint at **14 minutes** (before 15-minute timeout)
- Saves checkpoint every **10 stocks** during analysis
- Saves checkpoint every **5 stocks** during download
- Resumes automatically on next deployment

## Files

- `stock_dashboard_backend.py` - Main application with checkpoint logic
- `render.yaml` - Render deployment configuration
- `DEPLOYMENT_GUIDE.md` - Detailed deployment instructions
- `dashboard.html` - Frontend dashboard

## Differences from Main Version

- Full SECTORS list (300+ stocks) restored
- Checkpoint system implemented
- Timeout monitoring at 14 minutes
- Auto-resume from checkpoints
- Optimized for Render free plan

## Support

See `DEPLOYMENT_GUIDE.md` for detailed instructions and troubleshooting.
