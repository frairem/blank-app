import streamlit as st
import pdfplumber
import pandas as pd
import io
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

# --------------------
# Load environment and API key
# --------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# --------------------
# Helper functions
# --------------------
def extract_text_from_pdf(pdf_file):
    """Extract text from uploaded PDF file (in-memory)."""
    text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def generate_sections(cv_text, section_name):
    """Generate one structured section (no bullets, bold keywords)."""
    prompt = f"""
    You are an AI assistant that summarizes a candidate CV into specific structured sections. 
    Do NOT create new sections. Write the output in English.
    Return a JSON dictionary where the section is the Key and the information is the Value.

    SECTIONS TO GENERATE: {section_name}

    Formatting rules:
    - Use line breaks to separate each idea or item (no bullets).
    - Bold **keywords**, skills, or technologies (except for LANGUAGES section).
    - Maintain concise, professional tone.
    - Exclude candidate name, company names, institutions, and dates.
    - Assume Graphik 9 font style.

    Section details:
    - NAME: The name of the candidate. 
    - TOWER: Which tower they belong to. It can only be one of three: SAP ARIBA, SAP S/4HANA or CONTROL TOWER
    - PROFILE OVERVIEW: One concise paragraph summarizing the candidate’s experience, skills, expertise, and key achievements.
    - PROFESSIONAL EDUCATION: List only degree names, separated by line breaks.
    - INDUSTRY EXPERIENCE: Line-separated list of industries mapped to Accenture taxonomy:
        Communications, Media & Technology → Communications, Media & Entertainment, High Tech, Software & Platforms
        Financial Services → Banking, Capital Markets, Insurance
        Health & Public Service → Health, Public Service
        Products → Consumer Goods & Services, Life Sciences, Retail, Industrial, Automotive, Travel
        Resources → Energy, Chemicals, Utilities, Natural Resources
    - FUNCTIONAL EXPERIENCE: Line-separated list of functional expertise or focus areas.
    - CERTIFICATIONS/TRAINING: Line-separated list of certification or training program names.
    - LANGUAGES: List only the languages and proficiency levels (e.g., English B2, Spanish Native).
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt + "\n\nCandidate CV:\n" + cv_text}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()


def generate_roles(cv_text):
    """Generate up to 4 roles, formatted with bold keywords and line breaks."""
    prompt = f"""
    You are an AI assistant that extracts and rewrites a candidate’s RELEVANT EXPERIENCE into up to 4 roles.

    Formatting:
    - Each role:
        Role Title
        Responsibility #1
        Responsibility #2
    - Use **bold** for key words or technologies.
    - Do NOT use bullets or dashes.
    - Exclude company names, institutions, and dates.
    - Keep concise, professional English tone.
    - Max 4 roles.

    Candidate CV:
    {cv_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    text = response.choices[0].message.content.strip()
    roles = [r.strip() for r in text.split("\n\n") if r.strip()]
    return roles[:4]


def generate_one_pager(cv_file):
    """Generate the Excel as bytes (in-memory)."""
    cv_text = extract_text_from_pdf(cv_file)

    sections = [
        "NAME",
        "TOWER",
        "PROFILE OVERVIEW",
        "PROFESSIONAL EDUCATION",
        "INDUSTRY EXPERIENCE",
        "FUNCTIONAL EXPERIENCE",
        "CERTIFICATIONS/TRAINING",
        "LANGUAGES"
    ]

    # Fixed sections
    sections_json = generate_sections(cv_text, sections)
    response_dic = json.loads(sections_json)

    # Add roles
    roles = generate_roles(cv_text)
    for i, element in enumerate(roles):
        response_dic[f"Role_{i+1}"] = element

    # Build DataFrame
    df = pd.DataFrame(list(response_dic.items()), columns=["section_name", "output"])

    # Save Excel to memory
    excel_bytes = io.BytesIO()
    df.to_excel(excel_bytes, index=False)
    excel_bytes.seek(0)
    return excel_bytes


# --------------------
# Streamlit UI
# --------------------
st.title("📄 CV One Pager Generator")

uploaded_pdf = st.file_uploader("Upload a CV in PDF format", type=["pdf"])

if uploaded_pdf:
    with st.spinner("⏳ Generating one-pager summary..."):
        try:
            excel_data = generate_one_pager(uploaded_pdf)
            st.success("✅ Excel file generated successfully!")
            st.download_button(
                label="💾 Download Excel",
                data=excel_data,
                file_name="one_pager_summary.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except Exception as e:
            st.error(f"❌ Error: {e}")
