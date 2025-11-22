# Deploy to Render

This guide will help you deploy your Stocks RSPS System Dashboard to Render.

## Option 1: Deploy via Render Dashboard (Recommended for first-time)

1. **Push your code to GitHub:**
   ```bash
   cd "RSPS Stocks System Dashboard"
   git init
   git add .
   git commit -m "Initial commit - Stocks RSPS Dashboard"
   git branch -M main
   git remote add origin <YOUR_GITHUB_REPO_URL>
   git push -u origin main
   ```

2. **Deploy on Render:**
   - Go to https://dashboard.render.com
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Render will auto-detect the settings:
     - **Name:** stocks-rsps-dashboard
     - **Environment:** Python 3
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `gunicorn stock_dashboard_backend:app`
   - Click "Create Web Service"

3. **Your dashboard will be live at:** `https://stocks-rsps-dashboard.onrender.com`

## Option 2: Deploy via Render MCP Server (Using AI)

If you have the Render MCP server configured in Cursor/Claude:

1. **Set your workspace:**
   ```
   Set my Render workspace to [YOUR_WORKSPACE_NAME]
   ```

2. **Create the service:**
   ```
   Deploy a Flask web service on Render using this repository: [YOUR_GITHUB_REPO_URL]
   Name it: stocks-rsps-dashboard
   Use Python 3.11
   Build command: pip install -r requirements.txt
   Start command: gunicorn stock_dashboard_backend:app
   ```

## Important Notes

- **First deployment takes 5-10 minutes** (building dependencies)
- **Free tier services spin down after 15 minutes of inactivity** - first request after spin-down takes ~30 seconds
- **Upgrade to paid plan** for always-on service
- The dashboard will automatically use the correct API URL (no configuration needed)

## Files Created for Deployment

- `render.yaml` - Render configuration file
- `Procfile` - Alternative deployment config
- `.gitignore` - Excludes cache files from git
- Updated `requirements.txt` - Added gunicorn for production
- Updated `stock_dashboard_backend.py` - Uses PORT environment variable
- Updated `dashboard.html` - Uses dynamic API URL

## Troubleshooting

If deployment fails:
1. Check Render logs for errors
2. Ensure all dependencies are in `requirements.txt`
3. Verify `gunicorn` is installed (included in requirements.txt)
4. Check that `dashboard.html` is in the root directory

