import streamlit as st
from openai import OpenAI, OpenAIError
import os
import pandas as pd
from io import StringIO
from datetime import datetime

# עיצוב RTL
st.set_page_config(page_title="דו״ח שכר ארגוני מפורט", layout="centered")
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1, h2, h3 { color: #1E88E5; }
table { width: 100%; border-collapse: collapse; margin-top: 15px; }
th { background-color: #1976D2; color: white; padding: 10px; text-align: center; }
td { background-color: #FAFAFA; border: 1px solid #E3F2FD; padding: 8px; text-align: center; }
tr:nth-child(even) td { background-color: #F5F5F5; }
.copy-btn { background-color: #42A5F5; color: white; padding: 10px 20px; border-radius: 8px; font-weight: bold; border: none; cursor: pointer; }
.copy-btn:hover { background-color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# היסטוריה
if "history" not in st.session_state:
    st.session_state["history"] = []

st.title("💼 דו״ח בנצ'מארק שכר ארגוני – גרסה מפורטת")
st.markdown("הזן שם משרה כדי להפיק דו״ח מלא הכולל רכיבי שכר, ותק מדויק, הטבות, רכב, והוצאות מעסיק.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, סמנכ״ל מכירות):")

# פונקציה לשליפת הדו"ח
def generate_salary_report(job_title):
    prompt = f"""
    צור דו״ח שכר מפורט בעברית עבור המשרה "{job_title}" בשוק הישראלי.

    הצג רק טבלה אחת בפורמט Markdown עם העמודות הבאות:
    | רכיב שכר | טווח (מינימום–מקסימום) | ממוצע שוק (₪) | מנגנון תגמול מקובל | הערות / פירוט |

    הנחיות:
    - שכר בסיס לפי שנות ניסיון מדויקות:
      • שנה 1 • שנה 3 • שנה 5 • שנה 7 • שנה 10 • שנה 15+
      וציין שכר ממוצע לכל רמה (לדוגמה: שנה 1 – 15,000 ₪, שנה 5 – 20,500 ₪ וכו׳)
    - כלול עמלות, בונוסים, סיבוס, קרן השתלמות, ביטוח, טלפון, רכב חברה, מתנות, הבראה, נסיעות, ביגוד, מחשב נייד.
    - עבור רכב חברה:
      פרט את כל המרכיבים:
        • שווי שימוש חודשי
        • עלות דלק חודשית ממוצעת
        • שווי רכב בשוק (לדוגמה: 180–250 אלף ₪)
        • דגמים מקובלים לפי התפקיד
        • האם הרכב ממומן בליסינג או בבעלות
    - במנגנוני תגמול פרט מדרגות, אחוזים, תקרות, ותנאי זכאות אמיתיים.
    - הנתונים צריכים לשקף חברות דומות ל־Benda Magnetic בע״מ (יבואנים, טכנולוגיה, מוצרי חשמל, גאדג׳טים).
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "אתה יועץ שכר בכיר בישראל. הפלט הוא דו״ח ניהולי אמיתי המוצג להנהלה."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.55,
        )
        return response.choices[0].message.content
    except OpenAIError as e:
        st.error(f"שגיאת OpenAI: {e}")
        return None
    except Exception as e:
        st.error(f"שגיאה כללית: {e}")
        return None

# פונקציה להצגת הדו"ח
def markdown_table_to_html(report):
    lines = [line for line in report.splitlines() if "|" in line]
    data = [line for line in lines if not line.startswith("|-")]
    df = pd.read_csv(StringIO("\n".join(data)), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x: x.strip())
    return df

# הצגת דו"ח
if st.button("🔍 הפק דו״ח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו״ח מלא..."):
            report = generate_salary_report(job_title)
            if report:
                st.success("✅ דו״ח הופק בהצלחה")
                st.markdown("### 📊 טבלת שכר מלאה")
                df = markdown_table_to_html(report)
                st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

                # כפתור העתק דו"ח
                st.components.v1.html(f"""
                <div style="text-align:center; margin-top:15px;">
                    <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                    alert('✅ הדו״ח הועתק ללוח!');">📋 העתק דו״ח</button>
                </div>
                """, height=100)

                st.session_state["history"].append({
                    "job": job_title,
                    "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "report": report
                })

# היסטוריית דוחות
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות קודמים")
    for item in reversed(st.session_state["history"]):
        with st.expander(f"{item['job']} — {item['time']}"):
            st.markdown(item["report"])
