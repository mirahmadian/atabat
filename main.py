from flask import Flask, request, jsonify
import sqlite3
import json # برای دکمه ها

app = Flask(__name__)

DB_PATH = "atabat_sample.db"
# دیکشنری برای ذخیره کاربران احراز هویت شده
# ساختار: {chat_id: {"full_name": "...", "hotel_name": "...", "city": "...", "state": "awaiting_hotel_confirmation"}}
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
            # اگر کاربر قبلا احراز هویت شده و منتظر پاسخ به سوال هتل است
            # و پاسخی غیر از بله یا خیر داده، دوباره سوال را با دکمه می پرسیم
            if text.lower() not in ["بله", "خیر"]:
                reply = (
                    f"جناب آقای {user_data['full_name']}، شما قبلاً احراز هویت شده‌اید.\n"
                    f"هتل ثبت شده برای شما: {user_data['hotel_name']} ({user_data['city']}).\n"
                    "آیا در همین هتل اقامت داشته‌اید؟"
                )
                buttons = [
                    [{"text": "بله"}, {"text": "خیر"}]
                ]
                return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": buttons, "resize_keyboard": True, "one_time_keyboard": True}))
            # اگر بله یا خیر بود، به بخش پردازش پاسخ می رویم (در ادامه کد)
            pass


    if text == "/start":
        if chat_id in authenticated_users:
            # اگر کاربر قبلا با /start احراز هویت کرده و هنوز لاگ اوت نکرده
            user_data = authenticated_users[chat_id]
            reply = (
                f"جناب آقای {user_data['full_name']}، شما قبلاً احراز هویت شده‌اید.\n"
                f"هتل ثبت شده برای شما: {user_data['hotel_name']} ({user_data['city']}).\n"
                "آیا در همین هتل اقامت داشته‌اید؟"
            )
            buttons = [
                [{"text": "بله"}, {"text": "خیر"}]
            ]
            return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": buttons, "resize_keyboard": True, "one_time_keyboard": True}))
        else:
            reply = (
                "سلام! 👋\n"
                "به بات ارزشیابی مدیران ثابت خوش آمدید.\n"
                "لطفاً کد ملی خود را وارد نمایید:"
            )
            return send_message(chat_id, reply)

    # اگر کاربر احراز هویت نشده و متن ورودی /start یا /logout نیست، آن را به عنوان کد ملی در نظر می‌گیریم
    if chat_id not in authenticated_users:
        conn = get_connection()
        cursor = conn.cursor()
        # استفاده از نام ستون های صحیح: national_id, full_name, city
        cursor.execute("SELECT full_name, hotel_name, city FROM rahnama WHERE national_id = ?", (text,))
        row = cursor.fetchone()
        conn.close()

        if row is None:
            reply = "❌ کد ملی شما در سیستم یافت نشد. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
            return send_message(chat_id, reply)

        # ذخیره اطلاعات کاربر احراز هویت شده
        authenticated_users[chat_id] = {
            "full_name": row["full_name"],
            "hotel_name": row["hotel_name"],
            "city": row["city"],
            "state": "awaiting_hotel_confirmation" # وضعیت اولیه پس از احراز هویت
        }

        reply = (
            f"✅ جناب آقای {row['full_name']}، هویت شما با موفقیت تایید شد.\n"
            f"هتل ثبت شده برای شما: {row['hotel_name']} ({row['city']}).\n"
            "آیا در همین هتل اقامت داشته‌اید؟"
        )
        buttons = [
            [{"text": "بله"}, {"text": "خیر"}]
        ]
        return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": buttons, "resize_keyboard": True, "one_time_keyboard": True}))

    # اگر کاربر احراز هویت شده و در وضعیت awaiting_hotel_confirmation است
    # و متن ورودی "بله" یا "خیر" است:
    if chat_id in authenticated_users and \
       authenticated_users[chat_id]["state"] == "awaiting_hotel_confirmation" and \
       text.lower() in ["بله", "خیر"]:
        
        user_data = authenticated_users[chat_id]
        
        if text.lower() == "بله":
            user_data["state"] = "hotel_confirmed"
            # در اینجا می توانیم اطلاعات هتل تایید شده را هم ذخیره کنیم اگر لازم باشد
            # user_data["confirmed_hotel_name"] = user_data["hotel_name"] 
            # user_data["confirmed_hotel_city"] = user_data["city"]
            reply = (
                f"اقامت شما در هتل {user_data['hotel_name']} ({user_data['city']}) تایید شد.\n"
                "در حال حاضر، مرحله بعدی (ارزشیابی) هنوز پیاده‌سازی نشده است." # TODO: پیام مناسب بعدی
            )
            # حذف دکمه های قبلی
            return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))

        elif text.lower() == "خیر":
            user_data["state"] = "awaiting_alternative_hotel"
            current_city = user_data["city"]
            
            conn = get_connection()
            cursor = conn.cursor()
            # دریافت لیست هتل های دیگر در همان شهر
            # فرض می کنیم همه هتل ها در جدول rahnama و ستون hotel_name هستند
            # و می خواهیم هتل فعلی کاربر از لیست حذف شود
            cursor.execute("SELECT DISTINCT hotel_name FROM rahnama WHERE city = ? AND hotel_name != ?", (current_city, user_data["hotel_name"]))
            hotels_in_city_rows = cursor.fetchall()
            conn.close()

            if not hotels_in_city_rows:
                reply = (
                    f"متاسفانه هتل دیگری در شهر {current_city} در سیستم ثبت نشده است.\n"
                    "لطفاً با پشتیبانی تماس بگیرید."
                )
                # بازگرداندن وضعیت به حالت اولیه یا یک وضعیت خطا
                # authenticated_users[chat_id]["state"] = "error_no_other_hotels"
                # یا حذف کاربر از سیستم لاگین شده چون کار بیشتری نمی تواند انجام دهد
                del authenticated_users[chat_id]
                return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))

            hotels_list_text = "لطفاً نام هتلی که در آن اقامت داشته‌اید را از لیست زیر انتخاب و تایپ کنید:\n"
            # ایجاد دکمه برای هر هتل (روش پیشنهادی)
            hotel_buttons = []
            for hotel_row in hotels_in_city_rows:
                hotel_buttons.append([{"text": hotel_row["hotel_name"]}])
            
            if not hotel_buttons: # اگر لیست خالی بود (مثلا فقط هتل خودش در شهر بود)
                 reply = (
                    f"به نظر می‌رسد به جز هتل {user_data['hotel_name']}، هتل دیگری برای شهر {current_city} در سیستم ثبت نشده است.\n"
                    "اگر در هتل دیگری اقامت داشته اید، لطفاً نام آن را وارد کنید، در غیر این صورت برای بررسی با پشتیبانی تماس بگیرید."
                )
                 # اینجا هم دکمه های بله/خیر را حذف می کنیم چون کاربر "خیر" را انتخاب کرده
                 return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))


            # reply = hotels_list_text # اگر میخواستیم فقط لیست متنی بدهیم
            # در اینجا از دکمه های کیبورد برای انتخاب هتل استفاده می کنیم
            # این دکمه ها جایگزین دکمه های بله و خیر می شوند
            reply = "لطفاً از لیست زیر، هتلی که در آن اقامت داشته اید را انتخاب کنید:"
            return send_message(chat_id, reply, reply_markup=json.dumps({"keyboard": hotel_buttons, "resize_keyboard": True, "one_time_keyboard": True}))

    # اگر کاربر احراز هویت شده و در وضعیت awaiting_alternative_hotel است
    # و نام یک هتل را وارد کرده است
    elif chat_id in authenticated_users and \
         authenticated_users[chat_id]["state"] == "awaiting_alternative_hotel":
        
        user_data = authenticated_users[chat_id]
        selected_hotel_name = text # نام هتلی که کاربر وارد کرده

        # بررسی می کنیم آیا هتل وارد شده در لیست هتل های شهرش بوده یا خیر (اختیاری اما بهتر است)
        # این کار نیازمند آن است که لیست هتل ها را جایی ذخیره کرده باشیم یا دوباره کوئری بزنیم
        # فعلا فرض می کنیم کاربر نام را صحیح وارد می کند.
        
        user_data["state"] = "alternative_hotel_selected"
        user_data["confirmed_hotel_name"] = selected_hotel_name
        # شهر همان شهر قبلی است
        # user_data["confirmed_hotel_city"] = user_data["city"]
        
        reply = (
            f"اقامت شما در هتل {selected_hotel_name} ({user_data['city']}) تایید شد.\n"
            "در حال حاضر، مرحله بعدی (ارزشیابی) هنوز پیاده‌سازی نشده است." # TODO: پیام مناسب بعدی
        )
        return send_message(chat_id, reply, reply_markup=json.dumps({"remove_keyboard": True}))


    # پاسخ پیش‌فرض اگر هیچ‌کدام از شرایط بالا برقرار نبود
    # (این بخش معمولاً نباید اجرا شود اگر منطق به درستی پیاده‌سازی شده باشد)
    # reply = "دستور شما نامفهوم است. لطفاً از دستور /start برای شروع استفاده کنید."
    # return send_message(chat_id, reply)
    return jsonify({"status": "ok", "message": "No action taken for this input yet"})


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
