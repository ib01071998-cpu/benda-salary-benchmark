import streamlit as st
import os, re, requests
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות כלליות
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר – ישראל", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------
# עיצוב מקצועי
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:8px; }
h2 { color:#1565C0; font-weight:800; border-bottom:2px solid #BBDEFB; padding-bottom:4px; margin-top:18px; }
table{width:100%; border-collapse:collapse; border-radius:10px; overflow:hidden; box-shadow:0 3px 10px rgba(0,0,0,.08)}
th{background:#1976D2;color:#fff;padding:12px; font-weight:800; border:1px solid #E3F2FD; text-align:center}
td{background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center;font-size:15px}
tr:nth-child(even) td{background:#F1F8E9}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
.stButton>button {
  background: linear-gradient(90deg,#1976D2,#42A5F5); color:#fff; border:none; border-radius:10px;
  font-weight:700; padding:10px 20px; box-shadow:0 2px 10px rgba(0,0,0,.15);
}
.summary-box {
  background: #E3F2FD; border-left: 6px solid #1565C0; padding: 16px;
  border-radius: 10px; margin-top: 25px; line-height: 1.8; font-size: 16px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# יצירת טבלת בנצ'מארק מלאה
# -------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"

    prompt = f"""
צור טבלת בנצ'מארק שכר מפורטת לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.

יש לכלול את כלל רכיבי השכר הרלוונטיים במשק הישראלי, כולל רכיבים קבועים ומשתנים.

לכל רכיב חובה לציין:
- טווח שכר (₪)
- ממוצע שוק (₪)
- מנגנון תגמול מפורט ומבוסס שוק (אם משתנה – הצג 3 מנגנונים חלופיים ומלאים)
- אחוז חברות שמציעות את הרכיב
- מגמת שוק (עולה / יציב / בירידה)
- עלות מעסיק ממוצעת (₪)
- אחוז מהרכב השכר הכולל

בסוף הדוח הצג סיכום ברור ומעוצב הכולל:
- שכר ברוטו ממוצע כולל
- עלות מעסיק כוללת ממוצעת (יחס של כ-1.35 מהברוטו)
- הערות אנליסטיות (לדוגמה: "קיימת עלייה בביקוש למנהלים בתחום זה, הצפויה לעלות את רמות השכר ברבעון הקרוב")

התאם את רמת הפירוט לרמת דוח מקצועי של חברת ייעוץ שכר בכירה בישראל.
"""

    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה בלבד בעברית, ולאחריה סיכום מעוצב וברור."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – שוק העבודה בישראל")
st.caption("מבוסס GPT-4 Turbo | ניתוח מקיף של רכיבי שכר ומנגנוני תגמול במשק הישראלי")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל תפעול, מנהל שיווק):")
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
        with st.spinner("מחשב בנצ'מארק ומפיק דו\"ח מקצועי..."):
            md = generate_salary_table(job, exp)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job,
            "exp": exp,
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
        with st.expander(f"{item.get('job', 'לא צויין')} — {exp_label} — {item.get('time', 'לא ידוע')}"):
            st.markdown(item.get("report", "אין דו\"ח להצגה"))
