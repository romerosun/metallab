import streamlit as st
import pandas as pd
from pathlib import Path
from html import escape

st.set_page_config(page_title="Factory Dashboard", layout="wide")
BASE = Path(__file__).parent
machines = pd.read_csv(BASE / "machines.csv")
jobs = pd.read_csv(BASE / "jobs.csv")

STATUS = {"Running": "#22c55e", "Idle": "#f59e0b", "Down": "#ef4444", "Maintenance": "#94a3b8", "Planned": "#94a3b8"}
LINE_BG = {"line1": "#eff6ff", "line2": "#f0fdf4", "line3": "#faf5ff", "shared": "#fffbeb"}
LINE_BORDER = {"line1": "#60a5fa", "line2": "#4ade80", "line3": "#c084fc", "shared": "#f59e0b"}

st.markdown("""
<style>
.block-container {padding-top: 1.4rem; max-width: 1600px;}
.kpi {border:1px solid #e5e7eb; border-radius:14px; padding:16px; background:#fff; min-height:92px;}
.kpi-label {font-size:0.78rem; color:#64748b; margin-bottom:8px;}
.kpi-value {font-size:1.55rem; font-weight:750; color:#0f172a; line-height:1.15;}
.kpi-note {font-size:0.72rem; color:#64748b; margin-top:7px;}
.floor {border:2px solid #9ca3af; border-radius:8px; padding:16px; background:#fbfbfb; margin-top:8px;}
.layout-grid {display:grid; grid-template-columns: 120px 1.25fr 1fr 1fr 120px; gap:12px; align-items:stretch;}
.support {border:1px solid #d1d5db; border-radius:10px; padding:10px; background:#fff; font-size:0.72rem; color:#374151; display:flex; align-items:center; justify-content:center; text-align:center; min-height:74px; margin-bottom:12px;}
.zone {border:1.5px dashed; border-radius:12px; padding:10px; min-height:310px;}
.zone-title {font-size:0.75rem; font-weight:800; text-align:center; margin-bottom:10px; letter-spacing:.02em;}
.machine-grid {display:grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap:10px;}
.shared-grid {display:grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap:10px;}
.machine {border:1px solid #e5e7eb; border-radius:12px; background:#fff; padding:10px; min-height:130px; box-sizing:border-box;}
.machine-head {display:flex; justify-content:space-between; gap:8px; align-items:flex-start; margin-bottom:7px;}
.machine-name {font-size:0.74rem; font-weight:800; color:#111827; line-height:1.2;}
.dot {width:9px; height:9px; border-radius:50%; display:inline-block; flex:0 0 auto; margin-top:2px;}
.circles {display:flex; gap:12px; align-items:center; margin:8px 0;}
.circle {width:52px; height:52px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.76rem; font-weight:800; color:#111827;}
.circle-inner {width:40px; height:40px; border-radius:50%; background:white; display:flex; align-items:center; justify-content:center;}
.circle-label {font-size:0.60rem; color:#64748b; text-align:center; margin-top:2px;}
.time {font-size:0.65rem; color:#64748b; line-height:1.35;}
.shared-zone {margin:12px 132px 0 132px; min-height:0;}
.legend {display:flex; gap:18px; font-size:0.75rem; color:#475569; margin-top:10px; flex-wrap:wrap;}
@media (max-width: 1100px) {.layout-grid {grid-template-columns:1fr;} .shared-zone {margin:12px 0 0 0;} .shared-grid {grid-template-columns:1fr;} .machine-grid {grid-template-columns:1fr;}}
</style>
""", unsafe_allow_html=True)

active_jobs = len(jobs[~jobs["status"].isin(["Complete", "Cancelled"])])
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
    col.markdown(f"<div class='kpi'><div class='kpi-label'>{escape(str(label))}</div><div class='kpi-value'>{escape(str(value))}</div><div class='kpi-note'>{escape(str(note))}</div></div>", unsafe_allow_html=True)

st.markdown("### Factory floor live layout")

def machine_card(row):
    status_color = STATUS.get(str(row.status), "#94a3b8")
    util = int(row.utilization)
    hours = float(row.wip_hours)
    util_deg = max(0, min(util, 100)) * 3.6
    hour_deg = max(0, min(hours / 4, 1)) * 360
    return f"""
    <div class='machine'>
      <div class='machine-head'>
        <div class='machine-name'>{escape(str(row.id))}. {escape(str(row.machine))}</div>
        <span class='dot' style='background:{status_color}'></span>
      </div>
      <div class='circles'>
        <div><div class='circle' style='background:conic-gradient({status_color} {util_deg}deg, #e5e7eb 0deg)'><div class='circle-inner'>{util}%</div></div><div class='circle-label'>Util</div></div>
        <div><div class='circle' style='background:conic-gradient(#64748b {hour_deg}deg, #e5e7eb 0deg)'><div class='circle-inner'>{hours:.1f}h</div></div><div class='circle-label'>WIP</div></div>
      </div>
      <div class='time'>Started: {escape(str(row.started_at))}<br>Updated: {escape(str(row.last_updated))}<br>Job: <b>{escape(str(row.current_job))}</b></div>
    </div>
    """

def zone(area, title):
    subset = machines[machines["area"] == area]
    cards = "".join(machine_card(r) for r in subset.itertuples())
    return f"<div class='zone' style='background:{LINE_BG[area]}; border-color:{LINE_BORDER[area]}'><div class='zone-title'>{escape(title)}</div><div class='machine-grid'>{cards}</div></div>"

shared_cards = "".join(machine_card(r) for r in machines[machines["area"] == "shared"].itertuples())
html = """
<div class='floor'>
  <div class='layout-grid'>
    <div>
      <div class='support'>Raw material<br>storage</div>
      <div class='support'>Coil + sheet<br>storage</div>
      <div class='support'>Maintenance<br>tools</div>
    </div>
    {line1}
    {line2}
    {line3}
    <div>
      <div class='support'>Finished goods<br>+ QA</div>
      <div class='support'>Scrap / resale<br>material</div>
    </div>
  </div>
  <div class='zone shared-zone' style='background:{shared_bg}; border-color:{shared_border};'>
    <div class='zone-title'>SHARED RESOURCES</div>
    <div class='shared-grid'>{shared_cards}</div>
  </div>
  <div class='legend'>
    <span><span class='dot' style='background:#22c55e'></span> Running</span>
    <span><span class='dot' style='background:#f59e0b'></span> Idle</span>
    <span><span class='dot' style='background:#ef4444'></span> Down</span>
    <span><span class='dot' style='background:#94a3b8'></span> Planned / Maintenance</span>
  </div>
</div>
""".format(
    line1=zone("line1", "LINE 1 - RECTANGULAR DUCTS"),
    line2=zone("line2", "LINE 2 - ROUND / SPIRAL DUCTS"),
    line3=zone("line3", "LINE 3 - CUSTOM / WELDED PARTS"),
    shared_bg=LINE_BG["shared"],
    shared_border=LINE_BORDER["shared"],
    shared_cards=shared_cards,
)
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
