# ================================================================
# MACHINE PRE-BRIEF
# ================================================================

MACHINE_ACTIONS = {
    "PRIORITY REVIEW": (
        "Immediate analyst deep-dive warranted."
    ),

    "EARLY ENGAGEMENT REVIEW": (
        "Deepen financing thesis and test whether early "
        "relationship development is warranted."
    ),

    "MONITOR — RECENTLY FUNDED": (
        "Track deployment of recently raised capital and "
        "reassess as funding seasons."
    ),

    "MONITOR — FUNDABILITY CONSTRAINT": (
        "Investigate whether weak public-market fundability "
        "can realistically be overcome."
    ),

    "MONITOR": (
        "Track catalysts, funding position and market conditions."
    ),

    "LOWER CURRENT PRIORITY": (
        "Defer active origination work unless the financing "
        "context materially changes."
    ),

    "INSUFFICIENT EVIDENCE": (
        "Resolve missing evidence before forming a stronger view."
    ),
}


def _deduplicate(items):
    output = []
    seen = set()

    for item in items:
        if not item:
            continue

        text = str(item).strip()

        if text not in seen:
            output.append(text)
            seen.add(text)

    return output


def _build_machine_thesis(
    timing,
    fundability,
    integrated_view,
):
    funding = timing[
        "funding_timing"
    ]

    catalyst = timing[
        "catalyst_visibility"
    ]

    financing = timing[
        "financing_recency"
    ]

    market_support = fundability[
        "fundability"
    ]


    if integrated_view == "PRIORITY REVIEW":
        return (
            "The machine sees meaningful financing timing, "
            "credible market fundability and visible catalysts. "
            "The company warrants immediate deeper review."
        )


    if integrated_view == "EARLY ENGAGEMENT REVIEW":
        return (
            "The machine sees a potentially actionable combination "
            f"of {funding.lower()} funding timing, "
            f"{market_support.lower()} fundability and "
            f"{catalyst.lower()} catalyst visibility. "
            "The financing requirement is not necessarily immediate."
        )


    if integrated_view == "MONITOR — RECENTLY FUNDED":
        return (
            "The company shows financing activity or funding pressure, "
            "but a recent capital raise materially reduces immediate "
            "origination urgency."
        )


    if integrated_view == "MONITOR — FUNDABILITY CONSTRAINT":
        return (
            "The machine sees a potentially meaningful financing "
            f"requirement or catalyst, but current public-market "
            f"fundability is {market_support.lower()}. "
            "Need for capital should not be confused with ability "
            "to execute a conventional equity raising."
        )


    if integrated_view == "MONITOR":
        return (
            "The company remains strategically interesting, but "
            f"current funding timing is {funding.lower()} and does "
            "not yet support active origination."
        )


    if integrated_view == "LOWER CURRENT PRIORITY":
        return (
            "The current financing context appears less immediate. "
            f"Financing recency is {financing.lower()}, while funding "
            f"timing is {funding.lower()}."
        )


    return (
        "The machine does not yet have sufficient evidence to form "
        "a stronger origination conclusion."
    )


def build_machine_prebrief(
    ticker,
    timing,
    fundability,
    integrated_view,
    change_brief=None,
):
    """
    Generate a standardized machine-created pre-brief.

    This is produced entirely from structured inputs and
    rules-based intelligence. It is NOT the human Stage 2 view.
    """

    reasons = _deduplicate(
        timing.get(
            "reasons",
            [],
        )
        +
        fundability.get(
            "reasons",
            [],
        )
    )


    diligence = _deduplicate(
        timing.get(
            "diligence_gaps",
            [],
        )
        +
        fundability.get(
            "diligence_gaps",
            [],
        )
    )


    return {
        "ticker": ticker,

        "machine_view": integrated_view,

        "machine_thesis": (
            _build_machine_thesis(
                timing,
                fundability,
                integrated_view,
            )
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

        "financing_recency": timing[
            "financing_recency"
        ],

        "recommended_machine_action": (
            MACHINE_ACTIONS.get(
                integrated_view,
                "Review manually.",
            )
        ),

        "recent_change": (
            change_brief
            if change_brief
            else (
                "No material change was detected for this company "
                "between the two latest stored snapshots."
            )
        ),

        "reasons": reasons,

        "diligence_priorities": diligence,
    }
