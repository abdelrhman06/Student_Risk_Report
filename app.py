import streamlit as st
import pandas as pd
import numpy as np

self_paced = pd.read_excel("Self_Paced_progress.xlsx")
connect = pd.read_excel("Connect_session_attendance.xlsx")
physical = pd.read_excel("Summer_intake_-PS_Progress.xlsx")

connect_start = pd.to_datetime("2025-02-07")
connect_end = pd.to_datetime("2025-03-22")
physical_start = pd.to_datetime("2025-03-07")
physical_end = pd.to_datetime("2025-03-08")

connect["Event Date"] = pd.to_datetime(connect["Event Date"], errors="coerce")
physical["Event Date"] = pd.to_datetime(physical["Event Date"], errors="coerce")

connect_filtered = connect[
    (connect["Event Attendance (Status)"] == "Present") &
    (connect["Event Date"] >= connect_start) & 
    (connect["Event Date"] <= connect_end)
]
connect_count = connect_filtered.groupby("Username").size().reset_index(name="Connect Present Count")

physical_filtered = physical[
    (physical["Event Attendance (Status)"] == "Present") &
    (physical["Event Date"] >= physical_start) & 
    (physical["Event Date"] <= physical_end)
]
physical_count = physical_filtered.groupby("Username").size().reset_index(name="Physical Present Count")

self_paced["Course Progress (Formatted)"] = self_paced["Course Progress (%)"].apply(lambda x: float(str(x).replace("%", "").strip()) / 100 if pd.notnull(x) else 0)

bins = [0, 0.56, 0.62, 0.68, 0.75, 0.81, 0.87, 0.93, 1.001]
labels = ["W-9", "W-10", "W-11", "W-12", "W-13", "W-14", "W-15", "W-16"]
self_paced["Current Week Accurate"] = pd.cut(self_paced["Course Progress (Formatted)"], bins=bins, labels=labels, include_lowest=True)

merged = self_paced.merge(connect_count, on="Username", how="left")
merged = merged.merge(physical_count, on="Username", how="left")

merged["Connect Present Count"] = merged["Connect Present Count"].fillna(0)
merged["Physical Present Count"] = merged["Physical Present Count"].fillna(0)

merged["Overall Progress"] = merged.apply(
    lambda row: "At Risk" if (
        row["Course Progress (Formatted)"] < 0.87 or
        row["Physical Present Count"] < 1 or
        row["Connect Present Count"] < 5
    ) else "Pass", axis=1
)

def issue_type(row):
    issues = []
    if row["Course Progress (Formatted)"] < 0.87:
        issues.append("Self-paced")
    if row["Physical Present Count"] < 1:
        issues.append("Physical session")
    if row["Connect Present Count"] < 5:
        issues.append("Connect session")
    return ", ".join(issues) if issues else ""

merged["Overall Issue"] = merged.apply(issue_type, axis=1)

summary = {}
for i in range(2, 8):
    summary[f"Connect {i}"] = ((merged["Connect Present Count"] == i).sum())
for i in range(2):
    summary[f"Physical {i}"] = ((merged["Physical Present Count"] == i).sum())
for label in labels:
    summary[str(label)] = (self_paced["Current Week Accurate"] == label).sum()

summary["Total students"] = len(merged)
summary["Pass"] = (merged["Overall Progress"] == "Pass").sum()
summary["At Risk"] = (merged["Overall Progress"] == "At Risk").sum()
summary["Completion rate"] = round((merged["Overall Progress"] == "Pass").sum() / len(merged) * 100, 2)

for reason in merged["Overall Issue"].unique():
    if pd.notnull(reason):
        summary[reason] = (merged["Overall Issue"] == reason).sum()

summary_df = pd.DataFrame([summary]).T.reset_index().rename(columns={"index": "Category", 0: "Count"})

st.title("Student Risk Dashboard")
st.subheader("📊 Detailed Student Progress")
st.dataframe(merged)

st.subheader("📈 Summary Report")
st.dataframe(summary_df)
