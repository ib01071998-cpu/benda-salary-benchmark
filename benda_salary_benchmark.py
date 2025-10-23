import streamlit as st
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
import os

# הגדרות כלליות
st.set_page_config(page_title="דו\"ח שכר ארגוני – PRO", layout="wide")

# 🎨 עיצוב מקצועי ומרשים
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
body { background-color: #f6f9fc; }
h1 { color: #0D47A1; text-align: center; font-weight: 900; font-size: 36px; margin-bottom: 8px; }
h3 { color: #1565C0; margin-top: 25px; }
.stButton>button {
    background: linear-gradient(90deg, #1976D2, #42A5F5);
    color: white;
    padding: 10px 28px;
    border-radius: 10px;
    border: none;
    font-size: 16px;
    font-weight: bold;
    box-shadow: 0px 4px 12px rgba(0,0,0,0.15);
    transition: all 0.3s ease;
}
.stButton>button:hover {
    transform: scale(1.03);
    background: linear-gradient(90deg, #0D47A1, #2196F3);
}
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 25px;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
}
th {
    background-color: #1565C0;
    color: white;
    padding: 14px;
    font-weight: 700;
    font-size: 15px;
    border: 1px solid #E3F2FD;
    text-align: center;
}
td {
    background-color: #FFFFFF;
    border: 1px solid #E3F2FD;
    padding: 10px;
    text-align: center;
    font-size: 14px;
}
tr:nth-child(even) td { background-color: #F1F8E9; }
tfoot td {
    background-color: #BBDEFB;
    font-weight: 800;
    color: #0D47A1;
    border-top: 2px solid #0D47A1;
}
.copy-btn {
    background: linear-gradient(90deg, #1E88E5, #42A5F5);
    color: white;
    padding: 12px 32px;
    border-radius: 10px;
    border: none;
    font-weight: bold;
    cursor: pointer;
    font-size: 17px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.2);
    transition: all 0.3s ease;
}
.copy-btn:hover {
    transform: scale(1.05);
    background: linear-gradient(90deg, #0D47A1, #1E88E5);
}
</style>
""", unsafe_allow_html=True)

# API
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# פונקציות חישוב
def calc_employer_cost(salary):
    return round(salary * 1.32, 2)

def markdown_to_df(markdown_text):
    lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
    clean = [line for line in lines if not line.startswith("|-")]
    df = pd.read_csv(StringIO("\n".join(clean)), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x: x.strip())
    df = df.drop(df.index[0]) if df.iloc[0].str.contains("רכיב").any() else df
    return df

def calculate_from_table(df):
    numeric_values = []
    for val in df["עלות מעסיק (₪)"]:
        txt = str(val).replace("₪", "").replace(",", "").strip()
        if "–" in txt:
            parts = [p.strip() for p in txt.split("–") if p.replace('.', '', 1).isdigit()]
            if len(parts) == 2:
                avg_val = (float(parts[0]) + float(parts[1])) / 2
                numeric_values.append(avg_val)
        elif txt.replace('.', '', 1).isdigit():
            numeric_values.append(float(txt))
    if not numeric_values:
        return None, None
    total = sum(numeric_values)
    employer_total = calc_employer_cost(total)
    return round(total, 2), round(employer_total, 2)

# GPT
def generate_salary_table(job_title):
    prompt = f"""
    צור טבלת שכר מקצועית בעברית, הכוללת רק רכיבי שכר ישירים, עבור המשרה "{job_title}" בישראל.
    כלול עמודות: | רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | פירוט רכיב | עלות מעסיק (₪) | אחוז מעלות כוללת |
    כלול רכיבים: שכר בסיס, עמלות, בונוסים, סיבוס/אש"ל, טלפון, מחשב, ביטוחים, פנסיה, קרן השתלמות, נסיעות, הבראה, שעות נוספות, רכב חברה.
    פרט מנגנוני תגמול מדויקים (אחוזים / סכומים / חישוב שנתי).
    סיים עם שורה מסכמת של סה"כ כולל.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה בלבד."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.45,
    )
    return response.choices[0].message.content

# UI ראשי
st.title("📊 דו\"ח שכר ארגוני – PRO")
st.caption("דו״ח מקצועי הכולל רכיבי שכר ישירים וניתוח עלות מעסיק כולל")

job_title = st.text_input("הזן שם משרה (לדוגמה: סמנכ״ל מכירות, מנהל תפעול):")

if st.button("🔍 הפק דו״ח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו״ח מקצועי... אנא המתן..."):
            report = generate_salary_table(job_title)
            df = markdown_to_df(report)
            total_salary, total_employer = calculate_from_table(df)

            # הוספת שורה מסכמת לטבלה
            if total_salary:
                summary = pd.DataFrame([{
                    "רכיב שכר": "סה\"כ כולל",
                    "טווח שכר (₪)": "",
                    "ממוצע שוק (₪)": f"{total_salary:,.0f}",
                    "מנגנון תגמול / תנאי": "",
                    "פירוט רכיב": "",
                    "עלות מעסיק (₪)": f"{total_employer:,.0f}",
                    "אחוז מעלות כוללת": "100%"
                }])
                df = pd.concat([df, summary], ignore_index=True)

            # הצגת הדו"ח
            st.success("✅ דו״ח הופק בהצלחה")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

            # הצגת נתונים סופיים מעוצבים
            if total_salary:
                st.markdown(f"""
                <div style='background-color:#E3F2FD; padding:18px; border-radius:10px; margin-top:20px; text-align:center;'>
                    <h3 style='margin-bottom:10px;'>💰 סיכום עלות</h3>
                    <p><b>סה״כ שכר ברוטו:</b> {total_salary:,.0f} ₪<br>
                    <b>סה״כ עלות מעסיק:</b> {total_employer:,.0f} ₪</p>
                </div>
                """, unsafe_allow_html=True)

            # כפתור העתק דו"ח
            st.components.v1.html(f"""
            <div style="text-align:center; margin-top:25px;">
                <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                alert('✅ הדו\"ח הועתק ללוח!');">📋 העתק דו\"ח</button>
            </div>
            """, height=100)

