# How to Find Your Render Service ID

## Method 1: From Service URL (Easiest)

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your **Web Service** (`rsps-stocks-dashboard` or similar)
3. Look at the URL in your browser address bar
4. The URL will look like:
   ```
   https://dashboard.render.com/web/[SERVICE_ID]
   ```
5. The **SERVICE_ID** is the long string after `/web/`

**Example:**
- URL: `https://dashboard.render.com/web/srv-abc123xyz456`
- Service ID: `srv-abc123xyz456`

## Method 2: From Service Settings

1. Go to your Web Service in Render
2. Click **"Settings"** tab (left sidebar)
3. Scroll down to **"Service Details"** section
4. Look for **"Service ID"** - it will be displayed there
5. Copy it (it starts with `srv-`)

## Method 3: From API (If you have API key)

You can also list all your services using the API:

```bash
curl -H "Authorization: Bearer rnd_qksXBIROU0aXmKN8HZjym8SqUjh4" \
     https://api.render.com/v1/services
```

This will return a list of all your services with their IDs.

## Method 4: Quick Check

1. Go to your service
2. Look at the **"Events"** tab
3. Click on any recent deploy
4. The Service ID might be visible in the deploy details

## What It Looks Like

Service IDs typically look like:
- `srv-abc123def456ghi789`
- `srv-2abc3def4ghi5jkl6`
- Usually starts with `srv-` followed by alphanumeric characters

## Once You Have It

Add to Render Environment Variables:
- **Key**: `RENDER_SERVICE_ID`
- **Value**: Your service ID (e.g., `srv-abc123def456`)

