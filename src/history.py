import pandas as pd

from src.change_detection import (
    detect_changes,
    build_change_brief,
)


# ================================================================
# SNAPSHOT PAIR
# ================================================================

def get_latest_snapshot_pair(history):
    """
    Return the previous and latest complete machine snapshots.

    Historical timestamps may contain different valid ISO-8601
    representations, for example:
        2026-08-18T14:55:58Z
        2026-08-18T15:08:40.339364+00:00

    format='mixed' allows pandas to parse each value independently.
    """

    if history is None or history.empty:
        return None, None


    required = {
        "captured_at",
        "snapshot_source",
        "ticker",
    }

    if not required.issubset(
        history.columns
    ):
        return None, None


    working = history.copy()


    # ------------------------------------------------------------
    # ROBUST TIMESTAMP PARSING
    # ------------------------------------------------------------

    working["_captured_dt"] = pd.to_datetime(
        working["captured_at"],
        format="mixed",
        errors="coerce",
        utc=True,
    )


    # ------------------------------------------------------------
    # ONE RECORD PER SNAPSHOT
    # ------------------------------------------------------------

    snapshot_meta = (
        working[
            [
                "snapshot_source",
                "_captured_dt",
            ]
        ]
        .drop_duplicates()
        .dropna(
            subset=[
                "_captured_dt"
            ]
        )
        .sort_values(
            "_captured_dt"
        )
        .reset_index(
            drop=True
        )
    )


    if len(snapshot_meta) < 2:
        return None, None


    previous_source = (
        snapshot_meta.iloc[-2][
            "snapshot_source"
        ]
    )

    current_source = (
        snapshot_meta.iloc[-1][
            "snapshot_source"
        ]
    )


    previous = (
        working[
            working["snapshot_source"]
            == previous_source
        ]
        .drop(
            columns=[
                "_captured_dt"
            ]
        )
        .reset_index(
            drop=True
        )
    )


    current = (
        working[
            working["snapshot_source"]
            == current_source
        ]
        .drop(
            columns=[
                "_captured_dt"
            ]
        )
        .reset_index(
            drop=True
        )
    )


    return (
        previous,
        current,
    )


# ================================================================
# LATEST CHANGE ANALYSIS
# ================================================================

def analyse_latest_changes(history):
    """
    Compare the two most recent stored machine snapshots
    and produce both the underlying audit trail and
    analyst-facing machine briefs.
    """

    previous, current = (
        get_latest_snapshot_pair(
            history
        )
    )


    if (
        previous is None
        or current is None
    ):
        return {
            "previous": None,
            "current": None,
            "changes": pd.DataFrame(),
            "movements": pd.DataFrame(),
            "briefs": {},
        }


    changes = detect_changes(
        previous,
        current,
    )


    if changes.empty:

        movements = pd.DataFrame()

        briefs = {}


    else:

        movements = changes[
            changes["field"]
            == "Integrated Origination View"
        ].copy()


        affected_tickers = sorted(
            changes[
                "ticker"
            ].unique()
        )


        briefs = {
            ticker: build_change_brief(
                ticker,
                previous,
                current,
            )
            for ticker
            in affected_tickers
        }


    return {
        "previous": previous,
        "current": current,
        "changes": changes,
        "movements": movements,
        "briefs": briefs,
    }
