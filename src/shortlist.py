import pandas as pd

from src.intelligence import (
    assess_company,
)

from src.fundability import (
    assess_fundability,
)


# ================================================================
# COMMERCIAL INTERPRETATION
# ================================================================

def _equity_relevance(
    human_stage2,
):
    """
    How directly does the current thesis map to a conventional
    listed-equity origination opportunity?
    """

    status = str(
        human_stage2
    ).upper()


    if "EARLY ENGAGEMENT" in status:
        return "HIGH"


    if "STRATEGIC FINANCING" in status:
        return "MODERATE"


    if "PROJECT FINANCING" in status:
        return "MODERATE"


    return "LOW"


def _financing_complexity(
    human_stage2,
):
    """
    Complexity of the disclosed or inferred financing pathway.
    """

    status = str(
        human_stage2
    ).upper()


    if "EARLY ENGAGEMENT" in status:
        return "MODERATE"


    if "STRATEGIC FINANCING" in status:
        return "HIGH"


    if "PROJECT FINANCING" in status:
        return "VERY HIGH"


    return "HIGH"


def _time_horizon(
    human_stage2,
):
    status = str(
        human_stage2
    ).upper()


    if "EARLY ENGAGEMENT" in status:
        return "NEAR / MEDIUM TERM"


    if "STRATEGIC FINANCING" in status:
        return "ACTIVE STRUCTURING"


    if "PROJECT FINANCING" in status:
        return "MEDIUM TERM"


    return "MONITOR"


def _origination_actionability(
    machine_view,
    human_stage2,
    fundability,
):
    """
    Commercial usefulness to an origination analyst today.
    """

    machine = str(
        machine_view
    ).upper()

    human = str(
        human_stage2
    ).upper()

    fundability = str(
        fundability
    ).upper()


    if (
        "EARLY ENGAGEMENT" in machine
        and
        human.startswith("HOLD")
        and
        fundability in {
            "STRONG",
            "MODERATE",
        }
    ):
        return "HIGH"


    if (
        "STRATEGIC FINANCING"
        in human
    ):
        return "MODERATE"


    if (
        "PROJECT FINANCING"
        in human
    ):
        return "MODERATE"


    return "LOW"


# ================================================================
# FLAGSHIP LOGIC
# ================================================================

def _flagship_ready(
    machine_view,
    human_relationship,
    fundability,
    data_confidence,
    equity_relevance,
    actionability,
):
    """
    A company is flagship-ready only when the machine and human
    analyst broadly agree AND the opportunity is sufficiently
    actionable and addressable.

    No weighted score is used.
    """

    machine = str(
        machine_view
    ).upper()

    relationship = str(
        human_relationship
    ).upper()

    fundability = str(
        fundability
    ).upper()

    confidence = str(
        data_confidence
    ).upper()


    machine_positive = (
        machine in {
            "PRIORITY REVIEW",
            "EARLY ENGAGEMENT REVIEW",
        }
    )


    human_confirmation = (
        relationship
        == "HUMAN CONFIRMATION"
    )


    supportive_market = (
        fundability
        in {
            "STRONG",
            "MODERATE",
        }
    )


    sufficient_evidence = (
        confidence
        not in {
            "LIMITED",
            "LOW",
            "INSUFFICIENT",
        }
    )


    return bool(
        machine_positive
        and
        human_confirmation
        and
        supportive_market
        and
        sufficient_evidence
        and
        equity_relevance == "HIGH"
        and
        actionability == "HIGH"
    )


# ================================================================
# COMPARISON RATIONALE
# ================================================================

def _comparison_rationale(
    human_stage2,
    fundability,
    relationship,
):
    human = str(
        human_stage2
    ).upper()

    fundability = str(
        fundability
    ).upper()

    relationship = str(
        relationship
    ).upper()


    if (
        "EARLY ENGAGEMENT"
        in human
        and
        relationship
        == "HUMAN CONFIRMATION"
    ):
        return (
            "Machine and analyst align on an early-engagement "
            "opportunity, with a comparatively direct listed-equity "
            "origination pathway."
        )


    if (
        "STRATEGIC FINANCING"
        in human
    ):
        return (
            "Strategically relevant financing activity exists, "
            f"but public-market fundability is {fundability.lower()} "
            "and the pathway is broader than a conventional placement."
        )


    if (
        "PROJECT FINANCING"
        in human
    ):
        return (
            "Large future financing requirements are visible, "
            "but recent funding and a complex project-financing stack "
            "reduce immediate conventional equity actionability."
        )


    return (
        "The opportunity remains shortlisted but does not yet "
        "present the cleanest flagship origination case."
    )


# ================================================================
# BUILD SHORTLIST COMPARISON
# ================================================================

def build_shortlist_comparison(
    committee,
    companies,
    sources,
    market_data,
):
    """
    Compare only formally shortlisted companies.

    The output deliberately uses categorical commercial judgments
    rather than an opaque numerical score.
    """

    shortlist = committee[
        committee[
            "formal_shortlist"
        ]
    ].copy()


    rows = []


    for _, candidate in shortlist.iterrows():

        ticker = str(
            candidate["ticker"]
        ).upper()


        company_match = companies[
            companies["ticker"]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ]


        if company_match.empty:
            continue


        company = (
            company_match.iloc[0]
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


        equity_relevance = (
            _equity_relevance(
                candidate[
                    "human_stage2"
                ]
            )
        )


        complexity = (
            _financing_complexity(
                candidate[
                    "human_stage2"
                ]
            )
        )


        horizon = (
            _time_horizon(
                candidate[
                    "human_stage2"
                ]
            )
        )


        actionability = (
            _origination_actionability(
                candidate[
                    "machine_view"
                ],
                candidate[
                    "human_stage2"
                ],
                fundability[
                    "fundability"
                ],
            )
        )


        flagship_ready = (
            _flagship_ready(
                candidate[
                    "machine_view"
                ],
                candidate[
                    "machine_human_relationship"
                ],
                fundability[
                    "fundability"
                ],
                timing[
                    "data_confidence"
                ],
                equity_relevance,
                actionability,
            )
        )


        rationale = (
            _comparison_rationale(
                candidate[
                    "human_stage2"
                ],
                fundability[
                    "fundability"
                ],
                candidate[
                    "machine_human_relationship"
                ],
            )
        )


        rows.append(
            {
                "ticker": ticker,

                "company": candidate[
                    "company"
                ],

                "machine_view": candidate[
                    "machine_view"
                ],

                "human_stage2": candidate[
                    "human_stage2"
                ],

                "machine_human": candidate[
                    "machine_human_relationship"
                ],

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

                "equity_relevance": (
                    equity_relevance
                ),

                "financing_complexity": (
                    complexity
                ),

                "time_horizon": horizon,

                "origination_actionability": (
                    actionability
                ),

                "flagship_ready": (
                    flagship_ready
                ),

                "comparison_rationale": (
                    rationale
                ),
            }
        )


    return pd.DataFrame(
        rows
    )


# ================================================================
# SELECT FLAGSHIP
# ================================================================

def select_flagship(
    comparison,
):
    """
    Select a flagship only when exactly one shortlisted company
    satisfies all transparent flagship conditions.

    If zero or multiple companies qualify, no automatic selection
    is made and analyst judgment is required.
    """

    if (
        comparison is None
        or comparison.empty
    ):
        return None


    qualified = comparison[
        comparison[
            "flagship_ready"
        ]
    ].copy()


    if len(qualified) != 1:
        return None


    return qualified.iloc[0]
