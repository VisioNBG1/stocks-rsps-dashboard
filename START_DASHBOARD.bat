@echo off
cd /d "%~dp0"
echo ========================================
echo Stocks RSPS System Dashboard
echo ========================================
echo.
echo Step 1: Installing Python dependencies...
echo.
py -m pip install -r requirements.txt
echo.
echo Step 2: Starting the backend server...
echo.
echo The server will start on http://localhost:5000
echo Open http://localhost:5000 in your browser after the server starts
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.
py stock_dashboard_backend.py
pause

