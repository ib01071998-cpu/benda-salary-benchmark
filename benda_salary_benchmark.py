import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os

# יצירת לקוח OpenAI מה-API KEY מהסביבה
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="מערכת שכר ארגונית", layout="centered")

st.title("💼 מערכת חכמה לניתוח שכר")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מפורט לפי בנצ׳מארק משוק העבודה בישראל (מאומן על-ידי מספר “מקורות” ידע).")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

def analyze_salary_gpt(job_title):
    prompt = f"""
    אתה אנליסט שכר מומחה לשוק הישראלי.
    בתוך תפקיד "{job_title}" – תבצע ניתוח על-פי לפחות 5 מקורות ידע שונים (סקרי שכר, מודעות דרושים, מחקרי שוק, דוחות פנימיים ומקורות ציבוריים) בישראל.
    צור דו״ח מפורט בעברית הכולל:
    1. טווח שכר ממוצע (מינימום, ממוצע, מקסימום) בש״ח ברוטו.
    2. מבנה השכר: שכר בסיס, עמלות, בונוסים, משתנים.
    3. מודלי תגמול/בונוס נפוצים.
    4. הטבות ותנאים נפוצים (רכב חברה, סיבוס, קרן השתלמות וכו׳).
    5. הערות לפי ניסיון, אזור גאוגרפי, גודל חברה.
    6. מגמות עדכניות בשוק העבודה לתפקיד זה.
    כתוב בעברית תקנית, בסגנון מקצועי עבור מחלקת HR או הנהלה.
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
        except APIError as e:
            st.error(f"שגיאת שרת מצד OpenAI: {str(e)}")
            break
        except OpenAIError as e:
            st.error(f"שגיאת תקשורת עם OpenAI: {str(e)}")
            break
        except Exception as e:
            st.error(f"שגיאה כללית: {str(e)}")
            break

    st.error("המערכת עמוסה מדי כרגע או שהמפתח אינו תקין. נסה שוב בעוד מספר דקות.")
    return None

if st.button("נתח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מנתח נתוני שכר... אנא המתן..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ הדו״ח מוכן")
                st.markdown(report)
            else:
                st.error("לא ניתן להפיק דו״ח כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
