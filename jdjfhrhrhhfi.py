import requests
import json
import time
import asyncio
import aiohttp
import os
from flask import Flask
from threading import Thread

# --- إعداد Flask لـ Render ---
# Render يتطلب وجود منفذ مفتوح لضمان استمرار الخدمة
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running!"

def run_flask():
    # Render يمرر المنفذ عبر متغير البيئة PORT
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- الإعدادات الأساسية ---
GROK_API_URL = "https://viscodev.x10.mx/GROK/api.php"
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQvcZBWBv21wV8hVeR9TRsxMr0ucCxwKHI3QAZBl6hZCIrhMZAxRISLhYEuNrvqLioSZCj0ZB7ZCry2ZCrLxxmfebCoXBbHiQedQZAoLqF4saZC0zN9ctlQMpH6grVVdh4jy8AjETOte44S7SfqII8juvjD1zgXcGcX5OGUo5OeQnCYeqx8DzJkFebT9CNfcAZDZD'
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com/v11.0/me/messages'

# إعدادات التخزين والمزامنة
processed_message_ids = set()
running = True

# --- الدوال المساعدة ---

async def process_with_grok(text):
    try:
        params = {'message': text}
        async with aiohttp.ClientSession() as session:
            async with session.get(GROK_API_URL, params=params, timeout=30) as response:
                if response.status == 200:
                    return await response.json()
        return {'success': False, 'error': f'Status: {response.status}'}
    except Exception as e:
        return {'success': False, 'error': str(e)}

def is_image_url(url):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    return any(str(url).lower().endswith(ext) for ext in image_extensions)

# --- دوال فيسبوك ---

async def send_typing_on(recipient_id):
    data = {"recipient": {"id": recipient_id}, "sender_action": "typing_on"}
    async with aiohttp.ClientSession() as session:
        await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)

async def send_facebook_message(recipient_id, message_text):
    data = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data) as response:
                if response.status != 200:
                    print(f"Error sending message: {await response.text()}")
        except Exception as e:
            print(f"Exception sending message: {e}")

async def send_facebook_image(recipient_id, image_url):
    data = {
        "recipient": {"id": recipient_id},
        "message": {"attachment": {"type": "image", "payload": {"url": image_url, "is_reusable": True}}}
    }
    async with aiohttp.ClientSession() as session:
        await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)

# --- معالجة المنطق ---

async def handle_message(sender_id, message_text):
    if not message_text: return
    print(f"Processing message from {sender_id}")
    await send_typing_on(sender_id)
    ai_response = await process_with_grok(message_text)
    
    if ai_response.get('success'):
        response_text = ai_response.get('response', 'Empty response')
        if is_image_url(response_text):
            await send_facebook_image(sender_id, response_text)
        else:
            await send_facebook_message(sender_id, response_text)
    else:
        await send_facebook_message(sender_id, "❌ حدث خطأ في النظام.")

async def poll_facebook_messages():
    global running, processed_message_ids
    last_checked = int(time.time()) - 60
    print("Polling started...")
    
    while running:
        try:
            async with aiohttp.ClientSession() as session:
                conv_url = f"https://graph.facebook.com/v11.0/me/conversations?fields=messages.limit(5){{message,from,id}}&since={last_checked}&access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
                async with session.get(conv_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for conversation in data.get('data', []):
                            if 'messages' in conversation:
                                for msg in conversation['messages']['data']:
                                    msg_id = msg['id']
                                    if msg_id not in processed_message_ids:
                                        sender_id = msg['from']['id']
                                        text = msg.get('message')
                                        if text:
                                            await handle_message(sender_id, text)
                                            processed_message_ids.add(msg_id)
                    last_checked = int(time.time())
            await asyncio.sleep(2)
        except Exception as e:
            print(f"Polling error: {e}")
            await asyncio.sleep(5)

# --- نقطة الانطلاق ---

def start_bot():
    asyncio.run(poll_facebook_messages())

if __name__ == "__main__":
    # 1. تشغيل خادم Flask في الخلفية
    web_thread = Thread(target=run_flask)
    web_thread.daemon = True
    web_thread.start()
    
    # 2. تشغيل البوت في الخيط الرئيسي
    try:
        start_bot()
    except KeyboardInterrupt:
        running = False
        print("Bot stopped.")
        
