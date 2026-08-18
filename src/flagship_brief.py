import pandas as pd


# ================================================================
# HELPERS
# ================================================================

def _clean(value):
    if value is None:
        return ""

    try:
        if pd.isna(value):
            return ""
    except (TypeError, ValueError):
        pass

    return str(
        value
    ).strip()


def _money(value):
    try:
        if pd.isna(value):
            return "Not available"

        return (
            f"A${float(value):.1f}m"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "Not available"


def _quarters(value):
    try:
        if pd.isna(value):
            return "Not available"

        return (
            f"{float(value):.1f} quarters"
        )

    except (
        TypeError,
        ValueError,
    ):
        return "Not available"


def _get_evidence(
    evidence,
    claim_area,
):
    if (
        evidence is None
        or evidence.empty
    ):
        return ""


    match = evidence[
        evidence[
            "claim_area"
        ]
        .astype(str)
        .str.lower()
        .eq(
            str(
                claim_area
            ).lower()
        )
    ]


    if match.empty:
        return ""


    return _clean(
        match.iloc[-1][
            "evidence"
        ]
    )


def _split_questions(
    value,
    maximum=6,
):
    text = _clean(
        value
    )

    if not text:
        return []


    questions = [
        item.strip()
        for item
        in text.split(";")
        if item.strip()
    ]


    return questions[
        :maximum
    ]


# ================================================================
# FLAGSHIP BRIEF
# ================================================================

def build_flagship_brief(
    flagship,
    company,
    market,
    timing,
    fundability,
    deep_dive,
    evidence,
):
    """
    Convert the selected flagship company's machine intelligence,
    market data, Stage 2 diligence and evidence ledger into a
    concise origination brief.

    This is an analyst-assist output, not an investment
    recommendation or prediction of a financing event.
    """


    if (
        flagship is None
        or company is None
        or deep_dive is None
    ):
        return None


    ticker = _clean(
        company.get(
            "ticker"
        )
    )


    review_status = _clean(
        deep_dive.get(
            "review_status"
        )
    ).upper()


    # ------------------------------------------------------------
    # POSITIONING
    # ------------------------------------------------------------

    if (
        "EARLY ENGAGEMENT"
        in review_status
    ):

        positioning = (
            "EARLY ENGAGEMENT — "
            "NOT AN IMMEDIATE RAISE CALL"
        )

        engagement_case = (
            "Begin relationship-development and financing "
            "diligence before a funding requirement becomes "
            "urgent. The current case is about timing future "
            "origination, not predicting an imminent placement."
        )

        escalation_triggers = [
            (
                "A subsequent quarterly filing shows "
                "meaningful funding-runway compression."
            ),

            (
                "Management discloses an expanded exploration "
                "budget or materially larger program."
            ),

            (
                "Falcon explicitly signals an external "
                "equity requirement or financing process."
            ),

            (
                "A transaction, acquisition or development "
                "decision creates a defined use of proceeds."
            ),

            (
                "Continuing exploration success supports "
                "a larger or accelerated drilling program."
            ),
        ]

    else:

        positioning = (
            review_status
            if review_status
            else
            "FLAGSHIP REVIEW"
        )

        engagement_case = _clean(
            deep_dive.get(
                "analyst_verdict"
            )
        )

        escalation_triggers = []


    # ------------------------------------------------------------
    # EVIDENCE SNAPSHOT
    # ------------------------------------------------------------

    funding_evidence = (
        _get_evidence(
            evidence,
            "Funding position",
        )
    )

    scale_evidence = (
        _get_evidence(
            evidence,
            "Blue Moon scale",
        )
    )

    program_evidence = (
        _get_evidence(
            evidence,
            "Program intensity",
        )
    )

    errabiddy_evidence = (
        _get_evidence(
            evidence,
            "Errabiddy catalyst",
        )
    )

    capital_structure_evidence = (
        _get_evidence(
            evidence,
            "Capital structure",
        )
    )

    prior_access_evidence = (
        _get_evidence(
            evidence,
            "Prior capital access",
        )
    )


    # ------------------------------------------------------------
    # WHY NOW
    # ------------------------------------------------------------

    if ticker == "FAL":

        why_now = (
            "Exploration intensity is accelerating: Blue Moon "
            "mineralisation now extends beyond 850m, three diamond "
            "rigs are operating continuously, step-out and parallel-"
            "structure drilling continues, and the approved 3,500m "
            "maiden RC program at Errabiddy adds another visible "
            "near-term catalyst."
        )

    else:

        why_now_parts = [
            scale_evidence,
            program_evidence,
            errabiddy_evidence,
        ]

        why_now = " ".join(
            [
                item
                for item
                in why_now_parts
                if item
            ]
        )


    # ------------------------------------------------------------
    # CURRENT FINANCING POSITION
    # ------------------------------------------------------------

    cash = _money(
        company.get(
            "cash_aud_m"
        )
    )

    runway = _quarters(
        company.get(
            "reported_quarters_funding"
        )
    )


    if ticker == "FAL":

        financing_position = (
            f"No immediate funding pressure. Falcon reported "
            f"{cash} cash, nil financing facilities and "
            f"{runway} of funding at 30 June 2026. "
            "The current opportunity is therefore early engagement "
            "rather than an immediate financing call."
        )

    else:

        financing_position = (
            f"{_clean(deep_dive.get('financing_need_view'))}"
        )


    # ------------------------------------------------------------
    # CAPITAL MARKETS CASE
    # ------------------------------------------------------------

    capital_markets_case = (
        _clean(
            deep_dive.get(
                "capital_markets_support_view"
            )
        )
    )


    if prior_access_evidence:
        capital_markets_case = (
            capital_markets_case
            + " Historical precedent: "
            + prior_access_evidence
        )


    # ------------------------------------------------------------
    # CURRENT MACHINE / HUMAN VIEW
    # ------------------------------------------------------------

    machine_human_summary = (
        f"Machine: "
        f"{_clean(flagship.get('machine_view'))}. "
        f"Human Stage 2: "
        f"{review_status}. "
        f"Fundability: "
        f"{_clean(fundability.get('fundability'))}. "
        f"Funding timing: "
        f"{_clean(timing.get('funding_timing'))}."
    )


    # ------------------------------------------------------------
    # WHAT 180 COULD DO
    # ------------------------------------------------------------

    potential_180_role = (
        "Potential role is relationship-led origination and "
        "future placement readiness rather than pitching an "
        "immediate transaction. Verify Falcon's forward funding "
        "strategy, expected exploration budget and existing "
        "broker relationships before defining any mandate."
    )


    # ------------------------------------------------------------
    # WHAT WE MUST NOT CLAIM
    # ------------------------------------------------------------

    do_not_claim = (
        "Do not claim that Falcon is currently raising capital, "
        "that a placement is imminent, that a specific raise size "
        "is required, or that 180 Markets has an available mandate. "
        "The public evidence does not establish any of those points."
    )


    # ------------------------------------------------------------
    # DILIGENCE QUESTIONS
    # ------------------------------------------------------------

    diligence_questions = (
        _split_questions(
            deep_dive.get(
                "open_questions"
            )
        )
    )


    return {
        "ticker": ticker,

        "company": _clean(
            company.get(
                "company_name"
            )
        ),

        "positioning": (
            positioning
        ),

        "one_line_thesis": (
            "Strongly financeable explorer with visible "
            "exploration catalysts and demonstrated capital "
            "access, but without a presently disclosed "
            "near-term financing requirement."
        ),

        "machine_human_summary": (
            machine_human_summary
        ),

        "why_now": (
            why_now
        ),

        "funding_position": (
            financing_position
        ),

        "financing_window": (
            _clean(
                deep_dive.get(
                    "financing_window_view"
                )
            )
        ),

        "capital_markets_case": (
            capital_markets_case
        ),

        "capital_structure": (
            capital_structure_evidence
        ),

        "engagement_case": (
            engagement_case
        ),

        "potential_180_role": (
            potential_180_role
        ),

        "escalation_triggers": (
            escalation_triggers
        ),

        "key_risks": (
            _clean(
                deep_dive.get(
                    "key_risks"
                )
            )
        ),

        "diligence_questions": (
            diligence_questions
        ),

        "do_not_claim": (
            do_not_claim
        ),

        "confidence": (
            _clean(
                deep_dive.get(
                    "confidence"
                )
            )
        ),

        "funding_evidence": (
            funding_evidence
        ),
    }
