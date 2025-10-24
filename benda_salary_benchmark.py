import streamlit as st
import requests, os, re
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
from dotenv import load_dotenv

# ---------- הגדרות כלליות ----------
st.set_page_config(page_title="MASTER 4.2 – Benchmark Total Compensation", layout="wide")
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# ---------- עיצוב ----------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
h1 { color:#0D47A1; text-align:center; font-weight:900; margin-bottom:4px; }
.stButton>button {
  background: linear-gradient(90deg,#1976D2,#42A5F5); color:#fff; border:none; border-radius:10px;
  font-weight:700; padding:10px 20px; box-shadow:0 2px 10px rgba(0,0,0,.15); transition:.2s;
}
.stButton>button:hover { transform: translateY(-1px); }
table{width:100%; border-collapse:collapse; border-radius:12px; overflow:hidden; box-shadow:0 3px 10px rgba(0,0,0,.08)}
th{background:#1565C0;color:#fff;padding:12px; font-weight:800; border:1px solid #E3F2FD; text-align:center}
td{background:#fff;border:1px solid #E3F2FD;padding:10px;text-align:center}
tr:nth-child(even) td{background:#F1F8E9}
.summary-card{background:#E3F2FD; padding:16px; border-radius:10px; text-align:center; margin-top:14px}
.copy-btn{background:linear-gradient(90deg,#1E88E5,#42A5F5); color:#fff; padding:10px 26px; border:none; border-radius:10px; font-weight:700; cursor:pointer}
</style>
""", unsafe_allow_html=True)

# ---------- שליפת נתונים חיים מישראל ----------
def get_live_data(job_title:str)->str:
    """שואב תוצאות חיפוש חיים מ-Serper"""
    if not SERPER_KEY:
        return "⚠️ אין מפתח SERPER – הדוח מבוסס על GPT בלבד."
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    payload = {"q": f"שכר {job_title} site:alljobs.co.il OR site:drushim.co.il OR site:globes.co.il OR site:bizportal.co.il"}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15)
        items = r.json().get("organic", [])[:5]
        return "\n".join([f"{x.get('title','')} — {x.get('snippet','')}" for x in items])
    except Exception as e:
        return f"שגיאה ב-Serper: {e}"

# ---------- הפקת טבלת שכר ----------
def generate_salary_table(job_title, experience, live_data):
    exp_text = "בהתאם לממוצע השוק" if experience==0 else f"עבור עובד עם {experience} שנות ניסיון"
    prompt = f"""
להלן מידע חי ממקורות שוק בישראל עבור "{job_title}":
{live_data}

צור טבלת בנצ׳מארק שכר מפורטת בעברית מלאה, הכוללת **כל רכיב שכר אפשרי** (2025):
- בסיס, עמלות, בונוסים (חודשיים/רבעוניים/שנתיים), מענקי מצוינות, KPI, שעות נוספות, כוננויות, אחזקת רכב, אש"ל, קרן השתלמות, פנסיה, ביטוחים, ימי הבראה, שי לחגים, מענקי חתימה, חניה, ציוד, נסיעות, הטבות רכב, ועוד.
- לכל רכיב יש לכלול מנגנון תגמול מפורט (לדוג׳ 5% מהמכירות מעל יעד חודשי, מדרגות עמלות, נוסחת בונוס).
- סעיף רכב: יש לפרט דגמים מקובלים (לדוג׳ טויוטה קורולה, מאזדה 3, סקודה סופרב), שווי שוק הרכב החדש (₪), שווי שימוש חודשי ממוצע (₪), סוג מימון (ליסינג/בעלות), והאם כוללת דלק וביטוחים.
- כל ערך כספי בש״ח בלבד.
- עמודות חובה:
| רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | אחוז חברות שמציעות | מגמת שוק | עלות מעסיק (₪) | אחוז מעלות כוללת |
לא להוסיף מלל מחוץ לטבלה.
"""
    r = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role":"system","content":"אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלה בלבד בעברית."},
            {"role":"user","content":prompt}
        ],
        temperature=0.25,
    )
    return r.choices[0].message.content

# ---------- חישוב עלות מעסיק וברוטו ----------
def extract_average(df):
    """מחלץ שכר ממוצע מהעמודה הרלוונטית"""
    try:
        col = [c for c in df.columns if "ממוצע" in c or "שוק" in c][0]
        nums = []
        for v in df[col]:
            m = re.findall(r"\d{3,6}", str(v))
            if m:
                nums += [int(x) for x in m]
        return int(sum(nums)/len(nums)) if nums else None
    except:
        return None

def calc_employer_cost(avg_salary:int)->dict:
    """חישוב עלות מעסיק לפי ממוצע שוק"""
    if not avg_salary: return {}
    return {
        "שכר ברוטו": avg_salary,
        "פנסיה": round(avg_salary*0.065,0),
        "קרן השתלמות": round(avg_salary*0.075,0),
        "ביטוח לאומי": round(avg_salary*0.07,0),
        "הוצאות רכב ממוצעות": round(avg_salary*0.12,0),
        "סה״כ עלות מעסיק": round(avg_salary*1.31,0)
    }

# ---------- המרת Markdown ל-DataFrame ----------
def md_to_df(md:str):
    lines = [ln for ln in md.splitlines() if "|" in ln and not set(ln.strip()) <= {"|","-"}]
    csv_text = "\n".join(lines)
    df = pd.read_csv(StringIO(csv_text), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda x:x.strip())
    if "" in df.columns: df = df.drop(columns=[""])
    if len(df)>0 and "רכיב" in str(df.iloc[0,0]): df = df.iloc[1:].reset_index(drop=True)
    return df

# ---------- ממשק ----------
st.title("💎 MASTER 4.2 – מערכת בנצ׳מארק כוללת")
st.caption("GPT-4 + Serper | כל רכיבי השכר | חישוב עלות מעסיק | RTL מלא")

col1,col2 = st.columns([2,1])
with col1:
    job = st.text_input("שם המשרה (לדוג׳: סמנכ\"ל מכירות, מנהל לוגיסטיקה):")
with col2:
    exp = st.number_input("שנות ניסיון (0 = ממוצע שוק):",0,40,0)

if "history" not in st.session_state:
    st.session_state["history"] = []

btn1,btn2 = st.columns([1,1])
with btn1:
    run = st.button("🔍 הפק דו״ח")
with btn2:
    clear = st.button("🗑️ נקה היסטוריה")

if clear:
    st.session_state["history"] = []
    st.success("היסטוריה נוקתה ✅")

if run:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מבצע חיפוש במקורות ישראליים..."):
            live = get_live_data(job)
            st.markdown("### 🌐 דגימות שוק חיות:")
            st.markdown(live)
        with st.spinner("מפיק טבלת שכר..."):
            md = generate_salary_table(job,exp,live)
        st.markdown("### 📊 טבלת שכר מלאה:")
        st.markdown(md, unsafe_allow_html=True)

        try:
            df = md_to_df(md)
            avg = extract_average(df)
            cost = calc_employer_cost(avg)
            if cost:
                st.markdown(f"""
                <div class="summary-card">
                    <b>🧾 חישוב לפי שכר ממוצע ({avg:,.0f} ₪):</b><br>
                    שכר ברוטו לעובד: <b>{cost['שכר ברוטו']:,.0f} ₪</b><br>
                    פנסיה: {cost['פנסיה']:,.0f} ₪ | קרן השתלמות: {cost['קרן השתלמות']:,.0f} ₪ | ביטוח לאומי: {cost['ביטוח לאומי']:,.0f} ₪<br>
                    הוצאות רכב ממוצעות: {cost['הוצאות רכב ממוצעות']:,.0f} ₪<br>
                    <b>סה״כ עלות מעסיק משוערת: {cost['סה״כ עלות מעסיק']:,.0f} ₪</b>
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.info(f"לא ניתן לחשב סיכום ({e})")

        st.session_state["history"].append({
            "job": job,
            "exp": exp,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": md
        })

        st.components.v1.html(f"""
        <div style="text-align:center; margin-top:10px;">
          <button class="copy-btn" onclick="navigator.clipboard.writeText(`{md.replace('`','').replace('"','').replace("'","")}`); alert('הדו\"ח הועתק ✅');">📋 העתק דו\"ח</button>
        </div>
        """, height=80)

if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית דוחות")
    for item in reversed(st.session_state["history"]):
        exp_value = item.get("exp") or item.get("experience") or 0
        exp_label = "ממוצע שוק" if exp_value == 0 else f"{exp_value} שנות ניסיון"
        with st.expander(f"{item.get('job','לא צויין')} — {exp_label} — {item.get('time','לא ידוע')}"):
            st.markdown(item.get("report","אין דו\"ח להצגה"))
