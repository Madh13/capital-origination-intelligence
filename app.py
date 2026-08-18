import pandas as pd
import streamlit as st

from src.data_loader import (
    load_companies,
    load_sources,
    load_market_data,
    get_company,
    get_company_sources,
    get_market_snapshot,
    get_deep_dive,
    get_deep_dive_evidence,
    load_deep_dives,
    load_state_history,
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

from src.history import (
    analyse_latest_changes,
)

from src.prebrief import (
    build_machine_prebrief,
)

from src.committee import (
    build_opportunity_committee,
    committee_counts,
)

from src.shortlist import (
    build_shortlist_comparison,
    select_flagship,
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
state_history = load_state_history()
all_deep_dives = load_deep_dives()

history_analysis = analyse_latest_changes(
    state_history
)

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

committee = build_opportunity_committee(
    pipeline,
    all_deep_dives,
)

committee_summary = committee_counts(
    committee
)

shortlist_comparison = build_shortlist_comparison(
    committee,
    companies,
    all_sources,
    market_data,
)

flagship = select_flagship(
    shortlist_comparison
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
# OPPORTUNITY COMMITTEE
# ================================================================

st.markdown(
    "## Opportunity Committee"
)

st.caption(
    "Shortlist generated by combining the machine screening "
    "pipeline with completed Stage 2 analyst diligence."
)


committee_col1, committee_col2, committee_col3, committee_col4 = (
    st.columns(4)
)

with committee_col1:
    st.metric(
        "Shortlist",
        committee_summary[
            "shortlist"
        ],
    )

with committee_col2:
    st.metric(
        "Reserve",
        committee_summary[
            "reserve"
        ],
    )

with committee_col3:
    st.metric(
        "Deferred",
        committee_summary[
            "deferred"
        ],
    )

with committee_col4:
    st.metric(
        "Rejected",
        committee_summary[
            "rejected"
        ],
    )


# ------------------------------------------------------------
# FORMAL SHORTLIST
# ------------------------------------------------------------

formal_shortlist = committee[
    committee[
        "formal_shortlist"
    ]
].copy()


if formal_shortlist.empty:

    st.warning(
        "No companies currently qualify for the formal shortlist."
    )

else:

    shortlist_tickers = (
        formal_shortlist[
            "ticker"
        ]
        .astype(str)
        .tolist()
    )

    st.success(
        "Formal Shortlist: "
        + " • ".join(
            shortlist_tickers
        )
    )


    shortlist_display = formal_shortlist[
        [
            "ticker",
            "company",
            "machine_view",
            "human_stage2",
            "machine_human_relationship",
            "next_action",
        ]
    ].copy()


    shortlist_display = shortlist_display.rename(
        columns={
            "ticker": "Ticker",
            "company": "Company",
            "machine_view": "Machine View",
            "human_stage2": "Human Stage 2",
            "machine_human_relationship": "Machine / Human",
            "next_action": "Next Action",
        }
    )


    st.dataframe(
        shortlist_display,
        width="stretch",
        hide_index=True,
    )


# ------------------------------------------------------------
# FULL COMMITTEE AUDIT
# ------------------------------------------------------------

with st.expander(
    "View Full Opportunity Committee",
    expanded=False,
):

    committee_display = committee[
        [
            "committee_decision",
            "ticker",
            "company",
            "machine_view",
            "human_stage2",
            "machine_human_relationship",
            "committee_rationale",
            "next_action",
        ]
    ].copy()


    committee_display = committee_display.rename(
        columns={
            "committee_decision": "Decision",
            "ticker": "Ticker",
            "company": "Company",
            "machine_view": "Machine View",
            "human_stage2": "Human Stage 2",
            "machine_human_relationship": "Machine / Human",
            "committee_rationale": "Why",
            "next_action": "Next Action",
        }
    )


    st.dataframe(
        committee_display,
        width="stretch",
        hide_index=True,
    )


st.caption(
    "Shortlist placement is an origination workflow decision, "
    "not an investment recommendation."
)

st.divider()


# ================================================================
# SHORTLIST COMPARISON
# ================================================================

st.markdown(
    "## Shortlist Comparison"
)

st.caption(
    "Commercial comparison of shortlisted opportunities using "
    "transparent categorical criteria rather than a weighted score."
)


if shortlist_comparison.empty:

    st.info(
        "No shortlisted companies are currently available "
        "for comparison."
    )

else:

    comparison_display = shortlist_comparison[
        [
            "ticker",
            "funding_timing",
            "fundability",
            "catalyst_visibility",
            "data_confidence",
            "equity_relevance",
            "financing_complexity",
            "time_horizon",
            "origination_actionability",
            "flagship_ready",
        ]
    ].copy()


    comparison_display = comparison_display.rename(
        columns={
            "ticker": "Ticker",
            "funding_timing": "Funding Timing",
            "fundability": "Fundability",
            "catalyst_visibility": "Catalyst",
            "data_confidence": "Machine Confidence",
            "equity_relevance": "Equity Relevance",
            "financing_complexity": "Financing Complexity",
            "time_horizon": "Time Horizon",
            "origination_actionability": "Actionability",
            "flagship_ready": "Flagship Ready",
        }
    )


    st.dataframe(
        comparison_display,
        width="stretch",
        hide_index=True,
    )


# ------------------------------------------------------------
# FLAGSHIP
# ------------------------------------------------------------

st.markdown(
    "### Flagship Opportunity"
)


if flagship is None:

    st.warning(
        "No unique flagship currently satisfies all transparent "
        "selection conditions. Analyst judgment is required."
    )

else:

    st.success(
        f"{flagship['ticker']} — "
        f"{flagship['company']}"
    )


    flagship1, flagship2, flagship3, flagship4 = (
        st.columns(4)
    )


    with flagship1:
        st.metric(
            "Fundability",
            flagship[
                "fundability"
            ],
        )


    with flagship2:
        st.metric(
            "Equity Relevance",
            flagship[
                "equity_relevance"
            ],
        )


    with flagship3:
        st.metric(
            "Actionability",
            flagship[
                "origination_actionability"
            ],
        )


    with flagship4:
        st.metric(
            "Financing Complexity",
            flagship[
                "financing_complexity"
            ],
        )


    st.markdown(
        "**Why it leads**"
    )

    st.write(
        flagship[
            "comparison_rationale"
        ]
    )


st.caption(
    "Flagship selection is based on transparent origination "
    "conditions, not a predictive financing score or investment ranking."
)

st.divider()


# ================================================================
# UNIVERSE CHANGE MONITOR
# ================================================================

changes = history_analysis[
    "changes"
]

movements = history_analysis[
    "movements"
]


with st.expander(
    "Universe Change Monitor",
    expanded=False,
):

    st.caption(
        "Material changes across the full screening universe "
        "between the two most recent stored machine snapshots."
    )


    if changes.empty:

        st.write(
            "No material universe-level changes detected."
        )

    else:

        universe_change1, universe_change2 = st.columns(2)

        with universe_change1:
            st.metric(
                "Companies Changed",
                changes[
                    "ticker"
                ].nunique(),
            )

        with universe_change2:
            st.metric(
                "Pipeline Movements",
                len(
                    movements
                ),
            )


        if not movements.empty:

            movement_display = movements[
                [
                    "ticker",
                    "old_value",
                    "new_value",
                ]
            ].copy()


            movement_display = (
                movement_display.rename(
                    columns={
                        "ticker": "Ticker",
                        "old_value": "Previous View",
                        "new_value": "Current View",
                    }
                )
            )


            st.dataframe(
                movement_display,
                width="stretch",
                hide_index=True,
            )


        with st.expander(
            "Full Universe Change Audit",
            expanded=False,
        ):

            audit = changes[
                [
                    "ticker",
                    "field",
                    "old_value",
                    "new_value",
                    "change_type",
                ]
            ].copy()


            audit = audit.rename(
                columns={
                    "ticker": "Ticker",
                    "field": "Changed Field",
                    "old_value": "Previous",
                    "new_value": "Current",
                    "change_type": "Change Type",
                }
            )


            st.dataframe(
                audit,
                width="stretch",
                hide_index=True,
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

deep_dive = get_deep_dive(
    selected_ticker
)

deep_dive_evidence = get_deep_dive_evidence(
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

selected_change_brief = (
    history_analysis[
        "briefs"
    ].get(
        selected_ticker
    )
)

machine_prebrief = build_machine_prebrief(
    selected_ticker,
    timing,
    fundability,
    integrated_view,
    selected_change_brief,
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
# MACHINE PRE-BRIEF
# ================================================================

st.divider()

st.markdown(
    "### Machine Pre-Brief"
)

st.caption(
    "Automatically generated from structured company data, "
    "market data, evidence quality and the rules-based "
    "origination engine. Human Stage 2 judgment remains separate."
)


machine1, machine2, machine3, machine4 = st.columns(4)

with machine1:
    st.markdown(
        "**Machine View**"
    )

    st.write(
        machine_prebrief[
            "machine_view"
        ]
    )


with machine2:
    st.markdown(
        "**Funding Timing**"
    )

    st.write(
        machine_prebrief[
            "funding_timing"
        ]
    )


with machine3:
    st.markdown(
        "**Fundability**"
    )

    st.write(
        machine_prebrief[
            "fundability"
        ]
    )


with machine4:
    st.markdown(
        "**Confidence**"
    )

    st.write(
        machine_prebrief[
            "data_confidence"
        ]
    )


st.markdown(
    "#### Machine Thesis"
)

st.write(
    machine_prebrief[
        "machine_thesis"
    ]
)


st.markdown(
    "#### Recommended Machine Action"
)

st.write(
    machine_prebrief[
        "recommended_machine_action"
    ]
)


# ------------------------------------------------------------
# SELECTED-COMPANY CHANGE
# ------------------------------------------------------------

st.markdown(
    "#### Recent Machine Change"
)

if selected_change_brief:

    st.info(
        selected_change_brief
    )

else:

    st.caption(
        "No material change was detected for this company "
        "between the two latest stored snapshots."
    )


# ------------------------------------------------------------
# MACHINE EXPLAINABILITY
# ------------------------------------------------------------

with st.expander(
    "Machine Rationale and Diligence Priorities",
    expanded=False,
):

    rationale_left, rationale_right = st.columns(2)


    with rationale_left:

        st.markdown(
            "##### Machine Rationale"
        )

        for reason in machine_prebrief[
            "reasons"
        ]:

            st.write(
                f"• {reason}"
            )


    with rationale_right:

        st.markdown(
            "##### Diligence Priorities"
        )

        for gap in machine_prebrief[
            "diligence_priorities"
        ]:

            st.write(
                f"• {gap}"
            )


st.caption(
    "The Machine Pre-Brief is generated automatically. "
    "It does not replace analyst review."
)


# ================================================================
# STAGE 2 OPPORTUNITY DILIGENCE
# ================================================================

st.divider()

st.markdown(
    "### Stage 2 Opportunity Diligence"
)

st.caption(
    "Human analyst judgment layered on top of the automated "
    "screen. Facts and analyst inferences are tracked separately."
)


if deep_dive is None:

    st.info(
        "Stage 2 deep-dive diligence has not yet been "
        "completed for this company."
    )

else:

    # ------------------------------------------------------------
    # REVIEW STATUS
    # ------------------------------------------------------------

    stage_status1, stage_status2, stage_status3 = st.columns(3)

    with stage_status1:
        st.markdown("**Review Status**")
        st.write(
            clean_text(
                deep_dive["review_status"]
            )
        )

    with stage_status2:
        st.markdown("**Confidence**")
        st.write(
            clean_text(
                deep_dive["confidence"]
            )
        )

    with stage_status3:
        st.markdown("**Last Reviewed**")
        st.write(
            clean_text(
                deep_dive["last_reviewed"]
            )
        )


    # ------------------------------------------------------------
    # CORE THESIS
    # ------------------------------------------------------------

    st.markdown("#### Core Thesis")

    st.write(
        clean_text(
            deep_dive["core_thesis"]
        )
    )


    # ------------------------------------------------------------
    # FINANCING THESIS
    # ------------------------------------------------------------

    financing_left, financing_right = st.columns(2)

    with financing_left:
        st.markdown("#### Financing Need")

        st.write(
            clean_text(
                deep_dive[
                    "financing_need_view"
                ]
            )
        )

    with financing_right:
        st.markdown("#### Financing Window")

        st.write(
            clean_text(
                deep_dive[
                    "financing_window_view"
                ]
            )
        )


    # ------------------------------------------------------------
    # CAPITAL MARKETS + CATALYST
    # ------------------------------------------------------------

    capital_left, capital_right = st.columns(2)

    with capital_left:
        st.markdown(
            "#### Capital-Markets Support"
        )

        st.write(
            clean_text(
                deep_dive[
                    "capital_markets_support_view"
                ]
            )
        )

    with capital_right:
        st.markdown(
            "#### Catalyst Quality"
        )

        st.write(
            clean_text(
                deep_dive[
                    "catalyst_quality_view"
                ]
            )
        )


    # ------------------------------------------------------------
    # 180 FIT + MANAGEMENT
    # ------------------------------------------------------------

    fit_left, fit_right = st.columns(2)

    with fit_left:
        st.markdown(
            "#### 180 Markets Fit"
        )

        st.write(
            clean_text(
                deep_dive[
                    "fit_180_view"
                ]
            )
        )

    with fit_right:
        st.markdown(
            "#### Management / Execution"
        )

        st.write(
            clean_text(
                deep_dive[
                    "management_execution_view"
                ]
            )
        )


    # ------------------------------------------------------------
    # ANALYST VERDICT
    # ------------------------------------------------------------

    st.info(
        "Analyst Verdict: "
        + clean_text(
            deep_dive[
                "analyst_verdict"
            ]
        )
    )


    # ------------------------------------------------------------
    # FULL DILIGENCE
    # ------------------------------------------------------------

    with st.expander(
        "Full Stage 2 Diligence",
        expanded=False,
    ):

        st.markdown(
            "##### Likely Use of Proceeds"
        )

        st.write(
            clean_text(
                deep_dive[
                    "likely_use_of_proceeds_view"
                ]
            )
        )


        st.markdown(
            "##### Plausible Financing Structure"
        )

        st.write(
            clean_text(
                deep_dive[
                    "plausible_structure_view"
                ]
            )
        )


        st.markdown(
            "##### Raise Size View"
        )

        st.write(
            clean_text(
                deep_dive[
                    "raise_size_view"
                ]
            )
        )


        st.markdown(
            "##### Previous Brokers / Managers"
        )

        st.write(
            clean_text(
                deep_dive[
                    "prior_brokers_view"
                ]
            )
        )


        st.markdown(
            "##### Shareholder Register"
        )

        st.write(
            clean_text(
                deep_dive[
                    "shareholder_register_view"
                ]
            )
        )


        st.markdown(
            "##### Key Risks"
        )

        st.write(
            clean_text(
                deep_dive[
                    "key_risks"
                ]
            )
        )


        st.markdown(
            "##### Kill Conditions"
        )

        st.write(
            clean_text(
                deep_dive[
                    "kill_conditions"
                ]
            )
        )


        st.markdown(
            "##### Open Questions"
        )

        st.write(
            clean_text(
                deep_dive[
                    "open_questions"
                ]
            )
        )


    # ------------------------------------------------------------
    # DEEP-DIVE EVIDENCE TRAIL
    # ------------------------------------------------------------

    with st.expander(
        "Deep-Dive Evidence Trail",
        expanded=False,
    ):

        if deep_dive_evidence.empty:

            st.write(
                "No Stage 2 evidence records captured."
            )

        else:

            stage_evidence_display = deep_dive_evidence[
                [
                    "claim_area",
                    "claim_type",
                    "evidence",
                    "verified",
                    "source_type",
                    "source_title",
                    "source_date",
                    "source_url",
                ]
            ].copy()


            stage_evidence_display = (
                stage_evidence_display.rename(
                    columns={
                        "claim_area": "Claim Area",
                        "claim_type": "Claim Type",
                        "evidence": "Evidence / Basis",
                        "verified": "Verified",
                        "source_type": "Source Type",
                        "source_title": "Source",
                        "source_date": "Date",
                        "source_url": "Source URL",
                    }
                )
            )


            st.dataframe(
                stage_evidence_display,
                width="stretch",
                hide_index=True,
            )


    st.caption(
        "Stage 2 conclusions are analyst judgments, not "
        "predictions that a financing transaction will occur."
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
