import streamlit as st
import requests, os, re
from openai import OpenAI
import pandas as pd
from io import StringIO
from datetime import datetime
from dotenv import load_dotenv

# ---------- קונפיגורציה ----------
st.set_page_config(page_title="MASTER 4.1 – Benchmark Israel (All Components)", layout="wide")
load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
SERPER_KEY = os.getenv("SERPER_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

# ---------- עיצוב ----------
st.markdown("""
<style>
* { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
body { background:#f5f7fa; }
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

# ---------- Serper: נתוני שוק חיים ----------
def fetch_live_snippets(job_title:str)->str:
    if not SERPER_KEY:
        return "לא הוגדר SERPER_API_KEY בקובץ .env – מוציא דו\"ח ללא דגימות חיות."
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_KEY}
    q = f"שכר {job_title} site:alljobs.co.il OR site:drushim.co.il OR site:globes.co.il OR site:bizportal.co.il OR site:themarker.com"
    try:
        r = requests.post(url, headers=headers, json={"q": q}, timeout=20)
        r.raise_for_status()
        items = r.json().get("organic", [])[:6]
        parts = []
        for it in items:
            t = it.get("title","").strip()
            s = it.get("snippet","").strip()
            if t or s:
                parts.append(f"{t} — {s}")
        return "\n".join(parts) if parts else "לא נמצאו דגימות חיות רלוונטיות."
    except Exception as e:
        return f"שגיאה ב-Serper: {e}"

# ---------- GPT: הפקת טבלה מקיפה (כל רכיבי השכר) ----------
def generate_table(job_title:str, years:int, live_text:str)->str:
    exp_text = "לפי ממוצע השוק" if years==0 else f"לפי {years} שנות ניסיון"
    prompt = f"""
להלן דגימות חיות מהשוק הישראלי לתפקיד "{job_title}":
{live_text}

הפק טבלת בנצ'מארק שכר **אינפורמטיבית בלבד** (ללא טקסט חופשי) עבור ישראל, {exp_text}.
הטבלה חייבת לכלול **כל רכיב שכר רלוונטי** (כולל רכיבים קטנים), עם פירוט מנגנוני תגמול מפורט.
דוגמאות לרכיבים: שכר בסיס, עמלות, בונוסים חודשיים/רבעוניים/שנתיים, בונוס מצויינות/הצלחה/התמדה,
מודל יעדים, מדרגות עמלות, תקרות/רצפות, בונוס רווח/EBITDA, שעות נוספות, כוננויות,
סיבוס/אש\"ל, נסיעות, רכב חברה (דגמים/שווי שימוש/דלק/ליסינג/בעלות), אחזקת רכב,
טלפון, מחשב, אינטרנט, ביגוד מקצועי, קרן השתלמות, פנסיה, ביטוחי בריאות/אובדן כושר, ימי הבראה,
אופציות/RSU, מענקי חתימה/שימור/חד-פעמי, שי לחגים, כרטיסי מתנה, חניה, אחזקת ציוד, ימי משמרות/כוננות, כל מה שרלוונטי.

**מנגנוני תגמול – חובה לפרט באמת**:
- עמלות: אחוזים מדויקים, מדרגות, ספים (פלח/מחזור/רווח), תקרה אם קיימת, דוגמת חישוב קצרה.
- בונוסים: נוסחה (לדוג' עד X משכורות, Y% מהרווח, KPI אישיים/ארגוניים, תדירות).
- שעות נוספות/כוננויות: תעריפי 125%/150%/200%, דוגמת חישוב.
- רכב: שווי שימוש חודשי, דגמים מקובלים בדרג, דלק/כביש 6/ביטוח, סוג מימון (ליסינג/בעלות).
- קרן השתלמות/פנסיה/ביטוחים: אחוזי עובד/מעסיק.

עמודות חובה (ובעברית מדויקת):
| רכיב שכר | טווח שכר (₪) | ממוצע שוק (₪) | מנגנון תגמול / תנאי | אחוז חברות שמציעות רכיב זה | מגמת שוק | עלות מעסיק (₪) | אחוז מעלות כוללת |

דרישות קשיחות:
- סכומים בש״ח בלבד.
- אם הערך הוא טווח – כתוב בפורמט "מינימום–מקסימום" (מקף אמצעי – U+2013).
- מנגנון תגמול מפורט אמיתי (לא כותרת כללית).
- סיים את הטבלה עם שורה אחת מסכמת בלבד (סה״כ כולל) אם ברצונך; אחרת נשאיר את הסיכום לחישוב בצד הלקוח.
"""
    resp = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role":"system","content":"אתה אנליסט שכר בכיר בישראל. הפלט תמיד טבלת Markdown אחת בלבד, ללא טקסט חופשי."},
            {"role":"user","content":prompt}
        ],
        temperature=0.28,
    )
    return resp.choices[0].message.content

# ---------- המרת Markdown ל-DataFrame ----------
def markdown_to_df(md:str)->pd.DataFrame:
    lines = [ln for ln in md.splitlines() if "|" in ln]
    # להוריד מפרידי טבלאות
    lines = [ln for ln in lines if set(ln.replace("|","").strip()) - set("-:") ]
    csv_text = "\n".join(lines)
    df = pd.read_csv(StringIO(csv_text), sep="|").dropna(axis=1, how="all")
    df = df.rename(columns=lambda c: c.strip())
    # להסיר עמודה ריקה שמופיעה לפעמים בקצוות
    if "" in df.columns: df = df.drop(columns=[""])
    # להסיר שורת כותרת כפולה אם יש
    if len(df)>0 and any("רכיב" in str(x) for x in df.iloc[0].values):
        df = df.iloc[1:].reset_index(drop=True)
    # ניקוי רווחים
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].astype(str).str.strip()
    return df

# ---------- עזר: חילוץ מספר ממחרוזת (טווח/בודד) ----------
def _avg_from_text(val:str)->float|None:
    if val is None: return None
    s = str(val).replace("₪","").replace(",","").strip()
    s = s.replace(" ", "")
    # טווח עם מקף אמצעי/רגיל
    if "–" in s or "-" in s:
        parts = re.split(r"[–-]", s)
        nums = []
        for p in parts:
            try:
                nums.append(float(re.findall(r"\d+(?:\.\d+)?", p)[0]))
            except: pass
        if len(nums)==2:
            return (nums[0]+nums[1])/2
    # מספר בודד
    m = re.findall(r"\d+(?:\.\d+)?", s)
    if m:
        return float(m[0])
    return None

# ---------- חישוב סיכומים: ברוטו לעובד ועלות מעסיק ----------
def compute_totals(df:pd.DataFrame):
    gross_sum = 0.0
    emp_cost_sum = 0.0
    # ננסה למצוא עמודות לפי שמותיהן
    gross_col_candidates = [c for c in df.columns if "ממוצע" in c and "₪" in c or "שוק" in c]
    emp_col_candidates   = [c for c in df.columns if "עלות" in c and "₪" in c]
    gross_col = gross_col_candidates[0] if gross_col_candidates else None
    emp_col   = emp_col_candidates[0]   if emp_col_candidates   else None
    # לעבור על כל השורות (למעט סה״כ אם קיימת)
    for i, row in df.iterrows():
        if str(row.get("רכיב שכר","")).strip().startswith("סה"):
            continue
        if gross_col:
            v = _avg_from_text(row.get(gross_col))
            if v: gross_sum += v
        if emp_col:
            v2 = _avg_from_text(row.get(emp_col))
            if v2: emp_cost_sum += v2
    return round(gross_sum,2) if gross_sum else None, round(emp_cost_sum,2) if emp_cost_sum else None

# ---------- UI ----------
st.title("💎 MASTER 4.1 – בנצ׳מארק שכר כולל כל רכיבי השכר")
st.caption("GPT + Serper | טבלה אינפורמטיבית בלבד | פירוט מנגנוני תגמול | חישוב סה״כ ברוטו ועלות מעסיק מתוך הטבלה")

colA, colB = st.columns([2,1])
with colA:
    job = st.text_input("שם המשרה (לדוג׳: איש מכירות, סמנכ\"ל תפעול, מנהל לוגיסטיקה):")
with colB:
    years = st.number_input("שנות ניסיון (0 = ממוצע שוק):", min_value=0, max_value=40, step=1, value=0)

if "history" not in st.session_state:
    st.session_state["history"] = []

colC, colD = st.columns([1,1])
with colC:
    run_btn = st.button("🔍 הפק דו״ח")
with colD:
    clear_btn = st.button("🗑️ נקה היסטוריה")

if clear_btn:
    st.session_state["history"] = []
    st.success("היסטוריית החיפושים נוקתה ✅")

if run_btn:
    if not job.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מבצע חיפוש חי במקורות ישראליים..."):
            live = fetch_live_snippets(job)
            st.markdown("### 🌐 דגימות חיות מהשוק")
            st.markdown(live)

        with st.spinner("מפיק טבלת בנצ׳מארק מפורטת..."):
            md_table = generate_table(job, years, live)

        st.markdown("### 📊 טבלת שכר מלאה (כל רכיבי השכר)")
        st.markdown(md_table, unsafe_allow_html=True)

        # ננסה לחשב סיכומים מתוך הטבלה
        try:
            df = markdown_to_df(md_table)
            gross, emp_cost = compute_totals(df)
            if gross or emp_cost:
                st.markdown(f"""
                <div class="summary-card">
                    <b>סיכום חישובים מתוך הטבלה:</b><br>
                    {"שכר ברוטו לעובד (ממוצע רכיבים): <b>{:,.0f} ₪</b>".format(gross) if gross else "שכר ברוטו: לא ניתן לחשב"}<br>
                    {"עלות מעסיק כוללת (ממוצע רכיבים): <b>{:,.0f} ₪</b>".format(emp_cost) if emp_cost else "עלות מעסיק: לא ניתן לחשב"}
                </div>
                """, unsafe_allow_html=True)
        except Exception as e:
            st.info(f"לא הצלחתי להמיר את הטבלה לחישוב אוטומטי ({e}). אפשר עדיין להעתיק/לשמור את הטבלה.")

        # שמירה בהיסטוריה
        st.session_state["history"].append({
            "job": job, "experience": years,
            "time": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "report": md_table
        })

        # כפתור העתק דו"ח
        st.components.v1.html(f"""
        <div style="text-align:center; margin-top:12px;">
          <button class="copy-btn" onclick="navigator.clipboard.writeText(`{md_table.replace('`','').replace('"','').replace("'","")}`); alert('הדו\"ח הועתק ללוח ✅');">📋 העתק דו\"ח</button>
        </div>
        """, height=80)

# היסטוריה
if st.session_state["history"]:
    st.markdown("### 🕓 היסטוריית חיפושים")
    for item in reversed(st.session_state["history"]):
        job_ = item["job"]; exp_ = item["experience"]; t_ = item["time"]
        exp_label = "ממוצע שוק" if exp_==0 else f"{exp_} שנות ניסיון"
        with st.expander(f"{job_} — {exp_label} — {t_}"):
            st.markdown(item["report"])
