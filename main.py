from flask import Flask, request, jsonify
import sqlite3
import json
import jdatetime # برای کار با تاریخ شمسی
import datetime

# --- تنظیمات اولیه ---
app = Flask(__name__)
DB_PATH = "atabat_sample.db" # مطمئن شوید نام فایل دیتابیس شما همین است
BOT_TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX" # <<< توکن بات خود را اینجا قرار دهید

# --- مدیریت وضعیت کاربران (در حافظه موقت) ---
# این دیکشنری وضعیت هر کاربر را در گفتگو نگهداری می‌کند
# ساختار: {chat_id: {"state": "...", "data": {...}}}
user_states = {}

# --- تابع کمکی برای اتصال به دیتابیس ---
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# --- تابع کمکی برای ارسال پیام به بله ---
def send_message(chat_id, text, reply_markup=None):
    import requests
    BALE_API_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    try:
        response = requests.post(BALE_API_URL, json=payload)
        response.raise_for_status() # بررسی خطاهای احتمالی در پاسخ
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return jsonify({"ok": False, "description": "Failed to send message"}), 500

# --- مسیر اصلی بات (Webhook) ---
@app.route("/bot", methods=["POST"])
def bot_webhook():
    data = request.json
    
    # مدیریت کلیک روی دکمه‌های شیشه‌ای (Inline) - فعلا خالی
    if "callback_query" in data:
        # اینجا بعدا منطق مربوط به دکمه‌های امتیازدهی را اضافه می‌کنیم
        return jsonify({"status": "ok", "message": "callback received"})

    # مدیریت پیام‌های متنی
    if "message" in data:
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")

        if not chat_id:
            return jsonify({"status": "error", "message": "chat_id not found"})

        # --- منطق اصلی بات ---
        
        # 1. مدیریت دستور /start
        if text == "/start":
            reply = (
                "سلام! 👋\n"
                "به بات ارزشیابی مدیران ثابت خوش آمدید.\n"
                "لطفاً برای شروع و احراز هویت، کد ملی خود را وارد نمایید:"
            )
            return send_message(chat_id, reply)

        # 2. بررسی کد ملی و احراز هویت
        conn = get_connection()
        # استفاده از پارامتر ? برای جلوگیری از SQL Injection
        # همیشه آخرین ماموریت کاربر را بر اساس تاریخ ورود برمیگرداند
        rahnama_row = conn.execute(
            "SELECT * FROM rahnama WHERE guide_national_id = ? ORDER BY enter_date DESC LIMIT 1",
            (text,)
        ).fetchone()
        conn.close()

        if not rahnama_row:
            reply = "❌ کد ملی شما در سیستم یافت نشد. لطفاً مجدداً تلاش کنید."
            return send_message(chat_id, reply)

        # 3. بررسی بازه زمانی ارزشیابی
        try:
            # تبدیل تاریخ‌های شمسی از دیتابیس به تاریخ میلادی برای مقایسه
            exit_date_str = rahnama_row["exit_date"] # فرض می‌کنیم فرمت YYYY-MM-DD است
            shamsi_parts = list(map(int, exit_date_str.split('-')))
            exit_date_gregorian = jdatetime.date(shamsi_parts[0], shamsi_parts[1], shamsi_parts[2]).togregorian()
            
            today_gregorian = datetime.date.today()
            deadline = exit_date_gregorian + datetime.timedelta(days=30)

            if today_gregorian < exit_date_gregorian:
                # تبدیل تاریخ میلادی به شمسی برای نمایش به کاربر
                exit_date_jalali = jdatetime.date.fromgregorian(date=exit_date_gregorian)
                exit_date_shamsi_str = exit_date_jalali.strftime("%Y/%m/%d") # فرمت‌بندی تاریخ شمسی

                reply = f"دوره ارزشیابی شما برای این ماموریت هنوز آغاز نشده است. شما از تاریخ {exit_date_shamsi_str} می‌توانید ارزشیابی را انجام دهید."
                return send_message(chat_id, reply)
            
            if today_gregorian > deadline:
                reply = "مهلت یک ماهه شما برای ثبت ارزشیابی این ماموریت به پایان رسیده است."
                return send_message(chat_id, reply)

        except Exception as e:
            print(f"Date conversion error: {e}")
            reply = "خطا در پردازش تاریخ. لطفاً فرمت تاریخ در دیتابیس را بررسی کنید (باید YYYY-MM-DD باشد)."
            return send_message(chat_id, reply)
            
        # 4. اگر همه چیز درست بود، سوال تایید هتل را بپرس
        # ذخیره اطلاعات کاربر برای مراحل بعدی
        user_states[chat_id] = dict(rahnama_row)
        user_states[chat_id]["state"] = "awaiting_hotel_confirmation"

        hotel_name = rahnama_row["hotel_name"]
        manager_name = rahnama_row["fixed_manager_name"]
        
        reply = (
            f"✅ جناب آقای {rahnama_row['guide_name']}، هویت شما تایید شد.\n\n"
            f"لطفاً اطلاعات زیر را تایید کنید:\n"
            f"🏨 **هتل:** {hotel_name}\n"
            f"👤 **مدیر ثابت:** {manager_name}\n\n"
            "آیا این هتل و مدیری است که قصد ارزشیابی آن را دارید؟"
        )
        
        buttons = {
            "keyboard": [
                [{"text": "❌ خیر، اطلاعات اشتباه است"} , {"text": "✅ بله، صحیح است"}]
            ],
            "resize_keyboard": True,
            "one_time_keyboard": True
        }
        return send_message(chat_id, reply, reply_markup=json.dumps(buttons))

    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # در اینجا می‌توانید برنامه را برای تست محلی اجرا کنید
    # برای بارگذاری روی رندر، این بخش نیازی به تغییر ندارد
    app.run(host="0.0.0.0", port=10000, debug=True)
