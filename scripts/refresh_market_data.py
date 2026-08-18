from pathlib import Path
import sys


# ================================================================
# PROJECT PATH SETUP
# ================================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# Imports from our project must come AFTER root path setup.
import pandas as pd

from src.data_loader import load_companies
from src.market_data import fetch_market_snapshot


OUTPUT_PATH = ROOT_DIR / "data" / "market_data.csv"


# ================================================================
# MARKET DATA REFRESH
# ================================================================

def main():
    companies = load_companies()

    results = []

    print()
    print("Refreshing market data...")
    print("-" * 70)

    for ticker in companies["ticker"]:
        ticker = str(ticker).upper().strip()

        print(f"{ticker}: ", end="")

        try:
            result = fetch_market_snapshot(ticker)

            results.append(result)

            print(
                f"OK | "
                f"Price A${result['latest_price_aud']:.3f} | "
                f"20D ADV "
                f"A${result['avg_daily_value_traded_20d_aud_m']:.3f}m"
            )

        except Exception as exc:
            results.append(
                {
                    "ticker": ticker,
                    "yahoo_ticker": f"{ticker}.AX",
                    "latest_market_date": None,
                    "latest_price_aud": None,
                    "avg_daily_volume_20d": None,
                    "avg_daily_value_traded_20d_aud_m": None,
                    "return_1m_pct": None,
                    "return_3m_pct": None,
                    "trading_days_available": None,
                    "refreshed_at_utc": None,
                    "market_data_source": (
                        "Yahoo Finance via yfinance"
                    ),
                    "refresh_status": "FAILED",
                    "refresh_error": str(exc),
                }
            )

            print(f"FAILED | {exc}")

    output = pd.DataFrame(results)

    output.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("-" * 70)
    print(
        f"Saved {len(output)} records to "
        f"{OUTPUT_PATH}"
    )

    successful = int(
        (output["refresh_status"] == "SUCCESS").sum()
    )

    failed = int(
        (output["refresh_status"] == "FAILED").sum()
    )

    print(f"Successful: {successful}")
    print(f"Failed: {failed}")


if __name__ == "__main__":
    main()
