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
    - TOWER: Choose ONLY ONE → SAP ARIBA, SAP S/4HANA, CONTROL TOWER or ORACLE.
        • CONTROL TOWER → mentions SQL, Python, R, Power BI, Tableau, Looker, Alteryx, ETL, analytics, ML, automation, software development or data-driven tasks.
        • SAP S/4HANA → SAP modules (FI, CO, MM, SD, PP, PM, etc.), Fiori, ABAP, or S/4HANA implementations.
        • SAP ARIBA → procurement, sourcing, supplier, contracts, catalogs, SRM, or Ariba modules.
        • ORACLE → Oracle ERP Cloud, Oracle E-Business Suite (EBS), Oracle Fusion, or tasks related to financials, procurement, supply chain, or HCM using Oracle technologies.
        • If both SAP and data skills appear, pick CONTROL TOWER only if analytics/data focus is dominant.
    - PROFILE OVERVIEW: One concise paragraph summarizing the candidate’s experience, skills, expertise, and key achievements. No names or languages. Bold **keywords**.
    - PROFESSIONAL EDUCATION: List university-level degrees (e.g., Bachelor’s or Master’s), separated by line breaks. Do NOT repeat information. Do NOT mention High School information.
    - INDUSTRY EXPERIENCE: Line-separated list of sub-industries mapped to Accenture taxonomy (https://www.accenture.com/us-en/services). 
        This should be only one sub-industry per line. Map sub-industries as follows: Aerospace and Defense, Automotive, Banking, Capital Markets, 
        Chemicals, Communications and Media, Consumer Goods and Services, Energy, Health, High Tech, Industrial, Insurance, Life Science, Natural Resources, 
        Public Service, Private Equity, Retail, Software and Platforms, Travel, US Federal Government, Utilities.
    - FUNCTIONAL EXPERIENCE: Generate a concise, line-separated list (max 150 characters total) of the candidate’s functional expertise or focus areas.
        Each line must have 3–5 words only (no sentences or achievements).
        Select terms that reflect recognized job roles or processes within these categories only:
           • Executive / Corporate (leadership, management, coordination)
           • Technology / IT (software, data, SAP, cloud, product, QA, UX/UI)
           • Supply Chain / Logistics (procurement, planning, inventory, demand, operations)
           • Administration / Finance (accounting, payroll, treasury, billing, financial analysis)
           • Customer Service / Commercial (sales, client support, commercial operations)
        If no direct match exists, choose the nearest functional equivalent.
        Do not include project descriptions, achievements, or soft skills.
        Example: "SAP FI/MM configuration, Process automation, Financial analysis and reporting, Procurement and supplier management"
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