from flask import Flask, request, jsonify, render_template, redirect, url_for
import sqlite3
import json
import jdatetime
import datetime

# --- تنظیمات اولیه ---
app = Flask(__name__)
DB_PATH = "atabat_sample.db"
BOT_TOKEN = "YOUR_BOT_TOKEN" # <<< توکن بات خود را اینجا قرار دهید

# این دیکشنری وضعیت هر کاربر را در گفتگو نگهداری می‌کند
user_states = {}

# --- توابع کمکی ---
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_message(chat_id, text, reply_markup=None):
    import requests
    BALE_API_URL = f"https://tapi.bale.ai/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        response = requests.post(BALE_API_URL, json=payload)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.exceptions.RequestException as e:
        print(f"Error sending message: {e}")
        return jsonify({"ok": False, "description": "Failed to send message"}), 500

# --- مسیرهای مربوط به پنل مدیریت تحت وب ---

@app.route('/admin')
def admin_index():
    conn = get_connection()
    assignments = conn.execute('SELECT * FROM rahnama ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_layout.html', assignments=assignments) # یک فایل html جدید برای این می‌سازیم

@app.route('/admin/add', methods=('GET', 'POST'))
def admin_add():
    if request.method == 'POST':
        # دریافت داده از فرم
        guide_name = request.form['guide_name']
        guide_national_id = request.form['guide_national_id']
        enter_date = request.form['enter_date']
        exit_date = request.form['exit_date']
        city = request.form['city']
        hotel_name = request.form['hotel_name']
        fixed_manager_name = request.form['fixed_manager_name']
        
        # ذخیره در دیتابیس
        conn = get_connection()
        conn.execute('INSERT INTO rahnama (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_index'))

    return render_template('admin_form.html', assignment=None)

# --- مسیر اصلی بات (Webhook) ---
@app.route("/bot", methods=["POST"])
def bot_webhook():
    # ... (کد مربوط به وب‌هوک که قبلا داشتیم، بدون تغییر اینجا قرار می‌گیرد) ...
    # (برای سادگی، بخش بزرگی از کد قبلی شما اینجا تکرار می‌شود)
    data = request.json
    
    # مدیریت پیام‌های متنی
    if "message" in data:
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")

        if not chat_id:
            return jsonify({"status": "error"})

        if text == "/start":
            reply = "سلام! 👋\nبه بات ارزشیابی مدیران ثابت خوش آمدید.\nلطفاً برای شروع، کد ملی خود را وارد نمایید:"
            return send_message(chat_id, reply)

        conn = get_connection()
        rahnama_row = conn.execute("SELECT * FROM rahnama WHERE guide_national_id = ? ORDER BY enter_date DESC LIMIT 1", (text,)).fetchone()
        conn.close()

        if not rahnama_row:
            return send_message(chat_id, "❌ کد ملی شما در سیستم یافت نشد.")

        try:
            exit_date_str = rahnama_row["exit_date"]
            shamsi_parts = list(map(int, exit_date_str.split('-')))
            exit_date_gregorian = jdatetime.date(shamsi_parts[0], shamsi_parts[1], shamsi_parts[2]).togregorian()
            
            today_gregorian = datetime.date.today()
            deadline = exit_date_gregorian + datetime.timedelta(days=30)
            
            # تبدیل تاریخ به شمسی برای نمایش به کاربر
            exit_date_jalali = jdatetime.date.fromgregorian(date=exit_date_gregorian)
            exit_date_shamsi_str = exit_date_jalali.strftime("%Y/%m/%d")

            if today_gregorian < exit_date_gregorian:
                reply = f"دوره ارزشیابی شما برای این ماموریت هنوز آغاز نشده است. شما از تاریخ {exit_date_shamsi_str} می‌توانید ارزشیابی را انجام دهید."
                return send_message(chat_id, reply)
            
            if today_gregorian > deadline:
                reply = "مهلت یک ماهه شما برای ثبت ارزشیابی این ماموریت به پایان رسیده است."
                return send_message(chat_id, reply)

        except Exception as e:
            print(f"Date processing error: {e}")
            return send_message(chat_id, "خطا در پردازش تاریخ دیتابیس.")
            
        user_states[chat_id] = dict(rahnama_row)
        user_states[chat_id]["state"] = "awaiting_hotel_confirmation"

        reply = (
            f"✅ جناب آقای {rahnama_row['guide_name']}، هویت شما تایید شد.\n\n"
            f"لطفاً اطلاعات زیر را تایید کنید:\n"
            f"🏨 **هتل:** {rahnama_row['hotel_name']}\n"
            f"👤 **مدیر ثابت:** {rahnama_row['fixed_manager_name']}\n\n"
            "آیا این هتل و مدیری است که قصد ارزشیابی آن را دارید؟"
        )
        buttons = {"keyboard": [[{"text": "❌ خیر، اطلاعات اشتباه است"} , {"text": "✅ بله، صحیح است"}]], "resize_keyboard": True, "one_time_keyboard": True}
        return send_message(chat_id, reply, reply_markup=json.dumps(buttons))

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
