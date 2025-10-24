import streamlit as st
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר – גרסת אינטליגנטית ישראלית", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------
# עיצוב פרימיום
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
# פונקציה לזיהוי סוג המשרה – התאמת מבנה תגמול ישראלי
# -------------------------------------------------
def get_sales_type(job_title: str):
    title = job_title.lower()
    if any(word in title for word in ["שטח", "account", "b2b", "לקוחות", "sales executive", "יבוא"]):
        return "field_sales"  # אנשי מכירות שטח / B2B
    elif any(word in title for word in ["טלפ", "מוקד", "נציג", "קמעונ", "shop", "חנות"]):
        return "inside_sales"  # נציגים טלפוניים / ריטייל
    elif any(word in title for word in ["סמנכ", "מנהל מכירות", "ראש תחום", "sales director"]):
        return "managerial_sales"  # תפקידים ניהוליים בכירים
    else:
        return "general"  # שאר התפקידים

# -------------------------------------------------
# הפקת טבלת בנצ'מארק – התאמה חכמה לסוג התפקיד
# -------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    sales_type = get_sales_type(job_title)

    # התאמה חכמה של מבנה תגמול לפי סוג משרה
    if sales_type == "field_sales":
        sales_context = "אין תקרת עמלה. הצג מדרגות תגמול ריאליות: 3%-7% לפי רמות מכירות. הצג עמלות נטו ממכירות בפועל."
    elif sales_type == "inside_sales":
        sales_context = "קיימת תקרת בונוס או עמלה חודשית (עד 4,000 ₪). הצג טווחי עמלות של 1%-3% בלבד."
    elif sales_type == "managerial_sales":
        sales_context = "אין עמלות ישירות. הצג בונוס שנתי מבוסס יעדים עד 25% מהשכר, תקרה של 2-3 משכורות."
    else:
        sales_context = "הצג מבנה תגמול ממוצע בשוק הישראלי לפי מדרגות ביצועים."

    prompt = f"""
אתה אנליסט שכר בכיר בישראל.

צור טבלת בנצ'מארק שכר מקצועית לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.

השתמש בהנחיות לתגמול הבאות:
{sales_context}

הפלט חייב להיות טבלה אחת בלבד בעברית, ללא טקסט נוסף.

כלול את רכיבי השכר הבאים:
שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב (כולל שווי שוק ודגמים), שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, מתנות/ביגוד/רווחה.

לכל רכיב חובה לכלול:
- שלוש רמות תגמול בעמודות (בסיסית, בינונית, גבוהה)
- טווחים ברורים של שכר, אחוזים או סכומים (לדוגמה: 8,000–12,000 ₪ או 3%–6%)
- ממוצע שוק (₪)
- מנגנון תגמול מפורט (לדוגמה: 5% מהמכירות עד תקרה של 8,000 ₪)
- עלות מעסיק ממוצעת (₪)
- אחוז מעלות השכר הכוללת (%)

ברכיב "רכב חברה":
- הצג את שווי השוק של רכב מקובל לתפקיד זה (₪)
- ציין 3 דגמים נפוצים בישראל בשווי זה (לדוגמה: סקודה סופרב, טויוטה קאמרי, מאזדה 6)

בסוף הדוח הוסף סיכום מעוצב וברור:
- עלות מעסיק כוללת (שכר × 1.35 + עלויות נוספות)
- הערכת שווי כוללת של ההטבות (₪)
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט שלך הוא תמיד טבלה אחת בלבד בעברית, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content, sales_type

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – גרסת אינטליגנטית ישראלית")

col1, col2 = st.columns([2, 1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל תיקי לקוחות, נציג מכירות טלפוני):")
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
        with st.spinner("מחשב בנצ'מארק מקיף ומפיק דו״ח חכם..."):
            md, s_type = generate_salary_table(job, exp)

        # הצגת סוג המשרה שזוהה
        mapping = {
            "field_sales": "🟩 תפקיד מכירות שטח / B2B – ללא תקרת עמלה",
            "inside_sales": "🟧 תפקיד מכירות טלפוניות / מוקדים – עם תקרת עמלה",
            "managerial_sales": "🟦 תפקיד ניהולי בכיר – בונוס שנתי בלבד",
            "general": "⬜ תפקיד כללי – מבנה תגמול ממוצע"
        }
        st.info(f"**זוהה סוג משרה:** {mapping.get(s_type)}")

        # הצגת הטבלה
        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        # סיכום מעוצב
        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות (רכב, ביטוחים, סיבוס, קרנות).</div>
          <div class="summary-line">🚗 <span class="summary-value">הטבות ממוצעות:</span> רכב חברה, טלפון נייד, ביטוחים, מתנות ורווחה.</div>
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
