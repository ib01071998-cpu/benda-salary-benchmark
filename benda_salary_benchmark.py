import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os

# 🔹 הגדרות כלליות
st.set_page_config(page_title="מערכת שכר ארגונית", layout="centered")

# עיצוב RTL ו־UI
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
        font-size: 16px;
        line-height: 1.8;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

st.title("💼 מערכת חכמה לניתוח שכר")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מפורט לפי בנצ׳מארק השוק הישראלי, מותאם לחברות דומות ל־**Benda Magnetic בע״מ**.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

# פונקציה: ניתוח שכר דרך GPT
def analyze_salary_gpt(job_title):
    prompt = f"""
    אתה אנליסט שכר בכיר בישראל.
    צור דו״ח שכר מפורט עבור המשרה "{job_title}", בהקשר של חברות כמו בנדא מגנטיק בע״מ (יבואנים, טכנולוגיה, גאדג׳טים, ציוד אלקטרוני).

    הדו״ח צריך לכלול:
    1. **שכר בסיס:** טווח (מינימום, ממוצע, מקסימום) עם ערכים בש״ח.
    2. **תגמול משתנה:** עמלות, בונוסים, מנגנוני תגמול (לדוגמה: 5% מהמכירות החודשיות או בונוס רבעוני).
    3. **הטבות:** רכב חברה (דגמים ומחיר ממוצע), סיבוס, טלפון, קרן השתלמות וכו׳ עם סכומים מוערכים.
    4. **מגמות שוק:** מגמות המשפיעות על רמות השכר.
    5. **טבלה תיאורית מסכמת לפי רמות ניסיון** (במילים בלבד, לא נדרשת טבלה אמיתית).
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


# כפתור להרצת הניתוח
if st.button("🔍 נתח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מנתח נתוני שכר... אנא המתן..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ הדו״ח מוכן")
                st.markdown(f"<div class='report-container'>{report}</div>", unsafe_allow_html=True)
            else:
                st.error("לא ניתן להפיק דו״ח כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
