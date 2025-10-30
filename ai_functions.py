import pdfplumber
import pandas as pd
import io
import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key = api_key)

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
    - Maintain concise, professional tone.
    - Exclude candidate name, company names, institutions, and dates.
    - Assume Graphik 9 font style.

    Section details:
    - NAME: Candidate’s name.
    - TOWER: Choose ONLY ONE → SAP ARIBA, SAP S/4HANA, or CONTROL TOWER.
        • CONTROL TOWER → mentions SQL, Python, R, Power BI, Tableau, Looker, Alteryx, ETL, analytics, ML, automation, software development or data-driven tasks.
        • SAP S/4HANA → SAP modules (FI, CO, MM, SD, PP, PM, etc.), Fiori, ABAP, or S/4HANA implementations.
        • SAP ARIBA → procurement, sourcing, supplier, contracts, catalogs, SRM, or Ariba modules.
        • If both SAP and data skills appear, pick CONTROL TOWER only if analytics/data focus is dominant.
    - PROFILE OVERVIEW: One concise paragraph summarizing the candidate’s experience, skills, expertise, and key achievements. No names or languages. Bold **keywords**.
    - PROFESSIONAL EDUCATION: List only degree names, separated by line breaks. Do NOT repeat information. Do NOT mention High School information.
    - INDUSTRY EXPERIENCE: Line-separated list of industries mapped to Accenture taxonomy. Should only be one cell, don't create Industry per line. Map industries as follows:
        Communications, Media & Technology → Communications, Media & Entertainment, High Tech, Software & Platforms
        Financial Services → Banking, Capital Markets, Insurance
        Health & Public Service → Health, Public Service
        Products → Consumer Goods & Services, Life Sciences, Retail, Industrial, Automotive, Travel
        Resources → Energy, Chemicals, Utilities, Natural Resources
    - FUNCTIONAL EXPERIENCE: Line-separated list of functional expertise or focus areas.
        Each line should be short, max 3-5 words per line (~150 characters total for all lines as maximum).
        Only include key skills, modules, processes, or tools.
        Do NOT write sentences, achievements, or explanations.
        Example: "SAP FI/MM/PM configuration, Fiori interfaces, UAT testing, Process automation, Master data management"
    - CERTIFICATIONS/TRAINING: Line-separated list of certification or training program names.
    - LANGUAGES: List only the languages and proficiency levels (e.g., English B2, Spanish Native). Each on a separate line. No bold or bullets. Use only the Common European Framework of Reference for Languages (A1, A2, B1, B2, C1, C2).

    Candidate CV:
    {cv_text}
    """

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt, "reasoning-effort": "medium"}],
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

    - But look similar in structure but more detailed to this example. Never copy anything but the structure and always use at least 3 or more lines per role:
        Data Analyst
        Led the **development** of **data pipelines** using **Python** and **SQL** to streamline data processing.
        Collaborated with **cross-functional teams** to implement **data visualization** solutions using **Power BI and Tableau**, enhancing decision-making capabilities.
        Implemented **statistical analysis** and **machine learning** models using **R** and Python to derive actionable insights from large datasets, improving business strategies.

    - Each role must have 3-4 lines, maximum 400 characters per line.
    - Focus on responsibilities and achievements that highlight skills, tools, or technologies.
    - Bold **keywords**, **skills**, or **technologies** only.
    - Keep output concise and professional English tone.
    - Do NOT use bullets or dashes — only separate lines with line breaks.
    - Exclude company names, institutions, and dates.
    - Maximum of 4 roles. If fewer exist, only return those.

    Candidate CV:
    {cv_text}
    """

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": prompt, "reasoning-effort": "medium"}],
    )

    text = response.choices[0].message.content.strip()

    # Split each role block by double line breaks
    roles = [r.strip() for r in text.split("\n\n") if r.strip()]
    return roles[:4]

def generate_one_pager(cv_path, output_path="one_pager_summary.xlsx"):
    """Generate all sections and return DataFrame."""
    try:
        cv_text = extract_text_from_pdf(cv_path)

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

        # Generate fixed sections
        print("🔹 Generating: SECTIONS...")
        sections = generate_sections(cv_text, sections)
        response_dic = json.loads(sections)

        # Generate dynamic roles
        print("🔹 Generating: RELEVANT EXPERIENCE (Roles)...")
        roles = generate_roles(cv_text)
        for i, element in enumerate(roles):
            response_dic[f"Role_{i+1}"] = element

        # Create and return DataFrame
        df = pd.DataFrame(list(response_dic.items()), columns=["section_name", "output"])
        
        # ✅ Save to Excel
        df.to_excel(output_path, index=False)
        print(f"✅ One-pager saved at: {os.path.abspath(output_path)}")
        
        return df

    except Exception as e:
        print(f"Error generating one pager: {str(e)}")
        raise