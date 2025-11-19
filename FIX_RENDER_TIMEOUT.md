# Fix Render Timeout Issue

## Problem
Render is using old settings and timing out after 30 seconds. The `/analyze` endpoint needs 3-5 minutes to complete.

## Solution: Update Settings in Render Dashboard

Since Render might be using manual dashboard settings instead of files, update them manually:

### Steps:

1. **Go to Render Dashboard:**
   - https://dashboard.render.com
   - Click on your `stocks-rsps-dashboard` service

2. **Go to Settings Tab:**
   - Scroll down to "Start Command"

3. **Update Start Command:**
   Replace with:
   ```
   gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 600 --graceful-timeout 600 --keep-alive 5 stock_dashboard_backend:app
   ```

4. **Save Changes:**
   - Click "Save Changes"
   - Render will automatically redeploy

5. **Wait for Redeployment:**
   - Check the "Logs" tab
   - You should see: `Starting gunicorn` with the new command
   - Wait 2-3 minutes for deployment

## Why This Works:

- `--timeout 600`: Allows 10 minutes for requests (backtest takes 3-5 min)
- `--graceful-timeout 600`: Gives workers time to finish gracefully
- `--workers 1`: Reduces memory usage (free tier has limited RAM)
- `--keep-alive 5`: Keeps connections alive

## Alternative: Delete and Recreate

If manual update doesn't work:
1. Delete the current service
2. Create a new Web Service
3. Connect the same GitHub repo
4. Use the Start Command above
5. Render will use the Procfile automatically

