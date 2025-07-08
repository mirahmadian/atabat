from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'سلام از عتبات! برنامه شما روی لیارا اجرا شده است.'

if __name__ == '__main__':
    app.run()
