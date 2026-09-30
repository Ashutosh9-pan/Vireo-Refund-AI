import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import sys


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# =========================================================
# PROJECT MODULES
# =========================================================

from data_loader import (
    load_data,
    build_canonical_tickets,
)

from rag_engine import (
    ask_refund_ai,
)


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Vireo Refund AI",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# LOAD + PREPARE DATA
# =========================================================

@st.cache_data
def get_data():

    # load_data() returns a dictionary
    datasets = load_data()

    raw_tickets = datasets["tickets"]
    agents = datasets["agents"]
    customers = datasets["customers"]
    orders = datasets["orders"]
    products = datasets["products"]

    # Build one canonical record per ticket
    canonical = build_canonical_tickets(
        raw_tickets
    )

    return (
        raw_tickets,
        canonical,
        agents,
        customers,
        orders,
        products,
    )


tickets, df, agents, customers, orders, products = (
    get_data()
)


# =========================================================
# BASIC DATA CLEANING
# =========================================================

df["refund_amount_inr"] = pd.to_numeric(
    df["refund_amount_inr"],
    errors="coerce",
).fillna(0)

df["csat_score"] = pd.to_numeric(
    df["csat_score"],
    errors="coerce",
)

df["transfers"] = pd.to_numeric(
    df["transfers"],
    errors="coerce",
).fillna(0)

df["created_at"] = pd.to_datetime(
    df["created_at"],
    errors="coerce",
)

df["first_response_at"] = pd.to_datetime(
    df["first_response_at"],
    errors="coerce",
)

df["resolved_at"] = pd.to_datetime(
    df["resolved_at"],
    errors="coerce",
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("💳 Vireo Refund AI")

st.sidebar.caption(
    "Refund Intelligence & Support Analytics"
)

st.sidebar.divider()

st.sidebar.subheader("Filters")


# ---------------------------------------------------------
# CHANNEL FILTER
# ---------------------------------------------------------

channels = sorted(
    df["channel"]
    .dropna()
    .unique()
    .tolist()
)

selected_channels = st.sidebar.multiselect(
    "Channel",
    options=channels,
    default=channels,
)


# ---------------------------------------------------------
# TEAM FILTER
# ---------------------------------------------------------

teams = sorted(
    df["assigned_team"]
    .dropna()
    .unique()
    .tolist()
)

selected_teams = st.sidebar.multiselect(
    "Team",
    options=teams,
    default=teams,
)


# ---------------------------------------------------------
# STATUS FILTER
# ---------------------------------------------------------

statuses = sorted(
    df["status"]
    .dropna()
    .unique()
    .tolist()
)

selected_statuses = st.sidebar.multiselect(
    "Status",
    options=statuses,
    default=statuses,
)


# ---------------------------------------------------------
# PRIORITY FILTER
# ---------------------------------------------------------

priorities = sorted(
    df["priority"]
    .dropna()
    .unique()
    .tolist()
)

selected_priorities = st.sidebar.multiselect(
    "Priority",
    options=priorities,
    default=priorities,
)


# =========================================================
# APPLY FILTERS
# =========================================================

filtered = df[
    df["channel"].isin(selected_channels)
    & df["assigned_team"].isin(selected_teams)
    & df["status"].isin(selected_statuses)
    & df["priority"].isin(selected_priorities)
].copy()


# =========================================================
# HEADER
# =========================================================

st.title("💳 Vireo Refund AI")

st.markdown(
    """
    **Refund Intelligence Dashboard**

    Analyse refund volume, financial impact, support operations,
    agents, channels and ticket-level refund activity.
    """
)

st.divider()


# =========================================================
# KPI CALCULATIONS
# =========================================================

total_tickets = len(filtered)

refund_tickets = filtered[
    filtered["refund_amount_inr"] > 0
].copy()

refund_count = len(refund_tickets)

refund_amount = float(
    refund_tickets["refund_amount_inr"].sum()
)

avg_refund = (
    refund_amount / refund_count
    if refund_count > 0
    else 0
)

csat_values = filtered[
    "csat_score"
].dropna()

avg_csat = (
    float(csat_values.mean())
    if not csat_values.empty
    else 0
)

refund_rate = (
    refund_count / total_tickets * 100
    if total_tickets > 0
    else 0
)


# =========================================================
# KPI CARDS
# =========================================================

col1, col2, col3, col4, col5, col6 = (
    st.columns(6)
)

col1.metric(
    "Tickets",
    f"{total_tickets:,}",
)

col2.metric(
    "Refund Tickets",
    f"{refund_count:,}",
)

col3.metric(
    "Refund Amount",
    f"₹{refund_amount:,.0f}",
)

col4.metric(
    "Avg Refund",
    f"₹{avg_refund:,.0f}",
)

col5.metric(
    "Refund Rate",
    f"{refund_rate:.1f}%",
)

col6.metric(
    "Avg CSAT",
    f"{avg_csat:.2f}/5",
)


st.divider()


# =========================================================
# REFUNDS BY REASON
# =========================================================

left, right = st.columns(2)


with left:

    st.subheader("Refunds by Reason")

    if refund_tickets.empty:

        st.info(
            "No refund records for the selected filters."
        )

    else:

        reason_data = (
            refund_tickets
            .groupby(
                "refund_reason_code",
                dropna=False,
            )
            .agg(
                refund_tickets=(
                    "ticket_id",
                    "count",
                ),
                refund_amount=(
                    "refund_amount_inr",
                    "sum",
                ),
            )
            .reset_index()
        )

        reason_data[
            "refund_reason_code"
        ] = (
            reason_data[
                "refund_reason_code"
            ].fillna("Unknown")
        )

        reason_data = reason_data.sort_values(
            "refund_amount",
            ascending=False,
        )

        fig_reason = px.bar(
            reason_data,
            x="refund_amount",
            y="refund_reason_code",
            orientation="h",
            labels={
                "refund_amount": "Refund Amount (₹)",
                "refund_reason_code": "Reason Code",
            },
        )

        fig_reason.update_layout(
            height=420,
            margin=dict(
                l=10,
                r=30,
                t=30,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_reason,
            use_container_width=True,
        )


# =========================================================
# REFUNDS BY CHANNEL
# =========================================================

with right:

    st.subheader("Refunds by Channel")

    if refund_tickets.empty:

        st.info(
            "No refund records for the selected filters."
        )

    else:

        channel_data = (
            refund_tickets
            .groupby("channel")
            .agg(
                refund_tickets=(
                    "ticket_id",
                    "count",
                ),
                refund_amount=(
                    "refund_amount_inr",
                    "sum",
                ),
            )
            .reset_index()
        )

        fig_channel = px.bar(
            channel_data,
            x="channel",
            y="refund_amount",
            labels={
                "channel": "Channel",
                "refund_amount": "Refund Amount (₹)",
            },
        )

        fig_channel.update_layout(
            height=420,
            margin=dict(
                l=10,
                r=30,
                t=30,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_channel,
            use_container_width=True,
        )


# =========================================================
# MONTHLY REFUND TREND
# =========================================================

left, right = st.columns(2)


with left:

    st.subheader("Monthly Refund Trend")

    if refund_tickets.empty:

        st.info(
            "No refund records for the selected filters."
        )

    else:

        trend = (
            refund_tickets
            .dropna(
                subset=["created_at"]
            )
            .assign(
                month=lambda x:
                    x["created_at"]
                    .dt.to_period("M")
                    .astype(str)
            )
            .groupby("month")
            .agg(
                refund_amount=(
                    "refund_amount_inr",
                    "sum",
                ),
                refund_tickets=(
                    "ticket_id",
                    "count",
                ),
            )
            .reset_index()
        )

        fig_trend = px.line(
            trend,
            x="month",
            y="refund_amount",
            markers=True,
            labels={
                "month": "Month",
                "refund_amount": "Refund Amount (₹)",
            },
        )

        fig_trend.update_layout(
            height=420,
            margin=dict(
                l=10,
                r=30,
                t=30,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_trend,
            use_container_width=True,
        )


# =========================================================
# REFUNDS BY TEAM
# =========================================================

with right:

    st.subheader("Refunds by Team")

    if refund_tickets.empty:

        st.info(
            "No refund records for the selected filters."
        )

    else:

        team_data = (
            refund_tickets
            .groupby("assigned_team")
            .agg(
                refund_tickets=(
                    "ticket_id",
                    "count",
                ),
                refund_amount=(
                    "refund_amount_inr",
                    "sum",
                ),
            )
            .reset_index()
            .sort_values(
                "refund_amount",
                ascending=False,
            )
        )

        fig_team = px.bar(
            team_data,
            x="assigned_team",
            y="refund_amount",
            labels={
                "assigned_team": "Team",
                "refund_amount": "Refund Amount (₹)",
            },
        )

        fig_team.update_layout(
            height=420,
            margin=dict(
                l=10,
                r=30,
                t=30,
                b=10,
            ),
        )

        st.plotly_chart(
            fig_team,
            use_container_width=True,
        )


# =========================================================
# AGENT REFUND ANALYSIS
# =========================================================

st.divider()

st.subheader("👤 Agent Refund Analysis")

if refund_tickets.empty:

    st.info(
        "No refund records for the selected filters."
    )

else:

    agent_data = (
        refund_tickets
        .groupby("agent_id")
        .agg(
            refund_tickets=(
                "ticket_id",
                "count",
            ),
            refund_amount=(
                "refund_amount_inr",
                "sum",
            ),
            avg_csat=(
                "csat_score",
                "mean",
            ),
            avg_transfers=(
                "transfers",
                "mean",
            ),
        )
        .reset_index()
    )

    agent_data = agent_data.merge(
        agents[
            [
                "agent_id",
                "name",
                "team",
                "site",
            ]
        ],
        on="agent_id",
        how="left",
    )

    agent_data = agent_data[
        [
            "agent_id",
            "name",
            "team",
            "site",
            "refund_tickets",
            "refund_amount",
            "avg_csat",
            "avg_transfers",
        ]
    ].sort_values(
        "refund_amount",
        ascending=False,
    )

    agent_data[
        "refund_amount"
    ] = (
        agent_data[
            "refund_amount"
        ].round(2)
    )

    agent_data[
        "avg_csat"
    ] = (
        agent_data[
            "avg_csat"
        ].round(2)
    )

    agent_data[
        "avg_transfers"
    ] = (
        agent_data[
            "avg_transfers"
        ].round(2)
    )

    st.dataframe(
        agent_data.head(20),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# DATA RECONCILIATION
# =========================================================

st.divider()

st.subheader("🔍 Data Reconciliation")

raw_ticket_rows = len(tickets)

unique_ticket_ids = (
    tickets["ticket_id"].nunique()
)

duplicate_export_rows = (
    raw_ticket_rows - unique_ticket_ids
)

source_counts = (
    tickets["source_system"]
    .value_counts()
    .rename_axis("source_system")
    .reset_index(
        name="rows"
    )
)

c1, c2, c3 = st.columns(3)

c1.metric(
    "Raw Ticket Rows",
    f"{raw_ticket_rows:,}",
)

c2.metric(
    "Unique Ticket IDs",
    f"{unique_ticket_ids:,}",
)

c3.metric(
    "Duplicate Export Rows",
    f"{duplicate_export_rows:,}",
)

st.caption(
    "Refund analysis uses one canonical record per "
    "ticket ID. When a migrated ticket exists in both "
    "systems, the current helpdesk record is preferred."
)

st.dataframe(
    source_counts,
    use_container_width=True,
    hide_index=True,
)


# =========================================================
# TICKET EXPLORER
# =========================================================

st.divider()

st.subheader("🔎 Refund Ticket Explorer")

search = st.text_input(
    "Search by Ticket ID, Customer ID or Order ID",
    placeholder="Example: TK-240001",
)

ticket_view = refund_tickets.copy()


if search.strip():

    search_value = search.strip()

    mask = (
        ticket_view["ticket_id"]
        .astype(str)
        .str.contains(
            search_value,
            case=False,
            na=False,
            regex=False,
        )
        |
        ticket_view["customer_id"]
        .astype(str)
        .str.contains(
            search_value,
            case=False,
            na=False,
            regex=False,
        )
        |
        ticket_view["order_id"]
        .astype(str)
        .str.contains(
            search_value,
            case=False,
            na=False,
            regex=False,
        )
    )

    ticket_view = (
        ticket_view[mask]
    )


display_columns = [
    "ticket_id",
    "created_at",
    "status",
    "channel",
    "customer_id",
    "order_id",
    "product_sku",
    "category",
    "priority",
    "assigned_team",
    "agent_id",
    "refund_amount_inr",
    "refund_reason_code",
    "replacement_issued",
]


if search.strip() and ticket_view.empty:

    st.info(
        f"No refund ticket found for "
        f"`{search.strip()}`."
    )

else:

    st.dataframe(
        ticket_view[
            display_columns
        ]
        .sort_values(
            "refund_amount_inr",
            ascending=False,
        )
        .head(100),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# BUSINESS SNAPSHOT
# =========================================================

st.divider()

st.subheader("📌 Business Snapshot")

if refund_tickets.empty:

    st.info(
        "No refund records match the selected filters."
    )

else:

    reason_summary = (
        refund_tickets
        .groupby(
            "refund_reason_code"
        )["refund_amount_inr"]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    if not reason_summary.empty:

        top_reason = (
            reason_summary.index[0]
        )

        top_reason_amount = float(
            reason_summary.iloc[0]
        )

        share = (
            top_reason_amount
            / refund_amount
            * 100
            if refund_amount > 0
            else 0
        )

        st.write(
            f"**Largest refund reason:** "
            f"`{top_reason}` — "
            f"₹{top_reason_amount:,.0f} "
            f"({share:.1f}% of refund value)."
        )

    monthly_summary = (
        refund_tickets
        .dropna(
            subset=["created_at"]
        )
        .assign(
            month=lambda x:
                x["created_at"]
                .dt.to_period("M")
                .astype(str)
        )
        .groupby("month")[
            "refund_amount_inr"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    if not monthly_summary.empty:

        peak_month = (
            monthly_summary.index[0]
        )

        peak_amount = float(
            monthly_summary.iloc[0]
        )

        st.write(
            f"**Highest monthly refund value:** "
            f"{peak_month} — "
            f"₹{peak_amount:,.0f}."
        )


# =========================================================
# 🤖 ASK VIREO - AI ASSISTANT
# =========================================================

st.divider()

st.subheader("🤖 Ask Vireo")

st.markdown(
    """
    Ask Vireo questions about refund operations,
    refund reasons, support processes and the available
    Vireo knowledge base.
    """
)

ai_question = st.text_area(
    "Ask a question",
    placeholder=(
        "Example: What refund information is "
        "available in the knowledge base?"
    ),
    height=110,
)

ask_button = st.button(
    "✨ Ask Vireo",
    type="primary",
)


if ask_button:

    if not ai_question.strip():

        st.warning(
            "Please enter a question first."
        )

    else:

        with st.spinner(
            "Vireo AI is analysing the knowledge base..."
        ):

            try:

                answer = ask_refund_ai(
                    ai_question.strip()
                )

                st.markdown(
                    "### 💡 Vireo AI Response"
                )

                st.markdown(
                    answer
                )

            except Exception as error:

                st.error(
                    f"Unable to generate AI response: {error}"
                )


# =========================================================
# DATASET SUMMARY
# =========================================================

with st.expander(
    "📊 Dataset Summary"
):

    c1, c2, c3, c4, c5 = (
        st.columns(5)
    )

    c1.metric(
        "Raw Ticket Rows",
        f"{len(tickets):,}",
    )

    c2.metric(
        "Canonical Tickets",
        f"{df['ticket_id'].nunique():,}",
    )

    c3.metric(
        "Agents",
        f"{len(agents):,}",
    )

    c4.metric(
        "Customers",
        f"{len(customers):,}",
    )

    c5.metric(
        "Orders",
        f"{len(orders):,}",
    )

    st.write(
        f"Products in catalog: "
        f"**{len(products):,}**"
    )


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Vireo Refund AI • Refund Intelligence Dashboard • "
    "Python • Pandas • Plotly • Streamlit • Gemini"
)