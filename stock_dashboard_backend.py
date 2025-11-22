import yfinance as yf
import pandas as pd
import numpy as np
from statsmodels.tsa.stattools import adfuller, kpss
from arch.unitroot import PhillipsPerron
from hurst import compute_Hc
import warnings
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
from datetime import datetime, timedelta
import time
import threading
import schedule
from datetime import datetime, timedelta

# Supabase for persistent checkpoint storage
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("  ⚠ Supabase not available - checkpoints will use local storage only")

# Disable yfinance cache to avoid "database is locked" errors in multi-worker environments
# Set environment variable to disable cache
os.environ['YFINANCE_CACHE_DISABLE'] = '1'
# Also try to disable cache programmatically
try:
    import yfinance.cache as yf_cache
    # Disable cache by setting cache location to a temp directory that gets cleared
    import tempfile
    cache_dir = tempfile.mkdtemp()
    yf_cache.set_tz_cache_location(cache_dir)
except:
    pass  # If cache disabling fails, continue anyway

# --- Flask App Setup ---
app = Flask(__name__)
# CORS is required to allow the HTML file to call the server
CORS(app) 

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Global progress tracking
# Track daily update status
daily_update_status = {
    "last_update_time": None,  # Timestamp of last update completion
    "update_in_progress": False,  # Whether update is currently running
    "update_completed": False  # Whether update just completed (show refresh message)
}

analysis_progress = {
    "status": "idle",  # "idle", "downloading", "analyzing", "ratio_analysis", "backtesting", "complete", "error"
    "stage": "",
    "current": 0,
    "total": 0,
    "message": "",
    "start_time": None,
    "last_update": None,
    "results": None,
    "error": None
}

# Lock to prevent multiple analyses from running simultaneously
analysis_lock = threading.Lock()

# --- CONFIGURATION (Based on your PineScript inputs) ---
CONFIG = {
    "z_score_len": 50,
    "adx_smoothing": 14,
    "di_length": 22,
    "kpss_src": "Close",
    "kpss_length": 36,
    "adf_src": "Close",
    "adf_length": 40,
    "adf_nLag": 0,
    "garch_alpha": 0.10,
    "garch_beta": 0.80,
    "garch_emaLen": 20,
    "halflife_lookback": 90,
    "wavelet_alpha": 0.8,
    "wavelet_len": 30,
    "corr_length": 20,
    "corr_src": "Close",
    "corr_mom_type": "ROC", # "ROC" or "RSI"
    "chop_length": 22,
    "hurst_length": 75,
    "hurst_src": "Close",
    "atr_length1": 18,
    "pp_src": "Close",
    "pp_length": 240,
    "pp_nLag": 6,
    "yang_length": 20,
    "yang_src": "Close",
    "yang_factor": 2.0,
    # avg_score system inputs
    "rsi_length": 100,
    "smooth_rsi_length": 90,
    "roc_length": 90,
    "atr_length_avg": 80,
    "atr_smoothing": "EMA",
    "stochastic_length": 78,
    "stoch_smooth": 42,
    "ema_short_length": 12,
    "ema_long_length": 50,
    "main_ratio_length": 200,
    "trend_length": 160,
    "bb_length": 160,
    "bb_mult": 6.0,
    "chaikin_length": 84,
    "chaikin_roc_length": 200,
    "omega_calc_period": 80,
    "omega_target": 0.0,
    "sortino_length": 80,
    "sharpe_length": 80,
    "vr_length": 198,
    "wpr_length": 84,
    "adr_length": 82,
    "efi_length": 102,
    "bb_start_length": 40,
    "bb_end_length": 80,
    "bb_ma_type": "EMA",
    "bb_ma_length": 18,
    "stoch_smoothK": 4,
    "stoch_periodD": 20,
    "stoch_score_type": "d > 50",
    "stoch_start_length": 80,
    "stoch_end_length": 140,
    "stoch_ma_type": "EMA",
    "stoch_ma_length": 9,
    "avg_score_z_len": 100,
}

# --- Stock & Sector Definitions ---
# Comprehensive list of stocks from all major sectors
# FULL SECTORS LIST (BACKUP - TO RESTORE LATER):
# SECTORS_FULL = {
#     "Technology": [
#         "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL",
#         "AMD", "INTC", "CRM", "ADBE", "CSCO", "TXN", "QCOM", "NOW", "AMAT", "MU",
#         "LRCX", "KLAC", "SNPS", "CDNS", "ANSS", "INTU", "FTNT", "PANW", "CRWD", "ZS",
#         "NET", "DDOG", "TEAM", "DOCN", "MDB", "SNOW", "PLTR", "RPD", "ESTC", "SPLK"
#     ],
#     "Energy": [
#         "XOM", "CVX", "SLB", "MRO", "EOG", "COP", "MPC", "PSX", "VLO", "HAL",
#         "OXY", "DVN", "FANG", "CTRA", "APA", "HES", "BKR", "NOV", "FTI", "RIG",
#         "HP", "LBRT", "NBR", "PTEN", "WFRD", "VTLE", "SM", "CIVI", "MGY", "MTDR"
#     ],
#     "Health Care": [
#         "JNJ", "PFE", "LLY", "UNH", "ABBV", "TMO", "ABT", "DHR", "BMY", "AMGN",
#         "GILD", "CI", "HUM", "CVS", "ELV", "CNC", "MOH", "MRNA", "BIIB", "REGN",
#         "VRTX", "ALNY", "IONS", "FOLD", "ARWR", "SGMO", "BEAM", "CRISPR", "NTLA", "EDIT",
#         "ZTS", "IDXX", "ALGN", "ISRG", "SYK", "BAX", "EW", "BSX", "ZBH", "HOLX"
#     ],
#     "Industrials": [
#         "BA", "CAT", "DE", "HON", "GE", "RTX", "LMT", "NOC", "GD", "TDG",
#         "ETN", "EMR", "ITW", "PH", "AME", "DOV", "FTV", "GGG", "PNR", "ROK",
#         "CMI", "PCAR", "WAB", "KNX", "JBHT", "ODFL", "XPO", "CHRW", "EXPD", "FDX",
#         "UPS", "AAL", "DAL", "LUV", "UAL", "JBLU", "SAVE", "ALK", "HA", "SKYW"
#     ],
#     "Utilities": [
#         "NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "ES", "EIX", "PEG",
#         "ED", "FE", "AES", "VST", "CEG", "PCG", "ETR", "CMS", "ATO", "LNT",
#         "WEC", "CNP", "NI", "OGE", "PNW", "POR", "IDA", "SWX", "NWN", "RGCO"
#     ],
#     "Consumer Staples": [
#         "PG", "KO", "WMT", "COST", "PEP", "CL", "MDLZ", "GIS", "KMB", "HSY",
#         "SJM", "CPB", "CAG", "HRL", "TSN", "BG", "ADM", "LW", "FLO", "SJM",
#         "TGT", "HD", "LOW", "TJX", "ROST", "BBWI", "DKS", "ANF", "AEO", "GPS"
#     ],
#     "Financials": [
#         "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "COF",
#         "USB", "PNC", "TFC", "BK", "STT", "BEN", "IVZ", "ETFC", "AMTD", "HOOD",
#         "V", "MA", "PYPL", "FIS", "FISV", "GPN", "FLYW", "AFRM", "UPST", "SOFI"
#     ],
#     "Consumer Discretionary": [
#         "AMZN", "TSLA", "NKE", "SBUX", "MCD", "YUM", "CMG", "DPZ", "WING", "CAVA",
#         "DIS", "NFLX", "PARA", "WBD", "FOXA", "ROKU", "FUBO", "DKNG", "PENN", "LNW",
#         "F", "GM", "STLA", "HMC", "TM", "RIVN", "LCID", "FISK", "NKLA", "HYZN"
#     ],
#     "Real Estate": [
#         "AMT", "PLD", "EQIX", "PSA", "WELL", "VICI", "SPG", "O", "DLR", "EXPI",
#         "CBRE", "JLL", "CWK", "REXR", "STAG", "FR", "BRX", "BXP", "KIM", "REG",
#         "MAC", "SLG", "VTR", "PEAK", "CTRE", "HTA", "DOC", "MPW", "OHI", "GMRE"
#     ],
#     "Materials": [
#         "LIN", "APD", "ECL", "SHW", "PPG", "DD", "DOW", "FCX", "NEM", "VALE",
#         "RIO", "BHP", "SCCO", "TECK", "AA", "X", "CLF", "STLD", "NUE", "CMC",
#         "RS", "WLK", "LYB", "CE", "FMC", "MOS", "NTR", "CF", "CTVA", "ADM"
#     ],
#     "Communication Services": [
#         "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "LUMN",
#         "PARA", "WBD", "FOXA", "NWSA", "NWS", "IAC", "ANGI", "TRIP", "EXPE", "BKNG",
#         "ABNB", "UBER", "LYFT", "GRAB", "DIDI", "BIDU", "JD", "PDD", "BABA", "TME"
#     ]
# }

# TEMPORARY: Using 1 stock per sector for faster testing
# REMOVED STOCKS (to restore later): MSFT, CVX, JNJ, CAT, SO, KO, BAC, TSLA, PLD, APD, META
# --- Helper function for downloading stock data with rate limiting and retries ---
def get_cached_stock_data(ticker):
    """Load cached stock data from file"""
    cache_file = os.path.join(STOCK_DATA_CACHE_DIR, f"{ticker}.csv")
    if os.path.exists(cache_file):
        try:
            # Try to read the CSV file
            data = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            # Verify the data is valid (has a DatetimeIndex and is not empty)
            if data.empty or not isinstance(data.index, pd.DatetimeIndex):
                print(f"    ⚠ Cached data for {ticker} is invalid, deleting cache file...")
                os.remove(cache_file)
                return None
            return data
        except Exception as e:
            print(f"    ⚠ Error loading cached data for {ticker}: {e}")
            # Delete corrupted cache file
            try:
                os.remove(cache_file)
                print(f"    ✓ Deleted corrupted cache file for {ticker}")
            except:
                pass
            return None
    return None

def save_cached_stock_data(ticker, data):
    """Save stock data to cache file"""
    cache_file = os.path.join(STOCK_DATA_CACHE_DIR, f"{ticker}.csv")
    try:
        # Ensure data has a DatetimeIndex before saving
        if not isinstance(data.index, pd.DatetimeIndex):
            if data.index.name is None or data.index.name == 'Date':
                data.index = pd.to_datetime(data.index)
            else:
                # If index is not a date, try to reset it
                print(f"    ⚠ Warning: {ticker} data index is not a DatetimeIndex, attempting to fix...")
                data.index = pd.to_datetime(data.index, errors='coerce')
        # Save with date format
        data.to_csv(cache_file, date_format='%Y-%m-%d')
    except Exception as e:
        print(f"    ⚠ Error saving cached data for {ticker}: {e}")

def download_stock_data(ticker, period="2y", interval="1d", start=None, end=None, max_retries=3, delay=2.0, use_cache=True):
    """
    Download stock data with rate limiting, retry logic, and caching.
    
    Args:
        ticker: Stock ticker symbol
        period: Data period (e.g., "2y", "1d") - used if start/end not provided
        interval: Data interval (default: "1d")
        start: Start date (datetime or string) - alternative to period
        end: End date (datetime or string) - alternative to period
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between requests in seconds (default: 0.5)
        use_cache: Whether to use cached data and only download new data (default: True)
    
    Returns:
        pandas.DataFrame: Stock data or empty DataFrame if failed
    """
    # Try to load from cache first
    cached_data = None
    if use_cache:
        cached_data = get_cached_stock_data(ticker)
        if cached_data is not None and not cached_data.empty:
            # If we have cached data, check if we need to download only new data
            if start is None and end is None:
                # For daily updates, only download the latest day
                last_date = cached_data.index.max()
                # Ensure last_date is a Timestamp
                if not isinstance(last_date, pd.Timestamp):
                    last_date = pd.Timestamp(last_date)
                last_date = last_date.normalize()
                today = pd.Timestamp.now().normalize()
                # If cached data is up to yesterday, download only today
                if last_date < today:
                    try:
                        # Download only new data since last cached date
                        new_data = yf.download(ticker, start=last_date + pd.Timedelta(days=1), end=today + pd.Timedelta(days=1), interval=interval, progress=False)
                        if not new_data.empty:
                            # Combine cached and new data
                            combined_data = pd.concat([cached_data, new_data]).drop_duplicates().sort_index()
                            # Save updated cache
                            save_cached_stock_data(ticker, combined_data)
                            print(f"    ✓ {ticker}: Loaded from cache + downloaded {len(new_data)} new days")
                            return combined_data
                        else:
                            # No new data, return cached
                            print(f"    ✓ {ticker}: Using cached data (up to date)")
                            return cached_data
                    except Exception as e:
                        print(f"    ⚠ Error downloading new data for {ticker}: {e}, using cached data")
                        return cached_data
                else:
                    # Cached data is up to date
                    print(f"    ✓ {ticker}: Using cached data (up to date)")
                    return cached_data
            else:
                # If start/end specified, check if cached data covers the range
                if isinstance(start, str):
                    start = pd.Timestamp(start).normalize()
                if isinstance(end, str):
                    end = pd.Timestamp(end).normalize()
                # Ensure cached index values are Timestamps for comparison
                cache_min = cached_data.index.min()
                cache_max = cached_data.index.max()
                if not isinstance(cache_min, pd.Timestamp):
                    cache_min = pd.Timestamp(cache_min).normalize()
                else:
                    cache_min = cache_min.normalize()
                if not isinstance(cache_max, pd.Timestamp):
                    cache_max = pd.Timestamp(cache_max).normalize()
                else:
                    cache_max = cache_max.normalize()
                if cache_min <= start and cache_max >= end:
                    # Cached data covers the range
                    filtered_data = cached_data.loc[start:end]
                    if not filtered_data.empty:
                        print(f"    ✓ {ticker}: Using cached data for range {start} to {end}")
                        return filtered_data
    
    # Download fresh data if cache not available or not using cache
    for attempt in range(max_retries):
        try:
            # Add delay to avoid rate limiting (longer delay for retries)
            if attempt > 0:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                print(f"    Retrying {ticker} (attempt {attempt + 1}/{max_retries}) after {wait_time:.1f}s...")
                time.sleep(wait_time)
            else:
                # Small delay even on first attempt to avoid rate limits
                time.sleep(delay)
            
            # Use start/end if provided, otherwise use period
            if start is not None and end is not None:
                data = yf.download(ticker, start=start, end=end, interval=interval, progress=False)
            else:
                # Use period (defaults to "2y" if not specified)
                data = yf.download(ticker, period=period, interval=interval, progress=False)
            
            if not data.empty:
                # Save to cache
                if use_cache:
                    save_cached_stock_data(ticker, data)
                    print(f"    ✓ {ticker}: Downloaded and cached")
                return data
            else:
                print(f"    No data returned for {ticker}")
                return pd.DataFrame()
                
        except Exception as e:
            error_msg = str(e)
            # Check if it's a rate limit error
            if "Rate limited" in error_msg or "Too Many Requests" in error_msg or "429" in error_msg or "YFRateLimitError" in error_msg:
                if attempt < max_retries - 1:
                    # Much longer wait for rate limits: 30s, 60s, 120s
                    wait_time = 30 * (2 ** attempt)  # 30, 60, 120 seconds
                    print(f"    Rate limited for {ticker}. Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"    ✗ Rate limit error for {ticker} after {max_retries} attempts. Skipping.")
                    # Return cached data if available, even if outdated
                    if cached_data is not None and not cached_data.empty:
                        print(f"    ⚠ Using outdated cached data for {ticker}")
                        return cached_data
                    return pd.DataFrame()
            else:
                # Other errors - log and return empty
                print(f"    ✗ Error downloading {ticker}: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                else:
                    # Return cached data if available
                    if cached_data is not None and not cached_data.empty:
                        print(f"    ⚠ Using cached data for {ticker} due to download error")
                        return cached_data
                    return pd.DataFrame()
    
    # If all attempts failed, return cached data if available
    if cached_data is not None and not cached_data.empty:
        print(f"    ⚠ Using cached data for {ticker} after all download attempts failed")
        return cached_data
    
    return pd.DataFrame()

SECTORS = {
    "Technology": [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL",
        "AMD", "INTC", "CRM", "ADBE", "CSCO", "TXN", "QCOM", "NOW", "AMAT", "MU",
        "LRCX", "KLAC", "SNPS", "CDNS", "ANSS", "INTU", "FTNT", "PANW", "CRWD", "ZS",
        "NET", "DDOG", "TEAM", "DOCN", "MDB", "SNOW", "PLTR", "RPD", "ESTC", "SPLK"
    ],
    "Energy": [
        "XOM", "CVX", "SLB", "MRO", "EOG", "COP", "MPC", "PSX", "VLO", "HAL",
        "OXY", "DVN", "FANG", "CTRA", "APA", "HES", "BKR", "NOV", "FTI", "RIG",
        "HP", "LBRT", "NBR", "PTEN", "WFRD", "VTLE", "SM", "CIVI", "MGY", "MTDR"
    ],
    "Health Care": [
        "JNJ", "PFE", "LLY", "UNH", "ABBV", "TMO", "ABT", "DHR", "BMY", "AMGN",
        "GILD", "CI", "HUM", "CVS", "ELV", "CNC", "MOH", "MRNA", "BIIB", "REGN",
        "VRTX", "ALNY", "IONS", "FOLD", "ARWR", "SGMO", "BEAM", "CRISPR", "NTLA", "EDIT",
        "ZTS", "IDXX", "ALGN", "ISRG", "SYK", "BAX", "EW", "BSX", "ZBH", "HOLX"
    ],
    "Industrials": [
        "BA", "CAT", "DE", "HON", "GE", "RTX", "LMT", "NOC", "GD", "TDG",
        "ETN", "EMR", "ITW", "PH", "AME", "DOV", "FTV", "GGG", "PNR", "ROK",
        "CMI", "PCAR", "WAB", "KNX", "JBHT", "ODFL", "XPO", "CHRW", "EXPD", "FDX",
        "UPS", "AAL", "DAL", "LUV", "UAL", "JBLU", "SAVE", "ALK", "HA", "SKYW"
    ],
    "Utilities": [
        "NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "ES", "EIX", "PEG",
        "ED", "FE", "AES", "VST", "CEG", "PCG", "ETR", "CMS", "ATO", "LNT",
        "WEC", "CNP", "NI", "OGE", "PNW", "POR", "IDA", "SWX", "NWN", "RGCO"
    ],
    "Consumer Staples": [
        "PG", "KO", "WMT", "COST", "PEP", "CL", "MDLZ", "GIS", "KMB", "HSY",
        "SJM", "CPB", "CAG", "HRL", "TSN", "BG", "ADM", "LW", "FLO", "SJM",
        "TGT", "HD", "LOW", "TJX", "ROST", "BBWI", "DKS", "ANF", "AEO", "GPS"
    ],
    "Financials": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "COF",
        "USB", "PNC", "TFC", "BK", "STT", "BEN", "IVZ", "ETFC", "AMTD", "HOOD",
        "V", "MA", "PYPL", "FIS", "FISV", "GPN", "FLYW", "AFRM", "UPST", "SOFI"
    ],
    "Consumer Discretionary": [
        "AMZN", "TSLA", "NKE", "SBUX", "MCD", "YUM", "CMG", "DPZ", "WING", "CAVA",
        "DIS", "NFLX", "PARA", "WBD", "FOXA", "ROKU", "FUBO", "DKNG", "PENN", "LNW",
        "F", "GM", "STLA", "HMC", "TM", "RIVN", "LCID", "FISK", "NKLA", "HYZN"
    ],
    "Real Estate": [
        "AMT", "PLD", "EQIX", "PSA", "WELL", "VICI", "SPG", "O", "DLR", "EXPI",
        "CBRE", "JLL", "CWK", "REXR", "STAG", "FR", "BRX", "BXP", "KIM", "REG",
        "MAC", "SLG", "VTR", "PEAK", "CTRE", "HTA", "DOC", "MPW", "OHI", "GMRE"
    ],
    "Materials": [
        "LIN", "APD", "ECL", "SHW", "PPG", "DD", "DOW", "FCX", "NEM", "VALE",
        "RIO", "BHP", "SCCO", "TECK", "AA", "X", "CLF", "STLD", "NUE", "CMC",
        "RS", "WLK", "LYB", "CE", "FMC", "MOS", "NTR", "CF", "CTVA", "ADM"
    ],
    "Communication Services": [
        "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "LUMN",
        "PARA", "WBD", "FOXA", "NWSA", "NWS", "IAC", "ANGI", "TRIP", "EXPE", "BKNG",
        "ABNB", "UBER", "LYFT", "GRAB", "DIDI", "BIDU", "JD", "PDD", "BABA", "TME"
    ]
}

# --- Helper Functions ---

def calc_zscore(series, length):
    """
    Calculates Z-score matching PineScript calc_zscore function.
    Uses simple moving average (SMA) and standard deviation over rolling window.
    Returns the last (current) z-score value.
    """
    if len(series) < length:
        return 0.0
    
    # PineScript uses ta.sma (simple moving average) and ta.stdev
    # We need to use min_periods=length to match PineScript behavior
    mean = series.rolling(window=length, min_periods=length).mean()
    std = series.rolling(window=length, min_periods=length).std(ddof=0)  # ddof=0 matches PineScript stdev
    
    # Replace zero std with a small value to avoid division by zero
    std = std.replace(0, 1e-10)
    
    # Calculate z-score: (source - mean) / stdev
    z = (series - mean) / std
    
    # Return the last (current) value, matching PineScript behavior
    last_z = z.iloc[-1]
    
    # Handle NaN/Inf values
    if pd.isna(last_z) or np.isinf(last_z):
        return 0.0
    
    return float(last_z)

def rma(series, length):
    """PineScript 'rma' (Running Moving Average) implementation."""
    return series.ewm(alpha=1/length, adjust=False).mean()

# --- 12 COMPONENT CALCULATIONS ---

def calc_adx(high, low, close, di_len, adx_len):
    """1. ADX Calculation"""
    up = high.diff()
    down = -low.diff()
    
    plusDM = up.copy()
    plusDM[(plusDM < 0) | (plusDM <= down)] = 0
    
    minusDM = down.copy()
    minusDM[(minusDM < 0) | (minusDM <= up)] = 0
    
    tr1 = pd.DataFrame({'a': high - low, 'b': (high - close.shift(1)).abs(), 'c': (low - close.shift(1)).abs()}).max(axis=1)
    truerange = rma(tr1, di_len)
    
    plus = 100 * rma(plusDM, di_len) / truerange
    minus = 100 * rma(minusDM, di_len) / truerange
    
    sum_val = plus + minus
    adx_val = 100 * rma( (plus - minus).abs() / sum_val.replace(0, 1), adx_len)
    return adx_val

def calc_kpss_stat(series, length):
    """2. KPSS Statistic"""
    try:
        # Use only the last 'length' data points for the test
        kpss_data = series.iloc[-length:]
        # 'c' means test for level stationarity
        stat, p_value, lags, crit = kpss(kpss_data, regression='c', nlags='auto')
        return stat
    except Exception as e:
        # print(f"  KPSS Error: {e}")
        return 0.0

def calc_adf_stat(series, length, maxlag):
    """3. ADF Statistic"""
    try:
        adf_data = series.iloc[-length:]
        result = adfuller(adf_data, maxlag=maxlag, regression='c', autolag=None)
        return result[0] # Return the test statistic
    except Exception as e:
        # print(f"  ADF Error: {e}")
        return 0.0

def calc_garch_vol(series, alpha, beta, ema_len):
    """4. GARCH Volatility (Replicating PineScript logic)"""
    ema = series.ewm(span=ema_len, adjust=False).mean()
    returns_sq = (series - ema).pow(2)
    
    variance = pd.Series(index=series.index, dtype=float)
    variance.iloc[0] = returns_sq.iloc[0] # Initialize
    
    # Iterative calculation (slow, but matches Pine)
    for i in range(1, len(series)):
        prev_variance = variance.iloc[i-1] if pd.notna(variance.iloc[i-1]) else 0
        variance.iloc[i] = alpha * returns_sq.iloc[i] + beta * prev_variance
        
    garchVolatility = np.sqrt(variance)
    return garchVolatility

def calc_halflife(series, length):
    """5. Half-Life of Mean Reversion"""
    try:
        log_prices = np.log(series.iloc[-length:])
        delta_log = log_prices.diff().dropna()
        lagged_log = log_prices.shift(1).dropna()
        
        # Ensure same length
        delta_log = delta_log.iloc[-len(lagged_log):]
        lagged_log = lagged_log.iloc[-len(delta_log):]
        
        if len(delta_log) < 2: return 0.0

        # OLS regression: delta_log = slope * lagged_log + intercept
        slope = np.polyfit(lagged_log, delta_log, 1)[0]
        
        if slope == 0: return 0.0
        halflife = -np.log(2) / slope
        return halflife
    except Exception as e:
        # print(f"  Halflife Error: {e}")
        return 0.0
        
def calc_wavelet_vol(series, alpha, length):
    """6. Wavelet Volatility"""
    pole = 0.707 * alpha
    coeff1 = (1 - pole) * (1 - pole)
    coeff2 = 2 * (1 - pole)
    
    q1 = pd.Series(index=series.index, dtype=float)
    src_m_2 = series.shift(2).fillna(0)
    
    q1.iloc[0] = 0.0
    q1.iloc[1] = 0.0
    
    for i in range(2, len(series)):
        q1.iloc[i] = (coeff1 * (series.iloc[i] - src_m_2.iloc[i]) +
                      coeff2 * q1.iloc[i-1] -
                      pole * pole * q1.iloc[i-2])
    
    wave_line = 2 * q1 - q1.shift(2)
    wave_vol = wave_line.rolling(window=length).std()
    return wave_vol

def calc_pmc_corr(series, mom_type, length):
    """7. Price/Momentum Correlation"""
    if mom_type == "ROC":
        momentum = series.pct_change(1) * 100 # ta.roc(src, 1)
    else: # "RSI"
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = rma(gain, 14)
        avg_loss = rma(loss, 14)
        rs = avg_gain / avg_loss.replace(0, 1)
        momentum = 100 - (100 / (1 + rs))
        
    pmc_corr = series.rolling(window=length).corr(momentum)
    return pmc_corr

def calc_chop(high, low, close, length):
    """8. Choppiness Index"""
    tr1 = pd.DataFrame({'a': high - low, 'b': (high - close.shift(1)).abs(), 'c': (low - close.shift(1)).abs()}).max(axis=1)
    atr1 = rma(tr1, 1)
    
    atr_sum = atr1.rolling(window=length).sum()
    high_max = high.rolling(window=length).max()
    low_min = low.rolling(window=length).min()
    
    chop = 100 * np.log10(atr_sum / (high_max - low_min)) / np.log10(length)
    return chop

def calc_hurst(series, length):
    """9. Hurst Exponent"""
    try:
        hurst_data = series.iloc[-length:]
        # compute_Hc returns (H, c, data)
        H, c, data = compute_Hc(hurst_data, kind='price', simplified=True)
        return H
    except Exception as e:
        # print(f"  Hurst Error: {e}")
        return 0.0
        
def calc_atr(high, low, close, length):
    """10. ATR (Average True Range)"""
    tr1 = pd.DataFrame({'a': high - low, 'b': (high - close.shift(1)).abs(), 'c': (low - close.shift(1)).abs()}).max(axis=1)
    atr_val = rma(tr1, length)
    return atr_val

def calc_pp_stat(series, length, nlag):
    """11. Phillips-Perron Statistic"""
    try:
        pp_data = series.iloc[-length:]
        # 'c' for constant
        pp = PhillipsPerron(pp_data, lags=nlag, trend='c')
        return pp.stat
    except Exception as e:
        # print(f"  PP Error: {e}")
        return 0.0

def calc_yang_vol(open, high, low, close, length, factor):
    """12. Yang Volatility"""
    returns = (close / close.shift(1)).apply(np.log)
    vol_std = returns.rolling(window=length).std()
    
    ewma_returns2 = returns.pow(2).ewm(span=length, adjust=False).mean()
    vol_ewma = np.sqrt(ewma_returns2)
    
    pos_returns = returns.where(returns > 0, 0)
    neg_returns = returns.where(returns < 0, 0)
    
    vol_up = pos_returns.rolling(window=length).std()
    vol_down = neg_returns.rolling(window=length).std()
    
    vol_asymmetric = np.sqrt(vol_up.pow(2) + factor * vol_down.pow(2))
    
    yang_vol = pd.DataFrame({'std': vol_std, 'ewma': vol_ewma, 'asym': vol_asymmetric}).max(axis=1)
    return yang_vol.ewm(span=int(length / 2), adjust=False).mean()

# --- avg_score System Functions ---

def ma_function_avg(source, length, smoothing):
    """Moving average function matching PineScript"""
    if smoothing == "RMA":
        return rma(source, length)
    elif smoothing == "SMA":
        return source.rolling(window=length).mean()
    elif smoothing == "EMA":
        return source.ewm(span=length, adjust=False).mean()
    elif smoothing == "WMA":
        return source.rolling(window=length).apply(lambda x: np.average(x, weights=np.arange(1, len(x)+1)), raw=True)
    else:
        return source.ewm(span=length, adjust=False).mean()

def calc_trend_score_avg(src, length):
    """Trend Score calculation"""
    # Convert to numpy array for reliable position-based indexing
    src_values = src.values
    total = pd.Series(index=src.index, dtype=float)
    
    for i in range(length, len(src_values)):
        score = 0.0
        for j in range(1, length + 1):
            idx_prev = i - j
            # Check bounds - both indices must be valid
            if idx_prev >= 0 and i < len(src_values) and idx_prev < len(src_values):
                try:
                    score += 1 if src_values[i] >= src_values[idx_prev] else -1
                except (IndexError, KeyError):
                    # Skip if index is out of bounds
                    continue
        total.iloc[i] = score
    return total.fillna(0.0)

def calc_wpr(src, length):
    """Williams %R calculation"""
    highest = src.rolling(window=length).max()
    lowest = src.rolling(window=length).min()
    wpr = 100 * (src - highest) / (highest - lowest)
    return wpr.replace([np.inf, -np.inf], np.nan).fillna(0.0)

def bb_forloop(start_len, end_len, ma_len, ma_type, bb_source):
    """BB ForLoop calculation"""
    signal_array = []
    for x in range(end_len - start_len + 1):
        len_val = start_len + x
        if len_val > len(bb_source):
            continue
        basis = bb_source.rolling(window=len_val).mean()
        trend = (bb_source > basis).astype(int) * 2 - 1  # 1 or -1
        signal_array.append(trend.iloc[-1] if len(trend) > 0 else 0.0)
    
    if not signal_array:
        return pd.Series(index=bb_source.index, dtype=float).fillna(0.0)
    
    avg = np.mean(signal_array)
    if ma_type == "EMA":
        return pd.Series([avg] * len(bb_source), index=bb_source.index).ewm(span=ma_len, adjust=False).mean()
    elif ma_type == "SMA":
        return pd.Series([avg] * len(bb_source), index=bb_source.index).rolling(window=ma_len).mean()
    else:
        return pd.Series([avg] * len(bb_source), index=bb_source.index).ewm(span=ma_len, adjust=False).mean()

def stoch_forloop(start_len, end_len, ma_len, ma_type, smoothK, periodD, score_type, high, low, close):
    """Stochastic ForLoop calculation"""
    signal_array = []
    for x in range(end_len - start_len + 1):
        len_val = start_len + x
        if len_val > len(close):
            continue
        try:
            # Calculate stochastic
            lowest = low.rolling(window=len_val).min()
            highest = high.rolling(window=len_val).max()
            stoch_k = 100 * (close - lowest) / (highest - lowest)
            stoch_k = stoch_k.rolling(window=smoothK).mean()
            stoch_d = stoch_k.rolling(window=periodD).mean()
            
            k_val = stoch_k.iloc[-1] if len(stoch_k) > 0 else 50
            d_val = stoch_d.iloc[-1] if len(stoch_d) > 0 else 50
            
            if score_type == "k > 50":
                trend = 1 if k_val > 50 else -1
            elif score_type == "k > d":
                trend = 1 if k_val > d_val else -1
            else:  # "d > 50"
                trend = 1 if d_val > 50 else -1
            
            signal_array.append(trend)
        except:
            signal_array.append(0.0)
    
    if not signal_array:
        return pd.Series(index=close.index, dtype=float).fillna(0.0)
    
    avg = np.mean(signal_array)
    if ma_type == "EMA":
        return pd.Series([avg] * len(close), index=close.index).ewm(span=ma_len, adjust=False).mean()
    elif ma_type == "SMA":
        return pd.Series([avg] * len(close), index=close.index).rolling(window=ma_len).mean()
    else:
        return pd.Series([avg] * len(close), index=close.index).ewm(span=ma_len, adjust=False).mean()

def calc_avg_score(close, volume, open_price, high, low, config):
    """Calculate avg_score using all 22 indicators"""
    try:
        src = close
        vol = volume
        
        # ATR
        tr = pd.DataFrame({'a': high - low, 'b': (high - close.shift(1)).abs(), 'c': (low - close.shift(1)).abs()}).max(axis=1)
        atr_raw = ma_function_avg(tr, config['atr_length_avg'], config['atr_smoothing'])
        z_atr = calc_zscore(atr_raw, config['avg_score_z_len'])
        
        # Williams %R
        wpr_value = calc_wpr(close, config['wpr_length'])
        z_wpr = calc_zscore(wpr_value, config['avg_score_z_len'])
        
        # Trend Score
        trend_score = calc_trend_score_avg(src, config['trend_length'])
        z_trend_score = calc_zscore(trend_score, config['avg_score_z_len'])
        
        # RSI
        delta = src.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = rma(gain, config['rsi_length'])
        avg_loss = rma(loss, config['rsi_length'])
        rs = avg_gain / avg_loss.replace(0, 1)
        rsi_value = 100 - (100 / (1 + rs))
        z_rsi = calc_zscore(rsi_value, config['avg_score_z_len'])
        
        # Smooth RSI
        c1 = 100 - (100 / (1 + rma(gain, config['smooth_rsi_length']) / rma(loss, config['smooth_rsi_length']).replace(0, 1)))
        c2 = c1
        c3 = c1
        c4 = c1
        smooth_rsi = (c1 + c2 + c3 + c4) / 4
        z_smooth_rsi = calc_zscore(smooth_rsi, config['avg_score_z_len'])
        
        # ROC
        roc_value = src.pct_change(config['roc_length']) * 100
        z_roc = calc_zscore(roc_value, config['avg_score_z_len'])
        
        # Stochastic
        lowest = low.rolling(window=config['stochastic_length'], min_periods=1).min()
        highest = high.rolling(window=config['stochastic_length'], min_periods=1).max()
        stoch_k = 100 * (close - lowest) / (highest - lowest).replace(0, 1)
        stoch_k = stoch_k.rolling(window=config['stoch_smooth'], min_periods=1).mean()
        z_stoch = calc_zscore(stoch_k, config['avg_score_z_len'])
        
        # EMA Score
        ema_short = src.ewm(span=config['ema_short_length'], adjust=False).mean()
        ema_long = src.ewm(span=config['ema_long_length'], adjust=False).mean()
        ema_score = (ema_short > ema_long).astype(float) * 2 - 1  # 1 or -1
        
        # Main Ratio
        main_ratio = src / src.ewm(span=config['main_ratio_length'], adjust=False).mean()
        z_main_ratio = calc_zscore(main_ratio, config['avg_score_z_len'])
        
        # Sharpe - Match PineScript: ta.ema(src - ta.ema(src, sharpe_length), sharpe_length) / ta.stdev(src, sharpe_length)
        ema_src = src.ewm(span=config['sharpe_length'], adjust=False).mean()
        sharpe_numerator = (src - ema_src).ewm(span=config['sharpe_length'], adjust=False).mean()
        sharpe_denominator = src.rolling(window=config['sharpe_length'], min_periods=1).std(ddof=0).replace(0, 1e-10)
        sharpe_value = sharpe_numerator / sharpe_denominator
        z_sharpe = calc_zscore(sharpe_value, config['avg_score_z_len'])
        
        # Sortino - Match PineScript exactly
        ema_close = src.ewm(span=config['sortino_length'], adjust=False).mean()
        downside_returns = (ema_close - src).where(src < ema_close, 0)
        downside_ema = downside_returns.ewm(span=config['sortino_length'], adjust=False).mean()
        sortino_value = (ema_close - src) / downside_ema.replace(0, 1e-10)
        z_sortino = calc_zscore(sortino_value, config['avg_score_z_len'])
        
        # Omega
        omega_daily_returns = src.pct_change(1)
        omega_series = pd.Series(index=src.index, dtype=float)
        for i in range(config['omega_calc_period'], len(src)):
            returns_above = 0.0
            returns_below = 0.0
            for j in range(config['omega_calc_period']):
                ret = omega_daily_returns.iloc[i - j]
                if ret > config['omega_target']:
                    returns_above += (ret - config['omega_target'])
                else:
                    returns_below += (config['omega_target'] - ret)
            omega_series.iloc[i] = returns_above / returns_below if returns_below != 0 else np.nan
        z_omega = calc_zscore(omega_series.fillna(0.0), config['avg_score_z_len'])
        
        # Accumulation/Distribution - Match PineScript exactly
        # PineScript: ad = ta.cum(...) then z_ad = calc_zscore(ad, 100)
        clv = ((close - low) - (high - close)) / (high - low).replace(0, 1)
        ad = (clv * volume).cumsum()
        # Z-score the cumulative value directly (PineScript does this)
        z_ad = calc_zscore(ad, config['avg_score_z_len'])
        
        # OBV - Match PineScript exactly
        obv_value = (np.sign(src.diff()) * volume).cumsum()
        # Z-score the cumulative value directly
        z_obv = calc_zscore(obv_value, config['avg_score_z_len'])
        
        # Bollinger Bands
        bb_basis = src.rolling(window=config['bb_length']).mean()
        bb_dev = config['bb_mult'] * src.rolling(window=config['bb_length']).std(ddof=0)
        bb_upper = bb_basis + bb_dev
        bb_lower = bb_basis - bb_dev
        bb_percent_b = (src - bb_lower) / (bb_upper - bb_lower).replace(0, 1)
        z_bb = calc_zscore(bb_percent_b, config['avg_score_z_len'])
        
        # Chaikin Volatility
        chaikin_volatility = (high - low).ewm(span=config['chaikin_length'], adjust=False).mean()
        chaikin_volatility = chaikin_volatility.pct_change(config['chaikin_roc_length']) * 100
        z_chaikin = calc_zscore(chaikin_volatility, config['avg_score_z_len'])
        
        # Volume Ratio
        vr_up = pd.Series(index=src.index, dtype=float)
        vr_down = pd.Series(index=src.index, dtype=float)
        for i in range(config['vr_length'], len(src)):
            up = 0.0
            down = 0.0
            for j in range(config['vr_length']):
                idx = i - j
                # Check bounds - must be valid for both vol and src
                if idx < 0:
                    continue  # Skip negative indices
                if idx >= len(vol) or idx >= len(src):
                    continue  # Skip if index is out of bounds for either series
                # Check if we can calculate change (need previous index)
                if idx - 1 < 0 or idx - 1 >= len(src):
                    change = 0  # Can't calculate change if previous index is out of bounds
                else:
                    change = src.iloc[idx] - src.iloc[idx - 1]
                # Now safe to access vol.iloc[idx] since we've checked bounds
                # Double-check vol bounds before accessing
                if idx < len(vol):
                    try:
                        vol_val = vol.iloc[idx]
                        if change > 0:
                            up += vol_val
                        elif change == 0:
                            up += vol_val / 2
                        down += vol_val
                    except (IndexError, KeyError):
                        # Skip if access fails
                        continue
            vr_up.iloc[i] = up
            vr_down.iloc[i] = down
        vr = 100 * (vr_up / vr_down.replace(0, 1))
        z_vr = calc_zscore(vr.fillna(0.0), config['avg_score_z_len'])
        
        # Advance/Decline Ratio
        is_up = (close - open_price) >= 0
        up_bars = is_up.rolling(window=config['adr_length']).sum()
        down_bars = (~is_up).rolling(window=config['adr_length']).sum()
        adr_value = up_bars / down_bars.replace(0, 1)
        z_adr = calc_zscore(adr_value, config['avg_score_z_len'])
        
        # Elder Force Index
        efi_value = (src.diff() * vol).ewm(span=config['efi_length'], adjust=False).mean()
        z_efi = calc_zscore(efi_value, config['avg_score_z_len'])
        
        # Price Volume Trend - Match PineScript exactly
        pvt_value = (src.pct_change(1) * vol).cumsum()
        # Z-score the cumulative value directly
        z_pvt = calc_zscore(pvt_value, config['avg_score_z_len'])
        
        # BB ForLoop
        bb_ma_value = bb_forloop(config['bb_start_length'], config['bb_end_length'], 
                                 config['bb_ma_length'], config['bb_ma_type'], close)
        bb_ma_value = bb_ma_value.fillna(0.0)
        
        # Stochastic ForLoop
        stoch_ma_value = stoch_forloop(config['stoch_start_length'], config['stoch_end_length'],
                                       config['stoch_ma_length'], config['stoch_ma_type'],
                                       config['stoch_smoothK'], config['stoch_periodD'],
                                       config['stoch_score_type'], high, low, close)
        stoch_ma_value = stoch_ma_value.fillna(0.0)
        
        # Calculate average - ensure all values are finite and reasonable
        scores = []
        
        # Add z-scores with validation
        z_scores_list = [z_rsi, z_smooth_rsi, z_roc, z_atr, z_stoch, z_main_ratio, z_trend_score, 
                         z_obv, z_bb, z_ad, z_chaikin, z_omega, z_sortino, z_sharpe, z_vr, z_wpr, 
                         z_pvt, z_adr, z_efi]
        
        for z in z_scores_list:
            if pd.isna(z) or np.isinf(z):
                continue
            # Cap extreme z-scores to reasonable range
            z_capped = max(-10, min(10, z))
            scores.append(z_capped)
        
        # Add EMA score (should be -1 or 1)
        ema_val = ema_score.iloc[-1] if isinstance(ema_score, pd.Series) else ema_score
        if not (pd.isna(ema_val) or np.isinf(ema_val)):
            scores.append(ema_val)
        
        # Add ForLoop values (should be between -1 and 1)
        bb_val = bb_ma_value.iloc[-1] if isinstance(bb_ma_value, pd.Series) else 0.0
        if not (pd.isna(bb_val) or np.isinf(bb_val)) and abs(bb_val) <= 1:
            scores.append(bb_val)
        
        stoch_val = stoch_ma_value.iloc[-1] if isinstance(stoch_ma_value, pd.Series) else 0.0
        if not (pd.isna(stoch_val) or np.isinf(stoch_val)) and abs(stoch_val) <= 1:
            scores.append(stoch_val)
        
        if len(scores) == 0:
            return 0.0
        
        avg_score = sum(scores) / len(scores)
        # Ensure result is reasonable (z-scores should typically be between -3 and 3)
        if abs(avg_score) > 5:
            print(f"  [!] Warning: avg_score is extreme: {avg_score:.3f}, capping")
            avg_score = max(-3, min(3, avg_score))
        
        return float(avg_score) if not (pd.isna(avg_score) or np.isinf(avg_score)) else 0.0
        
    except Exception as e:
        print(f"  [!] Error calculating avg_score: {e}")
        import traceback
        traceback.print_exc()
        return 0.0


# --- Main Analysis Function ---
def analyze_stock(ticker, data, config):
    """
    Runs the full 12-factor analysis on a single stock's data.
    Returns the final z_avg score.
    """
    import sys  # Import sys for flush operations
    try:
        # Ensure we have enough data
        if len(data) < max(config['z_score_len'], config['pp_length'], config['hurst_length']):
            print(f"  [!] {ticker}: Insufficient data (have {len(data)} bars, need at least {max(config['z_score_len'], config['pp_length'], config['hurst_length'])} bars)")
            return None
            
        o = data['Open']
        h = data['High']
        l = data['Low']
        c = data['Close']
        vol = data['Volume'] if 'Volume' in data.columns else pd.Series(index=c.index, dtype=float).fillna(1.0)
        
        # Ensure all required columns exist
        required_cols = ['Open', 'High', 'Low', 'Close']
        if not all(col in data.columns for col in required_cols):
            print(f"  [!] {ticker}: Missing required columns. Available: {list(data.columns)}")
            return None
        
        # Select source data based on config
        kpss_src_data = data[config['kpss_src']]
        adf_src_data = data[config['adf_src']]
        corr_src_data = data[config['corr_src']]
        hurst_src_data = data[config['hurst_src']]
        pp_src_data = data[config['pp_src']]
        yang_src_data = data[config['yang_src']] # Using Close, as specified

        # 1. ADX
        print(f"    Calculating ADX...", flush=True)
        sys.stdout.flush()
        adx_value = calc_adx(h, l, c, config['di_length'], config['adx_smoothing'])
        z_adx = calc_zscore(adx_value, config['z_score_len'])
        
        # 2. KPSS - Calculate rolling KPSS values for z-scoring
        print(f"    Calculating KPSS...", flush=True)
        sys.stdout.flush()
        # Only calculate for the last window to match PineScript (which calculates on current bar)
        kpss_series = pd.Series(index=c.index, dtype=float)
        # Fill with NaN initially, then calculate only where we have enough data
        kpss_series[:] = np.nan
        for i in range(config['kpss_length'], len(kpss_src_data)):
            try:
                kpss_window = kpss_src_data.iloc[i-config['kpss_length']:i+1]  # Include current bar
                stat, _, _, _ = kpss(kpss_window, regression='c', nlags='auto')
                kpss_series.iloc[i] = stat
            except:
                kpss_series.iloc[i] = np.nan
        # Forward fill to create a series, but keep NaN for insufficient data
        kpss_series = kpss_series.ffill()
        # Replace NaN with 0 only for z-score calculation
        kpss_series_for_z = kpss_series.fillna(0.0)
        z_kpss = calc_zscore(kpss_series_for_z, config['z_score_len'])

        # 3. ADF - Calculate rolling ADF values for z-scoring
        print(f"    Calculating ADF...", flush=True)
        sys.stdout.flush()
        adf_series = pd.Series(index=c.index, dtype=float)
        adf_series[:] = np.nan
        for i in range(config['adf_length'], len(adf_src_data)):
            try:
                adf_window = adf_src_data.iloc[i-config['adf_length']:i+1]  # Include current bar
                result = adfuller(adf_window, maxlag=config['adf_nLag'], regression='c', autolag=None)
                adf_series.iloc[i] = result[0]
            except:
                adf_series.iloc[i] = np.nan
        adf_series = adf_series.ffill()
        adf_series_for_z = adf_series.fillna(0.0)
        z_adf = calc_zscore(adf_series_for_z, config['z_score_len'])
        
        # 4. GARCH
        print(f"    Calculating GARCH...", flush=True)
        sys.stdout.flush()
        garch_vol = calc_garch_vol(c, config['garch_alpha'], config['garch_beta'], config['garch_emaLen'])
        z_garch = calc_zscore(garch_vol, config['z_score_len'])
        
        # 5. Half-Life - Calculate rolling half-life values for z-scoring
        print(f"    Calculating Half-Life...", flush=True)
        sys.stdout.flush()
        halflife_series = pd.Series(index=c.index, dtype=float)
        halflife_series[:] = np.nan
        for i in range(config['halflife_lookback'], len(c)):
            try:
                halflife_val = calc_halflife(c.iloc[i-config['halflife_lookback']:i+1], config['halflife_lookback'])
                halflife_series.iloc[i] = halflife_val if not pd.isna(halflife_val) else np.nan
            except:
                halflife_series.iloc[i] = np.nan
        halflife_series = halflife_series.ffill()
        halflife_series_for_z = halflife_series.fillna(0.0)
        z_halflife = calc_zscore(halflife_series_for_z, config['z_score_len']) * -1 # Inverted
        
        # 6. Wavelet
        print(f"    Calculating Wavelet...", flush=True)
        sys.stdout.flush()
        wave_vol = calc_wavelet_vol(kpss_src_data, config['wavelet_alpha'], config['wavelet_len'])
        z_wave_vol = calc_zscore(wave_vol, config['z_score_len'])
        
        # 7. Price/Momentum Correlation
        print(f"    Calculating Price/Momentum Correlation...", flush=True)
        sys.stdout.flush()
        pmc_corr = calc_pmc_corr(corr_src_data, config['corr_mom_type'], config['corr_length'])
        z_pmc_corr = calc_zscore(pmc_corr, config['z_score_len'])

        # 8. Choppiness
        print(f"    Calculating Choppiness...", flush=True)
        sys.stdout.flush()
        chop_val = calc_chop(h, l, c, config['chop_length'])
        z_chop = calc_zscore(chop_val, config['z_score_len']) * -1 # Inverted
        
        # 9. Hurst - Calculate rolling Hurst values for z-scoring
        print(f"    Calculating Hurst (this may take a while)...", flush=True)
        sys.stdout.flush()
        hurst_series = pd.Series(index=c.index, dtype=float)
        hurst_series[:] = np.nan
        for i in range(config['hurst_length'], len(hurst_src_data)):
            try:
                hurst_window = hurst_src_data.iloc[i-config['hurst_length']:i+1]  # Include current bar
                H, _, _ = compute_Hc(hurst_window, kind='price', simplified=True)
                hurst_series.iloc[i] = H
            except:
                hurst_series.iloc[i] = np.nan
        hurst_series = hurst_series.ffill()
        hurst_series_for_z = hurst_series.fillna(0.0)
        z_hurst = calc_zscore(hurst_series_for_z, config['z_score_len'])
        
        # 10. ATR
        print(f"    Calculating ATR...", flush=True)
        sys.stdout.flush()
        atr_val = calc_atr(h, l, c, config['atr_length1'])
        z_atr = calc_zscore(atr_val, config['z_score_len'])
        
        # 11. Phillips-Perron - Calculate rolling PP values for z-scoring
        print(f"    Calculating Phillips-Perron (this may take a while)...", flush=True)
        sys.stdout.flush()
        pp_series = pd.Series(index=c.index, dtype=float)
        pp_series[:] = np.nan
        for i in range(config['pp_length'], len(pp_src_data)):
            try:
                pp_window = pp_src_data.iloc[i-config['pp_length']:i+1]  # Include current bar
                pp = PhillipsPerron(pp_window, lags=config['pp_nLag'], trend='c')
                pp_series.iloc[i] = pp.stat
            except:
                pp_series.iloc[i] = np.nan
        pp_series = pp_series.ffill()
        pp_series_for_z = pp_series.fillna(0.0)
        z_pp = calc_zscore(pp_series_for_z, config['z_score_len'])
        
        # 12. Yang Volatility
        yang_val = calc_yang_vol(o, h, l, c, config['yang_length'], config['yang_factor'])
        z_yang = calc_zscore(yang_val, config['z_score_len'])
        
        # Final Average Z-Score (Market Regime)
        z_scores = [z_adx, z_adf, z_kpss, z_atr, z_garch, z_halflife, 
                   z_wave_vol, z_pmc_corr, z_chop, z_hurst, z_pp, z_yang]
        
        # Filter out NaN values
        valid_scores = [z for z in z_scores if not pd.isna(z) and not np.isinf(z)]
        
        if len(valid_scores) == 0:
            print(f"  [!] {ticker}: All z-scores are invalid")
            return None
        
        z_avg = sum(valid_scores) / len(valid_scores)
        
        if pd.isna(z_avg) or np.isinf(z_avg):
            print(f"  [!] {ticker}: Final z_avg is invalid")
            return None
        
        # Calculate avg_score (Uptrend/Downtrend system)
        avg_score = calc_avg_score(c, vol, o, h, l, config)
        
        return {
            "z_avg": float(z_avg),  # Market Regime z-score
            "avg_score": float(avg_score)  # Uptrend/Downtrend z-score
        }

    except Exception as e:
        print(f"  [!] Error processing {ticker}: {e}")
        import traceback
        traceback.print_exc()
        return None


# --- Serve Dashboard HTML ---
@app.route('/')
def serve_dashboard():
    """Serve the dashboard HTML file"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'dashboard.html')

# --- Test endpoint ---
@app.route('/test', methods=['GET'])
def test_endpoint():
    """Simple test endpoint to verify server is running"""
    return jsonify({"status": "Server is running!", "message": "Flask backend is operational"})

# --- Health check endpoint for Render ---
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Render"""
    return jsonify({"status": "healthy", "service": "stocks-rsps-dashboard"}), 200

@app.route('/update-status', methods=['GET'])
def get_update_status():
    """Get daily update status and next update time"""
    global daily_update_status
    
    # Calculate next update time (13:00 today or tomorrow)
    now = datetime.now()
    next_update = now.replace(hour=13, minute=0, second=0, microsecond=0)
    if now >= next_update:
        # If it's past 13:00 today, next update is tomorrow at 13:00
        from datetime import timedelta
        next_update = next_update + timedelta(days=1)
    
    # Calculate time remaining
    time_remaining = next_update - now
    hours = int(time_remaining.total_seconds() // 3600)
    minutes = int((time_remaining.total_seconds() % 3600) // 60)
    
    return jsonify({
        "last_update_time": daily_update_status["last_update_time"].isoformat() if daily_update_status["last_update_time"] else None,
        "update_in_progress": daily_update_status["update_in_progress"],
        "update_completed": daily_update_status["update_completed"],
        "next_update_time": next_update.isoformat(),
        "time_remaining_hours": hours,
        "time_remaining_minutes": minutes
    })

# --- Status endpoint to check if /analyze is accessible ---
@app.route('/status', methods=['GET'])
def status_check():
    """Status check endpoint to verify server is responding"""
    return jsonify({
        "status": "online",
        "service": "stocks-rsps-dashboard",
        "endpoints": {
            "/analyze": "available",
            "/health": "available",
            "/test": "available"
        }
    }), 200

@app.route('/progress', methods=['GET'])
def get_progress():
    """Get current analysis progress"""
    global analysis_progress
    return jsonify(analysis_progress), 200

@app.route('/results', methods=['GET'])
def get_results():
    """Get cached analysis results if available"""
    global analysis_progress
    if analysis_progress["status"] == "complete" and analysis_progress["results"]:
        return jsonify(analysis_progress["results"]), 200
    else:
        return jsonify({
            "error": "Results not available",
            "status": analysis_progress["status"]
        }), 404

# --- Ratio Analysis and Backtesting Functions ---

def calculate_ratio_avg_score(ticker1, ticker2, config, data_cache=None):
    """Calculate avg_score for a ratio of two stocks (ticker1/ticker2)
    
    Args:
        ticker1: First stock ticker
        ticker2: Second stock ticker
        config: Configuration dictionary
        data_cache: Optional dictionary of pre-downloaded stock data {ticker: DataFrame}
    """
    try:
        # Use cached data if available, otherwise download
        if data_cache and ticker1 in data_cache and ticker2 in data_cache:
            data1 = data_cache[ticker1].copy()
            data2 = data_cache[ticker2].copy()
        else:
            # Fallback: download if cache not available
            print(f"    [!] Cache miss for {ticker1}/{ticker2}, downloading...", flush=True)
            data1 = download_stock_data(ticker1, period="2y", interval="1d", max_retries=3, delay=0.5)
            time.sleep(0.5)  # Delay between requests
            data2 = download_stock_data(ticker2, period="2y", interval="1d", max_retries=3, delay=0.5)
        
        if data1.empty or data2.empty:
            return None
        
        # Handle MultiIndex columns
        if isinstance(data1.columns, pd.MultiIndex):
            data1.columns = data1.columns.droplevel(1)
        if isinstance(data2.columns, pd.MultiIndex):
            data2.columns = data2.columns.droplevel(1)
        
        # Align data by date
        common_dates = data1.index.intersection(data2.index)
        if len(common_dates) < config['avg_score_z_len']:
            return None
        
        data1_aligned = data1.loc[common_dates]
        data2_aligned = data2.loc[common_dates]
        
        # Calculate ratio (ticker1 / ticker2)
        ratio_close = data1_aligned['Close'] / data2_aligned['Close']
        ratio_volume = (data1_aligned['Volume'] + data2_aligned['Volume']) / 2
        ratio_open = data1_aligned['Open'] / data2_aligned['Open']
        ratio_high = data1_aligned['High'] / data2_aligned['High']
        ratio_low = data1_aligned['Low'] / data2_aligned['Low']
        
        # Calculate avg_score for the ratio
        avg_score = calc_avg_score(ratio_close, ratio_volume, ratio_open, ratio_high, ratio_low, config)
        
        return avg_score
        
    except Exception as e:
        print(f"  [!] Error calculating ratio {ticker1}/{ticker2}: {e}")
        return None

def get_all_stock_tickers():
    """Get all unique stock tickers from all sectors"""
    all_tickers = []
    # Sort sectors for deterministic order
    for sector in sorted(SECTORS.keys()):
        tickers = SECTORS[sector]
        all_tickers.extend(tickers)
    # Remove duplicates while preserving order, then sort for full determinism
    seen = set()
    unique_tickers = []
    for ticker in all_tickers:
        if ticker not in seen:
            seen.add(ticker)
            unique_tickers.append(ticker)
    return sorted(unique_tickers)  # Sort for complete determinism

def calculate_stock_relative_scores(all_tickers, config, max_comparisons=50):
    """Calculate relative AS scores for each stock by comparing against others"""
    print("\n--- Calculating Relative Stock Scores via Ratio Analysis ---")
    
    stock_scores = {}
    total_comparisons = len(all_tickers) * (len(all_tickers) - 1) // 2
    
    # Limit comparisons to avoid too many API calls
    if total_comparisons > max_comparisons:
        # Use a subset - compare each stock against top 20 others
        comparison_tickers = all_tickers[:min(20, len(all_tickers))]
        print(f"  Using subset of {len(comparison_tickers)} stocks for comparison")
    else:
        comparison_tickers = all_tickers
    
    for i, ticker1 in enumerate(all_tickers):
        scores = []
        comparisons_made = 0
        
        for ticker2 in comparison_tickers:
            if ticker1 == ticker2:
                continue
            
            if comparisons_made >= 20:  # Limit comparisons per stock
                break
                
            ratio_score = calculate_ratio_avg_score(ticker1, ticker2, config)
            if ratio_score is not None:
                scores.append(ratio_score)
            comparisons_made += 1
        
        if scores:
            avg_relative_score = sum(scores) / len(scores)
            stock_scores[ticker1] = avg_relative_score
            print(f"  {ticker1}: {avg_relative_score:.3f} (from {len(scores)} comparisons)")
    
    return stock_scores

def perform_historical_backtest(top_stocks_with_scores, config, initial_capital=10000):
    """
    Perform historical backtest by rotating into best asset based on avg_score
    Uses historical data to calculate scores at each point in time
    """
    try:
        print("  Performing historical backtest...")
        
        # Get historical data for top stocks
        stock_data = {}
        all_dates = None
        
        # Extract tickers from (ticker, score) tuples
        # Sort for deterministic processing order
        top_stocks = sorted([ticker for ticker, _ in top_stocks_with_scores])
        
        for ticker in top_stocks:
            try:
                # Use helper function with rate limiting
                data = download_stock_data(ticker, period="2y", interval="1d", max_retries=3, delay=10.0)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    stock_data[ticker] = data
                    if all_dates is None:
                        all_dates = data.index
                    else:
                        # Use intersection but ensure deterministic order
                        all_dates = all_dates.intersection(data.index)
            except:
                continue
        
        if not stock_data or len(all_dates) < 50:
            return None
        
        # Sort dates - CRITICAL: Convert to list and sort for complete determinism
        # pandas Index intersection might not preserve exact order, so we explicitly sort
        all_dates = sorted(list(all_dates))
        
        # Determine minimum required bars (from analyze_stock requirements)
        min_required_bars = max(config.get('z_score_len', 100), 
                                config.get('pp_length', 240), 
                                config.get('hurst_length', 100),
                                config.get('avg_score_z_len', 100))
        
        # Start backtest after we have enough data
        start_index = min_required_bars + 50  # Extra buffer for calculations
        
        if start_index >= len(all_dates):
            print(f"  [!] Not enough historical data for backtest (need {start_index} bars, have {len(all_dates)})")
            return None
        
        print(f"  Starting backtest at index {start_index} (date: {all_dates[start_index]}) with {len(all_dates) - start_index} data points")
        
        # Calculate scores for each date (using rolling window)
        equity_curve = []
        current_asset = None
        entry_price = None
        entry_date = None
        base_equity = initial_capital  # Base equity (updated on exit)
        equity = initial_capital  # Current equity (includes unrealized gains)
        max_equity = initial_capital
        max_drawdown = 0.0
        hold_periods = []
        asset_periods = []
        previous_asset = None
        
        # Use weekly rebalancing to reduce computation
        rebalance_days = 5  # Rebalance every 5 days
        
        # Track pending rotation (signal detected, waiting for next day's open)
        pending_rotation = None
        pending_rotation_date = None
        pending_previous_asset = None  # Track previous asset for rotation display
        pending_previous_entry_price = None  # Store entry_price during transition
        pending_previous_entry_date = None  # Store entry_date during transition
        just_executed_rotation = False  # Track if we just executed a pending rotation this iteration
        
        for i in range(start_index, len(all_dates)):
            date = all_dates[i]
            just_executed_rotation = False  # Reset flag at start of each iteration
            
            # Check if we have a pending rotation to execute (enter on next day's open)
            if pending_rotation is not None and pending_rotation_date is not None:
                # Check if this is the next trading day after signal
                if date > pending_rotation_date:
                    # Execute pending rotation - enter on this day's open
                    rotation_occurred = True
                    just_executed_rotation = True  # Mark that we just executed a rotation
                    previous_asset = pending_previous_asset  # Use stored previous asset
                    current_asset = pending_rotation
                    
                    if pending_rotation is not None:
                        try:
                            asset_data = stock_data[current_asset]
                            date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                            if date_idx >= 0:
                                # Enter at open price (next day after signal confirmation)
                                entry_price = asset_data['Open'].iloc[date_idx]
                                entry_date = date  # CRITICAL: Set entry_date to TODAY (when we actually enter)
                                print(f"  [Entry] {current_asset} at ${entry_price:.2f} on {date.strftime('%Y-%m-%d')} (open) - entry_date={entry_date.strftime('%Y-%m-%d')}")
                                
                                # Store entry_date and entry_price on all future points of this trade
                                # This will be done after we append the current point to equity_curve
                                # We'll store it on all points until we exit
                        except Exception as e:
                            print(f"  [!] Error entering {pending_rotation}: {e}")
                            current_asset = None
                            entry_price = None
                            entry_date = None
                            rotation_occurred = False
                    
                    # Clear pending rotation
                    pending_rotation = None
                    pending_rotation_date = None
                    pending_previous_asset = None
                    pending_previous_entry_price = None
                    pending_previous_entry_date = None
                    
                    # CRITICAL: After entering, update previous_asset to current_asset for next rotation
                    # This ensures previous_asset is correct when we exit later
                    # We do this AFTER storing it on the rotation point (which happens later in the code)
                    # So we'll update it after we append the point
                else:
                    # Still waiting for next day - keep previous asset (not CASH) until we enter new one
                    rotation_occurred = False
                    # CRITICAL: Keep the previous asset throughout the transition period
                    # We haven't rotated yet - we're still holding the previous stock
                    # This ensures the transition period is counted as part of the current stock, not CASH
                    if pending_previous_asset:
                        current_asset = pending_previous_asset  # Keep showing the asset we're still holding
                        # Keep entry_price and entry_date from previous position
                        # Equity stays flat (base_equity) during this transition
                        # This makes the transition period part of the previous stock's period
                        # We're still in this stock - haven't rotated yet
                    else:
                        # No pending previous asset - this shouldn't happen during transition
                        # But if it does, we're in cash
                        current_asset = None
                        entry_price = None
                        entry_date = None
            
            # CRITICAL: Before processing this day, ensure current_asset is set correctly during transitions
            # During transition periods, we're still holding the previous stock (not CASH)
            if pending_rotation is not None and pending_previous_asset is not None:
                # We're in a transition - we haven't rotated yet, so we're still holding the previous asset
                # This ensures transition periods are counted as part of the current stock, not CASH
                current_asset = pending_previous_asset  # Force it to be the previous asset
                # Restore entry_price and entry_date from the previous position
                if pending_previous_entry_price is not None:
                    entry_price = pending_previous_entry_price
                if pending_previous_entry_date is not None:
                    entry_date = pending_previous_entry_date
                # We're still in this stock - haven't rotated yet
            
            # Only calculate scores on rebalance days
            if (i - start_index) % rebalance_days != 0:
                # Not a rebalance day - just update equity if we have a position
                if current_asset and entry_price:
                    try:
                        asset_data = stock_data[current_asset]
                        date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                        if date_idx >= 0:
                            current_price = asset_data['Close'].iloc[date_idx]
                            current_equity = base_equity * (current_price / entry_price)
                        else:
                            current_equity = base_equity
                    except:
                        current_equity = base_equity
                else:
                    current_equity = base_equity
                    current_price = None
                
                # Update max equity and drawdown
                if current_equity > max_equity:
                    max_equity = current_equity
                drawdown = (max_equity - current_equity) / max_equity if max_equity > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                # Record equity curve point
                entry_price_for_point = entry_price if current_asset else None
                entry_date_for_point = entry_date.strftime('%Y-%m-%d') if entry_date else None
                current_price_for_point = current_price if current_asset and entry_price else None
                
                # Mark if we're in a transition period
                is_transition = pending_rotation is not None
                
                # During transition, current_asset should ALWAYS be the previous asset (not CASH)
                # We haven't rotated yet - we're still holding the previous stock
                # current_asset should already be set to the previous asset by the check above
                if is_transition:
                    # During transition, we're still holding the previous stock
                    # NEVER use CASH during transitions - we're still in the previous stock
                    # Force use of pending_previous_asset if current_asset is somehow None
                    if pending_previous_asset and pending_previous_asset != 'CASH':
                        asset_for_display = pending_previous_asset  # Always use the previous asset during transition
                    elif current_asset and current_asset != 'CASH':
                        asset_for_display = current_asset
                    else:
                        # This should never happen - means logic error
                        asset_for_display = 'CASH'
                        print(f"  [!] ERROR: Both current_asset and pending_previous_asset are None/Invalid during transition on {date.strftime('%Y-%m-%d')}")
                        print(f"      pending_rotation={pending_rotation}, pending_previous_asset={pending_previous_asset}, current_asset={current_asset}")
                    print(f"  [Transition Day] {date.strftime('%Y-%m-%d')}: asset_for_display={asset_for_display}, current_asset={current_asset}, pending_previous_asset={pending_previous_asset}")
                else:
                    # Not in transition - use current_asset or CASH
                    asset_for_display = current_asset if current_asset else 'CASH'
                
                # Final safety check - ensure asset_for_display is never None or empty
                if not asset_for_display or asset_for_display == '':
                    print(f"  [!] CRITICAL ERROR: asset_for_display is None/empty on {date.strftime('%Y-%m-%d')}, forcing to pending_previous_asset={pending_previous_asset}")
                    asset_for_display = pending_previous_asset if pending_previous_asset else 'CASH'
                
                # Check for rotation marker on non-rebalance days too (when we execute pending rotations)
                # CRITICAL: Only show marker on the actual entry day, not on subsequent days
                rotation_asset = None
                rotation_to_show = False
                if rotation_occurred and current_asset and pending_rotation is None:
                    # Only show marker if we just executed a rotation OR entry_date matches today
                    # Do NOT use is_new_asset because it can stay True for multiple days
                    if just_executed_rotation or (entry_date is not None and entry_date == date):
                        rotation_asset = current_asset
                        rotation_to_show = True
                        print(f"  [Rotation Marker] Setting rotation=True for {current_asset} on {date.strftime('%Y-%m-%d')} (non-rebalance) - just_executed={just_executed_rotation}, entry_date={entry_date.strftime('%Y-%m-%d') if entry_date else 'None'}, entry_date_match={entry_date == date if entry_date else False}")
                
                equity_curve.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'equity': current_equity,
                    'asset': asset_for_display,
                    'rotation': rotation_to_show,
                    'rotation_asset': rotation_asset,
                    'previous_asset': previous_asset if rotation_occurred else None,
                    'entry_price': entry_price_for_point,
                    'entry_date': entry_date_for_point,
                    'current_price': current_price_for_point,
                    'exit_price': None,
                    'is_transition': is_transition
                })
                
                equity = current_equity
                continue
            
            # Rebalance day - calculate scores and check for rotation
            # Calculate current avg_score for each stock
            # Use sorted iteration to ensure deterministic order
            stock_scores = {}
            for ticker in sorted(stock_data.keys()):  # Sort for deterministic iteration
                data = stock_data[ticker]
                try:
                    # Get data up to current date (including current day's close)
                    historical_data = data.loc[data.index <= date]
                    if len(historical_data) < min_required_bars:
                        continue
                    
                    # Calculate avg_score
                    result = analyze_stock(ticker, historical_data, config)
                    if result:
                        stock_scores[ticker] = result.get('avg_score', 0.0)
                except Exception as e:
                    # Silently skip errors to avoid spam
                    continue
            
            if not stock_scores:
                # No scores available - just update equity
                if current_asset and entry_price:
                    try:
                        asset_data = stock_data[current_asset]
                        date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                        if date_idx >= 0:
                            current_price = asset_data['Close'].iloc[date_idx]
                            current_equity = base_equity * (current_price / entry_price)
                        else:
                            current_equity = base_equity
                    except:
                        current_equity = base_equity
                else:
                    current_equity = base_equity
                    current_price = None
                
                # Update max equity and drawdown
                if current_equity > max_equity:
                    max_equity = current_equity
                drawdown = (max_equity - current_equity) / max_equity if max_equity > 0 else 0
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
                
                entry_price_for_point = entry_price if current_asset else None
                entry_date_for_point = entry_date.strftime('%Y-%m-%d') if entry_date else None
                current_price_for_point = current_price if current_asset and entry_price else None
                
                # Check if this is the first entry after start (no previous rotations)
                is_first_entry = (current_asset is not None and entry_price is not None and 
                                i == start_index + 1 and not any(p.get('rotation') for p in equity_curve))
                
                # Mark if we're in a transition period
                is_transition = pending_rotation is not None
                
                # During transition, current_asset should ALWAYS be the previous asset (not CASH)
                # We haven't rotated yet - we're still holding the previous stock
                if is_transition:
                    # During transition, we're still holding the previous stock
                    # NEVER use CASH during transitions - we're still in the previous stock
                    # Force use of pending_previous_asset if current_asset is somehow None
                    if pending_previous_asset:
                        asset_for_display = pending_previous_asset  # Always use the previous asset during transition
                    elif current_asset:
                        asset_for_display = current_asset
                    else:
                        # This should never happen - means logic error
                        asset_for_display = 'CASH'
                        print(f"  [!] ERROR: Both current_asset and pending_previous_asset are None during transition on {date.strftime('%Y-%m-%d')}")
                else:
                    # Not in transition - use current_asset or CASH
                    asset_for_display = current_asset if current_asset else 'CASH'
                
                equity_curve.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'equity': current_equity,
                    'asset': asset_for_display,
                    'rotation': is_first_entry,  # Mark first entry as rotation
                    'rotation_asset': current_asset if is_first_entry else None,
                    'previous_asset': None,
                    'entry_price': entry_price_for_point,
                    'entry_date': entry_date_for_point,
                    'current_price': current_price_for_point,
                    'exit_price': None,
                    'is_transition': is_transition
                })
                
                equity = current_equity
                continue
            
            # Find best asset - but only if it has positive score
            # Use deterministic sorting: if scores are equal, prefer ticker with alphabetical order
            # This ensures consistent results across runs
            if stock_scores:
                sorted_scores = sorted(stock_scores.items(), key=lambda x: (x[1], x[0]), reverse=True)
                best_ticker, best_score = sorted_scores[0]
            else:
                best_ticker = None
                best_score = float('-inf')
            
            # Don't invest if all scores are negative
            if best_score < 0:
                best_ticker = None
                print(f"  [CASH Signal] All scores negative (best_score={best_score:.3f}), staying/entering CASH on {date.strftime('%Y-%m-%d')}")
            
            # Check if current asset goes negative - exit to cash
            if current_asset is not None and current_asset in stock_scores:
                current_asset_score = stock_scores[current_asset]
                if current_asset_score < 0:
                    # Current asset went negative - exit to cash
                    best_ticker = None
                    print(f"  [CASH Signal] Current asset {current_asset} went negative (score={current_asset_score:.3f}), exiting to CASH on {date.strftime('%Y-%m-%d')}")
            
            # Check if we need to rotate (signal detected on this day, will enter tomorrow)
            exit_price_recorded = None
            exit_date_recorded = None  # CRITICAL: Track exit date (when we exit at close)
            rotation_occurred = False
            exit_previous_asset = None  # Track asset we're exiting from
            
            # Determine if we need to rotate:
            # 1. We're in CASH and want to enter a stock (current_asset is None and best_ticker is not None)
            # 2. We want to rotate to a different stock (best_ticker != current_asset and both are not None)
            # 3. We want to exit to CASH (best_ticker is None and current_asset is not None)
            # NOTE: If we're already in CASH and all scores are negative (both None), we don't need to do anything
            needs_rotation = False
            if current_asset is None and best_ticker is not None:
                # We're in CASH and want to enter a stock
                needs_rotation = True
            elif current_asset is not None and best_ticker is not None and best_ticker != current_asset:
                # We want to rotate to a different stock
                needs_rotation = True
            elif best_ticker is None and current_asset is not None:
                # We want to exit to CASH
                needs_rotation = True
            
            if needs_rotation:
                # Signal detected on this day (at close) - exit current position, enter tomorrow at open
                exit_previous_asset = current_asset  # Remember what we're exiting from
                rotation_occurred = True
                
                # Close current position at today's close
                exit_date_recorded = None
                if current_asset is not None and entry_price is not None:
                    try:
                        prev_data = stock_data[current_asset]
                        prev_date_idx = prev_data.index.get_indexer([date], method='nearest')[0]
                        if prev_date_idx >= 0:
                            exit_price_recorded = prev_data['Close'].iloc[prev_date_idx]
                            exit_date_recorded = date  # CRITICAL: Store exit date (when we actually exit at close)
                            # Update base equity based on actual exit price
                            base_equity = base_equity * (exit_price_recorded / entry_price)
                            equity = base_equity  # Reset equity to base after exit
                            print(f"  [Exit] {current_asset} at ${exit_price_recorded:.2f} on {date.strftime('%Y-%m-%d')} (close) - exit_date={exit_date_recorded.strftime('%Y-%m-%d')}")
                            
                            if entry_date:
                                hold_days = (date - entry_date).days
                                hold_periods.append(hold_days)
                    except Exception as e:
                        print(f"  [!] Error exiting {current_asset}: {e}")
                
                # Set pending rotation - will enter on next day's open
                if best_ticker is not None:
                    pending_rotation = best_ticker
                    pending_rotation_date = date
                    # CRITICAL: If this is the first entry (current_asset is None), we don't have a previous asset
                    # In this case, we should enter immediately, not set up a transition
                    if current_asset is None:
                        # First entry - enter immediately, no transition needed
                        just_executed_rotation = True  # Mark that we just entered (first entry)
                        try:
                            asset_data = stock_data[best_ticker]
                            date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                            if date_idx >= 0:
                                entry_price = asset_data['Open'].iloc[date_idx]
                                entry_date = date
                                current_asset = best_ticker
                                previous_asset = None  # First entry, no previous asset
                                print(f"  [Entry] {current_asset} at ${entry_price:.2f} on {date.strftime('%Y-%m-%d')} (open) - first entry")
                                # Clear pending rotation since we entered immediately
                                pending_rotation = None
                                pending_rotation_date = None
                                pending_previous_asset = None
                                pending_previous_entry_price = None
                                pending_previous_entry_date = None
                        except Exception as e:
                            print(f"  [!] Error entering {best_ticker} on first entry: {e}")
                            rotation_occurred = False
                            just_executed_rotation = False
                    else:
                        # Not first entry - set up transition period
                        pending_previous_asset = exit_previous_asset  # Store for when we enter
                        # CRITICAL: Store entry_price and entry_date so we can restore them during transition
                        pending_previous_entry_price = entry_price  # Store entry_price from position we're exiting
                        pending_previous_entry_date = entry_date  # Store entry_date from position we're exiting
                        # CRITICAL: Keep current_asset as the previous asset throughout the transition
                        # This makes the transition period (from exit to entry) part of the current stock, not CASH
                        # We haven't rotated yet - we're still holding the previous stock until we enter the new one
                        previous_asset = exit_previous_asset
                        current_asset = exit_previous_asset  # Keep previous asset until entry - we're still in this stock
                        # CRITICAL: DO NOT clear entry_price or entry_date - we need them for the transition period
                        # entry_price and entry_date remain from the position we just exited
                        # The transition period will show as the previous asset, not CASH
                        # We're still holding this stock until we enter the new one at tomorrow's open
                    print(f"  [Signal] {best_ticker} detected on {date.strftime('%Y-%m-%d')}, will enter tomorrow at open")
                    print(f"  [Transition] Still holding {exit_previous_asset} during transition (not CASH)")
                    print(f"  [Transition] Preserved entry_price=${entry_price}, entry_date={entry_date}")
                    print(f"  [Transition] current_asset={current_asset}, pending_previous_asset={pending_previous_asset}")
                else:
                    # Exiting to cash - no pending entry
                    # CRITICAL: Store entry_price and asset before clearing them, so we can use them for trade_return_percent calculation
                    # This ensures we have the correct entry_price even when exiting to CASH
                    if exit_previous_asset and entry_price:
                        pending_previous_entry_price = entry_price
                        pending_previous_entry_date = entry_date
                        # Keep pending_previous_asset so we can match it when calculating trade_return_percent
                        # pending_previous_asset is already set to exit_previous_asset above, so we don't need to set it again
                    current_asset = None
                    entry_price = None
                    entry_date = None
                    pending_rotation = None
                    pending_rotation_date = None
                    # CRITICAL: Keep pending_previous_asset and pending_previous_entry_price when exiting to CASH
                    # so we can use them for trade_return_percent calculation
                    # Don't clear them here - they'll be cleared after we calculate trade_return_percent
                    print(f"  [Exit to CASH] on {date.strftime('%Y-%m-%d')}")
            else:
                rotation_occurred = False
            
            # CRITICAL: Before processing this day, ensure current_asset is set correctly during transitions
            # During transition periods, we're still holding the previous stock (not CASH)
            if pending_rotation is not None and pending_previous_asset is not None:
                # We're in a transition - we haven't rotated yet, so we're still holding the previous asset
                # This ensures transition periods are counted as part of the current stock, not CASH
                current_asset = pending_previous_asset  # Force it to be the previous asset
                # Restore entry_price and entry_date from the previous position
                if pending_previous_entry_price is not None:
                    entry_price = pending_previous_entry_price
                if pending_previous_entry_date is not None:
                    entry_date = pending_previous_entry_date
                # We're still in this stock - haven't rotated yet
            
            # Update equity if we have a position (keep flat if no position or during transition)
            # During transition (pending_rotation exists), keep equity flat even if we have current_asset
            if current_asset and entry_price and pending_rotation is None:
                # We have an active position (not in transition)
                try:
                    asset_data = stock_data[current_asset]
                    date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                    if date_idx >= 0:
                        current_price = asset_data['Close'].iloc[date_idx]
                        # Calculate equity based on base_equity and current price vs entry price
                        current_equity = base_equity * (current_price / entry_price)
                    else:
                        current_equity = base_equity
                except:
                    current_equity = base_equity
            else:
                # No position or in transition - keep equity flat (use base_equity)
                current_equity = base_equity
                current_price = None
            
            # Update max equity and drawdown
            if current_equity > max_equity:
                max_equity = current_equity
            drawdown = (max_equity - current_equity) / max_equity if max_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            
            # Record equity curve point with additional info for hover
            # CRITICAL: Only set entry_price and entry_date for the CURRENT asset (not during transition)
            # During transition, we're still holding the previous asset, so use its entry info
            if pending_rotation is not None and pending_previous_asset is not None:
                # In transition - use previous asset's entry info
                entry_price_for_point = pending_previous_entry_price if pending_previous_entry_price else None
                entry_date_for_point = pending_previous_entry_date.strftime('%Y-%m-%d') if pending_previous_entry_date else None
            else:
                # Not in transition - use current asset's entry info
                entry_price_for_point = entry_price if current_asset else None
                entry_date_for_point = entry_date.strftime('%Y-%m-%d') if entry_date else None
            
            current_price_for_point = current_price if current_asset and entry_price else None
            
            # If we just rotated out, use exit price and exit date; otherwise use current price
            exit_price_for_point = exit_price_recorded if rotation_occurred and exit_price_recorded else None
            exit_date_for_point = exit_date_recorded.strftime('%Y-%m-%d') if rotation_occurred and exit_date_recorded else None
            
            # Calculate return percentage and system performance for this trade if we just exited
            # Store this on ALL points of the trade period for easy access
            trade_return_percent = None
            trade_system_performance_percent = None
            # CRITICAL: When we exit, we need to use the entry_price from the position we're exiting
            # The entry_price used for the exit calculation (line 1691) is the correct one
            # We should use that same entry_price for calculating trade_return_percent
            # However, by the time we get here, entry_price might have been updated for a new position
            # So we need to use pending_previous_entry_price (which was set at exit time) or
            # calculate it from the equity change: base_equity was updated as base_equity * (exit_price / entry_price)
            # So entry_price = exit_price * base_equity_before / base_equity_after
            # But the simplest is to use pending_previous_entry_price which was captured at exit time
            exit_entry_price = None
            if exit_previous_asset:
                # CRITICAL: Use pending_previous_entry_price first (captured at exit time, line 1733)
                # This is the most reliable since it was captured exactly when we exited
                if pending_previous_entry_price:
                    exit_entry_price = pending_previous_entry_price
                # If not available (e.g., exiting to CASH), use entry_price if it matches the asset we're exiting
                elif entry_price and current_asset == exit_previous_asset:
                    exit_entry_price = entry_price
                else:
                    # Fallback: search backwards in equity_curve to find the entry_price for this asset
                    # Match by both asset and entry_date to ensure we get the correct trade
                    if exit_date_recorded:
                        entry_date_str = exit_date_recorded.strftime('%Y-%m-%d')
                        # Search for entry_price that matches this trade period
                        for j in range(len(equity_curve) - 1, -1, -1):
                            point = equity_curve[j]
                            if (point.get('asset') == exit_previous_asset and 
                                point.get('entry_price') and 
                                point.get('entry_date') and
                                point.get('entry_date') <= entry_date_str):
                                # Check if this entry_date is the most recent one before exit_date
                                exit_entry_price = point.get('entry_price')
                                break
                    else:
                        # No exit_date - just find the most recent entry_price for this asset
                        for j in range(len(equity_curve) - 1, -1, -1):
                            point = equity_curve[j]
                            if point.get('asset') == exit_previous_asset and point.get('entry_price'):
                                exit_entry_price = point.get('entry_price')
                                break
            
            if rotation_occurred and exit_price_recorded and exit_entry_price and exit_entry_price > 0:
                trade_return_percent = ((exit_price_recorded - exit_entry_price) / exit_entry_price) * 100
                
                # Calculate system performance: ((current_equity - initial_capital) / initial_capital * 100)
                # After exit, base_equity is updated to reflect the exit, so use that
                if initial_capital > 0:
                    trade_system_performance_percent = ((base_equity - initial_capital) / initial_capital) * 100
                
                # Store the return, system performance, exit_price, exit_date, entry_price, and entry_date on ALL points of the previous asset's trade period
                # This makes it accessible when hovering over any point in that trade
                if exit_previous_asset:
                    # Find all points that belong to this trade (same asset, not transition, between entry and exit)
                    # We'll store it on all points from the entry point to the exit point
                    entry_found = False
                    exit_date_str = exit_date_recorded.strftime('%Y-%m-%d') if exit_date_recorded else None
                    # Find entry_date for this trade (from pending_previous_entry_date or search backwards)
                    entry_date_str = None
                    if pending_previous_entry_date:
                        entry_date_str = pending_previous_entry_date.strftime('%Y-%m-%d')
                    else:
                        # Search backwards to find entry_date
                        for j in range(len(equity_curve) - 1, -1, -1):
                            point = equity_curve[j]
                            if point.get('asset') == exit_previous_asset and point.get('entry_date'):
                                entry_date_str = point.get('entry_date')
                                break
                            elif point.get('asset') != exit_previous_asset and point.get('asset') != 'CASH' and not point.get('is_transition', False):
                                break
                    
                    for j in range(len(equity_curve) - 1, -1, -1):
                        point = equity_curve[j]
                        # Check if this point belongs to the trade we just exited
                        if point.get('asset') == exit_previous_asset and not point.get('is_transition', False):
                            # This point is part of the trade - store ALL trade information
                            point['trade_return_percent'] = trade_return_percent
                            if trade_system_performance_percent is not None:
                                point['trade_system_performance_percent'] = trade_system_performance_percent
                            # Store exit_price and exit_date on all points of the trade
                            if exit_price_recorded:
                                point['exit_price'] = exit_price_recorded
                            if exit_date_str:
                                point['exit_date'] = exit_date_str
                            # Store entry_price and entry_date on all points of the trade
                            if exit_entry_price:
                                point['entry_price'] = exit_entry_price
                            if entry_date_str:
                                point['entry_date'] = entry_date_str
                            # Check if this is the entry point (has entry_price matching our exit_entry_price)
                            if point.get('entry_price') == exit_entry_price and not entry_found:
                                entry_found = True
                            # If we've found the entry point and moved past it, we can stop
                            # (we're going backwards, so once we pass the entry, we're done)
                        elif entry_found:
                            # We've passed all points of this trade, stop
                            break
                    
                    # After storing trade_return_percent on all points, clear pending_previous variables if we exited to CASH
                    # (if we entered a new position, they'll be cleared when we enter)
                    if exit_previous_asset and pending_rotation is None:
                        # We exited to CASH - clear the pending variables now that we've used them
                        pending_previous_asset = None
                        pending_previous_entry_price = None
                        pending_previous_entry_date = None
            
            # Update equity for next iteration (for max equity tracking)
            equity = current_equity
            
            # Determine rotation asset - show marker ONLY when actually entering a new asset
            # CRITICAL: Only show rotation marker when we actually ENTER (not when signal is detected)
            # rotation_occurred is True both when signal is detected AND when we enter
            # We only want to show the marker when we actually ENTER (current_asset changed to new asset)
            # IMPORTANT: We need to show rotation even if it's the same asset as a previous trade (e.g., JPM trade 1, then JPM trade 2)
            # The key indicator: if we executed a pending rotation today (pending_rotation was just cleared), we just entered
            rotation_asset = None
            rotation_to_show = False
            # Show rotation marker if:
            # 1. rotation_occurred is True (we detected a signal or entered)
            # 2. current_asset is set (we're entering a new asset, not exiting to cash)
            # 3. pending_rotation is None (we've actually entered, not just detected a signal)
            # 4. We just executed a rotation (just_executed_rotation is True) OR entry_date matches today OR this is a new asset
            # CRITICAL: Use just_executed_rotation flag to reliably detect when we just entered
            # CRITICAL: Also check if entry_date was just set to today (indicates we just entered)
            if rotation_occurred and current_asset and pending_rotation is None:
                # CRITICAL: Only show marker on the actual entry day, not on subsequent days
                # Only check if we just executed a rotation OR entry_date matches today
                # Do NOT use is_new_asset because it can stay True for multiple days after entry
                if just_executed_rotation or (entry_date is not None and entry_date == date):
                    # We just entered - show the marker
                    rotation_asset = current_asset
                    rotation_to_show = True
                    print(f"  [Rotation Marker] Setting rotation=True for {current_asset} on {date.strftime('%Y-%m-%d')} - just_executed={just_executed_rotation}, entry_date={entry_date.strftime('%Y-%m-%d') if entry_date else 'None'}, entry_date_match={entry_date == date if entry_date else False}")
                else:
                    print(f"  [Rotation Marker] NOT setting for {current_asset} on {date.strftime('%Y-%m-%d')} - just_executed={just_executed_rotation}, entry_date={entry_date.strftime('%Y-%m-%d') if entry_date else 'None'}, entry_date_match={entry_date == date if entry_date else False}")
            elif rotation_occurred and current_asset:
                print(f"  [Rotation Marker] NOT setting for {current_asset} on {date.strftime('%Y-%m-%d')} - pending_rotation={pending_rotation}")
            elif not rotation_occurred and current_asset:
                print(f"  [Rotation Marker] NOT setting for {current_asset} on {date.strftime('%Y-%m-%d')} - rotation_occurred=False")
            elif rotation_occurred and not current_asset:
                print(f"  [Rotation Marker] NOT setting - no current_asset on {date.strftime('%Y-%m-%d')}, rotation_occurred={rotation_occurred}")
            # When exiting to cash or just detecting a signal (pending_rotation exists), don't show marker
            
            # Mark if we're in a transition period (pending rotation exists)
            is_transition = pending_rotation is not None
            
            # During transition, current_asset should ALWAYS be the previous asset (not CASH)
            # We haven't rotated yet - we're still holding the previous stock
            # NEVER use CASH during transitions - we're still in the previous stock
            if is_transition:
                # During transition, we're still holding the previous stock
                # NEVER use CASH during transitions - we're still in the previous stock
                # Force use of pending_previous_asset if current_asset is somehow None
                if pending_previous_asset and pending_previous_asset != 'CASH':
                    asset_for_display = pending_previous_asset  # Always use the previous asset during transition
                elif current_asset and current_asset != 'CASH':
                    asset_for_display = current_asset
                else:
                    # This should never happen - means logic error
                    asset_for_display = 'CASH'
                    print(f"  [!] ERROR: Both current_asset and pending_previous_asset are None/Invalid during transition on {date.strftime('%Y-%m-%d')}")
                    print(f"      pending_rotation={pending_rotation}, pending_previous_asset={pending_previous_asset}, current_asset={current_asset}")
                print(f"  [Transition Day] {date.strftime('%Y-%m-%d')}: asset_for_display={asset_for_display}, current_asset={current_asset}, pending_previous_asset={pending_previous_asset}")
            else:
                # Not in transition - use current_asset or CASH
                asset_for_display = current_asset if current_asset else 'CASH'
                # Debug logging for CASH periods
                if asset_for_display == 'CASH':
                    print(f"  [CASH Period] {date.strftime('%Y-%m-%d')}: current_asset={current_asset}, best_ticker={best_ticker if 'best_ticker' in locals() else 'N/A'}, pending_rotation={pending_rotation}")
            
            # Final safety check - ensure asset_for_display is never None or empty
            if not asset_for_display or asset_for_display == '':
                print(f"  [!] CRITICAL ERROR: asset_for_display is None/empty on {date.strftime('%Y-%m-%d')}, forcing to pending_previous_asset={pending_previous_asset}")
                asset_for_display = pending_previous_asset if pending_previous_asset else 'CASH'
            
            # Store return and system performance on rotation point (where we enter new asset) - this point has previous_asset set
            # This ensures the return is always accessible when we have a rotation
            # Also store exit_date and exit_price for the previous asset on this rotation point
            rotation_point_return = None
            rotation_point_system_performance = None
            rotation_point_exit_price = None
            rotation_point_exit_date = None
            if rotation_occurred:
                if trade_return_percent is not None:
                    rotation_point_return = trade_return_percent
                    rotation_point_system_performance = trade_system_performance_percent
                # Store exit info for the previous asset on this rotation point
                if exit_price_recorded:
                    rotation_point_exit_price = exit_price_recorded
                if exit_date_recorded:
                    rotation_point_exit_date = exit_date_recorded.strftime('%Y-%m-%d')
            
            equity_curve.append({
                'date': date.strftime('%Y-%m-%d'),
                'equity': current_equity,
                'asset': asset_for_display,
                'rotation': rotation_to_show,  # Only mark rotation when entering an asset
                'rotation_asset': rotation_asset,  # Asset name to show on rotation marker (the asset we're entering)
                'previous_asset': previous_asset if rotation_occurred else None,
                'entry_price': entry_price_for_point,
                'entry_date': entry_date_for_point,
                'current_price': current_price_for_point,
                'exit_price': exit_price_for_point if exit_price_for_point else rotation_point_exit_price,  # Exit price for previous asset on rotation point
                'exit_date': exit_date_for_point if exit_price_for_point else rotation_point_exit_date,  # Exit date for previous asset on rotation point
                'trade_return_percent': rotation_point_return,  # Return percentage stored on rotation point (for previous_asset)
                'trade_system_performance_percent': rotation_point_system_performance,  # System performance stored on rotation point
                'is_transition': is_transition  # Flag to indicate we're in transition (not actual CASH)
            })
            
            # After appending the point, if we just entered a new asset, store entry_date and entry_price on ALL points of this trade
            # This ensures entry_date is available on all points of the trade period (same as exit_date)
            if rotation_occurred and current_asset and entry_date and entry_price:
                # We just entered a new asset - store entry_date and entry_price on the current point and all future points
                # until we exit (this will be updated when we exit, similar to how we store exit_date)
                entry_date_str = entry_date.strftime('%Y-%m-%d') if entry_date else None
                # Store on the current point (just appended)
                if len(equity_curve) > 0:
                    equity_curve[-1]['entry_date'] = entry_date_str
                    equity_curve[-1]['entry_price'] = entry_price
                # Future points will also have it set via entry_date_for_point as long as current_asset and entry_date remain set
                # But we'll also store it explicitly when we exit to ensure consistency
                
                # CRITICAL: Update previous_asset to current_asset after we've stored it on the rotation point
                # This ensures previous_asset is correct for the next rotation (when we exit)
                # The rotation point already has the correct previous_asset (the asset we exited from)
                # Now we update it so it's ready for the next exit
                # Only update if we actually just entered (just_executed_rotation is True)
                if just_executed_rotation:
                    previous_asset = current_asset
            
            # Use same logic for asset_periods
            if is_transition:
                # During transition, we're still holding the previous stock
                # current_asset should already be set to the previous asset
                asset_for_periods = current_asset if current_asset else pending_previous_asset
                if asset_for_periods is None:
                    asset_for_periods = 'CASH'  # Fallback (shouldn't happen)
            else:
                # Not in transition - use current_asset or CASH
                asset_for_periods = current_asset if current_asset else 'CASH'
            
            asset_periods.append({
                'date': date.strftime('%Y-%m-%d'),
                'asset': asset_for_periods,
                'equity': current_equity,
                'rotation': rotation_occurred
            })
        
        # Calculate statistics
        max_hold = max(hold_periods) if hold_periods else 0
        min_hold = min(hold_periods) if hold_periods else 0
        avg_hold = sum(hold_periods) / len(hold_periods) if hold_periods else 0
        num_trades = len(hold_periods)
        current_best = current_asset if current_asset else "N/A"
        final_equity = equity_curve[-1]['equity'] if equity_curve else initial_capital
        
        # Fetch S&P 500 data for comparison (automatically cached like other stocks)
        sp500_data = None
        sp500_returns = []
        try:
            print("  Fetching S&P 500 data for comparison...")
            # Use download_stock_data which automatically handles caching and updates
            sp500 = download_stock_data("^GSPC", period="3y", interval="1d", max_retries=3, delay=0.5, use_cache=True)
            
            if not sp500.empty:
                # Handle MultiIndex columns
                if isinstance(sp500.columns, pd.MultiIndex):
                    sp500 = sp500.droplevel(0, axis=1)
                
                if 'Close' in sp500.columns:
                    sp500_close = sp500['Close']
                    sp500_dates = pd.to_datetime(sp500.index)
                    
                    # Calculate S&P 500 returns (percentage from backtest start date)
                    # Use 2025-01-22 as the base date for percentage calculation
                    base_date = pd.Timestamp('2025-01-22')
                    if len(sp500_close) > 0 and len(all_dates) > start_index:
                        # Find S&P 500 price at base date (2025-01-22)
                        sp500_base_idx = sp500_dates.get_indexer([base_date], method='nearest')[0]
                        if sp500_base_idx >= 0 and sp500_base_idx < len(sp500_close):
                            sp500_base_price = sp500_close.iloc[sp500_base_idx]
                            base_date_actual = sp500_dates.iloc[sp500_base_idx]
                            print(f"  S&P 500 base price: ${sp500_base_price:.2f} on {base_date_actual.strftime('%Y-%m-%d')}")
                            
                            for date in all_dates[start_index:]:
                                # Find closest date in S&P 500 data
                                date_idx = sp500_dates.get_indexer([date], method='nearest')[0]
                                if date_idx >= 0 and date_idx < len(sp500_close):
                                    sp500_price = sp500_close.iloc[date_idx]
                                    sp500_return = ((sp500_price - sp500_base_price) / sp500_base_price) * 100
                                    sp500_returns.append({
                                        'date': date.strftime('%Y-%m-%d'),
                                        'return': sp500_return
                                    })
                                else:
                                    # Use last known value or 0
                                    sp500_returns.append({
                                        'date': date.strftime('%Y-%m-%d'),
                                        'return': 0
                                    })
                        else:
                            print(f"  [!] Could not find S&P 500 base price for {base_date}")
                    else:
                        print(f"  [!] Insufficient S&P 500 data: {len(sp500_close)} prices, {len(all_dates)} dates, start_index={start_index}")
            else:
                print("  [!] S&P 500 data is empty")
        except Exception as e:
            print(f"  [!] Error fetching S&P 500 data: {e}")
            import traceback
            traceback.print_exc()
        
        return {
            'equity_curve': equity_curve,
            'asset_periods': asset_periods,
            'max_drawdown': max_drawdown * 100,
            'max_hold_period': max_hold,
            'min_hold_period': min_hold,
            'avg_hold_period': round(avg_hold, 1),
            'num_trades': num_trades,
            'current_best_asset': current_best,
            'final_equity': final_equity,
            'total_return': ((final_equity - initial_capital) / initial_capital) * 100,
            'initial_capital': initial_capital,
            'sp500_returns': sp500_returns
        }
        
    except Exception as e:
        print(f"  [!] Error in historical backtest: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_backtest_incrementally(existing_backtest, top_stocks_with_scores, config, initial_capital=10000):
    """
    Update existing backtest with new day's data (incremental update).
    Only processes new dates since last backtest date.
    """
    try:
        if not existing_backtest or 'equity_curve' not in existing_backtest:
            print("  [!] No existing backtest found, performing full backtest...")
            return perform_historical_backtest(top_stocks_with_scores, config, initial_capital)
        
        print("  Updating backtest incrementally...")
        
        # Get last date from existing backtest
        existing_equity_curve = existing_backtest.get('equity_curve', [])
        if not existing_equity_curve:
            print("  [!] Empty equity curve, performing full backtest...")
            return perform_historical_backtest(top_stocks_with_scores, config, initial_capital)
        
        last_date_str = existing_equity_curve[-1].get('date')
        if not last_date_str:
            print("  [!] Could not find last date, performing full backtest...")
            return perform_historical_backtest(top_stocks_with_scores, config, initial_capital)
        
        last_date = datetime.strptime(last_date_str, '%Y-%m-%d').date()
        today = datetime.now().date()
        
        # Check if we need to update (if last date is today or yesterday, no update needed)
        if last_date >= today - timedelta(days=1):
            print(f"  ✓ Backtest is up to date (last date: {last_date_str})")
            return existing_backtest
        
        print(f"  Last backtest date: {last_date_str}, updating to today...")
        
        # Get historical data for new dates only
        top_stocks = [ticker for ticker, _ in top_stocks_with_scores]
        stock_data = {}
        all_new_dates = None
        
        for ticker in top_stocks:
            try:
                # Download data from last_date to today
                start_date = last_date + timedelta(days=1)
                end_date = today + timedelta(days=1)  # Include today
                data = download_stock_data(ticker, start=start_date, end=end_date, interval="1d", max_retries=3, delay=5.0)
                if not data.empty:
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    # Filter to only new dates (after last_date)
                    if hasattr(data.index, 'date'):
                        new_data = data[data.index.date > last_date]
                    else:
                        # If index is already date, compare directly
                        new_data = data[data.index > pd.Timestamp(last_date)]
                    if not new_data.empty:
                        stock_data[ticker] = new_data
                        if all_new_dates is None:
                            all_new_dates = new_data.index
                        else:
                            all_new_dates = all_new_dates.intersection(new_data.index)
            except Exception as e:
                print(f"  [!] Error downloading {ticker}: {e}")
                continue
        
        if not stock_data or len(all_new_dates) == 0:
            print("  [!] No new data available, returning existing backtest")
            return existing_backtest
        
        # Sort new dates
        all_new_dates = sorted(all_new_dates)
        print(f"  Processing {len(all_new_dates)} new trading days...")
        
        # Get state from last equity curve point
        last_point = existing_equity_curve[-1]
        current_equity = last_point.get('equity', initial_capital)
        base_equity = current_equity
        max_equity = max([p.get('equity', initial_capital) for p in existing_equity_curve], default=initial_capital)
        max_drawdown = existing_backtest.get('max_drawdown', 0) / 100  # Convert from percentage
        
        # Reconstruct current position from last point
        current_asset = last_point.get('asset')
        entry_price = last_point.get('entry_price')
        entry_date_str = last_point.get('entry_date')
        entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date() if entry_date_str else None
        
        # Continue from existing equity curve
        new_equity_curve = existing_equity_curve.copy()
        asset_periods = existing_backtest.get('asset_periods', []).copy()
        hold_periods = [p.get('hold_days', 0) for p in asset_periods]
        
        # Process new dates (simplified - just update equity based on current position)
        for date in all_new_dates:
            date_obj = date.date() if hasattr(date, 'date') else date
            
            # Update equity if we have a position
            if current_asset and entry_price and current_asset != 'CASH':
                try:
                    asset_data = stock_data[current_asset]
                    date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                    if date_idx >= 0:
                        current_price = asset_data['Close'].iloc[date_idx]
                        current_equity = base_equity * (current_price / entry_price)
                    else:
                        current_equity = base_equity
                except:
                    current_equity = base_equity
            else:
                current_equity = base_equity
            
            # Update max equity and drawdown
            if current_equity > max_equity:
                max_equity = current_equity
            drawdown = (max_equity - current_equity) / max_equity if max_equity > 0 else 0
            if drawdown > max_drawdown:
                max_drawdown = drawdown
            
            # Add new point to equity curve
            new_equity_curve.append({
                'date': date_obj.strftime('%Y-%m-%d'),
                'equity': current_equity,
                'asset': current_asset if current_asset else 'CASH',
                'rotation': False,  # No rotations in incremental update (would need full recalculation)
                'rotation_asset': None,
                'previous_asset': None,
                'entry_price': entry_price,
                'entry_date': entry_date_str if entry_date else None,
                'current_price': current_price if current_asset and entry_price else None,
                'exit_price': None,
                'is_transition': False
            })
        
        # Recalculate statistics
        final_equity = new_equity_curve[-1].get('equity', initial_capital)
        total_return = ((final_equity - initial_capital) / initial_capital) * 100
        
        # Update S&P 500 returns if needed
        sp500_returns = existing_backtest.get('sp500_returns', 0)
        
        # Recalculate average hold period and number of trades from asset_periods
        hold_periods_from_asset = [p.get('hold_days', 0) for p in asset_periods if p.get('hold_days', 0) > 0]
        avg_hold = sum(hold_periods_from_asset) / len(hold_periods_from_asset) if hold_periods_from_asset else existing_backtest.get('avg_hold_period', 0)
        num_trades = len(hold_periods_from_asset) if hold_periods_from_asset else existing_backtest.get('num_trades', 0)
        
        return {
            'equity_curve': new_equity_curve,
            'asset_periods': asset_periods,  # Keep existing periods
            'max_drawdown': max_drawdown * 100,
            'max_hold_period': existing_backtest.get('max_hold_period', 0),
            'min_hold_period': existing_backtest.get('min_hold_period', 0),
            'avg_hold_period': round(avg_hold, 1),
            'num_trades': num_trades,
            'current_best_asset': current_asset if current_asset else 'CASH',
            'final_equity': final_equity,
            'total_return': total_return,
            'initial_capital': initial_capital,
            'sp500_returns': sp500_returns
        }
        
    except Exception as e:
        print(f"  [!] Error in incremental backtest update: {e}")
        import traceback
        traceback.print_exc()
        # Fall back to full backtest
        return perform_historical_backtest(top_stocks_with_scores, config, initial_capital)

def backtest_rotation_strategy(stock_scores_history, initial_capital=10000):
    """
    Backtest rotation strategy: rotate into best asset on 1D confirmation
    stock_scores_history: list of dicts with {'date': date, 'scores': {ticker: score}}
    """
    equity_curve = []
    current_asset = None
    entry_price = None
    entry_date = None
    equity = initial_capital
    max_equity = initial_capital
    max_drawdown = 0.0
    hold_periods = []
    current_hold_days = 0
    
    asset_periods = []  # Track which asset was held during each period
    
    # Get all dates
    all_dates = sorted(set([item['date'] for item in stock_scores_history]))
    
    for i, date in enumerate(all_dates):
        # Get scores for this date
        date_scores = next((item['scores'] for item in stock_scores_history if item['date'] == date), {})
        
        if not date_scores:
            continue
        
        # Find best asset for this date
        # Use deterministic sorting: if scores are equal, prefer ticker with alphabetical order
        if date_scores:
            sorted_scores = sorted(date_scores.items(), key=lambda x: (x[1], x[0]), reverse=True)
            best_ticker = sorted_scores[0][0]
        else:
            best_ticker = None
        
        # Check if we need to rotate (on new day, if best asset changed)
        if current_asset is None or (best_ticker != current_asset and i > 0):
            # Close previous position
            if current_asset is not None and entry_price is not None:
                # Get exit price (use current day's price)
                try:
                    # Get data for the specific date (use date and next day to ensure we get the date)
                    exit_data = download_stock_data(current_asset, start=date, end=date + timedelta(days=1), interval="1d", max_retries=3, delay=0.3)
                    if not exit_data.empty:
                        if isinstance(exit_data.columns, pd.MultiIndex):
                            exit_data.columns = exit_data.columns.droplevel(1)
                        exit_price = exit_data['Close'].iloc[0]
                        # Update equity
                        equity = equity * (exit_price / entry_price)
                        
                        # Record hold period
                        if entry_date:
                            hold_days = (date - entry_date).days
                            hold_periods.append(hold_days)
                except:
                    pass
            
            # Enter new position
            current_asset = best_ticker
            try:
                # Get data for the specific date
                entry_data = download_stock_data(current_asset, start=date, end=date + timedelta(days=1), interval="1d", max_retries=3, delay=0.3)
                if not entry_data.empty:
                    if isinstance(entry_data.columns, pd.MultiIndex):
                        entry_data.columns = entry_data.columns.droplevel(1)
                    entry_price = entry_data['Close'].iloc[0]
                    entry_date = date
                    current_hold_days = 0
            except:
                current_asset = None
                entry_price = None
        
        if current_asset:
            current_hold_days += 1
        
        # Update max equity and drawdown
        if equity > max_equity:
            max_equity = equity
        drawdown = (max_equity - equity) / max_equity if max_equity > 0 else 0
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        
        # Record equity curve point
        equity_curve.append({
            'date': date,
            'equity': equity,
            'asset': current_asset,
            'hold_days': current_hold_days
        })
        
        asset_periods.append({
            'date': date,
            'asset': current_asset,
            'equity': equity
        })
    
    # Calculate statistics
    max_hold = max(hold_periods) if hold_periods else 0
    min_hold = min(hold_periods) if hold_periods else 0
    avg_hold = sum(hold_periods) / len(hold_periods) if hold_periods else 0
    num_trades = len(hold_periods)
    current_best = current_asset if current_asset else "N/A"
    
    return {
        'equity_curve': equity_curve,
        'asset_periods': asset_periods,
        'max_drawdown': max_drawdown * 100,  # As percentage
        'max_hold_period': max_hold,
        'min_hold_period': min_hold,
        'avg_hold_period': round(avg_hold, 1),
        'num_trades': num_trades,
        'current_best_asset': current_best,
        'final_equity': equity,
        'total_return': ((equity - initial_capital) / initial_capital) * 100
    }

# --- NEW API ENDPOINT ---
# Cache file path
# Cache file path - tries to use persistent volume if available
# On Fly.io free tier, storage is ephemeral (lost on restart)
# To use persistent storage, create a volume: fly volumes create cache_data --size 1 --region fra
# Then mount it in fly.toml and use /data/cache.json
# Use app directory for cache (more persistent than /tmp on Render)
# Render free plan: app directory persists better than /tmp
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(APP_DIR, '.cache')
os.makedirs(CACHE_DIR, exist_ok=True)

if os.path.exists('/data'):
    CACHE_FILE = '/data/analysis_cache.json'
    STOCK_DATA_CACHE_DIR = '/data/stock_data_cache'
else:
    # Use app directory cache (more persistent on Render free plan)
    CACHE_FILE = os.path.join(CACHE_DIR, 'analysis_cache.json')
    STOCK_DATA_CACHE_DIR = os.path.join(CACHE_DIR, 'stock_data_cache')

# Create stock data cache directory if it doesn't exist
os.makedirs(STOCK_DATA_CACHE_DIR, exist_ok=True)

# Initialize Supabase client for persistent checkpoint storage
supabase_client = None
if SUPABASE_AVAILABLE:
    supabase_url = os.environ.get('SUPABASE_URL', '').strip()
    supabase_key = os.environ.get('SUPABASE_KEY', '').strip()
    
    # Debug: Check what we got (without printing sensitive key)
    if not supabase_url:
        print("  ⚠ SUPABASE_URL environment variable is missing or empty")
    if not supabase_key:
        print("  ⚠ SUPABASE_KEY environment variable is missing or empty")
    
    if supabase_url and supabase_key:
        try:
            supabase_client = create_client(supabase_url, supabase_key)
            print(f"  ✓ Supabase client initialized for checkpoint storage")
            print(f"  ✓ Connected to: {supabase_url}")
        except Exception as e:
            print(f"  ⚠ Failed to initialize Supabase: {e}")
            import traceback
            traceback.print_exc()
            supabase_client = None
    else:
        print("  ⚠ Supabase credentials not found in environment variables")
        print("  ℹ Checkpoints will use local storage only")
        print("  ℹ To enable Supabase:")
        print("     1. Go to Render Dashboard → Your Service → Environment tab")
        print("     2. Add SUPABASE_URL = https://fzuxkphassgtvfiupixv.supabase.co")
        print("     3. Add SUPABASE_KEY = your_anon_key")
        print("     4. Click 'Save Changes'")
        print("     5. Manually redeploy the service")
else:
    print("  ⚠ Supabase library not available - install with: pip install supabase")

def save_checkpoint_to_supabase(data):
    """Save checkpoint data to Supabase database"""
    if not supabase_client:
        return False
    
    try:
        # Prepare data for Supabase
        # Note: Supabase JSONB column can store JSON directly, but we'll use JSON string for compatibility
        checkpoint_data = {
            "id": "main_checkpoint",  # Single checkpoint record
            "data": json.dumps(data, default=str),  # Store as JSON string
            "updated_at": datetime.now().isoformat(),
            "stage": data.get("_stage", "unknown"),
            "is_partial": data.get("_partial", False)
        }
        
        # Upsert (insert or update) the checkpoint
        # Use insert with on_conflict for upsert behavior
        try:
            result = supabase_client.table("checkpoints").upsert(
                checkpoint_data,
                on_conflict="id"
            ).execute()
        except Exception as upsert_error:
            # Fallback: try insert, then update if exists
            try:
                supabase_client.table("checkpoints").insert(checkpoint_data).execute()
            except:
                # Update if insert fails (record exists)
                supabase_client.table("checkpoints").update({
                    "data": checkpoint_data["data"],
                    "updated_at": checkpoint_data["updated_at"],
                    "stage": checkpoint_data["stage"],
                    "is_partial": checkpoint_data["is_partial"]
                }).eq("id", "main_checkpoint").execute()
        
        print(f"  ✓ Checkpoint saved to Supabase database", flush=True)
        return True
    except Exception as e:
        print(f"  ⚠ Failed to save checkpoint to Supabase: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return False

def load_checkpoint_from_supabase():
    """Load checkpoint data from Supabase database"""
    if not supabase_client:
        return None
    
    try:
        result = supabase_client.table("checkpoints").select("*").eq("id", "main_checkpoint").execute()
        
        if result.data and len(result.data) > 0:
            checkpoint_record = result.data[0]
            # Parse JSON string back to dict
            data = json.loads(checkpoint_record["data"])
            print(f"  ✓ Checkpoint loaded from Supabase (stage: {checkpoint_record.get('stage', 'unknown')})")
            return data
        else:
            print(f"  ℹ No checkpoint found in Supabase")
            return None
    except Exception as e:
        print(f"  ⚠ Failed to load checkpoint from Supabase: {e}")
        return None

def trigger_auto_redeploy(stage):
    """
    Save checkpoint to a file that will be committed to trigger auto-redeploy.
    Note: On Render, we can't commit directly, but we can save to a location
    that will be picked up on the next manual deploy or we can use Render API.
    For now, we'll save checkpoint data to a file and log instructions.
    """
    try:
        import datetime
        
        # Save checkpoint marker file (this will be in the container, not committed)
        # The actual cache is saved separately via save_cache()
        checkpoint_marker = os.path.join(CACHE_DIR, 'checkpoint_marker.json')
        marker_data = {
            "stage": stage,
            "timestamp": datetime.datetime.now().isoformat(),
            "message": "Checkpoint saved - manual redeploy needed or wait for auto-redeploy"
        }
        with open(checkpoint_marker, 'w') as f:
            json.dump(marker_data, f, indent=2)
        
        print(f"  💡 To trigger auto-redeploy:", flush=True)
        print(f"     1. The checkpoint is saved in: {CACHE_FILE}", flush=True)
        print(f"     2. On Render dashboard, click 'Manual Deploy' to resume", flush=True)
        print(f"     3. Or wait for the next automatic deployment", flush=True)
        return True
    except Exception as e:
        print(f"  ⚠ Checkpoint marker save failed: {e}", flush=True)
        return False

def load_cache():
    """Load analysis results from cache file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                data = json.load(f)
                print(f"  ✓ Cache file found: {CACHE_FILE} ({os.path.getsize(CACHE_FILE)} bytes)")
                return data
        except Exception as e:
            print(f"  [!] Error loading cache: {e}")
            return None
    else:
        print(f"  ℹ No cache file found at {CACHE_FILE}")
    return None

def save_cache(data, is_partial=False, stage=None, processed_tickers=None):
    """
    Save analysis results to cache file
    
    Args:
        data: The data dictionary to save
        is_partial: If True, marks this as a partial checkpoint
        stage: Current stage (e.g., "downloading", "stock_analysis", "ratio_analysis", "backtesting")
        processed_tickers: List of tickers already processed (for resuming)
    """
    try:
        # Ensure directory exists
        cache_dir = os.path.dirname(CACHE_FILE)
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        
        # Add checkpoint metadata
        if is_partial:
            data["_partial"] = True
            data["_stage"] = stage
            data["_checkpoint_time"] = time.time()
            if processed_tickers:
                data["_processed_tickers"] = processed_tickers
            print(f"  ⚠ Saving PARTIAL checkpoint at stage: {stage}", flush=True)
        else:
            data["_partial"] = False
        
        # Save to local file
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        file_size = os.path.getsize(CACHE_FILE)
        print(f"  ✓ Cache saved to {CACHE_FILE} ({file_size} bytes)", flush=True)
        
        # Also save to Supabase for persistence across deployments
        if supabase_client:
            save_checkpoint_to_supabase(data)
    except Exception as e:
        print(f"  [!] Error saving cache: {e}", flush=True)

def run_analysis_logic(force_refresh=False):
    """
    Core analysis logic that can be called from HTTP endpoint or background thread.
    Returns the response data dictionary.
    """
    global analysis_progress, analysis_lock  # Declare global at function level
    import time
    import sys
    
    # Check if analysis is already running
    if not analysis_lock.acquire(blocking=False):
        # Analysis already running, return current progress
        if analysis_progress["status"] in ["downloading", "analyzing", "ratio_analysis", "backtesting"]:
            raise Exception("Analysis already in progress. Please wait for it to complete.")
        # If not running, try to acquire lock
        analysis_lock.acquire()
    
    try:
        start_time = time.time()
        # RENDER FREE PLAN TIMEOUT: 15 minutes = 900 seconds
        # Save checkpoint at 14 minutes (840 seconds) to allow time for save and graceful exit
        RENDER_TIMEOUT_SECONDS = 840  # 14 minutes
        checkpoint_saved = False
        
        # Force flush to ensure logs appear immediately
        print(f"\n{'='*60}", flush=True)
        print(f"Received request at /analyze endpoint (PID: {os.getpid()})...", flush=True)
        print(f"⚠ RENDER FREE PLAN: Will save checkpoint at {RENDER_TIMEOUT_SECONDS}s (14 minutes)", flush=True)
        print(f"{'='*60}", flush=True)
        sys.stdout.flush()
        
        # Initialize progress tracking
        analysis_progress = {
            "status": "downloading",
            "stage": "Initializing",
            "current": 0,
            "total": 0,
            "message": "Starting analysis...",
            "start_time": time.time(),
            "last_update": time.time(),
            "results": None,
            "error": None
        }
        
        def check_timeout_and_save_checkpoint(current_stage, current_data=None, processed_tickers=None):
            """Check if we've hit the timeout and save checkpoint if needed"""
            nonlocal checkpoint_saved
            elapsed = time.time() - start_time
            if elapsed >= RENDER_TIMEOUT_SECONDS and not checkpoint_saved:
                checkpoint_saved = True
                print(f"\n{'='*60}", flush=True)
                print(f"⚠ TIMEOUT APPROACHING: {elapsed:.1f}s elapsed (limit: {RENDER_TIMEOUT_SECONDS}s)", flush=True)
                print(f"💾 Saving checkpoint at stage: {current_stage}", flush=True)
                print(f"{'='*60}\n", flush=True)
                
                # Prepare checkpoint data
                checkpoint_data = current_data if current_data else {}
                checkpoint_data["_checkpoint_elapsed"] = elapsed
                checkpoint_data["_checkpoint_timestamp"] = datetime.now().isoformat()
                
                # Save checkpoint
                save_cache(checkpoint_data, is_partial=True, stage=current_stage, processed_tickers=processed_tickers)
                
                # Try to trigger auto-redeploy by updating a trigger file
                try:
                    trigger_auto_redeploy(current_stage)
                except Exception as e:
                    print(f"  ⚠ Could not trigger auto-redeploy: {e}", flush=True)
                    print(f"  💡 Manual redeploy: Go to Render dashboard and click 'Manual Deploy'", flush=True)
                
                print(f"\n✓ Checkpoint saved successfully. Exiting gracefully...", flush=True)
                print(f"🔄 Next deployment will resume from: {current_stage}", flush=True)
                sys.stdout.flush()
                
                # Return True to indicate checkpoint was saved
                return True
            return False
        
        # Try to load from cache first (unless force refresh)
        resume_from_stage = None
        if not force_refresh:
            cached_data = load_cache()
            if cached_data:
                # Check if it's a complete cache
                if not cached_data.get("_partial", False):
                    elapsed = time.time() - start_time
                    print(f"✓ Loading data from cache... (took {elapsed:.2f}s)")
                    analysis_progress["status"] = "complete"
                    analysis_progress["results"] = cached_data
                    analysis_progress["message"] = "Loaded from cache"
                    return cached_data  # Return dict, not jsonify
                else:
                    # Partial cache - resume from checkpoint
                    resume_from_stage = cached_data.get("_stage", None)
                    print(f"✓ Found partial cache - resuming from stage: {resume_from_stage}")
                    if resume_from_stage == "stock_analysis_complete":
                        print("  Resuming from ratio analysis (stock analysis already complete)")
                    elif resume_from_stage == "ratio_analysis_complete":
                        print("  Resuming from backtesting (stock and ratio analysis already complete)")
        
        if force_refresh:
            print("  Force refresh requested - recalculating all values...")
        elif resume_from_stage:
            print(f"  Resuming analysis from checkpoint: {resume_from_stage}...")
        else:
            print("  No cache found - calculating fresh data (this may take 3-5 minutes)...")
        
        # Collect all tickers first
        # Sort sectors for deterministic order
        all_tickers = []
        ticker_to_sector = {}
        for sector in sorted(SECTORS.keys()):
            tickers = SECTORS[sector]
            # Sort tickers within each sector for determinism
            for ticker in sorted(tickers):
                all_tickers.append(ticker)
                ticker_to_sector[ticker] = sector
        
        # Check if we should skip download (resuming from checkpoint)
        if resume_from_stage in ["stock_analysis_complete", "ratio_analysis_complete"]:
            print("  ⏭ Skipping download (resuming from checkpoint)...", flush=True)
            batch_data = {}  # Empty batch_data since we're skipping download
        else:
            print(f"  Downloading data for {len(all_tickers)} stocks individually (to avoid rate limits)...")
            analysis_progress["status"] = "downloading"
            analysis_progress["stage"] = "Downloading stock data"
            analysis_progress["total"] = len(all_tickers)
            analysis_progress["current"] = 0
            analysis_progress["message"] = f"Downloading {len(all_tickers)} stocks..."
            analysis_progress["last_update"] = time.time()
            
            # Add initial delay to avoid immediate rate limits from Render's IP
            # Reduced to 60s to avoid timeout issues (with 15s between downloads, total time is manageable)
            print("  Waiting 60 seconds before first download attempt to avoid rate limits...")
            for i in range(60, 0, -10):
                print(f"  Waiting... {i}s remaining", end='\r', flush=True)
                time.sleep(10)
            print("\n  Delay complete, starting individual downloads with 15s delays...")
            
            # Skip batch download entirely - use individual downloads from the start
            # This is slower but more reliable for rate-limited IPs
            batch_data = {}
            download_delay = 15  # 15 seconds between downloads (reduced from 20s to speed up)
            rate_limit_wait = 60  # 60 seconds if rate limited
            
            for idx, ticker in enumerate(all_tickers, 1):
                # Check timeout before each download
                if check_timeout_and_save_checkpoint("downloading", {"downloaded_stocks": list(batch_data.keys())}, list(batch_data.keys())):
                    partial_response = {
                        "_partial": True,
                        "_stage": "downloading",
                        "downloaded_stocks": list(batch_data.keys()),
                        "progress": f"{idx-1}/{len(all_tickers)} stocks downloaded"
                    }
                    save_cache(partial_response, is_partial=True, stage="downloading", processed_tickers=list(batch_data.keys()))
                    raise Exception("TIMEOUT_CHECKPOINT: Checkpoint saved during download, will resume on next deployment")
                
                print(f"  Starting download {idx}/{len(all_tickers)}: {ticker}", flush=True)
                analysis_progress["current"] = idx
                analysis_progress["message"] = f"Downloading {ticker} ({idx}/{len(all_tickers)})..."
                analysis_progress["last_update"] = time.time()
                sys.stdout.flush()
                max_retries = 3
                download_success = False
                for retry in range(max_retries):
                    try:
                        print(f"  [{idx}/{len(all_tickers)}] Downloading {ticker} (attempt {retry + 1}/{max_retries})...", flush=True)
                        # Use cached download function which handles caching automatically
                        ticker_data = download_stock_data(ticker, period="2y", interval="1d", max_retries=1, delay=0.5, use_cache=True)
                        
                        if ticker_data is not None and not ticker_data.empty:
                            batch_data[ticker] = ticker_data
                            print(f"    ✓ {ticker} downloaded successfully ({len(ticker_data)} rows)", flush=True)
                            download_success = True
                            # Save checkpoint after each successful download
                            if idx % 5 == 0:  # Save checkpoint every 5 stocks
                                partial_response = {
                                    "_partial": True,
                                    "_stage": "downloading",
                                    "downloaded_stocks": list(batch_data.keys()),
                                    "progress": f"{idx}/{len(all_tickers)} stocks downloaded"
                                }
                                try:
                                    save_cache(partial_response)
                                except:
                                    pass
                            break  # Success, move to next ticker
                        else:
                            print(f"    ✗ {ticker} returned empty data", flush=True)
                            if retry < max_retries - 1:
                                print(f"    Retrying in 10s...", flush=True)
                                time.sleep(10)
                            continue
                            
                    except Exception as e:
                        error_msg = str(e)
                        if "Rate limited" in error_msg or "Too Many Requests" in error_msg or "429" in error_msg or "YFRateLimitError" in error_msg:
                            if retry < max_retries - 1:
                                wait_time = rate_limit_wait * (retry + 1)  # 60s, 120s, 180s
                                print(f"    ✗ {ticker} rate limited, waiting {wait_time}s before retry...", flush=True)
                                time.sleep(wait_time)
                            else:
                                print(f"    ✗ {ticker} rate limited after {max_retries} attempts, skipping...", flush=True)
                                break  # Skip this ticker
                        elif "database is locked" in error_msg.lower():
                            if retry < max_retries - 1:
                                print(f"    ✗ {ticker} cache locked, retrying in 10s...", flush=True)
                                time.sleep(10)
                            else:
                                print(f"    ✗ {ticker} cache locked after {max_retries} attempts, skipping...", flush=True)
                                break  # Skip this ticker
                        else:
                            print(f"    ✗ Error downloading {ticker}: {error_msg}", flush=True)
                            if retry < max_retries - 1:
                                print(f"    Retrying in 10s...", flush=True)
                                time.sleep(10)
                            else:
                                print(f"    ✗ {ticker} failed after {max_retries} attempts, skipping...", flush=True)
                                break  # Skip this ticker
                        continue
                
                if not download_success:
                    print(f"  ⚠ {ticker} failed to download after {max_retries} attempts, continuing to next stock...", flush=True)
                
                # Wait between downloads (except after the last one)
                if idx < len(all_tickers):
                    print(f"  Waiting {download_delay}s before next download (stock {idx}/{len(all_tickers)} complete)...", flush=True)
                    sys.stdout.flush()
                    # Sleep in smaller increments to allow for interruption and better logging
                    for wait_sec in range(download_delay):
                        time.sleep(1)
                        if wait_sec % 5 == 0 and wait_sec > 0:
                            print(f"    ... {download_delay - wait_sec}s remaining...", flush=True)
                            sys.stdout.flush()
                    print(f"  Wait complete, continuing to next stock...", flush=True)
                    sys.stdout.flush()
            
            # Check if we got any data (only if we actually downloaded)
            if not resume_from_stage and not batch_data:
                raise Exception("Failed to download any stock data after multiple attempts.")
            
            if not resume_from_stage:
                print(f"  ✓ Successfully downloaded {len(batch_data)}/{len(all_tickers)} stocks", flush=True)
                print(f"  Starting to process {len(batch_data)} downloaded stocks...", flush=True)
                sys.stdout.flush()
        
        # Check if we should skip stock analysis (resuming from checkpoint)
        processed_tickers_from_checkpoint = []
        if resume_from_stage in ["stock_analysis_complete", "ratio_analysis_complete"]:
            print("  ⏭ Skipping stock analysis (resuming from checkpoint)...", flush=True)
            cached_data = load_cache()
            if cached_data and "sectors" in cached_data:
                output_sectors = cached_data["sectors"]
                # Reconstruct results from sectors for ratio analysis
                results = []
                for sector in output_sectors:
                    for stock in sector.get("stocks", []):
                        ticker = stock["ticker"]
                        results.append({
                            "sector": sector["name"],
                            "ticker": ticker,
                            "z_avg": stock["z"],
                            "avg_score": stock["avg_score"]
                        })
                        processed_tickers_from_checkpoint.append(ticker)
                print(f"  ✓ Loaded {len(results)} stock results from checkpoint", flush=True)
            else:
                print("  ⚠ Could not load cached sectors, starting fresh...", flush=True)
                resume_from_stage = None  # Reset to start fresh
        elif not force_refresh:
            # Check if we have a partial checkpoint with processed_tickers
            cached_data = load_cache()
            if cached_data and cached_data.get("_partial") and cached_data.get("_processed_tickers"):
                processed_tickers_from_checkpoint = cached_data.get("_processed_tickers", [])
                print(f"  ✓ Resuming from checkpoint: {len(processed_tickers_from_checkpoint)} tickers already processed", flush=True)
                # Reconstruct results from checkpoint
                if "sectors" in cached_data:
                    results = []
                    for sector in cached_data["sectors"]:
                        for stock in sector.get("stocks", []):
                            results.append({
                                "sector": sector["name"],
                                "ticker": stock["ticker"],
                                "z_avg": stock["z"],
                                "avg_score": stock["avg_score"]
                            })
        else:
            # Process downloaded data
            results = []
            processed_tickers = []  # Track processed tickers for checkpoint
            # Sort sectors for deterministic processing order
            for sector in sorted(SECTORS.keys()):
                # Check timeout before processing each sector
                if check_timeout_and_save_checkpoint("stock_analysis", {"sectors": []}, processed_tickers):
                    # Prepare partial response for checkpoint
                    partial_response = {
                        "sectors": [],
                        "message": f"Checkpoint saved at sector: {sector}. Processed {len(processed_tickers)} tickers.",
                        "checkpoint": True
                    }
                    # Build sectors from results so far
                    sector_map = {}
                    for r in results:
                        sec = r["sector"]
                        if sec not in sector_map:
                            sector_map[sec] = {"name": sec, "stocks": []}
                        sector_map[sec]["stocks"].append({
                            "ticker": r["ticker"],
                            "z": r["z_avg"],
                            "avg_score": r["avg_score"]
                        })
                    partial_response["sectors"] = list(sector_map.values())
                    save_cache(partial_response, is_partial=True, stage="stock_analysis", processed_tickers=processed_tickers)
                    raise Exception("TIMEOUT_CHECKPOINT: Checkpoint saved, will resume on next deployment")
                
                tickers = SECTORS[sector]
                print(f"\n--- Processing Sector: {sector} ---", flush=True)
                sys.stdout.flush()
                # Sort tickers within sector for determinism
                for ticker in sorted(tickers):
                    # Skip if already processed (resuming from checkpoint)
                    if ticker in processed_tickers_from_checkpoint:
                        print(f"  ⏭ Skipping {ticker} (already processed in checkpoint)", flush=True)
                        continue
                    
                    # Check timeout before processing each ticker
                    if check_timeout_and_save_checkpoint("stock_analysis", {"sectors": []}, processed_tickers):
                        # Prepare partial response
                        partial_response = {
                            "sectors": [],
                            "message": f"Checkpoint saved. Processed {len(processed_tickers)} tickers.",
                            "checkpoint": True
                        }
                        # Build sectors from results so far
                        sector_map = {}
                        for r in results:
                            sec = r["sector"]
                            if sec not in sector_map:
                                sector_map[sec] = {"name": sec, "stocks": []}
                            sector_map[sec]["stocks"].append({
                                "ticker": r["ticker"],
                                "z": r["z_avg"],
                                "avg_score": r["avg_score"]
                            })
                        partial_response["sectors"] = list(sector_map.values())
                        save_cache(partial_response, is_partial=True, stage="stock_analysis", processed_tickers=processed_tickers)
                        raise Exception("TIMEOUT_CHECKPOINT: Checkpoint saved, will resume on next deployment")
                    max_retries = 3
                    timeout_seconds = 300  # 5 minutes per stock analysis
                    result = None
                    start_time = time.time()
                    
                    for attempt in range(1, max_retries + 1):
                        try:
                            if attempt > 1:
                                print(f"  Retrying {ticker} (attempt {attempt}/{max_retries})...", flush=True)
                                sys.stdout.flush()
                            else:
                                print(f"  Analyzing {ticker}...", flush=True)
                                sys.stdout.flush()
                            
                            # Get data from batch or download individually
                            if ticker in batch_data and not batch_data[ticker].empty:
                                data = batch_data[ticker]
                            else:
                                # Fallback: download individually with long delays
                                print(f"    Data not in batch, downloading individually with 10s delay...")
                                data = download_stock_data(ticker, period="2y", interval="1d", max_retries=3, delay=10.0)
                            
                            if data.empty:
                                print(f"  No data for {ticker}, skipping.")
                                break  # No point retrying if no data
                            
                            # Handle MultiIndex columns from yfinance
                            if isinstance(data.columns, pd.MultiIndex):
                                data.columns = data.columns.droplevel(1)
                            
                            # Use concurrent.futures to add timeout to analyze_stock
                            from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                            import threading
                            
                            with ThreadPoolExecutor(max_workers=1) as executor:
                                future = executor.submit(analyze_stock, ticker, data, CONFIG)
                                
                                # Start a progress monitor thread
                                progress_stop = threading.Event()
                                
                                def progress_monitor():
                                    start_time_monitor = time.time()
                                    while not progress_stop.is_set():
                                        time.sleep(15)  # Check every 15 seconds
                                        if not progress_stop.is_set():
                                            elapsed = int(time.time() - start_time_monitor)
                                            if elapsed < timeout_seconds:
                                                print(f"      ... {ticker} still analyzing ({elapsed}s elapsed)...", flush=True)
                                                sys.stdout.flush()
                                            else:
                                                break
                                
                                monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
                                monitor_thread.start()
                                
                                try:
                                    result = future.result(timeout=timeout_seconds)
                                    progress_stop.set()  # Stop progress monitor
                                except FutureTimeoutError:
                                    progress_stop.set()  # Stop progress monitor
                                    elapsed_total = time.time() - start_time
                                    print(f"  ⚠ {ticker} analysis timed out after {timeout_seconds}s (attempt {attempt}/{max_retries}, total elapsed: {elapsed_total:.1f}s)", flush=True)
                                    sys.stdout.flush()
                                    future.cancel()
                                    result = None
                                    if attempt < max_retries:
                                        print(f"    Waiting 10s before retry...", flush=True)
                                        sys.stdout.flush()
                                        time.sleep(10)
                                        start_time = time.time()  # Reset timer for retry
                                        continue
                                    else:
                                        print(f"  ✗ {ticker}: Failed after {max_retries} attempts (timeout)", flush=True)
                                        sys.stdout.flush()
                                        break
                            
                            # If we got a result, break out of retry loop
                            if result is not None and isinstance(result, dict):
                                z_avg = result.get("z_avg", 0.0)
                                avg_score = result.get("avg_score", 0.0)
                                results.append({
                                    "sector": sector, 
                                    "ticker": ticker, 
                                    "z_avg": z_avg,
                                    "avg_score": avg_score
                                })
                                processed_tickers.append(ticker)  # Track processed ticker
                                elapsed_total = time.time() - start_time
                                print(f"  ✓ {ticker}: z_avg = {z_avg:.3f}, avg_score = {avg_score:.3f} (completed in {elapsed_total:.1f}s)", flush=True)
                                sys.stdout.flush()
                                
                                # Periodically save checkpoint during processing (every 10 tickers)
                                if len(processed_tickers) % 10 == 0:
                                    elapsed = time.time() - start_time
                                    if elapsed > 600:  # After 10 minutes, save checkpoint every 10 tickers
                                        print(f"  💾 Saving intermediate checkpoint ({len(processed_tickers)} tickers processed)...", flush=True)
                                        partial_response = {
                                            "sectors": [],
                                            "message": f"Intermediate checkpoint: {len(processed_tickers)} tickers processed",
                                            "checkpoint": True
                                        }
                                        sector_map = {}
                                        for r in results:
                                            sec = r["sector"]
                                            if sec not in sector_map:
                                                sector_map[sec] = {"name": sec, "stocks": []}
                                            sector_map[sec]["stocks"].append({
                                                "ticker": r["ticker"],
                                                "z": r["z_avg"],
                                                "avg_score": r["avg_score"]
                                            })
                                        partial_response["sectors"] = list(sector_map.values())
                                        save_cache(partial_response, is_partial=True, stage="stock_analysis", processed_tickers=processed_tickers)
                                
                                break  # Success, exit retry loop
                            else:
                                if attempt < max_retries:
                                    print(f"  ⚠ {ticker} returned None (attempt {attempt}/{max_retries}), retrying...", flush=True)
                                    sys.stdout.flush()
                                    time.sleep(5)
                                    start_time = time.time()  # Reset timer for retry
                                    continue
                                else:
                                    print(f"  ✗ {ticker}: Failed to calculate scores after {max_retries} attempts", flush=True)
                                    sys.stdout.flush()
                                    break
                        
                        except Exception as e:
                            error_msg = str(e)
                            print(f"  ⚠ Error processing {ticker} (attempt {attempt}/{max_retries}): {error_msg}", flush=True)
                            sys.stdout.flush()
                            
                            if attempt < max_retries:
                                print(f"    Waiting 10s before retry...", flush=True)
                                sys.stdout.flush()
                                time.sleep(10)
                                start_time = time.time()  # Reset timer for retry
                                continue
                            else:
                                print(f"  ✗ {ticker}: Failed after {max_retries} attempts: {error_msg}", flush=True)
                                import traceback
                                traceback.print_exc(file=sys.stderr)
                                sys.stderr.flush()
                                break  # Move to next stock

        print(f"\n✓ Finished processing {len(results)} stocks", flush=True)
        sys.stdout.flush()

        if not results:
            print("\n⚠ No results calculated - returning error", flush=True)
            sys.stdout.flush()
            analysis_progress["status"] = "error"
            analysis_progress["error"] = "No results calculated"
            return jsonify({"error": "No results calculated. Check server logs for details."}), 500
            
        # --- Format data ---
        results_df = pd.DataFrame(results)
        sector_avg_df = results_df.groupby('sector').agg({
            'z_avg': 'mean',
            'avg_score': 'mean'
        }).reset_index()
        
        output_sectors = []
        for _, row in sector_avg_df.iterrows():
            sector_name = row['sector']
            avg_z = float(row['z_avg'])
            avg_score_sector = float(row['avg_score'])
            
            # Get stocks for this sector
            sector_stocks_df = results_df[results_df['sector'] == sector_name]
            stocks_list = [
                {
                    "ticker": s_row['ticker'], 
                    "z": float(s_row['z_avg']),
                    "avg_score": float(s_row['avg_score'])
                } 
                for _, s_row in sector_stocks_df.iterrows()
            ]
            
            # Sort stocks by combined score (z_avg + avg_score, highest first)
            stocks_list.sort(key=lambda x: x['z'] + x['avg_score'], reverse=True)
            
            output_sectors.append({
                "name": sector_name,
                "avg_z": avg_z,
                "avg_score": avg_score_sector,
                "stocks": stocks_list
            })
        
        # Sort sectors by combined score (highest first)
        output_sectors.sort(key=lambda x: x['avg_z'] + x['avg_score'], reverse=True)
        
        # Save partial results after stock analysis (checkpoint)
        partial_response = {
            "sectors": output_sectors,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "_partial": True,  # Mark as partial
            "_stage": "stock_analysis_complete"
        }
        save_cache(partial_response)
        print(f"  ✓ Checkpoint saved: Stock analysis complete ({len(results)} stocks)", flush=True)
        
        analysis_progress["status"] = "analyzing"
        analysis_progress["stage"] = "Stock analysis complete"
        analysis_progress["message"] = f"Analyzed {len(results)} stocks, starting ratio analysis..."
        analysis_progress["last_update"] = time.time()

        # --- Ratio Analysis and Backtesting ---
        print("\n--- Starting Ratio Analysis and Backtesting ---", flush=True)
        sys.stdout.flush()
        analysis_progress["status"] = "ratio_analysis"
        analysis_progress["stage"] = "Ratio Analysis"
        analysis_progress["message"] = "Calculating ratio analysis..."
        analysis_progress["last_update"] = time.time()
        ratio_analysis = None
        backtest_results = None
        
        # Check if we should skip ratio analysis (resuming from checkpoint)
        if resume_from_stage == "ratio_analysis_complete":
            print("  ⏭ Skipping ratio analysis (resuming from checkpoint)...", flush=True)
            cached_data = load_cache()
            if cached_data and "ratio_analysis" in cached_data:
                ratio_analysis = cached_data["ratio_analysis"]
                print(f"  ✓ Loaded ratio analysis from checkpoint", flush=True)
            else:
                print("  ⚠ Could not load cached ratio analysis, recalculating...", flush=True)
                resume_from_stage = "stock_analysis_complete"  # Fall back to ratio analysis
        
        if resume_from_stage != "ratio_analysis_complete":
            try:
                # Get all unique tickers - SORT for deterministic results
                all_tickers = sorted(list(results_df['ticker'].unique()))
                print(f"  Calculating ratio analysis for {len(all_tickers)} stocks...", flush=True)
                sys.stdout.flush()
                
                # Calculate ratio scores: each stock against all others
                ratio_scores = {}
                total_comparisons = len(all_tickers) * (len(all_tickers) - 1)
                print(f"  Total comparisons needed: {total_comparisons}", flush=True)
                sys.stdout.flush()
                
                # Compare each stock against all others for complete analysis
                # Full analysis: 11 stocks × 10 comparisons = 110 comparisons × ~10s = ~18 minutes
                comparison_limit = len(all_tickers) - 1  # Compare against all other stocks
                
                for i, ticker1 in enumerate(all_tickers):
                    if i % 10 == 0 or i == 0:
                        print(f"  Progress: {i}/{len(all_tickers)} stocks analyzed...", flush=True)
                        analysis_progress["current"] = i
                        analysis_progress["total"] = len(all_tickers)
                        analysis_progress["message"] = f"Ratio analysis: {i}/{len(all_tickers)} stocks..."
                        analysis_progress["last_update"] = time.time()
                        sys.stdout.flush()
                    
                    ratio_z_scores = []
                    comparisons_made = 0
                    
                    # Compare against other stocks - use sorted list for deterministic order
                    # CRITICAL: Sort ticker2 list to ensure deterministic comparison order
                    for ticker2 in sorted(all_tickers):
                        if ticker1 == ticker2:
                            continue
                        
                        if comparisons_made >= comparison_limit:
                            break
                        
                        # Calculate ratio avg_score (ticker1/ticker2) with retry logic and aggressive timeout
                        max_retries = 3
                        timeout_seconds = 60  # 60 seconds per ratio comparison (normal takes 15-30s)
                        ratio_score = None
                        start_time = time.time()
                        
                        for attempt in range(1, max_retries + 1):
                            try:
                                if attempt > 1:
                                    print(f"    Retrying {ticker1}/{ticker2} (attempt {attempt}/{max_retries})...", flush=True)
                                    sys.stdout.flush()
                                else:
                                    print(f"    Comparing {ticker1}/{ticker2} ({comparisons_made + 1}/{comparison_limit})...", flush=True)
                                    sys.stdout.flush()
                                
                                # Use concurrent.futures to add timeout to calculate_ratio_avg_score
                                from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
                                
                                with ThreadPoolExecutor(max_workers=1) as executor:
                                    future = executor.submit(calculate_ratio_avg_score, ticker1, ticker2, CONFIG, batch_data)
                                    
                                    # Start a progress monitor thread
                                    import threading
                                    progress_stop = threading.Event()
                                    
                                    def progress_monitor():
                                        start_time_monitor = time.time()
                                        while not progress_stop.is_set():
                                            time.sleep(15)  # Check every 15 seconds
                                            if not progress_stop.is_set():
                                                elapsed = int(time.time() - start_time_monitor)
                                                if elapsed < timeout_seconds:
                                                    print(f"      ... {ticker1}/{ticker2} still calculating ({elapsed}s elapsed)...", flush=True)
                                                    sys.stdout.flush()
                                                else:
                                                    break
                                    
                                    monitor_thread = threading.Thread(target=progress_monitor, daemon=True)
                                    monitor_thread.start()
                                    
                                    try:
                                        ratio_score = future.result(timeout=timeout_seconds)
                                        progress_stop.set()  # Stop progress monitor
                                    except FutureTimeoutError:
                                        progress_stop.set()  # Stop progress monitor
                                        elapsed_total = time.time() - start_time
                                        print(f"      ⚠ {ticker1}/{ticker2} timed out after {timeout_seconds}s (attempt {attempt}/{max_retries}, total elapsed: {elapsed_total:.1f}s)", flush=True)
                                        sys.stdout.flush()
                                        future.cancel()
                                        ratio_score = None
                                        if attempt < max_retries:
                                            print(f"        Waiting 5s before retry...", flush=True)
                                            sys.stdout.flush()
                                            time.sleep(5)
                                            start_time = time.time()  # Reset timer for retry
                                            continue
                                        else:
                                            print(f"      ✗ {ticker1}/{ticker2}: Failed after {max_retries} attempts (timeout), skipping...", flush=True)
                                            sys.stdout.flush()
                                            break
                                    
                                    # If we got a result, break out of retry loop
                                    if ratio_score is not None:
                                        elapsed_total = time.time() - start_time
                                        ratio_z_scores.append(ratio_score)
                                        print(f"      ✓ {ticker1}/{ticker2}: {ratio_score:.3f} (completed in {elapsed_total:.1f}s)", flush=True)
                                        sys.stdout.flush()
                                        break  # Success, exit retry loop
                                    else:
                                        if attempt < max_retries:
                                            print(f"      ⚠ {ticker1}/{ticker2} returned None (attempt {attempt}/{max_retries}), retrying...", flush=True)
                                            sys.stdout.flush()
                                            time.sleep(3)
                                            start_time = time.time()  # Reset timer for retry
                                            continue
                                        else:
                                            print(f"      ✗ {ticker1}/{ticker2}: Failed to calculate ratio after {max_retries} attempts, skipping...", flush=True)
                                            sys.stdout.flush()
                                            break
                                    
                            except Exception as e:
                                error_msg = str(e)
                                elapsed_total = time.time() - start_time
                                print(f"      ⚠ Error calculating ratio for {ticker1}/{ticker2} (attempt {attempt}/{max_retries}, elapsed: {elapsed_total:.1f}s): {error_msg}", flush=True)
                                sys.stdout.flush()
                                
                                if attempt < max_retries:
                                    print(f"        Waiting 5s before retry...", flush=True)
                                    sys.stdout.flush()
                                    time.sleep(5)
                                    start_time = time.time()  # Reset timer for retry
                                    continue
                                else:
                                    print(f"      ✗ {ticker1}/{ticker2}: Failed after {max_retries} attempts, skipping...", flush=True)
                                    sys.stdout.flush()
                                    break  # Move to next comparison
                    
                    comparisons_made += 1
                
                    if ratio_z_scores:
                        # Average z-score from all ratio comparisons
                        # CRITICAL: Sort ratio_z_scores before averaging to ensure deterministic results
                        # This ensures that even if comparisons complete in different orders, the average is the same
                        sorted_ratio_scores = sorted(ratio_z_scores)
                        avg_ratio_score = sum(sorted_ratio_scores) / len(sorted_ratio_scores)
                        ratio_scores[ticker1] = avg_ratio_score
                        print(f"  {ticker1}: {avg_ratio_score:.3f} (from {len(sorted_ratio_scores)} comparisons)", flush=True)
                        sys.stdout.flush()
                    else:
                        # If no successful comparisons, set score to negative infinity (will be sorted last)
                        ratio_scores[ticker1] = float('-inf')
                        print(f"  {ticker1}: No successful comparisons, skipping", flush=True)
                        sys.stdout.flush()
                
                # Sort by ratio score (after all stocks analyzed)
                # Use ticker name as secondary sort key for deterministic tie-breaking
                sorted_ratio_stocks = sorted(ratio_scores.items(), key=lambda x: (x[1], x[0]), reverse=True)
                top_ratio_stocks = sorted_ratio_stocks[:10]  # Top 10 for backtesting
                
                print(f"  Top stocks by ratio analysis: {[s[0] for s in top_ratio_stocks[:5]]}")
                
                analysis_progress["status"] = "backtesting"
                analysis_progress["stage"] = "Backtesting"
                analysis_progress["message"] = "Running historical backtest..."
                analysis_progress["last_update"] = time.time()
                
                # Check if we should do incremental update or full backtest
                cached_data = load_cache()
                incremental_update = False
                if cached_data and cached_data.get("backtest") and not force_refresh:
                    # Check if backtest exists and is recent (within last 2 days)
                    backtest_timestamp = cached_data.get("backtest_timestamp")
                    if backtest_timestamp:
                        try:
                            last_backtest_date = datetime.strptime(backtest_timestamp, "%Y-%m-%d %H:%M:%S")
                            days_since = (datetime.now() - last_backtest_date).days
                            if days_since <= 2:
                                incremental_update = True
                                print(f"  ✓ Found recent backtest (from {backtest_timestamp}), using incremental update...", flush=True)
                        except:
                            pass
            
            # Perform historical backtest using ratio scores
                if incremental_update:
                    backtest_results = update_backtest_incrementally(
                        cached_data.get("backtest"), 
                        top_ratio_stocks, 
                        CONFIG
                    )
                else:
                    backtest_results = perform_historical_backtest(top_ratio_stocks, CONFIG)
            
                ratio_analysis = {
                    "top_stocks": [{"ticker": ticker, "ratio_score": score} for ticker, score in top_ratio_stocks[:10]],
                    "current_best": top_ratio_stocks[0][0] if top_ratio_stocks else "N/A"
                }
                
                # Save partial results after ratio analysis (checkpoint)
                partial_response = {
                    "sectors": output_sectors,
                    "ratio_analysis": ratio_analysis,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "_partial": True,  # Mark as partial
                    "_stage": "ratio_analysis_complete"
                }
                save_cache(partial_response)
                print(f"  ✓ Checkpoint saved: Ratio analysis complete", flush=True)
            except Exception as e:
                print(f"  [!] Error in ratio analysis/backtesting: {e}", flush=True)
                import traceback
                traceback.print_exc(file=sys.stderr)
                sys.stderr.flush()
                analysis_progress["status"] = "error"
                analysis_progress["error"] = str(e)
                analysis_progress["last_update"] = time.time()

        print(f"\n✓ Analysis complete. Processed {len(results)} stocks across {len(output_sectors)} sectors.", flush=True)
        print("Sending JSON response to frontend.", flush=True)
        sys.stdout.flush()
        
        response_data = {
            "sectors": output_sectors,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if ratio_analysis:
            response_data["ratio_analysis"] = ratio_analysis
        if backtest_results:
            response_data["backtest"] = backtest_results
            response_data["backtest_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            response_data["backtest_timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Remove partial markers before final save
        if "_partial" in response_data:
            del response_data["_partial"]
        if "_stage" in response_data:
            del response_data["_stage"]
        
        # Save to cache
        save_cache(response_data)
        
        # Update progress as complete
        analysis_progress["status"] = "complete"
        analysis_progress["stage"] = "Complete"
        analysis_progress["message"] = "Analysis complete!"
        analysis_progress["results"] = response_data
        analysis_progress["last_update"] = time.time()
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✓ Analysis complete! Total time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
        print(f"{'='*60}\n")
        
        return response_data  # Return dict, not jsonify
        
    except Exception as e:
        import sys
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)
        tb_str = traceback.format_exc()
        
        # Update progress with error
        analysis_progress["status"] = "error"
        analysis_progress["error"] = error_msg
        analysis_progress["last_update"] = time.time()
        
        # Print to stdout (visible in Render logs) - force flush
        print(f"\n{'='*60}", flush=True)
        print(f"✗ FATAL ERROR in /analyze endpoint", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {error_type}", flush=True)
        print(f"Error Message: {error_msg}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        print(tb_str, flush=True)
        print(f"{'='*60}\n", flush=True)
        sys.stdout.flush()
        
        # Also print to stderr
        print(tb_str, file=sys.stderr)
        sys.stderr.flush()
        
        # Return error response (raise exception for background thread to catch)
        raise Exception(f"Server error: {error_msg}")
    finally:
        # Always release the lock
        analysis_lock.release()

@app.route('/analyze', methods=['GET'])
def get_analysis_results():
    """
    HTTP endpoint that calls the core analysis logic.
    """
    try:
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        print(f"\n{'='*60}", flush=True)
        print(f"Received request at /analyze endpoint (PID: {os.getpid()})...", flush=True)
        print(f"Force refresh: {force_refresh}", flush=True)
        print(f"{'='*60}\n", flush=True)
        
        result = run_analysis_logic(force_refresh=force_refresh)
        
        # Validate result structure
        if not result:
            print("ERROR: run_analysis_logic returned None or empty result", flush=True)
            return jsonify({"error": "No data returned from analysis"}), 500
        
        if not isinstance(result, dict):
            print(f"ERROR: run_analysis_logic returned non-dict: {type(result)}", flush=True)
            return jsonify({"error": f"Invalid response type: {type(result)}"}), 500
        
        if "sectors" not in result:
            print("ERROR: Result missing 'sectors' key", flush=True)
            print(f"Result keys: {list(result.keys())}", flush=True)
            return jsonify({"error": "Invalid response structure: missing 'sectors'"}), 500
        
        if not isinstance(result["sectors"], list):
            print(f"ERROR: 'sectors' is not a list: {type(result['sectors'])}", flush=True)
            return jsonify({"error": "Invalid response structure: 'sectors' is not a list"}), 500
        
        print(f"✓ Returning response with {len(result.get('sectors', []))} sectors", flush=True)
        if result.get('backtest'):
            print(f"✓ Response includes backtest data", flush=True)
        if result.get('ratio_analysis'):
            print(f"✓ Response includes ratio analysis data", flush=True)
        
        return jsonify(result)
    except Exception as e:
        import sys
        import traceback
        error_type = type(e).__name__
        error_msg = str(e)
        tb_str = traceback.format_exc()
        
        # Print to stdout (visible in Render logs) - force flush
        print(f"\n{'='*60}", flush=True)
        print(f"✗ FATAL ERROR in /analyze endpoint", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"Error Type: {error_type}", flush=True)
        print(f"Error Message: {error_msg}", flush=True)
        print(f"\nFull Traceback:", flush=True)
        print(tb_str, flush=True)
        print(f"{'='*60}\n", flush=True)
        sys.stdout.flush()
        
        # Return error response
        return jsonify({
            "error": f"Server error: {error_msg}",
            "error_type": error_type
        }), 500


# --- Keep-Alive Thread (prevents services from spinning down) ---
def start_keepalive():
    """Periodically hit health endpoint to keep service alive (Render, Fly.io, etc.)"""
    def keepalive_loop():
        from urllib.request import urlopen
        from urllib.error import URLError
        import time
        
        while True:
            try:
                # Wait 2 minutes between keep-alive requests (more frequent for Fly.io)
                time.sleep(120)  # 2 minutes
                
                # Make a request to health endpoint to keep service alive
                try:
                    port = os.environ.get('PORT', '8080')
                    url = f'http://localhost:{port}/health'
                    with urlopen(url, timeout=5) as response:
                        status = response.getcode()
                        print(f"✓ Keep-alive ping sent (status: {status})", flush=True)
                except (URLError, OSError) as e:
                    # Ignore keep-alive errors - they're non-critical
                    print(f"⚠ Keep-alive ping failed (non-critical): {e}", flush=True)
            except Exception as e:
                print(f"⚠ Keep-alive error (non-critical): {e}", flush=True)
                time.sleep(60)  # Wait 1 minute before retrying
    
    # Start keep-alive thread
    keepalive_thread = threading.Thread(target=keepalive_loop, daemon=True)
    keepalive_thread.start()
    print("✓ Keep-alive thread started (will ping every 2 minutes to prevent spin-down)", flush=True)

# --- Background Analysis Thread ---
def start_background_analysis():
    """Start analysis automatically in background thread after a short delay"""
    def run_analysis():
        # Wait 10 seconds for server to fully start
        time.sleep(10)
        
        # Check if cache exists
        cached_data = load_cache()
        if cached_data:
            print("\n" + "="*60, flush=True)
            print("✓ Cache found - analysis already completed", flush=True)
            print("="*60 + "\n", flush=True)
            global analysis_progress
            analysis_progress["status"] = "complete"
            analysis_progress["results"] = cached_data
            analysis_progress["message"] = "Loaded from cache"
            return
        
        # No cache - start analysis automatically
        print("\n" + "="*60, flush=True)
        print("🚀 Starting automatic background analysis...", flush=True)
        print("   (No cache found - will calculate fresh data)", flush=True)
        print("="*60 + "\n", flush=True)
        
        # Call the analysis function directly
        try:
            run_analysis_logic(force_refresh=False)
        except Exception as e:
            print(f"\n⚠ Error in background analysis: {e}", flush=True)
            import traceback
            import sys
            traceback.print_exc(file=sys.stderr)
            sys.stderr.flush()
    
    # Start background thread
    thread = threading.Thread(target=run_analysis, daemon=True)
    thread.start()
    print("✓ Background analysis thread started (will check cache and run if needed)", flush=True)

# Start keep-alive and background analysis when module loads (for gunicorn)
# Only start if not already running (to avoid duplicate threads)
if not hasattr(app, '_background_analysis_started'):
    app._background_analysis_started = True
    start_keepalive()  # Start keep-alive first
    start_background_analysis()

# --- Run Flask Server ---
def run_daily_update():
    """Run daily update at 13:00 - re-run z-scoring and ratio analysis, update backtest incrementally"""
    global daily_update_status, analysis_lock
    
    # Check if analysis is already running (e.g., from manual trigger)
    if not analysis_lock.acquire(blocking=False):
        print(f"\n⚠ Update skipped: Analysis already in progress\n")
        return
    
    # Save update checkpoint before starting
    update_checkpoint_file = CACHE_FILE.replace('.json', '_update_checkpoint.json')
    checkpoint_data = {
        "update_started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "stage": "starting"
    }
    
    try:
        daily_update_status["update_in_progress"] = True
        daily_update_status["update_completed"] = False
        
        # Save checkpoint that update is starting
        with open(update_checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"\n{'='*60}")
        print(f"🔄 Starting daily update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # Run analysis with incremental backtest update
        # force_refresh=False enables incremental update and uses cached stock data
        run_analysis_logic(force_refresh=False)
        
        daily_update_status["last_update_time"] = datetime.now()
        daily_update_status["update_completed"] = True
        print(f"\n✓ Daily update completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Remove checkpoint file on successful completion
        if os.path.exists(update_checkpoint_file):
            os.remove(update_checkpoint_file)
        
        # Reset the flag after 5 minutes so the message doesn't stay forever
        def reset_flag():
            time.sleep(300)  # 5 minutes
            daily_update_status["update_completed"] = False
        threading.Thread(target=reset_flag, daemon=True).start()
    except Exception as e:
        print(f"\n✗ Error in daily update: {e}\n")
        import traceback
        traceback.print_exc()
        # Save error checkpoint for resume
        checkpoint_data = {
            "update_started": checkpoint_data.get("update_started", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "stage": "error",
            "error": str(e),
            "error_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        try:
            with open(update_checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(checkpoint_data, f, indent=2)
        except:
            pass
    finally:
        daily_update_status["update_in_progress"] = False
        analysis_lock.release()

def start_scheduled_tasks():
    """Start scheduled task for daily updates at 13:00"""
    global daily_update_status
    
    # Initialize last update time from cache if available
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
                if 'backtest_timestamp' in cache_data:
                    # Parse timestamp and set as last update time
                    try:
                        daily_update_status["last_update_time"] = datetime.fromisoformat(cache_data['backtest_timestamp'])
                    except:
                        pass
    except:
        pass
    
    # Check for incomplete update checkpoint and resume if needed
    update_checkpoint_file = CACHE_FILE.replace('.json', '_update_checkpoint.json')
    if os.path.exists(update_checkpoint_file):
        try:
            with open(update_checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint = json.load(f)
                print(f"⚠ Found incomplete update checkpoint from {checkpoint.get('update_started', 'unknown')}")
                print(f"  Resuming update...")
                # Run update in background thread to resume
                def resume_update():
                    time.sleep(5)  # Wait a bit for server to start
                    run_daily_update()
                threading.Thread(target=resume_update, daemon=True).start()
        except Exception as e:
            print(f"  ⚠ Error reading checkpoint: {e}")
    
    # Schedule daily update at 13:00
    schedule.every().day.at("13:00").do(run_daily_update)
    print("✓ Scheduled daily update at 13:00 (your local time)")
    
    # Run scheduler in background thread
    def run_scheduler():
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    print("✓ Scheduler thread started")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("\n" + "="*60)
    print("Starting Stock Sector Trending Dashboard Server")
    print("="*60)
    print(f"Server will be available at: http://0.0.0.0:{port}")
    print("\n📊 OPEN THIS URL IN YOUR BROWSER:")
    print(f"   http://localhost:{port}")
    print("\n   (Do NOT open dashboard.html directly from file explorer!)")
    print(f"\nAPI endpoint: http://localhost:{port}/analyze")
    print("="*60 + "\n")
    
    # Check for force refresh flag and delete cache if it exists
    force_refresh_flag = '.force_refresh_cache'
    if os.path.exists(force_refresh_flag):
        print("🔄 Force refresh flag detected - deleting cache files...")
        try:
            if os.path.exists(CACHE_FILE):
                os.remove(CACHE_FILE)
                print(f"  ✓ Deleted cache file: {CACHE_FILE}")
            # Also delete the flag file
            os.remove(force_refresh_flag)
            print("  ✓ Removed force refresh flag")
        except Exception as e:
            print(f"  ⚠ Error deleting cache: {e}")
    
    # Start scheduled tasks for daily updates
    start_scheduled_tasks()
    
    app.run(host='0.0.0.0', port=port, debug=False)

# For Fly.io and other platforms that use gunicorn
# The app variable is already defined above and will be used by gunicorn

