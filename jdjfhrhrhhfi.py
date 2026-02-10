import requests
import json
import time
import asyncio
import aiohttp
import os
from flask import Flask
from threading import Thread

# --- إعداد Flask لـ Render ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- الإعدادات الأساسية ---
GROK_API_URL = "https://viscodev.x10.mx/GROK/api.php"
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQiK9MsZAMoZCgKB0qzwOdqD1lSHips2iuOQ5K4evAMj9EWLKaPeREZB354bXSeyxZCZAj5oTSNZBMwIZCMryYSaaw9mRyP78PJ3WoDG8qLZAbifQZBsdXdxEzYoe2ZCnkaubcU59iPMpMp8ZCw8vtBpHkqiu0l9RXsSEu1aYuuZACzA73avQRNcVZAAOZA91wlcwZDZD'
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com/v11.0/me/messages'

processed_message_ids = set()
running = True

# --- الدوال المساعدة ---

def split_message(text, limit=2000):
    """تقسيم النص الطويل إلى أجزاء لا تتجاوز الحد المسموح به في فيسبوك"""
    return [text[i:i+limit] for i in range(0, len(text), limit)]

async def keep_typing(session, recipient_id, stop_event):
    """وظيفة لإبقاء حالة 'جاري الكتابة' نشطة حتى انتهاء الطلب"""
    while not stop_event.is_set():
        data = {"recipient": {"id": recipient_id}, "sender_action": "typing_on"}
        await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)
        await asyncio.sleep(4) # فيسبوك يخفي الحالة بعد 5-6 ثوانٍ، لذا نجددها كل 4 ثوانٍ

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

# --- دوال فيسبوك ---

async def send_facebook_message(session, recipient_id, message_text):
    """إرسال النص مع دعم التقسيم التلقائي (Split)"""
    parts = split_message(message_text)
    for part in parts:
        data = {"recipient": {"id": recipient_id}, "message": {"text": part}}
        async with session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data) as response:
            if response.status != 200:
                print(f"Error sending part: {await response.text()}")

async def send_facebook_image(session, recipient_id, image_url):
    data = {
        "recipient": {"id": recipient_id},
        "message": {"attachment": {"type": "image", "payload": {"url": image_url, "is_reusable": True}}}
    }
    await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)

# --- معالجة المنطق ---

async def handle_message(session, sender_id, message_text):
    if not message_text: return
    
    # 1. تفعيل حالة الكتابة المستمرة
    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(keep_typing(session, sender_id, stop_typing))
    
    try:
        # 2. جلب الرد من GROK
        ai_response = await process_with_grok(session, message_text)
        
        # 3. إيقاف حالة الكتابة فور استلام الرد
        stop_typing.set()
        await typing_task
        
        if ai_response.get('success'):
            response_text = ai_response.get('response', 'Empty response')
            if is_image_url(response_text):
                await send_facebook_image(session, sender_id, response_text)
            else:
                # إرسال النص فوراً مع خاصية Split
                await send_facebook_message(session, sender_id, response_text)
        else:
            await send_facebook_message(session, sender_id, "❌ عذراً، واجهت مشكلة في معالجة طلبك.")
    except Exception as e:
        stop_typing.set()
        print(f"Handling Error: {e}")

async def poll_facebook_messages():
    global running, processed_message_ids
    last_checked = int(time.time()) - 60
    
    async with aiohttp.ClientSession() as session:
        print("Polling with persistent typing and split_message enabled...")
        while running:
            try:
                conv_url = f"https://graph.facebook.com/v11.0/me/conversations"
                params = {
                    "fields": "messages.limit(5){message,from,id}",
                    "since": last_checked,
                    "access_token": FACEBOOK_PAGE_ACCESS_TOKEN
                }
                async with session.get(conv_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        tasks = []
                        for conversation in data.get('data', []):
                            for msg in conversation.get('messages', {}).get('data', []):
                                if msg['id'] not in processed_message_ids:
                                    sender_id = msg['from']['id']
                                    text = msg.get('message')
                                    if text:
                                        # تشغيل كل رسالة في مهمة منفصلة لضمان السرعة
                                        asyncio.create_task(handle_message(session, sender_id, text))
                                        processed_message_ids.add(msg['id'])
                        
                        last_checked = int(time.time())
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Polling error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    web_thread = Thread(target=run_flask)
    web_thread.daemon = True
    web_thread.start()
    
    try:
        asyncio.run(poll_facebook_messages())
    except KeyboardInterrupt:
        running = False
