import streamlit as st
from openai import OpenAI
import pandas as pd
from io import StringIO
import os
from datetime import datetime

# הגדרות כלליות
st.set_page_config(page_title="דו\"ח שכר ארגוני מפורט – צבירן אלפא", layout="wide")

# עיצוב
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1, h2, h3 { color: #1565C0; text-align: center; }
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    border: 1px solid #E0E0E0;
}
th {
    background-color: #0D47A1;
    color: white;
    padding: 10px;
    font-weight: bold;
    border: 1px solid #E3F2FD;
}
td {
    background-color: #FAFAFA;
    border: 1px solid #E3F2FD;
    padding: 8px;
    text-align: center;
    font-size: 14px;
}
tr:nth-child(even) td { background-color: #E8F5E9; }
.copy-btn {
    background-color: #42A5F5;
    color: white;
    padding: 10px 20px;
    border-radius: 8px;
    font-weight: bold;
    border: none;
    cursor: pointer;
}
.copy-btn:hover { background-color: #1E88E5; }
</style>
""", unsafe_allow_html=True)

# יצירת לקוח GPT
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# היסטוריה
if "history" not in st.session_state:
    st.session_state["history"] = []

st.title("📊 דו\"ח שכר ארגוני מפורט – מערכת 'צבירן אלפא'")
st.markdown("הזן שם משרה לקבלת טבלה מלאה הכוללת את כל רכיבי השכר, ההטבות, מנגנוני התגמול וניתוח עלות המעסיק הכוללת.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל תפעול, סמנכ\"ל מכירות, מנהל לוגיסטיקה):")

# הפעלת GPT
def generate_salary_table(job_title):
    prompt = f"""
    צור טבלת שכר אחת בלבד, מקצועית ומפורטת מאוד, בעברית, עבור המשרה "{job_title}" בשוק הישראלי.

    אל תכתוב שום טקסט חופשי לפני או אחרי.
    הטבלה חייבת לכלול את העמודות הבאות:
    | רכיב | פירוט לפי שנות ניסיון (1, 3, 5, 7, 10, 15+) | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | פירוט רכיב השכר | עלות מעסיק (₪) | אחוז מעלות כוללת |

    הנחיות:
    - הצג שכר בסיס לפי שנות ניסיון מדויקות (1, 3, 5, 7, 10, 15+).
    - כלול את כל רכיבי השכר הקיימים בשוק הישראלי: בסיס, עמלות, בונוסים, סיבוס, טלפון, מחשב, ביטוחים, קרן השתלמות, הבראה, נסיעות, חניה, ביגוד, מתנות, הכשרות, ימי חופשה.
    - בסעיף רכב חברה:
      ציין:
        • שווי שימוש חודשי (₪)
        • עלות דלק ממוצעת (₪)
        • שווי רכב בשוק (₪)
        • דגמים לפי דרג
        • סוג המימון (ליסינג / בעלות)
    - הוסף מנגנוני תגמול מדויקים (לדוגמה: 3%–6% מהמכירות, בונוס רבעוני 8–15K ₪ לפי יעד).
    - הצג טווחי עלות מעסיק (לדוגמה: 28,000–32,500 ₪).
    - הצג אחוז מכלל עלות המעסיק.
    - כלל לפחות 15 רכיבים שונים.
    - אל תכתוב טקסט נוסף.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלת נתונים בלבד, ללא מלל נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.55,
    )
    return response.choices[0].message.content

# המרה לטבלה
def markdown_to_df(markdown_text):
    lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
    clean = [line for line in lines if not line.startswith("|-")]
    df = pd.read_csv(StringIO("\n".join(clean)), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x: x.strip())
    df = df.drop(df.index[0]) if df.iloc[0].str.contains("רכיב").any() else df
    return df

# חישוב עלות מעסיק כוללת
def calculate_total_employer_cost(df):
    try:
        # חילוץ סכומים מעמודת עלות מעסיק
        numeric_values = []
        for val in df["עלות מעסיק (₪)"]:
            text = str(val).replace("₪", "").replace(",", "").strip()
            if "–" in text:
                parts = [p.strip() for p in text.split("–")]
                numbers = [float(p) for p in parts if p.isdigit()]
                if len(numbers) == 2:
                    avg_val = sum(numbers) / 2
                    numeric_values.append(avg_val)
            elif text.replace(".", "", 1).isdigit():
                numeric_values.append(float(text))
        if numeric_values:
            total_cost = sum(numeric_values)
            return total_cost
        return None
    except Exception:
        return None

# הפעלת המודל
if st.button("🔍 הפק דו\"ח"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו\"ח מלא... אנא המתן..."):
            report = generate_salary_table(job_title)
            df = markdown_to_df(report)
            st.success("✅ דו\"ח הופק בהצלחה")

            # הצגת טבלה
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

            # חישוב סה״כ עלות מעסיק
            total_cost = calculate_total_employer_cost(df)
            if total_cost:
                st.markdown(f"""
                <div style='background:#E3F2FD;padding:15px;border-radius:10px;margin-top:15px;'>
                <b>סה״כ עלות מעסיק כוללת:</b> כ-{total_cost:,.0f} ₪<br>
                <small>הכוללת שכר, הטבות, תגמולים, ורכב חברה.</small>
                </div>
                """, unsafe_allow_html=True)

            # שמירה להיסטוריה
            st.session_state["history"].append({
                "job": job_title,
                "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "report": report
            })

            # כפתור העתק
            st.components.v1.html(f"""
            <div style="text-align:center; margin-top:15px;">
                <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                alert('✅ הדו\"ח הועתק ללוח!');">📋 העתק דו\"ח</button>
            </div>
            """, height=100)

# היסטוריית דוחות
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות קודמים")
    for item in reversed(st.session_state["history"]):
        with st.expander(f"{item['job']} — {item['time']}"):
            st.markdown(item["report"])
