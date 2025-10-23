import streamlit as st
from openai import OpenAI, OpenAIError
import os
import time
import pandas as pd
from io import StringIO
from datetime import datetime

# הגדרות כלליות
st.set_page_config(page_title="מערכת בנצ'מארק שכר חכמה", layout="centered")

# עיצוב ויזואלי בעברית
st.markdown("""
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
tr:nth-child(even) td { background-color: #F5F5F5; }
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
.copy-btn:hover { background-color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# היסטוריית חיפושים
if "history" not in st.session_state:
    st.session_state["history"] = []

st.title("💼 מערכת בנצ'מארק שכר חכמה ומפורטת")
st.markdown("הזן שם משרה בעברית לקבלת טבלת שכר מלאה הכוללת מדרגות ותק, מנגנוני תגמול, שווי רכב וניתוח עלות מעסיק.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל תפעול, סמנכ״ל מכירות, מנהל לוגיסטיקה):")

# יצירת פרומפט לניתוח השכר
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור טבלת שכר אחת בלבד בפורמט Markdown עבור המשרה "{job_title}" בשוק הישראלי.

    הפלט חייב להיות טבלה אחת בלבד בפורמט הבא:
    | רכיב שכר | טווח (מינימום–מקסימום) | ממוצע שוק (₪) | מנגנון תגמול מקובל | הערות / פירוט |

    הנחיות:
    - כלול את הרכיבים: שכר בסיס, עמלות מכירה, בונוסים, סיבוס/תן ביס, טלפון נייד, קרן השתלמות, ביטוח בריאות, פנסיה, רכב חברה.
    - עבור רכיב **שכר בסיס**, פרט מדרגות לפי ניסיון:
        - עד 3 שנות ניסיון (Junior)
        - 3–6 שנות ניסיון (Mid)
        - מעל 6 שנות ניסיון (Senior)
      וציין את השכר המקובל לכל רמה (לדוגמה: Junior – 18K, Mid – 23K, Senior – 28K).
    - במנגנוני תגמול פרט מדרגות עמלות, תקרות, אחוזים, ותנאי זכאות. לדוגמה: “3% עד 200K ₪, 5% מעל”.
    - ברכיב רכב חברה: ציין גם **שווי רכב מקובל בשוק** (לדוגמה: 180–250 אלף ₪) ודגמים (סקודה סופרב, מאזדה 6, טויוטה קאמרי).
    - אל תכתוב טקסט חופשי לפני או אחרי – רק טבלה אחת.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט מוצג למנהלים בכירים וצריך להיות מדויק וברור."},
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

# המרת Markdown ל-DataFrame
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

# חישוב עלות מעסיק ממוצעת
def calculate_employer_cost(df):
    try:
        avg_salary = 0
        for val in df["ממוצע שוק (₪)"]:
            try:
                avg_salary = max(avg_salary, float(str(val).replace("₪", "").replace(",", "").strip()))
            except:
                continue
        employer_cost = int(avg_salary * 1.32)
        return employer_cost
    except:
        return None

# הפעלת הניתוח
if st.button("🔍 הפק טבלת שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק טבלת שכר מקצועית..."):
            report = analyze_salary_gpt(job_title)
            if report:
                df = markdown_table_to_df(report)
                if df is not None:
                    st.success("✅ הטבלה הופקה בהצלחה")
                    st.markdown("### 🧾 טבלת שכר מפורטת")
                    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # חישוב עלות מעסיק כוללת
                    employer_cost = calculate_employer_cost(df)
                    if employer_cost:
                        st.markdown(f"""
                        <div style='background:#E3F2FD;padding:15px;border-radius:10px;margin-top:15px;'>
                        <b>עלות מעסיק כוללת (ממוצעת לפי שוק ישראלי):</b> כ-{employer_cost:,} ₪<br>
                        <small>כולל פנסיה, ביטוח לאומי, קרן השתלמות, הבראה ושווי רכב ממוצע.</small>
                        </div>
                        """, unsafe_allow_html=True)

                        # טבלת פירוק עלות מעסיק
                        st.markdown("#### 📊 פירוק עלות מעסיק ממוצעת")
                        st.table(pd.DataFrame({
                            "רכיב": ["שכר ברוטו", "פנסיה (6.5%)", "ביטוח לאומי (7.6%)", "קרן השתלמות (7.5%)", "אש\"ל/בונוסים (4%)", "רכב חברה (שווי שוק)"],
                            "אחוז מהשכר": ["100%", "6.5%", "7.6%", "7.5%", "4%", "שווי 100–250 אלף ₪"],
                            "הערות": ["שכר חודשי ממוצע", "הפרשת מעביד", "לפי מדרגה ממוצעת", "נהוג בתפקידים בכירים", "מוערך שנתי", "משוקלל לפי דרגה"]
                        }))

                    # כפתור העתק דו"ח
                    st.components.v1.html(f"""
                        <div style="text-align:center; margin-top:15px;">
                            <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                            alert('✅ הטבלה הועתקה ללוח!');">📋 העתק טבלה</button>
                        </div>
                    """, height=100)

                    # שמירה להיסטוריה
                    st.session_state["history"].append({
                        "job": job_title,
                        "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "report": report
                    })

# ספריית היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות קודמים")
    for item in reversed(st.session_state["history"]):
        with st.expander(f"{item['job']} — {item['time']}"):
            st.markdown(item["report"])
