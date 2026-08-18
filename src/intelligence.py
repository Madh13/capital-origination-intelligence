import pandas as pd


# ================================================================
# INTERNAL HELPERS
# ================================================================

def _is_missing(value):
    """Return True when a scalar value is missing or blank."""
    if pd.isna(value):
        return True

    if isinstance(value, str) and not value.strip():
        return True

    return False


def _safe_float(value):
    """Convert a value to float where possible."""
    if _is_missing(value):
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clean_text(value):
    """Return stripped text or None."""
    if _is_missing(value):
        return None

    return str(value).strip()


# ================================================================
# FUNDING TIMING
# ================================================================

def assess_funding_timing(company):
    """
    Assess funding timing using reported quarters of funding.

    This is deliberately a timing heuristic, not a prediction that
    a company will undertake a capital raising.
    """

    runway = _safe_float(
        company.get("reported_quarters_funding")
    )

    if runway is None:
        return {
            "label": "INSUFFICIENT EVIDENCE",
            "reason": (
                "Reported quarters of funding are not currently "
                "available."
            ),
        }

    if runway <= 1.5:
        label = "HIGH"

    elif runway <= 3.0:
        label = "ELEVATED"

    elif runway <= 5.0:
        label = "MODERATE"

    else:
        label = "LOW"

    return {
        "label": label,
        "reason": (
            f"Company reports approximately {runway:.2f} "
            "quarters of funding."
        ),
    }


# ================================================================
# FINANCING RECENCY
# ================================================================

def assess_financing_recency(company):
    """
    Categorise how recently the company completed its recorded raise.
    """

    raise_date_raw = company.get("last_raise_date")
    data_as_of_raw = company.get("data_as_of")

    if _is_missing(raise_date_raw):
        return {
            "label": "UNKNOWN",
            "days_since_raise": None,
            "reason": (
                "A complete recent financing date has not yet "
                "been captured."
            ),
        }

    if _is_missing(data_as_of_raw):
        return {
            "label": "UNKNOWN",
            "days_since_raise": None,
            "reason": (
                "The analysis date is unavailable, so financing "
                "recency cannot be calculated."
            ),
        }

    raise_date = pd.to_datetime(
        raise_date_raw,
        errors="coerce",
    )

    data_as_of = pd.to_datetime(
        data_as_of_raw,
        errors="coerce",
    )

    if pd.isna(raise_date) or pd.isna(data_as_of):
        return {
            "label": "UNKNOWN",
            "days_since_raise": None,
            "reason": (
                "The recorded financing date could not be "
                "interpreted reliably."
            ),
        }

    days_since_raise = (data_as_of - raise_date).days

    if days_since_raise < 0:
        return {
            "label": "UNKNOWN",
            "days_since_raise": None,
            "reason": (
                "The recorded financing date occurs after the "
                "analysis date and requires review."
            ),
        }

    if days_since_raise <= 120:
        label = "RECENT"

    elif days_since_raise <= 270:
        label = "INTERMEDIATE"

    else:
        label = "OLDER"

    return {
        "label": label,
        "days_since_raise": days_since_raise,
        "reason": (
            f"The latest recorded raise was approximately "
            f"{days_since_raise} days before the analysis date."
        ),
    }


# ================================================================
# CATALYST VISIBILITY
# ================================================================

def assess_catalyst_visibility(company):
    """
    Assess how clearly a catalyst and its timing are identifiable.

    This measures visibility of the catalyst in the current dataset.
    It does not claim to measure the economic strength of the catalyst.
    """

    catalyst = _clean_text(
        company.get("next_catalyst")
    )

    catalyst_date = _clean_text(
        company.get("catalyst_date")
    )

    catalyst_timing = _clean_text(
        company.get("catalyst_timing")
    )

    if catalyst is None:
        return {
            "label": "LIMITED",
            "reason": (
                "No specific next catalyst is currently captured."
            ),
        }

    if catalyst_date or catalyst_timing:
        return {
            "label": "HIGH",
            "reason": (
                "A specific catalyst is identified together with "
                "an expected timing window."
            ),
        }

    return {
        "label": "MODERATE",
        "reason": (
            "A specific catalyst is identified, but its timing "
            "is not yet captured."
        ),
    }


# ================================================================
# DATA CONFIDENCE
# ================================================================

def assess_data_confidence(sources):
    """
    Assess confidence in the current evidence ledger.

    This reflects the proportion of evidence records currently marked
    verified. It is not a guarantee that the underlying analysis is true.
    """

    if sources is None or len(sources) == 0:
        return {
            "label": "LIMITED",
            "verified": 0,
            "total": 0,
            "ratio": 0.0,
            "reason": "No evidence records are currently available.",
        }

    verified_series = sources["verified"].apply(
        lambda value: str(value).strip().lower()
        in {"true", "1", "yes"}
    )

    verified = int(verified_series.sum())
    total = len(sources)
    ratio = verified / total

    if ratio >= 0.80:
        label = "HIGH"

    elif ratio >= 0.50:
        label = "MODERATE"

    else:
        label = "LIMITED"

    return {
        "label": label,
        "verified": verified,
        "total": total,
        "ratio": ratio,
        "reason": (
            f"{verified} of {total} current evidence records "
            "are marked verified."
        ),
    }


# ================================================================
# PRELIMINARY OPPORTUNITY TIMING
# ================================================================

def determine_opportunity_timing(
    funding_timing,
    financing_recency,
    catalyst_visibility,
):
    """
    Combine timing signals into a preliminary origination category.

    IMPORTANT:
    This deliberately does not produce a probability of raising
    capital and does not yet constitute a complete fundability
    assessment.
    """

    funding = funding_timing["label"]
    financing = financing_recency["label"]
    catalyst = catalyst_visibility["label"]

    # Without a usable funding-timing input, do not force a conclusion.
    if funding == "INSUFFICIENT EVIDENCE":
        return "INSUFFICIENT EVIDENCE"

    # A company that has only recently raised and still has a
    # reasonable reported funding position is generally less urgent
    # from an origination-timing perspective.
    if (
        financing == "RECENT"
        and funding in {"LOW", "MODERATE"}
    ):
        return "LOWER CURRENT PRIORITY"

    # Tighter reported funding combined with a visible catalyst
    # warrants deeper analyst review.
    if (
        funding in {"HIGH", "ELEVATED"}
        and catalyst in {"HIGH", "MODERATE"}
    ):
        return "EARLY ENGAGEMENT REVIEW"

    # Moderate funding runway, an identifiable timed catalyst and an
    # older/intermediate financing can also justify earlier review.
    if (
        funding == "MODERATE"
        and catalyst == "HIGH"
        and financing in {"OLDER", "INTERMEDIATE"}
    ):
        return "EARLY ENGAGEMENT REVIEW"

    # Moderate runway without the combination above remains worth
    # monitoring rather than automatically escalating.
    if funding == "MODERATE":
        return "MONITOR"

    # Well-funded companies with strong catalyst visibility may still
    # be strategically interesting, but timing is less immediate.
    if (
        funding == "LOW"
        and catalyst == "HIGH"
    ):
        return "MONITOR"

    return "LOWER CURRENT PRIORITY"


# ================================================================
# DILIGENCE GAPS
# ================================================================

def build_diligence_gaps(
    company,
    funding_timing,
    financing_recency,
    data_confidence,
):
    """
    Identify important missing inputs before stronger origination
    conclusions are drawn.
    """

    gaps = []

    if financing_recency["label"] == "UNKNOWN":
        gaps.append(
            "Recent financing history requires additional diligence."
        )

    if funding_timing["label"] == "INSUFFICIENT EVIDENCE":
        gaps.append(
            "Reported funding runway requires primary-source review."
        )

    if data_confidence["label"] != "HIGH":
        gaps.append(
            "Additional primary-source verification is required."
        )

    debt = _safe_float(
        company.get("debt_aud_m")
    )

    facilities = _safe_float(
        company.get("finance_facilities_aud_m")
    )

    if debt is None and facilities is None:
        gaps.append(
            "Debt and financing-facility position is not yet "
            "fully captured."
        )

    if not gaps:
        gaps.append(
            "Full fundability analysis still requires market "
            "liquidity, recent trading behaviour and broader "
            "capital-markets context."
        )

    return gaps


# ================================================================
# FULL COMPANY ASSESSMENT
# ================================================================

def assess_company(company, sources):
    """
    Produce the complete preliminary origination-intelligence output
    for one company.
    """

    funding_timing = assess_funding_timing(company)

    financing_recency = assess_financing_recency(company)

    catalyst_visibility = assess_catalyst_visibility(company)

    data_confidence = assess_data_confidence(sources)

    opportunity_timing = determine_opportunity_timing(
        funding_timing,
        financing_recency,
        catalyst_visibility,
    )

    reasons = [
        funding_timing["reason"],
        financing_recency["reason"],
        catalyst_visibility["reason"],
        data_confidence["reason"],
    ]

    diligence_gaps = build_diligence_gaps(
        company,
        funding_timing,
        financing_recency,
        data_confidence,
    )

    return {
        "funding_timing": funding_timing["label"],
        "financing_recency": financing_recency["label"],
        "catalyst_visibility": catalyst_visibility["label"],
        "data_confidence": data_confidence["label"],
        "opportunity_timing": opportunity_timing,
        "reasons": reasons,
        "diligence_gaps": diligence_gaps,
    }


# ================================================================
# UNIVERSE ASSESSMENT
# ================================================================

def assess_universe(companies, sources):
    """
    Run the preliminary intelligence framework across the full
    screening universe.
    """

    assessments = []

    for _, company in companies.iterrows():
        ticker = str(company["ticker"]).upper()

        company_sources = sources[
            sources["ticker"]
            .astype(str)
            .str.upper()
            .eq(ticker)
        ].copy()

        result = assess_company(
            company,
            company_sources,
        )

        assessments.append(
            {
                "ticker": ticker,
                "funding_timing": result["funding_timing"],
                "financing_recency": result["financing_recency"],
                "catalyst_visibility": result[
                    "catalyst_visibility"
                ],
                "data_confidence": result["data_confidence"],
                "opportunity_timing": result[
                    "opportunity_timing"
                ],
            }
        )

    return pd.DataFrame(assessments)
