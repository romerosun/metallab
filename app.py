from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE = Path(__file__).parent

st.set_page_config(page_title="Factory Capacity Planner", layout="wide", page_icon="🏭")

CSS = """
<style>
:root { --bg:#0b0f16; --panel:#101722; --line:#263449; --text:#f8fafc; --muted:#9db1cf; --green:#22d36d; --yellow:#f5a400; --red:#ef4444; --blue:#2f80ff; }
html, body, [data-testid="stAppViewContainer"] { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { background: transparent; }
.block-container { padding-top: 1.2rem; max-width: 1500px; }
h1, h2, h3, h4, p, span, div, label { color: var(--text); }
.small { color: var(--muted); font-size: 0.85rem; }
.kpi { background: var(--panel); border:1px solid var(--line); border-radius:14px; padding:18px 20px; min-height:132px; }
.kpi .label { color:#9aa8bc; font-weight:800; font-size:0.85rem; }
.kpi .value { font-size:2rem; font-weight:900; margin-top:12px; }
.kpi .sub { color:#93c5fd; font-size:0.82rem; margin-top:12px; }
.kpi.good { border-color:#1f7a49; }
.kpi.warn { border-color:#a66d00; }
.kpi.bad { border-color:#9f2626; }
.badge { display:inline-block; padding:5px 10px; border-radius:999px; font-weight:800; font-size:0.8rem; }
.badge.good { background:#113d25; color:#48f28a; }
.badge.warn { background:#3a2e0e; color:#ffd166; }
.badge.bad { background:#3a1212; color:#ff8a8a; }
.bar-wrap { background:#1d2635; height:18px; border-radius:999px; overflow:hidden; border:1px solid #2d3b50; }
.bar-fill { height:100%; border-radius:999px; }
.note { background:#0f1724; border:1px solid #263449; border-radius:14px; padding:16px 18px; color:#b9c9e3; }
hr { border-color:#243044; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

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


def health_class(pct: float):
    if pct < 70:
        return "good", "#22d36d", "Comfortable"
    if pct <= 90:
        return "warn", "#f5a400", "Getting tight"
    return "bad", "#ef4444", "Overloaded"


def kpi_card(label, value, sub, cls=""):
    st.markdown(f"""
    <div class='kpi {cls}'>
      <div class='label'>{label}</div>
      <div class='value'>{value}</div>
      <div class='sub'>{sub}</div>
    </div>
    """, unsafe_allow_html=True)


def progress_bar(title, used, limit, suffix="h"):
    pct = 0 if limit <= 0 else min(140, used / limit * 100)
    cls, color, label = health_class(pct)
    st.markdown(f"""
    <div class='note'>
      <b>{title}</b><br>
      <span class='small'>{used:.1f}{suffix} used / {limit:.1f}{suffix} limit</span><br><br>
      <div class='bar-wrap'><div class='bar-fill' style='width:{min(pct,100):.1f}%; background:{color};'></div></div><br>
      <span class='badge {cls}'>{label} · {pct:.0f}%</span>
    </div>
    """, unsafe_allow_html=True)


def estimate_capacity(specs, avg_lengths, quantities, thicknesses, total_hours, operators_available, efficiency):
    specs = specs.copy()
    machine_limit_hours = total_hours * efficiency
    machine_load = {m: 0.0 for m in specs.machine}
    product_results = []

    for product, qty in quantities.items():
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
            machine_load[mach] += process_min
            total_job_min += process_min
            if process_min > bottleneck_min:
                bottleneck_min = process_min
                bottleneck = mach

        product_results.append({
            "product": product,
            "qty": qty,
            "avg_length_m": length,
            "thickness_mm": thickness,
            "estimated_machine_hours": round(total_job_min / 60, 2),
            "bottleneck_step": bottleneck,
            "thickness_ok": feasible_thickness,
        })

    load_df = pd.DataFrame([
        {"machine": m, "load_hours": v / 60, "utilization_%": 100 * (v / 60) / machine_limit_hours if machine_limit_hours else 0}
        for m, v in machine_load.items()
    ])
    load_df = load_df.merge(specs[["machine", "line", "process", "operators"]], on="machine", how="left")
    load_df["utilization_%"] = load_df["utilization_%"].round(1)
    load_df["load_hours"] = load_df["load_hours"].round(2)

    labor_required = sum((machine_load.get(row.machine, 0) / 60) * row.operators for _, row in specs.iterrows())
    labor_capacity = operators_available * total_hours * efficiency
    bottleneck_row = load_df.sort_values("utilization_%", ascending=False).iloc[0]
    return pd.DataFrame(product_results), load_df.sort_values("utilization_%", ascending=False), labor_required, labor_capacity, machine_limit_hours, bottleneck_row


st.title("Factory Capacity Planner")
st.caption("First-pass planning tool for duct manufacturing. Enter today's work and see labor load, machine limits, and bottlenecks.")

left, right = st.columns([1.0, 2.3], gap="large")

with left:
    st.subheader("Factory limits")
    shifts = st.number_input("Number of shifts", 1, 3, 1)
    hours_per_shift = st.number_input("Hours per shift", 1.0, 12.0, 8.0, 0.5)
    operators = st.number_input("Operators available", 1, 50, 6)
    efficiency = st.slider("Efficiency factor", 30, 100, 70, help="Practical usable time after setup, walking, waiting, breaks, rework, and material handling.") / 100
    total_hours = shifts * hours_per_shift

    st.markdown("---")
    st.subheader("Today’s order")
    st.caption("Use quantity, average length, and thickness for each product family.")

with right:
    products = ["Rectangular duct", "Round duct", "Connector / fitting", "Roof / HVAC base", "Custom work"]
    defaults = {
        "Rectangular duct": (80, 2.0, 0.9),
        "Round duct": (50, 2.0, 0.9),
        "Connector / fitting": (35, 0.8, 1.0),
        "Roof / HVAC base": (20, 1.5, 1.2),
        "Custom work": (10, 1.0, 1.5),
    }
    inputs = []
    for p in products:
        st.markdown(f"**{p}**")
        c1, c2, c3 = st.columns(3)
        dq, dl, dt = defaults[p]
        with c1: qty = st.number_input("Qty", 0, 10000, dq, key=f"qty_{p}")
        with c2: length = st.number_input("Avg length m", 0.1, 20.0, dl, 0.1, key=f"len_{p}")
        with c3: thk = st.number_input("Thickness mm", 0.1, 10.0, dt, 0.1, key=f"thk_{p}")
        inputs.append((p, qty, length, thk))

quantities = {p:q for p,q,_,_ in inputs}
avg_lengths = {p:l for p,_,l,_ in inputs}
thicknesses = {p:t for p,_,_,t in inputs}

specs = MACHINE_DEFAULTS.copy()
product_df, load_df, labor_required, labor_capacity, machine_limit_hours, bottleneck_row = estimate_capacity(
    specs, avg_lengths, quantities, thicknesses, total_hours, operators, efficiency
)

st.markdown("---")
st.subheader("Capacity result")

labor_pct = 0 if labor_capacity <= 0 else labor_required / labor_capacity * 100
machine_pct = load_df["utilization_%"].max()
labor_cls, _, labor_label = health_class(labor_pct)
machine_cls, _, machine_label = health_class(machine_pct)
feasible = "Yes" if machine_pct <= 100 and labor_pct <= 100 and product_df.thickness_ok.all() else "No"

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Labor required", f"{labor_required:.1f}h", f"Limit {labor_capacity:.1f}h · {labor_label}", labor_cls)
with k2: kpi_card("Machine bottleneck", bottleneck_row.machine, f"{machine_pct:.0f}% of daily machine limit", machine_cls)
with k3: kpi_card("Can make today?", feasible, "Based on current assumptions", "good" if feasible == "Yes" else "bad")
with k4: kpi_card("Unused labor", f"{max(labor_capacity-labor_required,0):.1f}h", "After planned work")

c1, c2 = st.columns(2, gap="large")
with c1:
    progress_bar("Labor capacity limit", labor_required, labor_capacity, "h")
with c2:
    progress_bar("Highest machine load limit", machine_pct, 100, "%")

st.markdown("---")
st.subheader("Machine load")
st.dataframe(load_df, use_container_width=True, hide_index=True)

fig = go.Figure(go.Bar(x=load_df["machine"], y=load_df["utilization_%"]))
fig.add_hline(y=70, line_dash="dot", annotation_text="comfortable limit")
fig.add_hline(y=90, line_dash="dot", annotation_text="tight")
fig.add_hline(y=100, line_dash="dash", annotation_text="capacity limit")
fig.update_layout(height=390, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="white"), yaxis_title="Utilization %", xaxis_title="")
st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

st.subheader("Product estimates")
st.dataframe(product_df, use_container_width=True, hide_index=True)

with st.expander("Machine assumptions", expanded=False):
    st.caption("Editable placeholders seeded from catalog-style machine ratings and conservative assumptions where exact rates are unknown.")
    edited = st.data_editor(MACHINE_DEFAULTS, use_container_width=True, hide_index=True, num_rows="fixed")
    st.info("After changing assumptions, copy them into the code or wire this table to a CSV/database in the next version.")
