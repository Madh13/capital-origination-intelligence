from pathlib import Path
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


from src.data_loader import (
    load_companies,
    load_sources,
    load_market_data,
    load_deep_dives,
    load_state_history,
)

from src.intelligence import (
    assess_company,
)

from src.fundability import (
    assess_fundability,
    integrate_origination_view,
)

from src.pipeline import (
    build_pipeline,
    pipeline_counts,
)

from src.committee import (
    build_opportunity_committee,
    committee_counts,
)

from src.shortlist import (
    build_shortlist_comparison,
    select_flagship,
)

from src.history import (
    analyse_latest_changes,
)


def check(condition, message):
    if not condition:
        raise AssertionError(message)

    print(
        "PASS |",
        message,
    )


print()
print("=" * 90)
print("CAPITAL ORIGINATION INTELLIGENCE — DEPLOYMENT PREFLIGHT")
print("=" * 90)
print()


# ================================================================
# LOAD CORE DATA
# ================================================================

companies = load_companies()
sources = load_sources()
market = load_market_data()
deep_dives = load_deep_dives()
history = load_state_history()


check(
    len(companies) == 8,
    "Eight-company screening universe loaded",
)

check(
    not sources.empty,
    "Evidence ledger loaded",
)

check(
    len(market) == 8,
    "Market snapshot contains eight companies",
)

check(
    not deep_dives.empty,
    "Stage 2 diligence dataset loaded",
)

check(
    not history.empty,
    "Machine-state history loaded",
)


# ================================================================
# TICKER INTEGRITY
# ================================================================

expected = {
    "FAL",
    "BGD",
    "QGL",
    "EGR",
    "MEI",
    "MMA",
    "EL8",
    "LRV",
}

actual = set(
    companies[
        "ticker"
    ]
    .astype(str)
    .str.upper()
)


check(
    actual == expected,
    "Expected ticker universe matches",
)


# ================================================================
# MACHINE PIPELINE
# ================================================================

pipeline = build_pipeline(
    companies,
    market,
    sources,
    assess_company,
    assess_fundability,
    integrate_origination_view,
)

pipeline_summary = pipeline_counts(
    pipeline
)


check(
    len(pipeline) == 8,
    "Machine pipeline generated for all eight companies",
)

check(
    (
        pipeline_summary["active_review"]
        + pipeline_summary["monitor"]
        + pipeline_summary["lower_priority"]
        + pipeline_summary["insufficient"]
    )
    == 8,
    "Pipeline counts reconcile to universe",
)


# ================================================================
# OPPORTUNITY COMMITTEE
# ================================================================

committee = build_opportunity_committee(
    pipeline,
    deep_dives,
)

counts = committee_counts(
    committee
)


check(
    counts["shortlist"] == 3,
    "Three companies carried to further-review shortlist",
)

check(
    counts["reserve"] == 2,
    "Two companies held as reserves",
)

check(
    counts["deferred"] == 2,
    "Two companies deferred",
)

check(
    counts["rejected"] == 1,
    "One company rejected by Stage 2",
)


# ================================================================
# SHORTLIST / ILLUSTRATIVE CASE
# ================================================================

comparison = build_shortlist_comparison(
    committee,
    companies,
    sources,
    market,
)


shortlisted = set(
    comparison[
        "ticker"
    ]
    .astype(str)
    .str.upper()
)


check(
    shortlisted
    == {
        "FAL",
        "EGR",
        "MEI",
    },
    "Shortlist contains FAL, EGR and MEI",
)


flagship = select_flagship(
    comparison
)


check(
    flagship is not None,
    "Unique illustrative case generated",
)

check(
    str(
        flagship[
            "ticker"
        ]
    ).upper()
    == "FAL",
    "Falcon Metals remains illustrative worked example",
)


# ================================================================
# MACHINE MEMORY
# ================================================================

snapshot_count = (
    history[
        "snapshot_source"
    ]
    .nunique()
)


check(
    snapshot_count >= 3,
    "At least three machine-state snapshots preserved",
)


history_analysis = (
    analyse_latest_changes(
        history
    )
)


check(
    "changes"
    in history_analysis,
    "Change-detection layer executes",
)


# ================================================================
# STAGE 2 CASE STUDIES
# ================================================================

reviews = {
    str(row["ticker"]).upper():
    str(row["review_status"])
    for _, row
    in deep_dives.iterrows()
}


check(
    "FAL" in reviews,
    "FAL Stage 2 review available",
)

check(
    "QGL" in reviews,
    "QGL Stage 2 review available",
)

check(
    "EGR" in reviews,
    "EGR Stage 2 review available",
)

check(
    "MEI" in reviews,
    "MEI Stage 2 review available",
)


print()
print("=" * 90)
print("PREFLIGHT RESULT: ALL CHECKS PASSED")
print("=" * 90)
