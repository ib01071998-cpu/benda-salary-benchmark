# -*- coding: utf-8 -*-
# 💼 מערכת חכמה לניתוח שכר בישראל (מבוססת GPT בלבד, ללא סריקת אתרים)

import streamlit as st
from openai import OpenAI
import os
from fpdf import FPDF

# קריאה למפתח ה-API מהסביבה המאובטחת של Streamlit
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# ---------------------------------------------------------
# 🧠 פונקציה לניתוח שכר מבוסס GPT בלבד
# ---------------------------------------------------------
def analyze_salary_gpt(job_title):
    prompt = f"""
    אתה אנליסט שכר בכיר לשוק הישראלי.
    תפקידך לנתח את השכר המקובל למשרה "{job_title}" בישראל, 
    בהתבסס על מקורות עדכניים, מגמות שוק וידע נרחב.
    צור דו״ח מפורט בעברית הכולל:

    1. טווח שכר ממוצע (מינימום, ממוצע, מקסימום – בש״ח ברוטו)
    2. מבנה השכר (שכר בסיס, עמלות, בונוסים, מנגנון תגמול משתנה)
    3. הטבות ותנאים נפוצים (סיבוס/אש״ל, רכב, טלפון, קרן השתלמות וכו׳)
    4. הערות לפי ניסיון, אזור גאוגרפי, וגודל חברה
    5. מגמות עדכניות בשוק התעסוקה למשרה זו

    כתוב את הדו״ח בעברית תקנית, בסגנון מקצועי, 
    כאילו הוא מיועד להנהלה או למחלקת HR בחברה גדולה.
    """

    response = client.chat.completions.create(
        model="gpt-5",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר לשוק העבודה הישראלי."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )

    return response.choices[0].message.content


# ---------------------------------------------------------
# 🎨 עיצוב ממשק Streamlit
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
st.write("הזן שם משרה בעברית כדי לקבל דו״ח שכר מקצועי ועדכני המבוסס על בינה מלאכותית בלבד.")
st.write("---")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

if st.button("נתח שכר"):
    if not job_title:
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מבצע ניתוח שכר חכם... אנא המתן ⏳"):
            report = analyze_salary_gpt(job_title)
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
