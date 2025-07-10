from flask import Flask, request, jsonify
import requests
import sqlite3

app = Flask(__name__)

TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

DB_PATH = "database.db"

def send_message(chat_id, text, keyboard=None):
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown"
    }
    if keyboard:
        data["reply_markup"] = keyboard
    resp = requests.post(BALE_API_URL, json=data)
    return resp.json()

def get_user_info_by_national_code(n_code):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, hotel, city, exit_date FROM managers INNER JOIN fixed_managers ON managers.id = fixed_managers.manager_id WHERE managers.national_code = ?", (n_code,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return {
            "name": result[0],
            "hotel": result[1],
            "city": result[2],
            "exit_date": result[3]
        }
    return None

@app.route("/", methods=["GET"])
def home():
    return "Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    # بله فرستاده
    message = data.get("message")
    if not message:
        return jsonify({"status": "no message"}), 200
    
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    # وضعیت کاربر را در دیتابیس یا حافظه بررسی و مدیریت کن (برای سادگی اینجا فقط پاسخ اولیه)
    if text == "/start":
        welcome_text = (
            "سلام!\n"
            "هدف این بات: ارزشیابی مدیران ثابت توسط مدیران راهنما.\n"
            "لطفا کد ملی خود را وارد کنید."
        )
        send_message(chat_id, welcome_text)
        return jsonify({"status": "ok"}), 200

    # فرض می‌کنیم متن ارسالی کد ملی است
    user_info = get_user_info_by_national_code(text)
    if user_info is None:
        send_message(chat_id, "کد ملی یافت نشد. لطفا دوباره کد ملی خود را وارد کنید.")
        return jsonify({"status": "ok"}), 200

    # بررسی تاریخ خروج (بر اساس تاریخ امروز)
    from datetime import datetime
    today = datetime.now().date()
    try:
        exit_date = datetime.strptime(user_info["exit_date"], "%Y-%m-%d").date()
    except Exception:
        send_message(chat_id, "خطا در پردازش تاریخ خروج. لطفا با پشتیبانی تماس بگیرید.")
        return jsonify({"status": "ok"}), 200

    if today < exit_date:
        send_message(chat_id, f"امکان ارزشیابی تا تاریخ {exit_date} وجود ندارد. لطفا بعد از این تاریخ تلاش کنید.")
        return jsonify({"status": "ok"}), 200

    # پیام تایید اطلاعات
    confirm_text = (
        f"جناب آقای {user_info['name']}،\n"
        f"لطفا ارزشیابی مدیر ثابت هتل {user_info['hotel']} در شهر {user_info['city']} را با دقت انجام دهید.\n"
        "آیا اطلاعات صحیح است؟"
    )
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "بله، صحیح است", "callback_data": "confirm_yes"},
                {"text": "خیر، اصلاح شود", "callback_data": "confirm_no"}
            ]
        ]
    }
    send_message(chat_id, confirm_text, keyboard)
    
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run(port=10000)
