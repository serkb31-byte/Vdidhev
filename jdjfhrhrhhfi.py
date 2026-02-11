import requests
import json
import time
import asyncio
import aiohttp
import os
import random
from flask import Flask, request
from threading import Thread

app = Flask(__name__)

# --- الإعدادات ---
GROK_API_URL = "https://viscodev.x10.mx/GROK/api.php"
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQkrr1slTiEjL7mEVyoN4EfDM6ZAhRJ6GxDZBRTp0IdF8Mm7K4wJU2OYIYMA38dBNr64ZCazOTjwMNNZA0R58wpRD4Dlf8v0R8P65wJU6NzLtZCUNuCWZCfDN7rt4ZC004u112LKF7IqirLfP89dZCvJlfXOnuLTXepCX8eiRHBq0JiNXH5lMEMOhgkXSuwZDZD'
VERIFY_TOKEN = "hduhdg98" # كلمة السر التي طلبتها
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com/v19.0/me/messages'

processed_message_ids = set()
sem = asyncio.Semaphore(5) # حماية: معالجة 5 رسائل فقط في نفس الوقت

# --- Flask Routes ---

@app.route('/', methods=['GET'])
def verify():
    # التحقق من الويب هوك عند الإعداد في فيسبوك
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
            for messaging_event in entry.get("messaging", []):
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    message_text = messaging_event["message"].get("text")
                    message_id = messaging_event["message"].get("mid")
                    
                    if message_id not in processed_message_ids:
                        processed_message_ids.add(message_id)
                        # تشغيل المعالجة في الخلفية
                        asyncio.run_coroutine_threadsafe(
                            handle_message_wrapper(sender_id, message_text), 
                            loop
                        )
    return "EVENT_RECEIVED", 200

# --- منطق المعالجة والحماية ---

async def handle_message_wrapper(sender_id, text):
    async with sem:
        async with aiohttp.ClientSession() as session:
            await handle_message(session, sender_id, text)

async def handle_message(session, sender_id, message_text):
    if not message_text: return
    
    # تأخير بشري عشوائي (حماية من الحظر)
    await asyncio.sleep(random.uniform(2, 5))
    
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(session, sender_id, stop_typing))
    
    try:
        # جلب الرد من الذكاء الاصطناعي
        params = {'message': message_text}
        async with session.get(GROK_API_URL, params=params, timeout=30) as response:
            ai_data = await response.json() if response.status == 200 else {}
        
        stop_typing.set()
        await typing_task

        if ai_data.get('success'):
            res_text = ai_data.get('response', '')
            # تقسيم الرسائل الطويلة (حماية)
            parts = [res_text[i:i+1000] for i in range(0, len(res_text), 1000)]
            for part in parts:
                await asyncio.sleep(random.uniform(1, 2))
                payload = {"recipient": {"id": sender_id}, "message": {"text": part}}
                await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=payload)
    except Exception as e:
        print(f"Error: {e}")
        stop_typing.set()

async def keep_typing(session, recipient_id, stop_event):
    while not stop_event.is_set():
        payload = {"recipient": {"id": recipient_id}, "sender_action": "typing_on"}
        await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=payload)
        await asyncio.sleep(4)

# --- تشغيل السيرفر ---

def run_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    t = Thread(target=run_loop, args=(loop,))
    t.start()
    
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
