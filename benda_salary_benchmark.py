import streamlit as st
import os, re, requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר – גרסת פרימיום ישראלית", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב חדש – רמה בינלאומית
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:6px; }
h2 { color:#1565C0; font-weight:800; margin-top:20px; }
.dataframe {width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden; box-shadow:0 3px 12px rgba(0,0,0,0.08)}
.dataframe th {background:#1976D2;color:#fff;padding:12px;font-weight:700;border:1px solid #E3F2FD;text-align:center}
.dataframe td {background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center;font-size:15px}
.dataframe tr:nth-child(even) td {background:#F1F8E9}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
.summary-box {background:#E3F2FD; padding:22px; border-radius:12px; text-align:center; margin-top:30px; box-shadow:inset 0 0 8px rgba(0,0,0,0.1);}
.summary-line {font-size:18px; font-weight:600; color:#0D47A1;}
.summary-value {font-size:22px; font-weight:800; color:#1E88E5;}
table {width:100%; border-collapse:collapse; border-radius:10px; overflow:hidden;}
td, th {padding:8px; border:1px solid #ccc;}
tr:nth-child(even){background:#FAFAFA;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# שליפת נתוני אמת
# -------------------------------------------------
def get_live_salary_data(job_title: str):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = [
        "site:alljobs.co.il", "site:drushim.co.il", "site:globes.co.il",
        "site:bizportal.co.il", "site:maariv.co.il", "site:ynet.co.il"
    ]
    rows = []
    for src in sources:
        payload = {"q": f"שכר {job_title} {src}"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            items = r.json().get("organic", [])
            for item in items:
                snippet = item.get("snippet", "")
                nums = re.findall(r"\d{1,3}(?:,\d{3})", snippet)
                salaries = [int(x.replace(",", "")) for x in nums]
                if salaries:
                    rows.append({
                        "מקור": src.split(":")[1].split(".")[0].capitalize(),
                        "מינימום": min(salaries),
                        "מקסימום": max(salaries),
                        "ממוצע": int(sum(salaries)/len(salaries))
                    })
        except Exception:
            continue
    return pd.DataFrame(rows)

# -------------------------------------------------
# הפקת טבלת בנצ'מארק
# -------------------------------------------------
def generate_salary_table(job_title, experience, df):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    live_summary = "לא נמצאו נתוני אמת – יוצג בנצ'מארק ממוצע." if df.empty else f"נתוני אמת משוק העבודה בישראל:\n{df.to_string(index=False)}"

    prompt = f"""
{live_summary}

צור טבלת בנצ'מארק שכר מקצועית לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.
יש להציג טבלה בפורמט HTML בלבד – לא Markdown!

יש לכלול את כלל רכיבי השכר:
שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב (כולל זקיפת שווי במשכורת), שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, רווחה.

לכל רכיב הצג:
- טווחים ברורים (₪ או %)
- שלוש רמות תגמול בעמודות (בסיסית, בינונית, גבוהה)
- ממוצע שוק (₪)
- מנגנון תגמול מקובל בישראל בפועל
- עלות מעסיק ממוצעת (₪)
- אחוז מעלות כוללת (%)

ברכיב "רכב חברה":
- הצג את זקיפת השווי למשכורת החודשית (₪)
- ציין 3 דגמים תואמים (למשל סקודה סופרב, טויוטה קאמרי, מאזדה 6)

בסוף הדוח הצג תיבת סיכום מעוצבת עם:
- עלות מעסיק כוללת (שכר × 1.35 + עלויות נלוות)
- הערכת שווי כוללת של ההטבות (₪)
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא HTML בלבד, כולל טבלה מעוצבת מלאה."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – גרסת Ultimate ישראלית")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: מנהל מכירות, מנהל לוגיסטיקה, אנליסט שכר):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):", 0, 40, 0)

if "history" not in st.session_state:
    st.session_state["history"] = []

btn1, btn2 = st.columns([1, 1])
with btn1:
    run = st.button("🚀 הפק דו״ח")
with btn2:
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state["history"] = []
        st.success("היסטוריה נוקתה בהצלחה ✅")

if run:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("📡 שולף נתונים ממקורות ישראליים..."):
            df = get_live_salary_data(job)
        with st.spinner("🧠 מחשב בנצ'מארק ומעצב דוח..."):
            html = generate_salary_table(job, exp, df)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.components.v1.html(html, height=1000, scrolling=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות (רכב, ביטוחים, סיבוס, רווחה).</div>
          <div class="summary-line">🚗 <span class="summary-value">הטבות ממוצעות:</span> רכב חברה (זקיפת שווי), טלפון נייד, ביטוחים, מתנות ורווחה.</div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job, "exp": exp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": html
        })

        st.components.v1.html(f"""
        <div style="text-align:center; margin-top:10px;">
          <button class="copy-btn" onclick="navigator.clipboard.writeText(`{html.replace('`','').replace('"','').replace("'","")}`); alert('הדו\"ח הועתק ✅');">📋 העתק דו\"ח</button>
        </div>
        """, height=80)

# היסטוריית דוחות
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_label = "ממוצע שוק" if item["exp"] == 0 else f"{item['exp']} שנות ניסיון"
        with st.expander(f"{item['job']} — {exp_label} — {item['time']}"):
            st.components.v1.html(item["report"], height=600, scrolling=True)
