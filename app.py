import pandas as pd
import streamlit as st

from src.data_loader import (
    load_companies,
    load_sources,
    get_company,
    get_company_sources,
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
# HELPER FUNCTIONS
# ================================================================

def format_money(value, decimals=1):
    if pd.isna(value):
        return "Not available"

    return f"A${value:.{decimals}f}m"


def format_price(value):
    if pd.isna(value):
        return "Not available"

    return f"A${value:.3f}"


def format_quarters(value):
    if pd.isna(value):
        return "Not available"

    return f"{value:.2f} quarters"


def clean_text(value, fallback="Not available"):
    if pd.isna(value):
        return fallback

    text = str(value).strip()

    if not text:
        return fallback

    return text


# ================================================================
# LOAD DATA
# ================================================================

companies = load_companies()
all_sources = load_sources()

if companies.empty:
    st.error("No companies found in the screening universe.")
    st.stop()


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

    company_options = companies.sort_values("ticker").copy()

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
        company_options["selector_label"] == selected_label,
        "ticker",
    ].iloc[0]

    st.divider()

    st.caption(
        "Select a company from the screening universe "
        "to review its funding position, catalysts and evidence."
    )


# ================================================================
# UNIVERSE SUMMARY
# ================================================================

st.markdown("## Screening Universe")

summary1, summary2, summary3, summary4 = st.columns(4)

with summary1:
    st.metric("Companies Screened", len(companies))

with summary2:
    st.metric("Commodities", companies["commodity"].nunique())

with summary3:
    st.metric("Evidence Records", len(all_sources))

with summary4:
    st.metric(
        "Verified Evidence",
        int(all_sources["verified"].sum()),
    )


# ================================================================
# UNIVERSE TABLE
# ================================================================

universe_display = companies[
    [
        "ticker",
        "company_name",
        "commodity",
        "market_cap_aud_m",
        "cash_aud_m",
        "reported_quarters_funding",
        "next_catalyst",
        "catalyst_timing",
    ]
].copy()


universe_display["market_cap_aud_m"] = universe_display[
    "market_cap_aud_m"
].apply(
    lambda x: format_money(x, 1)
)

universe_display["cash_aud_m"] = universe_display[
    "cash_aud_m"
].apply(
    lambda x: format_money(x, 3)
)

universe_display["reported_quarters_funding"] = universe_display[
    "reported_quarters_funding"
].apply(
    format_quarters
)


universe_display = universe_display.rename(
    columns={
        "ticker": "Ticker",
        "company_name": "Company",
        "commodity": "Commodity",
        "market_cap_aud_m": "Market Cap",
        "cash_aud_m": "Cash",
        "reported_quarters_funding": "Reported Funding",
        "next_catalyst": "Next Catalyst",
        "catalyst_timing": "Catalyst Timing",
    }
)


st.dataframe(
    universe_display,
    width="stretch",
    hide_index=True,
)


st.caption(
    "The screening universe supports analyst review. "
    "It is not a ranking of investment attractiveness."
)


# ================================================================
# SELECTED COMPANY
# ================================================================

company = get_company(selected_ticker)
sources = get_company_sources(selected_ticker)

if company is None:
    st.error("Selected company could not be loaded.")
    st.stop()


st.divider()


# ================================================================
# COMPANY HEADER
# ================================================================

st.markdown(
    f"## {company['company_name']} ({company['ticker']})"
)

st.caption(
    f"{clean_text(company['sector'])} • "
    f"{clean_text(company['commodity'])} • "
    f"Data compiled as of {clean_text(company['data_as_of'])}"
)


# ================================================================
# KEY MARKET + FUNDING METRICS
# ================================================================

metric1, metric2, metric3, metric4 = st.columns(4)

with metric1:
    st.metric(
        "Share Price",
        format_price(company["share_price_aud"]),
    )

with metric2:
    st.metric(
        "Market Cap",
        format_money(company["market_cap_aud_m"], 1),
    )

with metric3:
    st.metric(
        "Cash",
        format_money(company["cash_aud_m"], 3),
    )

with metric4:
    st.metric(
        "Reported Funding",
        format_quarters(
            company["reported_quarters_funding"]
        ),
    )


# ================================================================
# PROGRAM + CATALYST
# ================================================================

research_left, research_right = st.columns(2)

with research_left:
    st.markdown("### Planned Program")

    st.write(
        clean_text(
            company["planned_program"],
            "No planned program captured.",
        )
    )


with research_right:
    st.markdown("### Next Catalyst")

    st.write(
        clean_text(
            company["next_catalyst"],
            "No catalyst captured.",
        )
    )

    catalyst_timing = clean_text(
        company["catalyst_timing"],
        "",
    )

    if catalyst_timing:
        st.caption(
            f"Timing: {catalyst_timing}"
        )


# ================================================================
# FUNDING POSITION
# ================================================================

st.markdown("### Funding Position")

funding1, funding2, funding3, funding4 = st.columns(4)

with funding1:
    st.metric(
        "Quarterly Operating Cash Flow",
        format_money(
            company["quarterly_operating_cf_aud_m"],
            3,
        ),
    )

with funding2:
    st.metric(
        "Exploration / Development Spend",
        format_money(
            company["exploration_development_spend_aud_m"],
            3,
        ),
    )

with funding3:
    st.metric(
        "Debt",
        format_money(
            company["debt_aud_m"],
            1,
        ),
    )

with funding4:
    st.metric(
        "Finance Facilities",
        format_money(
            company["finance_facilities_aud_m"],
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
# RECENT FINANCING
# ================================================================

st.markdown("### Recent Financing")

raise_amount = company["last_raise_amount_aud_m"]
raise_price = company["last_raise_price_aud"]
raise_type = company["last_raise_type"]
raise_date = company["last_raise_date"]

if (
    pd.notna(raise_amount)
    and pd.notna(raise_price)
    and pd.notna(raise_type)
    and pd.notna(raise_date)
):
    raise_text = (
        f"Last recorded raise: "
        f"A${raise_amount:.1f}m "
        f"{raise_type} at "
        f"A${raise_price:.2f} per share "
        f"on {raise_date}."
    )

    st.text(raise_text)

else:
    st.write(
        "No complete recent financing record captured."
    )


lead_manager = clean_text(
    company["lead_manager"],
    "",
)

if lead_manager:
    st.caption(
        f"Lead manager / broker: {lead_manager}"
    )


# ================================================================
# EVIDENCE LEDGER
# ================================================================

st.markdown("### Evidence Ledger")

verified_count = int(sources["verified"].sum())
unverified_count = len(sources) - verified_count

evidence1, evidence2, evidence3 = st.columns(3)

with evidence1:
    st.metric("Evidence Records", len(sources))

with evidence2:
    st.metric("Verified", verified_count)

with evidence3:
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
    "or predict that a company will undertake a capital raising."
)
