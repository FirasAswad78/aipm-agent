import os
from typing import TypedDict

import streamlit as st
from openai import OpenAI
from sqlalchemy import create_engine, text
from langgraph.graph import StateGraph, START, END


# -----------------------------
# Environment Variables
# -----------------------------
api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

client = OpenAI(api_key=api_key)
engine = create_engine(DATABASE_URL)


# -----------------------------
# Streamlit Page Setup
# -----------------------------
st.set_page_config(
    page_title="AI IT Project Manager",
    page_icon="📊"
)


# -----------------------------
# Database Setup
# -----------------------------
with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS pm_reports (
            id SERIAL PRIMARY KEY,
            project_name TEXT,
            project_info TEXT,
            ai_report TEXT,
            overall_status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """))
    connection.commit()


# -----------------------------
# LangGraph State
# -----------------------------
class PMState(TypedDict):
    project_name: str
    project_info: str
    risks: str
    blockers: str
    status: str
    final_report: str


# -----------------------------
# Agent 1: Risk Agent
# -----------------------------
def risk_agent(state: PMState):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
You are a senior IT project risk analyst.

Identify the key project risks from the project information below.

Project Name:
{state["project_name"]}

Project Information:
{state["project_info"]}

Return only clear bullet points.
"""
    )

    return {"risks": response.output_text}


# -----------------------------
# Agent 2: Blocker Agent
# -----------------------------
def blocker_agent(state: PMState):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
You are an IT delivery blocker analyst.

Identify the current active blockers from the project information below.

Project Name:
{state["project_name"]}

Project Information:
{state["project_info"]}

Return only clear bullet points.
"""
    )

    return {"blockers": response.output_text}


# -----------------------------
# Agent 3: Status Agent
# -----------------------------
def status_agent(state: PMState):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
You are a PMO project status evaluator.

Determine the overall project status as one of:

Green
Amber
Red

Use the project information, risks, and blockers.

Project Name:
{state["project_name"]}

Project Information:
{state["project_info"]}

Risks:
{state["risks"]}

Blockers:
{state["blockers"]}

Return only one word:
Green, Amber, or Red.
"""
    )

    status = response.output_text.strip()

    if "Red" in status:
        status = "Red"
    elif "Amber" in status:
        status = "Amber"
    elif "Green" in status:
        status = "Green"
    else:
        status = "Unknown"

    return {"status": status}


# -----------------------------
# Agent 4: Report Agent
# -----------------------------
def report_agent(state: PMState):
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=f"""
You are a senior enterprise IT Project Manager.

Create a professional PMO-style project status report.

Project Name:
{state["project_name"]}

Project Information:
{state["project_info"]}

Identified Risks:
{state["risks"]}

Identified Blockers:
{state["blockers"]}

Overall Status:
{state["status"]}

Return the report in this exact format:

# PM Status Report

## Overall Status
{state["status"]}

## Executive Summary
2-4 professional sentences.

## Key Risks
Use bullet points.

## Blockers
Use bullet points.

## Recommended Actions
Use numbered actions.

## Next Steps
Use numbered next steps.
"""
    )

    return {"final_report": response.output_text}


# -----------------------------
# Build LangGraph Workflow
# -----------------------------
workflow = StateGraph(PMState)

workflow.add_node("risk_agent", risk_agent)
workflow.add_node("blocker_agent", blocker_agent)
workflow.add_node("status_agent", status_agent)
workflow.add_node("report_agent", report_agent)

workflow.add_edge(START, "risk_agent")
workflow.add_edge("risk_agent", "blocker_agent")
workflow.add_edge("blocker_agent", "status_agent")
workflow.add_edge("status_agent", "report_agent")
workflow.add_edge("report_agent", END)

pm_graph = workflow.compile()


# -----------------------------
# Streamlit UI
# -----------------------------
st.title("AI IT Project Manager")
st.write("Generate PM status reports using a LangGraph multi-agent workflow.")

st.markdown("""
### Workflow

Project Input  
↓  
Risk Agent  
↓  
Blocker Agent  
↓  
Status Agent  
↓  
Report Agent  
↓  
PostgreSQL Save
""")

project_name = st.text_input(
    "Project Name",
    placeholder="Example: Network Upgrade Project"
)

project_info = st.text_area(
    "Project Information",
    height=250,
    placeholder="""Example:
Tasks:
- Firewall setup blocked
- Testing not started
- Routers installed

Deadline: July 30"""
)


# -----------------------------
# Generate Report
# -----------------------------
if st.button("Generate PM Report"):

    if not project_name.strip():
        st.warning("Please enter a project name.")

    elif not project_info.strip():
        st.warning("Please enter project information.")

    else:
        with st.spinner("Running LangGraph PM agents..."):

            result = pm_graph.invoke({
                "project_name": project_name,
                "project_info": project_info,
                "risks": "",
                "blockers": "",
                "status": "",
                "final_report": ""
            })

            ai_report = result["final_report"]
            overall_status = result["status"]

            with engine.connect() as connection:
                connection.execute(
                    text("""
                        INSERT INTO pm_reports
                        (project_name, project_info, ai_report, overall_status)
                        VALUES (:project_name, :project_info, :ai_report, :overall_status)
                    """),
                    {
                        "project_name": project_name,
                        "project_info": project_info,
                        "ai_report": ai_report,
                        "overall_status": overall_status
                    }
                )
                connection.commit()

            st.success("PM report generated and saved to PostgreSQL.")

            st.markdown(ai_report)


# -----------------------------
# Saved Reports
# -----------------------------
st.divider()

st.subheader("Saved PM Reports")

with engine.connect() as connection:
    reports = connection.execute(text("""
        SELECT id, project_name, overall_status, created_at
        FROM pm_reports
        ORDER BY created_at DESC
        LIMIT 10
    """)).fetchall()

if reports:
    for report in reports:
        st.write(
            f"**{report.project_name}** | "
            f"Status: **{report.overall_status}** | "
            f"Created: {report.created_at}"
        )
else:
    st.info("No saved reports yet.")