from io import StringIO
from pathlib import Path
from datetime import datetime, timezone
import subprocess
import sys

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

from src.change_detection import (
    build_machine_state,
)


OUTPUT_PATH = (
    ROOT_DIR
    / "data"
    / "state_history.csv"
)


# ================================================================
# READ CSV FROM CURRENT GIT HEAD
# ================================================================

def read_head_csv(path):
    result = subprocess.run(
        [
            "git",
            "show",
            f"HEAD:{path}",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return pd.read_csv(
        StringIO(
            result.stdout
        )
    )


# ================================================================
# GET HEAD TIMESTAMP
# ================================================================

def get_head_timestamp():
    result = subprocess.run(
        [
            "git",
            "log",
            "-1",
            "--format=%cI",
            "HEAD",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return result.stdout.strip()


# ================================================================
# PREVIOUS COMMITTED STATE
# ================================================================

head_companies = read_head_csv(
    "data/companies.csv"
)

head_sources = read_head_csv(
    "data/sources.csv"
)

head_market = read_head_csv(
    "data/market_data.csv"
)


if head_companies is None:
    raise RuntimeError(
        "Could not read companies.csv from HEAD."
    )

if head_sources is None:
    raise RuntimeError(
        "Could not read sources.csv from HEAD."
    )

if head_market is None:
    head_market = load_market_data()


previous_state = build_machine_state(
    head_companies,
    head_sources,
    head_market,
)


# ================================================================
# CURRENT WORKING STATE
# ================================================================

current_state = build_machine_state(
    load_companies(),
    load_sources(),
    load_market_data(),
)


# ================================================================
# ADD SNAPSHOT METADATA
# ================================================================

head_timestamp = get_head_timestamp()

current_timestamp = datetime.now(
    timezone.utc
).isoformat()


previous_state.insert(
    0,
    "snapshot_source",
    "GIT_HEAD_BEFORE_EGR_UPGRADE",
)

previous_state.insert(
    0,
    "captured_at",
    head_timestamp,
)


current_state.insert(
    0,
    "snapshot_source",
    "WORKING_TREE_AFTER_EGR_UPGRADE",
)

current_state.insert(
    0,
    "captured_at",
    current_timestamp,
)


# ================================================================
# SAVE HISTORY
# ================================================================

history = pd.concat(
    [
        previous_state,
        current_state,
    ],
    ignore_index=True,
)


history.to_csv(
    OUTPUT_PATH,
    index=False,
)


print()
print("=" * 100)
print("MACHINE STATE HISTORY SEEDED")
print("=" * 100)

print()
print(
    "Snapshots:",
    history[
        "snapshot_source"
    ].nunique(),
)

print(
    "Rows:",
    len(history),
)

print()
print("EGR HISTORY")
print("-" * 100)

print(
    history[
        history["ticker"] == "EGR"
    ][
        [
            "captured_at",
            "snapshot_source",
            "reported_quarters_funding",
            "funding_timing",
            "data_confidence",
            "fundability",
            "integrated_view",
        ]
    ].to_string(
        index=False
    )
)

print()
print(
    "Saved to:",
    OUTPUT_PATH,
)
