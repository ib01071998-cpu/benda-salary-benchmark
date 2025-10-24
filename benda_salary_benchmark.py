import streamlit as st
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="בנצ'מארק שכר ישראל – דוח מקצועי", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------
# עיצוב כללי
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:4px; }
h2 { color:#1565C0; font-weight:800; margin-top:20px; }
table {width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden; box-shadow:0 3px 12px rgba(0,0,0,0.1)}
th {background:#1976D2;color:#fff;padding:12px; font-weight:700; border:1px solid #E3F2FD; text-align:center}
td {background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center;font-size:15px}
tr:nth-child(even) td {background:#F9FBE7}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
.summary-box {background:#E3F2FD; padding:20px; border-radius:12px; text-align:center; margin-top:25px; box-shadow:inset 0 0 8px rgba(0,0,0,0.1);}
.summary-line {font-size:18px; font-weight:600; color:#0D47A1;}
.summary-value {font-size:22px; font-weight:800; color:#1E88E5;}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# הפונקציה שמפיקה את טבלת הבנצ'מארק
# -------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    prompt = f"""
צור טבלת בנצ'מארק שכר מקצועית לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.
הפלט חייב להיות טבלה בלבד בעברית, ברמה של חברת ייעוץ שכר כמו צבירן או פילת, ללא הסברים מסביב.

יש לכלול את כלל רכיבי השכר הבאים:
שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב (כולל שווי שוק ודגמים), שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, מתנות/ביגוד/רווחה.

לכל רכיב חובה לכלול:
- טווח שכר (₪)
- ממוצע שוק (₪)
- מנגנון תגמול מפורט
- **עבור רכיבי שכר משתנים (כמו עמלות, בונוסים, מענקים וכו') יש להציג שלושה מנגנוני תגמול שונים ומפורטים**, לדוגמה: 5% מהמכירות עד תקרה של 8,000 ₪, או בונוס שנתי של שתי משכורות.
- אחוז חברות שמציעות את הרכיב
- מגמת שוק (עולה / יציב / בירידה)
- עלות מעסיק ממוצעת (₪)
- אחוז מכלל עלות השכר הכוללת

בסעיף "רכב חברה":
- יש לציין את **שווי השוק של הרכב המקובל** לאותה רמת תפקיד.
- יש לציין **3 דגמים נפוצים** שניתנים לרכב חברה ברמה זו (למשל: סקודה סופרב, טויוטה קאמרי, מאזדה 6).

בסוף הדוח יש להוסיף **סיכום מעוצב וברור** הכולל:
- שכר ברוטו ממוצע כולל.
- עלות מעסיק כוללת ממוצעת (בהתאם ליחס ממוצע של 1.35 משכר הברוטו).
- הערכת שווי כוללת להטבות (סיבוס, טלפון, רכב וכו').
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלה בעברית בלבד, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content


# -------------------------------------------------
# ממשק משתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – דוח פרימיום ישראלי")

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
        with st.spinner("מפיק דוח בנצ'מארק מקצועי ומפורט..."):
            md = generate_salary_table(job, exp)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        # חלק סיכום יפהפה
        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">💰 <span class="summary-value">שכר ברוטו ממוצע כולל:</span> מחושב לפי טווחי השכר בטבלה.</div>
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר ברוטו × 1.35 + עלויות נלוות (רכב, סיבוס, ביטוחים).</div>
          <div class="summary-line">🚗 <span class="summary-value">הטבות ממוצעות:</span> רכב חברה, טלפון, ביטוח בריאות, סיבוס, מתנות.</div>
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

# היסטוריית דוחות
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report", "אין דו\"ח להצגה"))
