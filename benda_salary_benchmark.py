import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os
from fpdf import FPDF

# יצירת לקוח OpenAI
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY)

# הגדרות עמוד
st.set_page_config(page_title="מערכת שכר ארגונית", layout="centered")

st.title("💼 מערכת חכמה לניתוח שכר")
st.markdown("הזן שם משרה בעברית ותקבל דו״ח שכר מפורט לפי בנצ'מארק השוק הישראלי.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

def analyze_salary_gpt(job_title):
    prompt = f"""
    אתה אנליסט שכר מומחה לשוק הישראלי.
    צור דו״ח שכר מפורט עבור המשרה "{job_title}" הכולל:
    1. טווח שכר ממוצע (מינימום, ממוצע, מקסימום)
    2. מבנה השכר (בסיס, עמלות, בונוסים)
    3. מודלי תגמול ובונוס
    4. הטבות נפוצות (רכב, סיבוס, קרן השתלמות וכו׳)
    5. הערות לפי אזור גיאוגרפי וניסיון
    6. מגמות שוק עדכניות
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


def generate_pdf(report_text, job_title):
    """יוצר קובץ PDF מהדו״ח"""
    pdf = FPDF()
    pdf.add_page()
    pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
    pdf.set_font('DejaVu', '', 14)
    
    pdf.cell(0, 10, f"דו״ח שכר - {job_title}", ln=True, align='R')
    pdf.ln(10)
    pdf.multi_cell(0, 10, report_text, align='R')
    
    pdf_file = f"Salary_Report_{job_title}.pdf"
    pdf.output(pdf_file)
    return pdf_file


if st.button("נתח שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מנתח נתוני שכר... אנא המתן..."):
            report = analyze_salary_gpt(job_title)
            if report:
                st.success("✅ הדו״ח מוכן")
                st.markdown(report)

                pdf_file = generate_pdf(report, job_title)
                with open(pdf_file, "rb") as file:
                    st.download_button(
                        label="📄 הורד דו״ח כ-PDF",
                        data=file,
                        file_name=pdf_file,
                        mime="application/pdf"
                    )
            else:
                st.error("לא ניתן להפיק דו״ח כרגע. ייתכן והמפתח שגוי או שנגמרו הקרדיטים.")
