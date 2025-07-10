from flask import Flask, request, render_template, redirect, flash
import sqlite3
import jdatetime
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = "your-secret-key"  # برای flash message

DB_PATH = "atabat.db"  # مسیر فایل دیتابیس

# توکن بات بله (تغییر نده)
TOKEN = "6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX"
BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

# مسیر نمایش و پردازش فرم
@app.route("/add_rahnama", methods=["GET", "POST"])
def add_rahnama():
    if request.method == "POST":
        try:
            # دریافت داده‌ها از فرم
            guide_name = request.form["guide_name"]
            guide_national_id = request.form["guide_national_id"]
            enter_date_shamsi = request.form["enter_date"]
            exit_date_shamsi = request.form["exit_date"]
            city = request.form["city"]
            hotel_name = request.form["hotel_name"]
            fixed_manager_name = request.form["fixed_manager_name"]
            fixed_manager_national_id = request.form["fixed_manager_national_id"]

            # تبدیل تاریخ شمسی به میلادی
            enter_date = jdatetime.datetime.strptime(enter_date_shamsi, "%Y/%m/%d").togregorian().strftime("%Y-%m-%d")
            exit_date = jdatetime.datetime.strptime(exit_date_shamsi, "%Y/%m/%d").togregorian().strftime("%Y-%m-%d")

            # ذخیره در دیتابیس
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
                INSERT INTO evaluations (
                    guide_national_id, guide_name, city, hotel_name,
                    fixed_manager_name, fixed_manager_national_id,
                    enter_date, exit_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                guide_national_id, guide_name, city, hotel_name,
                fixed_manager_name, fixed_manager_national_id,
                enter_date, exit_date
            ))
            conn.commit()
            conn.close()
            flash("ثبت با موفقیت انجام شد.", "success")
            return redirect("/add_rahnama")
        except Exception as e:
            print("خطا:", e)
            flash(f"خطا در ثبت: {e}", "error")
            return redirect("/add_rahnama")

    return render_template("add_rahnama.html")

# صفحه اصلی ساده
@app.route("/")
def index():
    return "✅ بات در حال اجراست. برای ثبت مدیر راهنما به مسیر /add_rahnama بروید."

if __name__ == "__main__":
    app.run(debug=True)
