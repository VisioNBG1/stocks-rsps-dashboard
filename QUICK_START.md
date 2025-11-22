# Quick Start Guide

## Step-by-Step Instructions

### Option 1: Using the Batch File (Easiest - Windows)

1. **Double-click** `START_DASHBOARD.bat` in your file explorer
   - Location: `C:\Users\USER\START_DASHBOARD.bat`
   - This will automatically install dependencies and start the server

### Option 2: Using Command Prompt/PowerShell (Manual)

1. **Open Command Prompt or PowerShell:**
   - Press `Windows Key + R`
   - Type `cmd` or `powershell` and press Enter
   - OR right-click the Start button and select "Windows PowerShell" or "Command Prompt"

2. **Navigate to the project folder:**
   ```bash
   cd C:\Users\USER
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   python stock_dashboard_backend.py
   ```

5. **Open the dashboard:**
   - After the server starts (you'll see "Running on http://0.0.0.0:5000")
   - Open `dashboard.html` in your web browser
   - You can find it at: `C:\Users\USER\dashboard.html`
   - Or double-click `dashboard.html` in File Explorer

## What You'll See

1. **In the Terminal:**
   - Installation progress for Python packages
   - Server startup messages
   - Analysis progress as stocks are processed
   - "Running on http://0.0.0.0:5000" when ready

2. **In the Browser:**
   - A beautiful dashboard showing:
     - Sectors ranked by trending strength
     - Individual stocks within each sector
     - Color-coded z-scores

## Troubleshooting

- **"python is not recognized"**: 
  - Install Python from python.org
  - Or try `py` instead of `python`: `py stock_dashboard_backend.py`

- **"pip is not recognized"**:
  - Make sure Python is installed and added to PATH
  - Or use: `py -m pip install -r requirements.txt`

- **Port 5000 already in use**:
  - Close other applications using port 5000
  - Or modify the port in `stock_dashboard_backend.py` (line 449)

- **Dashboard shows "Error loading data"**:
  - Make sure the server is running
  - Check that you see "Running on http://0.0.0.0:5000" in the terminal

## Stopping the Server

- Press `Ctrl + C` in the terminal window
- Or close the terminal window

