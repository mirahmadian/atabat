from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

DB_PATH = "atabat_sample.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/bot", methods=["POST"])
def bot_webhook():
    data = request.json
    message = data.get("message", {})
    text = message.get("text", "").strip()
    chat_id = message.get("chat", {}).get("id")

    if text == "/start":
        reply = (
            "سلام! 👋\n"
            "به بات ارزشیابی مدیران ثابت خوش آمدید.\n"
            "لطفاً کد ملی خود را وارد نمایید:"
        )
        return send_message(chat_id, reply)

    # جستجو در دیتابیس براساس کدملی
    row = None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM rahnama WHERE guide_national_id = ?", (text,))
    row = cursor.fetchone()
    conn.close()

    if row is None:
        reply = "❌ کد ملی شما در سیستم یافت نشد."
        return send_message(chat_id, reply)

    reply = (
        f"جناب آقای {row['guide_name']}،\n"
        f"لطفا ارزشیابی مدیر ثابت هتل {row['hotel_name']}، "
        f"جناب آقای {row['fixed_manager_name']} را با دقت تکمیل نمایید."
    )
    # اینجا می‌تونی کلید تایید و رد اضافه کنی (اگر خواستی)
    return send_message(chat_id, reply)


def send_message(chat_id, text):
    import requests
    TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
    BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    response = requests.post(BALE_API_URL, json=payload)
    return jsonify(response.json())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
