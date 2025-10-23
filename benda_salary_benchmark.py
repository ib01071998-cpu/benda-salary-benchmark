import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os

# 🔹 הגדרות כלליות
st.set_page_config(page_title="טבלת בנצ'מארק שכר", layout="centered")

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

st.title("💼 טבלת בנצ'מארק שכר ממוקדת")
st.markdown("הזן שם משרה בעברית ותקבל טבלת שכר מסכמת הכוללת רכיבי שכר, טווחים, ממוצעים, מנגנוני תגמול, והטבות – כולל דגמי רכב ושווי רכב מקובל.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

# פונקציה לניתוח השכר
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור טבלת שכר מסכמת בלבד עבור המשרה "{job_title}" בשוק הישראלי.
    אל תכתוב טקסט נוסף לפני או אחרי – רק טבלה בפורמט Markdown.

    הטבלה צריכה לכלול את העמודות הבאות:
    | רכיב שכר | טווח (מינימום–מקסימום) | ממוצע שוק (₪) | מנגנון תגמול מקובל | הערות / פירוט |

    עליך לכלול לפחות את הרכיבים הבאים:
    - שכר בסיס
    - עמלות מכירה או בונוסים (אם רלוונטי)
    - סיבוס / תן ביס
    - טלפון נייד
    - קרן השתלמות
    - ביטוח בריאות
    - פנסיה
    - רכב חברה (כולל דגמים מקובלים, לדוגמה: סקודה סופרב, מאזדה 6, טויוטה קאמרי; ולהוסיף גם שווי שימוש חודשי ממוצע בשקלים)

    דוגמה לעיצוב שורה:
    | רכב חברה | 2,000–4,000 | 3,000 | חודשי | דגמים: סקודה סופרב, מאזדה 6, טויוטה קאמרי — שווי שימוש חודשי כ־3,000 ₪ |

    יש להציג את כל הנתונים בעברית מלאה, מדויקת וברורה בלבד.
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "אתה אנליסט שכר ויועץ ארגוני בכיר בישראל."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
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
if st.button("🔍 הפק טבלת שכר"):
    if not job_title.strip():
        st.warning("אנא הזן שם משרה.")
    else:
        with st.spinner("מפיק טבלת שכר... אנא המתן..."):
            report = analyze_salary_gpt(job_title)

            if report:
                st.success("✅ טבלת השכר הופקה בהצלחה")

                # ✅ מציג רק את הטבלה (Markdown מעוצב)
                st.markdown("### 🧾 טבלת שכר מסכמת", unsafe_allow_html=True)
                st.markdown(report)

                # ✅ כפתור העתק דו"ח
                st.components.v1.html(
                    f"""
                    <div style="text-align:center; margin-top:15px;">
                        <button class="copy-btn" onclick="navigator.clipboard.writeText(`{report.replace('`','').replace('"','').replace("'", '')}`);
                        alert('✅ הטבלה הועתקה ללוח!');">
                            📋 העתק טבלה
                        </button>
                    </div>
                    """,
                    height=100,
                )
            else:
                st.error("לא ניתן להפיק טבלה כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
