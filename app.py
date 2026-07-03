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
.block-container {padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1760px;}
#MainMenu, footer, header {visibility: hidden;}
h1 {font-size: 2.2rem; margin-bottom: .2rem;}
.kpi-row {display:grid; grid-template-columns: repeat(5, minmax(180px, 1fr)); gap:18px; margin: 24px 0 30px 0;}
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
  <div class="kpi"><div class="kpi-label">Completed today</div><div class="kpi-value">{completed_today}</div><div class="kpi-note">Finished and sent to QA</div></div>
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
    <div class="machine" style="border-color:{line_color}">
      <div class="m-top"><div class="m-name">{int(r.id)}. {name}</div><span class="dot" style="background:{status_color}"></span></div>
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
body {{ margin:0; background:#0b0f16; color:#f8fafc; font-family:Inter, Segoe UI, Arial, sans-serif; }}
.wrap {{ width:100%; box-sizing:border-box; padding:0; }}
.floor {{
  position:relative; width:100%; min-height:920px; box-sizing:border-box;
  border:2px solid #334155; border-radius:20px; background:#0d121a; overflow:hidden;
}}
.floor-title {{ position:absolute; top:18px; left:0; right:0; text-align:center; font-weight:800; color:#dbeafe; font-size:18px; }}
.support {{ position:absolute; left:26px; top:90px; width:170px; display:grid; gap:22px; }}
.output {{ position:absolute; right:26px; top:110px; width:190px; display:grid; gap:22px; }}
.zone-box {{ border-radius:14px; padding:28px 18px; border:1px solid #334155; background:#132338; color:#60a5fa; font-weight:700; text-align:center; font-size:17px; line-height:1.35; }}
.output .zone-box:first-child {{ background:#12331f; color:#4ade80; }}
.output .zone-box:nth-child(2) {{ background:#36340d; color:#fde68a; }}
.line {{ position:absolute; border:1.5px solid #334155; border-radius:18px; padding:56px 22px 22px 22px; box-sizing:border-box; }}
.line h3 {{ position:absolute; top:18px; left:22px; margin:0; font-size:17px; letter-spacing:.02em; }}
.line1 {{ left:225px; top:88px; width:500px; min-height:535px; }}
.line2 {{ left:755px; top:88px; width:500px; min-height:535px; }}
.line3 {{ left:1285px; top:88px; width:390px; min-height:680px; }}
.l1 h3 {{ color:#60a5fa; }} .l2 h3 {{ color:#4ade80; }} .l3 h3 {{ color:#c084fc; }}
.grid {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; }}
.line3 .grid {{ grid-template-columns:1fr; }}
.machine {{ background:#10141c; border:2px solid; border-radius:14px; min-height:205px; padding:18px; box-sizing:border-box; }}
.m-top {{ display:flex; justify-content:space-between; gap:10px; align-items:flex-start; margin-bottom:14px; }}
.m-name {{ font-weight:800; line-height:1.18; font-size:15.5px; max-width:190px; }}
.dot {{ width:12px; height:12px; border-radius:50%; display:block; flex:0 0 auto; box-shadow:0 0 0 4px rgba(255,255,255,.04); }}
.rings {{ display:flex; gap:24px; align-items:center; margin:8px 0 16px 0; }}
.ring {{ width:86px; height:86px; border-radius:50%; background:conic-gradient(var(--c) calc(var(--p)*1%), #e8edf5 0); position:relative; display:grid; place-items:center; }}
.ring:after {{ content:""; position:absolute; inset:15px; background:#0b0f16; border-radius:50%; }}
.ring div {{ position:relative; z-index:1; text-align:center; }}
.ring b {{ display:block; font-size:15px; }}
.ring small {{ display:block; color:#dbeafe; font-size:10px; margin-top:2px; }}
.meta {{ display:grid; grid-template-columns:1fr 1fr; column-gap:16px; row-gap:7px; color:#dbeafe; font-size:12.5px; }}
.meta span {{ display:block; color:#7892b8; font-size:11px; }}
.shared {{ position:absolute; left:360px; right:270px; bottom:62px; border:1.5px dashed #f59e0b; border-radius:18px; padding:48px 22px 22px 22px; min-height:210px; box-sizing:border-box; background:rgba(245,158,11,.04); }}
.shared h3 {{ position:absolute; top:16px; left:22px; margin:0; color:#fbbf24; font-size:17px; }}
.shared .grid {{ grid-template-columns:repeat(3, minmax(0,1fr)); }}
.wip-lane {{ position:absolute; left:360px; right:270px; bottom:300px; height:90px; border:1px solid #334155; border-radius:14px; background:#111827; display:grid; place-items:center; color:#93c5fd; font-weight:700; }}
.arrow {{ position:absolute; color:#64748b; font-size:38px; }}
.a1 {{ left:200px; top:283px; }} .a2 {{ left:728px; top:283px; }} .a3 {{ right:228px; top:323px; transform:rotate(-25deg); }}
.legend {{ position:absolute; left:30px; bottom:24px; display:flex; gap:22px; color:#cbd5e1; font-size:13px; }}
.legend span:before {{ content:""; display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:7px; background:var(--c); }}
@media(max-width:1500px) {{ .floor {{ transform:scale(.86); transform-origin:top left; width:116%; }} }}
</style>
</head>
<body>
<div class="wrap">
  <div class="floor">
    <div class="floor-title">Factory floor live layout</div>
    <div class="support">
      <div class="zone-box">Raw material<br>storage</div>
      <div class="zone-box">Coil + sheet<br>storage</div>
      <div class="zone-box">Maintenance<br>tools</div>
    </div>
    <div class="output">
      <div class="zone-box">Finished goods<br>+ QA</div>
      <div class="zone-box">Scrap / resale<br>material</div>
    </div>
    <div class="arrow a1">→</div><div class="arrow a2">→</div><div class="arrow a3">→</div>
    <section class="line line1 l1"><h3>LINE 1 · RECTANGULAR DUCTS</h3><div class="grid">{cards_for('Line 1')}</div></section>
    <section class="line line2 l2"><h3>LINE 2 · ROUND / SPIRAL</h3><div class="grid">{cards_for('Line 2')}</div></section>
    <section class="line line3 l3"><h3>LINE 3 · CUSTOM / WELDED</h3><div class="grid">{cards_for('Line 3')}</div></section>
    <div class="wip-lane">Assembly / WIP staging lane</div>
    <section class="shared"><h3>SHARED RESOURCES</h3><div class="grid">{cards_for('Shared')}</div></section>
    <div class="legend">
      <span style="--c:#22c55e">Running</span><span style="--c:#f59e0b">Idle</span><span style="--c:#ef4444">Down</span><span style="--c:#94a3b8">Planned</span>
    </div>
  </div>
</div>
</body>
</html>
"""

st.subheader("Factory floor live layout")
components.html(layout_html, height=980, scrolling=False)

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
