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
def download_stock_data(ticker, period="2y", interval="1d", start=None, end=None, max_retries=3, delay=2.0):
    """
    Download stock data with rate limiting and retry logic.
    
    Args:
        ticker: Stock ticker symbol
        period: Data period (e.g., "2y", "1d") - used if start/end not provided
        interval: Data interval (default: "1d")
        start: Start date (datetime or string) - alternative to period
        end: End date (datetime or string) - alternative to period
        max_retries: Maximum number of retry attempts (default: 3)
        delay: Initial delay between requests in seconds (default: 0.5)
    
    Returns:
        pandas.DataFrame: Stock data or empty DataFrame if failed
    """
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
                    return pd.DataFrame()
            else:
                # Other errors - log and return empty
                print(f"    ✗ Error downloading {ticker}: {error_msg}")
                if attempt < max_retries - 1:
                    time.sleep(delay * (attempt + 1))
                else:
                    return pd.DataFrame()
    
    return pd.DataFrame()

SECTORS = {
    "Technology": ["AAPL"],
    "Energy": ["XOM"],
    "Health Care": ["LLY"],
    "Industrials": ["BA"],
    "Utilities": ["NEE"],
    "Consumer Staples": ["PG"],
    "Financials": ["JPM"],
    "Consumer Discretionary": ["AMZN"],
    "Real Estate": ["AMT"],
    "Materials": ["LIN"],
    "Communication Services": ["GOOGL"]
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
    total = pd.Series(index=src.index, dtype=float)
    for i in range(length, len(src)):
        score = 0.0
        for j in range(1, length + 1):
            if i - j >= 0:
                score += 1 if src.iloc[i] >= src.iloc[i - j] else -1
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
                if idx < 0 or idx >= len(vol):
                    continue  # Skip if index is out of bounds
                change = src.iloc[idx] - src.iloc[idx - 1] if idx - 1 >= 0 else 0
                if change > 0:
                    up += vol.iloc[idx]
                elif change == 0:
                    up += vol.iloc[idx] / 2
                down += vol.iloc[idx]
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
        adx_value = calc_adx(h, l, c, config['di_length'], config['adx_smoothing'])
        z_adx = calc_zscore(adx_value, config['z_score_len'])
        
        # 2. KPSS - Calculate rolling KPSS values for z-scoring
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
        garch_vol = calc_garch_vol(c, config['garch_alpha'], config['garch_beta'], config['garch_emaLen'])
        z_garch = calc_zscore(garch_vol, config['z_score_len'])
        
        # 5. Half-Life - Calculate rolling half-life values for z-scoring
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
        wave_vol = calc_wavelet_vol(kpss_src_data, config['wavelet_alpha'], config['wavelet_len'])
        z_wave_vol = calc_zscore(wave_vol, config['z_score_len'])
        
        # 7. Price/Momentum Correlation
        pmc_corr = calc_pmc_corr(corr_src_data, config['corr_mom_type'], config['corr_length'])
        z_pmc_corr = calc_zscore(pmc_corr, config['z_score_len'])

        # 8. Choppiness
        chop_val = calc_chop(h, l, c, config['chop_length'])
        z_chop = calc_zscore(chop_val, config['z_score_len']) * -1 # Inverted
        
        # 9. Hurst - Calculate rolling Hurst values for z-scoring
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
        atr_val = calc_atr(h, l, c, config['atr_length1'])
        z_atr = calc_zscore(atr_val, config['z_score_len'])
        
        # 11. Phillips-Perron - Calculate rolling PP values for z-scoring
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

# --- Ratio Analysis and Backtesting Functions ---

def calculate_ratio_avg_score(ticker1, ticker2, config):
    """Calculate avg_score for a ratio of two stocks (ticker1/ticker2)"""
    try:
        # Download data for both stocks
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
    for tickers in SECTORS.values():
        all_tickers.extend(tickers)
    return list(set(all_tickers))  # Remove duplicates

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
        top_stocks = [ticker for ticker, _ in top_stocks_with_scores]
        
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
                        all_dates = all_dates.intersection(data.index)
            except:
                continue
        
        if not stock_data or len(all_dates) < 50:
            return None
        
        # Sort dates
        all_dates = sorted(all_dates)
        
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
        
        for i in range(start_index, len(all_dates)):
            date = all_dates[i]
            
            # Check if we have a pending rotation to execute (enter on next day's open)
            if pending_rotation is not None and pending_rotation_date is not None:
                # Check if this is the next trading day after signal
                if date > pending_rotation_date:
                    # Execute pending rotation - enter on this day's open
                    rotation_occurred = True
                    previous_asset = pending_previous_asset  # Use stored previous asset
                    current_asset = pending_rotation
                    
                    if pending_rotation is not None:
                        try:
                            asset_data = stock_data[current_asset]
                            date_idx = asset_data.index.get_indexer([date], method='nearest')[0]
                            if date_idx >= 0:
                                # Enter at open price (next day after signal confirmation)
                                entry_price = asset_data['Open'].iloc[date_idx]
                                entry_date = date
                                print(f"  [Entry] {current_asset} at ${entry_price:.2f} on {date.strftime('%Y-%m-%d')} (open)")
                        except Exception as e:
                            print(f"  [!] Error entering {pending_rotation}: {e}")
                            current_asset = None
                            entry_price = None
                            rotation_occurred = False
                    
                    # Clear pending rotation
                    pending_rotation = None
                    pending_rotation_date = None
                    pending_previous_asset = None
                    pending_previous_entry_price = None
                    pending_previous_entry_date = None
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
                
                equity_curve.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'equity': current_equity,
                    'asset': asset_for_display,
                    'rotation': False,
                    'previous_asset': None,
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
            stock_scores = {}
            for ticker, data in stock_data.items():
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
            best_ticker = max(stock_scores.items(), key=lambda x: x[1])[0]
            best_score = stock_scores[best_ticker]
            
            # Don't invest if all scores are negative
            if best_score < 0:
                best_ticker = None
            
            # Check if current asset goes negative - exit to cash
            if current_asset is not None and current_asset in stock_scores:
                current_asset_score = stock_scores[current_asset]
                if current_asset_score < 0:
                    # Current asset went negative - exit to cash
                    best_ticker = None
            
            # Check if we need to rotate (signal detected on this day, will enter tomorrow)
            exit_price_recorded = None
            rotation_occurred = False
            exit_previous_asset = None  # Track asset we're exiting from
            
            if current_asset is None or best_ticker != current_asset or (best_ticker is None and current_asset is not None):
                # Signal detected on this day (at close) - exit current position, enter tomorrow at open
                exit_previous_asset = current_asset  # Remember what we're exiting from
                rotation_occurred = True
                
                # Close current position at today's close
                if current_asset is not None and entry_price is not None:
                    try:
                        prev_data = stock_data[current_asset]
                        prev_date_idx = prev_data.index.get_indexer([date], method='nearest')[0]
                        if prev_date_idx >= 0:
                            exit_price_recorded = prev_data['Close'].iloc[prev_date_idx]
                            # Update base equity based on actual exit price
                            base_equity = base_equity * (exit_price_recorded / entry_price)
                            equity = base_equity  # Reset equity to base after exit
                            print(f"  [Exit] {current_asset} at ${exit_price_recorded:.2f} on {date.strftime('%Y-%m-%d')} (close)")
                            
                            if entry_date:
                                hold_days = (date - entry_date).days
                                hold_periods.append(hold_days)
                    except Exception as e:
                        print(f"  [!] Error exiting {current_asset}: {e}")
                
                # Set pending rotation - will enter on next day's open
                if best_ticker is not None:
                    pending_rotation = best_ticker
                    pending_rotation_date = date
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
                    current_asset = None
                    entry_price = None
                    entry_date = None
                    pending_rotation = None
                    pending_rotation_date = None
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
            entry_price_for_point = entry_price if current_asset else None
            entry_date_for_point = entry_date.strftime('%Y-%m-%d') if entry_date else None
            current_price_for_point = current_price if current_asset and entry_price else None
            
            # If we just rotated out, use exit price; otherwise use current price
            exit_price_for_point = exit_price_recorded if rotation_occurred and exit_price_recorded else None
            
            # Update equity for next iteration (for max equity tracking)
            equity = current_equity
            
            # Determine rotation asset - show marker when entering a new asset
            rotation_asset = None
            rotation_to_show = False
            if rotation_occurred:
                if current_asset:  # Entering a new asset - show the asset name
                    rotation_asset = current_asset
                    rotation_to_show = True
                # When exiting to cash, we don't show a rotation marker (only show when entering assets)
            
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
            
            # Final safety check - ensure asset_for_display is never None or empty
            if not asset_for_display or asset_for_display == '':
                print(f"  [!] CRITICAL ERROR: asset_for_display is None/empty on {date.strftime('%Y-%m-%d')}, forcing to pending_previous_asset={pending_previous_asset}")
                asset_for_display = pending_previous_asset if pending_previous_asset else 'CASH'
            
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
                'exit_price': exit_price_for_point,
                'is_transition': is_transition  # Flag to indicate we're in transition (not actual CASH)
            })
            
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
        current_best = current_asset if current_asset else "N/A"
        final_equity = equity_curve[-1]['equity'] if equity_curve else initial_capital
        
        # Fetch S&P 500 data for comparison
        sp500_data = None
        sp500_returns = []
        try:
            print("  Fetching S&P 500 data for comparison...")
            # Fetch more data to ensure we have coverage
            sp500 = download_stock_data("^GSPC", period="3y", interval="1d", max_retries=3, delay=0.5)
            if not sp500.empty:
                # Handle MultiIndex columns
                if isinstance(sp500.columns, pd.MultiIndex):
                    sp500 = sp500.droplevel(0, axis=1)
                
                if 'Close' in sp500.columns:
                    sp500_close = sp500['Close']
                    sp500_dates = pd.to_datetime(sp500.index)
                    
                    # Calculate S&P 500 returns (percentage from backtest start date)
                    if len(sp500_close) > 0 and len(all_dates) > start_index:
                        # Find S&P 500 price at backtest start date
                        backtest_start_date = all_dates[start_index]
                        sp500_start_idx = sp500_dates.get_indexer([backtest_start_date], method='nearest')[0]
                        if sp500_start_idx >= 0 and sp500_start_idx < len(sp500_close):
                            sp500_start = sp500_close.iloc[sp500_start_idx]
                            print(f"  S&P 500 start price: ${sp500_start:.2f} on {backtest_start_date.strftime('%Y-%m-%d')}")
                            
                            for date in all_dates[start_index:]:
                                # Find closest date in S&P 500 data
                                date_idx = sp500_dates.get_indexer([date], method='nearest')[0]
                                if date_idx >= 0 and date_idx < len(sp500_close):
                                    sp500_price = sp500_close.iloc[date_idx]
                                    sp500_return = ((sp500_price - sp500_start) / sp500_start) * 100
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
                            print(f"  [!] Could not find S&P 500 start price for {backtest_start_date}")
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
        best_ticker = max(date_scores.items(), key=lambda x: x[1])[0] if date_scores else None
        
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
    current_best = current_asset if current_asset else "N/A"
    
    return {
        'equity_curve': equity_curve,
        'asset_periods': asset_periods,
        'max_drawdown': max_drawdown * 100,  # As percentage
        'max_hold_period': max_hold,
        'min_hold_period': min_hold,
        'current_best_asset': current_best,
        'final_equity': equity,
        'total_return': ((equity - initial_capital) / initial_capital) * 100
    }

# --- NEW API ENDPOINT ---
# Cache file path
CACHE_FILE = 'analysis_cache.json'

def load_cache():
    """Load analysis results from cache file"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"  [!] Error loading cache: {e}")
            return None
    return None

def save_cache(data):
    """Save analysis results to cache file"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"  ✓ Cache saved to {CACHE_FILE}")
    except Exception as e:
        print(f"  [!] Error saving cache: {e}")

@app.route('/analyze', methods=['GET'])
def get_analysis_results():
    """
    This function replaces main() and is called by the frontend.
    It formats the results to match what the frontend expects.
    """
    try:
        import time
        import sys
        start_time = time.time()
        # Force flush to ensure logs appear immediately
        print(f"\n{'='*60}", flush=True)
        print(f"Received request at /analyze endpoint (PID: {os.getpid()})...", flush=True)
        print(f"{'='*60}", flush=True)
        sys.stdout.flush()
        
        # Check if we should use cache or force refresh
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'
        
        # Try to load from cache first (unless force refresh)
        if not force_refresh:
            cached_data = load_cache()
            if cached_data:
                elapsed = time.time() - start_time
                print(f"✓ Loading data from cache... (took {elapsed:.2f}s)")
                return jsonify(cached_data)
        
        if force_refresh:
            print("  Force refresh requested - recalculating all values...")
        else:
            print("  No cache found - calculating fresh data (this may take 3-5 minutes)...")
        
        # Collect all tickers first
        all_tickers = []
        ticker_to_sector = {}
        for sector, tickers in SECTORS.items():
            for ticker in tickers:
                all_tickers.append(ticker)
                ticker_to_sector[ticker] = sector
        
        print(f"  Downloading data for {len(all_tickers)} stocks individually (to avoid rate limits)...")
        
        # Add a long initial delay to avoid immediate rate limits from Render's IP
        # Render's IP may already be rate-limited from previous attempts
        print("  Waiting 120 seconds before first download attempt to avoid rate limits...")
        for i in range(120, 0, -10):
            print(f"  Waiting... {i}s remaining", end='\r', flush=True)
            time.sleep(10)
        print("\n  Delay complete, starting individual downloads with 20s delays...")
        
        # Skip batch download entirely - use individual downloads from the start
        # This is slower but more reliable for rate-limited IPs
        batch_data = {}
        download_delay = 20  # 20 seconds between downloads
        rate_limit_wait = 60  # 60 seconds if rate limited
        
        for idx, ticker in enumerate(all_tickers, 1):
            max_retries = 3
            for retry in range(max_retries):
                try:
                    print(f"  [{idx}/{len(all_tickers)}] Downloading {ticker}...", flush=True)
                    # Use Ticker class - different API endpoint, potentially less rate-limited
                    ticker_obj = yf.Ticker(ticker)
                    ticker_obj.session = None  # Disable cache
                    ticker_data = ticker_obj.history(period="2y", interval="1d", timeout=60)
                    
                    if not ticker_data.empty:
                        batch_data[ticker] = ticker_data
                        print(f"    ✓ {ticker} downloaded successfully", flush=True)
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
            
            # Wait between downloads (except after the last one)
            if idx < len(all_tickers):
                time.sleep(download_delay)
        
        # Check if we got any data
        if not batch_data:
            raise Exception("Failed to download any stock data after multiple attempts.")
        
        print(f"  ✓ Successfully downloaded {len(batch_data)}/{len(all_tickers)} stocks")
        
        # Process downloaded data
        results = []
        for sector, tickers in SECTORS.items():
            print(f"\n--- Processing Sector: {sector} ---")
            for ticker in tickers:
                try:
                    print(f"  Analyzing {ticker}...")
                    
                    # Get data from batch or download individually
                    if ticker in batch_data and not batch_data[ticker].empty:
                        data = batch_data[ticker]
                    else:
                        # Fallback: download individually with long delays
                        print(f"    Data not in batch, downloading individually with 10s delay...")
                        data = download_stock_data(ticker, period="2y", interval="1d", max_retries=3, delay=10.0)
                    
                    if data.empty:
                        print(f"  No data for {ticker}, skipping.")
                        continue
                    
                    # Handle MultiIndex columns from yfinance
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = data.columns.droplevel(1)
                    
                    result = analyze_stock(ticker, data, CONFIG)
                    
                    if result is not None and isinstance(result, dict):
                        z_avg = result.get("z_avg", 0.0)
                        avg_score = result.get("avg_score", 0.0)
                        results.append({
                            "sector": sector, 
                            "ticker": ticker, 
                            "z_avg": z_avg,
                            "avg_score": avg_score
                        })
                        print(f"  ✓ {ticker}: z_avg = {z_avg:.3f}, avg_score = {avg_score:.3f}")
                    else:
                        print(f"  ✗ {ticker}: Failed to calculate scores")
                        
                except Exception as e:
                    print(f"  ✗ Error processing {ticker}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue

        if not results:
            print("\n⚠ No results calculated - returning error")
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

        # --- Ratio Analysis and Backtesting ---
        print("\n--- Starting Ratio Analysis and Backtesting ---")
        ratio_analysis = None
        backtest_results = None
        
        try:
            # Get all unique tickers - SORT for deterministic results
            all_tickers = sorted(list(results_df['ticker'].unique()))
            print(f"  Calculating ratio analysis for {len(all_tickers)} stocks...")
            
            # Calculate ratio scores: each stock against all others
            ratio_scores = {}
            total_comparisons = len(all_tickers) * (len(all_tickers) - 1)
            print(f"  Total comparisons needed: {total_comparisons}")
            
            # Limit to avoid too many API calls and timeout - compare each stock against top 5 others
            # Reduced from 50 to 5 to speed up processing and avoid timeouts
            comparison_limit = min(5, len(all_tickers) - 1)
            
            for i, ticker1 in enumerate(all_tickers):
                if i % 10 == 0:
                    print(f"  Progress: {i}/{len(all_tickers)} stocks analyzed...")
                
                ratio_z_scores = []
                comparisons_made = 0
                
                # Compare against other stocks - use sorted list for deterministic order
                for ticker2 in all_tickers:
                    if ticker1 == ticker2:
                        continue
                    
                    if comparisons_made >= comparison_limit:
                        break
                    
                    # Calculate ratio avg_score (ticker1/ticker2)
                    try:
                        ratio_score = calculate_ratio_avg_score(ticker1, ticker2, CONFIG)
                        if ratio_score is not None:
                            ratio_z_scores.append(ratio_score)
                    except Exception as e:
                        print(f"    Error calculating ratio for {ticker1}/{ticker2}: {e}")
                        # Continue with next comparison
                    
                    comparisons_made += 1
                
                if ratio_z_scores:
                    # Average z-score from all ratio comparisons
                    avg_ratio_score = sum(ratio_z_scores) / len(ratio_z_scores)
                    ratio_scores[ticker1] = avg_ratio_score
                    print(f"  {ticker1}: {avg_ratio_score:.3f} (from {len(ratio_z_scores)} comparisons)")
            
            # Sort by ratio score
            sorted_ratio_stocks = sorted(ratio_scores.items(), key=lambda x: x[1], reverse=True)
            top_ratio_stocks = sorted_ratio_stocks[:10]  # Top 10 for backtesting
            
            print(f"  Top stocks by ratio analysis: {[s[0] for s in top_ratio_stocks[:5]]}")
            
            # Perform historical backtest using ratio scores
            backtest_results = perform_historical_backtest(top_ratio_stocks, CONFIG)
            
            ratio_analysis = {
                "top_stocks": [{"ticker": ticker, "ratio_score": score} for ticker, score in top_ratio_stocks[:10]],
                "current_best": top_ratio_stocks[0][0] if top_ratio_stocks else "N/A"
            }
            
        except Exception as e:
            print(f"  [!] Error in ratio analysis/backtesting: {e}")
            import traceback
            traceback.print_exc()

        print(f"\n✓ Analysis complete. Processed {len(results)} stocks across {len(output_sectors)} sectors.")
        print("Sending JSON response to frontend.")
        
        response_data = {
            "sectors": output_sectors,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        if ratio_analysis:
            response_data["ratio_analysis"] = ratio_analysis
        if backtest_results:
            response_data["backtest"] = backtest_results
        
        # Save to cache
        save_cache(response_data)
        
        elapsed = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"✓ Analysis complete! Total time: {elapsed:.2f}s ({elapsed/60:.2f} minutes)")
        print(f"{'='*60}\n")
        
        return jsonify(response_data)
        
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
        
        # Also print to stderr
        print(tb_str, file=sys.stderr)
        sys.stderr.flush()
        
        # Return error response
        return jsonify({
            "error": f"Server error: {error_msg}",
            "error_type": error_type
        }), 500


# --- Run Flask Server ---
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
    app.run(host='0.0.0.0', port=port, debug=False)

