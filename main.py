from flask import Flask, request, jsonify, render_template, redirect, url_for, abort
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import jdatetime
import datetime
import os

app = Flask(__name__)

# اتصال به دیتابیس PostgreSQL از طریق متغیر محیطی
DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rahnama (
            id SERIAL PRIMARY KEY,
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
    cursor.close()
    conn.close()


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


@app.route("/admin/add", methods=("GET", "POST"))
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


@app.route("/bot", methods=["POST"])
def bot_webhook():
    try:
        data = request.json
        if "message" in data:
            message = data.get("message", {})
            text = message.get("text", "").strip()
            chat_id = message.get("chat", {}).get("id")
            if not chat_id:
                return jsonify({"status": "error", "message": "chat_id not found"})
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rahnama WHERE guide_national_id = %s ORDER BY enter_date DESC LIMIT 1", (text,))
            rahnama_row = cursor.fetchone()
            cursor.close()
            conn.close()
            if not rahnama_row:
                return jsonify({"message": "کد ملی یافت نشد."})
            return jsonify(rahnama_row)
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/")
def index():
    return redirect(url_for("admin_index"))


if __name__ == "__main__":
    init_database()
    app.run(host="0.0.0.0", port=10000, debug=True)
