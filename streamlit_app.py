import streamlit as st
import pdfplumber
import pandas as pd
import io
import json
from openai import OpenAI
import os
from dotenv import load_dotenv
from cv_process_sort_gen import *
from populate_pptx import *
from pptx import Presentation

# --------------------
# Streamlit UI
# --------------------
st.title("📄 CV One Pager Generator")

uploaded_pdf = st.file_uploader("Upload a CV in PDF format", type=["pdf"])

# --------------------
# Choose Tower Section
# --------------------
file_name = 'tower_flavor.json' 

with open(file_name, 'r') as file:
    tower_flavor_df = json.load(file)



st.markdown("🏗️ Choose the Tower")
st.markdown(
    """
    Select the Tower that best represents the candidate’s area of expertise.
    This selection will guide how the CV is interpreted and structured.
    """
)
tower_options = list(tower_flavor_df.keys()) + ["None"]
tower_selected = st.radio(
    "Tower:",
    tower_options,
    horizontal=True
)
tower_selected = None if tower_selected == "None" else tower_selected

flavor_options = tower_flavor_df[tower_selected] + ["None"] if tower_selected else ["None"]
st.markdown("🎯 Select the Candidate Profile")
st.markdown(
    "This selection will refine the CV to better match the candidate’s target role based on the selected tower. "
    "Choose **None** if you want to keep the CV in its original form."
)
flavor = st.radio(
    "Profile:",
    flavor_options,
    horizontal=True
)
flavor = None if flavor == "None" else flavor

# --------------------
if uploaded_pdf:
    with st.spinner("⏳ Generating PowerPoint..."):
        try:
            # 1️⃣ Extract and structure CV content
            df = generate_one_pager(cv_path = uploaded_pdf, tower_selected = tower_selected, flavor = flavor)

            # (optional: save CSV if you want for debugging)
            # df.to_csv("data/output/temp_summary.csv", index=False)

            # 2️⃣ Generate the PowerPoint file
            pptx_path = populate_pptx(df)  # returns path like "data/output/output.pptx"

            # 3️⃣ Read file bytes for download
            with open(pptx_path, "rb") as f:
                pptx_bytes = f.read()

            st.success("✅ One-pager generated successfully!")

            # 4️⃣ Provide download button
            st.download_button(
                label="📊 Download OnePager",
                data=pptx_bytes,
                file_name="OnePager.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            )

        except Exception as e:
            st.error(f"❌ Error while generating PowerPoint: {e}")