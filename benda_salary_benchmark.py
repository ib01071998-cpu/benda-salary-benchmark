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
# זיהוי סוג משרה
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
# יצירת טבלת בנצ'מארק
# -------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    sales_type = get_sales_type(job_title)

    # 🎯 התאמה חכמה לתקרות לפי סוג תפקיד – לא מוחקת תקרה, רק מציגה כשמקובל
    if sales_type == "field_sales":
        sales_context = (
            "לתפקידי מכירות שטח בישראל לרוב אין תקרת עמלה, אך כאשר מדובר במכירת פרויקטים או עסקאות עתירות רווח "
            "נהוג לקבוע תקרה רכה סביב פי 2 משכר הבסיס. הצג מדרגות עמלות ריאליות (3%-7%) עם מנגנון תגמול מפורט."
        )
    elif sales_type == "inside_sales":
        sales_context = (
            "בתפקידי מכירות טלפוניות, מוקדים או חנויות קמעונאות נהוגה תקרת בונוס חודשית ברורה (2,000–4,000 ₪). "
            "הצג טווחי עמלות 1%-3% ותקרות בהתאם לשוק."
        )
    elif sales_type == "managerial_sales":
        sales_context = (
            "בתפקידי ניהול בכירים (כגון סמנכ\"ל מכירות או מנהל תחום), אין עמלות ישירות אלא בונוס שנתי מבוסס יעדים "
            "עם תקרה של 2–3 משכורות שנתיות. הצג את מנגנון הבונוס במפורט."
        )
    else:
        sales_context = (
            "לתפקיד זה הצג מבנה תגמול ממוצע בשוק הישראלי, כולל תקרות רק אם הן מקובלות במשרות דומות."
        )

    prompt = f"""
אתה אנליסט שכר בכיר בישראל.
צור טבלת בנצ'מארק לתפקיד "{job_title}" {exp_text} לשנת 2025.

{sales_context}

עבור רכיב 'רכב חברה':
- בעמודת מנגנון תגמול יש לציין גם את שווי השוק של הרכב (למשל 180–240 אלף ₪)
- יש לציין שלושה דגמים נפוצים בישראל בשווי זה (למשל סקודה סופרב, טויוטה קאמרי, מאזדה 6).

בכל יתר הרכיבים:
- הצג שלוש רמות תגמול (בסיסית / בינונית / גבוהה)
- הצג טווחים ריאליים, ממוצע שוק, מנגנון תגמול מפורט (כולל מדרגות עמלות, תקרות אם יש, בונוסים וקרנות)
- הצג עלות מעסיק ממוצעת (₪)
- הצג אחוז מסך השכר הכולל (%)
- אל תוסיף טקסט מחוץ לטבלה.
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט שלך הוא תמיד טבלה אחת בלבד בעברית, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )
    return r.choices[0].message.content, sales_type

# -------------------------------------------------
# ממשק משתמש
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

        mapping = {
            "field_sales": "🟩 תפקיד מכירות שטח / B2B – לרוב ללא תקרת עמלה, אלא תקרה רכה בלבד",
            "inside_sales": "🟧 תפקיד מכירות טלפוניות / מוקדים – תקרה חודשית ברורה",
            "managerial_sales": "🟦 תפקיד ניהולי בכיר – בונוס שנתי עם תקרה של 2–3 משכורות",
            "general": "⬜ תפקיד כללי – מבנה תגמול ממוצע"
        }
        st.info(f"**זוהה סוג משרה:** {mapping.get(s_type)}")

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות (רכב, ביטוחים, קרנות).</div>
          <div class="summary-line">🚗 <span class="summary-value">הטבות ממוצעות:</span> רכב חברה (180–240 אלף ₪), טלפון, ביטוחים, רווחה.</div>
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
