import telebot
from flask import Flask, request
import sqlite3
from datetime import datetime

API_TOKEN = 'توکن_ربات_تو_اینجا_بگذار'
bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

DB_PATH = "atabat.db"  # فایل دیتابیس SQLite شما

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# نگه داشتن حالت هر کاربر (مثلا منتظر کد ملی، منتظر تایید و ...)
user_states = {}

WELCOME_TEXT = """
سلام!  
هدف این ربات، ارزشیابی مدیران ثابت توسط مدیران راهنماست.  
لطفا ابتدا کد ملی خود را وارد کنید:
"""

def check_can_evaluate(departure_date_str, today=None):
    # بررسی اینکه تاریخ امروز >= تاریخ خروج از شهر باشد تا اجازه ارزیابی بدهد
    if today is None:
        today = datetime.now().date()
    try:
        departure_date = datetime.strptime(departure_date_str, "%Y-%m-%d").date()
        return today >= departure_date
    except Exception as e:
        return False

@app.route('/' + API_TOKEN, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return '', 200

@app.route('/')
def index():
    return "ربات فعال است.", 200

@bot.message_handler(commands=['start'])
def start_message(message):
    user_states[message.chat.id] = "waiting_for_national_code"
    bot.send_message(message.chat.id, WELCOME_TEXT)

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_national_code")
def process_national_code(message):
    national_code = message.text.strip()
    # اعتبارسنجی ساده کد ملی: حداقل 8 رقم باشد (شما می توانید دقیق‌تر کنید)
    if not national_code.isdigit() or len(national_code) < 8:
        bot.send_message(message.chat.id, "کد ملی نامعتبر است. لطفا مجدداً وارد کنید.")
        return

    conn = get_db_connection()
    cur = conn.cursor()
    # کوئری دریافت آخرین اعزام مدیر راهنما با این کد ملی
    cur.execute("""
        SELECT mrm.name AS manager_name, mrm.national_code AS manager_ncode,
               at.departure_date, at.city, at.hotel, fixedm.name AS fixed_manager_name
        FROM manager_rahna mrm
        JOIN assignments at ON mrm.national_code = at.manager_ncode
        JOIN manager_sabet fixedm ON fixedm.national_code = at.fixed_manager_ncode
        WHERE mrm.national_code = ?
        ORDER BY at.departure_date DESC
        LIMIT 1
    """, (national_code,))
    row = cur.fetchone()
    conn.close()

    if not row:
        bot.send_message(message.chat.id, "اطلاعات شما یافت نشد. لطفا کد ملی صحیح وارد کنید یا با مدیر سیستم تماس بگیرید.")
        return

    # بررسی امکان ارزیابی بر اساس تاریخ خروج (ما از departure_date استفاده کردیم، اگر خروج دارید می تونید اصلاح کنید)
    can_evaluate = check_can_evaluate(row["departure_date"])

    if not can_evaluate:
        bot.send_message(message.chat.id, f"جناب آقای {row['manager_name']} عزیز، هنوز امکان ارزشیابی وجود ندارد. لطفا بعد از پایان اقامت اقدام کنید.")
        return

    user_states[message.chat.id] = "waiting_for_confirmation"
    # پیام خوش آمد + اطلاعات هتل و مدیر ثابت + دکمه تایید
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton("تایید اطلاعات درست است", callback_data="confirm_yes"))
    keyboard.add(telebot.types.InlineKeyboardButton("اطلاعات اشتباه است", callback_data="confirm_no"))

    msg = (f"جناب آقای {row['manager_name']}،\n"
           f"لطفا ارزشیابی مدیر ثابت هتل {row['hotel']}، جناب آقای {row['fixed_manager_name']} را با دقت تکمیل نمایید.\n"
           f"آیا اطلاعات فوق درست است؟")
    bot.send_message(message.chat.id, msg, reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "confirm_yes":
        bot.answer_callback_query(call.id, "شما تایید کردید.")
        bot.send_message(call.message.chat.id, "خوب، حالا می‌توانید ارزشیابی را شروع کنید (این قسمت را شما کامل می‌کنید).")
        # اینجا می‌توانید ادامه کد ارزیابی را بنویسید و user_states را به حالت بعدی ببرید
        user_states[call.message.chat.id] = "evaluating"
    elif call.data == "confirm_no":
        bot.answer_callback_query(call.id, "شما اطلاعات را اشتباه اعلام کردید.")
        bot.send_message(call.message.chat.id, "لطفا نام هتل صحیح را وارد نمایید:")
        user_states[call.message.chat.id] = "waiting_for_correct_hotel"

@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "waiting_for_correct_hotel")
def get_correct_hotel(message):
    correct_hotel = message.text.strip()
    # اینجا می‌توانید ذخیره تغییر هتل یا اعلام به سیستم اصلی را اضافه کنید
    bot.send_message(message.chat.id, f"ممنون، هتل به {correct_hotel} تغییر کرد. اکنون می‌توانید ارزشیابی را شروع کنید.")
    user_states[message.chat.id] = "evaluating"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
