from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import requests

app = Flask(__name__)

# توکن بات بله خودت را اینجا بگذار
BOT_API_TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"

# متغیر محیطی DATABASE_URL باید در محیط رندر تنظیم شده باشد
DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def send_message(chat_id, text):
    url = "https://api.bale.ai/bot/v1/message/send/text"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BOT_API_TOKEN}"
    }
    data = {
        "chat_id": chat_id,
        "text": text
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

@app.route("/admin")
def admin_index():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM rahnama ORDER BY id DESC")
        assignments = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template("admin_index.html", assignments=assignments)
    except Exception as e:
        return f"خطا در نمایش لیست: {e}", 500

@app.route("/admin/add", methods=["GET", "POST"])
def admin_add():
    if request.method == "POST":
        try:
            form_data = {k: request.form.get(k, "").strip() for k in [
                "guide_name", "guide_national_id", "enter_date", "exit_date",
                "city", "hotel_name", "fixed_manager_name"]}
            for key, value in form_data.items():
                if not value:
                    return f"خطا: فیلد {key} الزامی است و نمی‌تواند خالی باشد.", 400
            if not form_data['guide_national_id'].isdigit() or len(form_data['guide_national_id']) != 10:
                return "خطا: کد ملی باید 10 رقم باشد.", 400
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO rahnama (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', tuple(form_data.values()))
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("admin_index"))
        except Exception as e:
            return f"خطا در ذخیره داده‌ها: {str(e)}", 500
    return render_template("admin_form.html", assignment=None)

@app.route("/admin/edit/<int:id>", methods=["GET", "POST"])
def admin_edit(id):
    conn = get_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        guide_name = request.form.get("guide_name", "").strip()
        guide_national_id = request.form.get("guide_national_id", "").strip()
        enter_date = request.form.get("enter_date", "").strip()
        exit_date = request.form.get("exit_date", "").strip()
        city = request.form.get("city", "").strip()
        hotel_name = request.form.get("hotel_name", "").strip()
        fixed_manager_name = request.form.get("fixed_manager_name", "").strip()

        cursor.execute('''
            UPDATE rahnama SET
                guide_name=%s,
                guide_national_id=%s,
                enter_date=%s,
                exit_date=%s,
                city=%s,
                hotel_name=%s,
                fixed_manager_name=%s
            WHERE id=%s
        ''', (guide_name, guide_national_id, enter_date, exit_date, city, hotel_name, fixed_manager_name, id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("admin_index"))
    else:
        cursor.execute("SELECT * FROM rahnama WHERE id=%s", (id,))
        assignment = cursor.fetchone()
        cursor.close()
        conn.close()
        if assignment is None:
            abort(404)
        return render_template("admin_form.html", assignment=assignment)

@app.route("/admin/delete/<int:id>", methods=["POST"])
def admin_delete(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM rahnama WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_index"))

@app.route("/bot", methods=["POST"])
def bot_webhook():
    try:
        data = request.json
        if not data:
            return jsonify({"status": "no data"})

        print("داده دریافتی از بله:", data)

        if "message" in data:
            message = data["message"]
            text = message.get("text", "").strip()
            chat_id = message.get("chat", {}).get("id")

            if not chat_id:
                return jsonify({"status": "error", "message": "chat_id not found"})

            if text == "/start":
                send_message(chat_id, "سلام! ربات شما آماده است. خوش آمدید!")
                return jsonify({"status": "ok", "message": "start handled"})

            # سایر دستورات یا پاسخ‌ها می‌توانند اینجا اضافه شوند

        return jsonify({"status": "ok", "echo": data})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/")
def index():
    return redirect(url_for("admin_index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
