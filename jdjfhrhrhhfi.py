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
    return "High-Quality AI Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- الإعدادات الأساسية ---
GROK_API_URL = "https://viscodev.x10.mx/GROK/api.php"
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQvcZBWBv21wV8hVeR9TRsxMr0ucCxwKHI3QAZBl6hZCIrhMZAxRISLhYEuNrvqLioSZCj0ZB7ZCry2ZCrLxxmfebCoXBbHiQedQZAoLqF4saZC0zN9ctlQMpH6grVVdh4jy8AjETOte44S7SfqII8juvjD1zgXcGcX5OGUo5OeQnCYeqx8DzJkFebT9CNfcAZDZD'
FACEBOOK_GRAPH_API_URL = 'https://graph.facebook.com/v11.0/me/messages'

# إعدادات إنشاء الصور الفائقة
GETIMG_API_URL = "https://api.getimg.ai/v1/stable-diffusion-xl/text-to-image"
GETIMG_API_KEY = "key-3XbWkFO34FVCQUnJQ6A3qr702Eu7DDR1dqoJOyhMHqhruEhs22KUzR7w631ZFiA5OFZIba7i44qDQEMpKxzegOUm83vCfILb"

processed_message_ids = set()
running = True

# --- الدوال المساعدة لإنشاء الصور الفائقة ---

async def generate_images(session, user_prompt):
    """إنشاء صورة واقعية جداً بدقة احترافية"""
    headers = {
        'Authorization': f'Bearer {GETIMG_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    # إضافة محسنات الواقعية والدقة تلقائياً للمطلب
    enhanced_prompt = (
        f"{user_prompt}, photorealistic, ultra-detailed, 8k resolution, highly cinematic, "
        "masterpiece, realistic textures, raw photo, f/1.8, high sharp focus, 12k UHD, HDR"
    )
    
    negative_prompt = (
        "low resolution, blurry, distorted, cartoon, anime, drawing, painting, "
        "nude, naked, sex, porn, ugly, deformed hands, extra fingers, text, watermark"
    )
    
    data = {
        'model': 'realvis-xl-v4',
        'prompt': enhanced_prompt,
        'negative_prompt': negative_prompt,
        'response_format': 'url',
        'seed': int(time.time()),
        'steps': 40,  # زيادة عدد الخطوات لتحسين التفاصيل
        'guidance': 8.5,
        'height': 1024,
        'width': 1024
    }
    
    try:
        async with session.post(GETIMG_API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result.get('url')
            else:
                print(f"GetImg Error: {await response.text()}")
    except Exception as e:
        print(f"Image generation error: {e}")
    return None

# --- الدوال المساعدة لـ GROK ---

async def process_with_grok(session, text):
    try:
        params = {'message': text}
        async with session.get(GROK_API_URL, params=params, timeout=30) as response:
            if response.status == 200:
                return await response.json()
    except Exception as e:
        print(f"Grok API Error: {e}")
    return {'success': False}

def is_image_url(url):
    image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
    return any(str(url).lower().endswith(ext) for ext in image_extensions)

# --- دوال فيسبوك ---

async def send_fb_action(session, recipient_id, action):
    data = {"recipient": {"id": recipient_id}, "sender_action": action}
    await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)

async def send_facebook_message(session, recipient_id, message_text):
    data = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    async with session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data) as response:
        if response.status != 200:
            print(f"FB Error: {await response.text()}")

async def send_facebook_image(session, recipient_id, image_url):
    data = {
        "recipient": {"id": recipient_id},
        "message": {"attachment": {"type": "image", "payload": {"url": image_url, "is_reusable": True}}}
    }
    await session.post(FACEBOOK_GRAPH_API_URL, params={"access_token": FACEBOOK_PAGE_ACCESS_TOKEN}, json=data)

# --- معالجة المنطق ---

async def handle_message(session, sender_id, message_text):
    if not message_text: return
    
    await send_fb_action(session, sender_id, "typing_on")
    
    # كلمات مفتاحية لتفعيل رسم الصور
    image_keywords = ["ارسم", "صورة لـ", "تخيل", "انشئ صورة", "draw", "imagine", "create image", "رسم"]
    
    if any(keyword in message_text.lower() for keyword in image_keywords):
        await send_facebook_message(session, sender_id, "📸 جاري معالجة صورتك بدقة 8K الواقعية... انتظر قليلاً.")
        
        image_url = await generate_images(session, message_text)
        
        if image_url:
            await send_facebook_image(sender_id, image_url)
        else:
            await send_facebook_message(sender_id, "❌ عذراً، لم أتمكن من رسم الصورة حالياً. حاول مجدداً بوصف آخر.")
        return

    # الرد النصي عبر GROK
    ai_response = await process_with_grok(session, message_text)
    
    if ai_response.get('success'):
        response_text = ai_response.get('response', 'استجابة فارغة')
        if is_image_url(response_text):
            await send_facebook_image(sender_id, response_text)
        else:
            await send_facebook_message(sender_id, response_text)
    else:
        await send_facebook_message(sender_id, "⚠️ الخادم مشغول حالياً، يرجى المحاولة لاحقاً.")

async def poll_facebook_messages():
    global running, processed_message_ids
    last_checked = int(time.time()) - 60
    
    async with aiohttp.ClientSession() as session:
        print("Polling high-res bot started...")
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
                                msg_id = msg['id']
                                if msg_id not in processed_message_ids:
                                    sender_id = msg['from']['id']
                                    text = msg.get('message')
                                    if text:
                                        tasks.append(handle_message(session, sender_id, text))
                                        processed_message_ids.add(msg_id)
                        
                        if tasks:
                            await asyncio.gather(*tasks)
                        
                        last_checked = int(time.time())
                
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Loop Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    web_thread = Thread(target=run_flask)
    web_thread.daemon = True
    web_thread.start()
    
    try:
        asyncio.run(poll_facebook_messages())
    except KeyboardInterrupt:
        running = False
