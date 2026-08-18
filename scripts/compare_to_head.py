from io import StringIO
from pathlib import Path
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
    detect_changes,
    build_change_brief,
)


# ================================================================
# READ A CSV FROM LAST COMMIT
# ================================================================

def read_head_csv(path):
    """
    Read a CSV exactly as it existed in the current Git HEAD.
    """

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
# LOAD PREVIOUS COMMITTED STATE
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
        "Could not read committed companies.csv."
    )


if head_sources is None:
    raise RuntimeError(
        "Could not read committed sources.csv."
    )


# If market_data.csv was not yet committed at HEAD,
# use the current cached market snapshot so that the comparison
# isolates fundamental/evidence changes.
if head_market is None:
    head_market = load_market_data()


# ================================================================
# CURRENT WORKING STATE
# ================================================================

current_companies = load_companies()
current_sources = load_sources()
current_market = load_market_data()


# ================================================================
# BUILD MACHINE STATES
# ================================================================

previous_state = build_machine_state(
    head_companies,
    head_sources,
    head_market,
)

current_state = build_machine_state(
    current_companies,
    current_sources,
    current_market,
)


# ================================================================
# DETECT CHANGES
# ================================================================

changes = detect_changes(
    previous_state,
    current_state,
)


print()
print("=" * 100)
print(
    "MACHINE CHANGE DETECTION — "
    "LAST COMMIT vs WORKING TREE"
)
print("=" * 100)


if changes.empty:

    print()
    print(
        "No material machine-state changes detected."
    )

else:

    print()

    print(
        changes.to_string(
            index=False
        )
    )


# ================================================================
# EGR MACHINE PRE-BRIEF
# ================================================================

print()
print("=" * 100)
print(
    "EGR — MACHINE PRE-BRIEF"
)
print("=" * 100)

print()

print(
    build_change_brief(
        "EGR",
        previous_state,
        current_state,
    )
)
