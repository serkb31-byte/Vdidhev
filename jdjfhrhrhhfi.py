import requests
import json
import time
import asyncio
import aiohttp
import os
import random
from flask import Flask
from threading import Thread

# --- إعداد Flask لـ Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and protected with the new Token!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- الإعدادات الأساسية ---
GROK_API_URL = "https://viscodev.x10.mx/GROK/api.php"
# تم وضع التوكن الجديد هنا
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQiK9MsZAMoZCgKB0qzwOdqD1lSHips2iuOQ5K4evAMj9EWLKaPeREZB354bXSeyxZCZAj5oTSNZBMwIZCMryYSaaw9mRyP78PJ3WoDG8qLZAbifQZBsdXdxEzYoe2ZCnkaubcU59iPMpMp8ZCw8vtBpHkqiu0l9RXsSEu1aYuuZACzA73avQRNcVZAAOZA91wlcwZDZD'
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com/v19.0/me/messages'

processed_message_ids = set()
running = True

# --- الدوال المساعدة للحماية ---

def split_message(text, limit=1000):
    """تقسيم الرسائل الطويلة لتقليل مخاطر الحظر"""
    return [text[i:i+limit] for i in range(0, len(text), limit)]

async def keep_typing(session, recipient_id, stop_event):
    """محاكاة سلوك بشري في الكتابة"""
    while not stop_event.is_set():
        data = {"recipient": {"id": recipient_id}, "sender_action": "typing_on"}
        try:
            await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)
        except: pass
        await asyncio.sleep(random.uniform(3, 5))

async def process_with_grok(session, text):
    try:
        params = {'message': text}
        async with session.get(GROK_API_URL, params=params, timeout=40) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"AI Error: {e}")
    return {'success': False}

def is_image_url(url):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    return any(str(url).lower().endswith(ext) for ext in image_extensions)

# --- دوال الإرسال المحمية ---

async def send_facebook_message(session, recipient_id, message_text):
    parts = split_message(message_text)
    for part in parts:
        # تأخير عشوائي بين الأجزاء لكسر النمط الآلي
        await asyncio.sleep(random.uniform(1.2, 2.8))
        data = {"recipient": {"id": recipient_id}, "message": {"text": part}}
        async with session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data) as response:
            if response.status != 200:
                print(f"Error sending: {await response.text()}")

async def send_facebook_image(session, recipient_id, image_url):
    data = {
        "recipient": {"id": recipient_id},
        "message": {"attachment": {"type": "image", "payload": {"url": image_url, "is_reusable": True}}}
    }
    await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)

# --- منطق معالجة الرسائل ---

async def handle_message(session, sender_id, message_text):
    if not message_text: return
    
    # تأخير قبل البدء بالرد لمحاكاة التفكير البشري
    await asyncio.sleep(random.uniform(1, 4))
    
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(session, sender_id, stop_typing))
    
    try:
        ai_response = await process_with_grok(session, message_text)
        
        stop_typing.set()
        await typing_task
        
        if ai_response.get('success'):
            response_text = ai_response.get('response', '...')
            if is_image_url(response_text):
                await send_facebook_image(session, sender_id, response_text)
            else:
                await send_facebook_message(session, sender_id, response_text)
        else:
            await send_facebook_message(session, sender_id, "⚠️ نعتذر، هناك ضغط حالياً. حاول لاحقاً.")
    except Exception as e:
        stop_typing.set()
        print(f"Handling Error: {e}")

async def poll_facebook_messages():
    global running, processed_message_ids
    last_checked = int(time.time()) - 30
    
    # تحديد عدد المحادثات المتزامنة (حماية قصوى)
    sem = asyncio.Semaphore(3) 

    async with aiohttp.ClientSession() as session:
        print("Bot is running with NEW TOKEN and Anti-Ban protection...")
        while running:
            try:
                conv_url = f"https://graph.facebook.com/v19.0/me/conversations"
                params = {
                    "fields": "messages.limit(5){message,from,id}",
                    "since": last_checked,
                    "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
                }
                async with session.get(conv_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        for conversation in data.get('data', []):
                            for msg in conversation.get('messages', {}).get('data', []):
                                if msg['id'] not in processed_message_ids:
                                    sender_id = msg['from']['id']
                                    text = msg.get('message')
                                    if text:
                                        async with sem:
                                            asyncio.create_task(handle_message(session, sender_id, text))
                                        processed_message_ids.add(msg['id'])
                        
                        last_checked = int(time.time())
                
                # فحص كل 5-8 ثوانٍ لتقليل الضغط على السيرفر
                await asyncio.sleep(random.uniform(5, 8))
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(15)

if __name__ == "__main__":
    web_thread = Thread(target=run_flask)
    web_thread.daemon = True
    web_thread.start()
    
    try:
        asyncio.run(poll_facebook_messages())
    except KeyboardInterrupt:
        running = False
