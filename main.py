from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
import sqlite3
import json
import jdatetime
import datetime

# --- تنظیمات اولیه ---
app = Flask(__name__)
DB_PATH = "atabat_sample.db"
BOT_TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"  # توکن بات خود را اینجا قرار دهید

user_states = {}

def get_connection():
    """اتصال به دیتابیس با تنظیمات بهینه"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_message(chat_id, text, reply_markup=None):
    """ارسال پیام به بات بله"""
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

def init_database():
    """ایجاد جدول در صورت عدم وجود"""
    conn = get_connection()
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS rahnama (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guide_name TEXT NOT NULL,
                guide_national_id TEXT NOT NULL,
                enter_date TEXT NOT NULL,
                exit_date TEXT NOT NULL,
                city TEXT NOT NULL,
                hotel_name TEXT NOT NULL,
                fixed_manager_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

# --- مسیرهای مربوط به پنل مدیریت ---
@app.route('/admin')
def admin_index():
    """نمایش لیست کلیه ماموریت‌ها"""
    try:
        conn = get_connection()
        assignments = conn.execute('SELECT * FROM rahnama ORDER BY id DESC').fetchall()
        conn.close()
        return render_template('admin_index.html', assignments=assignments)
    except Exception as e:
        print(f"Error in admin_index: {e}")
        return f"خطا در نمایش لیست: {e}", 500

@app.route('/admin/add', methods=('GET', 'POST'))
def admin_add():
    """افزودن ماموریت جدید"""
    if request.method == 'POST':
        print("=== درخواست POST دریافت شد ===")
        
        try:
            # دریافت داده‌های فرم
            guide_name = request.form.get('guide_name', '').strip()
            guide_national_id = request.form.get('guide_national_id', '').strip()
            enter_date = request.form.get('enter_date', '').strip()
            exit_date = request.form.get('exit_date', '').strip()
            city = request.form.get('city', '').strip()
            hotel_name = request.form.get('hotel_name', '').strip()
            fixed_manager_name = request.form.get('fixed_manager_name', '').strip()
            
            # چاپ داده‌ها برای debug
            print(f"guide_name: {guide_name}")
            print(f"guide_national_id: {guide_national_id}")
            print(f"enter_date: {enter_date}")
            print(f"exit_date: {exit_date}")
            print(f"city: {city}")
            print(f"hotel_name: {hotel_name}")
            print(f"fixed_manager_name: {fixed_manager_name}")
            
            # بررسی اجباری بودن فیلدها
            required_fields = {
                'guide_name': guide_name,
                'guide_national_id': guide_national_id,
                'enter_date': enter_date,
                'exit_date': exit_date,
                'city': city,
                'hotel_name': hotel_name,
                'fixed_manager_name': fixed_manager_name
            }
            
            for field_name, field_value in required_fields.items():
                if not field_value:
                    return f"خطا: فیلد {field_name} الزامی است و نمی‌تواند خالی باشد.", 400
            
            # اعتبارسنجی کد ملی (10 رقم)
            if not guide_national_id.isdigit() or len(guide_national_id) != 10:
                return "خطا: کد ملی باید 10 رقم باشد.", 400
            
            # اعتبارسنجی فرمت تاریخ
            def validate_date_format(date_str, field_name):
                try:
                    parts = date_str.split('/')
                    if len(parts) != 3:
                        return False, f"فرمت تاریخ {field_name} اشتباه است. فرمت صحیح: YYYY/MM/DD"
                    
                    year, month, day = map(int, parts)
                    if year < 1300 or year > 1500:
                        return False, f"سال در تاریخ {field_name} نامعتبر است."
                    if month < 1 or month > 12:
                        return False, f"ماه در تاریخ {field_name} نامعتبر است."
                    if day < 1 or day > 31:
                        return False, f"روز در تاریخ {field_name} نامعتبر است."
                    
                    return True, None
                except ValueError:
                    return False, f"فرمت تاریخ {field_name} اشتباه است."
            
            # اعتبارسنجی تاریخ ورود
            is_valid, error_msg = validate_date_format(enter_date, "ورود")
            if not is_valid:
                return f"خطا: {error_msg}", 400
            
            # اعتبارسنجی تاریخ خروج
            is_valid, error_msg = validate_date_format(exit_date, "خروج")
            if not is_valid:
                return f"خطا: {error_msg}", 400
            
            # ذخیره در دیتابیس
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rahnama (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name))
            
            conn.commit()
            
            # بررسی اینکه رکورد واقعاً ذخیره شده است
            last_id = cursor.lastrowid
            print(f"=== رکورد جدید با ID {last_id} ذخیره شد ===")
            
            # تست خواندن رکورد ذخیره شده
            test_record = conn.execute('SELECT * FROM rahnama WHERE id = ?', (last_id,)).fetchone()
            if test_record:
                print(f"=== تست: رکورد با موفقیت خوانده شد: {dict(test_record)} ===")
            else:
                print("=== خطا: رکورد ذخیره نشد ===")
            
            conn.close()
            
            return redirect(url_for('admin_index'))
            
        except Exception as e:
            print(f"خطا در ذخیره: {e}")
            return f"خطا در ذخیره داده‌ها: {str(e)}", 500
    
    # برای GET request
    return render_template('admin_form.html', assignment=None)

@app.route('/admin/edit/<int:id>', methods=('GET', 'POST'))
def admin_edit(id):
    """ویرایش ماموریت موجود"""
    conn = get_connection()
    
    try:
        assignment = conn.execute('SELECT * FROM rahnama WHERE id = ?', (id,)).fetchone()
        
        if assignment is None:
            conn.close()
            abort(404)
        
        if request.method == 'POST':
            print(f"=== درخواست POST برای ویرایش ID {id} ===")
            
            # دریافت داده‌های فرم
            guide_name = request.form.get('guide_name', '').strip()
            guide_national_id = request.form.get('guide_national_id', '').strip()
            enter_date = request.form.get('enter_date', '').strip()
            exit_date = request.form.get('exit_date', '').strip()
            city = request.form.get('city', '').strip()
            hotel_name = request.form.get('hotel_name', '').strip()
            fixed_manager_name = request.form.get('fixed_manager_name', '').strip()
            
            # بررسی اجباری بودن فیلدها
            required_fields = {
                'guide_name': guide_name,
                'guide_national_id': guide_national_id,
                'enter_date': enter_date,
                'exit_date': exit_date,
                'city': city,
                'hotel_name': hotel_name,
                'fixed_manager_name': fixed_manager_name
            }
            
            for field_name, field_value in required_fields.items():
                if not field_value:
                    conn.close()
                    return f"خطا: فیلد {field_name} الزامی است و نمی‌تواند خالی باشد.", 400
            
            # به‌روزرسانی رکورد
            conn.execute('''
                UPDATE rahnama 
                SET guide_name = ?, guide_national_id = ?, enter_date = ?, exit_date = ?, 
                    city = ?, hotel_name = ?, fixed_manager_name = ? 
                WHERE id = ?
            ''', (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name, id))
            
            conn.commit()
            print(f"=== رکورد با ID {id} به‌روزرسانی شد ===")
            
            conn.close()
            return redirect(url_for('admin_index'))
        
        conn.close()
        return render_template('admin_form.html', assignment=assignment)
        
    except Exception as e:
        conn.close()
        print(f"خطا در ویرایش: {e}")
        return f"خطا در ویرایش: {str(e)}", 500

@app.route('/admin/delete/<int:id>', methods=('POST',))
def admin_delete(id):
    """حذف ماموریت"""
    try:
        conn = get_connection()
        
        # بررسی وجود رکورد
        existing = conn.execute('SELECT * FROM rahnama WHERE id = ?', (id,)).fetchone()
        if not existing:
            conn.close()
            abort(404)
        
        # حذف رکورد
        conn.execute('DELETE FROM rahnama WHERE id = ?', (id,))
        conn.commit()
        
        print(f"=== رکورد با ID {id} حذف شد ===")
        
        conn.close()
        return redirect(url_for('admin_index'))
        
    except Exception as e:
        print(f"خطا در حذف: {e}")
        return f"خطا در حذف: {str(e)}", 500

# --- مسیر اصلی بات (Webhook) ---
@app.route("/bot", methods=["POST"])
def bot_webhook():
    """پردازش پیام‌های بات"""
    try:
        data = request.json
        if "message" in data:
            message = data.get("message", {})
            text = message.get("text", "").strip()
            chat_id = message.get("chat", {}).get("id")
            
            if not chat_id:
                return jsonify({"status": "error", "message": "chat_id not found"})

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

                # تبدیل تاریخ شمسی به میلادی
                shamsi_parts = list(map(int, exit_date_str.split('/')))
                if len(shamsi_parts) != 3:
                    raise ValueError("فرمت تاریخ نامعتبر است.")
                
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
            buttons = {
                "keyboard": [
                    [{"text": "❌ خیر، اطلاعات اشتباه است"}, {"text": "✅ بله، صحیح است"}]
                ], 
                "resize_keyboard": True, 
                "one_time_keyboard": True
            }
            return send_message(chat_id, reply, reply_markup=json.dumps(buttons))

        return jsonify({"status": "ok"})
        
    except Exception as e:
        print(f"Error in bot_webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# --- مسیر اصلی ---
@app.route('/')
def index():
    """صفحه اصلی"""
    return redirect(url_for('admin_index'))

# --- مسیر تست دیتابیس ---
@app.route('/test-db')
def test_db():
    """تست اتصال دیتابیس"""
    try:
        conn = get_connection()
        
        # تست ایجاد جدول
        conn.execute('''
            CREATE TABLE IF NOT EXISTS rahnama (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guide_name TEXT NOT NULL,
                guide_national_id TEXT NOT NULL,
                enter_date TEXT NOT NULL,
                exit_date TEXT NOT NULL,
                city TEXT NOT NULL,
                hotel_name TEXT NOT NULL,
                fixed_manager_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # تست نمایش جداول
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        
        # تست شمارش رکوردها
        count = conn.execute("SELECT COUNT(*) FROM rahnama").fetchone()[0]
        
        # تست نمایش چند رکورد اول
        records = conn.execute("SELECT * FROM rahnama ORDER BY id DESC LIMIT 5").fetchall()
        
        conn.close()
        
        result = {
            "status": "success",
            "tables": [dict(table) for table in tables],
            "total_records": count,
            "recent_records": [dict(record) for record in records]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    # ایجاد جدول در شروع برنامه
    init_database()
    
    print("=== شروع سرور Flask ===")
    print("پنل مدیریت: http://localhost:10000/admin")
    print("تست دیتابیس: http://localhost:10000/test-db")
    
    app.run(host="0.0.0.0", port=10000, debug=True)
