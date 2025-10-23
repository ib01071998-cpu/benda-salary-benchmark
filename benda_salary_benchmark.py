# -*- coding: utf-8 -*-
# 💼 מערכת חכמה לניתוח שכר – גרסה לפריסה מלאה בענן (Streamlit Cloud)

import streamlit as st
from openai import OpenAI
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF
import os

# קריאה למפתח ה-API מהסביבה המאובטחת של Streamlit
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# ---------------------------------------------------------
# סריקת מודעות מאתרי דרושים ציבוריים בישראל
# ---------------------------------------------------------
def scrape_jobs(job_title):
    results = []

    try:
        # AllJobs
        url_alljobs = f"https://www.alljobs.co.il/SearchResultsGuest.aspx?position={job_title}"
        html = requests.get(url_alljobs, timeout=10)
        soup = BeautifulSoup(html.text, "html.parser")
        for div in soup.find_all("div", class_="job-content-top"):
            txt = div.get_text(separator=" ", strip=True)
            if txt not in results:
                results.append(txt)

        # JobMaster
        url_jobmaster = f"https://www.jobmaster.co.il/jobs/?keyword={job_title}"
        html = requests.get(url_jobmaster, timeout=10)
        soup = BeautifulSoup(html.text, "html.parser")
        for div in soup.find_all("div", class_="jobs-item"):
            txt = div.get_text(separator=" ", strip=True)
            if txt not in results:
                results.append(txt)

        # Indeed IL
        url_indeed = f"https://il.indeed.com/jobs?q={job_title}"
        html = requests.get(url_indeed, timeout=10)
        soup = BeautifulSoup(html.text, "html.parser")
        for div in soup.find_all("div", class_="job_seen_beacon"):
            txt = div.get_text(separator=" ", strip=True)
            if txt not in results:
                results.append(txt)

    except Exception as e:
        st.error(f"שגיאה בסריקה: {e}")

    return results


# ---------------------------------------------------------
# ניתוח הנתונים בעזרת GPT-5
# ---------------------------------------------------------
def analyze_salary(job_title, jobs_texts):
    joined_text = "\n\n".join(jobs_texts[:10])
    prompt = f"""
    אתה אנליסט שכר ישראלי בכיר.
    קיבלת רשימת מודעות למשרה "{job_title}" מאתרי דרושים בישראל.
    צור דו״ח שכר מקצועי בעברית הכולל:
    • טווח שכר ממוצע (ש״ח)
    • מבנה השכר (בסיס, עמלות, בונוסים וכו׳)
    • הטבות נפוצות (סיבוס, רכב, קרן השתלמות וכו׳)
    • הערות לפי אזור, ניסיון, סוג חברה או תחום פעילות
    • מסקנה כללית על מגמות השוק לתפקיד זה.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר לשוק הישראלי."},
            {"role": "user", "content": prompt + joined_text}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content


# ---------------------------------------------------------
# 🎨 עיצוב ממשק
# ---------------------------------------------------------
st.set_page_config(page_title="מודל שכר חכם | BENDA", layout="centered")
st.markdown("""
    <style>
    body {
        background-color: #F8F9FA;
        direction: rtl;
        text-align: right;
        font-family: "Segoe UI", sans-serif;
    }
    .stTextInput>div>div>input {
        text-align: right;
    }
    .stButton>button {
        background-color: #1E90FF;
        color: white;
        border-radius: 10px;
        height: 3em;
        width: 100%;
        font-size: 1.1em;
    }
    .stButton>button:hover {
        background-color: #007ACC;
        color: #fff;
    }
    </style>
""", unsafe_allow_html=True)

st.title("💼 מערכת חכמה לניתוח שכר")
st.write("הזן שם משרה בעברית כדי לקבל דו״ח שכר מקצועי ומעודכן המבוסס על בינה מלאכותית.")
st.write("---")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

if st.button("נתח שכר"):
    if not job_title:
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מבצע ניתוח שכר... אנא המתן כ-20 שניות ⏳"):
            job_data = scrape_jobs(job_title)
            if not job_data:
                st.error("לא נמצאו מודעות רלוונטיות, נסה שם אחר או תפקיד דומה.")
            else:
                report = analyze_salary(job_title, job_data)
                st.success("הדו״ח מוכן ✅")
                st.markdown(f"### דו״ח שכר עבור **{job_title}**")
                st.write(report)
                st.write("---")

                # ייצוא ל-PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Helvetica", size=12)
                pdf.multi_cell(0, 10, txt=f"דו\"ח שכר למשרה: {job_title}\n\n{report}")
                pdf.output("דו\"ח_שכר.pdf")

                with open("דו\"ח_שכר.pdf", "rb") as f:
                    st.download_button("📄 הורד דו״ח PDF", f, file_name=f"דוח_שכר_{job_title}.pdf")
