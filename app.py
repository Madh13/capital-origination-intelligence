import pandas as pd
import streamlit as st

from src.data_loader import (
    get_company,
    get_company_sources,
)


st.set_page_config(
    page_title="Capital Origination Intelligence",
    page_icon="📊",
    layout="wide",
)


st.title("Capital Origination Intelligence")
st.caption(
    "Public-data screening and research support for equity capital markets origination."
)


# -------------------------------------------------------------------
# COMPANY SELECTION
# -------------------------------------------------------------------

ticker = "FAL"

company = get_company(ticker)
sources = get_company_sources(ticker)

if company is None:
    st.error("Company not found.")
    st.stop()


st.divider()


# -------------------------------------------------------------------
# COMPANY HEADER
# -------------------------------------------------------------------

st.subheader(f"{company['company_name']} ({company['ticker']})")

st.caption(
    f"{company['sector']} • {company['commodity']} • "
    f"Data compiled as of {company['data_as_of']}"
)


# -------------------------------------------------------------------
# KEY MARKET + FUNDING METRICS
# -------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Share Price",
        f"A${company['share_price_aud']:.3f}",
    )

with col2:
    st.metric(
        "Market Cap",
        f"A${company['market_cap_aud_m']:.1f}m",
    )

with col3:
    st.metric(
        "Cash",
        f"A${company['cash_aud_m']:.3f}m",
    )

with col4:
    st.metric(
        "Reported Funding",
        f"{company['reported_quarters_funding']:.1f} quarters",
    )


# -------------------------------------------------------------------
# COMPANY RESEARCH
# -------------------------------------------------------------------

left, right = st.columns(2)

with left:
    st.markdown("### Planned Program")
    st.write(company["planned_program"])

with right:
    st.markdown("### Next Catalyst")
    st.write(company["next_catalyst"])

    if pd.notna(company["catalyst_timing"]):
        st.caption(f"Timing: {company['catalyst_timing']}")


# -------------------------------------------------------------------
# FUNDING POSITION
# -------------------------------------------------------------------

st.markdown("### Funding Position")

funding_col1, funding_col2, funding_col3 = st.columns(3)

with funding_col1:
    st.metric(
        "Quarterly Operating Cash Flow",
        f"A${company['quarterly_operating_cf_aud_m']:.3f}m",
    )

with funding_col2:
    st.metric(
        "Exploration / Development Spend",
        f"A${company['exploration_development_spend_aud_m']:.3f}m",
    )

with funding_col3:
    debt = company["debt_facilities_aud_m"]

    if pd.notna(debt):
        st.metric(
            "Debt / Facilities",
            f"A${debt:.1f}m",
        )
    else:
        st.metric(
            "Debt / Facilities",
            "Not disclosed",
        )


# -------------------------------------------------------------------
# RECENT FINANCING
# -------------------------------------------------------------------

st.markdown("### Recent Financing")

raise_text = (
    f"Last recorded raise: A${company['last_raise_amount_aud_m']:.1f}m "
    f"{company['last_raise_type']} at "
    f"A${company['last_raise_price_aud']:.2f} per share "
    f"on {company['last_raise_date']}."
)

st.text(raise_text)


# -------------------------------------------------------------------
# EVIDENCE LEDGER
# -------------------------------------------------------------------

st.markdown("### Evidence Ledger")

verified_count = int(sources["verified"].sum())
unverified_count = len(sources) - verified_count

evidence_col1, evidence_col2 = st.columns(2)

with evidence_col1:
    st.metric(
        "Verified Evidence",
        verified_count,
    )

with evidence_col2:
    st.metric(
        "Awaiting Primary Verification",
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


st.dataframe(
    display_sources,
    width="stretch",
    hide_index=True,
)


st.caption(
    "This prototype is an origination-support research tool, "
    "not an investment recommendation."
)
