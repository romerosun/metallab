import math
from pathlib import Path
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title='HVAC Production Metro', layout='wide')
BASE = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    return (
        pd.read_csv(BASE / 'orders.csv'),
        pd.read_csv(BASE / 'machines.csv'),
        pd.read_csv(BASE / 'routing_assumptions.csv'),
    )

orders_default, machines_default, routing_default = load_data()

# Normalize dtypes for Streamlit data_editor compatibility.
orders_default['due_date'] = pd.to_datetime(orders_default['due_date'], errors='coerce')
orders_default['quantity'] = pd.to_numeric(orders_default['quantity'], errors='coerce').fillna(0).astype(int)
orders_default['avg_length_m'] = pd.to_numeric(orders_default['avg_length_m'], errors='coerce').fillna(0.0).astype(float)
orders_default['thickness_mm'] = pd.to_numeric(orders_default['thickness_mm'], errors='coerce').fillna(0.0).astype(float)
machines_default['parallel_units'] = pd.to_numeric(machines_default['parallel_units'], errors='coerce').fillna(1).astype(int)
machines_default['availability'] = pd.to_numeric(machines_default['availability'], errors='coerce').fillna(1.0).astype(float)
routing_default['base_minutes_per_unit'] = pd.to_numeric(routing_default['base_minutes_per_unit'], errors='coerce').fillna(0.0).astype(float)
routing_default['labor_touch_factor'] = pd.to_numeric(routing_default['labor_touch_factor'], errors='coerce').fillna(0.0).astype(float)

st.markdown('''
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 3rem; max-width: 1600px;}
[data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.25); border-radius: 14px; padding: 14px 16px; background: rgba(128,128,128,.04);}
[data-testid="stMetricLabel"] {font-size: .88rem;}
div[data-testid="stDataEditor"] {border-radius: 12px; overflow: hidden;}
</style>
''', unsafe_allow_html=True)

st.title('HVAC Production Metro')
st.caption('Mock production plan using the updated machine inventory. Processing times are editable assumptions until actual shop data is collected.')

with st.sidebar:
    st.header('Planning inputs')
    shifts = st.number_input('Shifts', min_value=1, max_value=3, value=1, step=1)
    hours_per_shift = st.number_input('Hours per shift', min_value=1.0, max_value=16.0, value=8.0, step=0.5)
    operators = st.number_input('Operators available', min_value=1, max_value=100, value=8, step=1)
    paid_hours = st.number_input('Actual paid labor hours', min_value=0.0, value=64.0, step=1.0)
    labor_efficiency = st.slider('Labor efficiency', 40, 100, 82, 1) / 100
    setup_minutes = st.number_input('Setup minutes per order / machine', min_value=0.0, value=12.0, step=1.0)

plan_tab, order_tab, assumption_tab = st.tabs(['Metro plan', 'Order list', 'Assumptions'])

with order_tab:
    st.subheader('Example order list')
    st.caption('Replace these example rows after learning how the company records orders.')
    orders = st.data_editor(
        orders_default,
        num_rows='dynamic',
        use_container_width=True,
        hide_index=True,
        column_config={
            'family': st.column_config.SelectboxColumn('family', options=['Rectangular','Round','Fittings','Custom'], required=True),
            'due_date': st.column_config.DateColumn('due_date'),
            'quantity': st.column_config.NumberColumn('quantity', min_value=1),
            'avg_length_m': st.column_config.NumberColumn('avg_length_m', min_value=0.1, format='%.2f'),
            'thickness_mm': st.column_config.NumberColumn('thickness_mm', min_value=0.1, format='%.2f'),
        },
        key='orders_editor',
    )

with assumption_tab:
    st.subheader('Machine-time assumptions')
    st.caption('These are placeholders. Update them using time studies, machine logs, or validated catalog calculations.')
    routing = st.data_editor(
        routing_default,
        use_container_width=True,
        hide_index=True,
        disabled=['family','machine_id','machine'],
        column_config={
            'base_minutes_per_unit': st.column_config.NumberColumn('Base min/unit', min_value=0.01, format='%.2f'),
            'labor_touch_factor': st.column_config.NumberColumn('Labor touch factor', min_value=0.0, max_value=2.0, format='%.2f'),
        },
        key='routing_editor',
    )
    st.subheader('Machine availability')
    machines = st.data_editor(
        machines_default,
        use_container_width=True,
        hide_index=True,
        disabled=['machine_id','machine','line'],
        column_config={
            'parallel_units': st.column_config.NumberColumn('Parallel units', min_value=1, step=1),
            'availability': st.column_config.NumberColumn('Availability', min_value=0.1, max_value=1.0, format='%.2f'),
        },
        key='machines_editor',
    )

# The data_editor return values are the edited DataFrames for this rerun.
# Do not read the widget's internal session-state payload as if it were a DataFrame.

def adjusted_minutes(order, base):
    length_factor = max(float(order['avg_length_m']) / 2.0, 0.35)
    thickness_factor = 1.0 + max(float(order['thickness_mm']) - 0.8, 0) * 0.22
    return base * length_factor * thickness_factor

records = []
for _, order in orders.iterrows():
    routes = routing[routing['family'] == order['family']]
    for _, route in routes.iterrows():
        run_minutes = float(order['quantity']) * adjusted_minutes(order, float(route['base_minutes_per_unit']))
        machine_minutes = run_minutes + setup_minutes
        labor_minutes = run_minutes * float(route['labor_touch_factor']) + setup_minutes
        records.append({
            'order_id': order['order_id'],
            'product': order['product'],
            'family': order['family'],
            'machine_id': int(route['machine_id']),
            'machine': route['machine'],
            'machine_hours': machine_minutes / 60,
            'labor_hours': labor_minutes / 60 / labor_efficiency,
        })

load = pd.DataFrame(records)
if load.empty:
    machine_load = pd.DataFrame(columns=['machine_id','machine','machine_hours','labor_hours','orders','line','parallel_units','availability','available_machine_hours','utilization'])
else:
    machine_load = (
        load.groupby(['machine_id','machine'], as_index=False)
            .agg(machine_hours=('machine_hours','sum'), labor_hours=('labor_hours','sum'), orders=('order_id','nunique'))
            .merge(machines[['machine_id','line','parallel_units','availability']], on='machine_id', how='left')
    )
    machine_load['available_machine_hours'] = shifts * hours_per_shift * machine_load['parallel_units'] * machine_load['availability']
    machine_load['utilization'] = machine_load['machine_hours'] / machine_load['available_machine_hours'].replace(0, math.nan)
    machine_load['utilization'] = machine_load['utilization'].fillna(0)

total_machine_hours = machine_load['machine_hours'].sum() if not machine_load.empty else 0
estimated_labor_hours = load['labor_hours'].sum() if not load.empty else 0
available_labor_hours = operators * shifts * hours_per_shift
paid_variance = paid_hours - estimated_labor_hours
bottleneck = machine_load.sort_values('utilization', ascending=False).iloc[0] if not machine_load.empty else None

with plan_tab:
    cols = st.columns(6)
    cols[0].metric('Estimated labor hours', f'{estimated_labor_hours:,.1f} h')
    cols[1].metric('Paid labor hours', f'{paid_hours:,.1f} h', f'{paid_variance:+.1f} h vs estimate')
    cols[2].metric('Total machine hours', f'{total_machine_hours:,.1f} h')
    cols[3].metric('Available labor hours', f'{available_labor_hours:,.1f} h')
    cols[4].metric('Orders', f"{orders['order_id'].nunique():,}")
    cols[5].metric('Constraint', bottleneck['machine'] if bottleneck is not None else '—', f"{bottleneck['utilization']:.0%} load" if bottleneck is not None else None)

    labor_ratio = estimated_labor_hours / available_labor_hours if available_labor_hours else 0
    paid_ratio = estimated_labor_hours / paid_hours if paid_hours else 0
    st.markdown('#### Labor comparison')
    c1, c2 = st.columns(2)
    with c1:
        st.progress(min(labor_ratio, 1.0), text=f'Estimated labor demand: {estimated_labor_hours:.1f} / {available_labor_hours:.1f} available hours')
    with c2:
        st.progress(min(paid_ratio, 1.0), text=f'Estimated productive labor: {estimated_labor_hours:.1f} / {paid_hours:.1f} paid hours')

    st.markdown('#### Production metro')
    st.caption('Each station shows estimated machine hours from the current order list. Shared stations appear on multiple lines.')

    station = {int(r.machine_id): r for r in machine_load.itertuples()} if not machine_load.empty else {}
    def node(mid, label):
        r = station.get(mid)
        hours = r.machine_hours if r else 0
        util = r.utilization if r else 0
        status = 'over' if util > 1 else 'near' if util > .85 else 'ok'
        return f'''<div class="station {status}"><div class="dot"></div><div class="station-name">{label}</div><div class="station-hours">{hours:.1f} h</div><div class="station-util">{util:.0%} of available</div></div>'''

    metro_html = f'''
    <style>
      :root {{ color-scheme: light dark; }}
      body {{ margin:0; font-family:Inter,ui-sans-serif,system-ui; background:transparent; color:inherit; }}
      .metro {{ padding:8px 4px 18px; }}
      .line-row {{ display:grid; grid-template-columns:155px 1fr; gap:18px; margin:22px 0; align-items:start; }}
      .line-label {{ font-weight:700; padding-top:22px; }}
      .track {{ display:flex; align-items:flex-start; gap:16px; position:relative; padding:0 8px; flex-wrap:wrap; }}
      .track:before {{ content:''; position:absolute; left:18px; right:18px; top:27px; height:5px; border-radius:999px; background:var(--line); opacity:.75; }}
      .station {{ width:150px; min-height:118px; padding:14px 12px 12px; border:1px solid rgba(128,128,128,.34); border-radius:14px; background:rgba(128,128,128,.07); position:relative; z-index:2; box-sizing:border-box; }}
      .dot {{ width:18px; height:18px; border-radius:50%; border:5px solid var(--line); background:Canvas; margin-bottom:13px; }}
      .station-name {{ font-size:13px; line-height:1.25; font-weight:650; min-height:34px; }}
      .station-hours {{ font-size:22px; font-weight:750; margin-top:7px; }}
      .station-util {{ font-size:11px; opacity:.68; margin-top:2px; }}
      .station.near {{ border-color:#d89a18; }} .station.over {{ border-color:#d34848; }}
      .shared {{ --line:#d49b22; }} .rect {{ --line:#4387f5; }} .round {{ --line:#36b86c; }} .custom {{ --line:#a66be8; }}
      .legend {{ display:flex; flex-wrap:wrap; gap:12px; font-size:12px; opacity:.78; margin:8px 0 0 173px; }}
      @media(max-width:800px) {{ .line-row {{ grid-template-columns:1fr; }} .line-label {{ padding-top:0; }} .track:before {{ display:none; }} .legend {{ margin-left:0; }} }}
    </style>
    <div class="metro">
      <div class="line-row shared"><div class="line-label">Shared cutting</div><div class="track">{node(1,'Fiber Laser #1')}{node(2,'Fiber Laser #2')}</div></div>
      <div class="line-row rect"><div class="line-label">Rectangular line</div><div class="track">{node(6,'Pittsburgh Lock #1')}{node(7,'Pittsburgh / TDC #2')}{node(5,'Hydraulic Pan Brake')}{node(8,'Beader / Crimper')}{node(9,'Duct Seamer')}</div></div>
      <div class="line-row round"><div class="line-label">Round / spiral line</div><div class="track">{node(14,'Spiral Duct Former')}{node(10,'3-Roll Plate Roller #1')}{node(11,'3-Roll Plate Roller #2')}{node(8,'Beader / Crimper')}{node(9,'Duct Seamer')}</div></div>
      <div class="line-row custom"><div class="line-label">Fittings / custom</div><div class="track">{node(15,'Elbow / Gore Former')}{node(16,'Collar Maker')}{node(12,'Mechanical Press')}{node(13,'Ironworker')}{node(5,'Hydraulic Pan Brake')}</div></div>
      <div class="legend"><span>Normal &lt;85%</span><span>Amber 85–100%</span><span>Red &gt;100%</span></div>
    </div>'''
    components.html(metro_html, height=760, scrolling=False)

    st.markdown('#### Machine load')
    if machine_load.empty:
        st.info('Add at least one order to calculate machine load.')
    else:
        display = machine_load.copy()
        display['Machine hours'] = display['machine_hours'].round(1)
        display['Available hours'] = display['available_machine_hours'].round(1)
        display['Utilization'] = (display['utilization'] * 100).round(0).astype(int).astype(str) + '%'
        display['Labor hours'] = display['labor_hours'].round(1)
        st.dataframe(display[['machine','line','orders','Machine hours','Available hours','Utilization','Labor hours']].sort_values('Machine hours', ascending=False), use_container_width=True, hide_index=True)

    st.info('The paid-hours comparison should later separate direct production, setup, material handling, maintenance, rework, breaks, and idle time.')
