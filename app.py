from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Factory Dashboard", layout="wide")
BASE = Path(__file__).parent

STATUS_COLOR = {
    "Running": "#22c55e",
    "Idle": "#f59e0b",
    "Down": "#ef4444",
    "Maintenance": "#94a3b8",
    "Planned": "#94a3b8",
}
LINE_COLOR = {
    "Line 1": "#3b82f6",
    "Line 2": "#22c55e",
    "Line 3": "#a855f7",
    "Shared": "#f59e0b",
}

@st.cache_data
def load_data():
    return pd.read_csv(BASE / "machines.csv"), pd.read_csv(BASE / "jobs.csv")

machines, jobs = load_data()

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; max-width: 1560px;}
    div[data-testid="stMetric"] {border: 1px solid #262b36; border-radius: 16px; padding: 14px; background: #10141c;}
    div[data-testid="stMetricLabel"] {font-size: .82rem; color: #9ca3af;}
    div[data-testid="stMetricValue"] {font-size: 1.35rem;}
    .small-note {font-size: .78rem; color: #94a3b8;}
    </style>
    """,
    unsafe_allow_html=True,
)


def donut(value, label, color="#22c55e", suffix="%", max_value=100):
    value = float(value)
    pct = max(0, min(value / max_value * 100, 100))
    fig = go.Figure(go.Pie(
        values=[pct, 100 - pct],
        hole=0.76,
        sort=False,
        direction="clockwise",
        marker=dict(colors=[color, "#263040"]),
        textinfo="none",
        hoverinfo="skip",
    ))
    fig.add_annotation(
        text=f"<b>{value:g}{suffix}</b><br><span style='font-size:10px'>{label}</span>",
        x=0.5, y=0.5, showarrow=False, font=dict(color="#f8fafc", size=12)
    )
    fig.update_layout(height=120, margin=dict(l=0, r=0, t=0, b=0), showlegend=False, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def metric_card(title, value, note, circle_value=None, color="#22c55e", suffix="%", max_value=100):
    with st.container(border=True):
        left, right = st.columns([1.4, 1])
        left.caption(title)
        left.subheader(value)
        left.markdown(f"<div class='small-note'>{note}</div>", unsafe_allow_html=True)
        if circle_value is not None:
            right.plotly_chart(donut(circle_value, "", color=color, suffix=suffix, max_value=max_value), use_container_width=True, config={"displayModeBar": False})


def factory_layout(df):
    fig = go.Figure()

    # Building walls and support/output zones
    fig.add_shape(type="rect", x0=0, y0=0, x1=12, y1=9, line=dict(color="#64748b", width=3), fillcolor="#0b0f16")
    zones = [
        (0.3, 7.2, 1.3, 1.1, "Raw\nMaterial", "#132338"),
        (0.3, 5.7, 1.3, 1.1, "Coil +\nSheets", "#132338"),
        (0.3, 4.2, 1.3, 1.1, "Tools", "#132338"),
        (10.6, 7.2, 1.1, 1.1, "Finished\nGoods + QA", "#12331f"),
        (10.6, 5.7, 1.1, 1.1, "Scrap /\nResale", "#36340d"),
        (1.9, 1.0, 8.2, 0.8, "Assembly / WIP staging lane", "#111827"),
    ]
    for x, y, w, h, txt, fill in zones:
        fig.add_shape(type="rect", x0=x, y0=y, x1=x+w, y1=y+h, line=dict(color="#334155", width=1), fillcolor=fill)
        fig.add_annotation(x=x+w/2, y=y+h/2, text=txt, showarrow=False, font=dict(size=11, color="#e5e7eb"))

    # Flow arrows
    arrows = [(1.7, 7.7, 1.95, 7.3), (3.7, 7.3, 4.15, 7.3), (6.1, 6.4, 6.4, 6.0), (10.2, 6.4, 10.55, 7.7)]
    for x0, y0, x1, y1 in arrows:
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=3, arrowsize=1.1, arrowwidth=1.5, arrowcolor="#64748b")

    # Machine boxes
    for _, r in df.iterrows():
        color = STATUS_COLOR.get(r.status, "#94a3b8")
        line_color = LINE_COLOR.get(r.line, "#64748b")
        fig.add_shape(
            type="rect", x0=r.x, y0=r.y, x1=r.x+r.w, y1=r.y+r.h,
            line=dict(color=line_color, width=2), fillcolor="#10141c", opacity=1
        )
        fig.add_trace(go.Scatter(
            x=[r.x + .18], y=[r.y + r.h - .18], mode="markers",
            marker=dict(size=11, color=color), hoverinfo="skip", showlegend=False
        ))
        label = f"<b>{int(r.id)}. {r.machine}</b><br>{r.utilization}% util | {r.wip_hours}h WIP<br>{r.current_job}"
        fig.add_annotation(x=r.x+r.w/2, y=r.y+r.h/2+.05, text=label, showarrow=False, align="center", font=dict(size=10, color="#f8fafc"))
        fig.add_annotation(x=r.x+r.w/2, y=r.y+.12, text=f"Updated {r.last_updated}", showarrow=False, font=dict(size=9, color="#94a3b8"))

    fig.add_annotation(x=6, y=8.75, text="Factory floor mock layout", showarrow=False, font=dict(size=14, color="#f8fafc"))
    fig.update_xaxes(visible=False, range=[0, 12])
    fig.update_yaxes(visible=False, range=[0, 9], scaleanchor="x", scaleratio=1)
    fig.update_layout(height=650, margin=dict(l=10, r=10, t=10, b=10), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
    return fig


active_jobs = len(jobs[jobs.status == "WIP"])
completed_today = len(jobs[jobs.status == "Complete"])
overall_util = round(machines[machines.status != "Planned"].utilization.mean())
wip_hours = round(machines.wip_hours.sum(), 1)
bottleneck = machines.sort_values("utilization", ascending=False).iloc[0]
throughput = completed_today

st.title("Factory Dashboard")
st.caption("Minimal mock live dashboard for duct manufacturing")

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1: metric_card("Utilization", f"{overall_util}%", "Average active load", overall_util)
with k2: metric_card("WIP hours", f"{wip_hours}h", "Estimated work", wip_hours, "#64748b", "h", 20)
with k3: metric_card("Active jobs", str(active_jobs), "Open production jobs")
with k4: metric_card("Completed", str(completed_today), "Finished today")
with k5: metric_card("Throughput", str(throughput), "Jobs/day mock")
with k6: metric_card("Bottleneck", bottleneck.machine[:18] + "...", f"{bottleneck.utilization}% utilization")

st.subheader("Factory floor live layout")
st.plotly_chart(factory_layout(machines), use_container_width=True, config={"displayModeBar": False})

left, right = st.columns([0.9, 1.1])
with left:
    st.subheader("Machine details")
    choices = machines.apply(lambda r: f"{int(r.id)} · {r.machine}", axis=1).tolist()
    selected = st.selectbox("Select machine", choices, label_visibility="collapsed")
    mid = int(selected.split(" · ")[0])
    m = machines[machines.id == mid].iloc[0]
    c1, c2 = st.columns(2)
    c1.plotly_chart(donut(m.utilization, "Utilization", STATUS_COLOR.get(m.status, "#94a3b8")), use_container_width=True, config={"displayModeBar": False})
    c2.plotly_chart(donut(m.wip_hours, "WIP", "#64748b", "h", 4), use_container_width=True, config={"displayModeBar": False})
    st.write(f"**Status:** {m.status}")
    st.write(f"**Current job:** {m.current_job}")
    st.write(f"**Operator:** {m.operator}")
    st.write(f"**Started:** {m.started_at}")
    st.write(f"**Last updated:** {m.last_updated}")
    st.write(f"**Expected finish:** {m.expected_finish}")

with right:
    st.subheader("Production lists")
    tab1, tab2 = st.tabs(["WIP", "Completed"])
    with tab1:
        st.dataframe(jobs[jobs.status == "WIP"][["job_id", "product", "line", "current_stage", "progress", "started_at", "last_updated", "due"]], use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(jobs[jobs.status == "Complete"][["job_id", "product", "line", "completed_at"]], use_container_width=True, hide_index=True)

st.subheader("Operator phone input mock")
with st.form("operator_update", border=True):
    a, b, c, d = st.columns([1, 1, 1, 1])
    job = a.selectbox("Job", jobs[jobs.status == "WIP"].job_id)
    machine = b.selectbox("Machine", machines.machine)
    action = c.selectbox("Action", ["Start", "Pause", "Resume", "Complete stage", "Send to QA"])
    note = d.text_input("Note", placeholder="optional")
    submitted = st.form_submit_button("Submit mock update")
    if submitted:
        st.success(f"Mock saved: {job} · {machine} · {action}. Later this can write to PostgreSQL/Firebase/Supabase.")
