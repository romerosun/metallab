import math
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE = Path(__file__).parent

st.set_page_config(page_title="Factory Dashboard", layout="wide", page_icon="🏭")

CSS = """
<style>
:root { --bg:#0b0f16; --panel:#101722; --line:#263449; --text:#f8fafc; --muted:#9db1cf; --blue:#2f80ff; --green:#22d36d; --orange:#f5a400; --purple:#b75cff; --red:#ef4444; }
html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 1600px; }
h1, h2, h3, h4, p, span, div { color: var(--text); }
.small { color: var(--muted); font-size: 0.82rem; }
.kpi { background: var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px 20px; min-height:140px; }
.kpi .label { color:#9aa8bc; font-weight:700; font-size:0.85rem; }
.kpi .value { font-size:2rem; font-weight:800; margin-top:14px; }
.kpi .sub { color:#93c5fd; font-size:0.8rem; margin-top:14px; }
.floor { border:2px solid #2a3a52; border-radius:18px; padding:26px; background:#0b111a; }
.zone { border:1px solid #33465f; border-radius:16px; background:#0d141f; padding:18px; min-height:560px; }
.zone-title { font-weight:900; letter-spacing:.04em; font-size:1.05rem; margin-bottom:18px; }
.card { border:1px solid #33465f; border-radius:14px; background:#0c121c; padding:14px; min-height:235px; margin-bottom:18px; }
.card-running { border-color:#1fbe65; }
.card-idle { border-color:#f5a400; }
.card-down { border-color:#ef4444; }
.card-planned { border-color:#8da2c2; }
.machine-title { font-size:0.98rem; font-weight:900; line-height:1.1; margin-bottom:6px; }
.status-dot { float:right; width:12px; height:12px; border-radius:50%; margin-top:2px; }
.dot-running { background:#22d36d; box-shadow:0 0 14px #22d36d88; }
.dot-idle { background:#f5a400; box-shadow:0 0 14px #f5a40088; }
.dot-down { background:#ef4444; box-shadow:0 0 14px #ef444488; }
.dot-planned { background:#8da2c2; }
.meta { display:grid; grid-template-columns:1fr 1fr; gap:6px 14px; margin-top:8px; font-size:0.82rem; }
.meta .k { color:#82a6d9; }
.support-box { background:#10243a; border:1px solid #2b4c72; border-radius:12px; padding:20px; text-align:center; margin-bottom:18px; color:#58a6ff; font-weight:800; min-height:82px; display:flex; align-items:center; justify-content:center; }
.output-good { background:#123820; border:1px solid #1f6b39; border-radius:12px; padding:20px; margin-bottom:18px; color:#48f28a; font-weight:800; min-height:82px; display:flex; align-items:center; justify-content:center; text-align:center; }
.output-scrap { background:#3a3c0f; border:1px solid #777a1b; border-radius:12px; padding:20px; margin-bottom:18px; color:#f7ee65; font-weight:800; min-height:82px; display:flex; align-items:center; justify-content:center; text-align:center; }
.shared { border:1px dashed #f5a400; border-radius:16px; padding:18px; margin-top:24px; background:#15171b; }
.shared-title { color:#f5a400; font-weight:900; font-size:1rem; margin-bottom:12px; }
.stDataFrame { background:#0b111a; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

machines = pd.read_csv(BASE / "machines.csv")
jobs = pd.read_csv(BASE / "jobs.csv")

# Enrich old v7 data if needed
if "wip_hours" not in machines.columns:
    machines["wip_hours"] = [3.2,1.2,2.1,1.6,0.9,1.4,1.8,1.1,0.7,0.5,0.0][:len(machines)]
if "started_at" not in machines.columns:
    machines["started_at"] = ["07:30","09:00","08:05","08:10","09:15","09:05","08:30","08:45","09:20","09:25","-"][:len(machines)]
if "last_updated" not in machines.columns:
    machines["last_updated"] = ["10:24","10:18","10:22","10:20","10:21","10:19","10:23","10:17","10:16","10:15","-"][:len(machines)]
if "current_job" not in machines.columns:
    machines["current_job"] = ["JOB-1029","JOB-1024","JOB-1024","JOB-1030","JOB-1028","JOB-1026","JOB-1025","JOB-1031","JOB-1027","nan","-"][:len(machines)]
if "status" not in machines.columns:
    machines["status"] = ["Running","Idle","Running","Running","Running","Idle","Running","Running","Running","Idle","Planned"][:len(machines)]
if "utilization" not in machines.columns:
    machines["utilization"] = [88,65,82,74,68,60,75,69,63,58,0][:len(machines)]

status_class = {"Running":"running", "Idle":"idle", "Down":"down", "Planned":"planned", "Maintenance":"planned"}


def mini_gauge(value, label, color="#22d36d", suffix=""):
    value = float(value or 0)
    fig = go.Figure(go.Pie(
        values=[max(min(value, 100), 0), 100 - max(min(value, 100), 0)],
        hole=.72,
        sort=False,
        direction="clockwise",
        marker=dict(colors=[color, "#e8edf5"], line=dict(width=0)),
        textinfo="none",
        showlegend=False,
    ))
    fig.add_annotation(text=f"<b>{value:g}{suffix}</b><br><span style='font-size:10px'>{label}</span>", x=.5, y=.5, showarrow=False, font=dict(color="white", size=13))
    fig.update_layout(height=120, width=120, margin=dict(l=0,r=0,t=0,b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def kpi_card(label, value, sub):
    st.markdown(f"""
    <div class='kpi'>
      <div class='label'>{label}</div>
      <div class='value'>{value}</div>
      <div class='sub'>{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def machine_card(row, accent="#22d36d"):
    cls = status_class.get(str(row.status), "planned")
    st.markdown(f"""
    <div class='card card-{cls}'>
      <span class='status-dot dot-{cls}'></span>
      <div class='machine-title'>{row.machine}</div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(mini_gauge(row.utilization, "Util", accent), use_container_width=False, config={"displayModeBar": False})
    with c2:
        st.plotly_chart(mini_gauge(row.wip_hours, "WIP", "#8da2c2", "h"), use_container_width=False, config={"displayModeBar": False})
    st.markdown(f"""
      <div class='meta'>
        <div><div class='k'>Job</div><div>{row.current_job}</div></div>
        <div><div class='k'>Started</div><div>{row.started_at}</div></div>
        <div><div class='k'>Updated</div><div>{row.last_updated}</div></div>
        <div><div class='k'>Status</div><div>{row.status}</div></div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ---------- Capacity model defaults ----------
MACHINE_DEFAULTS = pd.DataFrame([
    {"machine":"CNC Plasma Cutting Table", "line":"Shared", "process":"Cutting", "speed_m_min":6.0, "setup_min":20, "operators":1, "thickness_min":0.5, "thickness_max":6.0},
    {"machine":"Hydraulic Pan Brake", "line":"Shared", "process":"Bending", "speed_m_min":4.0, "setup_min":15, "operators":1, "thickness_min":0.5, "thickness_max":3.0},
    {"machine":"Pittsburgh Lock Rollformer #1", "line":"Rectangular", "process":"Lock forming", "speed_m_min":10.5, "setup_min":10, "operators":1, "thickness_min":0.5, "thickness_max":1.6},
    {"machine":"Pittsburgh Lock / TDC Rollformer #2", "line":"Rectangular", "process":"Lock/TDC forming", "speed_m_min":12.0, "setup_min":10, "operators":1, "thickness_min":0.5, "thickness_max":1.6},
    {"machine":"Beading / Crimping Machine", "line":"Shared", "process":"Beading/crimping", "speed_m_min":8.0, "setup_min":10, "operators":1, "thickness_min":0.5, "thickness_max":2.0},
    {"machine":"Duct Seaming Machine", "line":"Shared", "process":"Seaming", "speed_m_min":7.0, "setup_min":10, "operators":1, "thickness_min":0.5, "thickness_max":2.0},
    {"machine":"3-Roll Plate Roller #1", "line":"Round", "process":"Rolling", "speed_m_min":4.0, "setup_min":20, "operators":1, "thickness_min":0.5, "thickness_max":3.0},
    {"machine":"3-Roll Plate Bending Machine #2", "line":"Round", "process":"Heavy rolling", "speed_m_min":3.0, "setup_min":25, "operators":1, "thickness_min":0.5, "thickness_max":5.0},
    {"machine":"Mechanical Power Press", "line":"Custom", "process":"Punching/forming", "speed_m_min":5.0, "setup_min":20, "operators":1, "thickness_min":0.5, "thickness_max":4.0},
    {"machine":"Hydraulic Punch / Ironworker", "line":"Custom", "process":"Punching/notching", "speed_m_min":4.5, "setup_min":20, "operators":1, "thickness_min":0.5, "thickness_max":5.0},
])

ROUTES = {
    "Rectangular duct": ["CNC Plasma Cutting Table", "Pittsburgh Lock Rollformer #1", "Pittsburgh Lock / TDC Rollformer #2", "Hydraulic Pan Brake", "Beading / Crimping Machine", "Duct Seaming Machine"],
    "Round duct": ["CNC Plasma Cutting Table", "3-Roll Plate Roller #1", "3-Roll Plate Bending Machine #2", "Beading / Crimping Machine", "Duct Seaming Machine"],
    "Connector / fitting": ["CNC Plasma Cutting Table", "Hydraulic Pan Brake", "Mechanical Power Press", "Hydraulic Punch / Ironworker", "Duct Seaming Machine"],
    "Roof / HVAC base": ["CNC Plasma Cutting Table", "Hydraulic Pan Brake", "Mechanical Power Press", "Hydraulic Punch / Ironworker"],
    "Custom work": ["CNC Plasma Cutting Table", "Mechanical Power Press", "Hydraulic Punch / Ironworker", "Hydraulic Pan Brake"],
}


def estimate_capacity(specs, product_mix, avg_lengths, quantities, thicknesses, total_hours, operators_available, efficiency):
    specs = specs.copy()
    available_machine_minutes = total_hours * 60 * efficiency
    machine_load = {m: 0.0 for m in specs.machine}
    product_results = []

    for product, mix_pct in product_mix.items():
        qty = quantities[product]
        length = avg_lengths[product]
        thickness = thicknesses[product]
        route = ROUTES[product]
        total_job_min = 0.0
        bottleneck = None
        bottleneck_min = -1
        feasible_thickness = True

        for mach in route:
            row = specs.loc[specs.machine == mach].iloc[0]
            if not (row.thickness_min <= thickness <= row.thickness_max):
                feasible_thickness = False
            process_min = row.setup_min + (qty * length) / max(row.speed_m_min, 0.01)
            # product mix is treated as demand priority weighting, not physical share multiplier
            machine_load[mach] += process_min
            total_job_min += process_min
            if process_min > bottleneck_min:
                bottleneck_min = process_min
                bottleneck = mach

        product_results.append({
            "product": product,
            "qty_input": qty,
            "avg_length_m": length,
            "thickness_mm": thickness,
            "route_machines": len(route),
            "est_total_machine_hours": round(total_job_min / 60, 2),
            "bottleneck_step": bottleneck,
            "thickness_ok": feasible_thickness,
        })

    load_df = pd.DataFrame([{"machine": m, "load_hours": v/60, "utilization_%": 100*(v/60)/total_hours if total_hours else 0} for m, v in machine_load.items()])
    load_df = load_df.merge(specs[["machine", "line", "process"]], on="machine", how="left")
    load_df["utilization_%"] = load_df["utilization_%"].round(1)
    load_df["load_hours"] = load_df["load_hours"].round(2)
    labor_required = 0
    for _, row in specs.iterrows():
        labor_required += (machine_load.get(row.machine, 0) / 60) * row.operators
    labor_capacity = operators_available * total_hours
    bottleneck_row = load_df.sort_values("utilization_%", ascending=False).iloc[0]
    return pd.DataFrame(product_results), load_df.sort_values("utilization_%", ascending=False), labor_required, labor_capacity, bottleneck_row


st.title("Factory Dashboard")
st.caption("Live production view + first-pass capacity calculator for duct manufacturing")

tab1, tab2, tab3 = st.tabs(["Live dashboard", "Capacity calculator", "Data"])

with tab1:
    active = int((jobs.get("status", pd.Series([None]*len(jobs))).fillna("") != "Completed").sum()) if "status" in jobs.columns else 8
    completed = int((jobs.get("status", pd.Series()).fillna("") == "Completed").sum()) if "status" in jobs.columns else 3
    avg_util = int(machines[machines.status != "Planned"].utilization.mean())
    wip_hours = round(float(machines.wip_hours.sum()), 1)
    bottleneck = machines.sort_values("utilization", ascending=False).iloc[0]

    cols = st.columns(6)
    with cols[0]: kpi_card("Utilization", f"{avg_util}%", "Average active load")
    with cols[1]: kpi_card("WIP hours", f"{wip_hours}h", "Estimated work")
    with cols[2]: kpi_card("Active jobs", active, "Open production jobs")
    with cols[3]: kpi_card("Completed", completed, "Finished today")
    with cols[4]: kpi_card("Throughput", completed, "Jobs/day mock")
    with cols[5]: kpi_card("Bottleneck", str(bottleneck.machine).replace(" Table", ""), f"{bottleneck.utilization}% utilization")

    st.markdown("## Factory floor live layout")
    with st.container():
        st.markdown("<div class='floor'>", unsafe_allow_html=True)
        support, line1, line2, line3, output = st.columns([1.1, 3.2, 3.2, 3.2, 1.2], gap="large")
        with support:
            st.markdown("<div class='zone-title'>Support</div>", unsafe_allow_html=True)
            for txt in ["Raw material storage", "Coil + sheet storage", "Maintenance tools"]:
                st.markdown(f"<div class='support-box'>{txt}</div>", unsafe_allow_html=True)
        with line1:
            st.markdown("<div class='zone'><div class='zone-title' style='color:#58a6ff'>LINE 1 · RECTANGULAR DUCTS</div>", unsafe_allow_html=True)
            for _, row in machines[machines.line.astype(str).str.contains("Line 1", na=False)].iterrows():
                machine_card(row, "#2f80ff" if row.status == "Running" else "#f5a400")
            st.markdown("</div>", unsafe_allow_html=True)
        with line2:
            st.markdown("<div class='zone'><div class='zone-title' style='color:#34e57a'>LINE 2 · ROUND / SPIRAL</div>", unsafe_allow_html=True)
            for _, row in machines[machines.line.astype(str).str.contains("Line 2", na=False)].iterrows():
                machine_card(row, "#22d36d" if row.status == "Running" else "#f5a400")
            st.markdown("</div>", unsafe_allow_html=True)
        with line3:
            st.markdown("<div class='zone'><div class='zone-title' style='color:#c66bff'>LINE 3 · CUSTOM / WELDED</div>", unsafe_allow_html=True)
            for _, row in machines[machines.line.astype(str).str.contains("Line 3", na=False)].iterrows():
                machine_card(row, "#b75cff" if row.status == "Running" else "#f5a400")
            st.markdown("</div>", unsafe_allow_html=True)
        with output:
            st.markdown("<div class='zone-title'>Output</div>", unsafe_allow_html=True)
            st.markdown("<div class='output-good'>Finished goods + QA</div>", unsafe_allow_html=True)
            st.markdown("<div class='output-scrap'>Scrap / resale material</div>", unsafe_allow_html=True)

        st.markdown("<div class='shared'><div class='shared-title'>SHARED RESOURCES</div>", unsafe_allow_html=True)
        scols = st.columns(3)
        shared_names = ["CNC Plasma Cutting Table", "Hydraulic Pan Brake", "Beading / Crimping Machine"]
        for i, name in enumerate(shared_names):
            rows = machines[machines.machine.str.contains(name.split()[0], case=False, na=False)]
            if name == "Hydraulic Pan Brake": rows = machines[machines.machine.str.contains("Pan Brake", case=False, na=False)]
            if name == "Beading / Crimping Machine": rows = machines[machines.machine.str.contains("Beading", case=False, na=False)]
            if len(rows):
                with scols[i]:
                    machine_card(rows.iloc[0], "#f5a400")
        st.markdown("</div></div>", unsafe_allow_html=True)

    st.markdown("## Production lists")
    a, b = st.columns(2)
    with a:
        st.subheader("Work in progress")
        st.dataframe(jobs[jobs.get("status", "") != "Completed"] if "status" in jobs.columns else jobs, use_container_width=True, hide_index=True)
    with b:
        st.subheader("Completed")
        if "status" in jobs.columns:
            st.dataframe(jobs[jobs.status == "Completed"], use_container_width=True, hide_index=True)
        else:
            st.dataframe(jobs.tail(3), use_container_width=True, hide_index=True)

with tab2:
    st.header("Capacity calculator")
    st.caption("First-pass estimate. Use it to structure the conversation with the factory, not as a final engineering rating.")

    left, right = st.columns([1.1, 2.2], gap="large")
    with left:
        st.subheader("Shift + labor")
        shifts = st.number_input("Number of shifts", 1, 3, 1)
        hours_per_shift = st.number_input("Hours per shift", 1.0, 12.0, 8.0, 0.5)
        operators = st.number_input("Operators available", 1, 50, 6)
        efficiency = st.slider("Practical efficiency factor", 30, 100, 70, help="Accounts for setup, walking, waiting, breaks, rework and material handling.") / 100
        total_hours = shifts * hours_per_shift

        st.subheader("Demand / product mix")
        rect_pct = st.slider("Rectangular ducts %", 0, 100, 40)
        round_pct = st.slider("Round ducts %", 0, 100, 25)
        fittings_pct = st.slider("Connectors / fittings %", 0, 100, 15)
        roof_pct = st.slider("Roof / HVAC bases %", 0, 100, 15)
        custom_pct = max(0, 100 - rect_pct - round_pct - fittings_pct - roof_pct)
        st.metric("Custom work %", f"{custom_pct}%")

    products = ["Rectangular duct", "Round duct", "Connector / fitting", "Roof / HVAC base", "Custom work"]
    with right:
        st.subheader("Order assumptions")
        st.caption("These are editable mock assumptions. Replace them with real averages after visiting the factory.")
        inputs = []
        defaults = {
            "Rectangular duct": (80, 2.0, 0.9),
            "Round duct": (50, 2.0, 0.9),
            "Connector / fitting": (35, 0.8, 1.0),
            "Roof / HVAC base": (20, 1.5, 1.2),
            "Custom work": (10, 1.0, 1.5),
        }
        for p in products:
            c1, c2, c3 = st.columns(3)
            dq, dl, dt = defaults[p]
            with c1: qty = st.number_input(f"{p}: qty", 0, 10000, dq, key=f"qty_{p}")
            with c2: length = st.number_input(f"{p}: avg length m", 0.1, 20.0, dl, 0.1, key=f"len_{p}")
            with c3: thk = st.number_input(f"{p}: thickness mm", 0.1, 10.0, dt, 0.1, key=f"thk_{p}")
            inputs.append((p, qty, length, thk))

    product_mix = {
        "Rectangular duct": rect_pct,
        "Round duct": round_pct,
        "Connector / fitting": fittings_pct,
        "Roof / HVAC base": roof_pct,
        "Custom work": custom_pct,
    }
    quantities = {p:q for p,q,_,_ in inputs}
    avg_lengths = {p:l for p,_,l,_ in inputs}
    thicknesses = {p:t for p,_,_,t in inputs}

    st.subheader("Machine assumptions")
    st.caption("Speeds are editable placeholders seeded from catalog-style machine ratings and conservative assumptions for unknown machines.")
    specs = st.data_editor(MACHINE_DEFAULTS, use_container_width=True, hide_index=True, num_rows="fixed")

    product_df, load_df, labor_required, labor_capacity, bottleneck_row = estimate_capacity(
        specs, product_mix, avg_lengths, quantities, thicknesses, total_hours, operators, efficiency
    )

    st.subheader("Capacity result")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Available machine hours", f"{total_hours * efficiency:.1f}h", f"{shifts} shift(s)")
    with k2: st.metric("Labor required", f"{labor_required:.1f}h", f"capacity {labor_capacity:.1f}h")
    with k3: st.metric("Bottleneck", bottleneck_row.machine, f"{bottleneck_row['utilization_%']}% load")
    with k4:
        feasible = "Yes" if (load_df["utilization_%"].max() <= 100 and labor_required <= labor_capacity and product_df.thickness_ok.all()) else "No"
        st.metric("Can make today?", feasible)

    st.subheader("Machine load")
    st.dataframe(load_df, use_container_width=True, hide_index=True)
    st.subheader("Product estimates")
    st.dataframe(product_df, use_container_width=True, hide_index=True)

    fig = go.Figure(go.Bar(x=load_df["machine"], y=load_df["utilization_%"]))
    fig.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), yaxis_title="Utilization %", xaxis_title="")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with tab3:
    st.header("Raw data")
    st.subheader("Machines")
    st.dataframe(machines, use_container_width=True, hide_index=True)
    st.subheader("Jobs")
    st.dataframe(jobs, use_container_width=True, hide_index=True)
