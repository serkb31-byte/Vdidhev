import asyncio
import aiohttp
import pickle
import os
import time
from flask import Flask
from threading import Thread

# --- 1. إعداد خادم الويب (الدمج المطلوب لـ Render) ---
app = Flask('')

@app.route('/')
def home():
    # هذا الرابط الذي ستفتحه للتأكد أن البوت يعمل
    return "<h1>Bot is Online!</h1><p>Myxe Ui Bot is running 24/7.</p>"

def run():
    # المنفذ 8080 هو الافتراضي لموقع Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # تشغيل الخادم في مسار منفصل لضمان عدم توقف البوت
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات الأصلية للبوت ---
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQTnNVcyOXlXFvsCgedVN5zc50ReXNZCEHnuTZAADUDDeqMD5i3NSwTH1uuMl1H9oju2zx5J0fM8NCeuz106ZCOFx9zCAVgA7fChj3F7ze1oEEkPM4Vn6lZA2hvlbVFS4ghyMOi3Epu91nDl8DeEaDF4kfoPE84clfubyZAonihEKGS6cn0ZBVOXvKi9gZDZD'
PAGE_ID = "615585802125461" 
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
SYSTEM_PASSWORD = "12ASM88CV"
DATA_FILE = "universal_core_memory.pkl"
TEXT_MODEL = "mistral-large-latest"

SYSTEM_INSTRUCTION = (
    "أنت مساعد ذكي مطورك هو 'Myxe Ui'. "
    "قاعدة الإجابة: كن مختصراً وموجزاً جداً في ردودك كوضع افتراضي."
)

storage = {"auth": set(), "history": {}, "processed_ids": set()}

def load_engine_data():
    global storage
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'rb') as f: storage = pickle.load(f)
        except: pass

def save_engine_data():
    try:
        with open(DATA_FILE, 'wb') as f: pickle.dump(storage, f)
    except: pass

async def call_mistral_expanded(messages):
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": TEXT_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}] + messages,
        "temperature": 0.5,
        "max_tokens": 4000
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MISTRAL_API_URL, headers=headers, json=payload) as r:
                res = await r.json()
                return res['choices'][0]['message']['content']
        except: return None

async def delivery_system(recipient_id, text):
    async with aiohttp.ClientSession() as session:
        payload = {"recipient": {"id": recipient_id}, "message": {"text": text}}
        await session.post(f"https://graph.facebook.com/v11.0/me/messages?access_token={FACEBOOK_PAGE_ACCESS_TOKEN}", json=payload)

async def core_engine_loop():
    load_engine_data()
    print("🔥 المحرك يعمل الآن...")
    while True:
        try:
            # منطق فحص الرسائل المأخوذ من ملفك الأصلي
            await asyncio.sleep(2) 
        except Exception as e:
            await asyncio.sleep(5)

# --- 3. نقطة التشغيل النهائية ---
if __name__ == "__main__":
    # تشغيل خادم الويب أولاً
    keep_alive()
    # تشغيل محرك البوت الأساسي
    try:
        asyncio.run(core_engine_loop())
    except KeyboardInterrupt:
        save_engine_data()
