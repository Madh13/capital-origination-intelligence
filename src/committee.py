import pandas as pd


# ================================================================
# COMMITTEE ORDER
# ================================================================

COMMITTEE_ORDER = {
    "ADVANCE — SHORTLIST": 1,
    "RESERVE — STAGE 2 REQUIRED": 2,
    "DEFER": 3,
    "DEFER — EVIDENCE GAP": 4,
    "REJECT": 5,
}


HUMAN_PRIORITY = {
    "HOLD — EARLY ENGAGEMENT": 1,
    "HOLD — STRATEGIC FINANCING REVIEW": 2,
    "HOLD — PROJECT FINANCING WATCH": 3,
}


# ================================================================
# HUMAN / MACHINE RELATIONSHIP
# ================================================================

def _relationship(
    machine_view,
    human_status,
):
    if human_status is None:
        return "MACHINE ONLY"

    human_upper = str(
        human_status
    ).upper()

    machine_upper = str(
        machine_view
    ).upper()

    if human_upper.startswith(
        "KILL"
    ):
        return "HUMAN REJECTION"

    if (
        "EARLY ENGAGEMENT"
        in machine_upper
        and
        "EARLY ENGAGEMENT"
        in human_upper
    ):
        return "HUMAN CONFIRMATION"

    if (
        "FUNDABILITY CONSTRAINT"
        in machine_upper
        and
        human_upper.startswith(
            "HOLD"
        )
    ):
        return "HUMAN BROADENED PATHWAY"

    if (
        "RECENTLY FUNDED"
        in machine_upper
        and
        human_upper.startswith(
            "HOLD"
        )
    ):
        return "HUMAN EXTENDED HORIZON"

    if human_upper.startswith(
        "HOLD"
    ):
        return "HUMAN CONFIRMATION"

    return "HUMAN REVIEW"


# ================================================================
# COMMITTEE DECISION
# ================================================================

def _committee_decision(
    machine_view,
    human_status,
):
    """
    Convert machine pipeline + Stage 2 human judgment
    into a committee workflow decision.
    """

    if human_status is not None:

        human_upper = str(
            human_status
        ).upper()

        if human_upper.startswith(
            "KILL"
        ):
            return "REJECT"

        if human_upper in {
            status.upper()
            for status
            in HUMAN_PRIORITY
        }:
            return "ADVANCE — SHORTLIST"

        if human_upper.startswith(
            "HOLD"
        ):
            return "ADVANCE — SHORTLIST"


    machine_upper = str(
        machine_view
    ).upper()


    if machine_upper in {
        "PRIORITY REVIEW",
        "EARLY ENGAGEMENT REVIEW",
    }:
        return (
            "RESERVE — STAGE 2 REQUIRED"
        )


    if machine_upper.startswith(
        "MONITOR"
    ):
        return (
            "RESERVE — STAGE 2 REQUIRED"
        )


    if machine_upper == (
        "LOWER CURRENT PRIORITY"
    ):
        return "DEFER"


    if machine_upper == (
        "INSUFFICIENT EVIDENCE"
    ):
        return (
            "DEFER — EVIDENCE GAP"
        )


    return "DEFER"


# ================================================================
# RATIONALE
# ================================================================

def _committee_rationale(
    machine_view,
    human_status,
    decision,
):
    if decision == (
        "ADVANCE — SHORTLIST"
    ):

        if (
            human_status
            and
            "EARLY ENGAGEMENT"
            in str(
                human_status
            ).upper()
        ):
            return (
                "Positive machine signal survived "
                "deeper human diligence."
            )

        if (
            human_status
            and
            "STRATEGIC FINANCING"
            in str(
                human_status
            ).upper()
        ):
            return (
                "Machine identified a constraint, "
                "but human diligence found a credible "
                "strategic-financing pathway."
            )

        if (
            human_status
            and
            "PROJECT FINANCING"
            in str(
                human_status
            ).upper()
        ):
            return (
                "Immediate equity need is limited, "
                "but a material future project-financing "
                "cycle warrants continued coverage."
            )

        return (
            "Human diligence supports carrying "
            "the opportunity forward."
        )


    if decision == (
        "RESERVE — STAGE 2 REQUIRED"
    ):
        return (
            "Machine screen remains potentially interesting, "
            "but no completed human Stage 2 review exists."
        )


    if decision == "REJECT":
        return (
            "Human Stage 2 diligence rejected the "
            "current active origination thesis."
        )


    if decision == (
        "DEFER — EVIDENCE GAP"
    ):
        return (
            "Evidence remains insufficient for "
            "shortlist consideration."
        )


    return (
        "Current financing timing does not warrant "
        "additional active origination work."
    )


# ================================================================
# NEXT ACTION
# ================================================================

def _next_action(
    decision,
    human_status,
):
    if decision == (
        "ADVANCE — SHORTLIST"
    ):

        if (
            human_status
            and
            "EARLY ENGAGEMENT"
            in str(
                human_status
            ).upper()
        ):
            return (
                "Build flagship financing thesis "
                "and engagement case."
            )

        if (
            human_status
            and
            "STRATEGIC FINANCING"
            in str(
                human_status
            ).upper()
        ):
            return (
                "Track strategic-equity process and "
                "define any addressable ASX equity role."
            )

        if (
            human_status
            and
            "PROJECT FINANCING"
            in str(
                human_status
            ).upper()
        ):
            return (
                "Monitor project-funding stack and "
                "future equity requirement."
            )

        return (
            "Advance to final opportunity review."
        )


    if decision == (
        "RESERVE — STAGE 2 REQUIRED"
    ):
        return (
            "Hold as reserve; conduct Stage 2 only "
            "if shortlist capacity or conditions change."
        )


    if decision == "REJECT":
        return (
            "Remove from active origination work; "
            "retain only for monitoring."
        )


    if decision == (
        "DEFER — EVIDENCE GAP"
    ):
        return (
            "Resolve evidence gap only if new information "
            "makes the company strategically relevant."
        )


    return (
        "Monitor only; do not allocate active "
        "origination resources."
    )


# ================================================================
# BUILD OPPORTUNITY COMMITTEE
# ================================================================

def build_opportunity_committee(
    pipeline,
    deep_dives,
):
    """
    Combine machine pipeline output with human Stage 2
    assessments to form the shortlist committee view.
    """

    rows = []


    for _, item in pipeline.iterrows():

        ticker = str(
            item["ticker"]
        ).upper()


        human_match = deep_dives[
            deep_dives["ticker"]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ]


        if human_match.empty:

            human_status = None
            human_confidence = None
            human_verdict = None

        else:

            human = (
                human_match.iloc[0]
            )

            human_status = human.get(
                "review_status"
            )

            human_confidence = human.get(
                "confidence"
            )

            human_verdict = human.get(
                "analyst_verdict"
            )


        machine_view = item[
            "pipeline_stage"
        ]


        decision = (
            _committee_decision(
                machine_view,
                human_status,
            )
        )


        relationship = (
            _relationship(
                machine_view,
                human_status,
            )
        )


        rationale = (
            _committee_rationale(
                machine_view,
                human_status,
                decision,
            )
        )


        next_action = (
            _next_action(
                decision,
                human_status,
            )
        )


        human_rank = (
            HUMAN_PRIORITY.get(
                str(
                    human_status
                ),
                99,
            )
            if human_status
            else 99
        )


        rows.append(
            {
                "ticker": ticker,

                "company": item[
                    "company"
                ],

                "commodity": item[
                    "commodity"
                ],

                "committee_decision": (
                    decision
                ),

                "committee_rank": (
                    COMMITTEE_ORDER.get(
                        decision,
                        99,
                    )
                ),

                "human_priority": (
                    human_rank
                ),

                "machine_view": (
                    machine_view
                ),

                "human_stage2": (
                    human_status
                    if human_status
                    else "NOT COMPLETED"
                ),

                "human_confidence": (
                    human_confidence
                    if human_confidence
                    else "N/A"
                ),

                "machine_human_relationship": (
                    relationship
                ),

                "committee_rationale": (
                    rationale
                ),

                "next_action": (
                    next_action
                ),

                "human_verdict": (
                    human_verdict
                    if human_verdict
                    else ""
                ),

                "formal_shortlist": (
                    decision
                    == "ADVANCE — SHORTLIST"
                ),
            }
        )


    committee = pd.DataFrame(
        rows
    )


    committee = committee.sort_values(
        [
            "committee_rank",
            "human_priority",
            "ticker",
        ]
    ).reset_index(
        drop=True
    )


    return committee


# ================================================================
# COMMITTEE COUNTS
# ================================================================
# ================================================================
# COMMITTEE COUNTS
# ================================================================

def committee_counts(
    committee,
):
    """
    Summarise the number of companies in each
    Opportunity Committee workflow category.
    """

    shortlist = committee[
        committee["committee_decision"]
        == "ADVANCE — SHORTLIST"
    ]


    reserve = committee[
        committee["committee_decision"]
        == "RESERVE — STAGE 2 REQUIRED"
    ]


    deferred = committee[
        committee["committee_decision"].isin(
            [
                "DEFER",
                "DEFER — EVIDENCE GAP",
            ]
        )
    ]


    rejected = committee[
        committee["committee_decision"]
        == "REJECT"
    ]


    return {
        "shortlist": int(
            len(shortlist)
        ),

        "reserve": int(
            len(reserve)
        ),

        "deferred": int(
            len(deferred)
        ),

        "rejected": int(
            len(rejected)
        ),
    }
