import streamlit as st
import pandas as pd
from pathlib import Path
from html import escape

st.set_page_config(page_title="Duct Factory Dashboard", layout="wide")
BASE = Path(__file__).parent
machines = pd.read_csv(BASE / "machines.csv")
jobs = pd.read_csv(BASE / "jobs.csv")

STATUS = {"Running": "#22c55e", "Idle": "#f59e0b", "Down": "#ef4444", "Maintenance": "#94a3b8", "Planned": "#94a3b8"}
LINE_BG = {"line1": "#eff6ff", "line2": "#f0fdf4", "line3": "#faf5ff", "shared": "#fffbeb"}
LINE_BORDER = {"line1": "#60a5fa", "line2": "#4ade80", "line3": "#c084fc", "shared": "#f59e0b"}

st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
[data-testid="stMetricValue"] {font-size: 1.75rem;}
.kpi {border:1px solid #e5e7eb; border-radius:14px; padding:16px; background:#fff; min-height:95px;}
.kpi-label {font-size:0.78rem; color:#64748b; margin-bottom:8px;}
.kpi-value {font-size:1.8rem; font-weight:700; color:#0f172a;}
.kpi-note {font-size:0.75rem; color:#64748b; margin-top:4px;}
.floor {border:2px solid #9ca3af; border-radius:8px; padding:16px; background:#fbfbfb;}
.layout-grid {display:grid; grid-template-columns: 120px 1fr 1fr 1fr 120px; gap:12px; align-items:stretch;}
.support {border:1px solid #d1d5db; border-radius:10px; padding:10px; background:#fff; font-size:0.75rem; color:#374151; display:flex; align-items:center; justify-content:center; text-align:center; min-height:78px;}
.zone {border:1.5px dashed; border-radius:12px; padding:10px; min-height:330px;}
.zone-title {font-size:0.78rem; font-weight:700; text-align:center; margin-bottom:10px;}
.machine-grid {display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px;}
.shared-grid {display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px; margin-top:12px;}
.machine {border:1px solid #e5e7eb; border-radius:12px; background:#fff; padding:10px; min-height:136px;}
.machine-head {display:flex; justify-content:space-between; gap:8px; align-items:flex-start; margin-bottom:8px;}
.machine-name {font-size:0.78rem; font-weight:700; color:#111827; line-height:1.15;}
.dot {width:9px; height:9px; border-radius:50%; display:inline-block;}
.circles {display:flex; gap:12px; align-items:center; margin:8px 0;}
.circle {width:54px; height:54px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.78rem; font-weight:700; color:#111827;}
.circle-inner {width:42px; height:42px; border-radius:50%; background:white; display:flex; align-items:center; justify-content:center;}
.circle-label {font-size:0.62rem; color:#64748b; text-align:center; margin-top:2px;}
.time {font-size:0.68rem; color:#64748b; line-height:1.35;}
.legend {display:flex; gap:18px; font-size:0.78rem; color:#475569; margin-top:10px;}
</style>
""", unsafe_allow_html=True)

active_jobs = len(jobs[~jobs["status"].isin(["Complete", "Cancelled"])])
wip = len(jobs[jobs["status"] == "WIP"])
complete_today = len(jobs[jobs["status"] == "Complete"])
overall_util = round(machines[machines["status"] != "Planned"]["utilization"].mean())
bottleneck = machines.sort_values("utilization", ascending=False).iloc[0]
wip_hours = round(machines["wip_hours"].sum(), 1)

st.title("Factory Dashboard")
st.caption("Mock live dashboard for duct manufacturing")

cols = st.columns(5)
items = [
    ("Overall utilization", f"{overall_util}%", "Average active machine load"),
    ("Active jobs", active_jobs, "Open jobs in production"),
    ("WIP hours", f"{wip_hours}h", "Estimated work in progress"),
    ("Completed today", complete_today, "Finished and sent to QA"),
    ("Bottleneck", bottleneck["machine"], f"{bottleneck['utilization']}% utilization"),
]
for col, (label, value, note) in zip(cols, items):
    col.markdown(f"<div class='kpi'><div class='kpi-label'>{label}</div><div class='kpi-value'>{value}</div><div class='kpi-note'>{note}</div></div>", unsafe_allow_html=True)

st.markdown("### Factory floor live layout")

def machine_card(row):
    status_color = STATUS.get(row.status, "#94a3b8")
    util = int(row.utilization)
    hours = float(row.wip_hours)
    util_circle = f"conic-gradient({status_color} {util*3.6}deg, #e5e7eb 0deg)"
    hour_pct = min(hours / 4, 1) * 360
    hour_circle = f"conic-gradient(#64748b {hour_pct}deg, #e5e7eb 0deg)"
    return f"""
    <div class='machine'>
      <div class='machine-head'>
        <div class='machine-name'>{escape(str(row.id))}. {escape(row.machine)}</div>
        <span class='dot' style='background:{status_color}'></span>
      </div>
      <div class='circles'>
        <div><div class='circle' style='background:{util_circle}'><div class='circle-inner'>{util}%</div></div><div class='circle-label'>Util</div></div>
        <div><div class='circle' style='background:{hour_circle}'><div class='circle-inner'>{hours:.1f}h</div></div><div class='circle-label'>WIP</div></div>
      </div>
      <div class='time'>Started: {escape(str(row.started_at))}<br>Updated: {escape(str(row.last_updated))}<br>Job: <b>{escape(str(row.current_job))}</b></div>
    </div>
    """

def zone(area, title):
    subset = machines[machines["area"] == area]
    cards = "".join(machine_card(r) for r in subset.itertuples())
    return f"<div class='zone' style='background:{LINE_BG[area]}; border-color:{LINE_BORDER[area]}'><div class='zone-title'>{title}</div><div class='machine-grid'>{cards}</div></div>"

html = f"""
<div class='floor'>
  <div class='layout-grid'>
    <div>
      <div class='support'>Raw material<br>storage</div><br>
      <div class='support'>Coil + sheet<br>storage</div><br>
      <div class='support'>Maintenance<br>tools</div>
    </div>
    {zone('line1', 'LINE 1 - RECTANGULAR DUCTS')}
    {zone('line2', 'LINE 2 - ROUND / SPIRAL DUCTS')}
    {zone('line3', 'LINE 3 - CUSTOM / WELDED PARTS')}
    <div>
      <div class='support'>Finished goods<br>+ QA</div><br>
      <div class='support'>Scrap / resale<br>material</div>
    </div>
  </div>
  <div class='zone' style='background:{LINE_BG['shared']}; border-color:{LINE_BORDER['shared']}; margin:12px 132px 0 132px; min-height:0;'>
    <div class='zone-title'>SHARED RESOURCES</div>
    <div class='shared-grid'>{''.join(machine_card(r) for r in machines[machines['area']=='shared'].itertuples())}</div>
  </div>
  <div class='legend'>
    <span><span class='dot' style='background:#22c55e'></span> Running</span>
    <span><span class='dot' style='background:#f59e0b'></span> Idle</span>
    <span><span class='dot' style='background:#ef4444'></span> Down</span>
    <span><span class='dot' style='background:#94a3b8'></span> Planned / Maintenance</span>
  </div>
</div>
"""
st.markdown(html, unsafe_allow_html=True)

st.markdown("### Production lists")
left, right = st.columns(2)
with left:
    st.dataframe(jobs[jobs["status"] == "WIP"][["job_id", "product", "line", "current_stage", "progress", "started_at", "last_updated", "due"]], use_container_width=True, hide_index=True)
with right:
    st.dataframe(jobs[jobs["status"] == "Complete"][["job_id", "product", "line", "completed_at"]], use_container_width=True, hide_index=True)

with st.expander("Operator update mock"):
    with st.form("operator_update"):
        job = st.selectbox("Job", jobs[jobs["status"] == "WIP"]["job_id"])
        stage = st.selectbox("New stage", ["Cutting", "Forming", "Beading", "Seaming", "Welding", "Assembly", "QA", "Complete"])
        submitted = st.form_submit_button("Mark update")
        if submitted:
            st.success(f"Mock update: {job} → {stage}. Future version will save this to a database.")
