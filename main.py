from flask import Flask, request, jsonify, render_template
import sqlite3

app = Flask(__name__)

DB_NAME = "atabat.db"

# تابع کمکی برای اتصال به دیتابیس و اجرای کوئری
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# صفحه اصلی ربات (مثلا برای تست)
@app.route("/", methods=["GET"])
def home():
    return "ربات بله روی رندر فعال است."

# دریافت پیام از بات بله
@app.route("/bot", methods=["POST"])
def bot():
    data = request.json

    # نمونه ساده: دریافت پیام متنی از کاربر و پاسخ دادن
    message = data.get("message", {})
    text = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if text == "/start":
        reply = ("سلام! 👋\n"
                 "به بات ارزشیابی مدیران ثابت خوش آمدید.\n"
                 "لطفاً کد ملی خود را وارد نمایید:")
        send_message(chat_id, reply)
        return jsonify({"status": "ok"})

    # اینجا می تونید منطق بات رو اضافه کنید...

    send_message(chat_id, "پیغام شما دریافت شد: " + text)
    return jsonify({"status": "ok"})

# تابع ارسال پیام به بات بله
def send_message(chat_id, text):
    import requests
    TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
    BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    requests.post(BALE_API_URL, json=payload)

# مسیر فرم اضافه کردن مدیر راهنما
@app.route("/add_rahnama", methods=["GET", "POST"])
def add_rahnama():
    if request.method == "POST":
        codemeli = request.form["codemeli"]
        name = request.form["name"]
        family = request.form["family"]
        date_azmoon = request.form["date_azmoon"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO rahnama (codemeli, name, family, date_azmoon) VALUES (?, ?, ?, ?)",
            (codemeli, name, family, date_azmoon))
        conn.commit()
        conn.close()

        return "✅ اطلاعات با موفقیت ثبت شد."

    return render_template("add_rahnama.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
