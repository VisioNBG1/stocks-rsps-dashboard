# Stock Sector Trending Dashboard

A live dashboard that compares stock sectors and individual stocks based on a comprehensive z-score analysis derived from 12 technical indicators. The dashboard identifies which sectors and stocks are trending the most versus those that are mean-reverting.

## Features

- **Sector Comparison**: Compare average z-scores across different market sectors
- **Individual Stock Analysis**: View z-scores for each stock within a sector
- **Real-time Data**: Uses yfinance to fetch live market data
- **12-Factor Analysis**: Calculates z-scores from:
  1. ADX (Average Directional Index)
  2. ADF (Augmented Dickey-Fuller Test)
  3. KPSS (Kwiatkowski-Phillips-Schmidt-Shin Test)
  4. ATR (Average True Range)
  5. GARCH Volatility
  6. Half-Life of Mean Reversion
  7. Wavelet Volatility
  8. Price/Momentum Correlation
  9. Choppiness Index
  10. Hurst Exponent
  11. Phillips-Perron Test
  12. Yang Volatility

## Understanding Z-Scores

- **Positive Z-Score**: Indicates a trending market (higher = more trending)
- **Negative Z-Score**: Indicates a mean-reverting market (lower = more mean-reverting)
- **Near Zero**: Neutral/transitional market state

## Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
python stock_dashboard_backend.py
```

The server will start on `http://localhost:5000`

### 3. Open the Dashboard

Open `dashboard.html` in your web browser. The dashboard will automatically connect to the backend API.

## Configuration

All indicator parameters can be modified in the `CONFIG` dictionary in `stock_dashboard_backend.py`. These match the settings from your PineScript TradingView indicator:

- `z_score_len`: 50 (rolling window for z-score calculation)
- `adx_smoothing`: 14
- `di_length`: 22
- `kpss_length`: 36
- `adf_length`: 40
- `garch_alpha`: 0.10
- `garch_beta`: 0.80
- And more...

## Stock Sectors

The dashboard currently analyzes these sectors:

- Technology: AAPL, MSFT, GOOGL, NVDA, AMD
- Energy: XOM, CVX, SLB, MRO
- Health Care: JNJ, PFE, LLY, UNH
- Industrials: BA, CAT, DE, HON
- Utilities: NEE, SO, DUK
- Consumer Staples: PG, KO, WMT, COST

You can modify the `SECTORS` dictionary in `stock_dashboard_backend.py` to add or change stocks.

## Auto-Refresh

The dashboard automatically refreshes every 5 minutes. You can also manually refresh by clicking the "🔄 Refresh Data" button.

## API Endpoint

The backend provides a single API endpoint:

- `GET /analyze`: Returns JSON data with sectors and their stocks, sorted by z-score

## Troubleshooting

- **Connection Error**: Make sure the Flask server is running on port 5000
- **No Data**: Check your internet connection and ensure yfinance can access market data
- **Slow Loading**: The first request may take 30-60 seconds as it downloads data for all stocks

## License

This project is for educational and personal use.

