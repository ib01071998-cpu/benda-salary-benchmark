import streamlit as st
from openai import OpenAI
import pandas as pd
from io import StringIO
import os

# הגדרות בסיסיות
st.set_page_config(page_title="דו\"ח שכר מפורט – מערכת ארגונית", layout="wide")

# עיצוב מקצועי RTL
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1, h2, h3 { color: #1E88E5; text-align: center; }
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
}
th {
    background-color: #1565C0;
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
tr:nth-child(even) td { background-color: #F1F8E9; }
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

# יצירת לקוח GPT
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

st.title("📊 דו\"ח שכר ארגוני מפורט – מודל 'צבירן PRO'")
st.markdown("הזן שם משרה בעברית להפקת טבלת שכר מלאה ומפורטת הכוללת כל רכיב שכר, תגמול והטבה – ללא טקסט חופשי.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, סמנכ\"ל מכירות, מהנדס שירות):")

def generate_massive_salary_table(job_title):
    prompt = f"""
    צור טבלת שכר אחת בלבד בפורמט Markdown עבור המשרה "{job_title}" בישראל.

    אל תכתוב שום טקסט חופשי – רק טבלה אחת בלבד עם העמודות הבאות:
    | רכיב | פירוט לפי שנות ניסיון (1, 3, 5, 7, 10, 15+) | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | פירוט מלא של רכיב השכר | עלות מעסיק (₪) | אחוז מסך עלות מעסיק |

    הנחיות:
    - הצג שכר בסיס לכל רמת ניסיון עם נתונים מדויקים (לדוגמה: שנה 1 – 15,000 ₪, שנה 5 – 20,500 ₪, שנה 10 – 26,000 ₪).
    - הוסף עמלות, בונוסים, סיבוס, טלפון נייד, ביטוחים, קרן השתלמות, הבראה, ביגוד, הכשרות, מחשב, חניה, נסיעות, מתנות.
    - בסעיף רכב חברה:
        • שווי שימוש חודשי (₪)
        • עלות דלק חודשית ממוצעת (₪)
        • שווי רכב בשוק (₪)
        • דגמים לפי רמות תפקיד
        • סוג המימון (ליסינג / בעלות)
    - בסוף כל רכיב הצג עמודת עלות מעסיק = ממוצע × 1.3 אם רלוונטי.
    - הערכות מבוססות על שוק דומה לחברות כמו Benda Magnetic בע\"מ (יבואנים, טכנולוגיה, גאדג'טים).
    - ודא שהטבלה מקיפה לפחות 12–15 רכיבים כולל עלויות כלליות (בונוס מצטיין, חופשות, מתנות, וכו׳).
    - אין לכתוב שום טקסט נוסף לפני או אחרי.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלת נתונים מלאה בלבד, ללא טקסט חופשי."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content

# המרת Markdown ל-HTML
def markdown_to_html_table(markdown_text):
    lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
    clean_lines = [line for line in lines if not line.startswith("|-")]
    df = pd.read_csv(StringIO("\n".join(clean_lines)), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x: x.strip())
    df = df.drop(df.index[0]) if df.iloc[0].str.contains("רכיב").any() else df
    return df

# הפעלת המודל
if st.button("🔍 הפק דו\"ח"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו\"ח מלא... אנא המתן..."):
            report = generate_massive_salary_table(job_title)
            df = markdown_to_html_table(report)
            st.success("✅ דו\"ח הופק בהצלחה")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

            # כפתור העתק
            st.components.v1.html(f"""
            <div style="text-align:center; margin-top:15px;">
                <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                alert('✅ הטבלה הועתקה ללוח!');">📋 העתק טבלה</button>
            </div>
            """, height=100)
