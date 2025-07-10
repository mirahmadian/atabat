from flask import Flask, request, jsonify
import sqlite3
import json # برای دکمه ها
import jdatetime # برای کار با تاریخ شمسی
from datetime import datetime # برای گرفتن تاریخ فعلی

app = Flask(__name__)

DB_PATH = "atabat_sample.db" # یا "atabat.db" اگر از آن استفاده می کنید
# دیکشنری برای ذخیره کاربران احراز هویت شده و وضعیت آنها
# ساختار کلی: {chat_id: {"national_id": "...", "full_name": "...", "state": "...", ...}}
authenticated_users = {}

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

    # مدیریت دستور /logout
    if text == "/logout":
        if chat_id in authenticated_users:
            del authenticated_users[chat_id]
            reply = "شما با موفقیت از حساب خود خارج شدید."
        else:
            reply = "شما هنوز احراز هویت نکرده‌اید."
        return send_message(chat_id, reply)

    # بررسی اینکه آیا کاربر قبلا احراز هویت شده است
    if chat_id in authenticated_users:
        user_data = authenticated_users[chat_id]
        # اینجا منطق مربوط به مراحل بعدی (پس از احراز هویت) قرار خواهد گرفت
        # که در مرحله "پردازش پاسخ کاربر در مورد هتل" تکمیل خواهد شد.
        if user_data["state"] == "awaiting_hotel_confirmation":
            # این بخش مربوط به سناریوی قبلی بود، فعلا آن را ساده نگه می داریم
            # و در مراحل بعدی طبق سناریوی جدید تکمیل می کنیم.
            # اگر کاربر لاگین است و دستوری غیر از دستورات شناخته شده می فرستد،
            # می توانیم وضعیت فعلی او را یادآوری کنیم یا راهنمایی کنیم.
            # فعلا فرض می کنیم کاربر مسیر را طبق دکمه ها و راهنمایی ها دنبال می کند.
            pass # ادامه می دهیم تا ببینیم متن ورودی با کدام شرط جدید مطابقت دارد


    if text == "/start":
        # اگر کاربر قبلا اطلاعاتی در authenticated_users داشته، پاک می کنیم تا فرآیند از نو شروع شود
        if chat_id in authenticated_users:
            del authenticated_users[chat_id]
            
        reply = (
            "سلام! به سامانه ارزشیابی مدیران ثابت عتبات خوش آمدید.\n"
            "هدف این سامانه، دریافت نظرات شما مدیران محترم راهنما درباره عملکرد مدیران ثابت هتل‌ها در شهرهای زیارتی است.\n\n"
            "لطفاً برای شروع، کد ملی خود را وارد نمایید:"
        )
        # حذف هرگونه کیبورد قبلی
        return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))

    # سایر منطق ها (احراز هویت، انتخاب شهر و ...) در ادامه اضافه خواهند شد.
    # این بخش فعلا برای این است که ربات به پیام های دیگر پاسخی داشته باشد.
    # در مراحل بعدی این بخش با منطق اصلی جایگزین یا تکمیل می شود.
    
    # اگر کاربر هنوز احراز هویت نشده و متنی غیر از دستورات بالا فرستاده،
    # آن را به عنوان تلاش برای ورود کد ملی در نظر می گیریم.
    if chat_id not in authenticated_users:
        # این بخش مربوط به احراز هویت با کد ملی خواهد بود (مرحله ۲ طرح)
        # فعلا یک پاسخ موقت می دهیم
        # TODO: پیاده سازی احراز هویت با کد ملی
        pass # به ادامه کد می رود تا توسط بخش احراز هویت پردازش شود


    # پاسخ پیش‌فرض اگر هیچ‌کدام از شرایط بالا برقرار نبود
    # (این بخش معمولاً نباید اجرا شود اگر منطق به درستی پیاده‌سازی شده باشد)
    # فعلا یک پیام موقت برای ورودی های دیگر
    if chat_id not in authenticated_users and text not in ["/start", "/logout"]:
        # اینجا باید منطق احراز هویت کد ملی بیاید
        # این در مرحله بعدی تکمیل می شود
        pass # به بخش احراز هویت می رود

    # اگر کاربر احراز هویت شده، باید وضعیت او را بررسی و اقدام متناسب را انجام دهیم.
    # این در مراحل بعدی (انتخاب شهر و ...) تکمیل می شود.
    elif chat_id in authenticated_users:
        # TODO: مدیریت وضعیت های مختلف کاربر احراز هویت شده
        user_state = authenticated_users[chat_id].get("state")
        if user_state == "awaiting_city_selection":
            # TODO: پردازش انتخاب شهر
            pass
        elif user_state == "awaiting_hotel_manager_confirmation":
            # TODO: پردازش تایید هتل و مدیر
            pass
        # ... سایر وضعیت ها

    # اگر هیچ شرطی بررسی نشد، یک پیام عمومی می دهیم یا هیچ کاری نمی کنیم
    # این return jsonify باید در انتهای تابع و پس از همه if/elif ها باشد
    # اگر هیچ کدام از return های قبلی اجرا نشده باشند.
    # اما چون در مراحل بعدی return های بیشتری اضافه می شود، این بخش ممکن است تغییر کند.
    
    # این بخش باید با دقت بیشتری مدیریت شود تا همیشه یک پاسخ JSON معتبر برگردانده شود.
    # فعلا برای جلوگیری از خطا، اگر هیچ مسیری منجر به send_message نشود، یک پاسخ خالی برمیگردانیم.
    # این باید در تکمیل منطق بهبود یابد.
    # return jsonify({"status": "unhandled_message"}) # این خط را موقتا کامنت می کنیم

    # این بخش مربوط به زمانی است که کاربر کد ملی را وارد می کند (خارج از /start)
    # و هنوز احراز هویت نشده است.
    if chat_id not in authenticated_users and text not in ['/start', '/logout']:
        # ورودی کاربر به عنوان کد ملی در نظر گرفته می شود
        national_id_input = text.strip()

        # TODO: اینجا می توان یک اعتبارسنجی اولیه برای فرمت کد ملی اضافه کرد (مثلا تعداد ارقام)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT national_id, full_name FROM rahnama WHERE national_id = ?", (national_id_input,))
        row = cursor.fetchone()
        conn.close()

        if row:
            # کاربر با کد ملی معتبر پیدا شد
            authenticated_users[chat_id] = {
                "national_id": row["national_id"],
                "full_name": row["full_name"],
                "state": "awaiting_city_selection" # وضعیت بعدی: انتظار برای انتخاب شهر
            }
            # پیام موفقیت آمیز بودن احراز هویت و رفتن به مرحله انتخاب شهر
            # این پیام در مرحله بعدی تکمیل می شود (با دکمه های شهر)
            reply = (
                f"✅ جناب آقای/سرکار خانم {row['full_name']}، هویت شما با موفقیت تایید شد.\n"
                "لطفاً شهری که قصد ارزشیابی مدیر ثابت آن را دارید انتخاب کنید:"
            )
            city_buttons = [
                [{"text": "کربلا"}, {"text": "نجف"}]
            ]
            return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": city_buttons, "resize_keyboard": True, "one_time_keyboard": True}))
        else:
            # کد ملی در سیستم یافت نشد
            reply = "❌ کد ملی وارد شده در سیستم یافت نشد. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
            return send_message(chat_id, reply)

    # اگر کاربر احراز هویت شده باشد، وضعیت او بررسی و اقدام متناسب انجام می شود
    elif chat_id in authenticated_users:
        user_data = authenticated_users[chat_id]
        current_state = user_data.get("state")
        text_input = text.strip()

        if current_state == "awaiting_city_selection":
            if text_input in ["کربلا", "نجف"]:
                user_data["selected_city"] = text_input
                
                # --- شروع منطق بررسی تاریخ و واکشی اطلاعات آخرین اعزام ---
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT enter_date, exit_date, hotel_name, fixed_manager_name 
                    FROM rahnama 
                    WHERE national_id = ? AND city = ? 
                    ORDER BY exit_date DESC 
                    LIMIT 1
                """, (user_data["national_id"], user_data["selected_city"]))
                last_trip = cursor.fetchone()
                conn.close()

                if not last_trip:
                    reply = f"متاسفانه سابقه‌ای از اعزام شما به شهر {user_data['selected_city']} در سیستم یافت نشد."
                    if chat_id in authenticated_users: del authenticated_users[chat_id] 
                    return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))

                user_data["last_trip_enter_date_str"] = last_trip["enter_date"]
                user_data["last_trip_exit_date_str"] = last_trip["exit_date"]
                user_data["last_trip_hotel_name"] = last_trip["hotel_name"]
                user_data["last_trip_fixed_manager_name"] = last_trip["fixed_manager_name"]

                try:
                    exit_date_str_to_parse = last_trip["exit_date"]
                    # تلاش برای تطبیق با فرمت های رایج تاریخ شمسی
                    parsed_date = None
                    for fmt in ("%Y/%m/%d", "%Y-%m-%d", "%Y%m%d"):
                        try:
                            parsed_date = jdatetime.datetime.strptime(exit_date_str_to_parse, fmt).date()
                            break
                        except ValueError:
                            continue
                    if parsed_date is None:
                        raise ValueError(f"Date format for '{exit_date_str_to_parse}' not recognized.")
                    
                    exit_date_jd = parsed_date
                    today_jd = jdatetime.date.today()

                    if not (today_jd >= exit_date_jd and today_jd <= exit_date_jd + jdatetime.timedelta(days=30)):
                        reply = (
                            f"امکان ارزشیابی برای شما در حال حاضر فعال نیست. "
                            f"ارزشیابی از روز آخر اقامت شما در شهر {user_data['selected_city']} "
                            f"(تاریخ {last_trip['exit_date']}) تا ۳۰ روز پس از آن امکان‌پذیر است."
                        )
                        if chat_id in authenticated_users: del authenticated_users[chat_id]
                        return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))
                    
                    user_data["state"] = "awaiting_hotel_manager_confirmation"
                    reply = (
                        f"شرایط تاریخی برای ارزشیابی شما در شهر {user_data['selected_city']} (اعزام با تاریخ خروج {last_trip['exit_date']}) تایید شد.\n"
                        f"هتل ثبت شده برای این اعزام: {last_trip['hotel_name']}\n"
                        f"مدیر ثابت ثبت شده: {last_trip['fixed_manager_name']}\n\n"
                        "آیا این اطلاعات صحیح است؟"
                    )
                    confirmation_buttons = [
                        [{"text": "بله، اطلاعات صحیح است"}], [{"text": "خیر، اطلاعات صحیح نیست"}]
                    ]
                    return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": confirmation_buttons, "resize_keyboard": True, "one_time_keyboard": True}))

                except ValueError as e:
                    print(f"Error parsing date: {e}. Date string was: {last_trip['exit_date']}")
                    reply = "خطایی در پردازش تاریخ اعزام شما (فرمت نامعتبر) رخ داده است. لطفاً با پشتیبانی تماس بگیرید."
                    if chat_id in authenticated_users: del authenticated_users[chat_id]
                    return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))
                # --- پایان منطق بررسی تاریخ ---
            else:
                # ورودی نامعتبر برای انتخاب شهر
                reply = "لطفاً یکی از شهرهای کربلا یا نجف را با استفاده از دکمه‌های زیر انتخاب کنید:"
                city_buttons = [
                    [{"text": "کربلا"}, {"text": "نجف"}]
                ]
                return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": city_buttons, "resize_keyboard": True, "one_time_keyboard": True}))
        
        elif current_state == "awaiting_hotel_manager_confirmation":
            if text_input == "بله، اطلاعات صحیح است":
                user_data["state"] = "ready_for_evaluation"
                # اطلاعات هتل و مدیر ثابت تایید شده، می توان آنها را برای مراحل بعدی نگه داشت
                # user_data["confirmed_hotel"] = user_data["last_trip_hotel_name"]
                # user_data["confirmed_manager"] = user_data["last_trip_fixed_manager_name"]
                reply = (
                    "اطلاعات هتل و مدیر ثابت تایید شد.\n"
                    "در حال حاضر بخش ارزشیابی در دست ساخت است. از همکاری شما متشکریم!" 
                    # TODO: در آینده به بخش ارزشیابی هدایت شود.
                )
                # اینجا می توان کاربر را لاگ اوت کرد یا منتظر دستور بعدی گذاشت
                # فعلا لاگ اوت می کنیم تا فرآیند کامل تلقی شود
                if chat_id in authenticated_users: del authenticated_users[chat_id]
                return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))

            elif text_input == "خیر، اطلاعات صحیح نیست":
                user_data["state"] = "information_mismatch"
                reply = (
                    "از اطلاع‌رسانی شما متشکریم. مورد عدم تطابق اطلاعات هتل/مدیر ثابت برای بررسی به مدیر سیستم ارجاع داده شد.\n"
                    "لطفاً برای پیگیری با پشتیبانی تماس بگیرید."
                )
                if chat_id in authenticated_users: del authenticated_users[chat_id] # خروج کاربر
                return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))
            else:
                # ورودی نامعتبر
                reply = "لطفاً با استفاده از دکمه‌های ارائه شده پاسخ دهید:"
                confirmation_buttons = [
                    [{"text": "بله، اطلاعات صحیح است"}], [{"text": "خیر، اطلاعات صحیح نیست"}]
                ]
                return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": confirmation_buttons, "resize_keyboard": True, "one_time_keyboard": True}))

    return jsonify({"status": "ok", "message": "No specific action taken for this input based on current logic."})


def send_message(chat_id, text, reply_markup=None):
    import requests
    TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX" # توکن شما
    BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
        
    response = requests.post(BALE_API_URL, json=payload)
    return jsonify(response.json())

if __name__ == "__main__":
    # اطمینان از اینکه ستون hotel_city در دیتابیس وجود دارد
    # این یک مثال است و باید با ساختار واقعی دیتابیس شما تطابق داده شود
    # conn = get_connection()
    # cursor = conn.cursor()
    # try:
    #     cursor.execute("ALTER TABLE rahnama ADD COLUMN hotel_city TEXT")
    #     conn.commit()
    #     print("Column hotel_city added to rahnama table.")
    # except sqlite3.OperationalError as e:
    #     if "duplicate column name" in str(e):
    #         print("Column hotel_city already exists in rahnama table.")
    #     else:
    #         raise e
    # finally:
    #     conn.close()
    app.run(host="0.0.0.0", port=10000)
