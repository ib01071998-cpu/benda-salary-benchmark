import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os
import pandas as pd
import matplotlib.pyplot as plt

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

st.set_page_config(page_title="מערכת שכר ארגונית", layout="centered")

st.title("💼 מערכת חכמה לניתוח שכר - Benda Magnetic")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מפורט לפי בנצ׳מארק משוק העבודה הישראלי, בהתאמה לחברות דומות ל־Benda Magnetic בע״מ.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

def analyze_salary_gpt(job_title):
    prompt = f"""
    אתה אנליסט שכר בכיר המתמחה בשוק הישראלי.
    צור דו״ח שכר מלא עבור המשרה "{job_title}", בהקשר של חברות דומות לבנדא מגנטיק בע״מ – כלומר יבואנים, משווקים, חברות טכנולוגיה, גאדג׳טים וציוד אלקטרוני.

    הדו״ח יכלול:
    1. **שכר בסיס:** טווח (מינימום, ממוצע, מקסימום) עם מספרים בש״ח.
    2. **תגמול משתנה:** עמלות, בונוסים, מנגנוני תגמול (לדוגמה: 5% מהמכירות, בונוס רבעוני לפי יעד).
    3. **הטבות:** רכב חברה (כולל ערך הרכב ודגמים נפוצים), סיבוס / תן ביס (גובה סכום חודשי), טלפון, מחשב, קרן השתלמות וכו׳.
    4. **מגמות שוק:** מגמות משפיעות על השכר או על הדרישה לתפקיד (לדוגמה: עלייה בתחרות על אנשי מכירות טכנולוגיים).
    5. **טבלת סיכום לפי ניסיון:**
       - רמה התחלתית (0–2 שנים)
       - בינונית (3–5 שנים)
       - בכירה (6+ שנים)
       כל שורה תכלול שכר בסיס, משתנה, סה״כ ממוצע והערות.
    
    הצג הכל בעברית תקנית, בטבלה מסודרת ובשפה מקצועית של HR.
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


def draw_salary_chart(min_salary, avg_salary, max_salary, title):
    """מציג גרף טווח שכר"""
    fig, ax = plt.subplots()
    categories = ["מינימום", "ממוצע", "מקסימום"]
    values = [min_salary, avg_salary, max_salary]
    bars = ax.bar(categories, values)
    ax.bar_label(bars)
    plt.title(f"טווח שכר עבור {title}")
    plt.ylabel("ש״ח")
    st.pyplot(fig)


if st.button("נתח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מנתח נתוני שכר... אנא המתן..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ הדו״ח מוכן")
                st.markdown(report)

                # ניסיון לחלץ טווחי שכר בסיסיים מתוך הטקסט
                import re
                salaries = re.findall(r"(\d{4,6})", report)
                if len(salaries) >= 3:
                    min_sal, avg_sal, max_sal = map(int, salaries[:3])
                    draw_salary_chart(min_sal, avg_sal, max_sal, job_title)
                else:
                    st.info("⚠️ לא נמצאו נתוני טווח ברורים לגרף.")
            else:
                st.error("לא ניתן להפיק דו״ח כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
