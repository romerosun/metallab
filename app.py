from pathlib import Path
import html
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Factory Dashboard", layout="wide", initial_sidebar_state="collapsed")
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
LINE_COLOR = {"Line 1": "#3b82f6", "Line 2": "#22c55e", "Line 3": "#a855f7", "Shared": "#f59e0b"}

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1900px;}
#MainMenu, footer, header {visibility: hidden;}
h1 {font-size: 2.15rem; margin-bottom: .1rem;}
.kpi-row {display:grid; grid-template-columns: repeat(5, minmax(190px, 1fr)); gap:18px; margin: 24px 0 30px 0;}
.kpi {background:#10141c; border:1px solid #2a3140; border-radius:18px; padding:22px 24px; min-height:126px;}
.kpi-label {color:#a8b3c7; font-size:.9rem; margin-bottom:10px;}
.kpi-value {font-size:2rem; font-weight:800; color:#f8fafc; line-height:1;}
.kpi-note {color:#8fb4e8; font-size:.86rem; margin-top:16px;}
.clean-card {background:#10141c; border:1px solid #2a3140; border-radius:18px; padding:18px;}
</style>
""", unsafe_allow_html=True)

active_jobs = len(jobs[jobs.status == "WIP"])
completed_today = len(jobs[jobs.status == "Complete"])
overall_util = round(machines[machines.status != "Planned"].utilization.mean())
wip_hours = round(machines.wip_hours.sum(), 1)
bottleneck = machines.sort_values("utilization", ascending=False).iloc[0]

st.title("Factory Dashboard")
st.caption("Mock live dashboard for duct manufacturing")

st.markdown(f"""
<div class="kpi-row">
  <div class="kpi"><div class="kpi-label">Overall utilization</div><div class="kpi-value">{overall_util}%</div><div class="kpi-note">Average active load</div></div>
  <div class="kpi"><div class="kpi-label">Active jobs</div><div class="kpi-value">{active_jobs}</div><div class="kpi-note">Open production jobs</div></div>
  <div class="kpi"><div class="kpi-label">WIP hours</div><div class="kpi-value">{wip_hours}h</div><div class="kpi-note">Estimated work in progress</div></div>
  <div class="kpi"><div class="kpi-label">Completed today</div><div class="kpi-value">{completed_today}</div><div class="kpi-note">Finished today</div></div>
  <div class="kpi"><div class="kpi-label">Bottleneck</div><div class="kpi-value" style="font-size:1.55rem">{html.escape(bottleneck.machine)}</div><div class="kpi-note">{int(bottleneck.utilization)}% utilization</div></div>
</div>
""", unsafe_allow_html=True)


def machine_card(r):
    status_color = STATUS_COLOR.get(str(r.status), "#94a3b8")
    line_color = LINE_COLOR.get(str(r.line), "#64748b")
    util = int(r.utilization)
    wip_pct = min(float(r.wip_hours) / 4 * 100, 100)
    name = html.escape(str(r.machine))
    current_job = html.escape(str(r.current_job))
    status = html.escape(str(r.status))
    return f"""
    <div class="machine" style="--line:{line_color};--status:{status_color};">
      <div class="m-top">
        <div class="m-name">{int(r.id)}. {name}</div>
        <span class="dot"></span>
      </div>
      <div class="rings">
        <div class="ring" style="--p:{util};--c:{status_color};"><div><b>{util}%</b><small>Util</small></div></div>
        <div class="ring" style="--p:{wip_pct};--c:#8aa0bd;"><div><b>{r.wip_hours}h</b><small>WIP</small></div></div>
      </div>
      <div class="meta">
        <div><span>Job</span>{current_job}</div>
        <div><span>Started</span>{html.escape(str(r.started_at))}</div>
        <div><span>Updated</span>{html.escape(str(r.last_updated))}</div>
        <div><span>Status</span>{status}</div>
      </div>
    </div>
    """


def cards_for(line):
    rows = machines[machines.line == line].sort_values("id")
    return "".join(machine_card(r) for _, r in rows.iterrows())

layout_html = f"""
<!doctype html>
<html>
<head>
<style>
* {{ box-sizing:border-box; }}
body {{ margin:0; background:#0b0f16; color:#f8fafc; font-family:Inter, Segoe UI, Arial, sans-serif; }}
.floor {{ width:100%; min-height:1160px; border:2px solid #334155; border-radius:22px; background:#0d121a; padding:34px 34px 28px; overflow:visible; }}
.floor-title {{ text-align:center; font-weight:800; color:#dbeafe; font-size:18px; margin-bottom:36px; }}
.main-grid {{ display:grid; grid-template-columns: 180px 1.35fr 1.35fr 1.15fr 180px; gap:34px; align-items:start; }}
.support, .output {{ display:grid; gap:26px; padding-top:8px; }}
.zone-box {{ border-radius:14px; padding:30px 18px; border:1px solid #334155; background:#132338; color:#60a5fa; font-weight:800; text-align:center; font-size:16px; line-height:1.35; min-height:100px; display:grid; place-items:center; }}
.output .zone-box:first-child {{ background:#12331f; color:#4ade80; }}
.output .zone-box:nth-child(2) {{ background:#36340d; color:#fde68a; }}
.line {{ border:1.5px solid #334155; border-radius:18px; padding:26px 26px 28px; min-height:640px; background:rgba(2,6,23,.14); }}
.line h3 {{ margin:0 0 22px; font-size:17px; letter-spacing:.02em; white-space:nowrap; }}
.l1 h3 {{ color:#60a5fa; }} .l2 h3 {{ color:#4ade80; }} .l3 h3 {{ color:#c084fc; }}
.line-grid {{ display:grid; grid-template-columns:repeat(2, minmax(220px, 1fr)); gap:28px; }}
.l3 .line-grid {{ grid-template-columns:1fr; }}
.machine {{ background:#10141c; border:1.5px solid #2e3746; border-left:4px solid var(--line); border-radius:15px; min-height:245px; padding:20px; }}
.m-top {{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; margin-bottom:18px; }}
.m-name {{ font-weight:850; line-height:1.18; font-size:16px; max-width:210px; }}
.dot {{ width:12px; height:12px; border-radius:50%; display:block; flex:0 0 auto; background:var(--status); box-shadow:0 0 0 5px rgba(255,255,255,.04); }}
.rings {{ display:flex; gap:28px; align-items:center; margin:10px 0 20px; }}
.ring {{ width:88px; height:88px; border-radius:50%; background:conic-gradient(var(--c) calc(var(--p)*1%), #e8edf5 0); position:relative; display:grid; place-items:center; }}
.ring:after {{ content:""; position:absolute; inset:16px; background:#0b0f16; border-radius:50%; }}
.ring div {{ position:relative; z-index:1; text-align:center; }}
.ring b {{ display:block; font-size:15px; }}
.ring small {{ display:block; color:#dbeafe; font-size:10px; margin-top:2px; }}
.meta {{ display:grid; grid-template-columns:1fr 1fr; column-gap:20px; row-gap:9px; color:#dbeafe; font-size:13px; }}
.meta span {{ display:block; color:#7892b8; font-size:11px; }}
.flow-row {{ display:grid; grid-template-columns: 180px 1fr 180px; gap:34px; margin:34px 0; align-items:center; }}
.wip-lane {{ height:100px; border:1px solid #334155; border-radius:16px; background:#111827; display:grid; place-items:center; color:#93c5fd; font-weight:800; font-size:17px; }}
.shared {{ border:1.5px dashed #f59e0b; border-radius:18px; padding:28px; background:rgba(245,158,11,.04); margin:0 214px; }}
.shared h3 {{ margin:0 0 22px; color:#fbbf24; font-size:17px; }}
.shared-grid {{ display:grid; grid-template-columns:repeat(3, minmax(230px, 1fr)); gap:28px; }}
.legend {{ margin-top:28px; display:flex; gap:26px; color:#cbd5e1; font-size:13px; }}
.legend span:before {{ content:""; display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:7px; background:var(--c); }}
@media(max-width:1500px) {{
  .floor {{ min-width:1600px; }}
}}
</style>
</head>
<body>
<div class="floor">
  <div class="floor-title">Factory floor live layout</div>
  <div class="main-grid">
    <div class="support">
      <div class="zone-box">Raw material<br>storage</div>
      <div class="zone-box">Coil + sheet<br>storage</div>
      <div class="zone-box">Maintenance<br>tools</div>
    </div>
    <section class="line l1"><h3>LINE 1 · RECTANGULAR DUCTS</h3><div class="line-grid">{cards_for('Line 1')}</div></section>
    <section class="line l2"><h3>LINE 2 · ROUND / SPIRAL</h3><div class="line-grid">{cards_for('Line 2')}</div></section>
    <section class="line l3"><h3>LINE 3 · CUSTOM / WELDED</h3><div class="line-grid">{cards_for('Line 3')}</div></section>
    <div class="output">
      <div class="zone-box">Finished goods<br>+ QA</div>
      <div class="zone-box">Scrap / resale<br>material</div>
    </div>
  </div>

  <div class="flow-row">
    <div></div>
    <div class="wip-lane">Assembly / WIP staging lane</div>
    <div></div>
  </div>

  <section class="shared">
    <h3>SHARED RESOURCES</h3>
    <div class="shared-grid">{cards_for('Shared')}</div>
  </section>

  <div class="legend">
    <span style="--c:#22c55e">Running</span><span style="--c:#f59e0b">Idle</span><span style="--c:#ef4444">Down</span><span style="--c:#94a3b8">Planned</span>
  </div>
</div>
</body>
</html>
"""

st.subheader("Factory floor live layout")
components.html(layout_html, height=1220, scrolling=True)

left, right = st.columns([1, 1.35])
with left:
    st.subheader("Machine detail")
    selected = st.selectbox("Machine", machines.apply(lambda r: f"{int(r.id)} · {r.machine}", axis=1))
    m = machines[machines.id == int(selected.split(" · ")[0])].iloc[0]
    st.markdown(f"""
    <div class="clean-card">
      <h3 style="margin-top:0">{html.escape(m.machine)}</h3>
      <p><b>Status:</b> {html.escape(m.status)}</p>
      <p><b>Current job:</b> {html.escape(str(m.current_job))}</p>
      <p><b>Operator:</b> {html.escape(str(m.operator))}</p>
      <p><b>Started:</b> {html.escape(str(m.started_at))}</p>
      <p><b>Last updated:</b> {html.escape(str(m.last_updated))}</p>
      <p><b>Expected finish:</b> {html.escape(str(m.expected_finish))}</p>
    </div>
    """, unsafe_allow_html=True)

with right:
    st.subheader("Production lists")
    tab1, tab2 = st.tabs(["WIP", "Completed"])
    with tab1:
        st.dataframe(jobs[jobs.status == "WIP"][["job_id", "product", "line", "current_stage", "progress", "started_at", "last_updated", "due"]], use_container_width=True, hide_index=True)
    with tab2:
        st.dataframe(jobs[jobs.status == "Complete"][["job_id", "product", "line", "completed_at"]], use_container_width=True, hide_index=True)

st.subheader("Operator phone input mock")
with st.form("operator_update", border=True):
    a, b, c, d = st.columns([1, 1, 1, 1.2])
    job = a.selectbox("Job", jobs[jobs.status == "WIP"].job_id)
    machine = b.selectbox("Machine", machines.machine)
    action = c.selectbox("Action", ["Start", "Pause", "Resume", "Complete stage", "Send to QA"])
    note = d.text_input("Note", placeholder="optional")
    if st.form_submit_button("Submit mock update"):
        st.success(f"Mock saved: {job} · {machine} · {action}")
