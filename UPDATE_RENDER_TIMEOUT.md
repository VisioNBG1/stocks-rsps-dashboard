# Update Render Timeout Settings

## Important: Manual Update Required

Render's dashboard settings override the configuration files. You need to manually update the timeout in the Render dashboard.

## Steps to Update Timeout:

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your service: **stocks-rsps-dashboard**
3. Go to **Settings** tab
4. Scroll down to **Start Command**
5. Update the command to:
   ```
   gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 900 --graceful-timeout 900 --keep-alive 5 stock_dashboard_backend:app
   ```
6. Click **Save Changes**
7. Render will automatically redeploy with the new settings

## Why This is Needed:

- The files (`render.yaml`, `Procfile`) have been updated to use 900 seconds (15 minutes)
- But Render's dashboard settings take precedence
- The current timeout (600 seconds = 10 minutes) is too short for:
  - 60 second initial delay
  - 15 second delays between 11 stock downloads
  - Stock analysis processing
  - Ratio analysis (110 comparisons)

## Expected Total Time:

- Initial delay: 60s
- Downloads: 11 stocks × 15s = 165s
- Processing: ~3-5 minutes
- **Total: ~6-8 minutes** (should complete within 15 minute timeout)

