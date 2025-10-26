import streamlit as st
import os, re, requests
from openai import OpenAI
from dotenv import load_dotenv
import pandas as pd
from datetime import datetime

# -------------------------------------------------
# הגדרות מערכת
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר - גרסה ישראלית", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב ממשק
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
# שליפת נתוני אמת ממקורות ישראליים (דרך SERPER)
# -------------------------------------------------
def get_live_salary_data(job_title: str):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = [
        "site:alljobs.co.il",
        "site:drushim.co.il",
        "site:globes.co.il",
        "site:bizportal.co.il",
        "site:calcalist.co.il"
    ]
    rows = []
    for src in sources:
        payload = {"q": f"שכר {job_title} {src}"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=15)
            items = r.json().get("organic", [])
            for item in items:
                snippet = item.get("snippet", "")
                nums = re.findall(r"\d{1,3}(?:,\d{3})", snippet)
                salaries = [int(x.replace(",", "")) for x in nums]
                if salaries:
                    rows.append({
                        "מקור": src.split(":")[1].split(".")[0].capitalize(),
                        "מינימום": min(salaries),
                        "מקסימום": max(salaries),
                        "ממוצע": int(sum(salaries)/len(salaries))
                    })
        except Exception:
            continue
    return pd.DataFrame(rows)

# -------------------------------------------------
# יצירת טבלת בנצ'מארק עם GPT
# -------------------------------------------------
def generate_salary_table(job_title, df):
    live_summary = (
        "לא נמצאו נתוני אמת – יוצג בנצ'מארק ממוצע בלבד."
        if df.empty else
        f"נתוני אמת ממקורות ישראליים:\n{df.to_string(index=False)}"
    )

    prompt = f"""
{live_summary}

צור טבלת שכר מלאה ומפורטת לתפקיד "{job_title}" בישראל (2025),
בהתבסס על נתוני אמת משוק העבודה הישראלי (AllJobs, Drushim, Globes, Calcalist, Bizportal)
ועל נתוני שוק אמיתיים מחברות יבוא, אלקטרוניקה ולוגיסטיקה הדומות לבנדא מגנטיק.

הצג את כל רכיבי השכר האפשריים:
שכר בסיס, עמלות, בונוסים, מענקים, רכב חברה, שעות נוספות, קרן השתלמות, פנסיה, ביטוחים, אש"ל, ימי הבראה, ציוד, טלפון נייד, דלק, חניה, חופשות, מתנות ורווחה.

בכל שורה הצג:
- טווח שכר או אחוזים (לדוג׳ 3%–7% או 10,000–14,000 ₪)
- בסיסית / בינונית / גבוהה
- ממוצע שוק (₪)
- מנגנון תגמול מפורט בהתאם לנורמות השוק בישראל (למשל: עמלות 5% מהמכירות נטו עד תקרה של 8,000 ₪)
- עלות מעסיק ממוצעת (₪)
- אחוז מעלות השכר הכוללת (%)

⚠️ רכיב "רכב חברה":
ציין את שווי השוק של הרכב (₪) ודגמים תואמים.
בעלות מעסיק הצג את זקיפת השווי (לדוג׳ 3,000 ₪ לחודש לקבוצה 4).

הפלט יהיה **אך ורק טבלה אחת מסודרת** בפורמט כמו בדוגמה הבאה:

| רכיב שכר | טווח שכר | בסיסית | בינונית | גבוהה | ממוצע שוק (₪) | מנגנון תגמול מפורט | עלות מעסיק ממוצעת (₪) | אחוז מעלות שכר כוללת (%) |

בסיום הוסף שורה נפרדת מחוץ לטבלה עם:
💰 שכר ברוטו ממוצע כולל  
🏢 עלות מעסיק כוללת (שכר × 1.35 + עלויות נוספות)  
🚗 זקיפת שווי רכב ממוצעת (כ־3,000 ₪ לחודש)
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "אתה אנליסט שכר בכיר בישראל. הפלט הוא טבלה אחת בלבד בעברית, ללא מלל נוסף."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר - גרסה ישראלית מלאה")

job = st.text_input("הזן שם משרה (לדוג׳: מנהל מכירות, מנהל לוגיסטיקה, טכנאי שירות):")

if st.button("🚀 הפק דו״ח"):
    if not job.strip():
        st.warning("אנא הזן שם משרה תקפה.")
    else:
        with st.spinner("📡 שולף נתוני אמת ממקורות ישראליים..."):
            df = get_live_salary_data(job)

        with st.spinner("🧠 מפיק טבלת בנצ'מארק מלאה ומדויקת..."):
            md = generate_salary_table(job, df)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.markdown("""
        <div class="summary-box">
          <div class="summary-line">💰 <span class="summary-value">שכר ברוטו ממוצע כולל:</span> לפי ממוצעי השוק בטבלה.</div>
          <div class="summary-line">🏢 <span class="summary-value">עלות מעסיק כוללת:</span> שכר × 1.35 + עלויות נלוות (רכב, ביטוחים, סיבוס וכו').</div>
          <div class="summary-line">🚗 <span class="summary-value">זקיפת שווי רכב חברה:</span> לפי קבוצת רכב ממוצעת (כ־3,000 ₪ לחודש).</div>
        </div>
        """, unsafe_allow_html=True)
