import streamlit as st
import os, re, requests
import pandas as pd
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------
# הגדרות כלליות
# -------------------------------------------------
st.set_page_config(page_title="MASTER 4.6 – Real Market Benchmark", layout="wide")
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
table{width:100%; border-collapse:collapse; border-radius:10px; overflow:hidden; box-shadow:0 3px 10px rgba(0,0,0,.08)}
th{background:#1565C0;color:#fff;padding:12px; font-weight:800; border:1px solid #E3F2FD; text-align:center}
td{background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center}
tr:nth-child(even) td{background:#F1F8E9}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
.stButton>button {
  background: linear-gradient(90deg,#1976D2,#42A5F5); color:#fff; border:none; border-radius:10px;
  font-weight:700; padding:10px 20px; box-shadow:0 2px 10px rgba(0,0,0,.15);
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# שליפת נתונים אמיתיים ממקורות ישראליים
# -------------------------------------------------
def get_live_salary_data(job_title: str) -> pd.DataFrame:
    """שולף נתוני שכר ממספר אתרים ישראליים אמיתיים"""
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    sources = [
        "site:alljobs.co.il",
        "site:drushim.co.il",
        "site:globes.co.il",
        "site:bizportal.co.il",
        "site:indeed.com/q-israel"
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
                        "source": src.split(":")[1].split(".")[0].capitalize(),
                        "min": min(salaries),
                        "max": max(salaries),
                        "avg": sum(salaries) / len(salaries)
                    })
        except Exception:
            continue
    return pd.DataFrame(rows)

# -------------------------------------------------
# יצירת טבלת בנצ'מארק רחבה ומפורטת
# -------------------------------------------------
def generate_salary_table(job_title, experience, df):
    """יוצר טבלת בנצ’מארק מלאה ומבוססת נתוני אמת + השלמות GPT"""
    avg_market = int(df["avg"].mean()) if not df.empty else None
    live_summary = f"נתוני אמת ממקורות שוק בישראל:\n{df.to_string(index=False)}" if not df.empty else "לא נמצאו נתוני אמת, הפלט יתבסס על GPT בלבד."
    exp_text = "בהתאם לממוצע השוק" if experience==0 else f"עבור {experience} שנות ניסיון"

    prompt = f"""
{live_summary}

צור טבלת בנצ׳מארק מקיפה לתפקיד "{job_title}" בישראל {exp_text} לשנת 2025.
התבסס על הנתונים למעלה, ובנה טבלה הכוללת את כלל רכיבי השכר הקיימים במשק.

יש לכלול:
- שכר בסיס, עמלות, בונוסים, מענקים, אחזקת רכב, שעות נוספות, אש"ל, קרן השתלמות, פנסיה, ביטוחים, ימי הבראה, ציוד, חניה, טלפון נייד, דלק, ביגוד, חופשות.
- עבור כל רכיב ציין:
  * טווח שכר (₪)
  * ממוצע שוק (₪)
  * מנגנון תגמול מפורט ומבוסס (לדוג׳: 5% מהמכירות עד תקרה של 8,000 ₪)
  * אחוז חברות שמציעות את הרכיב
  * מגמת שוק (עולה / יציב / בירידה)
  * עלות מעסיק משוערת (₪)
  * אחוז מכלל עלות השכר הכוללת

הצג את הנתונים בצורה של טבלה מקצועית בלבד, ללא טקסט נוסף.
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role":"system","content":"אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלה בלבד בעברית."},
            {"role":"user","content":prompt}
        ],
        temperature=0.2,
    )
    return r.choices[0].message.content, avg_market

# -------------------------------------------------
# ממשק משתמש
# -------------------------------------------------
st.title("💼 MASTER 4.6 – Real Market Benchmark")
st.caption("GPT-4 Turbo + SERPER API | בנצ׳מארק אמיתי ורחב על סמך מקורות שוק ישראליים")

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
        with st.spinner("📡 שואב נתונים ממקורות אמת בישראל..."):
            live_df = get_live_salary_data(job)
        st.markdown("### 🌐 נתוני אמת מהשוק:")
        if not live_df.empty:
            st.dataframe(live_df, hide_index=True, use_container_width=True)
        else:
            st.info("לא נמצאו נתונים אמיתיים, מוצג ממוצע GPT בלבד.")

        with st.spinner("מפיק טבלת בנצ׳מארק אמינה ומפורטת..."):
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

# היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report","אין דו\"ח להצגה"))
