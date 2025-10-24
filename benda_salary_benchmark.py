import streamlit as st
import os, re, requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="בנצ'מארק שכר ישראל – גרסת MASTER REAL", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב פרימיום
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:6px; }
table {width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden; box-shadow:0 3px 12px rgba(0,0,0,0.1)}
th {background:#1976D2;color:#fff;padding:12px; font-weight:700; border:1px solid #E3F2FD; text-align:center}
td {background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center;font-size:15px}
tr:nth-child(even) td {background:#F9FBE7}
.summary-box {background:#E3F2FD; padding:22px; border-radius:12px; text-align:center; margin-top:30px; box-shadow:inset 0 0 8px rgba(0,0,0,0.1);}
.summary-line {font-size:18px; font-weight:600; color:#0D47A1;}
.summary-value {font-size:22px; font-weight:800; color:#1E88E5;}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# שליפת נתוני אמת מהשוק
# -------------------------------------------------
def get_real_salary_data(job_title: str):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = [
        "site:alljobs.co.il", "site:drushim.co.il",
        "site:globes.co.il", "site:ynet.co.il",
        "site:maariv.co.il", "site:bizportal.co.il"
    ]
    all_snippets = []
    for src in sources:
        payload = {"q": f"שכר {job_title} {src}"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            data = r.json().get("organic", [])
            for item in data:
                snippet = item.get("snippet", "")
                if snippet:
                    all_snippets.append(snippet)
        except:
            continue
    return " ".join(all_snippets[:30]) if all_snippets else None

# -------------------------------------------------
# יצירת טבלת בנצ'מארק אמיתית
# -------------------------------------------------
def generate_salary_table(job_title, experience, real_data):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    real_snippets = real_data if real_data else "לא נמצאו נתונים ישירים, השתמש בהערכות שוק מבוססות GPT בלבד."

    prompt = f"""
השתמש במידע הבא שנשלף ממקורות ישראליים כדי לחשב טווחי שכר אמיתיים:
{real_snippets}

צור טבלת בנצ'מארק שכר מקצועית לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025
