from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'سلام! برنامه Flask شما روی لیارا اجرا شد 🎉'

if __name__ == '__main__':
    app.run()
