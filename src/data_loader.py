from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


# ================================================================
# LOADERS
# ================================================================

def load_companies():
    """Load the company screening universe."""
    return pd.read_csv(
        DATA_DIR / "companies.csv"
    )


def load_sources():
    """Load the evidence ledger."""
    return pd.read_csv(
        DATA_DIR / "sources.csv"
    )


def load_market_data():
    """
    Load the most recently cached dynamic market-data snapshot.

    Returns an empty DataFrame if the market-data refresh has not
    yet been run.
    """

    path = DATA_DIR / "market_data.csv"

    if not path.exists():
        return pd.DataFrame(
            columns=[
                "ticker",
                "latest_market_date",
                "latest_price_aud",
                "avg_daily_volume_20d",
                "avg_daily_value_traded_20d_aud_m",
                "return_1m_pct",
                "return_3m_pct",
                "refresh_status",
            ]
        )

    return pd.read_csv(path)


# ================================================================
# COMPANY LOOKUPS
# ================================================================

def get_company(ticker):
    """Return one company record by ASX ticker."""

    companies = load_companies()

    match = companies[
        companies["ticker"]
        .astype(str)
        .str.upper()
        .eq(str(ticker).upper())
    ]

    if match.empty:
        return None

    return match.iloc[0]


def get_company_sources(ticker):
    """Return evidence records associated with one company."""

    sources = load_sources()

    return sources[
        sources["ticker"]
        .astype(str)
        .str.upper()
        .eq(str(ticker).upper())
    ].copy()


def get_market_snapshot(ticker):
    """Return the latest cached market snapshot for one company."""

    market = load_market_data()

    if market.empty:
        return None

    match = market[
        market["ticker"]
        .astype(str)
        .str.upper()
        .eq(str(ticker).upper())
    ]

    if match.empty:
        return None

    return match.iloc[0]
