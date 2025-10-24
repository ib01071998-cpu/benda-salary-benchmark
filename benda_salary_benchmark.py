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
# עיצוב
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:6px; }
h2 { color:#1565C0; font-weight:800; margin-top:20px; }
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
# שליפת נתוני אמת ממקורות ישראליים
# -------------------------------------------------
def get_live_salary_data(job_title: str):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = [
        "site:alljobs.co.il",
        "site:drushim.co.il",
        "site:globes.co.il",
        "site:bizportal.co.il",
        "site:maariv.co.il",
        "site:ynet.co.il"
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
# הפקת טבלת בנצ'מארק מקצועית עם מנגנוני תגמול ישראליים
# -------------------------------------------------
def generate_salary_table(job_title, experience, df):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    live_summary = "לא נמצאו נתוני אמת – יוצג בנצ'מארק ממוצע." if df.empty else f"נתוני אמת משוק העבודה בישראל:\n{df.to_string(index=False)}"

    prompt = f"""
{live_summary}

צור טבלת בנצ'מארק שכר מלאה לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.
שלב בין נתוני אמת ממקורות ישראליים לידע מקצועי אמין ומעודכן.

הצג את כלל רכיבי השכר הבאים (בהתאם לרלוונטיות התפקיד):
שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב (כולל שווי שוק ודגמים), שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, מתנות/ביגוד/רווחה, כוננויות, אופציות / RSU.

לכל רכיב:
- טווח מדויק (מינימום–מקסימום)
- רמות תגמול: בסיסית, בינונית, גבוהה
- ממוצע שוק (₪)
- מנגנון תגמול מפורט, בהתאם לפרקטיקות **המקובלות בישראל בפועל**
- עלות מעסיק ממוצעת (₪)
- אחוז מעלות השכר הכוללת (%)

התאם את מנגנוני התגמול כך שישקפו את השוק הישראלי בפועל:

🟦 שכר בסיס:
- משולם חודשי, קבוע, לרוב כולל רכיב גלובלי לשעות נוספות.
- משולם ב־1 לחודש.

🟩 עמלות:
- אחוז מהמכירות נטו (3%–7%).
- מודלים מקובלים:
  1. מדרגות: 3% עד 100K ₪, 5% מ־100K–200K ₪, 7% מעל 200K ₪.
  2. בונוס נוסף בעמידה ב־90% יעד (1% נוסף).
  3. תקרה חודשית 8,000–12,000 ₪.
- משולמות רק לאחר אספקת ההזמנה בפועל.

🟨 בונוסים:
- חודשיים, רבעוניים או שנתיים.
- סכום קבוע לפי KPI: רווח גולמי, גבייה, שירות לקוחות.
- טווחים: 5,000–15,000 ₪.
- לעיתים מחולקים כבונוס שנתי של 0.5–1.5 משכורות.

🟧 רכב חברה:
- קבוצה לפי דרג: מנהלים זוטרים – קבוצה 3 (120–140K ₪), מנהלים – קבוצה 4–5 (150–200K ₪), בכירים – קבוצה 6+ (220–260K ₪).
- דגמים: טויוטה קורולה, סקודה סופרב, מאזדה 6, יונדאי טוסון.
- זקיפת שווי: 2,800–3,500 ₪ לחודש.

🟦 קרן השתלמות:
- 7.5% מעסיק + 2.5% עובד.
- נהוגה בתפקידים אדמיניסטרטיביים, ניהוליים ובכירים.

🟩 פנסיה:
- 6.5% מעסיק + 6% עובד + 8.33% פיצויים.
- מחושבת רק על רכיבי הברוטו הקבועים.

🟨 ביטוחים:
- בריאות: 300–600 ₪ לחודש.
- חיים/אובדן כושר: 1%–1.5% מהשכר.

🟧 סיבוס / אש"ל:
- 700–1,000 ₪ בחודש.
- בחברות גדולות לעיתים 1,200 ₪.

🟩 ימי הבראה:
- 5–10 ימים × 400–450 ₪.
- לעיתים מגולם חודשי.

🟦 ציוד / טלפון / דלק:
- טלפון: 150–300 ₪.
- דלק: החזר לפי ק"מ – 2.0–2.4 ₪.
- מחשב נייד: עד 150 ₪ תקשורת.

🟨 רווחה / שי לחגים:
- שי חגים: 800–1,500 ₪ לשנה.
- רווחה כללית: 1,500–3,000 ₪.

⚙️ אופציות:
- 0.05%–0.3% מהמניות או 30–80 אלף ₪ שנתי.

⚠️ הצג ערכים ריאליים, יחס מקסימום/מינימום בין 1.2 ל־1.5.
⚠️ ברכב חברה הצג שווי שוק + זקיפת שווי בלבד (לא עלות מעסיק אמיתית).

בסוף הטבלה הוסף שורה: סה״כ עלות מעסיק כוללת (₪) לפי ממוצעי השוק.
"""

    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה אחת בלבד בעברית, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.15,
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
        with st.spinner("📡 שולף נתונים ממקורות ישראליים (AllJobs, Drushim, Globes, Bizportal)..."):
            df = get_live_salary_data(job)

        with st.spinner("🧠 מחשב בנצ'מארק חכם ומפיק טבלת שכר מלאה..."):
            md = generate_salary_table(job, exp, df)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job, "exp": exp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": md
        })

        st.components.v1.html(f"""
        <div style="text-align:center; margin-top:10px;">
          <button class="copy-btn" onclick="navigator.clipboard.writeText(`{md.replace('`','').replace('"','').replace("'","")}`); alert('הדו\"ח הועתק ✅');">📋 העתק דו\"ח</button>
        </div>
        """, height=80)

# היסטוריית דוחות
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report", "אין דו\"ח להצגה"))
