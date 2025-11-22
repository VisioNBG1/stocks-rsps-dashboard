# Quick Deploy to Render - Step by Step

Your code is already on GitHub: `https://github.com/VisioNBG1/stocks-rsps-dashboard.git`

## Deployment Steps:

1. **Go to Render Dashboard:**
   - Visit: https://dashboard.render.com
   - Sign in with your GitHub account (recommended) or email

2. **Create New Web Service:**
   - Click the **"New +"** button (top right)
   - Select **"Web Service"**

3. **Connect Repository:**
   - If not connected, click **"Connect account"** to link your GitHub
   - Select repository: **`VisioNBG1/stocks-rsps-dashboard`**
   - Click **"Connect"**

4. **Configure Service:**
   - **Name:** `stocks-rsps-dashboard` (or your preferred name)
   - **Environment:** `Python 3`
   - **Region:** Choose closest to you
   - **Branch:** `main`
   - **Root Directory:** (leave empty - files are in root)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn stock_dashboard_backend:app`

5. **Create Service:**
   - Click **"Create Web Service"**
   - Wait 5-10 minutes for first build

6. **Access Your Dashboard:**
   - Once deployed, your dashboard will be at:
   - `https://stocks-rsps-dashboard.onrender.com` (or your custom name)
   - The dashboard will automatically use the correct API URL

## Important Notes:

- ✅ All files are ready (render.yaml, Procfile, requirements.txt)
- ✅ Backend is configured to use PORT environment variable
- ✅ Frontend uses dynamic API URL detection
- ⚠️ Free tier services spin down after 15 min inactivity (first request takes ~30 sec)
- 💰 Upgrade to paid plan for always-on service

## Troubleshooting:

If build fails:
- Check the "Logs" tab in Render dashboard
- Verify all dependencies are in `requirements.txt`
- Ensure `gunicorn` is installed (it's in requirements.txt)

