from datetime import datetime, timezone
from pathlib import Path
import sys


# ================================================================
# PROJECT PATH SETUP
# ================================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(
        0,
        str(ROOT_DIR),
    )


import pandas as pd

from src.data_loader import (
    load_companies,
    load_sources,
    load_market_data,
)

from src.market_data import (
    fetch_market_snapshot,
)

from src.change_detection import (
    build_machine_state,
)


MARKET_OUTPUT_PATH = (
    ROOT_DIR
    / "data"
    / "market_data.csv"
)

STATE_HISTORY_PATH = (
    ROOT_DIR
    / "data"
    / "state_history.csv"
)


# ================================================================
# HELPERS
# ================================================================

def _previous_market_row(
    previous_market,
    ticker,
):
    """
    Return the previous cached market row for a ticker.
    """

    if (
        previous_market is None
        or previous_market.empty
    ):
        return None


    match = previous_market[
        previous_market["ticker"]
        .astype(str)
        .str.upper()
        .eq(str(ticker).upper())
    ]


    if match.empty:
        return None


    return (
        match.iloc[0]
        .to_dict()
    )


def _fallback_market_row(
    ticker,
    previous_row,
    error,
):
    """
    Preserve previously cached market information when a live
    refresh fails, rather than replacing useful data with blanks.
    """

    if previous_row is not None:

        row = dict(
            previous_row
        )

        row["ticker"] = ticker

        row["refresh_status"] = (
            "STALE — REFRESH FAILED"
        )

        row["refresh_error"] = str(
            error
        )

        row["refreshed_at_utc"] = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        return row


    return {
        "ticker": ticker,
        "yahoo_ticker": (
            f"{ticker}.AX"
        ),
        "latest_market_date": None,
        "latest_price_aud": None,
        "avg_daily_volume_20d": None,
        "avg_daily_value_traded_20d_aud_m": None,
        "return_1m_pct": None,
        "return_3m_pct": None,
        "trading_days_available": None,
        "refreshed_at_utc": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "market_data_source": (
            "Yahoo Finance via yfinance"
        ),
        "refresh_status": (
            "FAILED — NO CACHE"
        ),
        "refresh_error": str(
            error
        ),
    }


# ================================================================
# SAVE MACHINE STATE SNAPSHOT
# ================================================================

def save_machine_snapshot(
    companies,
    sources,
    market_data,
):
    """
    Recalculate the machine interpretation of the full universe
    and append it to persistent state history.
    """

    captured_at = datetime.now(
        timezone.utc
    ).isoformat()


    snapshot_source = (
        "AUTO_MARKET_REFRESH_"
        + captured_at
    )


    state = build_machine_state(
        companies,
        sources,
        market_data,
    )


    state.insert(
        0,
        "snapshot_source",
        snapshot_source,
    )

    state.insert(
        0,
        "captured_at",
        captured_at,
    )


    if STATE_HISTORY_PATH.exists():

        history = pd.read_csv(
            STATE_HISTORY_PATH
        )

        history = pd.concat(
            [
                history,
                state,
            ],
            ignore_index=True,
        )

    else:

        history = state.copy()


    history.to_csv(
        STATE_HISTORY_PATH,
        index=False,
    )


    return (
        state,
        captured_at,
        snapshot_source,
    )


# ================================================================
# MARKET DATA REFRESH
# ================================================================

def main():

    companies = load_companies()

    sources = load_sources()

    previous_market = (
        load_market_data()
    )


    results = []


    print()
    print(
        "Refreshing market data..."
    )

    print(
        "-" * 80
    )


    for ticker in companies[
        "ticker"
    ]:

        ticker = (
            str(ticker)
            .upper()
            .strip()
        )


        print(
            f"{ticker}: ",
            end="",
        )


        try:

            result = (
                fetch_market_snapshot(
                    ticker
                )
            )


            results.append(
                result
            )


            print(
                f"OK | "
                f"Price "
                f"A${result['latest_price_aud']:.3f} | "
                f"20D ADV "
                f"A${result['avg_daily_value_traded_20d_aud_m']:.3f}m"
            )


        except Exception as exc:

            previous_row = (
                _previous_market_row(
                    previous_market,
                    ticker,
                )
            )


            fallback = (
                _fallback_market_row(
                    ticker,
                    previous_row,
                    exc,
                )
            )


            results.append(
                fallback
            )


            if previous_row is not None:

                print(
                    "FAILED — USING PREVIOUS CACHE | "
                    f"{exc}"
                )

            else:

                print(
                    "FAILED — NO CACHE | "
                    f"{exc}"
                )


    # ============================================================
    # SAVE CURRENT MARKET CACHE
    # ============================================================

    output = pd.DataFrame(
        results
    )


    output.to_csv(
        MARKET_OUTPUT_PATH,
        index=False,
    )


    print(
        "-" * 80
    )


    print(
        f"Saved {len(output)} market records to "
        f"{MARKET_OUTPUT_PATH}"
    )


    successful = int(
        (
            output[
                "refresh_status"
            ]
            == "SUCCESS"
        ).sum()
    )


    stale = int(
        output[
            "refresh_status"
        ]
        .astype(str)
        .str.startswith(
            "STALE"
        )
        .sum()
    )


    failed = int(
        output[
            "refresh_status"
        ]
        .astype(str)
        .str.startswith(
            "FAILED"
        )
        .sum()
    )


    print(
        f"Successful: {successful}"
    )

    print(
        f"Stale cache retained: {stale}"
    )

    print(
        f"Failed without cache: {failed}"
    )


    # ============================================================
    # CREATE AUTOMATIC MACHINE SNAPSHOT
    # ============================================================

    state, captured_at, snapshot_source = (
        save_machine_snapshot(
            companies,
            sources,
            output,
        )
    )


    print()
    print(
        "=" * 80
    )

    print(
        "MACHINE STATE SNAPSHOT SAVED"
    )

    print(
        "=" * 80
    )


    print(
        "Captured at:",
        captured_at,
    )


    print(
        "Snapshot source:",
        snapshot_source,
    )


    print(
        "Companies recorded:",
        len(state),
    )


    print(
        "History file:",
        STATE_HISTORY_PATH,
    )


    print()
    print(
        state[
            [
                "ticker",
                "funding_timing",
                "fundability",
                "integrated_view",
            ]
        ].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
