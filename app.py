import os
import streamlit as st
from openai import OpenAI
from sqlalchemy import create_engine, text

api_key = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

client = OpenAI(api_key=api_key)
engine = create_engine(DATABASE_URL)

st.set_page_config(page_title="AI IT Project Manager", page_icon="📊")

# Create table if it does not exist
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

st.title("AI IT Project Manager")
st.write("Paste project information below and generate a PM status report.")

project_name = st.text_input("Project Name", placeholder="Example: Network Upgrade Project")

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

if st.button("Generate PM Report"):

    if not project_name.strip():
        st.warning("Please enter a project name.")

    elif not project_info.strip():
        st.warning("Please enter project information.")

    else:
        with st.spinner("Generating PM report..."):

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=f"""
You are a senior enterprise IT Project Manager.

Analyze the project information below and generate a professional PM status report.

Project Name:
{project_name}

Project Information:
{project_info}

Return:

# PM Status Report

## Overall Status
(Green / Amber / Red)

## Executive Summary

## Key Risks
- bullet points

## Blockers
- bullet points

## Recommended Actions
1. numbered list

## Next Steps
1. numbered list
"""
            )

            ai_report = response.output_text

            if "Red" in ai_report:
                overall_status = "Red"
            elif "Amber" in ai_report:
                overall_status = "Amber"
            elif "Green" in ai_report:
                overall_status = "Green"
            else:
                overall_status = "Unknown"

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

            st.success("PM report saved to database.")
            st.markdown(ai_report)

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
            f"**{report.project_name}** | Status: **{report.overall_status}** | Created: {report.created_at}"
        )
else:
    st.info("No saved reports yet.")