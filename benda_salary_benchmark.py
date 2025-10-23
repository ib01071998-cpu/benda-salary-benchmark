import streamlit as st
from openai import OpenAI, RateLimitError, APIError, OpenAIError
import time
import os
import pandas as pd
from io import StringIO

# הגדרות כלליות
st.set_page_config(page_title="טבלת בנצ'מארק שכר", layout="centered")

# עיצוב כללי RTL + עיצוב טבלה מקצועי
st.markdown(
    """
    <style>
    * { direction: rtl; text-align: right; font-family: "Heebo", sans-serif; }
    h1, h2, h3 { color: #1E88E5; }
    table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        border: 1px solid #E0E0E0;
    }
    th {
        background-color: #1976D2;
        color: white;
        padding: 12px;
        font-weight: bold;
        border: 1px solid #BBDEFB;
        text-align: center;
    }
    td {
        background-color: #FAFAFA;
        border: 1px solid #E3F2FD;
        padding: 10px;
        text-align: center;
        vertical-align: middle;
    }
    tr:nth-child(even) td {
        background-color: #F5F5F5;
    }
    .copy-btn {
        background-color: #42A5F5;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        font-weight: bold;
        cursor: pointer;
        border: none;
        font-size: 16px;
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

st.title("💼 טבלת בנצ'מארק שכר מקצועית")
st.markdown("הזן שם משרה בעברית ותקבל טבלת שכר מעוצבת הכוללת טווחים, ממוצעים, מנגנוני תגמול והטבות – כולל דגמי רכב ושווי רכב מקובל.")

job_title = st.text_input("שם המשרה (לדוגמה: מנהל לוגיסטיקה, איש מכירות, סמנכ״ל תפעול):")

# פונקציה לניתוח השכר
def analyze_salary_gpt(job_title):
    prompt = f"""
    צור טבלת שכר מסכמת בלבד עבור המשרה "{job_title}" בשוק הישראלי.
    אל תכתוב טקסט נוסף לפני או אחרי – רק טבלה בפורמט Markdown.
    עמודות:
    | רכיב שכר | טווח (מינימום–מקסימום) | ממוצע שוק (₪) | מנגנון תגמול מקובל | הערות / פירוט |
    כולל שורת רכב חברה עם דגמים מקובלים (סקודה סופרב, מאזדה 6, טויוטה קאמרי) ושווי שימוש ממוצע.
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


# המרה של טבלת Markdown ל-DataFrame
def markdown_table_to_df(markdown_text):
    try:
        lines = [line.strip() for line in markdown_text.splitlines() if "|" in line]
        data_lines = [line for line in lines if not line.startswith("|-")]
        df = pd.read_csv(StringIO("\n".join(data_lines)), sep="|").dropna(axis=1, how="all")
        df = df.rename(columns=lambda x: x.strip())
        df = df.drop(df.index[0]) if df.iloc[0].str.contains("רכיב").any() else df
        return df
    except Exception as e:
        st.error(f"שגיאה בעיבוד הטבלה: {e}")
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

                df = markdown_table_to_df(report)
                if df is not None:
                    st.markdown("### 🧾 טבלת שכר מסכמת")
                    st.markdown(df.to_html(escape=False, index=False), unsafe_allow_html=True)

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
                    st.markdown("לא ניתן להמיר את הטבלה, מוצג הפלט הגולמי:")
                    st.markdown(report)
            else:
                st.error("לא ניתן להפיק טבלה כרגע. ייתכן שהמפתח שגוי או שנגמרו הקרדיטים.")
