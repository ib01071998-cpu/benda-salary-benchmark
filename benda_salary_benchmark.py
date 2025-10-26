import streamlit as st
import os, re, requests
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר - גרסה ישראלית חכמה", layout="wide")
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
# שליפת נתוני אמת ממקורות ישראליים (SERPER)
# -------------------------------------------------
def get_live_salary_data(job_title, level, company_size, industry, region):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    query = f"שכר {job_title} דרג {level} {company_size} {industry} {region} site:(alljobs.co.il OR drushim.co.il OR globes.co.il OR bizportal.co.il OR calcalist.co.il)"
    payload = {"q": query}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
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
                    "ממוצע": int(sum(salaries) / len(salaries))
                })
        return pd.DataFrame(rows)
    except Exception:
        return pd.DataFrame()

# -------------------------------------------------
# יצירת טבלת בנצ'מארק עם GPT
# -------------------------------------------------
def generate_salary_table(job_title, level, company_size, industry, region, exp, df):
    exp_text = "בהתאם לממוצע השוק" if exp == 0 else f"עבור {exp} שנות ניסיון"
    live_summary = (
        "לא נמצאו נתוני אמת – יוצג בנצ'מארק ממוצע בלבד."
        if df.empty else
        f"נתוני אמת ממקורות ישראליים:\n{df.to_string(index=False)}"
    )

    prompt = f"""
{live_summary}

צור טבלת שכר מפורטת ומקיפה עבור תפקיד "{job_title}" בישראל לשנת 2025,
בדרג "{level}", בחברה בגודל "{company_size}", בתחום "{industry}", באזור "{region}", {exp_text}.

התאם את הנתונים לשוק הישראלי האמיתי — במיוחד לענפים דומים לחברות כמו בנדא מגנטיק
(יבוא, לוגיסטיקה, תעשייה, אלקטרוניקה, קמעונאות טכנולוגית).

הצג טבלה עם כלל רכיבי השכר הרלוונטיים:
שכר בסיס, עמלות, בונוסים, מענקים, רכב חברה (כולל שווי שוק ודגמים), קרן השתלמות, פנסיה, ביטוחים, אש"ל, דלק, שעות נוספות, ימי הבראה, חופשות, רווחה, ציוד, טלפון נייד, חניה.

לכל רכיב הצג:
- טווח שכר או אחוזים (לדוג׳ 3%–7% או 10,000–14,000 ₪)
- בסיסית / בינונית / גבוהה
- ממוצע שוק (₪)
- מנגנון תגמול מפורט **בהתאם לנוהג בישראל** — לדוגמה:
  - עמלות: 4%–6% מהמכירות נטו עד תקרה של 10,000 ₪
  - בונוס רבעוני: לפי עמידה ביעדים (עד 15% מהשכר הרבעוני)
  - קרן השתלמות: 7.5% מהמעסיק + 2.5% מהעובד
  - שעות נוספות: לפי 125%–150% מעל התקן
  - רכב חברה: לפי דרג — מנהלים: קבוצה 3–4; סמנכ״לים: 5–6; מנכ״לים: 6+
- עלות מעסיק ממוצעת (₪)
- אחוז מעלות השכר הכוללת (%)

הצג את הפלט בטבלה אחת בלבד, בפורמט הבא:

| רכיב שכר | טווח שכר | בסיסית | בינונית | גבוהה | ממוצע שוק (₪) | מנגנון תגמול מפורט | עלות מעסיק ממוצעת (₪) | אחוז מעלות שכר כוללת (%) |

בסיום הוסף בלוק מסכם (לא חלק מהטבלה):
💰 שכר ברוטו ממוצע כולל  
🏢 עלות מעסיק כוללת (שכר × 1.35 + עלויות נלוות)  
🚗 זקיפת שווי רכב ממוצעת לפי הדרג (2,800–3,800 ₪ לחודש)
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה אחת בלבד בעברית, ללא מלל נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר - גרסה חכמה ומקומית 🇮🇱")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם משרה (לדוג׳: מנהל מכירות, סמנכ\"ל תפעול):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):", 0, 40, 0)

col3, col4, col5, col6 = st.columns(4)
with col3:
    level = st.selectbox("דרג תפקיד:", ["זוטר", "ביניים", "ניהולי", "בכיר", "סמנכ\"ל", "מנכ\"ל"])
with col4:
    company_size = st.selectbox("גודל חברה:", ["קטנה (עד 50)", "בינונית (50–250)", "גדולה (250+)"])
with col5:
    industry = st.selectbox("תחום פעילות:", ["יבוא", "לוגיסטיקה", "אלקטרוניקה", "קמעונאות טכנולוגית", "תעשייה", "שירות"])
with col6:
    region = st.selectbox("אזור גיאוגרפי:", ["מרכז", "שרון", "צפון", "דרום"])

if "history" not in st.session_state:
    st.session_state["history"] = []

col_a, col_b = st.columns([1, 1])
with col_a:
    run = st.button("🚀 הפק דו״ח")
with col_b:
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state["history"] = []
        st.success("היסטוריית הדוחות נוקתה בהצלחה ✅")

if run:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("📡 שולף נתוני אמת ממקורות ישראליים..."):
            df = get_live_salary_data(job, level, company_size, industry, region)

        with st.spinner("🧠 מחשב בנצ'מארק חכם..."):
            md = generate_salary_table(job, level, company_size, industry, region, exp, df)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">💰 <span class="summary-value">שכר ברוטו ממוצע כולל:</span> לפי ממוצעי השוק בטבלה.</div>
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות.</div>
          <div class="summary-line">🚗 <span class="summary-value">זקיפת שווי רכב:</span> לפי הדרג (2,800–3,800 ₪ לחודש).</div>
        </div>
        """, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job,
            "level": level,
            "size": company_size,
            "industry": industry,
            "region": region,
            "exp": exp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": md
        })

# -------------------------------------------------
# היסטוריית דוחות
# -------------------------------------------------
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות קודמים")
    for item in reversed(st.session_state["history"]):
        with st.expander(f"{item['job']} — {item['level']} — {item['time']}"):
            st.markdown(item["report"], unsafe_allow_html=True)
