import streamlit as st
import os, re, requests
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="💼 מערכת בנצ'מארק שכר – Benchmark AI Ultimate 🇮🇱", layout="wide")
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
# ניקוי וזיהוי דרג
# -------------------------------------------------
def normalize_text(text: str) -> str:
    return re.sub(r"[\"׳״׳׳']", "", text.replace("’", "").replace("”", "").replace("“", "")).lower().strip()

def detect_role_level(job_title: str) -> str:
    job = normalize_text(job_title)
    if any(word in job for word in ["מנכל", "ceo", "chief executive", "chief officer"]):
        return "מנכ״ל"
    elif any(word in job for word in ["סמנכל", "סמנכ", "vp", "vice president", "v.p", "vicepresident"]):
        return "סמנכ״ל"
    elif any(word in job for word in ["מנהל בכיר", "head of", "director", "ראש אגף", "מנהל תחום", "chief", "lead"]):
        return "בכיר"
    elif any(word in job for word in ["מנהל", "אחראי", "supervisor", "ראש צוות", "team leader"]):
        return "ביניים"
    elif any(word in job for word in ["נציג", "עוזר", "רכז", "מתאם", "עובד", "assistant", "coordinator", "representative"]):
        return "זוטר"
    else:
        return "לא מוגדר"

# -------------------------------------------------
# רכב לפי דרג
# -------------------------------------------------
def get_vehicle_data(level: str):
    data = {
        "מנכ״ל": ("קבוצה 7", "Volvo XC60, Audi Q5, Lexus NX", "330,000–400,000 ₪", "4,200 ₪"),
        "סמנכ״ל": ("קבוצה 6", "Mazda CX-5, Skoda Superb, Hyundai Tucson", "240,000–280,000 ₪", "3,200 ₪"),
        "בכיר": ("קבוצה 5", "Toyota Corolla Hybrid, Kia Niro, Peugeot 3008", "200,000–240,000 ₪", "2,900 ₪"),
        "ביניים": ("קבוצה 4", "Kia Sportage, Hyundai i30, Toyota Corolla", "160,000–200,000 ₪", "2,500 ₪"),
        "זוטר": ("קבוצה 2", "Kia Picanto, Hyundai i20, Toyota Yaris", "110,000–130,000 ₪", "1,800 ₪"),
    }
    return data.get(level, ("לא ידוע", "-", "-", "-"))

# -------------------------------------------------
# שליפת נתונים ממקורות ישראליים
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
# יצירת טבלת בנצ'מארק מלאה
# -------------------------------------------------
def generate_salary_table(job_title, company_size, industry, region, exp, df, level):
    exp_text = "בהתאם לממוצע השוק" if exp == 0 else f"עבור {exp} שנות ניסיון"
    live_summary = (
        "לא נמצאו נתוני אמת – יוצג בנצ'מארק ממוצע בלבד."
        if df.empty else
        f"נתוני אמת ממקורות ישראליים:\n{df.to_string(index=False)}"
    )
    vehicle_group, vehicle_models, vehicle_value, vehicle_tax = get_vehicle_data(level)

    prompt = f"""
{live_summary}

צור טבלת שכר מפורטת ומלאה לתפקיד "{job_title}" בישראל בשנת 2025 בדרג "{level}".
הנתונים צריכים להיות ריאליים ומתאימים לשוק הישראלי, ובפרט לחברות דומות לבנדא מגנטיק (יבוא, לוגיסטיקה, אלקטרוניקה, קמעונאות טכנולוגית).

כלול את *כל* רכיבי השכר המקובלים:
שכר בסיס, עמלות, בונוסים, מענקים, אש"ל, שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, ימי הבראה, רכב חברה, טלפון נייד, אינטרנט, דלק, חניה, ביגוד, מתנות, חופשות, ציוד, רווחה, ארוחות, ימי מחלה, הטבות נוספות.

לכל רכיב הצג:
- טווח (לדוג׳ 10,000–14,000 ₪ או 3%–7%)
- ממוצע תואם סוג הערכים
- מנגנון תגמול מפורט לפי הנוהג בישראל
- עלות מעסיק (₪)
- אחוז מעלות כוללת (%)

ברכיב רכב חברה השתמש בנתונים:
• קבוצת רכב: {vehicle_group}
• דגמים לדוגמה: {vehicle_models}
• שווי שוק: {vehicle_value}
• זקיפת שווי חודשית לעובד: {vehicle_tax}

בסוף הטבלה הצג שורה מסכמת עם:
💰 שכר ברוטו ממוצע כולל  
🏢 עלות מעסיק כוללת (שכר × 1.35 + עלויות נלוות)
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה אחת בלבד בעברית, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – Benchmark AI Ultimate 🇮🇱")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם משרה (לדוג׳: מנהל מכירות, סמנכ\"ל תפעול, רכז לוגיסטיקה):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):", 0, 40, 0)

col3, col4, col5 = st.columns(3)
with col3:
    company_size = st.selectbox("גודל חברה:", ["קטנה (עד 50)", "בינונית (50–250)", "גדולה (250+)"])
with col4:
    industry = st.selectbox("תחום פעילות:", ["יבוא", "לוגיסטיקה", "אלקטרוניקה", "קמעונאות טכנולוגית", "תעשייה", "שירות"])
with col5:
    region = st.selectbox("אזור גיאוגרפי:", ["מרכז", "שרון", "צפון", "דרום"])

if "history" not in st.session_state:
    st.session_state["history"] = []

if st.button("🚀 הפק דו״ח"):
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        detected_level = detect_role_level(job)
        st.info(f"🔍 דרג מזוהה: {detected_level}")
        with st.spinner("📡 שולף נתונים ממקורות ישראליים..."):
            df = get_live_salary_data(job, company_size, industry, region, exp, detected_level)
        with st.spinner("🧠 מפיק טבלת בנצ'מארק מקיפה..."):
            md = generate_salary_table(job, company_size, industry, region, exp, df, detected_level)
        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)
        st.session_state["history"].append({
            "job": job,
            "level": detected_level,
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
        job_title = item.get("job", "לא צוין")
        level = item.get("level", "לא זוהה")
        exp_value = item.get("exp", 0)
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{job_title} — דרג {level} — {exp_label} — {item.get('time','')}"):
            st.markdown(item.get("report", "אין דו\"ח להצגה"))
