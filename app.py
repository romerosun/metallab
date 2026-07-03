import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(page_title="Production Dashboard", layout="wide")

BASE = Path(__file__).parent
machines = pd.read_csv(BASE / "machines.csv")
jobs = pd.read_csv(BASE / "jobs.csv")

st.title("Production Dashboard")
st.caption("Mock live view for duct manufacturing")

active_jobs = len(jobs[~jobs["status"].isin(["Complete", "Cancelled"])])
wip = len(jobs[jobs["status"] == "WIP"])
complete_today = len(jobs[jobs["status"] == "Complete"])
overall_util = round(machines["utilization"].mean())
bottleneck = machines.sort_values("utilization", ascending=False).iloc[0]

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Active jobs", active_jobs)
c2.metric("WIP", wip)
c3.metric("Completed today", complete_today)
c4.metric("Overall utilization", f"{overall_util}%")
c5.metric("Bottleneck", bottleneck["machine"])

st.divider()

st.subheader("Factory floor")

status_icon = {"Running": "🟢", "Idle": "🟡", "Down": "🔴", "Maintenance": "⚪"}

line_names = {
    "Line 1": "Rectangular ducts",
    "Line 2": "Round / spiral ducts",
    "Line 3": "Custom / welded parts",
    "Shared": "Shared resources",
}

for line in ["Line 1", "Line 2", "Line 3", "Shared"]:
    st.markdown(f"#### {line}: {line_names[line]}")
    subset = machines[machines["line"] == line]
    cols = st.columns(3)
    for i, (_, m) in enumerate(subset.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"**{status_icon.get(m['status'], '')} {m['machine']}**")
                st.progress(int(m["utilization"]) / 100)
                st.write(f"Utilization: **{m['utilization']}%**")
                st.write(f"Status: **{m['status']}**")
                st.write(f"Current job: **{m['current_job']}**")
    st.write("")

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("Work in progress")
    wip_jobs = jobs[jobs["status"] != "Complete"]
    st.dataframe(
        wip_jobs[["job_id", "product", "line", "current_stage", "progress", "due"]],
        use_container_width=True,
        hide_index=True,
    )

with right:
    st.subheader("Completed")
    done = jobs[jobs["status"] == "Complete"]
    st.dataframe(
        done[["job_id", "product", "line", "completed_at"]],
        use_container_width=True,
        hide_index=True,
    )

st.divider()
st.subheader("Operator update mock")
with st.form("operator_update"):
    job = st.selectbox("Job", jobs["job_id"])
    stage = st.selectbox("New stage", ["Cutting", "Forming", "Beading", "Seaming", "Welding", "Assembly", "QA", "Complete"])
    submitted = st.form_submit_button("Mark update")
    if submitted:
        st.success(f"Mock update saved: {job} → {stage}")

st.caption("Future version: connect this form to a database so operators can update job status from a phone or tablet.")
