from flask import Flask, request, jsonify
import sqlite3
import requests
import os

app = Flask(__name__)

# توکن بات بله
TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

# مسیر صفحه اصلی
@app.route('/')
def home():
    return "ربات بله فعال است."

# مسیر دریافت پیام‌ها از بات
@app.route('/bot', methods=['POST'])
def webhook():
    try:
        data = request.get_json()

        # گرفتن اطلاعات کاربر و پیام
        message = data.get("message", {})
        text = message.get("text", "")
        chat_id = message.get("chat", {}).get("id", "")

        if not chat_id or not text:
            return jsonify({"status": "no message"}), 200

        if text == "/start":
            welcome = (
                "سلام! 👋\n"
                "به بات ارزشیابی مدیران ثابت خوش آمدید.\n"
                "این بات به شما کمک می‌کند تا پس از اقامت، مدیر ثابت هر هتل را ارزیابی کنید.\n\n"
                "لطفاً کد ملی خود را وارد نمایید:"
            )
            send_message(chat_id, welcome)
            return jsonify({"status": "ok"})

        # بررسی کدملی وارد شده
        if text.isdigit() and len(text) == 10:
            user_info = get_user_info(text)
            if user_info:
                name = user_info['rahname_name']
                hotel = user_info['hotel']
                modir_name = user_info['modir_name']
                exit_date = user_info['exit_date']

                if is_allowed_to_rate(exit_date):
                    msg = (
                        f"جناب آقای {name}، خوش آمدید 🌟\n"
                        f"لطفاً مدیر ثابت هتل {hotel}، جناب آقای {modir_name} را با دقت ارزیابی نمایید.\n"
                        "آیا اطلاعات فوق صحیح است؟"
                    )
                    keyboard = {
                        "keyboard": [
                            [{"text": "✅ بله، صحیح است"}, {"text": "❌ خیر، اشتباه است"}]
                        ],
                        "resize_keyboard": True
                    }
                    send_message(chat_id, msg, keyboard)
                else:
                    send_message(chat_id, "⏳ هنوز مجاز به ثبت ارزشیابی نیستید. لطفاً پس از پایان اقامت اقدام فرمایید.")
            else:
                send_message(chat_id, "❌ کد ملی شما در سیستم یافت نشد.")
        else:
            send_message(chat_id, "لطفاً یک کد ملی معتبر ۱۰ رقمی وارد نمایید.")

        return jsonify({"status": "ok"})

    except Exception as e:
        print("خطا:", e)
        return jsonify({"status": "error", "message": str(e)})

# تابع ارسال پیام به کاربر
def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(BALE_API_URL, json=payload)
        print("پاسخ بله:", response.text)
    except Exception as e:
        print("خطا در ارسال پیام:", e)

# دریافت اطلاعات کاربر از دیتابیس SQLite
def get_user_info(codemelli):
    try:
        conn = sqlite3.connect('atabat.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rahname_name, hotel, modir_name, exit_date 
            FROM rahnamah_info 
            WHERE codemelli = ?
        """, (codemelli,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "rahname_name": row[0],
                "hotel": row[1],
                "modir_name": row[2],
                "exit_date": row[3]
            }
        return None
    except Exception as e:
        print("خطا در اتصال به دیتابیس:", e)
        return None

# بررسی اینکه آیا مجاز به ارزشیابی هست یا نه (بعد از تاریخ خروج)
from datetime import datetime
def is_allowed_to_rate(exit_date_str):
    try:
        today = datetime.today().date()
        exit_date = datetime.strptime(exit_date_str, "%Y-%m-%d").date()
        return today >= exit_date
    except Exception as e:
        print("خطا در پردازش تاریخ:", e)
        return False

# اجرای برنامه
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
