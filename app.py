import os
import streamlit as st
from openai import OpenAI
from sqlalchemy import create_engine, text
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key)
DATABASE_URL = os.getenv("DATABASE_URL")

try:
    engine = create_engine(DATABASE_URL)

    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        st.success("Database connection successful!")

except Exception as e:
    st.error(f"Database connection failed: {e}")


st.set_page_config(
    page_title="AI IT Project Manager",
    page_icon="📊"
)

st.title("AI IT Project Manager")

st.write(
    "Paste project information below and generate a PM status report."
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

if st.button("Generate PM Report"):

    if not project_info.strip():
        st.warning("Please enter project information.")

    else:

        with st.spinner("Generating PM report..."):

            response = client.responses.create(
                model="gpt-4.1-mini",
                input=f"""
You are a senior enterprise IT Project Manager.

Analyze the project information below and generate a professional PM status report.

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

            st.markdown(response.output_text)