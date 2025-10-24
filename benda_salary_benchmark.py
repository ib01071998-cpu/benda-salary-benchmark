import streamlit as st
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות כלליות
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר ישראלית חכמה", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------
# עיצוב מקצועי ברמה עסקית גבוהה
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
# פונקציה לזיהוי סוג המשרה
# -------------------------------------------------
def get_sales_type(job_title: str):
    title = job_title.lower()
    if any(word in title for word in ["שטח", "account", "b2b", "לקוחות", "sales executive", "יבוא"]):
        return "field_sales"  # אנשי מכירות שטח / B2B
    elif any(word in title for word in ["טלפ", "מוקד", "נציג", "קמעונ", "shop", "חנות"]):
        return "inside_sales"  # נציגים טלפוניים / ריטייל
    elif any(word in title for word in ["סמנכ", "מנהל מכירות", "ראש תחום", "sales director"]):
        return "managerial_sales"  # ניהול מכירות בכיר
    else:
        return "general"  # אחר

# -------------------------------------------------
# הפקת טבלת בנצ'מארק אמיתית
# -------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"עבור {experience} שנות ניסיון"
    sales_type = get_sales_type(job_title)

    # 🎯 התאמה לשוק הישראלי – לא מסיר תקרות, רק מציג כשמקובל
    if sales_type == "field_sales":
        sales_context = (
            "במכירות שטח / B2B בישראל לרוב אין תקרת עמלה, אך במקרים של עסקאות פרויקטליות או מכירות עתירות רווח "
            "נהוגה תקרה רכה של עד פי 2 משכר הבסיס. הצג מדרגות עמלות מפורטות (3%-7%) לפי היקף המכירות בפועל."
        )
    elif sales_type == "inside_sales":
        sales_context = (
            "במכירות טלפוניות, מוקדים וחנויות נהוגה תקרת בונוס חודשית ברורה (2,000–4,000 ₪). "
            "הצג עמלות נמוכות (1%-3%) ובונוסים לפי עמידה ביעדים."
        )
    elif sales_type == "managerial_sales":
        sales_context = (
            "בסמנכ\"לי מכירות ומנהלי תחום נהוג בונוס שנתי של 10%-25% מהשכר השנתי, "
            "עם תקרה של 2–3 משכורות, ללא עמלות ישירות."
        )
    else:
        sales_context = (
            "לתפקיד זה הצג מבנה תגמול ממוצע בשוק הישראלי, כולל עמלות, בונוסים והטבות כפי שנהוג בחברות בינוניות וגדולות."
        )

    prompt = f"""
אתה אנליסט שכר בכיר בישראל.
צור טבלת בנצ'מארק מקצועית לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.

{sales_context}

דרישות הפלט:
- טבלה אחת בלבד בעברית, ללא מלל נוסף.
- הצג שלוש רמות תגמול (בסיסית / בינונית / גבוהה).
- לכל רכיב שכר: הצג טווחים ריאליים (₪ או אחוזים), ממוצע שוק, מנגנון תגמול מפורט (כולל מדרגות עמלות ותקרות אם קיימות), עלות מעסיק ממוצעת (₪) ואחוז מסך הכולל (%).
- ברכיב "רכב חברה" יש לציין בעמודת מנגנון תגמול את שווי השוק של הרכב (לדוגמה 180–240 אלף ₪) ושלושה דגמים נפוצים בישראל.
- ברכיבים משתנים כמו עמלות ובונוסים יש להציג 3 מנגנוני תגמול חלופיים ומפורטים (לדוגמה מדרגות עמלות או יעדים שונים).
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
        with st.spinner("מחשב בנצ'מארק אמיתי ומפיק דו״ח חכם..."):
            md, s_type = generate_salary_table(job, exp)

        mapping = {
            "field_sales": "🟩 תפקיד מכירות שטח / B2B – לרוב ללא תקרת עמלה",
            "inside_sales": "🟧 מכירות טלפוניות / ריטייל – תקרת בונוס חודשית",
            "managerial_sales": "🟦 ניהול בכיר – בונוס שנתי בלבד",
            "general": "⬜ תפקיד כללי – תגמול ממוצע בשוק"
        }
        st.info(f"**זוהה סוג משרה:** {mapping.get(s_type)}")

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות (רכב, ביטוחים, קרנות, רווחה).</div>
          <div class="summary-line">🚗 <span class="summary-value">הטבות ממוצעות:</span> רכב חברה (180–240 אלף ₪), טלפון, ביטוחים, אש"ל ורווחה.</div>
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
