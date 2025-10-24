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
st.set_page_config(page_title="MASTER 3.0 – Benchmark Israel", layout="wide")

st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { text-align: center; color: #0D47A1; font-weight: 900; }
h3 { color: #1565C0; margin-top: 20px; }
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
.copy-btn {
    background: linear-gradient(90deg, #1E88E5, #42A5F5);
    color: white;
    padding: 10px 25px;
    border-radius: 10px;
    border: none;
    font-weight: bold;
    cursor: pointer;
}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------
# פונקציה: חיפוש נתוני שכר חיים מישראל (דרך Serper)
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
# פונקציה: המרת טקסט לטבלה
# -----------------------------------------------------------
def markdown_to_df(markdown_text):
    lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
    clean = [line for line in lines if not line.startswith("|-")]
    df = pd.read_csv(StringIO("\n".join(clean)), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x: x.strip())
    return df

# -----------------------------------------------------------
# פונקציה: הפקת דו"ח GPT
# -----------------------------------------------------------
def generate_salary_table(job_title, experience, live_data):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"בהתאם לעובד עם {experience} שנות ניסיון"
    prompt = f"""
הנה מידע חי מהאינטרנט על משרת "{job_title}":
{live_data}

בהתאם לנתונים ולידע שלך על השוק הישראלי לשנת 2025,
צור טבלה מפורטת ואינפורמטיבית של רכיבי השכר בישראל, כולל:

- טווחי שכר לפי מינימום, ממוצע, מקסימום
- מנגנוני תגמול מלאים (אחוזים, ספים, בונוסים)
- אחוז החברות המעניקות רכיב זה
- מגמת שוק (↑ עלייה / ↓ ירידה / → יציב)
- עלות מעסיק משוערת (₪)
- אחוז מתוך העלות הכוללת

עמודות חובה:
| רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | אחוז חברות שמציעות רכיב זה | מגמת שוק | עלות מעסיק (₪) | אחוז מעלות כוללת |

ציין גם רכיבים נפוצים פחות אם רלוונטיים (כוננויות, אחזקת רכב, בונוס שנתי וכו׳).
הצג רק טבלה, ללא הסברים נוספים.
"""
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט שלך הוא טבלה בלבד."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.35,
    )
    return response.choices[0].message.content

# -----------------------------------------------------------
# ממשק משתמש
# -----------------------------------------------------------
st.title("💎 MASTER 3.0 – מערכת בנצ׳מארק שכר בזמן אמת")
st.caption("מבוססת GPT + Serper | נתוני אמת מהשוק הישראלי")

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

        with st.spinner("מנתח ומפיק דו״ח GPT..."):
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
# היסטוריה
# -----------------------------------------------------------
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        job = item.get("job", "לא צויין")
        exp = item.get("experience", 0)
        time = item.get("time", "לא ידוע")
        report = item.get("report", "")
        exp_label = "ממוצע שוק" if exp == 0 else f"{exp} שנות ניסיון"
        with st.expander(f"{job} — {exp_label} — {time}"):
            st.markdown(report)
