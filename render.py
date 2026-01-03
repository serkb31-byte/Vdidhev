import asyncio
import aiohttp
import pickle
import os
from flask import Flask, request
from threading import Thread

# --- 1. إعداد خادم الويب (للربط مع ميتا للمطورين) ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>Bot is Online!</h1><p>Status: Live and waiting for Facebook Webhooks.</p>"

@app.route('/', methods=['GET'])
def verify():
    # هذا هو الجزء الذي يطلبه ميتا للمطورين للتحقق من الرابط
    # تم ضبط رمز التحقق (Verify Token) إلى 444666 بناءً على طلبك
    verify_token = "444666"
    
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == verify_token:
        print("✅ Webhook Verified Successfully!")
        return challenge
    return "Verification Failed", 403

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات الأساسية للبوت ---
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQeZCf8Fjatgj3BbtrZA8siV3yAnckdqFo8ssedvKm1AZAQHQ8iXVkEqlWMZBt9Qi5EjOoOnMJw4TDGjlE1N8RrT82DAa3dGY0j4spSk3fmOxdt5jATjwqFGrABm7tRJN2JmfjzkIGlYJtXmMmTzWdrGacCv5cs5SkCciNR6ZAMGKEW4ZC2kHQQjUwQiwZDZD'
PAGE_ID = "615585802125461" 
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"

# كلمة سر التفعيل التي طلبتها
SYSTEM_PASSWORD = "abc12" 

DATA_FILE = "universal_core_memory.pkl"
TEXT_MODEL = "mistral-large-latest"

SYSTEM_INSTRUCTION = (
    "أنت مساعد ذكي مطورك هو 'Myxe Ui'. "
    "قاعدة الإجابة: كن مختصراً وموجزاً جداً في ردودك."
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

# --- 3. نظام المعالجة والإرسال ---
async def call_mistral_expanded(messages):
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": TEXT_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}] + messages,
        "temperature": 0.5,
        "max_tokens": 1000
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
    print(f"🔥 المحرك يعمل بكلمة سر التفعيل: {SYSTEM_PASSWORD}")
    while True:
        try:
            # هنا يوضع كود فحص الرسائل الأصلي
            await asyncio.sleep(2) 
        except Exception as e:
            await asyncio.sleep(5)

if __name__ == "__main__":
    keep_alive() # تشغيل خادم الويب في الخلفية للربط مع ميتا
    try:
        asyncio.run(core_engine_loop()) # تشغيل محرك البوت
    except KeyboardInterrupt:
        save_engine_data()
    
