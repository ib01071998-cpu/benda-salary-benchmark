import streamlit as st
import requests
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
import os
from dotenv import load_dotenv

# -----------------------------------------------------------
# טעינת מפתחות API
# -----------------------------------------------------------
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# -----------------------------------------------------------
# הגדרות Streamlit
# -----------------------------------------------------------
st.set_page_config(page_title="MASTER 4.0 – Benchmark Israel", layout="wide")

st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { text-align: center; color: #0D47A1; font-weight: 900; }
h3 { color: #1565C0; margin-top: 25px; }
table {
    width: 100%;
    border-collapse: collapse;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 3px 10px rgba(0,0,0,0.1);
}
th {
    background-color: #1565C0;
    color: white;
    padding: 12px;
    text-align: center;
    font-weight: bold;
}
td {
    padding: 10px;
    border: 1px solid #E3F2FD;
    text-align: center;
}
tr:nth-child(even) td { background-color: #F1F8E9; }
.report-box {
    background-color: #E3F2FD;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 20px;
}
button, .stButton>button {
    background: linear-gradient(90deg, #1E88E5, #42A5F5);
    color: white;
    font-weight: bold;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# פונקציה: חיפוש נתוני שכר חיים בישראל דרך Serper
# -----------------------------------------------------------
def get_live_salary_data(job_title):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    query = f"שכר {job_title} site:alljobs.co.il OR site:drushim.co.il OR site:globes.co.il OR site:bizportal.co.il"
    payload = {"q": query}
    try:
        res = requests.post(url, headers=headers, json=payload)
        results = res.json().get("organic", [])
        texts = []
        for r in results[:5]:
            title = r.get("title", "")
            snippet = r.get("snippet", "")
            texts.append(f"{title} – {snippet}")
        return "\n".join(texts)
    except Exception as e:
        return f"שגיאה בגישה ל-Serper API: {e}"

# -----------------------------------------------------------
# פונקציה: הפקת דו"ח GPT עם מנגנוני תגמול מפורטים
# -----------------------------------------------------------
def generate_salary_table(job_title, experience, live_data):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"בהתאם לעובד עם {experience} שנות ניסיון"
    prompt = f"""
הנה מידע אמיתי מהאינטרנט על משרת "{job_title}":
{live_data}

בהתאם לכך ולידע שלך על השוק הישראלי לשנת 2025,
צור טבלה מפורטת של רכיבי השכר בישראל, כולל:

- טווחי שכר (מינימום, ממוצע, מקסימום)
- פירוט מנגנוני תגמול ברמה גבוהה מאוד:
  • עמלות אישיות, קבוצתיות, לפי יעד, לפי רווח גולמי
  • בונוס שנתי / רבעוני לפי KPIs, עמידה ביעדים, שימור לקוחות
  • תגמולים לא כספיים (ימי חופשה, הכשרות, תמריצים)
- אחוז חברות שמציעות רכיב זה
- מגמת שוק (עלייה / ירידה / יציב)
- עלות מעסיק לרכיב
- אחוז מעלות כוללת

עמודות חובה:
| רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול מפורט | אחוז חברות שמציעות רכיב זה | מגמת שוק | עלות מעסיק (₪) | אחוז מעלות כוללת |

לאחר מכן הצג שורה מסכמת של:
**סה״כ עלות מעסיק ממוצעת (₪)**

הצג רק טבלה אחת — ללא טקסט נוסף.
"""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט שלך הוא טבלה בלבד, בשפה מקצועית ומדויקת."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.35,
    )
    return response.choices[0].message.content

# -----------------------------------------------------------
# ממשק משתמש
# -----------------------------------------------------------
st.title("💎 MASTER 4.0 PRO – מערכת בנצ׳מארק שכר בזמן אמת")
st.caption("מבוססת GPT + Serper | נתוני אמת מהשוק הישראלי | גרסה מקצועית")

col1, col2 = st.columns([2, 1])
with col1:
    job_title = st.text_input("שם המשרה:")
with col2:
    experience = st.number_input("שנות ניסיון (0 = ממוצע שוק):", min_value=0, max_value=40, value=0, step=1)

if "history" not in st.session_state:
    st.session_state["history"] = []

if st.button("🔍 הפק דו״ח"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מחפש נתוני שוק חיים..."):
            live_data = get_live_salary_data(job_title)
            st.markdown("### 🌐 מידע חי מהשוק הישראלי:")
            st.markdown(live_data)

        with st.spinner("מנתח ומפיק דו״ח GPT מקצועי..."):
            report = generate_salary_table(job_title, experience, live_data)
            st.markdown("### 📊 דו״ח שכר מפורט:")
            st.markdown(report, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job_title,
            "experience": experience,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": report
        })

# -----------------------------------------------------------
# היסטוריה מלאה + ניקוי
# -----------------------------------------------------------
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    clear_col, _ = st.columns([1, 4])
    with clear_col:
        if st.button("🗑 נקה היסטוריה"):
            st.session_state["history"] = []
            st.success("ההיסטוריה נוקתה בהצלחה ✅")

    for item in reversed(st.session_state["history"]):
        job = item.get("job", "לא צויין")
        exp = item.get("experience", 0)
        time = item.get("time", "לא ידוע")
        report = item.get("report", "")
        exp_label = "ממוצע שוק" if exp == 0 else f"{exp} שנות ניסיון"
        with st.expander(f"{job} — {exp_label} — {time}"):
            st.markdown(report)
