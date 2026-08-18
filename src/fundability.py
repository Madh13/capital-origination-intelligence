import pandas as pd


# ================================================================
# HELPERS
# ================================================================

def _missing(value):
    if value is None:
        return True

    try:
        if pd.isna(value):
            return True
    except (TypeError, ValueError):
        pass

    if isinstance(value, str) and not value.strip():
        return True

    return False


def _number(value):
    if _missing(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ================================================================
# LIQUIDITY
# ================================================================

def assess_liquidity(market):
    """
    Assess recent dollar liquidity.

    IMPORTANT:
    These are transparent prototype screening buckets,
    not claimed industry-standard thresholds.
    """

    if market is None:
        return {
            "label": "INSUFFICIENT EVIDENCE",
            "value": None,
            "reason": (
                "No refreshed market-data record is available."
            ),
        }

    status = str(
        market.get("refresh_status", "")
    ).upper()

    if status != "SUCCESS":
        return {
            "label": "INSUFFICIENT EVIDENCE",
            "value": None,
            "reason": (
                "The latest market-data refresh was unsuccessful."
            ),
        }

    adv = _number(
        market.get(
            "avg_daily_value_traded_20d_aud_m"
        )
    )

    if adv is None:
        return {
            "label": "INSUFFICIENT EVIDENCE",
            "value": None,
            "reason": (
                "20-day average daily value traded "
                "is unavailable."
            ),
        }

    if adv >= 0.20:
        label = "STRONG"

    elif adv >= 0.05:
        label = "MODERATE"

    elif adv >= 0.01:
        label = "THIN"

    else:
        label = "VERY THIN"

    return {
        "label": label,
        "value": adv,
        "reason": (
            "20-day average daily value traded is "
            f"approximately AUD {adv:.3f}m."
        ),
    }


# ================================================================
# MARKET MOMENTUM
# ================================================================

def assess_momentum(market):
    """
    Assess recent observed share-price behaviour.

    This is contextual information for fundability,
    not a prediction of future price performance.
    """

    if market is None:
        return {
            "label": "INSUFFICIENT EVIDENCE",
            "reason": (
                "No refreshed market-data record is available."
            ),
        }

    one_month = _number(
        market.get("return_1m_pct")
    )

    three_month = _number(
        market.get("return_3m_pct")
    )

    if one_month is None and three_month is None:
        return {
            "label": "INSUFFICIENT EVIDENCE",
            "reason": (
                "Recent price-performance data are unavailable."
            ),
        }

    if (
        one_month is not None
        and three_month is not None
    ):
        if one_month >= 0 and three_month >= 0:
            label = "SUPPORTIVE"

        elif one_month < 0 and three_month < 0:
            label = "WEAK"

        else:
            label = "MIXED"

        return {
            "label": label,
            "reason": (
                f"Recent price performance: "
                f"1M {one_month:+.2f}% and "
                f"3M {three_month:+.2f}%."
            ),
        }

    available = (
        one_month
        if one_month is not None
        else three_month
    )

    label = (
        "SUPPORTIVE"
        if available >= 0
        else "WEAK"
    )

    return {
        "label": label,
        "reason": (
            "Only one recent price-performance "
            "window is currently available."
        ),
    }


# ================================================================
# PREVIOUS ACCESS TO EQUITY CAPITAL
# ================================================================

def assess_prior_raise_access(company):
    """
    Identify whether a complete prior equity-raising record
    has been captured in the current dataset.
    """

    raise_date = company.get(
        "last_raise_date"
    )

    raise_amount = _number(
        company.get(
            "last_raise_amount_aud_m"
        )
    )

    if not _missing(raise_date) and raise_amount is not None:
        return {
            "label": "DEMONSTRATED",
            "reason": (
                "A complete previous capital-raising "
                "record is captured."
            ),
        }

    return {
        "label": "UNKNOWN",
        "reason": (
            "Previous equity-raising access has not yet "
            "been fully captured."
        ),
    }


# ================================================================
# MARKET-CAP CONTEXT
# ================================================================

def assess_market_cap_context(company):
    """
    Provide market-cap context without treating it as a
    standalone measure of fundability.
    """

    market_cap = _number(
        company.get("market_cap_aud_m")
    )

    if market_cap is None:
        return {
            "label": "UNKNOWN",
            "reason": (
                "Reference market capitalisation "
                "is unavailable."
            ),
        }

    if market_cap >= 150:
        label = "ABOVE AUD 150M"

    elif market_cap >= 75:
        label = "AUD 75–150M"

    elif market_cap >= 25:
        label = "AUD 25–75M"

    else:
        label = "BELOW AUD 25M"

    return {
        "label": label,
        "reason": (
            "Reference market capitalisation is "
            f"approximately AUD {market_cap:.1f}m."
        ),
    }


# ================================================================
# PRELIMINARY FUNDABILITY
# ================================================================

def determine_fundability(
    liquidity,
    momentum,
    prior_raise,
):
    """
    Combine observable public-market signals into a
    preliminary fundability category.

    No probability of raising capital is implied.
    """

    liquidity_label = liquidity["label"]
    momentum_label = momentum["label"]
    prior_label = prior_raise["label"]

    if liquidity_label == "INSUFFICIENT EVIDENCE":
        return "INSUFFICIENT EVIDENCE"

    # Extremely thin observable trading activity is a
    # material constraint regardless of funding need.
    if liquidity_label == "VERY THIN":
        return "WEAK"

    # Thin liquidity combined with weak momentum or an
    # unverified raising history remains a material constraint.
    if liquidity_label == "THIN":
        if (
            momentum_label == "WEAK"
            or prior_label == "UNKNOWN"
        ):
            return "WEAK"

        return "MODERATE"

    # Strong liquidity plus demonstrated prior access
    # provides the strongest observable public-market case.
    if (
        liquidity_label == "STRONG"
        and prior_label == "DEMONSTRATED"
        and momentum_label
        in {"SUPPORTIVE", "MIXED"}
    ):
        return "STRONG"

    if (
        liquidity_label == "STRONG"
        and prior_label == "DEMONSTRATED"
    ):
        return "STRONG"

    if (
        liquidity_label == "MODERATE"
        and prior_label == "DEMONSTRATED"
    ):
        return "MODERATE"

    if liquidity_label in {"STRONG", "MODERATE"}:
        return "MODERATE"

    return "WEAK"


# ================================================================
# DILIGENCE GAPS
# ================================================================

def build_fundability_gaps(
    liquidity,
    momentum,
    prior_raise,
):
    gaps = []

    if liquidity["label"] in {
        "THIN",
        "VERY THIN",
    }:
        gaps.append(
            "Observed trading liquidity may constrain "
            "equity fundability."
        )

    if momentum["label"] == "WEAK":
        gaps.append(
            "Recent share-price behaviour is currently "
            "a less supportive market backdrop."
        )

    if prior_raise["label"] == "UNKNOWN":
        gaps.append(
            "Previous capital-raising history requires "
            "additional diligence."
        )

    if (
        liquidity["label"]
        == "INSUFFICIENT EVIDENCE"
    ):
        gaps.append(
            "Market-liquidity data require review."
        )

    if not gaps:
        gaps.append(
            "Further fundability diligence should still "
            "consider capital structure, investor appetite, "
            "management credibility and sector conditions."
        )

    return gaps


# ================================================================
# FULL FUNDABILITY ASSESSMENT
# ================================================================

def assess_fundability(company, market):
    liquidity = assess_liquidity(market)

    momentum = assess_momentum(market)

    prior_raise = assess_prior_raise_access(
        company
    )

    market_cap_context = (
        assess_market_cap_context(company)
    )

    fundability = determine_fundability(
        liquidity,
        momentum,
        prior_raise,
    )

    reasons = [
        liquidity["reason"],
        momentum["reason"],
        prior_raise["reason"],
        market_cap_context["reason"],
    ]

    gaps = build_fundability_gaps(
        liquidity,
        momentum,
        prior_raise,
    )

    return {
        "fundability": fundability,
        "liquidity": liquidity["label"],
        "momentum": momentum["label"],
        "prior_raise_access": prior_raise["label"],
        "market_cap_context": (
            market_cap_context["label"]
        ),
        "reasons": reasons,
        "diligence_gaps": gaps,
    }


# ================================================================
# INTEGRATED ORIGINATION VIEW
# ================================================================
# ================================================================
# INTEGRATED ORIGINATION VIEW
# ================================================================

def integrate_origination_view(
    timing_assessment,
    fundability_assessment,
):
    """
    Combine financing timing with preliminary fundability.

    Recent financing is explicitly considered before escalation.
    This prevents a recently funded company from becoming a
    priority solely because a reported runway metric is tight.
    """

    funding = timing_assessment[
        "funding_timing"
    ]

    financing = timing_assessment[
        "financing_recency"
    ]

    catalyst = timing_assessment[
        "catalyst_visibility"
    ]

    timing_view = timing_assessment[
        "opportunity_timing"
    ]

    fundability = fundability_assessment[
        "fundability"
    ]


    # ------------------------------------------------------------
    # EVIDENCE CONTROL
    # ------------------------------------------------------------

    if (
        funding == "INSUFFICIENT EVIDENCE"
        or fundability == "INSUFFICIENT EVIDENCE"
    ):
        return "INSUFFICIENT EVIDENCE"


    # ------------------------------------------------------------
    # RECENTLY FUNDED COMPANIES
    # ------------------------------------------------------------

    # A recent financing materially changes origination timing.
    # Moderate/low funding pressure after a recent raise is
    # generally lower priority.

    if financing == "RECENT":

        if funding in {"LOW", "MODERATE"}:
            return "LOWER CURRENT PRIORITY"

        # Elevated/high reported funding pressure immediately
        # after a raise can reflect an intensive work program.
        # It warrants monitoring rather than automatic escalation.

        if funding in {"ELEVATED", "HIGH"}:

            if fundability == "WEAK":
                return "MONITOR — FUNDABILITY CONSTRAINT"

            return "MONITOR — RECENTLY FUNDED"


    # ------------------------------------------------------------
    # HIGH / ELEVATED FUNDING TIMING
    # ------------------------------------------------------------

    if funding in {"HIGH", "ELEVATED"}:

        if (
            fundability in {"STRONG", "MODERATE"}
            and catalyst in {"HIGH", "MODERATE"}
        ):
            return "PRIORITY REVIEW"

        if fundability == "WEAK":
            return "MONITOR — FUNDABILITY CONSTRAINT"


    # ------------------------------------------------------------
    # EARLY ENGAGEMENT
    # ------------------------------------------------------------

    if timing_view == "EARLY ENGAGEMENT REVIEW":

        if fundability in {"STRONG", "MODERATE"}:
            return "EARLY ENGAGEMENT REVIEW"

        return "MONITOR — FUNDABILITY CONSTRAINT"


    # ------------------------------------------------------------
    # REMAINING TIMING STATES
    # ------------------------------------------------------------

    if timing_view == "LOWER CURRENT PRIORITY":
        return "LOWER CURRENT PRIORITY"

    if timing_view == "MONITOR":
        return "MONITOR"

    return timing_view
