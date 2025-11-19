# Troubleshooting Guide

## Error: HTTP error! status: 500

This means the server is running but encountered an error processing your request. Here's how to fix it:

### Step 1: Check the Server Terminal

Look at the terminal window where you ran `START_DASHBOARD.bat` or `py stock_dashboard_backend.py`. You should see error messages that tell you what went wrong.

### Step 2: Restart the Server

1. **Stop the server**: Press `Ctrl+C` in the terminal window
2. **Restart it**: Run `py stock_dashboard_backend.py` again (or double-click `START_DASHBOARD.bat`)

The updated code now has better error handling and will show you exactly what's wrong.

### Step 3: Test the Server

Run this command in a **new** PowerShell window (while server is running):

```powershell
py test_server.py
```

This will test if the server is working and show you any errors.

### Common Issues and Solutions

#### Issue 1: "No results calculated"
- **Cause**: All stocks failed to download or process
- **Solution**: 
  - Check your internet connection
  - Wait a few minutes and try again (yfinance may be rate-limited)
  - Check the server terminal for specific error messages

#### Issue 2: "Insufficient data"
- **Cause**: Not enough historical data for some stocks
- **Solution**: The code will skip stocks with insufficient data and continue with others

#### Issue 3: yfinance download errors
- **Cause**: Network issues or rate limiting
- **Solution**: 
  - Wait 1-2 minutes and refresh the dashboard
  - Check if you can access yahoo.com in your browser
  - Try again later if Yahoo Finance is having issues

#### Issue 4: Calculation errors
- **Cause**: Some statistical calculations may fail for certain stocks
- **Solution**: The updated code now handles these gracefully and continues with other stocks

### Step 4: Check Server Logs

The server terminal will show:
- ✓ Success messages for each stock processed
- ✗ Error messages for stocks that failed
- Detailed traceback for debugging

### Step 5: Verify Server is Running

1. Open a browser and go to: `http://localhost:5000/test`
2. You should see: `{"status": "Server is running!", "message": "Flask backend is operational"}`

If this works, the server is running correctly.

### Still Having Issues?

1. **Check Python version**: Run `py --version` (should be 3.7+)
2. **Reinstall dependencies**: `py -m pip install -r requirements.txt --upgrade`
3. **Check firewall**: Make sure Windows Firewall isn't blocking port 5000
4. **Try a different port**: Edit `stock_dashboard_backend.py` line 448, change `port=5000` to `port=5001`, then update `dashboard.html` line 60 to use `http://localhost:5001/analyze`

### Getting Help

When asking for help, provide:
1. The error message from the server terminal
2. The output of `py test_server.py`
3. Your Python version (`py --version`)

