import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os

# הגדרות כלליות
st.set_page_config(page_title="מערכת שכר ארגונית חכמה", layout="centered")

# עיצוב RTL
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
    .copy-btn {
        background-color: #42A5F5;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        border: none;
    }
    .copy-btn:hover {
        background-color: #1E88E5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# כותרת
st.title("💼 מערכת ניתוח שכר ארגונית מתקדמת")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מלא הכולל טווחי שכר, מנגנוני תגמול, פירוט הטבות ושווי רכב מקובל – מותאם לחברות דומות ל־**Benda Magnetic בע״מ**.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

# פונקציה לניתוח השכר
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור דו״ח שכר מקצועי ומלא עבור המשרה "{job_title}" בשוק הישראלי,
    בהקשר של חברות דומות ל"בנדא מגנטיק בע״מ" (יבואנים, טכנולוגיה, אלקטרוניקה, גאדג׳טים).

    חלק את הדו״ח לשישה חלקים:
    1. סקירה כללית של התפקיד – מהות, תחומי אחריות, ענפים רלוונטיים.
    2. מבנה השכר – טווחים (מינימום, ממוצע, מקסימום) לפי השוק הישראלי בלבד.
    3. תגמול משתנה – עמלות, בונוסים, מנגנוני חישוב ואחוזים מקובלים.
    4. הטבות ותנאים נלווים – לפרט כל רכיב בנפרד (סיבוס, טלפון, קרן השתלמות, ביטוחים וכו׳) ולציין את הסכום הממוצע.
    5. רכבי חברה – לציין דגמים מקובלים ושווי רכב משוער לתפקיד זה.
    6. מגמות שוק והשפעות – שינויים טכנולוגיים, ביקוש, עלויות מחיה, ייבוא, חוסר בכוח אדם וכו׳.

    בסוף הדו״ח הוסף טבלה מסכמת עם עמודות:
    • רכיב שכר
    • טווח (מינימום–מקסימום)
    • ממוצע שוק (₪)
    • מנגנון תגמול מקובל
    • הערות / פירוט

    הצג את התוצאה בעברית מקצועית וברורה בלבד.
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "אתה אנליסט שכר ויועץ ארגוני בכיר בישראל."},
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

                # ✅ מציג Markdown מעוצב תקין
                st.markdown("### 🧾 דו״ח שכר", unsafe_allow_html=True)
                st.markdown(report)

                # ✅ כפתור העתק דו"ח עובד
                st.components.v1.html(
                    f"""
                    <div style="text-align:center; margin-top:15px;">
                        <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                        alert('✅ הדו״ח הועתק ללוח!');">
                            📋 העתק דו״ח
                        </button>
                    </div>
                    """,
                    height=100,
                )
            else:
                st.error("לא ניתן להפיק דו״ח כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
