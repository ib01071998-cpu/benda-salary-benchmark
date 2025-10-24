import streamlit as st
import os, re, requests, statistics
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות כלליות
# -------------------------------------------------
st.set_page_config(page_title="בנצ'מארק שכר ישראל – MASTER REAL ISRAEL V3", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב מקצועי
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
# שליפת נתוני אמת ממודעות (SERPER)
# -------------------------------------------------
def get_real_salary_data(job_title: str):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = ["site:alljobs.co.il", "site:drushim.co.il", "site:globes.co.il"]
    all_snippets, numbers = [], []

    for src in sources:
        payload = {"q": f"שכר {job_title} {src}"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            data = r.json().get("organic", [])
            for item in data:
                snippet = item.get("snippet", "")
                if snippet:
                    all_snippets.append(snippet)
                    found = re.findall(r'(\d{1,3}(?:,\d{3})?)[\s\-–]{1,3}(\d{1,3}(?:,\d{3})?)', snippet)
                    for match in found:
                        try:
                            n1, n2 = [int(re.sub(r'[^\d]', '', x)) for x in match]
                            if 2000 < n1 < 100000 and 2000 < n2 < 100000:
                                numbers.append((n1, n2))
                        except:
                            pass
        except Exception:
            continue

    if numbers:
        lows, highs = [n[0] for n in numbers], [n[1] for n in numbers]
        avg_low, avg_high = round(statistics.mean(lows)), round(statistics.mean(highs))
        avg_text = f"{avg_low:,}–{avg_high:,} ₪"
    else:
        avg_text = "לא נמצאו טווחים ריאליים"
    return {"snippets": " ".join(all_snippets[:40]), "avg_range": avg_text}

# -------------------------------------------------
# בניית טבלת בנצ'מארק (הוראות חכמות למודל)
# -------------------------------------------------
def generate_salary_table(job_title, experience, real_data):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    snippets = real_data.get("snippets", "")
    avg = real_data.get("avg_range", "לא זמין")

    prompt = f"""
צור טבלת בנצ'מארק שכר לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.
השתמש במידע ממודעות אמיתיות מהשוק הישראלי ({avg}):
{snippets}

הנחיות עיצוב התוכן:
- הצג **אך ורק טווחים** (לא ערכים בודדים), לדוגמה:
  ₪12,000–₪15,000 / ‎6%–7.5%‎.
- התאמת סוג הנתון לסוג הרכיב (₪ או %).
- כלול בעמודה "מנגנון תגמול מפורט" את המנגנון המקובל בישראל לפי סוג רכיב:
  • שכר בסיס – טווח שכר חודשי לפי דרג.
  • עמלות – 3%–5% מהמכירות, תקרה 10,000 ₪.
  • בונוסים – 1–2 משכורות שנתיות לפי עמידה ביעדים.
  • מענקים – תמריץ חד-פעמי על ביצועים מיוחדים.
  • קרן השתלמות – 7% עובד + 7.5% מעסיק.
  • פנסיה – 6% עובד + 6.5% מעסיק.
  • רכב – שווי שוק 120–160 אלף ₪ (סקודה סופרב, קאמרי, מאזדה 6), כולל דלק וביטוח.
  • דלק – כלול ברכב או החזר 1,500–2,000 ₪.
  • ביטוחים – בריאות, חיים, תאונות, 300–600 ₪.
  • אש"ל – 400–1,000 ₪ או כרטיס סיבוס.
  • שעות נוספות – 125%–150% לפי חוק.
  • ציוד – מחשב, טלפון, רכב עבודה, לפי המקובל.
- הצג בכל שורה: טווח נמוך, טווח גבוה, טווח ממוצע, מנגנון תגמול מפורט.
- הצג עלות מעסיק מוערכת (₪) ואחוז מהרכב הכולל.
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אנליסט שכר בכיר בישראל. צור טבלה אחת בלבד בעברית, מבוססת טווחים בלבד."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – גרסת MASTER REAL ISRAEL V3")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: מנהל מכירות, מנהל לוגיסטיקה):")
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
        with st.spinner("📡 שולף נתוני אמת ממודעות ישראליות..."):
            real_data = get_real_salary_data(job)

        with st.spinner("🧮 מחשב טווחים ריאליים ומבנה תגמול ישראלי..."):
            md = generate_salary_table(job, exp, real_data)

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

# -------------------------------------------------
# היסטוריית דוחות
# -------------------------------------------------
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_label = "ממוצע שוק" if item["exp"] == 0 else f"{item['exp']} שנות ניסיון"
        with st.expander(f"{item['job']} — {exp_label} — {item['time']}"):
            st.markdown(item["report"], unsafe_allow_html=True)
