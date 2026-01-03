import asyncio
import aiohttp
import pickle
import os
import time
from flask import Flask
from threading import Thread

# --- 1. خادم الويب لمنع "النوم" واستقبال النبضات ---
app = Flask('')

@app.route('/')
def home():
    # هذه الصفحة ستظهر عند زيارة رابط البوت أو من قبل Cron-job
    return "<h1>Bot Status: Active</h1><p>The engine is running in Polling mode.</p>"

def run():
    # تشغيل الخادم على المنفذ 8080 المتوافق مع Render
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    # تشغيل الخادم في خيط منفصل (Thread) لكي لا يعطل محرك البوت
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات والبيانات الأصلية ---
FACEBOOK_PAGE_ACCESS_TOKEN = 'EAAMJBZBOZCnhsBQTnNVcyOXlXFvsCgedVN5zc50ReXNZCEHnuTZAADUDDeqMD5i3NSwTH1uuMl1H9oju2zx5J0fM8NCeuz106ZCOFx9zCAVgA7fChj3F7ze1oEEkPM4Vn6lZA2hvlbVFS4ghyMOi3Epu91nDl8DeEaDF4kfoPE84clfubyZAonihEKGS6cn0ZBVOXvKi9gZDZD'
PAGE_ID = "615585802125461" 
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"
SYSTEM_PASSWORD = "12ASM88CV" # كلمة السر الأصلية لتفعيل المحرك
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
    
    if sender_id not in storage["auth"]:
        if text.strip() == SYSTEM_PASSWORD:
            storage["auth"].add(sender_id)
            save_engine_data()
            await delivery_system(sender_id, "✅ تم تفعيل المحرك بنجاح.")
        else:
            await delivery_system(sender_id, "🔒 المحرك مغلق. أدخل مفتاح الوصول:")
        return

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
    print("🔥 المحرك يعمل بنظام السحب المستمر (Polling Mode)...")
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
            await asyncio.sleep(1) # فحص الرسائل كل ثانية
        except Exception as e:
            print(f"Error in loop: {e}")
            await asyncio.sleep(2)

# --- 4. نقطة الانطلاق المزدوجة ---
if __name__ == "__main__":
    keep_alive() # تشغيل خادم الويب في الخلفية
    try:
        asyncio.run(core_engine_loop()) # تشغيل محرك البوت الأساسي
    except KeyboardInterrupt:
        save_engine_data()
