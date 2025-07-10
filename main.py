from flask import Flask, request, jsonify, render_template, redirect
import requests
import sqlite3
import jdatetime
from datetime import datetime

app = Flask(__name__)
TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
DB_PATH = "atabat.db"

# مسیر اصلی فقط برای بررسی اجرا شدن بات
@app.route("/")
def index():
    return "✅ بات در حال اجراست. برای ثبت مدیر راهنما به مسیر /add_rahnama بروید."


# مسیر ثبت اطلاعات مدیر راهنما
@app.route("/add_rahnama", methods=["GET", "POST"])
def add_rahnama():
    if request.method == "POST":
        try:
            guide_name = request.form["guide_name"]
            guide_national_id = request.form["guide_national_id"]
            city = request.form["city"]
            hotel_name = request.form["hotel_name"]
            fixed_manager_name = request.form["fixed_manager_name"]
            fixed_manager_national_id = request.form["fixed_manager_national_id"]
            enter_date_str = request.form["enter_date"]
            exit_date_str = request.form["exit_date"]

            # تبدیل تاریخ شمسی به میلادی
            enter_date = jdatetime.date.fromisoformat(enter_date_str).togregorian().isoformat()
            exit_date = jdatetime.date.fromisoformat(exit_date_str).togregorian().isoformat()

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evaluations (
                    guide_national_id, guide_name, city, hotel_name,
                    fixed_manager_name, fixed_manager_national_id,
                    enter_date, exit_date
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (guide_national_id, guide_name, city, hotel_name, fixed_manager_name,
                  fixed_manager_national_id, enter_date, exit_date))
            conn.commit()
            conn.close()
            return "✅ ثبت با موفقیت انجام شد."

        except Exception as e:
            return f"خطا در ثبت: {e}"

    return render_template("add_rahnama.html")


# مسیر Webhook برای بات بله
@app.route("/bot", methods=["POST"])
def webhook():
    data = request.json

    if not data or "message" not in data:
        return jsonify({"status": "no message"}), 400

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text == "/start":
        send_message(chat_id, "سلام! 👋\n"
                              "به بات ارزشیابی مدیران ثابت خوش آمدید.\n"
                              "این بات به شما کمک می‌کند تا پس از اقامت، مدیر ثابت هر هتل را ارزیابی کنید.\n\n"
                              "لطفاً کد ملی خود را وارد نمایید:")

    elif text.isdigit() and len(text) == 10:
        national_id = text
        info = get_user_info(national_id)
        if info:
            guide_name, city, hotel_name, fixed_manager_name, exit_date = info
            today = datetime.now().date()
            if today >= datetime.strptime(exit_date, "%Y-%m-%d").date():
                msg = f"جناب آقای {guide_name}، خوش آمدید 🌺\n"
                msg += f"شما در شهر {city} اقامت داشتید.\n"
                msg += f"لطفاً مدیر ثابت هتل {hotel_name}، آقای {fixed_manager_name} را ارزیابی نمایید.\n\n"
                msg += "آیا اطلاعات بالا درست است؟"
                send_message(chat_id, msg)
            else:
                send_message(chat_id, "❗️هنوز امکان ارزشیابی وجود ندارد. لطفاً پس از پایان اقامت اقدام نمایید.")
        else:
            send_message(chat_id, "❌ کد ملی شما در سیستم یافت نشد.")

    return jsonify({"status": "ok"})


# تابع ارسال پیام به کاربر در بله
def send_message(chat_id, text):
    try:
        payload = {"chat_id": chat_id, "text": text}
        response = requests.post(BALE_API_URL, json=payload)
        return response.status_code == 200
    except Exception as e:
        print("خطا در ارسال پیام:", e)
        return False


# تابع دریافت اطلاعات کاربر از دیتابیس
def get_user_info(national_id):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT guide_name, city, hotel_name, fixed_manager_name, exit_date
            FROM evaluations
            WHERE guide_national_id = ?
            ORDER BY id DESC LIMIT 1
        """, (national_id,))
        result = cursor.fetchone()
        conn.close()
        return result
    except Exception as e:
        print("DB Error:", e)
        return None


if __name__ == "__main__":
    app.run(debug=True)
