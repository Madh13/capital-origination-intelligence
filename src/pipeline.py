import pandas as pd


# ================================================================
# PIPELINE ORDER
# ================================================================

PIPELINE_ORDER = {
    "PRIORITY REVIEW": 1,
    "EARLY ENGAGEMENT REVIEW": 2,
    "MONITOR — RECENTLY FUNDED": 3,
    "MONITOR — FUNDABILITY CONSTRAINT": 4,
    "MONITOR": 5,
    "LOWER CURRENT PRIORITY": 6,
    "INSUFFICIENT EVIDENCE": 7,
}


# ================================================================
# PIPELINE ACTIONS
# ================================================================

PIPELINE_ACTIONS = {
    "PRIORITY REVIEW": (
        "Deep-dive now; test financing thesis and potential approach."
    ),

    "EARLY ENGAGEMENT REVIEW": (
        "Deepen diligence and assess whether early relationship "
        "development is warranted."
    ),

    "MONITOR — RECENTLY FUNDED": (
        "Track capital deployment and upcoming catalysts; "
        "reassess as the recent raise seasons."
    ),

    "MONITOR — FUNDABILITY CONSTRAINT": (
        "Resolve market-fundability constraints before escalation."
    ),

    "MONITOR": (
        "Track catalysts, funding position and market conditions "
        "for a change in opportunity timing."
    ),

    "LOWER CURRENT PRIORITY": (
        "Keep on the universe but defer active origination work."
    ),

    "INSUFFICIENT EVIDENCE": (
        "Complete missing diligence before assigning an "
        "origination priority."
    ),
}


# ================================================================
# SHORT RATIONALE
# ================================================================

def build_pipeline_rationale(
    timing,
    fundability,
    integrated_view,
):
    """
    Produce a compact analyst-facing explanation for why the
    company sits in its current pipeline category.
    """

    funding = timing["funding_timing"]
    financing = timing["financing_recency"]
    catalyst = timing["catalyst_visibility"]

    fundability_label = fundability[
        "fundability"
    ]

    if integrated_view == "PRIORITY REVIEW":
        return (
            f"{funding.lower()} funding timing, "
            f"{fundability_label.lower()} fundability and "
            f"{catalyst.lower()} catalyst visibility."
        )

    if integrated_view == "EARLY ENGAGEMENT REVIEW":
        return (
            f"{funding.lower()} funding timing with "
            f"{fundability_label.lower()} fundability; "
            f"last financing is {financing.lower()}."
        )

    if integrated_view == "MONITOR — RECENTLY FUNDED":
        return (
            f"Funding timing is {funding.lower()}, but the "
            "company has recently completed financing."
        )

    if integrated_view == "MONITOR — FUNDABILITY CONSTRAINT":
        return (
            f"Funding timing is {funding.lower()}, but observable "
            f"market fundability is {fundability_label.lower()}."
        )

    if integrated_view == "MONITOR":
        return (
            f"Current funding timing is {funding.lower()}; "
            "catalysts remain worth monitoring."
        )

    if integrated_view == "LOWER CURRENT PRIORITY":
        return (
            f"Current financing timing is less immediate; "
            f"recent financing status is {financing.lower()}."
        )

    return (
        "Current evidence is insufficient for a stronger "
        "origination conclusion."
    )


# ================================================================
# BUILD PIPELINE
# ================================================================

def build_pipeline(
    companies,
    market_data,
    all_sources,
    assess_company,
    assess_fundability,
    integrate_origination_view,
):
    """
    Build a sorted analyst-review pipeline from the full
    company universe.
    """

    rows = []

    for _, company in companies.iterrows():
        ticker = company["ticker"]

        sources = all_sources[
            all_sources["ticker"] == ticker
        ]

        market_match = market_data[
            market_data["ticker"] == ticker
        ]

        market = (
            market_match.iloc[0]
            if not market_match.empty
            else None
        )

        timing = assess_company(
            company,
            sources,
        )

        fundability = assess_fundability(
            company,
            market,
        )

        integrated = integrate_origination_view(
            timing,
            fundability,
        )

        rationale = build_pipeline_rationale(
            timing,
            fundability,
            integrated,
        )

        action = PIPELINE_ACTIONS.get(
            integrated,
            "Review manually.",
        )

        rows.append(
            {
                "ticker": ticker,
                "company": company[
                    "company_name"
                ],
                "commodity": company[
                    "commodity"
                ],
                "pipeline_stage": integrated,
                "pipeline_rank": PIPELINE_ORDER.get(
                    integrated,
                    99,
                ),
                "funding_timing": timing[
                    "funding_timing"
                ],
                "fundability": fundability[
                    "fundability"
                ],
                "catalyst_visibility": timing[
                    "catalyst_visibility"
                ],
                "data_confidence": timing[
                    "data_confidence"
                ],
                "rationale": rationale,
                "analyst_action": action,
            }
        )

    pipeline = pd.DataFrame(rows)

    pipeline = pipeline.sort_values(
        [
            "pipeline_rank",
            "ticker",
        ]
    ).reset_index(drop=True)

    return pipeline


# ================================================================
# PIPELINE COUNTS
# ================================================================

def pipeline_counts(pipeline):
    """
    Return useful top-level pipeline metrics.
    """

    active_review = pipeline[
        pipeline["pipeline_stage"].isin(
            [
                "PRIORITY REVIEW",
                "EARLY ENGAGEMENT REVIEW",
            ]
        )
    ]

    monitor = pipeline[
        pipeline["pipeline_stage"].str.startswith(
            "MONITOR",
            na=False,
        )
    ]

    lower_priority = pipeline[
        pipeline["pipeline_stage"]
        == "LOWER CURRENT PRIORITY"
    ]

    insufficient = pipeline[
        pipeline["pipeline_stage"]
        == "INSUFFICIENT EVIDENCE"
    ]

    return {
        "active_review": len(active_review),
        "monitor": len(monitor),
        "lower_priority": len(
            lower_priority
        ),
        "insufficient": len(
            insufficient
        ),
    }
