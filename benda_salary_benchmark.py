import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os
import pandas as pd
from io import StringIO
from datetime import datetime

# הגדרות כלליות
st.set_page_config(page_title="טבלת בנצ'מארק שכר", layout="centered")

# עיצוב RTL וטבלה מקצועית
st.markdown(
    """
    <style>
    * { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
    h1, h2, h3 { color: #1E88E5; }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        border: 1px solid #E0E0E0;
    }
    th {
        background-color: #1976D2;
        color: white;
        padding: 12px;
        font-weight: bold;
        border: 1px solid #BBDEFB;
        text-align: center;
    }
    td {
        background-color: #FAFAFA;
        border: 1px solid #E3F2FD;
        padding: 10px;
        text-align: center;
        vertical-align: middle;
        font-size: 15px;
    }
    tr:nth-child(even) td {
        background-color: #F5F5F5;
    }
    .copy-btn {
        background-color: #42A5F5;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        border: none;
        font-size: 16px;
    }
    .copy-btn:hover {
        background-color: #1E88E5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# היסטוריית חיפושים
if "history" not in st.session_state:
    st.session_state["history"] = []

st.title("💼 טבלת בנצ'מארק שכר מקצועית ומפורטת")
st.markdown("הזן שם משרה כדי להפיק טבלת שכר מפורטת הכוללת מנגנוני תגמול, הטבות, ועלות מעסיק ממוצעת.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, סמנכ״ל מכירות, מנהל תפעול):")

# פונקציה לניתוח השכר
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור טבלת שכר אחת בלבד בפורמט Markdown עבור המשרה "{job_title}" בשוק הישראלי.
    אל תכתוב טקסט לפני או אחרי — רק טבלה אחת בפורמט הבא:

    | רכיב שכר | טווח (מינימום–מקסימום) | ממוצע שוק (₪) | מנגנון תגמול מקובל | הערות / פירוט |

    **הנחיות:**
    - כלול: שכר בסיס, עמלות מכירה, בונוסים, סיבוס / תן ביס, טלפון נייד, קרן השתלמות, ביטוח בריאות, פנסיה, רכב חברה.
    - ברכיב "רכב חברה": כלול דגמים מקובלים (סקודה סופרב, מאזדה 6, טויוטה קאמרי) ושווי שימוש ממוצע בש״ח.
    - במנגנוני התגמול פרט מדרגות, אחוזים, תנאי זכאות, תקרות, ותדירות תשלום.
    - כלול דוגמה ריאלית (לדוגמה: "3% עד 200K ₪, 5% מעל").
    - כתוב רק טבלה אחת, קריאה וברורה.

    בסיום, הוסף משפט אחד שמסכם:
    "**עלות מעסיק כוללת (ממוצעת לפי שוק ישראלי):** כ-{int(ממוצע השכר * 1.3)} ₪, כולל הפרשות סוציאליות, קרן השתלמות, ביטוח לאומי ושווי רכב."
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט מוצג למנהלים בכירים והוא חייב להיות ריאלי וברור."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.55,
            )
            return response.choices[0].message.content
        except Exception as e:
            st.error(f"שגיאה: {e}")
            return None


# המרת טבלת Markdown ל-DataFrame
def markdown_table_to_df(markdown_text):
    try:
        lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
        data_lines = [line for line in lines if not line.startswith("|-")]
        df = pd.read_csv(StringIO("\n".join(data_lines)), sep="|").dropna(axis=1, how="all")
        df = df.rename(columns=lambda x: x.strip())
        df = df.drop(df.index[0]) if df.iloc[0].str.contains("רכיב").any() else df
        return df
    except Exception as e:
        st.error(f"שגיאה בעיבוד הטבלה: {e}")
        return None


# הפעלת הניתוח
if st.button("🔍 הפק טבלת שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק טבלת שכר..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ טבלת השכר הופקה בהצלחה")
                df = markdown_table_to_df(report)
                if df is not None:
                    st.markdown("### 🧾 טבלת שכר מסכמת")
                    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # הוספת משפט סיכום עלות מעסיק
                    st.markdown("<br><b>עלות מעסיק כוללת:</b> מחושבת לפי ממוצע שוק (כ-30% תוספת על השכר החודשי).", unsafe_allow_html=True)

                    # כפתור העתק דו"ח
                    st.components.v1.html(
                        f"""
                        <div style="text-align:center; margin-top:15px;">
                            <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                            alert('✅ הטבלה הועתקה ללוח!');">
                                📋 העתק טבלה
                            </button>
                        </div>
                        """,
                        height=100,
                    )

                    # שמירה בהיסטוריה
                    st.session_state["history"].append({
                        "job": job_title,
                        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "report": report
                    })
                else:
                    st.markdown(report)

# הצגת ספריית היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for i, item in enumerate(st.session_state["history"][::-1]):
        with st.expander(f"{item['job']} — {item['time']}"):
            st.markdown(item["report"])
