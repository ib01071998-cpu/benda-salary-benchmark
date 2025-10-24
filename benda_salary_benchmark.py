import streamlit as st
import os
from datetime import datetime
import requests
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר בזמן אמת – גרסה ישראלית חכמה", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; }
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
# פונקציות עזר
# -------------------------------------------------
def get_sales_type(job_title: str):
    title = job_title.lower()
    if any(word in title for word in ["שטח", "account", "b2b", "לקוחות", "sales executive", "יבוא"]):
        return "field_sales"
    elif any(word in title for word in ["טלפ", "מוקד", "נציג", "קמעונ", "shop", "חנות"]):
        return "inside_sales"
    elif any(word in title for word in ["סמנכ", "מנהל מכירות", "ראש תחום", "sales director"]):
        return "managerial_sales"
    else:
        return "general"

# -------------------------------------------------
# שליפת נתוני אמת מ-Serper API
# -------------------------------------------------
def fetch_real_data(job_title):
    if not SERPER_API_KEY:
        return "לא הוגדר מפתח Serper API בקובץ .env"
    
    headers = {"X-API-KEY": SERPER_API_KEY}
    query = f"שכר {job_title} ישראל site:alljobs.co.il OR site:drushim.co.il OR site:jobmaster.co.il OR site:ynet.co.il OR site:bizportal.co.il"
    
    response = requests.post(
        "https://google.serper.dev/search",
        headers=headers,
        json={"q": query, "num": 8, "hl": "he"}
    )
    results = response.json()
    snippets = []
    if "organic" in results:
        for r in results["organic"]:
            if "snippet" in r:
                snippets.append(r["snippet"])
    return "\n".join(snippets[:10]) if snippets else "לא נמצאו תוצאות עדכניות."

# -------------------------------------------------
# הפקת דוח GPT עם שילוב הנתונים
# -------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    sales_type = get_sales_type(job_title)
    real_data = fetch_real_data(job_title)

    sales_context = {
        "field_sales": "אין תקרת עמלה ברוב המקרים, אך לעיתים יש תקרה רכה (פי 2 מהבסיס). הצג מדרגות 3%-7%.",
        "inside_sales": "יש תקרת בונוס חודשית (2,000–4,000 ₪). הצג עמלות 1%-3%.",
        "managerial_sales": "אין עמלות ישירות. הצג בונוס שנתי עד 25% מהשכר (תקרה של 3 משכורות).",
        "general": "הצג מבנה תגמול ממוצע בשוק הישראלי."
    }[sales_type]

    prompt = f"""
השתמש במידע הבא שאספת ממקורות ישראליים בזמן אמת:
{real_data}

אתה אנליסט שכר בכיר בישראל. צור טבלת בנצ'מארק לשנת 2025 לתפקיד "{job_title}" {exp_text}.
{sales_context}

הוראות:
- הצג טבלה אחת בלבד בעברית, עם שלוש רמות תגמול (בסיסית / בינונית / גבוהה)
- כלול רכיבים: שכר בסיס, עמלות, בונוסים, אחזקת רכב (עם שווי שוק ודגמים), קרנות, ביטוחים, אש"ל, טלפון, חופשות.
- לכל רכיב: טווחים ריאליים, ממוצע שוק, מנגנון תגמול מפורט (כולל מדרגות ותקרות), עלות מעסיק (₪), אחוז מסך הכולל.
- ברכב: ציין שווי שוק ממוצע (לדוגמה 180–240 אלף ₪) ודגמים (סקודה סופרב, טויוטה קאמרי, מאזדה 6).
- סיים בסיכום קצר עם הערכת עלות מעסיק כוללת.
"""

    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר ישראלי בכיר. הפלט שלך הוא תמיד טבלה אחת בלבד בעברית, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    return r.choices[0].message.content, sales_type

# -------------------------------------------------
# ממשק
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר בזמן אמת – גרסה ישראלית חכמה")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל תיקי לקוחות, נציג מכירות):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):", 0, 40, 0)

if "history" not in st.session_state:
    st.session_state["history"] = []

btn1, btn2 = st.columns([1, 1])
with btn1:
    run = st.button("🚀 הפק דו״ח בזמן אמת")
with btn2:
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state["history"] = []
        st.success("היסטוריה נוקתה ✅")

if run:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מבצע סריקה חכמה של מקורות ישראליים בזמן אמת..."):
            md, s_type = generate_salary_table(job, exp)

        mapping = {
            "field_sales": "🟩 מכירות שטח / B2B – ללא תקרה קשיחה",
            "inside_sales": "🟧 מכירות טלפוניות / מוקדים – עם תקרת בונוס חודשית",
            "managerial_sales": "🟦 ניהול מכירות בכיר – בונוס שנתי עם תקרה",
            "general": "⬜ תפקיד כללי – מבנה תגמול ממוצע"
        }
        st.info(f"**זוהה סוג משרה:** {mapping.get(s_type)}")

        st.markdown("### 📊 טבלת רכיבי שכר בזמן אמת:")
        st.markdown(md, unsafe_allow_html=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">🏢 <span class="summary-value">הדו״ח מבוסס על נתוני אמת ממקורות ישראליים בזמן אמת (AllJobs, Drushim, JobMaster וכו׳).</span></div>
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

# היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report", "אין דו\"ח להצגה"))
