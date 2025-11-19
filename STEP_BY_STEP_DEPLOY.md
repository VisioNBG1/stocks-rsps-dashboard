# Step-by-Step Deployment Guide

## Step 1: Configure Render MCP Server in Cursor ✅

**Location:** `C:\Users\USER\AppData\Roaming\Cursor\User\mcp.json`

**Create or edit this file with this content:**
```json
{
  "mcpServers": {
    "render": {
      "url": "https://mcp.render.com/mcp",
      "headers": {
        "Authorization": "Bearer rnd_XhTbbOQGqZwGJvVzfelNxdCogIy7"
      }
    }
  }
}
```

**To verify:**
1. Open File Explorer
2. Navigate to: `C:\Users\USER\AppData\Roaming\Cursor\User\`
3. Check if `mcp.json` exists and contains the above JSON
4. **Restart Cursor** after creating/editing the file

---

## Step 2: Initialize Git Repository

**Where to run these commands:** Open PowerShell or Command Prompt and navigate to your project folder.

**Commands to run:**
```powershell
# Navigate to your project directory
cd "C:\Users\USER\RSPS Stocks System Dashboard"

# Initialize git repository
git init

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit - Stocks RSPS Dashboard"

# Rename branch to main (if needed)
git branch -M main
```

**Next:** Push to GitHub
1. Create a new repository on GitHub (https://github.com/new)
2. Copy the repository URL (e.g., `https://github.com/yourusername/stocks-rsps-dashboard.git`)
3. Run these commands:
```powershell
git remote add origin https://github.com/yourusername/stocks-rsps-dashboard.git
git push -u origin main
```

---

## Step 3: Deploy to Render

### Option A: Using Render Dashboard (Easier)
1. Go to https://dashboard.render.com
2. Sign in with your Render account
3. Click "New +" → "Web Service"
4. Connect your GitHub account
5. Select your repository: `stocks-rsps-dashboard`
6. Render will auto-detect settings:
   - **Name:** stocks-rsps-dashboard
   - **Environment:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn stock_dashboard_backend:app`
7. Click "Create Web Service"
8. Wait 5-10 minutes for first deployment

### Option B: Using MCP Server (After Step 1)
Once MCP is configured and Cursor is restarted, you can ask me:
"Deploy my Flask web service to Render using my GitHub repository: [YOUR_REPO_URL]"

---

## Quick Reference

**Project Directory:**
```
C:\Users\USER\RSPS Stocks System Dashboard
```

**MCP Config Location:**
```
C:\Users\USER\AppData\Roaming\Cursor\User\mcp.json
```

**Git Commands Location:**
Run in PowerShell/CMD from the project directory above.

