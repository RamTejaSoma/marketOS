import json
from pathlib import Path

import pandas as pd
import yfinance as yf


# ============================================================
# MARKET UNIVERSE
# ============================================================

MARKET_UNIVERSE = {

    # Major indices
    "indices": {
        # US
        "^GSPC": "S&P 500",
        "^NDX": "Nasdaq-100",
        "^DJI": "Dow Jones",

        # India
        "^NSEI": "NIFTY 50",
        "^NSEBANK": "NIFTY Bank",
        "^BSESN": "Sensex",

        # Asia
        "^N225": "Nikkei 225",
        "^HSI": "Hang Seng",
        "000001.SS": "Shanghai Composite",

        # Europe
        "^FTSE": "FTSE 100",
        "^GDAXI": "DAX",
        "^FCHI": "CAC 40",
    },

    # ETFs
    "etfs": {
        "SPY": "S&P 500 ETF",
        "QQQ": "Nasdaq-100 ETF",
        "IWM": "Russell 2000 ETF",
        "EEM": "Emerging Markets ETF",
        "GLD": "Gold ETF",
        "SLV": "Silver ETF",
    },

    # Selected stocks
    "stocks": {
        "AAPL": "Apple",
        "MSFT": "Microsoft",
        "NVDA": "NVIDIA",
        "AMZN": "Amazon",
        "GOOGL": "Alphabet",
        "META": "Meta",
        "TSLA": "Tesla",
    },

    # Sector performance
    "sectors": {
        "XLK": "Technology",
        "XLF": "Financials",
        "XLE": "Energy",
        "XLV": "Healthcare",
        "XLI": "Industrials",
        "XLY": "Consumer Discretionary",
        "XLP": "Consumer Staples",
        "XLU": "Utilities",
        "XLRE": "Real Estate",
        "XLB": "Materials",
        "XLC": "Communication Services",
    },

    # Volatility + interest rates
    "macro_market": {
        "^VIX": "VIX",
        "^TNX": "10-Year Treasury Yield",
    },

    # US futures
    "us_futures": {
        "ES=F": "S&P 500 Futures",
        "NQ=F": "Nasdaq-100 Futures",
        "YM=F": "Dow Futures",
    },

    # Forex
    "forex": {
        "USDINR=X": "USD/INR",
        "EURUSD=X": "EUR/USD",
        "USDJPY=X": "USD/JPY",
        "GBPUSD=X": "GBP/USD",
        "USDCNY=X": "USD/CNY",
    },

    # Commodities
    "commodities": {
        "GC=F": "Gold",
        "SI=F": "Silver",
        "CL=F": "WTI Crude",
        "BZ=F": "Brent Crude",
        "HG=F": "Copper",
        "NG=F": "Natural Gas",
    }
}


# ============================================================
# CONFIGURATION
# ============================================================

NO_MEANINGFUL_VOLUME = {
    "indices",
    "forex",
    "macro_market"
}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
OUTPUT_FILE = DATA_DIR / "market_data.json"


# ============================================================
# SYMBOL HELPERS
# ============================================================

def get_all_symbols(universe):
    """Return all symbols from the market universe."""

    symbols = []

    for category in universe.values():
        symbols.extend(category.keys())

    return symbols


# ============================================================
# DOWNLOAD MARKET DATA
# ============================================================

def download_market_data(
    symbols,
    period="5d",
    interval="1d"
):
    """Download market data from Yahoo Finance."""

    data = yf.download(
        tickers=symbols,
        period=period,
        interval=interval,
        auto_adjust=False,
        progress=False,
        group_by="ticker",
        threads=True
    )

    return data


# ============================================================
# EXTRACT INDIVIDUAL SYMBOL DATA
# ============================================================

def extract_symbol_data(data, symbol):
    """Extract price history for one symbol."""

    try:

        if isinstance(data.columns, pd.MultiIndex):

            if symbol not in data.columns.get_level_values(0):
                return None

            df = data[symbol].copy()

        else:
            df = data.copy()

        # Keep only rows with a valid closing price
        df = df.dropna(subset=["Close"])

        return df

    except Exception as e:

        print(f"Error extracting {symbol}: {e}")

        return None


# ============================================================
# CREATE MARKET SNAPSHOT
# ============================================================

def create_market_snapshot(data, universe):
    """Create the latest market snapshot for all symbols."""

    snapshot = {}

    symbol_info = {}

    # Build symbol metadata
    for category, symbols in universe.items():

        for symbol, name in symbols.items():

            symbol_info[symbol] = {
                "category": category,
                "name": name
            }

    # Process every symbol
    for symbol, info in symbol_info.items():

        df = extract_symbol_data(data, symbol)

        if df is None or len(df) < 2:

            print(
                f"Insufficient valid closing-price data: "
                f"{symbol}"
            )

            continue

        latest = df.iloc[-1]
        previous = df.iloc[-2]

        latest_close = latest["Close"]
        previous_close = previous["Close"]

        if pd.isna(latest_close) or pd.isna(previous_close):

            print(f"Invalid price data: {symbol}")

            continue

        change = latest_close - previous_close

        change_pct = (
            change / previous_close * 100
            if previous_close != 0
            else None
        )

        # Volume
        if info["category"] in NO_MEANINGFUL_VOLUME:

            volume = None

        elif (
            "Volume" in df.columns
            and pd.notna(latest["Volume"])
        ):

            volume = int(latest["Volume"])

        else:

            volume = None

        snapshot[symbol] = {

            "name": info["name"],
            "category": info["category"],

            "date": df.index[-1].strftime("%Y-%m-%d"),

            "open": float(latest["Open"]),
            "high": float(latest["High"]),
            "low": float(latest["Low"]),
            "close": float(latest_close),

            "previous_close": float(previous_close),

            "change": float(change),
            "change_pct": float(change_pct),

            "volume": volume
        }

    return snapshot


# ============================================================
# GLOBAL INDICES
# ============================================================

def get_global_indices(snapshot):
    """Group major indices by geographical region."""

    regions = {
        "US": [],
        "India": [],
        "Asia": [],
        "Europe": []
    }

    region_map = {

        "^GSPC": "US",
        "^NDX": "US",
        "^DJI": "US",

        "^NSEI": "India",
        "^NSEBANK": "India",
        "^BSESN": "India",

        "^N225": "Asia",
        "^HSI": "Asia",
        "000001.SS": "Asia",

        "^FTSE": "Europe",
        "^GDAXI": "Europe",
        "^FCHI": "Europe"
    }

    for symbol, region in region_map.items():

        if symbol in snapshot:

            regions[region].append(
                snapshot[symbol]
            )

    return regions


# ============================================================
# CREATE MORNING REPORT DATA
# ============================================================

def create_morning_report(snapshot):
    """Organize market snapshot into the final report structure."""

    report = {

        "global_indices": {
            "US": [],
            "India": [],
            "Asia": [],
            "Europe": []
        },

        "sectors": [],
        "futures": [],
        "stocks": [],
        "etfs": [],
        "forex": [],
        "commodities": [],
        "macro": []
    }

    # --------------------------------------------------------
    # Global indices
    # --------------------------------------------------------

    report["global_indices"] = get_global_indices(
        snapshot
    )

    # --------------------------------------------------------
    # Other categories
    # --------------------------------------------------------

    for symbol, data in snapshot.items():

        category = data["category"]

        if category == "sectors":

            report["sectors"].append(data)

        elif category == "us_futures":

            report["futures"].append(data)

        elif category == "stocks":

            report["stocks"].append(data)

        elif category == "etfs":

            report["etfs"].append(data)

        elif category == "forex":

            report["forex"].append(data)

        elif category == "commodities":

            report["commodities"].append(data)

        elif category == "macro_market":

            report["macro"].append(data)

    # --------------------------------------------------------
    # Sort sectors by performance
    # --------------------------------------------------------

    report["sectors"].sort(
        key=lambda x: x["change_pct"],
        reverse=True
    )

    return report


# ============================================================
# SAVE MARKET DATA
# ============================================================

def save_market_data(
    market_data,
    output_file=OUTPUT_FILE
):
    """Save market data to JSON."""

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            market_data,
            f,
            indent=2,
            ensure_ascii=False,
            default=str
        )

    print(
        f"Market data saved successfully: "
        f"{output_file}"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_market_pipeline():
    """Run the complete market data pipeline."""

    all_symbols = get_all_symbols(
        MARKET_UNIVERSE
    )

    print(
        f"Total symbols: {len(all_symbols)}"
    )

    raw_data = download_market_data(
        all_symbols
    )

    morning_market_data = create_market_snapshot(
        raw_data,
        MARKET_UNIVERSE
    )

    print(
        f"Successfully collected "
        f"{len(morning_market_data)} / "
        f"{len(all_symbols)} symbols"
    )

    morning_report = create_morning_report(
        morning_market_data
    )

    save_market_data(
        morning_report
    )

    return morning_report


# ============================================================
# SCRIPT ENTRY POINT
# ============================================================

if __name__ == "__main__":

    run_market_pipeline()