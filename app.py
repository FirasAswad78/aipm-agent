import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI IT Project Manager", page_icon="📊")

st.title("AI IT Project Manager")
st.write("Paste project information below and generate a PM status report.")

project_info = st.text_area(
    "Project information",
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
        st.warning("Please paste some project information first.")
    else:
        with st.spinner("Generating report..."):
            response = client.responses.create(
                model="gpt-4.1-mini",
                input=f"""
You are a senior enterprise IT Project Manager.

Analyze the project information and generate a professional PMO-style status report.

Project Information:
{project_info}

Instructions:
- Be concise and executive-friendly
- Use professional PM terminology
- Identify schedule, delivery, vendor, testing, and dependency risks
- Determine overall project health

Return the response in this exact format:

# PM Status Report

## Overall Status
(Green / Amber / Red)

## Executive Summary
(2-4 sentences)

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

            st.subheader("PM Status Report")
            st.markdown(response.output_text)