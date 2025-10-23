import streamlit as st
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
import os

# 🧠 הגדרות כלליות
st.set_page_config(page_title="דו\"ח שכר ארגוני – צבירן אלפא PRO+", layout="wide")

# 🎨 עיצוב יוקרתי ומדויק
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color: #0D47A1; text-align: center; font-weight: 800; margin-bottom: 10px; }
h2, h3 { color: #1565C0; text-align: right; }
table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
    border-radius: 12px;
    overflow: hidden;
}
th {
    background-color: #1565C0;
    color: white;
    padding: 12px;
    font-weight: bold;
    border: 1px solid #E3F2FD;
    text-align: center;
    font-size: 15px;
}
td {
    background-color: #FAFAFA;
    border: 1px solid #E3F2FD;
    padding: 10px;
    text-align: center;
    font-size: 14px;
}
tr:nth-child(even) td { background-color: #E8F5E9; }
div[data-testid="stMetricValue"] { font-size: 28px !important; color: #0D47A1; }
.copy-btn {
    background: linear-gradient(90deg, #42A5F5, #1E88E5);
    color: white;
    padding: 10px 25px;
    border-radius: 8px;
    border: none;
    font-weight: bold;
    cursor: pointer;
    font-size: 16px;
}
.copy-btn:hover { background: linear-gradient(90deg, #1976D2, #0D47A1); }
</style>
""", unsafe_allow_html=True)

# 🔑 הגדרת API
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# 🕓 שמירת היסטוריה
if "history" not in st.session_state:
    st.session_state["history"] = []

# 🧭 כותרת
st.title("📊 דו\"ח שכר ארגוני חכם – מערכת 'צבירן אלפא PRO+'")

# 📥 קלטים
col1, col2 = st.columns([2, 1])
with col1:
    job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, סמנכ״ל מכירות):")
with col2:
    experience = st.number_input("שנות ניסיון:", min_value=0, max_value=30, value=5, step=1)

# 🧮 פונקציית חישוב עלות מעסיק
def calc_employer_cost(salary):
    """עלות מעסיק לפי ממוצע המשק (≈32%)"""
    return round(salary * 1.32, 2)

# 🧠 הפעלת GPT
def generate_salary_table(job_title, experience):
    prompt = f"""
    צור טבלת שכר אחת בלבד, מקצועית ומפורטת מאוד, בעברית, עבור המשרה "{job_title}" בשוק הישראלי.
    אין לכתוב שום טקסט חופשי לפני או אחרי.
    הטבלה חייבת לכלול את העמודות הבאות:
    | רכיב | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | פירוט רכיב השכר | עלות מעסיק (₪) | אחוז מעלות כוללת |

    הנחיות:
    - התייחס לעובד עם {experience} שנות ניסיון.
    - כלול לפחות 15 רכיבים שונים: שכר בסיס, עמלות, בונוסים, סיבוס, טלפון, מחשב, ביטוחים, קרן השתלמות, הבראה, נסיעות, חניה, ביגוד, מתנות, הכשרות, רכב חברה.
    - עבור רכב חברה פרט:
      • שווי שימוש חודשי (₪)
      • עלות דלק ממוצעת (₪)
      • שווי רכב בשוק (₪)
      • דגמים לפי דרג
      • סוג מימון (ליסינג / בעלות)
    - במנגנוני תגמול פרט אחוזים מדויקים (למשל 3%–6% מהמכירות, 8–15K ₪ רבעוני).
    - הוסף טווח עלות מעסיק (לדוגמה: 28,000–32,500 ₪) וחישוב כולל.
    - מבוסס על חברות דומות ל-Benda Magnetic בע״מ (יבואנים, טכנולוגיה, מוצרי חשמל, גאדג׳טים).
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלת נתונים בלבד, ללא טקסט נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.55,
    )
    return response.choices[0].message.content

# 🧾 המרת Markdown ל-DataFrame
def markdown_to_df(markdown_text):
    lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
    clean = [line for line in lines if not line.startswith("|-")]
    df = pd.read_csv(StringIO("\n".join(clean)), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x: x.strip())
    df = df.drop(df.index[0]) if df.iloc[0].str.contains("רכיב").any() else df
    return df

# 💰 חישוב עלות מעסיק כוללת
def calculate_total_employer_cost(df):
    total = 0
    for val in df["עלות מעסיק (₪)"]:
        txt = str(val).replace("₪", "").replace(",", "").strip()
        if "–" in txt:
            parts = [p.strip() for p in txt.split("–") if p.replace('.', '', 1).isdigit()]
            if len(parts) == 2:
                avg_val = (float(parts[0]) + float(parts[1])) / 2
                total += avg_val
        elif txt.replace('.', '', 1).isdigit():
            total += float(txt)
    return round(total, 2) if total > 0 else None

# 🚀 הפקת דו"ח
if st.button("🔍 הפק דו\"ח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו\"ח מלא... אנא המתן..."):
            report = generate_salary_table(job_title, experience)
            df = markdown_to_df(report)

            # הצגת טבלה
            st.success("✅ דו\"ח הופק בהצלחה")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

            # חישוב עלות כוללת
            total_cost = calculate_total_employer_cost(df)
            if total_cost:
                avg_cost = calc_employer_cost(total_cost)
                st.metric(label="💰 סה״כ עלות מעסיק משוערת לפי ממוצע המשק", value=f"{avg_cost:,.0f} ₪")

            # כפתור העתקה
            st.components.v1.html(f"""
            <div style="text-align:center; margin-top:15px;">
                <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                alert('✅ הדו\"ח הועתק ללוח!');">📋 העתק דו\"ח</button>
            </div>
            """, height=100)

            # שמירה להיסטוריה
            st.session_state["history"].append({
                "job": job_title,
                "experience": experience,
                "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "report": report
            })

# 📂 ניהול היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    col_h1, col_h2 = st.columns([4, 1])
    with col_h2:
        if st.button("🧹 נקה היסטוריה"):
            st.session_state["history"] = []
            st.success("היסטוריה נוקתה בהצלחה ✅")
            st.stop()

    for item in reversed(st.session_state["history"]):
        job = item.get("job", "לא צויין")
        exp = item.get("experience", 0)
        time = item.get("time", "לא ידוע")
        report = item.get("report", "אין מידע להצגה")
        with st.expander(f"{job} – {exp} שנות ניסיון — {time}"):
            st.markdown(report)
