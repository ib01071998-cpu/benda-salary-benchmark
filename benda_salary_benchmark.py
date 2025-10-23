import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import os
import time
import pandas as pd
from io import StringIO
from datetime import datetime

# הגדרות כלליות
st.set_page_config(page_title="טבלת בנצ'מארק שכר מקצועית", layout="centered")

# עיצוב ויזואלי נקי בעברית
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

st.title("💼 טבלת בנצ'מארק שכר מקצועית ומפורטת")
st.markdown("הזן שם משרה בעברית כדי להפיק טבלת שכר הכוללת מנגנוני תגמול, פירוט רכב וניתוח עלות מעסיק ממוצעת לפי המשק הישראלי.")

job_title = st.text_input("שם המשרה (לדוגמה: סמנכ״ל מכירות, מנהל לוגיסטיקה, ראש צוות שירות):")

# פונקציה שמדברת עם GPT
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור טבלת שכר אחת בלבד בפורמט Markdown עבור המשרה "{job_title}" בשוק הישראלי.
    אל תכתוב טקסט לפני או אחרי — רק טבלה אחת בפורמט הבא:

    | רכיב שכר | טווח (מינימום–מקסימום) | ממוצע שוק (₪) | מנגנון תגמול מקובל | הערות / פירוט |

    הנחיות:
    - כלול את הרכיבים: שכר בסיס, עמלות מכירה, בונוסים, סיבוס / תן ביס, טלפון נייד, קרן השתלמות, ביטוח בריאות, פנסיה, רכב חברה.
    - עבור רכיב "רכב חברה": ציין דגמים מקובלים (סקודה סופרב, מאזדה 6, טויוטה קאמרי) וכתוב גם "שווי רכב מקובל בשוק" (לדוגמה: 180,000–250,000 ₪) בנוסף לשווי שימוש חודשי.
    - במנגנוני תגמול פרט מדרגות עמלות, אחוזים, תקרות בונוס, תנאי זכאות, תדירות תשלום, ודוגמה ריאלית אחת.
    - הנתונים צריכים להיות תואמים לשוק חברות כמו Benda Magnetic (יבוא, טכנולוגיה, מוצרי חשמל, גאדג'טים).

    התוצאה: טבלה אחת בלבד, מקצועית וברורה, ללא טקסט נוסף.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט מוצג למנהלים בכירים וצריך להיות מדויק, ריאלי וברור."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"שגיאה בתקשורת עם OpenAI: {e}")
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

                    # הצגת טבלת השכר
                    st.markdown("### 🧾 טבלת שכר מסכמת")
                    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # חישוב עלות מעסיק
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
                            "הערות": ["שכר בסיס", "הפרשת מעביד", "לפי מדרגה ממוצעת", "נהוג בתפקידים בכירים", "מוערך שנתי", "משוקלל לפי דרגה"]
                        }))

                    # כפתור העתק
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
                else:
                    st.markdown(report)

# ספריית היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית חיפושים")
    for item in reversed(st.session_state["history"]):
        with st.expander(f"{item['job']} — {item['time']}"):
            st.markdown(item["report"])
