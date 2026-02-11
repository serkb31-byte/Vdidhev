import requests
import json
import asyncio
import aiohttp
import os
import random
import re
from flask import Flask, request
from threading import Thread

app = Flask(__name__)

# --- الإعدادات ---
GROK_API_URL = "https://viscodev.x10.mx/GROK/api.php"
# التوكن الجديد الذي أرسلته
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQkrr1slTiEjL7mEVyoN4EfDM6ZAhRJ6GxDZBRTp0IdF8Mm7K4wJU2OYIYMA38dBNr64ZCazOTjwMNNZA0R58wpRD4Dlf8v0R8P65wJU6NzLtZCUNuCWZCfDN7rt4ZC004u112LKF7IqirLfP89dZCvJlfXOnuLTXepCX8eiRHBq0JiNXH5lMEMOhgkXSuwZDZD'
VERIFY_TOKEN = "hduhdg98"
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com/v19.0/me/messages'

processed_message_ids = set()
# تقليل التزامن لرسالة واحدة فقط في الوقت الحالي لضمان عدم لفت الانتباه
sem = asyncio.Semaphore(1) 

def safety_filter(text):
    """منع إرسال الروابط تماماً لأنها السبب الأول لحظر الحسابات الجديدة"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    return re.sub(url_pattern, '[رابط]', text)

@app.route('/', methods=['GET'])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Verification failed", 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for event in entry.get("messaging", []):
                if event.get("message") and not event["message"].get("is_echo"):
                    sender_id = event["sender"]["id"]
                    text = event["message"].get("text")
                    mid = event["message"].get("mid")
                    
                    if mid not in processed_message_ids:
                        processed_message_ids.add(mid)
                        asyncio.run_coroutine_threadsafe(handle_message_wrapper(sender_id, text), loop)
    return "EVENT_RECEIVED", 200

async def handle_message_wrapper(sender_id, text):
    async with sem:
        async with aiohttp.ClientSession() as session:
            # تأخير عشوائي طويل (محاكاة التفكير البشري)
            await asyncio.sleep(random.uniform(6, 12))
            await handle_message(session, sender_id, text)

async def handle_message(session, sender_id, message_text):
    if not message_text: return
    
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(session, sender_id, stop_typing))
    
    try:
        params = {'message': message_text}
        async with session.get(GROK_API_URL, params=params, timeout=30) as response:
            ai_data = await response.json() if response.status == 200 else {}
        
        stop_typing.set()
        await typing_task

        if ai_data.get('success'):
            raw_res = ai_data.get('response', '')
            # تطبيق فلتر الحماية
            clean_res = safety_filter(raw_res)
            
            # تقسيم الرسائل مع تأخير بين كل جزء
            parts = [clean_res[i:i+600] for i in range(0, len(clean_res), 600)]
            for part in parts:
                await asyncio.sleep(random.uniform(2, 5))
                payload = {"recipient": {"id": sender_id}, "message": {"text": part}}
                await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=payload)
    except Exception:
        stop_typing.set()

async def keep_typing(session, recipient_id, stop_event):
    while not stop_event.is_set():
        try:
            payload = {"recipient": {"id": recipient_id}, "sender_action": "typing_on"}
            await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=payload)
            await asyncio.sleep(random.uniform(3, 5))
        except: break

def run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    t = Thread(target=run_loop, args=(loop,))
    t.start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
    
