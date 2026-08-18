from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


def load_companies():
    """Load the company screening universe."""
    return pd.read_csv(DATA_DIR / "companies.csv")


def load_sources():
    """Load the evidence/source ledger."""
    return pd.read_csv(DATA_DIR / "sources.csv")


def get_company(ticker):
    """Return one company record by ASX ticker."""
    companies = load_companies()

    match = companies[
        companies["ticker"].str.upper() == ticker.upper()
    ]

    if match.empty:
        return None

    return match.iloc[0]


def get_company_sources(ticker):
    """Return all evidence records associated with one company."""
    sources = load_sources()

    return sources[
        sources["ticker"].str.upper() == ticker.upper()
    ].copy()
