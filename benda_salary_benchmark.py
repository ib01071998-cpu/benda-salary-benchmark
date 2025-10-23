import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import pandas as pd
import matplotlib.pyplot as plt
import time
import os
import io

# 🔹 הגדרות כלליות
st.set_page_config(page_title="מערכת שכר ארגונית", layout="centered")

# יישור טקסט לימין – RTL
st.markdown(
    """
    <style>
    * { direction: rtl; text-align: right; }
    div.stButton > button {
        background-color: #1E88E5;
        color: white;
        border-radius: 8px;
        font-weight: bold;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #1565C0;
        color: #fff;
    }
    .report-container {
        background-color: #F9FAFB;
        padding: 20px;
        border-radius: 10px;
        margin-top: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

st.title("💼 מערכת חכמה לניתוח שכר")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מפורט המבוסס על בנצ'מארק בשוק הישראלי, מותאם לאופי חברות כמו **Benda Magnetic בע״מ** – יבואנים, משווקי טכנולוגיה וציוד אלקטרוני.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")


# פונקציה לקבלת ניתוח שכר מה-GPT
def analyze_salary_gpt(job_title):
    prompt = f"""
    אתה אנליסט שכר בכיר בישראל.
    צור דו״ח שכר מפורט עבור המשרה "{job_title}", בהקשר של חברות כמו בנדא מגנטיק בע״מ (יבואנים, טכנולוגיה, גאדג׳טים, ציוד אלקטרוני).

    מבנה הדו״ח:
    1. **שכר בסיס:** הצג טווח (מינימום, ממוצע, מקסימום) עם ערכים בש״ח.
    2. **תגמול משתנה:** פרט עמלות, בונוסים ומנגנוני תגמול – לדוגמה: 5% מהמכירות החודשיות או בונוס רבעוני לפי יעדים.
    3. **הטבות:** פרט רכב חברה (דגמים ומחיר ממוצע), סיבוס / תן ביס, טלפון, קרן השתלמות וכו׳ כולל סכומים מוערכים.
    4. **מגמות שוק:** נתח מגמות המשפיעות על השכר או הדרישה למקצוע.
    5. **טבלה מסכמת לפי ניסיון תעסוקתי:** 
        | רמה | שכר בסיס | תגמול משתנה | סה״כ ממוצע | הערות |
        |------|------------|----------------|----------------|----------|
        | ג׳וניור (0–2 שנים) | ... | ... | ... | ... |
        | ביניים (3–5 שנים) | ... | ... | ... | ... |
        | בכיר (6+ שנים) | ... | ... | ... | ... |
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "אתה אנליסט שכר מנוסה לשוק הישראלי."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6,
            )
            return response.choices[0].message.content

        except RateLimitError:
            wait = 10 * (attempt + 1)
            st.warning(f"המערכת עמוסה כרגע. ניסיון חוזר בעוד {wait} שניות...")
            time.sleep(wait)
        except (APIError, OpenAIError) as e:
            st.error(f"שגיאת תקשורת עם OpenAI: {str(e)}")
            break
        except Exception as e:
            st.error(f"שגיאה כללית: {str(e)}")
            break

    st.error("המערכת עמוסה מדי כרגע או שהמפתח אינו תקין. נסה שוב בעוד מספר דקות.")
    return None


# פונקציה לציור גרף טווח שכר
def draw_salary_chart(min_salary, avg_salary, max_salary, title):
    fig, ax = plt.subplots()
    categories = ["מינימום", "ממוצע", "מקסימום"]
    values = [min_salary, avg_salary, max_salary]
    bars = ax.bar(categories, values, color=["#64B5F6", "#42A5F5", "#1E88E5"])
    ax.bar_label(bars)
    plt.title(f"טווח שכר עבור {title}")
    plt.ylabel("ש״ח")
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    st.pyplot(fig)


if st.button("🔍 נתח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מנתח נתוני שכר... אנא המתן..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ הדו״ח מוכן")
                st.markdown(f"<div class='report-container'>{report}</div>", unsafe_allow_html=True)

                # ניסיון לחלץ טווח שכר מתוך הטקסט
                import re
                salaries = re.findall(r"(\d{4,6})", report)
                if len(salaries) >= 3:
                    min_sal, avg_sal, max_sal = map(int, salaries[:3])
                    draw_salary_chart(min_sal, avg_sal, max_sal, job_title)

                # יצירת טבלה אינטראקטיבית (אם יש מידע מתאים)
                data = {
                    "רמת ניסיון": ["ג׳וניור (0–2)", "ביניים (3–5)", "בכיר (6+)"],
                    "שכר בסיס (ש״ח)": [min_sal, avg_sal, max_sal],
                    "תגמול משתנה (ש״ח)": [int(min_sal*0.1), int(avg_sal*0.15), int(max_sal*0.2)],
                    "סה״כ ממוצע (ש״ח)": [int(min_s_]()
