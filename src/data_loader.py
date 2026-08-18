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

    Returns an empty DataFrame if market data have not yet
    been refreshed.
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


def load_deep_dives():
    """
    Load Stage 2 analyst deep-dive judgments.

    Returns an empty DataFrame when no Stage 2 file exists.
    """

    path = DATA_DIR / "deep_dives.csv"

    if not path.exists():
        return pd.DataFrame(
            columns=[
                "ticker",
                "review_status",
                "core_thesis",
                "analyst_verdict",
                "confidence",
                "last_reviewed",
            ]
        )

    return pd.read_csv(path)


def load_deep_dive_evidence():
    """
    Load the Stage 2 claim-level evidence and
    fact-vs-inference audit trail.
    """

    path = DATA_DIR / "deep_dive_evidence.csv"

    if not path.exists():
        return pd.DataFrame(
            columns=[
                "ticker",
                "claim_area",
                "claim_type",
                "source_type",
                "source_title",
                "source_date",
                "source_url",
                "evidence",
                "verified",
            ]
        )

    return pd.read_csv(path)


# ================================================================
# MACHINE STATE HISTORY
# ================================================================

def load_state_history():
    """
    Load historical machine-state snapshots.

    Each snapshot records both structured inputs and the
    machine interpretation produced from those inputs.
    """

    path = DATA_DIR / "state_history.csv"

    if not path.exists():
        return pd.DataFrame()

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


# ================================================================
# STAGE 2 LOOKUPS
# ================================================================

def get_deep_dive(ticker):
    """
    Return the current Stage 2 analyst assessment
    for one company.
    """

    deep_dives = load_deep_dives()

    if deep_dives.empty:
        return None

    match = deep_dives[
        deep_dives["ticker"]
        .astype(str)
        .str.upper()
        .eq(str(ticker).upper())
    ]

    if match.empty:
        return None

    return match.iloc[0]


def get_deep_dive_evidence(ticker):
    """
    Return the Stage 2 evidence trail for one company.
    """

    evidence = load_deep_dive_evidence()

    if evidence.empty:
        return evidence

    return evidence[
        evidence["ticker"]
        .astype(str)
        .str.upper()
        .eq(str(ticker).upper())
    ].copy()
