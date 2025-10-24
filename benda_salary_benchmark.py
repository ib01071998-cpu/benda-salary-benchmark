import streamlit as st
import os, re, requests, statistics
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="בנצ'מארק שכר ישראל – MASTER REAL+", layout="wide")
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
# פונקציה לשאיבת נתוני אמת מהשוק (SERPER)
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
    numbers = []

    for src in sources:
        payload = {"q": f"שכר {job_title} {src}"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10)
            data = r.json().get("organic", [])
            for item in data:
                snippet = item.get("snippet", "")
                if snippet:
                    all_snippets.append(snippet)
                    # חילוץ טווחי שכר (לדוגמה: 12-18 אלף)
                    found = re.findall(r'(\d{1,3}(?:,\d{3})?)[\s\-–]{1,3}(\d{1,3}(?:,\d{3})?)', snippet)
                    for match in found:
                        try:
                            n1, n2 = [int(re.sub(r'[^\d]', '', x)) for x in match]
                            if 2000 < n1 < 100000 and 2000 < n2 < 100000:
                                numbers.append((n1 + n2) / 2)
                        except:
                            pass
        except Exception as e:
            continue

    avg_salary = round(statistics.mean(numbers)) if numbers else None
    return {"snippets": " ".join(all_snippets[:40]), "avg": avg_salary}

# -------------------------------------------------
# בניית טבלת בנצ'מארק
# -------------------------------------------------
def generate_salary_table(job_title, experience, real_data):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    snippets = real_data.get("snippets", "")
    avg = real_data.get("avg", "לא זמין")

    prompt = f"""
להלן מידע ממקורות ישראליים על שכר לתפקיד "{job_title}" בישראל לשנת 2025:
{snippets}

הממוצע המשוער לפי מקורות אמיתיים הוא: {avg} ₪.

צור טבלת בנצ'מארק שכר מקצועית עם הנתונים הבאים:

יש לכלול את כלל רכיבי השכר הרלוונטיים:
שכר בסיס, עמלות, בונוסים, מענקים, שעות נוספות, אחזקת רכב, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, מתנות/רווחה.

לכל רכיב חובה לכלול:
- טווחים אמיתיים (₪ או אחוזים) לפי השוק.
- שלוש רמות תגמול (בסיסית, בינונית, גבוהה).
- ממוצע באותו פרמטר (₪ / %).
- **מנגנון תגמול מפורט** – המבוסס על נורמות מקובלות בישראל, לדוגמה:
  - עמלות: 3%–5% מהמכירות עם תקרה של 10,000 ₪.
  - בונוסים: בונוס שנתי עד 2 משכורות, לפי עמידה ביעדים.
  - רכב: רכב צמוד בשווי שוק 120–160 אלף ₪ (סקודה סופרב, טויוטה קאמרי, מאזדה 6), כולל ביטוח ותחזוקה.
  - דלק: לרוב כלול ברכב צמוד, או החזר של 1,500–2,000 ₪ לעובד עם רכב פרטי.
  - שעות נוספות: 125%–150% לפי חוק.
- עלות מעסיק ממוצעת (₪).
- אחוז מעלות השכר הכוללת (%).

בסוף הדו"ח הצג תיבת סיכום הכוללת:
- שכר ברוטו ממוצע כולל (₪).
- עלות מעסיק כוללת משוערת (₪).
- סך שווי ההטבות (₪).
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלה אחת בלבד בעברית, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק משתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – גרסת MASTER REAL+")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל לוגיסטיקה):")
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
        with st.spinner("📡 שולף נתוני אמת ממקורות ישראליים..."):
            real_data = get_real_salary_data(job)

        with st.spinner("מחשב בנצ'מארק חכם על סמך נתוני אמת..."):
            md = generate_salary_table(job, exp, real_data)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">💰 <span class="summary-value">שכר ברוטו ממוצע כולל:</span> לפי טווחי השכר בטבלה.</div>
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות (רכב, דלק, ביטוחים).</div>
          <div class="summary-line">🚗 <span class="summary-value">הטבות משוקללות:</span> רכב חברה (כולל דלק וביטוח), טלפון נייד, קרן השתלמות.</div>
        </div>
        """, unsafe_allow_html=True)

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
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report", "אין דו\"ח להצגה"))
