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

# Initialize session state for tower and flavor
if 'tower_selected' not in st.session_state:
    st.session_state.tower_selected = None
if 'flavor_selected' not in st.session_state:
    st.session_state.flavor_selected = None

st.markdown("🏗️ Choose the Tower")
st.markdown(
    """
    Select the Tower that best represents the candidate's area of expertise.
    This selection will guide how the CV is interpreted and structured.
    """
)

tower_options = list(tower_flavor_df.keys())
tower_selected = st.radio(
    "Tower:",
    tower_options,
    horizontal=True,
    index=None,
    key="tower_radio"
)

# Update session state
if tower_selected != st.session_state.tower_selected:
    st.session_state.tower_selected = tower_selected
    st.session_state.flavor_selected = None  # Reset flavor when tower changes

# Only show flavor selection if a tower is selected
if st.session_state.tower_selected:
    flavor_options = tower_flavor_df[st.session_state.tower_selected]
    
    st.markdown("🎯 Select the Candidate Profile")
    st.markdown(
        "This selection will refine the CV to better match the candidate's target role based on the selected tower. "
        "**Choose 'None' if you prefer to keep the CV in its original form without specific role refinement.**"
    )
    
    # Add "None" option to flavor options
    flavor_options_with_none = ["None"] + flavor_options
    
    flavor = st.radio(
        "Profile:",
        flavor_options_with_none,
        horizontal=True,
        index=0,  # Default to "None"
        key="flavor_radio"
    )
    
    # Update session state
    if flavor != st.session_state.flavor_selected:
        st.session_state.flavor_selected = flavor
    
    # Convert "None" to actual None
    flavor = None if flavor == "None" else flavor

# --------------------
# Process PDF only when all conditions are met
if uploaded_pdf and st.session_state.tower_selected:
    # Add a generate button for better UX
    if st.button("🚀 Generate One-Pager", type="primary"):
        with st.spinner("⏳ Generating PowerPoint..."):
            try:
                # 1️⃣ Extract and structure CV content
                df = generate_one_pager(
                    cv_path=uploaded_pdf, 
                    tower_selected=st.session_state.tower_selected, 
                    flavor=flavor
                )

                # (optional: show preview of the data)
                with st.expander("📊 Preview Extracted Data"):
                    st.dataframe(df)

                # 2️⃣ Generate the PowerPoint file
                pptx_path = populate_pptx(df)

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
                st.error(f"❌ Error while generating PowerPoint: {str(e)}")
                st.info("💡 Tip: Check if the PDF is readable and contains text content.")
elif uploaded_pdf and not st.session_state.tower_selected:
    st.warning("⚠️ Please select a Tower to generate the one-pager.")
elif not uploaded_pdf:
    st.info("📁 Please upload a PDF file to get started.")