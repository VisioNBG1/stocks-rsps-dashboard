"""Count unique stocks in SECTORS dictionary"""
SECTORS = {
    "Technology": [
        "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "TSLA", "AVGO", "ORCL",
        "AMD", "INTC", "CRM", "ADBE", "CSCO", "TXN", "QCOM", "NOW", "AMAT", "MU",
        "LRCX", "KLAC", "SNPS", "CDNS", "INTU", "FTNT", "PANW", "CRWD", "ZS",
        "NET", "DDOG", "TEAM", "DOCN", "MDB", "SNOW", "PLTR", "RPD", "ESTC"
    ],
    "Energy": [
        "XOM", "CVX", "SLB", "EOG", "COP", "MPC", "PSX", "VLO", "HAL",
        "OXY", "DVN", "FANG", "CTRA", "APA", "BKR", "NOV", "FTI", "RIG",
        "HP", "LBRT", "NBR", "PTEN", "WFRD", "VTLE", "SM", "CIVI", "MGY", "MTDR"
    ],
    "Health Care": [
        "JNJ", "PFE", "LLY", "UNH", "ABBV", "TMO", "ABT", "DHR", "BMY", "AMGN",
        "GILD", "CI", "HUM", "CVS", "ELV", "CNC", "MOH", "MRNA", "BIIB", "REGN",
        "VRTX", "ALNY", "IONS", "FOLD", "ARWR", "SGMO", "BEAM", "NTLA", "EDIT",
        "ZTS", "IDXX", "ALGN", "ISRG", "SYK", "BAX", "EW", "BSX", "ZBH", "HOLX"
    ],
    "Industrials": [
        "BA", "CAT", "DE", "HON", "GE", "RTX", "LMT", "NOC", "GD", "TDG",
        "ETN", "EMR", "ITW", "PH", "AME", "DOV", "FTV", "GGG", "PNR", "ROK",
        "CMI", "PCAR", "WAB", "KNX", "JBHT", "ODFL", "XPO", "CHRW", "EXPD", "FDX",
        "UPS", "AAL", "DAL", "LUV", "UAL", "JBLU", "ALK", "SKYW"
    ],
    "Utilities": [
        "NEE", "SO", "DUK", "AEP", "SRE", "EXC", "XEL", "ES", "EIX", "PEG",
        "ED", "FE", "AES", "VST", "CEG", "PCG", "ETR", "CMS", "ATO", "LNT",
        "WEC", "CNP", "NI", "OGE", "PNW", "POR", "IDA", "SWX", "NWN", "RGCO"
    ],
    "Consumer Staples": [
        "PG", "KO", "WMT", "COST", "PEP", "CL", "MDLZ", "GIS", "KMB", "HSY",
        "SJM", "CPB", "CAG", "HRL", "TSN", "BG", "ADM", "LW", "FLO", "SJM",
        "TGT", "HD", "LOW", "TJX", "ROST", "BBWI", "DKS", "ANF", "AEO"
    ],
    "Financials": [
        "JPM", "BAC", "WFC", "C", "GS", "MS", "BLK", "SCHW", "AXP", "COF",
        "USB", "PNC", "TFC", "BK", "STT", "BEN", "IVZ", "AMTD", "HOOD",
        "V", "MA", "PYPL", "FIS", "FISV", "GPN", "FLYW", "AFRM", "UPST", "SOFI"
    ],
    "Consumer Discretionary": [
        "AMZN", "TSLA", "NKE", "SBUX", "MCD", "YUM", "CMG", "DPZ", "WING", "CAVA",
        "DIS", "NFLX", "WBD", "FOXA", "ROKU", "FUBO", "DKNG", "PENN", "LNW",
        "F", "GM", "STLA", "HMC", "TM", "RIVN", "LCID", "FISK"
    ],
    "Real Estate": [
        "AMT", "PLD", "EQIX", "PSA", "WELL", "VICI", "SPG", "O", "DLR", "EXPI",
        "CBRE", "JLL", "CWK", "REXR", "STAG", "FR", "BRX", "BXP", "KIM", "REG",
        "MAC", "SLG", "VTR", "CTRE", "DOC", "MPW", "OHI", "GMRE"
    ],
    "Materials": [
        "LIN", "APD", "ECL", "SHW", "PPG", "DD", "DOW", "FCX", "NEM", "VALE",
        "RIO", "BHP", "SCCO", "TECK", "AA", "CLF", "STLD", "NUE", "CMC",
        "RS", "WLK", "LYB", "CE", "FMC", "MOS", "NTR", "CF", "CTVA", "ADM"
    ],
    "Communication Services": [
        "GOOGL", "GOOG", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS", "LUMN",
        "WBD", "FOXA", "NWSA", "NWS", "IAC", "ANGI", "TRIP", "EXPE", "BKNG",
        "ABNB", "UBER", "LYFT", "GRAB", "BIDU", "JD", "PDD", "BABA", "TME"
    ]
}

# Collect all tickers
all_tickers = []
for sector, tickers in SECTORS.items():
    all_tickers.extend(tickers)

# Count unique tickers
unique_tickers = sorted(list(set(all_tickers)))
total_unique = len(unique_tickers)

# Find duplicates within sectors
duplicates = {}
for ticker in all_tickers:
    count = all_tickers.count(ticker)
    if count > 1:
        if ticker not in duplicates:
            duplicates[ticker] = count

print("=" * 60)
print("STOCK COUNT ANALYSIS")
print("=" * 60)
print(f"\nTotal tickers (with duplicates): {len(all_tickers)}")
print(f"Unique tickers: {total_unique}")
print(f"\nExpected: 334")
print(f"Actual: {total_unique}")
print(f"Difference: {334 - total_unique}")

if duplicates:
    print(f"\n⚠️  Found {len(duplicates)} tickers that appear multiple times:")
    for ticker, count in sorted(duplicates.items()):
        print(f"   {ticker}: appears {count} times")

# Check for "X" (should be removed)
if "X" in unique_tickers:
    print(f"\n⚠️  'X' is still in the list (should be removed)")
    unique_tickers.remove("X")
    print(f"After removing 'X': {len(unique_tickers)} unique tickers")

print(f"\n✅ Final unique count: {len(unique_tickers)}")
print(f"\nFirst 20: {', '.join(unique_tickers[:20])}")
print(f"Last 20: {', '.join(unique_tickers[-20:])}")

