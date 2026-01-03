import asyncio
import aiohttp
import pickle
import os
import time
from flask import Flask
from threading import Thread

# --- 1. إعداد "الباب" (خادم الويب) ---
app = Flask('')

@app.route('/')
def home():
    # هذا هو "الباب" الذي سيطرقه Cron-job. 
    # الرد نصي فقط ولا يرسل أي أوامر لفيسبوك، مما يمنع طلب كلمة السر.
    return "<h1>Bot Status: Active</h1><p>The engine is running and waiting for messages...</p>"

@app.route('/health')
def health():
    return "OK", 200

def run():
    # Render يمرر المنفذ عبر متغير البيئة PORT تلقائياً
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    # تشغيل الخادم في خلفية الكود لضمان عدم توقف السحب (Polling)
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات والبيانات (بدون كلمة سر) ---
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQTnNVcyOXlXFvsCgedVN5zc50ReXNZCEHnuTZAADUDDeqMD5i3NSwTH1uuMl1H9oju2zx5J0fM8NCeuz106ZCOFx9zCAVgA7fChj3F7ze1oEEkPM4Vn6lZA2hvlbVFS4ghyMOi3Epu91nDl8DeEaDF4kfoPE84clfubyZAonihEKGS6cn0ZBVOXvKi9gZDZD'
PAGE_ID = "615585802125461" 
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
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

# --- 3. أنظمة المعالجة والإرسال ---
async def typing_on_loop(recipient_id, stop_event):
    async with aiohttp.ClientSession() as session:
        while not stop_event.is_set():
            payload = {"recipient": {"id": recipient_id}, "sender_action": "typing_on"}
            await session.post(f"https://graph.facebook.com/v11.0/me/messages?access_token={FACEBOOK_PAGE_ACCESS_TOKEN}", json=payload)
            await asyncio.sleep(2.5)

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
        chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
        for chunk in chunks:
            payload = {"recipient": {"id": recipient_id}, "message": {"text": chunk}}
            await session.post(f"https://graph.facebook.com/v11.0/me/messages?access_token={FACEBOOK_PAGE_ACCESS_TOKEN}", json=payload)
            await asyncio.sleep(0.5)

async def handle_user_logic(sender_id, text):
    if str(sender_id) == str(PAGE_ID) or not text: return
    
    # تم إلغاء طلب كلمة السر: تفعيل المستخدم تلقائياً
    if sender_id not in storage["auth"]:
        storage["auth"].add(sender_id)
        save_engine_data()

    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(typing_on_loop(sender_id, stop_typing))
    
    try:
        history = storage["history"].get(sender_id, [])
        history.append({"role": "user", "content": text})
        response = await call_mistral_expanded(history[-15:])
        if response:
            await delivery_system(sender_id, response)
            history.append({"role": "assistant", "content": response})
            storage["history"][sender_id] = history
            save_engine_data()
    finally:
        stop_typing.set()
        await typing_task

async def core_engine_loop():
    load_engine_data()
    print("🔥 المحرك يعمل الآن بدون كلمة مرور مع دعم بقاء الاتصال...")
    while True:
        try:
            url = f"https://graph.facebook.com/v11.0/me/conversations?fields=messages.limit(5){{message,from,id}}&access_token={FACEBOOK_PAGE_ACCESS_TOKEN}"
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as r:
                    data = await r.json()
                    for conv in data.get('data', []):
                        for m in conv.get('messages', {}).get('data', []):
                            m_id, sender_id = m['id'], m['from']['id']
                            if sender_id != PAGE_ID and m_id not in storage.get("processed_ids", set()):
                                if "processed_ids" not in storage: storage["processed_ids"] = set()
                                storage["processed_ids"].add(m_id)
                                asyncio.create_task(handle_user_logic(sender_id, m.get('message', '')))
            await asyncio.sleep(1)
        except Exception as e:
            await asyncio.sleep(2)

# --- 4. التشغيل النهائي ---
if __name__ == "__main__":
    keep_alive() # فتح "الباب" لـ Cron-job ولنظام Render
    try:
        asyncio.run(core_engine_loop()) # تشغيل محرك البوت
    except KeyboardInterrupt:
        save_engine_data()
        
