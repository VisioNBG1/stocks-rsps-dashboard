# Install Git and Push to GitHub

## Option 1: Install Git for Windows (Recommended)

1. **Download Git:**
   - Go to: https://git-scm.com/download/win
   - Download the installer (it will auto-detect 64-bit or 32-bit)

2. **Install Git:**
   - Run the installer
   - Use default settings (just click Next)
   - **Important:** Make sure "Git from the command line and also from 3rd-party software" is selected

3. **Restart PowerShell/Command Prompt** after installation

4. **Then run these commands:**
   ```powershell
   cd "C:\Users\USER\RSPS Stocks System Dashboard"
   git init
   git add .
   git commit -m "Initial commit - Stocks RSPS Dashboard"
   git branch -M main
   git remote add origin https://github.com/VisioNBG1/stocks-rsps-dashboard.git
   git push -u origin main
   ```

## Option 2: Use GitHub Desktop (If you have it)

1. Open GitHub Desktop
2. File → Add Local Repository
3. Browse to: `C:\Users\USER\RSPS Stocks System Dashboard`
4. Click "Create a Repository" if needed
5. In the bottom panel, write commit message: "Initial commit - Stocks RSPS Dashboard"
6. Click "Commit to main"
7. Click "Publish repository" (top right)
8. Make sure the remote is: `https://github.com/VisioNBG1/stocks-rsps-dashboard.git`
9. Click "Publish repository"

## Option 3: Manual Upload via GitHub Web (Temporary Solution)

If you can't install Git right now:
1. Go to: https://github.com/VisioNBG1/stocks-rsps-dashboard
2. Click "uploading an existing file"
3. Drag and drop all files from `C:\Users\USER\RSPS Stocks System Dashboard`
4. Commit the files

**Note:** This method is tedious but works if you need a quick solution.

---

## After Pushing to GitHub

Once your code is on GitHub, I can help you deploy to Render using the MCP server!

