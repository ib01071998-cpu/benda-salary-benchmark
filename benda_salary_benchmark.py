import streamlit as st
import os, re, requests
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="💼 מערכת בנצ'מארק שכר – גרסה חכמה ואוטומטית 🇮🇱", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:6px; }
table {width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden; box-shadow:0 3px 12px rgba(0,0,0,0.1)}
th {background:#1976D2;color:#fff;padding:12px; font-weight:700; border:1px solid #E3F2FD; text-align:center}
td {background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center;font-size:15px}
tr:nth-child(even) td {background:#F9FBE7}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
.summary-box {background:#E3F2FD; padding:22px; border-radius:12px; text-align:center; margin-top:30px; box-shadow:inset 0 0 8px rgba(0,0,0,0.1);}
.summary-line {font-size:18px; font-weight:600; color:#0D47A1;}
.summary-value {font-size:22px; font-weight:800; color:#1E88E5;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# פונקציה לזיהוי הדרג מתוך שם המשרה
# -------------------------------------------------
def detect_role_level(job_title: str) -> str:
    job_title = job_title.lower()
    if any(word in job_title for word in ["מנכ", "ceo", "chief executive"]):
        return "מנכ״ל"
    elif any(word in job_title for word in ["סמנכ", "vp", "vice president"]):
        return "סמנכ״ל"
    elif any(word in job_title for word in ["מנהל בכיר", "head of", "director", "אגף"]):
        return "בכיר"
    elif any(word in job_title for word in ["מנהל", "אחראי", "ראש צוות", "supervisor"]):
        return "ביניים"
    elif any(word in job_title for word in ["נציג", "עוזר", "רכז", "מתאם", "עובד"]):
        return "זוטר"
    else:
        return "לא מוגדר"

# -------------------------------------------------
# שליפת נתוני אמת ממקורות ישראליים
# -------------------------------------------------
def get_live_salary_data(job_title, company_size, industry, region, exp, level):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    query = f"שכר {job_title} דרג {level} בתחום {industry} בחברה {company_size} באזור {region} עם {exp} שנות ניסיון site:(alljobs.co.il OR drushim.co.il OR globes.co.il OR bizportal.co.il OR calcalist.co.il)"
    try:
        r = requests.post(url, headers=headers, json={"q": query}, timeout=20)
        items = r.json().get("organic", [])
        rows = []
        for item in items:
            snippet = item.get("snippet", "")
            nums = re.findall(r"\d{1,3}(?:,\d{3})", snippet)
            salaries = [int(x.replace(",", "")) for x in nums]
            if salaries:
                rows.append({
                    "מקור": item.get("link", "לא צוין"),
                    "מינימום": min(salaries),
                    "מקסימום": max(salaries),
                    "ממוצע": int(sum(salaries)/len(salaries))
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

# -------------------------------------------------
# הפקת טבלת בנצ'מארק
# -------------------------------------------------
def generate
