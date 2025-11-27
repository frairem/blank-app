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
from PIL import Image

# --------------------
# Custom CSS for Accenture Branding
# --------------------
def inject_custom_css():
    st.markdown("""
        <style>
        /* Main background and text colors */
        .stApp {
            background-color: #000000;
            color: #FFFFFF;
        }
        
        /* Headers styling */
        h1, h2, h3 {
            color: #A100FF !important;  /* Accenture Purple */
            font-family: 'Arial', sans-serif;
            font-weight: 600;
        }
        
        /* Main title with gradient */
        .main-title {
            background: linear-gradient(45deg, #A100FF, #00B2FF);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 2.5rem !important;
            font-weight: 700 !important;
            text-align: center;
            margin-bottom: 2rem !important;
        }
        
        /* Card-like containers for sections */
        .section-container {
            background-color: #1A1A1A;
            border-radius: 10px;
            padding: 1.5rem;
            margin: 1rem 0;
            border-left: 4px solid #A100FF;
        }
        
        /* File uploader styling */
        .stFileUploader > div {
            background-color: #2D2D2D !important;
            border: 2px dashed #A100FF !important;
            border-radius: 10px !important;
        }
        
        /* Radio button styling */
        .stRadio > div {
            background-color: #2D2D2D;
            padding: 1rem;
            border-radius: 8px;
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(45deg, #A100FF, #00B2FF) !important;
            color: white !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 0.75rem 2rem !important;
            font-weight: 600 !important;
            font-size: 1.1rem !important;
            width: 100%;
            margin-top: 1rem;
        }
        
        .stButton > button:hover {
            background: linear-gradient(45deg, #8A00E6, #0099E6) !important;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        /* Success message styling */
        .stSuccess {
            background-color: #1A3A1A !important;
            border: 1px solid #00CC00 !important;
            border-radius: 8px !important;
        }
        
        /* Warning and info messages */
        .stWarning, .stInfo {
            background-color: #2D2D2D !important;
            border-radius: 8px !important;
            border-left: 4px solid #FFB300 !important;
        }
        
        /* Download button specific styling */
        .download-btn > button {
            background: linear-gradient(45deg, #00B2FF, #00CC88) !important;
            margin-top: 0.5rem !important;
        }
        
        /* Logo container */
        .logo-container {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
            padding: 1rem;
            background-color: #000000;
            border-bottom: 2px solid #A100FF;
        }
        
        /* Logo styling */
        .logo-img {
            height: 40px;
            margin-right: 15px;
        }
        
        /* Header text next to logo */
        .header-text {
            flex-grow: 1;
        }
        
        /* Progress spinner color */
        .stSpinner > div {
            border-color: #A100FF !important;
        }
        
        /* Dataframe styling in expander */
        .dataframe {
            background-color: #2D2D2D !important;
            color: white !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #2D2D2D !important;
            color: white !important;
            border-radius: 8px !important;
        }
        
        /* Hide default Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        header {visibility: hidden;}
        
        </style>
    """, unsafe_allow_html=True)

# --------------------
# Initialize App
# --------------------
inject_custom_css()

# Logo and Header
col1, col2 = st.columns([1, 4])
with col1:
    try:
        # Load and display Accenture logo
        logo = Image.open("accenture-logo.png")
        st.image(logo, width=120)
    except:
        # Fallback if logo file is not found
        st.markdown("""
            <div style='color: #A100FF; font-weight: bold; font-size: 1.5rem;'>
                ACCENTURE
            </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="header-text">
            <h1 style='margin:0; color: #A100FF !important;'>📄 CV One Pager Generator</h1>
            <p style='margin:0; color: #CCCCCC; font-size: 1rem;'>AI-Powered CV Processing Solution</p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# --------------------
# Main Content
# --------------------

# File Upload Section
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.markdown("### 📁 Upload CV")
uploaded_pdf = st.file_uploader("Upload a CV in PDF format", type=["pdf"], help="Please upload the candidate's CV in PDF format")
st.markdown('</div>', unsafe_allow_html=True)

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

# Tower Selection
st.markdown('<div class="section-container">', unsafe_allow_html=True)
st.markdown("### 🏗️ Choose the Tower")
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
st.markdown('</div>', unsafe_allow_html=True)

# Flavor Selection (only shown when tower is selected)
if st.session_state.tower_selected:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    flavor_options = tower_flavor_df[st.session_state.tower_selected]
    
    st.markdown("### 🎯 Select the Candidate Profile")
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
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------
# Generate Section
# --------------------
if uploaded_pdf and st.session_state.tower_selected:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown("### 🚀 Generate One-Pager")
    
    # Add a generate button for better UX
    if st.button("Generate One-Pager", type="primary"):
        with st.spinner("⏳ Processing CV and generating PowerPoint..."):
            try:
                # 1️⃣ Extract and structure CV content
                df = generate_one_pager(
                    cv_path=uploaded_pdf, 
                    tower_selected=st.session_state.tower_selected, 
                    flavor=flavor
                )

                # Show preview of the data
                with st.expander("📊 Preview Extracted Data"):
                    st.dataframe(df)

                # 2️⃣ Generate the PowerPoint file
                pptx_path = populate_pptx(df)

                # 3️⃣ Read file bytes for download
                with open(pptx_path, "rb") as f:
                    pptx_bytes = f.read()

                st.success("✅ One-pager generated successfully!")
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.metric("Tower Selected", st.session_state.tower_selected)
                with col2:
                    profile_display = flavor if flavor else "None (Original)"
                    st.metric("Profile", profile_display)

                # 4️⃣ Provide download button
                st.markdown('<div class="download-btn">', unsafe_allow_html=True)
                st.download_button(
                    label="📊 Download OnePager",
                    data=pptx_bytes,
                    file_name="OnePager.pptx",
                    mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                )
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"❌ Error while generating PowerPoint: {str(e)}")
                st.info("💡 Tip: Check if the PDF is readable and contains text content.")
    st.markdown('</div>', unsafe_allow_html=True)
    
elif uploaded_pdf and not st.session_state.tower_selected:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.warning("⚠️ Please select a Tower to generate the one-pager.")
    st.markdown('</div>', unsafe_allow_html=True)
elif not uploaded_pdf:
    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.info("📁 Please upload a PDF file to get started.")
    st.markdown('</div>', unsafe_allow_html=True)

# --------------------
# Footer
# --------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; font-size: 0.9rem;'>
        <img src='https://www.accenture.com/favicon.ico' width='16' style='vertical-align: middle; margin-right: 8px;'>
        Powered by Accenture AI • Professional CV Processing Solution
    </div>
    """, 
    unsafe_allow_html=True
)