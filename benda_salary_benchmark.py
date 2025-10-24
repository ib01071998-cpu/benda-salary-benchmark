import streamlit as st
import os, re, requests
import pandas as pd
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות כלליות
# -------------------------------------------------
st.set_page_config(page_title="מערכת בנצ'מארק שכר – שוק העבודה בישראל", layout="wide")
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
SERPER_KEY = os.getenv("SERPER_API_KEY")

# -------------------------------------------------
# עיצוב מקצועי
# -------------------------------------------------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:6px; }
h2 { color:#1565C0; font-weight:800; border-bottom:2px solid #BBDEFB; padding-bottom:4px; }
table{width:100%; border-collapse:collapse; border-radius:10px; overflow:hidden; box-shadow:0 3px 10px rgba(0,0,0,.08)}
th{background:#1976D2;color:#fff;padding:12px; font-weight:800; border:1px solid #E3F2FD; text-align:center}
td{background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center;font-size:15px}
tr:nth-child(even) td{background:#F1F8E9}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
.stButton>button {
  background: linear-gradient(90deg,#1976D2,#42A5F5); color:#fff; border:none; border-radius:10px;
  font-weight:700; padding:10px 20px; box-shadow:0 2px 10px rgba(0,0,0,.15);
}
div[data-testid="stExpander"] { border:1px solid #BBDEFB; border-radius:8px; background:#FAFAFA; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# שליפת נתוני אמת ממקורות ישראליים בלבד
# -------------------------------------------------
def get_live_salary_data(job_title: str) -> pd.DataFrame:
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = [
        "site:alljobs.co.il",
        "site:drushim.co.il",
        "site:globes.co.il",
        "site:bizportal.co.il",
        "site:maariv.co.il",
        "site:ynet.co.il"
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
                        "שכר מינימום": min(salaries),
                        "שכר מקסימום": max(salaries),
                        "שכר ממוצע": sum(salaries)/len(salaries)
                    })
        except Exception:
            continue
    return pd.DataFrame(rows)

# -------------------------------------------------
# בנצ'מארק חכם מבוסס GPT ונתוני אמת
# -------------------------------------------------
def generate_salary_table(job_title, experience, df):
    avg_market = int(df["שכר ממוצע"].mean()) if not df.empty else None
    live_summary = f"נתוני אמת שנשלפו ממקורות שוק בישראל:\n{df.to_string(index=False)}" if not df.empty else "לא נמצאו נתוני אמת – יוצג בנצ'מארק GPT בלבד."
    exp_text = "בהתאם לממוצע השוק" if experience==0 else f"עבור {experience} שנות ניסיון"

    prompt = f"""
{live_summary}

צור טבלת בנצ'מארק שכר מלאה לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.
התבסס על נתוני אמת משוק העבודה הישראלי (AllJobs, Drushim, Globes, Bizportal, Ynet, Maariv)
והצג טבלה אינפורמטיבית מלאה ומפורטת בלבד – ללא מלל נוסף.

יש לכלול:
- שכר בסיס
- עמלות
- בונוסים
- מענקים
- אחזקת רכב (כולל שווי שוק ודגמים)
- שעות נוספות
- קרן השתלמות
- פנסיה
- ביטוחים
- אש"ל
- ימי הבראה
- ציוד
- טלפון נייד
- דלק
- חניה
- חופשות
- מתנות / ביגוד / רווחה

לכל רכיב ציין:
* טווח שכר (₪)
* ממוצע שוק (₪)
* מנגנון תגמול מפורט ומבוסס שוק (לדוג׳: 5% מהמכירות עד תקרה של 8,000 ₪, או בונוס שנתי 2 משכורות)
* אחוז חברות שמציעות את הרכיב
* מגמת שוק (עולה / יציב / בירידה)
* עלות מעסיק ממוצעת (₪)
* אחוז מכלל עלות השכר הכוללת

בסוף הוסף שורת סיכום הכוללת:
- שכר ברוטו ממוצע כולל
- עלות מעסיק כוללת ממוצעת (בהתאם ליחס ממוצע של 1.35 משכר הברוטו)
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role":"system","content":"אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלה בלבד בעברית, ללא טקסט נוסף."},
            {"role":"user","content":prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content, avg_market

# -------------------------------------------------
# ממשק המשתמש
# -------------------------------------------------
st.title("💼 מערכת בנצ'מארק שכר – שוק העבודה בישראל")
st.caption("מבוסס על GPT-4 Turbo + SERPER API | מקורות: AllJobs, Drushim, Globes, Bizportal, Maariv, Ynet")

col1, col2 = st.columns([2,1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל לוגיסטיקה):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):", 0, 40, 0)

if "history" not in st.session_state:
    st.session_state["history"] = []

btn1, btn2 = st.columns([1,1])
with btn1: run = st.button("🚀 הפק דו״ח")
with btn2:
    if st.button("🗑️ נקה היסטוריה"):
        st.session_state["history"] = []
        st.success("היסטוריה נוקתה בהצלחה ✅")

if run:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("📡 שולף נתונים אמיתיים ממקורות ישראליים..."):
            live_df = get_live_salary_data(job)

        st.markdown("### 🌐 נתוני אמת מהשוק:")
        if not live_df.empty:
            st.dataframe(live_df, hide_index=True, use_container_width=True)
        else:
            st.info("לא נמצאו נתונים אמיתיים, יוצג חישוב ממוצע משוק העבודה הכללי.")

        with st.spinner("מחשב בנצ'מארק חכם ומפיק טבלת שכר מלאה..."):
            md, avg = generate_salary_table(job, exp, live_df)

        st.markdown("### 📊 טבלת רכיבי שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        st.session_state["history"].append({
            "job": job, "exp": exp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": md
        })

        st.components.v1.html(f"""
        <div style="text-align:center; margin-top:10px;">
          <button class="copy-btn" onclick="navigator.clipboard.writeText(`{md.replace('`','').replace('"','').replace("'","")}`); alert('הדו\"ח הועתק ✅');">📋 העתק דו\"ח</button>
        </div>
        """, height=80)

# היסטוריית דוחות
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report","אין דו\"ח להצגה"))
