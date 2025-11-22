@echo off
cd /d "%~dp0"
echo ========================================
echo Stocks RSPS System Dashboard
echo ========================================
echo.
echo Step 1: Installing Python dependencies...
echo.
py -m pip install -r requirements.txt --quiet
echo.
echo Step 2: Starting automatic data collection...
echo.
echo The system will now:
echo   - Collect and analyze all stock data (z-scoring, ratio analysis)
echo   - Perform historical backtest
echo   - Save results to cache for faster loading
echo   - Start the dashboard server
echo.
echo This may take 10-20 minutes for the first run.
echo The server will start automatically after data collection completes.
echo.
echo Daily updates will run automatically at 13:00 (your local time)
echo.
echo ========================================
echo.
py stock_dashboard_backend.py
pause

