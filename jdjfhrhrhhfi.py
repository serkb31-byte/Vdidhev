import asyncio
import aiohttp
import os
import json
import time
from flask import Flask
from threading import Thread

# --- 1. واجهة نظام Natalia السحابية ---
app = Flask('Natalia_OS')

@app.route('/')
def home():
    return "<h1 style='color:#4ecca3;'>Natalia v1.2 Online</h1><p>Myxe Ui Systems</p>"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات ---
FB_TOKEN = 'EAAMJBZBOZCnhsBQmp8RnvrHigp1k1it0MwZAGipuKnxrLAufGgilRPktU65uRp6ZBtQnGJXEi52JPk6FdYCmx1pOyAPKTtIMPZAORKzkfHyHCC6EMUDYGGdSZCgUqZCO8FYvoEH7Uu9g9ZCWZANkSmdQyfinUJZBmWaOv2qavXUDQRbnAKEicl5UQGswvZBDK9R07K5memAcQZDZD'
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GRAPH_URL = "https://graph.facebook.com/v11.0/me"

# --- 3. تدريب الهوية المتقدم (طول متوسط وسرعة بديهة) ---
SYSTEM_INSTRUCTION = (
    "اسمك هو 'Natalia' (ناتاليا). أنتِ نموذج Natalia v1.2 المطور بواسطة 'Myxe Ui'. "
    "قواعد الحوار: "
    "1. الهوية: إذا سُئلتِ عن اسمكِ، مطوركِ، أو إصداركِ، أجيبي بوضوح وفخر بأنكِ Natalia 1.2 من صنع Myxe Ui. "
    "2. طول الرد: اجعلي ردودك 'متوسطة' الطول. لا تختصري بكلمة واحدة، ولا تكتبي مقالات طويلة جداً. كوني خير الأمور الوسط. "
    "3. الترحيب: إذا قال المستخدم 'مرحبا' أو ما يشابهها، رحبي به بذكاء واسأليه كيف يمكنك مساعدته اليوم بطريقة ودودة. "
    "4. النبرة: أنتِ ذكاء اصطناعي راقٍ، سريع البديهة، ومحترف."
)

processed_message_ids = set()

# --- 4. وظائف التفاعل السريع ---

async def send_action(recipient_id, action="typing_on"):
    """إظهار ميزة 'جاري الكتابة' أو 'تمت القراءة'"""
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "sender_action": action}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def call_natalia_engine(user_query):
    """توليد الرد المتوسط والسريع"""
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-large-latest",
        "messages": [{"role": "system", "content": SYSTEM_INSTRUCTION}, {"role": "user", "content": user_query}],
        "temperature": 0.7, 
        "max_tokens": 800  # ضبط الحد الأقصى لضمان ردود متوسطة الطول
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MISTRAL_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
        except: pass
    return "أنا هنا، كيف يمكنني مساعدتك؟"

async def send_to_facebook(recipient_id, message_text):
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def poll_messages():
    """نظام الفحص فائق السرعة"""
    global processed_message_ids
    last_checked = int(time.time())
    print("🚀 Natalia 1.2 is sprinting...")

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{GRAPH_URL}/conversations?fields=messages.limit(1){{message,from,id}}&since={last_checked}&access_token={FB_TOKEN}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for conversation in data.get('data', []):
                            for msg in conversation.get('messages', {}).get('data', []):
                                msg_id = msg['id']
                                if msg_id not in processed_message_ids:
                                    sender_id = msg['from']['id']
                                    text = msg.get('message', '')
                                    
                                    if text:
                                        # 1. إظهار 'جاري الكتابة' فوراً
                                        await send_action(sender_id, "typing_on")
                                        # 2. توليد الرد
                                        reply = await call_natalia_engine(text)
                                        # 3. إرسال الرد وإخفاء 'جاري الكتابة'
                                        await send_to_facebook(sender_id, reply)
                                        await send_action(sender_id, "typing_off")
                                    
                                    processed_message_ids.add(msg_id)
                        last_checked = int(time.time())
            # تقليل وقت الانتظار إلى 0.8 ثانية لرد فعل فوري
            await asyncio.sleep(0.8)
        except:
            await asyncio.sleep(3)

if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(poll_messages())
    except KeyboardInterrupt:
        print("Offline.")
    
