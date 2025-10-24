import streamlit as st
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
import os

# -----------------------------------------------------------
# הגדרות כלליות
# -----------------------------------------------------------
st.set_page_config(page_title="MASTER+ BENCHMARK SYSTEM – PRO ISRAEL", layout="wide")

# 🎨 עיצוב יוקרתי
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
body { background-color: #f4f6f8; }
h1 { color: #0D47A1; text-align: center; font-weight: 900; font-size: 38px; margin-bottom: 10px; }
h3 { color: #1565C0; margin-top: 25px; }
.stButton>button {
    background: linear-gradient(90deg, #1976D2, #42A5F5);
    color: white;
    padding: 12px 30px;
    border-radius: 10px;
    border: none;
    font-weight: bold;
    font-size: 16px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.15);
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
    box-shadow: 0px 3px 10px rgba(0,0,0,0.1);
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

# -----------------------------------------------------------
# הגדרת API
# -----------------------------------------------------------
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    st.warning("⚠️ לא נמצא מפתח API. הזן אותו כמשתנה סביבה לפני ההרצה.")
client = OpenAI(api_key=API_KEY)

# -----------------------------------------------------------
# פונקציות עיבוד
# -----------------------------------------------------------
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

# -----------------------------------------------------------
# מנוע GPT לבנצ'מארק ישראלי מורחב
# -----------------------------------------------------------
def generate_salary_table(job_title, experience):
    exp_text = "בהתאם לממוצע השוק" if experience == 0 else f"בהתאם לעובד עם {experience} שנות ניסיון"

    prompt = f"""
    צור דו״ח שכר מפורט בעברית, עבור המשרה "{job_title}" בישראל.
    יש לבצע בנצ'מארק רחב על כלל מקורות השוק המקומיים האפשריים
    (AllJobs, JobMaster, Drushim, Globes, LMAS, דוחות שכר פומביים ועוד),
    בשילוב עם ידע עדכני על מגמות השכר בשוק הישראלי לשנת 2025.

    הצג רק טבלה אינפורמטיבית.
    כלול את כלל רכיבי השכר הישירים האפשריים, עם עומק מידע מקסימלי:

    🧩 עבור כל רכיב חובה לכלול:
    - טווח שכר / ערך ריאלי בשוק
    - ממוצע שוק עדכני
    - מנגנון תגמול מפורט (כמו אחוזים, ספים, מודלים מדורגים וכו׳)
    - אחוז החברות בישראל שמציעות רכיב זה
    - מגמת השינוי (↑ עלייה / ↓ ירידה / → יציב)
    - עלות מעסיק משוערת (₪)
    - אחוז מתוך העלות הכוללת

    עמודות חובה:
    | רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | אחוז חברות שמציעות רכיב זה | מגמת שוק | עלות מעסיק (₪) | אחוז מעלות כוללת |

    הצג גם רכיבים נפוצים פחות אך רלוונטיים כמו:
    - כוננויות
    - אחזקת רכב
    - תמריצים שנתיים
    - שעות נוספות
    - אחזקת ציוד אישי
    - מענקי התמדה

    סיים בשורה מסכמת של:
    - סך הכל ברוטו (ממוצע כל הרכיבים)
    - סך הכל עלות מעסיק משוקללת
    """

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט שלך הוא טבלה בלבד."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.35,
    )
    return response.choices[0].message.content

# -----------------------------------------------------------
# ממשק משתמש
# -----------------------------------------------------------
st.title("💎 MASTER+ BENCHMARK SYSTEM – PRO ISRAEL")
st.caption("מערכת אנליטיקת שכר חכמה ומפורטת ברמה בינלאומית")

col1, col2 = st.columns([2, 1])
with col1:
    job_title = st.text_input("שם המשרה:")
with col2:
    experience = st.number_input("שנות ניסיון (0 = ממוצע שוק):", min_value=0, max_value=40, value=0, step=1)

if "history" not in st.session_state:
    st.session_state["history"] = []

# -----------------------------------------------------------
# הפקת דו"ח
# -----------------------------------------------------------
if st.button("🔍 בצע בנצ'מארק שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו״ח מקצועי... אנא המתן..."):
            report = generate_salary_table(job_title, experience)
            df = markdown_to_df(report)
            total_salary, total_employer = calculate_from_table(df)

            if total_salary:
                summary = pd.DataFrame([{
                    "רכיב שכר": "סה\"כ כולל",
                    "טווח שכר (₪)": "",
                    "ממוצע שוק (₪)": f"{total_salary:,.0f}",
                    "מנגנון תגמול / תנאי": "",
                    "אחוז חברות שמציעות רכיב זה": "",
                    "מגמת שוק": "",
                    "עלות מעסיק (₪)": f"{total_employer:,.0f}",
                    "אחוז מעלות כוללת": "100%"
                }])
                df = pd.concat([df, summary], ignore_index=True)

            st.success("✅ דו״ח הופק בהצלחה")
            st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

            if total_salary:
                st.markdown(f"""
                <div style='background-color:#E3F2FD; padding:18px; border-radius:10px; margin-top:20px; text-align:center;'>
                    <h3 style='margin-bottom:10px;'>💰 סיכום כולל</h3>
                    <p><b>סה״כ שכר ברוטו:</b> {total_salary:,.0f} ₪<br>
                    <b>סה״כ עלות מעסיק:</b> {total_employer:,.0f} ₪</p>
                </div>
                """, unsafe_allow_html=True)

            st.session_state["history"].append({
                "job": job_title,
                "experience": experience,
                "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "report": report
            })

            st.components.v1.html(f"""
            <div style="text-align:center; margin-top:25px;">
                <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                alert('✅ הדו\"ח הועתק ללוח!');">📋 העתק דו\"ח</button>
            </div>
            """, height=100)

# -----------------------------------------------------------
# היסטוריה
# -----------------------------------------------------------
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
        exp_label = "ממוצע שוק" if exp == 0 else f"{exp} שנות ניסיון"
        with st.expander(f"{job} — {exp_label} — {time}"):
            st.markdown(report)
