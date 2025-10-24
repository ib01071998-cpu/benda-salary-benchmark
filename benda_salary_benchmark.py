import streamlit as st
import os, re, requests
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר – גרסת Ultimate ישראלית", layout="wide")
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
# הפקת טבלת בנצ'מארק מקצועית מלאה
# -------------------------------------------------
def generate_salary_table(job_title, experience, df):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    live_summary = "לא נמצאו נתוני אמת – יוצג בנצ'מארק ממוצע." if df.empty else f"נתוני אמת משוק העבודה בישראל:\n{df.to_string(index=False)}"

    prompt = f"""
{live_summary}

צור טבלת בנצ'מארק שכר מקצועית עבור התפקיד "{job_title}" בישראל {exp_text} לשנת 2025.

הצג את הטבלה **בפורמט אחיד בלבד**:
עמודות:  
רכיב שכר | טווח שכר או אחוזים | בסיסית (₪) | בינונית (₪) | גבוהה (₪) | ממוצע שוק (₪) | מנגנון תגמול מפורט | עלות מעסיק ממוצעת (₪) | אחוז מעלות השכר הכוללת (%)

⚙️ כללים:
- הצג את כל רכיבי השכר הרלוונטיים: שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב (כולל שווי שוק ודגמים), שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, מתנות/ביגוד/רווחה.
- אם יש רכיבים רלוונטיים לפי סוג המשרה (כוננויות, אופציות, רווחה, הוצאות), הוסף אותם.
- הצג טווחים מציאותיים לפי השוק הישראלי, ללא עיגול יתר.
- ברכיבי שכר משתנים (עמלות, בונוסים וכו׳) הצג **שלושה מודלים ישראליים נפוצים** באותו שדה של מנגנון תגמול.

🇮🇱 מנגנוני תגמול ישראליים לפי סוג רכיב:
שכר בסיס — משולם חודשי, לעיתים כולל שעות נוספות גלובליות.
עמלות — לפי מכירות נטו: 3%–7%. דוגמה: מדרגות (3% עד 100K ₪, 5% עד 200K ₪, 7% מעל). תקרה 10–12K ₪.
בונוסים — חודשי/רבעוני/שנתי לפי עמידה ב־KPI (רווח, גבייה, שביעות רצון). 5K–15K ₪.
רכב חברה — קבוצה 3–6. שווי שוק 140–240K ₪. דגמים: טויוטה קורולה, סקודה סופרב, יונדאי טוסון. זקיפת שווי 2,800–3,500 ₪.
קרן השתלמות — 7.5% מעסיק + 2.5% עובד.
פנסיה — 6.5% מעסיק + 6% עובד + 8.33% פיצויים.
סיבוס — 700–1,000 ₪ בחודש.
אש"ל — 400–800 ₪ בהתאם לאופי התפקיד.
ביטוח בריאות — השתתפות 300–600 ₪ לחודש.
ימי הבראה — 5–10 ימים × 450 ₪.
טלפון נייד — 150–300 ₪.
דלק — 2.0–2.4 ₪ לק"מ.
ציוד / מחשב — 100–150 ₪ החזר תקשורת חודשית.
שי לחגים / ביגוד — 800–1,500 ₪ לשנה.

🧮 חישוב עלות מעסיק:
עלות מעסיק ממוצעת = ממוצע שוק × 1.35.
אחוז מעלות כוללת – הערכה יחסית בין רכיבים.

הצג אך ורק טבלה אחת מסודרת וברורה ללא טקסט חופשי נוסף.
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה אחת בלבד בעברית, ללא הסברים נוספים."},
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

        with st.spinner("🧠 מחשב בנצ'מארק ומפיק טבלת שכר מלאה..."):
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
