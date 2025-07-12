from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
import sqlite3
import json
import jdatetime
import datetime

# --- تنظیمات اولیه ---
app = Flask(__name__)
DB_PATH = "atabat_sample.db"
BOT_TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX" # <<< توکن بات خود را اینجا قرار دهید

# ... (بقیه کد شما تا این بخش بدون تغییر باقی می‌ماند) ...
user_states = {}

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

# --- مسیرهای مربوط به پنل مدیریت (بدون تغییر) ---
@app.route('/admin')
def admin_index():
    conn = get_connection()
    assignments = conn.execute('SELECT * FROM rahnama ORDER BY id DESC').fetchall()
    conn.close()
    return render_template('admin_index.html', assignments=assignments)

@app.route('/admin/add', methods=('GET', 'POST'))
def admin_add():
    if request.method == 'POST':
        guide_name = request.form['guide_name']
        guide_national_id = request.form['guide_national_id']
        enter_date = request.form['enter_date']
        exit_date = request.form['exit_date']
        city = request.form['city']
        hotel_name = request.form['hotel_name']
        fixed_manager_name = request.form['fixed_manager_name']
        conn = get_connection()
        conn.execute('INSERT INTO rahnama (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_index'))
    return render_template('admin_form.html', assignment=None)

@app.route('/admin/edit/<int:id>', methods=('GET', 'POST'))
def admin_edit(id):
    conn = get_connection()
    assignment = conn.execute('SELECT * FROM rahnama WHERE id = ?', (id,)).fetchone()
    if request.method == 'POST':
        guide_name = request.form['guide_name']
        guide_national_id = request.form['guide_national_id']
        enter_date = request.form['enter_date']
        exit_date = request.form['exit_date']
        city = request.form['city']
        hotel_name = request.form['hotel_name']
        fixed_manager_name = request.form['fixed_manager_name']
        conn.execute('UPDATE rahnama SET guide_name = ?, guide_national_id = ?, enter_date = ?, exit_date = ?, city = ?, hotel_name = ?, fixed_manager_name = ? WHERE id = ?',
                     (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name, id))
        conn.commit()
        conn.close()
        return redirect(url_for('admin_index'))
    conn.close()
    if assignment is None:
        abort(404)
    return render_template('admin_form.html', assignment=assignment)

@app.route('/admin/delete/<int:id>', methods=('POST',))
def admin_delete(id):
    conn = get_connection()
    conn.execute('DELETE FROM rahnama WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_index'))

# --- مسیر اصلی بات (Webhook) ---
@app.route("/bot", methods=["POST"])
def bot_webhook():
    data = request.json
    if "message" in data:
        message = data.get("message", {})
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")
        if not chat_id: return jsonify({"status": "error"})

        if text == "/start":
            reply = "سلام! 👋\nبه بات ارزشیابی مدیران ثابت خوش آمدید.\nلطفاً برای شروع، کد ملی خود را وارد نمایید:"
            return send_message(chat_id, reply)

        conn = get_connection()
        rahnama_row = conn.execute("SELECT * FROM rahnama WHERE guide_national_id = ? ORDER BY enter_date DESC LIMIT 1", (text,)).fetchone()
        
        if not rahnama_row:
            conn.close()
            return send_message(chat_id, "❌ کد ملی شما در سیستم یافت نشد.")

        try:
            exit_date_str = rahnama_row["exit_date"]
            # اطمینان از اینکه تاریخ خالی نیست
            if not exit_date_str:
                raise ValueError("تاریخ خروج در دیتابیس خالی است.")

            shamsi_parts = list(map(int, exit_date_str.split('-')))
            exit_date_gregorian = jdatetime.date(shamsi_parts[0], shamsi_parts[1], shamsi_parts[2]).togregorian()
            
            today_gregorian = datetime.date.today()
            deadline = exit_date_gregorian + datetime.timedelta(days=30)
            
            exit_date_jalali = jdatetime.date.fromgregorian(date=exit_date_gregorian)
            exit_date_shamsi_str = exit_date_jalali.strftime("%Y/%m/%d")

            if today_gregorian < exit_date_gregorian:
                reply = f"دوره ارزشیابی شما برای این ماموریت هنوز آغاز نشده است. شما از تاریخ {exit_date_shamsi_str} می‌توانید ارزشیابی را انجام دهید."
                return send_message(chat_id, reply)
            
            if today_gregorian > deadline:
                reply = "مهلت یک ماهه شما برای ثبت ارزشیابی این ماموریت به پایان رسیده است."
                return send_message(chat_id, reply)

        except Exception as e:
            # --- این بخش تغییر کرده است ---
            # ما مقدار دقیق تاریخ مشکل‌ساز را در پیام خطا نمایش می‌دهیم
            problematic_date = rahnama_row['exit_date'] if rahnama_row else "NOT_FOUND"
            print(f"Date processing error: {e} -- Value was: '{problematic_date}'")
            reply = f"خطا در پردازش تاریخ. فرمت تاریخ ذخیره شده در دیتابیس نامعتبر است: '{problematic_date}'"
            conn.close()
            return send_message(chat_id, reply)
            
        # اگر همه چیز درست بود، به اینجا می‌رسیم
        conn.close()
        user_states[chat_id] = dict(rahnama_row)
        user_states[chat_id]["state"] = "awaiting_hotel_confirmation"

        reply = (f"✅ جناب آقای {rahnama_row['guide_name']}، هویت شما تایید شد.\n\n"
                 f"لطفاً اطلاعات زیر را تایید کنید:\n"
                 f"🏨 **هتل:** {rahnama_row['hotel_name']}\n"
                 f"👤 **مدیر ثابت:** {rahnama_row['fixed_manager_name']}\n\n"
                 "آیا این هتل و مدیری است که قصد ارزشیابی آن را دارید؟")
        buttons = {"keyboard": [[{"text": "❌ خیر، اطلاعات اشتباه است"} , {"text": "✅ بله، صحیح است"}]], "resize_keyboard": True, "one_time_keyboard": True}
        return send_message(chat_id, reply, reply_markup=json.dumps(buttons))

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
