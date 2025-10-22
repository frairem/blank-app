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

def extract_text_from_pdf(pdf_path):
    """Extract text from all pages of the PDF."""
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()

def generate_sections(cv_text, section_name):
    """Generate one structured section (no bullets, bold keywords)."""
    prompt = f"""
    You are an AI assistant that summarizes a candidate CV into specific structured sections. Do NOT create new sections.
    Write the output in English.
    Return an dictionary where the section is the Key and the its information is the Value.

    SECTIONS TO GENERATE: {section_name}

    Formatting rules:
    - Use line breaks to separate each idea or item. Do NOT use bullet symbols or dashes.
    - Bold **keywords**, skills, or technologies (except for LANGUAGES section).
    - Maintain concise, professional tone.
    - Exclude candidate name, company names, institutions, and dates.
    - Assume Graphik 9 font style.

    Section details:
    - PROFILE OVERVIEW: One concise paragraph summarizing the candidate’s experience, skills, expertise, and key achievements. No names or languages.
    - PROFESSIONAL EDUCATION: List only degree names, separated by line breaks. Do NOT repeat information. Do NOT mention High School information.
    - INDUSTRY EXPERIENCE: Line-separated list of industries mapped to Accenture taxonomy:
        Communications, Media & Technology → Communications, Media & Entertainment, High Tech, Software & Platforms
        Financial Services → Banking, Capital Markets, Insurance
        Health & Public Service → Health, Public Service
        Products → Consumer Goods & Services, Life Sciences, Retail, Industrial, Automotive, Travel
        Resources → Energy, Chemicals, Utilities, Natural Resources
    - FUNCTIONAL EXPERIENCE: Line-separated list of functional expertise or focus areas.
    - CERTIFICATIONS/TRAINING: Line-separated list of certification or training program names.
    - LANGUAGES: List only the languages and proficiency levels (e.g., English B2, Spanish Native). Each on a separate line. No bold or bullets.

    Candidate CV:
    {cv_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",  # You can upgrade to gpt-4o or gpt-5
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def generate_roles(cv_text):
    """Generate up to 4 roles, formatted with bold keywords and line breaks only."""
    prompt = f"""
    You are an AI assistant that extracts and rewrites a candidate’s RELEVANT EXPERIENCE into up to 4 roles.

    Formatting and style:
    - Each role must have this structure:
        Role Title
        Responsibility or achievement #1
        Responsibility or achievement #2
        ...
    - Use **bold** for key words, skills, tools, or technologies.
    - Do NOT use bullets or dashes — only separate lines with line breaks.
    - Exclude company names, institutions, and dates.
    - Keep concise, professional English tone.
    - Maximum of 4 roles. If fewer exist, only return those.

    Candidate CV:
    {cv_text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    text = response.choices[0].message.content.strip()

    # Split each role block by double line breaks
    roles = [r.strip() for r in text.split("\n\n") if r.strip()]
    return roles[:4]

def generate_one_pager(cv_path, output_path="one_pager_summary.xlsx"):
    """Generate all sections and export as Excel file."""
    cv_text = extract_text_from_pdf(cv_path)

    sections = [
        "PROFILE OVERVIEW",
        "PROFESSIONAL EDUCATION",
        "INDUSTRY EXPERIENCE",
        "FUNCTIONAL EXPERIENCE",
        "CERTIFICATIONS/TRAINING",
        "LANGUAGES"
    ]

    # Generate fixed sections
    print("🔹 Generating: SECTIONS...")
    sections = generate_sections(cv_text, sections)
    response_dic = json.loads(sections)

    # Generate dynamic roles
    print("🔹 Generating: RELEVANT EXPERIENCE (Roles)...")
    roles = generate_roles(cv_text)
    for i, element in enumerate(roles):
        response_dic[f"Role_{i+1}"] = element

    # Create DataFrame and export
    df = pd.DataFrame(list(response_dic.items()), columns=["section_name", "output"])
    df.to_excel(output_path, index=False)
    print(f"\n✅ One Pager Excel file created successfully: {output_path}")


if __name__ == "__main__":
    input_dir = "data/input"
    output_dir = "data/output"
    os.makedirs(output_dir, exist_ok=True)

for file_name in os.listdir(input_dir):
    if file_name.lower().endswith(".pdf"):
        pdf_path = os.path.join(input_dir, file_name)
        output_path = os.path.join(output_dir, file_name.replace(".pdf", "_one_pager.xlsx"))
        generate_one_pager(pdf_path, output_path)