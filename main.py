from flask import Flask, request
import requests
import os

app = Flask(__name__)

TOKEN = 'توکن بات بله را اینجا قرار بده'
BALE_API_URL = f"https://tapi.bale.ai/bot{TOKEN}/sendMessage"

@app.route('/', methods=['GET'])
def home():
    return 'ربات بله روی لیارا فعال است.'

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
