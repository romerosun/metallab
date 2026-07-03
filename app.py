from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Factory Dashboard", layout="wide")
BASE = Path(__file__).parent
machines = pd.read_csv(BASE / "machines.csv")
jobs = pd.read_csv(BASE / "jobs.csv")

STATUS_COLOR = {
    "Running": "#22c55e",
    "Idle": "#f59e0b",
    "Down": "#ef4444",
    "Maintenance": "#94a3b8",
    "Planned": "#94a3b8",
}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; max-width: 1500px;}
    div[data-testid="stMetric"] {border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px; background: white;}
    div[data-testid="stMetricLabel"] {font-size: 0.82rem; color: #64748b;}
    div[data-testid="stMetricValue"] {font-size: 1.45rem;}
    .small {font-size: 0.78rem; color: #64748b;}
    .machine-title {font-weight: 700; font-size: 0.88rem; line-height: 1.2;}
    .status-dot {height: 9px; width: 9px; border-radius: 50%; display: inline-block; margin-right: 6px;}
    .zone-title {font-weight: 800; font-size: .88rem; margin: .2rem 0 .6rem 0;}
    </style>
    """,
    unsafe_allow_html=True,
)


def donut(value: float, label: str, color: str):
    value = max(0, min(float(value), 100))
    fig = go.Figure(
        go.Pie(
            values=[value, 100 - value],
            hole=0.72,
            sort=False,
            direction="clockwise",
            marker=dict(colors=[color, "#e5e7eb"]),
            textinfo="none",
            hoverinfo="skip",
        )
    )
    fig.add_annotation(text=f"<b>{value:.0f}%</b><br><span style='font-size:10px'>{label}</span>", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=105, showlegend=False)
    return fig


def hours_donut(hours: float):
    pct = max(0, min(float(hours) / 4 * 100, 100))
    fig = go.Figure(
        go.Pie(
            values=[pct, 100 - pct],
            hole=0.72,
            sort=False,
            direction="clockwise",
            marker=dict(colors=["#64748b", "#e5e7eb"]),
            textinfo="none",
            hoverinfo="skip",
        )
    )
    fig.add_annotation(text=f"<b>{hours:.1f}h</b><br><span style='font-size:10px'>WIP</span>", x=0.5, y=0.5, showarrow=False)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=105, showlegend=False)
    return fig


def machine_card(row):
    color = STATUS_COLOR.get(row.status, "#94a3b8")
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"<div class='machine-title'>{int(row.id)}. {row.machine}</div>", unsafe_allow_html=True)
        c2.markdown(f"<span class='status-dot' style='background:{color}'></span>", unsafe_allow_html=True)
        g1, g2 = st.columns(2)
        g1.plotly_chart(donut(row.utilization, "Util", color), use_container_width=True, config={"displayModeBar": False})
        g2.plotly_chart(hours_donut(row.wip_hours), use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f"<div class='small'>Started: {row.started_at}<br>Updated: {row.last_updated}<br>Job: <b>{row.current_job}</b><br>Status: {row.status}</div>",
            unsafe_allow_html=True,
        )


def zone(title, area, ncols=2):
    with st.container(border=True):
        st.markdown(f"<div class='zone-title'>{title}</div>", unsafe_allow_html=True)
        subset = machines[machines.area == area].reset_index(drop=True)
        rows = [subset.iloc[i : i + ncols] for i in range(0, len(subset), ncols)]
        for chunk in rows:
            cols = st.columns(ncols)
            for col, (_, row) in zip(cols, chunk.iterrows()):
                with col:
                    machine_card(row)


active_jobs = len(jobs[jobs.status == "WIP"])
completed_today = len(jobs[jobs.status == "Complete"])
overall_util = round(machines[machines.status != "Planned"].utilization.mean())
wip_hours = round(machines.wip_hours.sum(), 1)
bottleneck = machines.sort_values("utilization", ascending=False).iloc[0]

st.title("Factory Dashboard")
st.caption("Mock live dashboard for duct manufacturing")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Overall utilization", f"{overall_util}%", "Average active load")
k2.metric("Active jobs", active_jobs, "Open jobs")
k3.metric("WIP hours", f"{wip_hours}h", "Estimated work")
k4.metric("Completed today", completed_today, "Sent to QA")
k5.metric("Bottleneck", bottleneck.machine, f"{bottleneck.utilization}% utilization")

st.subheader("Factory floor live layout")

with st.container(border=True):
    left, center, right = st.columns([0.7, 4.5, 0.8])
    with left:
        st.markdown("**Support**")
        st.info("Raw material storage")
        st.info("Coil + sheet storage")
        st.info("Maintenance tools")
    with center:
        z1, z2, z3 = st.columns([1.25, 1, 1])
        with z1:
            zone("LINE 1 · RECTANGULAR DUCTS", "line1", 2)
        with z2:
            zone("LINE 2 · ROUND / SPIRAL", "line2", 1)
        with z3:
            zone("LINE 3 · CUSTOM / WELDED", "line3", 1)
        zone("SHARED RESOURCES · ALL LINES", "shared", 3)
    with right:
        st.markdown("**Output**")
        st.success("Finished goods + QA")
        st.warning("Scrap / resale material")

st.subheader("Production lists")
wip, complete = st.columns(2)
with wip:
    st.markdown("**Work in progress**")
    st.dataframe(
        jobs[jobs.status == "WIP"][["job_id", "product", "line", "current_stage", "progress", "started_at", "last_updated", "due"]],
        use_container_width=True,
        hide_index=True,
    )
with complete:
    st.markdown("**Completed today**")
    st.dataframe(
        jobs[jobs.status == "Complete"][["job_id", "product", "line", "completed_at"]],
        use_container_width=True,
        hide_index=True,
    )

with st.expander("Operator update mock"):
    with st.form("operator_update"):
        job = st.selectbox("Job", jobs[jobs.status == "WIP"].job_id)
        stage = st.selectbox("New stage", ["Cutting", "Forming", "Beading", "Seaming", "Welding", "Assembly", "QA", "Complete"])
        submitted = st.form_submit_button("Mark update")
        if submitted:
            st.success(f"Mock update: {job} → {stage}. Future version can save this to a database.")
