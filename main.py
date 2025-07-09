from flask import Flask, request
import requests
import pandas as pd
import jdatetime

app = Flask(__name__)

# توکن و لینک API بات
BALE_BOT_TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
BALE_API_URL = f"https://tapi.bale.ai/bot{BALE_BOT_TOKEN}"

# مسیر فایل اکسل آزمایشی
EXCEL_FILE = "atabat_sample.xlsx"

@app.route("/", methods=["POST"])
def webhook():
    data = request.get_json()

    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        if text == "/start":
            response = handle_start(chat_id)
            send_message(chat_id, response)

    return "OK", 200

def handle_start(chat_id):
    try:
        df = pd.read_excel(EXCEL_FILE)
        # فرض: ستون‌های فایل شامل کدملی مدیر راهنما و سایر اطلاعات هستند
        df["تاریخ اعزام"] = df["تاریخ اعزام"].apply(shamsi_to_miladi)

        # برای تست ساده، فرض می‌کنیم chat_id همان کدملی است
        user_id = str(chat_id)

        df_user = df[df["کدملی مدیر راهنما"] == user_id]
        if df_user.empty:
            return "اطلاعاتی برای شما پیدا نشد."

        # پیدا کردن آخرین اعزام (جدیدترین تاریخ)
        latest_row = df_user.sort_values("تاریخ اعزام", ascending=False).iloc[0]

        # ساخت پیام
        msg = (
            "📅 آخرین اعزام شما:\n"
            f"شهر: {latest_row['شهر']}\n"
            f"هتل: {latest_row['نام هتل']}\n"
            f"مدیر ثابت: {latest_row['نام مدیر ثابت']} ({latest_row['کدملی مدیر ثابت']})\n"
            f"تاریخ اعزام: {latest_row['تاریخ اعزام'].date()}"
        )
        return msg
    except Exception as e:
        return f"خطا در پردازش اطلاعات: {str(e)}"

def shamsi_to_miladi(date_str):
    try:
        jdate = jdatetime.datetime.strptime(str(date_str), "%Y/%m/%d")
        return jdate.togregorian()
    except Exception:
        return pd.NaT

def send_message(chat_id, text):
    url = f"{BALE_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(url, json=payload)
