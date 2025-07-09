from flask import Flask, request
import requests

app = Flask(__name__)

# توکن بات بله شما
TOKEN = '6616020:CAwP1U9uX7ibGLXM17Cb9BztVy97pZUUXnDWvIjX'
BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

@app.route('/', methods=['GET'])
def home():
    return 'ربات بله روی رندر فعال است.'

@app.route('/', methods=['POST'])
def webhook():
    data = request.json
    if 'message' in data and 'text' in data['message']:
        chat_id = data['message']['chat']['id']
        text = data['message']['text']
        reply = f"شما گفتید: {text}"

        requests.post(BALE_API_URL, json={
            'chat_id': chat_id,
            'text': reply
        })

    return 'ok'

# لازم نیست app.run در رندر باشه چون رندر خودش اجرا رو مدیریت می‌کند
