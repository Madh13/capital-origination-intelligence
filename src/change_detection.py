import math

import pandas as pd

from src.intelligence import assess_company
from src.fundability import (
    assess_fundability,
    integrate_origination_view,
)


# ================================================================
# HELPERS
# ================================================================

def _number(value):
    try:
        if pd.isna(value):
            return None

        return float(value)

    except (TypeError, ValueError):
        return None


def _same_number(a, b, tolerance=1e-9):
    a = _number(a)
    b = _number(b)

    if a is None and b is None:
        return True

    if a is None or b is None:
        return False

    return math.isclose(
        a,
        b,
        rel_tol=tolerance,
        abs_tol=tolerance,
    )


def _material_numeric_change(field, old_value, new_value):
    """
    Ignore immaterial numerical noise while retaining changes
    that could reasonably matter for origination monitoring.
    """

    old = _number(old_value)
    new = _number(new_value)

    if old is None and new is None:
        return False

    if old is None or new is None:
        return True

    absolute_change = abs(new - old)

    relative_change = (
        absolute_change / abs(old)
        if old != 0
        else float("inf")
    )

    thresholds = {
        "cash_aud_m": {
            "absolute": 0.05,
            "relative": 0.02,
        },
        "reported_quarters_funding": {
            "absolute": 0.25,
            "relative": 0.05,
        },
        "avg_daily_value_20d_aud_m": {
            "absolute": 0.01,
            "relative": 0.20,
        },
        "return_1m_pct": {
            "absolute": 5.0,
            "relative": float("inf"),
        },
        "return_3m_pct": {
            "absolute": 5.0,
            "relative": float("inf"),
        },
    }

    rule = thresholds.get(field)

    if rule is None:
        return not _same_number(
            old,
            new,
        )

    return (
        absolute_change >= rule["absolute"]
        or relative_change >= rule["relative"]
    )


# ================================================================
# BUILD MACHINE STATE
# ================================================================

def build_machine_state(
    companies,
    sources,
    market_data,
):
    """
    Convert raw company, evidence and market data into the
    machine's interpreted state for every company.
    """

    rows = []

    for _, company in companies.iterrows():

        ticker = (
            str(company["ticker"])
            .upper()
            .strip()
        )

        company_sources = sources[
            sources["ticker"]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ].copy()


        market_match = market_data[
            market_data["ticker"]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ]

        market = (
            market_match.iloc[0]
            if not market_match.empty
            else None
        )


        timing = assess_company(
            company,
            company_sources,
        )


        fundability = assess_fundability(
            company,
            market,
        )


        integrated = integrate_origination_view(
            timing,
            fundability,
        )


        rows.append(
            {
                "ticker": ticker,

                # ------------------------------
                # RAW / STRUCTURED STATE
                # ------------------------------

                "cash_aud_m": _number(
                    company.get(
                        "cash_aud_m"
                    )
                ),

                "reported_quarters_funding": _number(
                    company.get(
                        "reported_quarters_funding"
                    )
                ),

                "avg_daily_value_20d_aud_m": (
                    _number(
                        market.get(
                            "avg_daily_value_traded_20d_aud_m"
                        )
                    )
                    if market is not None
                    else None
                ),

                "return_1m_pct": (
                    _number(
                        market.get(
                            "return_1m_pct"
                        )
                    )
                    if market is not None
                    else None
                ),

                "return_3m_pct": (
                    _number(
                        market.get(
                            "return_3m_pct"
                        )
                    )
                    if market is not None
                    else None
                ),

                # ------------------------------
                # MACHINE INTERPRETATION
                # ------------------------------

                "funding_timing": timing[
                    "funding_timing"
                ],

                "financing_recency": timing[
                    "financing_recency"
                ],

                "catalyst_visibility": timing[
                    "catalyst_visibility"
                ],

                "data_confidence": timing[
                    "data_confidence"
                ],

                "fundability": fundability[
                    "fundability"
                ],

                "liquidity": fundability[
                    "liquidity"
                ],

                "integrated_view": integrated,
            }
        )


    return pd.DataFrame(rows)


# ================================================================
# DETECT CHANGES
# ================================================================

def detect_changes(
    previous,
    current,
):
    """
    Compare two machine states and return material changes.
    """

    changes = []

    previous = previous.set_index(
        "ticker"
    )

    current = current.set_index(
        "ticker"
    )


    tickers = sorted(
        set(previous.index)
        | set(current.index)
    )


    numeric_fields = {
        "cash_aud_m": "Cash",
        "reported_quarters_funding": (
            "Reported Funding"
        ),
        "avg_daily_value_20d_aud_m": (
            "20D Avg Daily Value"
        ),
        "return_1m_pct": (
            "1M Price Change"
        ),
        "return_3m_pct": (
            "3M Price Change"
        ),
    }


    category_fields = {
        "funding_timing": (
            "Funding Timing"
        ),
        "financing_recency": (
            "Financing Recency"
        ),
        "catalyst_visibility": (
            "Catalyst Visibility"
        ),
        "data_confidence": (
            "Data Confidence"
        ),
        "fundability": (
            "Fundability"
        ),
        "liquidity": (
            "Liquidity"
        ),
        "integrated_view": (
            "Integrated Origination View"
        ),
    }


    for ticker in tickers:

        if ticker not in previous.index:
            changes.append(
                {
                    "ticker": ticker,
                    "field": "Universe",
                    "old_value": None,
                    "new_value": "NEW COMPANY",
                    "change_type": "NEW",
                }
            )

            continue


        if ticker not in current.index:
            changes.append(
                {
                    "ticker": ticker,
                    "field": "Universe",
                    "old_value": "ACTIVE",
                    "new_value": "REMOVED",
                    "change_type": "REMOVED",
                }
            )

            continue


        old = previous.loc[
            ticker
        ]

        new = current.loc[
            ticker
        ]


        # --------------------------------------------------------
        # NUMERIC CHANGES
        # --------------------------------------------------------

        for field, label in numeric_fields.items():

            old_value = old.get(
                field
            )

            new_value = new.get(
                field
            )


            if _material_numeric_change(
                field,
                old_value,
                new_value,
            ):

                changes.append(
                    {
                        "ticker": ticker,
                        "field": label,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change_type": "DATA",
                    }
                )


        # --------------------------------------------------------
        # INTERPRETATION CHANGES
        # --------------------------------------------------------

        for field, label in category_fields.items():

            old_value = old.get(
                field
            )

            new_value = new.get(
                field
            )


            if str(old_value) != str(
                new_value
            ):

                changes.append(
                    {
                        "ticker": ticker,
                        "field": label,
                        "old_value": old_value,
                        "new_value": new_value,
                        "change_type": "INTELLIGENCE",
                    }
                )


    return pd.DataFrame(
        changes
    )


# ================================================================
# MACHINE PRE-BRIEF
# ================================================================

def build_change_brief(
    ticker,
    previous,
    current,
):
    """
    Generate a simple explainable machine pre-brief describing
    how the system's view changed.
    """

    ticker = str(
        ticker
    ).upper()


    old_match = previous[
        previous["ticker"] == ticker
    ]

    new_match = current[
        current["ticker"] == ticker
    ]


    if old_match.empty:
        return (
            f"{ticker} is new to the "
            "screening universe."
        )


    if new_match.empty:
        return (
            f"{ticker} has been removed "
            "from the screening universe."
        )


    old = old_match.iloc[0]
    new = new_match.iloc[0]


    statements = []


    if (
        str(old["integrated_view"])
        != str(new["integrated_view"])
    ):
        statements.append(
            "Integrated origination view moved "
            f"from {old['integrated_view']} "
            f"to {new['integrated_view']}."
        )


    if (
        str(old["funding_timing"])
        != str(new["funding_timing"])
    ):
        statements.append(
            "Funding timing changed "
            f"from {old['funding_timing']} "
            f"to {new['funding_timing']}."
        )


    old_runway = _number(
        old[
            "reported_quarters_funding"
        ]
    )

    new_runway = _number(
        new[
            "reported_quarters_funding"
        ]
    )


    if not _same_number(
        old_runway,
        new_runway,
    ):
        old_text = (
            "not available"
            if old_runway is None
            else f"{old_runway:.2f} quarters"
        )

        new_text = (
            "not available"
            if new_runway is None
            else f"{new_runway:.2f} quarters"
        )

        statements.append(
            "Reported funding changed "
            f"from {old_text} "
            f"to {new_text}."
        )


    if (
        str(old["data_confidence"])
        != str(new["data_confidence"])
    ):
        statements.append(
            "Evidence confidence changed "
            f"from {old['data_confidence']} "
            f"to {new['data_confidence']}."
        )


    if (
        str(old["fundability"])
        != str(new["fundability"])
    ):
        statements.append(
            "Fundability changed "
            f"from {old['fundability']} "
            f"to {new['fundability']}."
        )


    if not statements:
        return (
            f"No material machine-state change "
            f"was detected for {ticker}."
        )


    return " ".join(
        statements
    )
