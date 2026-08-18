import pandas as pd
import streamlit as st

from src.data_loader import (
    load_companies,
    load_sources,
    load_market_data,
    get_company,
    get_company_sources,
    get_market_snapshot,
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


# ================================================================
# PAGE CONFIGURATION
# ================================================================

st.set_page_config(
    page_title="Capital Origination Intelligence",
    page_icon="📊",
    layout="wide",
)


# ================================================================
# FORMATTERS
# ================================================================

def format_money(value, decimals=1):
    if pd.isna(value):
        return "Not available"

    return f"A${float(value):.{decimals}f}m"


def format_price(value):
    if pd.isna(value):
        return "Not available"

    return f"A${float(value):.3f}"


def format_quarters(value):
    if pd.isna(value):
        return "Not available"

    return f"{float(value):.2f} quarters"


def format_return(value):
    if pd.isna(value):
        return "Not available"

    return f"{float(value):+.2f}%"


def clean_text(value, fallback="Not available"):
    if pd.isna(value):
        return fallback

    text = str(value).strip()

    return text if text else fallback


# ================================================================
# LOAD DATA
# ================================================================

companies = load_companies()
all_sources = load_sources()
market_data = load_market_data()

if companies.empty:
    st.error("No companies found.")
    st.stop()


# ================================================================
# BUILD ORIGINATION PIPELINE
# ================================================================

pipeline = build_pipeline(
    companies,
    market_data,
    all_sources,
    assess_company,
    assess_fundability,
    integrate_origination_view,
)

pipeline_summary = pipeline_counts(
    pipeline
)


# ================================================================
# BUILD UNIVERSE INTELLIGENCE
# ================================================================

universe_rows = []

for _, company_row in companies.iterrows():
    ticker = company_row["ticker"]

    company_sources = all_sources[
        all_sources["ticker"] == ticker
    ]

    market_match = market_data[
        market_data["ticker"] == ticker
    ]

    market_row = (
        market_match.iloc[0]
        if not market_match.empty
        else None
    )

    timing = assess_company(
        company_row,
        company_sources,
    )

    fundability = assess_fundability(
        company_row,
        market_row,
    )

    integrated = integrate_origination_view(
        timing,
        fundability,
    )

    universe_rows.append(
        {
            "ticker": ticker,
            "company_name": company_row[
                "company_name"
            ],
            "commodity": company_row[
                "commodity"
            ],
            "reported_funding": company_row[
                "reported_quarters_funding"
            ],
            "funding_timing": timing[
                "funding_timing"
            ],
            "liquidity": fundability[
                "liquidity"
            ],
            "fundability": fundability[
                "fundability"
            ],
            "integrated_view": integrated,
        }
    )


universe_intelligence = pd.DataFrame(
    universe_rows
)


# ================================================================
# HEADER
# ================================================================

st.title("Capital Origination Intelligence")

st.caption(
    "Public-data screening and research support for "
    "equity capital markets origination."
)


# ================================================================
# SIDEBAR
# ================================================================

with st.sidebar:
    st.header("Company Review")

    company_options = companies.sort_values(
        "ticker"
    ).copy()

    company_options["selector_label"] = (
        company_options["ticker"]
        + " — "
        + company_options["company_name"]
    )

    selected_label = st.selectbox(
        "Select company",
        company_options["selector_label"].tolist(),
    )

    selected_ticker = company_options.loc[
        company_options["selector_label"]
        == selected_label,
        "ticker",
    ].iloc[0]

    st.divider()

    st.caption(
        "Review funding timing, market fundability, "
        "catalysts and supporting evidence."
    )


# ================================================================
# ORIGINATION PIPELINE
# ================================================================

st.markdown("## Origination Pipeline")

st.caption(
    "Analyst-review queue generated from funding timing, "
    "market fundability, catalyst visibility and financing context."
)


pipe1, pipe2, pipe3, pipe4 = st.columns(4)

with pipe1:
    st.metric(
        "Active Review",
        pipeline_summary[
            "active_review"
        ],
    )

with pipe2:
    st.metric(
        "Monitor",
        pipeline_summary[
            "monitor"
        ],
    )

with pipe3:
    st.metric(
        "Lower Priority",
        pipeline_summary[
            "lower_priority"
        ],
    )

with pipe4:
    st.metric(
        "Incomplete Diligence",
        pipeline_summary[
            "insufficient"
        ],
    )


pipeline_display = pipeline[
    [
        "pipeline_stage",
        "ticker",
        "company",
        "commodity",
        "funding_timing",
        "fundability",
        "rationale",
        "analyst_action",
    ]
].copy()


pipeline_display = pipeline_display.rename(
    columns={
        "pipeline_stage": "Pipeline Stage",
        "ticker": "Ticker",
        "company": "Company",
        "commodity": "Commodity",
        "funding_timing": "Funding Timing",
        "fundability": "Fundability",
        "rationale": "Why Here",
        "analyst_action": "Next Analyst Action",
    }
)


st.dataframe(
    pipeline_display,
    width="stretch",
    hide_index=True,
)


st.caption(
    "Pipeline placement is an origination-workflow signal, "
    "not an investment ranking or prediction of a financing event."
)


st.divider()


# ================================================================
# SCREENING UNIVERSE
# ================================================================

st.markdown("## Screening Universe")

summary1, summary2, summary3, summary4 = st.columns(4)

with summary1:
    st.metric(
        "Companies Screened",
        len(companies),
    )

with summary2:
    st.metric(
        "Market Feeds",
        int(
            (
                market_data["refresh_status"]
                == "SUCCESS"
            ).sum()
        ),
    )

with summary3:
    st.metric(
        "Evidence Records",
        len(all_sources),
    )

with summary4:
    st.metric(
        "Verified Evidence",
        int(
            all_sources["verified"].sum()
        ),
    )


universe_display = universe_intelligence.copy()

universe_display[
    "reported_funding"
] = universe_display[
    "reported_funding"
].apply(
    format_quarters
)


universe_display = universe_display.rename(
    columns={
        "ticker": "Ticker",
        "company_name": "Company",
        "commodity": "Commodity",
        "reported_funding": "Reported Funding",
        "funding_timing": "Funding Timing",
        "liquidity": "Liquidity",
        "fundability": "Fundability",
        "integrated_view": "Integrated Origination View",
    }
)


st.dataframe(
    universe_display,
    width="stretch",
    hide_index=True,
)


st.caption(
    "The integrated view combines financing timing "
    "with preliminary public-market fundability. "
    "It is not an investment recommendation or prediction."
)


# ================================================================
# SELECT COMPANY
# ================================================================

company = get_company(
    selected_ticker
)

sources = get_company_sources(
    selected_ticker
)

market = get_market_snapshot(
    selected_ticker
)

timing = assess_company(
    company,
    sources,
)

fundability = assess_fundability(
    company,
    market,
)

integrated_view = integrate_origination_view(
    timing,
    fundability,
)


st.divider()


# ================================================================
# COMPANY HEADER
# ================================================================

st.markdown(
    f"## {company['company_name']} "
    f"({company['ticker']})"
)

st.caption(
    f"{clean_text(company['sector'])} • "
    f"{clean_text(company['commodity'])} • "
    f"Research compiled as of "
    f"{clean_text(company['data_as_of'])}"
)


# ================================================================
# CORE METRICS
# ================================================================

latest_price = (
    market["latest_price_aud"]
    if market is not None
    else company["share_price_aud"]
)

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Latest Market Price",
        format_price(latest_price),
    )

with metric2:
    st.metric(
        "Reference Market Cap",
        format_money(
            company["market_cap_aud_m"],
            1,
        ),
    )

with metric3:
    st.metric(
        "Cash",
        format_money(
            company["cash_aud_m"],
            3,
        ),
    )

with metric4:
    st.metric(
        "Reported Funding",
        format_quarters(
            company[
                "reported_quarters_funding"
            ]
        ),
    )


if market is not None:
    st.caption(
        "Market data refreshed through "
        f"{market['latest_market_date']}. "
        "Reference market capitalisation remains "
        "the sourced company snapshot."
    )


# ================================================================
# INTEGRATED ORIGINATION INTELLIGENCE
# ================================================================

st.markdown(
    "### Integrated Origination Intelligence"
)

intel1, intel2, intel3, intel4 = st.columns(4)

with intel1:
    st.metric(
        "Funding Timing",
        timing["funding_timing"],
    )

with intel2:
    st.metric(
        "Fundability",
        fundability["fundability"],
    )

with intel3:
    st.metric(
        "Catalyst Visibility",
        timing["catalyst_visibility"],
    )

with intel4:
    st.metric(
        "Data Confidence",
        timing["data_confidence"],
    )


st.info(
    "Integrated Origination View: "
    f"{integrated_view}"
)


# ================================================================
# MARKET FUNDABILITY
# ================================================================

st.markdown(
    "### Market Fundability"
)

market1, market2, market3, market4 = st.columns(4)

if market is not None:

    with market1:
        st.metric(
            "20D Avg Daily Value",
            format_money(
                market[
                    "avg_daily_value_traded_20d_aud_m"
                ],
                3,
            ),
        )

    with market2:
        st.metric(
            "1M Price Change",
            format_return(
                market["return_1m_pct"]
            ),
        )

    with market3:
        st.metric(
            "3M Price Change",
            format_return(
                market["return_3m_pct"]
            ),
        )

    with market4:
        st.metric(
            "Prior Raise Access",
            fundability[
                "prior_raise_access"
            ],
        )

else:
    st.warning(
        "No refreshed market data are currently "
        "available for this company."
    )


# ================================================================
# EXPLAINABILITY
# ================================================================

explain_left, explain_right = st.columns(2)

with explain_left:
    st.markdown("#### Why It Surfaced")

    for reason in timing["reasons"]:
        st.write(
            f"• {reason}"
        )

    for reason in fundability["reasons"]:
        st.write(
            f"• {reason}"
        )


with explain_right:
    st.markdown("#### Diligence Required")

    combined_gaps = (
        timing["diligence_gaps"]
        + fundability["diligence_gaps"]
    )

    seen = set()

    for gap in combined_gaps:
        if gap not in seen:
            st.write(
                f"• {gap}"
            )
            seen.add(gap)


st.caption(
    "Prototype fundability categories use transparent "
    "internal screening thresholds. They are not claimed "
    "industry standards and remain subject to analyst judgment."
)


# ================================================================
# PROGRAM + CATALYST
# ================================================================

program_left, program_right = st.columns(2)

with program_left:
    st.markdown(
        "### Planned Program"
    )

    st.write(
        clean_text(
            company["planned_program"],
            "No planned program captured.",
        )
    )


with program_right:
    st.markdown(
        "### Next Catalyst"
    )

    st.write(
        clean_text(
            company["next_catalyst"],
            "No catalyst captured.",
        )
    )

    timing_text = clean_text(
        company["catalyst_timing"],
        "",
    )

    if timing_text:
        st.caption(
            f"Timing: {timing_text}"
        )


# ================================================================
# FUNDING POSITION
# ================================================================

st.markdown(
    "### Funding Position"
)

fund1, fund2, fund3, fund4 = st.columns(4)

with fund1:
    st.metric(
        "Quarterly Operating Cash Flow",
        format_money(
            company[
                "quarterly_operating_cf_aud_m"
            ],
            3,
        ),
    )

with fund2:
    st.metric(
        "Exploration / Development Spend",
        format_money(
            company[
                "exploration_development_spend_aud_m"
            ],
            3,
        ),
    )

with fund3:
    st.metric(
        "Debt",
        format_money(
            company["debt_aud_m"],
            1,
        ),
    )

with fund4:
    st.metric(
        "Finance Facilities",
        format_money(
            company[
                "finance_facilities_aud_m"
            ],
            2,
        ),
    )


facility_notes = clean_text(
    company["facility_notes"],
    "",
)

if facility_notes:
    st.caption(
        f"Facilities note: {facility_notes}"
    )


# ================================================================
# EVIDENCE LEDGER
# ================================================================

st.markdown(
    "### Evidence Ledger"
)

verified_count = int(
    sources["verified"].sum()
)

unverified_count = (
    len(sources) - verified_count
)

ev1, ev2, ev3 = st.columns(3)

with ev1:
    st.metric(
        "Evidence Records",
        len(sources),
    )

with ev2:
    st.metric(
        "Verified",
        verified_count,
    )

with ev3:
    st.metric(
        "Awaiting Verification",
        unverified_count,
    )


display_sources = sources[
    [
        "field_name",
        "source_type",
        "source_title",
        "source_date",
        "reported_value",
        "verified",
        "source_url",
    ]
].copy()


display_sources = display_sources.rename(
    columns={
        "field_name": "Field",
        "source_type": "Source Type",
        "source_title": "Source",
        "source_date": "Date",
        "reported_value": "Reported Value",
        "verified": "Verified",
        "source_url": "Source URL",
    }
)


st.dataframe(
    display_sources,
    width="stretch",
    hide_index=True,
)


# ================================================================
# DISCLAIMER
# ================================================================

st.divider()

st.caption(
    "Capital Origination Intelligence is a public-data "
    "origination-support research prototype. "
    "It does not provide investment recommendations "
    "or predict that a company will undertake a "
    "capital raising."
)
