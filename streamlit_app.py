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
st.markdown("### 🏗️ Choose the Tower")
st.markdown(
    """
    **Disclaimer:** Please select the Tower that best represents the candidate’s area of expertise.
    This selection will guide how the CV is interpreted and structured.
    """
)

tower_selected = st.radio(
    "Select one option:",
    ["Control_Tower", "SAP", "ORACLE"],
    horizontal=True
)

flavor = st.radio(
    "Select one option:",
    #Dictionary flavors[['Tower'] == tower_selected.lower()]',
    horizontal=True
)

## acá agregamos opción de tildar con el default == None
flavor = None
# perfil = input('Lo que quiere el usuario')
if uploaded_pdf:
    with st.spinner("⏳ Generating PowerPoint..."):
        try:
            # 1️⃣ Extract and structure CV content
            df = generate_one_pager(uploaded_pdf)

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