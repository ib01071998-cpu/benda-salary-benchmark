import streamlit as st
import os, re, requests
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
from dotenv import load_dotenv

# ----------------------------------------------
# הגדרות כלליות
# ----------------------------------------------
st.set_page_config(page_title="MASTER 4.3.1 – מערכת בנצ׳מארק חכמה", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# ----------------------------------------------
# עיצוב כללי
# ----------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:6px; }
.stButton>button {
  background: linear-gradient(90deg,#1976D2,#42A5F5); color:#fff; border:none; border-radius:10px;
  font-weight:700; padding:10px 20px; box-shadow:0 2px 10px rgba(0,0,0,.15); transition:.2s;
}
.stButton>button:hover { transform: translateY(-1px); }
table{width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden; box-shadow:0 3px 10px rgba(0,0,0,.08)}
th{background:#1565C0;color:#fff;padding:12px; font-weight:800; border:1px solid #E3F2FD; text-align:center}
td{background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center}
tr:nth-child(even) td{background:#F1F8E9}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------
# פונקציות עזר
# ----------------------------------------------
def get_live_data(job_title: str) -> str:
    """שליפת מידע ממקורות שכר בישראל"""
    if not SERPER_KEY:
        return "⚠️ אין מפתח SERPER — הפלט מבוסס רק על GPT."
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    payload = {"q": f"שכר {job_title} site:alljobs.co.il OR site:drushim.co.il OR site:globes.co.il OR site:bizportal.co.il"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        items = r.json().get("organic", [])[:5]
        return "\n".join([f"{x.get('title','')} — {x.get('snippet','')}" for x in items])
    except Exception as e:
        return f"שגיאה: {e}"

def generate_salary_table(job_title, experience, live_data):
    """מפיק טבלת שכר אינפורמטיבית ומפורטת בלבד"""
    exp_text = "בהתאם לממוצע השוק" if experience==0 else f"עבור {experience} שנות ניסיון"
    prompt = f"""
להלן מידע חי ממקורות ישראליים עבור "{job_title}":
{live_data}

צור טבלת בנצ׳מארק שכר מפורטת (2025) בעברית מלאה, הכוללת:
- כל רכיבי השכר האפשריים: שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב, אש"ל, שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, ימי הבראה, ציוד, דלק, טלפון, חניה וכו׳.
- עבור רכיבי שכר משתנים, פרט מנגנוני תגמול מלאים כולל:
  * שיעור תגמול (באחוזים)
  * מדרגות תגמול (לדוג׳: 3% עד יעד, 5% מעל יעד)
  * תדירות (חודשי/רבעוני/שנתי)
  * תקרת תגמול אם קיימת
  * דוגמה מספרית ריאלית
- עבור רכבי חברה, פרט:
  * דגמים מקובלים (לדוג׳ טויוטה קורולה, מאזדה 3, סקודה סופרב)
  * שווי שוק רכב חדש (₪)
  * שווי שימוש חודשי ממוצע (₪)
  * סוג מימון (ליסינג/בעלות)
  * האם כולל דלק וביטוחים

הצג אך ורק טבלה, ללא טקסט נוסף.
העמודות:
| רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול מפורט | אחוז חברות שמציעות | מגמת שוק | עלות מעסיק (₪) | אחוז מעלות כוללת |
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role":"system","content":"אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלה בלבד בעברית."},
            {"role":"user","content":prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# ----------------------------------------------
# ממשק ראשי
# ----------------------------------------------
st.title("💼 MASTER 4.3.1 – מערכת בנצ׳מארק כוללת")
st.caption("GPT-4 Turbo + Serper | כל רכיבי השכר | מנגנוני תגמול מפורטים | ללא חישוב ברוטו/עלות מעסיק")

col1, col2 = st.columns([2,1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל לוגיסטיקה):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):",0,40,0)

if "history" not in st.session_state:
    st.session_state["history"] = []

btn1, btn2 = st.columns([1,1])
with btn1: run = st.button("🚀 הפק דו״ח")
with btn2:
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state["history"] = []
        st.success("היסטוריה נוקתה בהצלחה ✅")

if run:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מבצע חיפוש במקורות ישראליים..."):
            live = get_live_data(job)
            st.markdown("### 🌐 מקורות שוק ישראליים:")
            st.markdown(live)
        with st.spinner("מפיק דו״ח..."):
            md = generate_salary_table(job, exp, live)
        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job,
            "exp": exp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": md
        })

        st.components.v1.html(f"""
        <div style="text-align:center; margin-top:10px;">
          <button class="copy-btn" onclick="navigator.clipboard.writeText(`{md.replace('`','').replace('"','').replace("'","")}`); alert('הדו\"ח הועתק ✅');">📋 העתק דו\"ח</button>
        </div>
        """, height=80)

# היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report","אין דו\"ח להצגה"))
