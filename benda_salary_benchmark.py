import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os

# 🔹 הגדרות כלליות
st.set_page_config(page_title="מערכת שכר ארגונית מתקדמת", layout="centered")

# עיצוב ממשק RTL
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
        padding: 25px;
        border-radius: 12px;
        margin-top: 20px;
        font-size: 17px;
        line-height: 1.9;
    }
    h2 {
        color: #1E88E5;
        font-size: 22px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# כותרת
st.title("💼 מערכת ניתוח שכר חכמה ומעמיקה")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מלא הכולל טווחי שכר, מבנה תגמול, הטבות, מגמות שוק ומדדי תחרותיות – מותאם לחברות דומות ל־**Benda Magnetic בע״מ**.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

# פונקציה: ניתוח שכר דרך GPT
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור דו״ח שכר מקצועי ומלא עבור המשרה "{job_title}" בשוק הישראלי,
    בהקשר של חברות דומות ל"בנדא מגנטיק בע״מ" (יבואנים, טכנולוגיה, אלקטרוניקה, גאדג׳טים).

    חלק את הדו״ח לשישה פרקים מסודרים:
    1. סקירה כללית של התפקיד – מהות, תחומי אחריות, ענפים רלוונטיים.
    2. מבנה השכר – הצג טווחים (מינימום, ממוצע, מקסימום) לפי השוק הישראלי בלבד.
    3. תגמול משתנה – עמלות, בונוסים, מנגנוני חישוב, אחוזים מקובלים.
    4. הטבות ותנאים נלווים – סוגי רכב ודגמים, סיבוס, טלפון, קרן השתלמות, ביטוחים וכו׳.
    5. מגמות שוק והשפעות – שינויים טכנולוגיים, מגמות ביקוש, עלויות מחיה, השפעת ייבוא, חוסר בכוח אדם וכו׳.
    6. ניתוח חכם:
        • מדד תחרותיות שכר (נמוך / בינוני / גבוה)
        • מדד אטרקטיביות כוללת (שכר + תנאים)
        • אחוז סטייה בין טווחי השוק הכלליים
        • המלצות ניהוליות לפעולה

    הצג את התשובה בעברית ברורה, עם כותרות משנה, הדגשות, ורצוי לכלול הערכות כמותיות (₪) כשאפשר.
    אין צורך להשוות לשכר פנימי בארגון, רק לשוק הישראלי.
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "אתה אנליסט שכר ויעוץ ארגוני בכיר בישראל."},
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


# הפעלת הניתוח
if st.button("🔍 הפק דו״ח ניתוח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק דו״ח ניתוח שכר מקיף... אנא המתן..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ הדו״ח הופק בהצלחה")
                st.markdown(f"<div class='report-container'>{report}</div>", unsafe_allow_html=True)
            else:
                st.error("לא ניתן להפיק דו״ח כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
