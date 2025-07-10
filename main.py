from flask import Flask, request, render_template
import sqlite3

app = Flask(__name__)

DB_PATH = "data.db"  # آدرس فایل دیتابیس شما

# مسیر نمایش و ثبت فرم مدیر راهنما
@app.route("/add_rahnama", methods=["GET", "POST"])
def add_rahnama():
    if request.method == "POST":
        try:
            codemeli = request.form["codemeli"]
            name = request.form["name"]
            family = request.form["family"]
            date_start = request.form["date_start"]
            date_end = request.form["date_end"]
            city = request.form["city"]
            hotel = request.form["hotel"]
            manager_name = request.form["manager_name"]

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO rahnama (codemeli, name, family, date_start, date_end, city, hotel, manager_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (codemeli, name, family, date_start, date_end, city, hotel, manager_name),
            )

            conn.commit()
            conn.close()

            return "✅ اطلاعات با موفقیت ثبت شد."

        except Exception as e:
            return f"خطا در ثبت: {e}"

    return render_template("add_rahnama.html")
