import asyncio
import aiohttp
import os
import json
import time
from flask import Flask
from threading import Thread

# --- 1. واجهة النظام ---
app = Flask('Natalia_OS')

@app.route('/')
def home():
    return "<h1 style='color:#38bdf8;'>Natalia v1.2 is Ready</h1><p>Myxe Ui Systems</p>"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات والتوكن ---
FB_TOKEN = 'EAAMJBZBOZCnhsBQmp8RnvrHigp1k1it0MwZAGipuKnxrLAufGgilRPktU65uRp6ZBtQnGJXEi52JPk6FdYCmx1pOyAPKTtIMPZAORKzkfHyHCC6EMUDYGGdSZCgUqZCO8FYvoEH7Uu9g9ZCWZANkSmdQyfinUJZBmWaOv2qavXUDQRbnAKEicl5UQGswvZBDK9R07K5memAcQZDZD'
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GRAPH_URL = "https://graph.facebook.com/v11.0/me"

user_memory = {}
processed_message_ids = set()

# --- 3. التدريب الذكي المطور ---
SYSTEM_INSTRUCTION = (
    "أنت 'Natalia' (ناتاليا) الإصدار 1.2. "
    "قواعد الحوار: "
    "1. الحوار العام: تحدث بالمذكر كمساعد ذكي 👨‍💻. "
    "2. التعريف بالذات: عند السؤال حصراً عن اسمك أو من صنعك، أجب بالمؤنث (أنا ناتاليا من Myxe Ui) 🌸. "
    "3. رسالة الترحيب الأولى: إذا كانت هذه أول مرة يتواصل فيها المستخدم، رحب به بحرارة باستخدام الإيموجي "
    "وقل له: 'أهلاً بك! أنا ناتاليا، يسعدني جداً تواصلك معي اليوم ✨.. كيف يمكنني مساعدتك؟ 🤝' "
    "يُمنع ذكر اسم المطور (Myxe Ui) أو مصطلح 'محرك سيادي' في هذه الرسالة الترحيبية الأولى نهائياً. "
    "4. الأسلوب: ردود متوسطة، ذكية، ومليئة بالحيوية والإيموجي المناسب 🚀."
)

# --- 4. محركات التواصل ---

async def send_typing_action(recipient_id, action="typing_on"):
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "sender_action": action}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def call_natalia_engine(sender_id, user_query):
    is_new_user = False
    if sender_id not in user_memory:
        user_memory[sender_id] = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        is_new_user = True
    
    # تنبيه داخلي للنموذج بخصوص أول رسالة
    input_text = f"[FIRST_TIME_CONTACT]: {user_query}" if is_new_user else user_query
    
    user_memory[sender_id].append({"role": "user", "content": input_text})
    
    if len(user_memory[sender_id]) > 11:
        user_memory[sender_id] = [user_memory[sender_id][0]] + user_memory[sender_id][-10:]

    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-large-latest",
        "messages": user_memory[sender_id],
        "temperature": 0.75,
        "max_tokens": 1000
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MISTRAL_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    reply = data['choices'][0]['message']['content']
                    user_memory[sender_id].append({"role": "assistant", "content": reply})
                    return reply
        except: pass
    return "أهلاً بك! ناتاليا معك، كيف أقدر أساعدك اليوم؟ ✨"

async def send_to_facebook(recipient_id, message_text):
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def poll_messages():
    global processed_message_ids
    last_checked = int(time.time())
    print("🚀 Natalia 1.2 is LIVE with Emoji Greeting...")

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{GRAPH_URL}/conversations?fields=messages.limit(1){{message,from,id}}&since={last_checked}&access_token={FB_TOKEN}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for conversation in data.get('data', []):
                            for msg in conversation.get('messages', {}).get('data', []):
                                if msg['id'] not in processed_message_ids:
                                    sender_id = msg['from']['id']
                                    text = msg.get('message', '')
                                    
                                    if text:
                                        await send_typing_action(sender_id, "typing_on")
                                        reply = await call_natalia_engine(sender_id, text)
                                        await send_to_facebook(sender_id, reply)
                                        await send_typing_action(sender_id, "typing_off")
                                    
                                    processed_message_ids.add(msg['id'])
                        last_checked = int(time.time())
            await asyncio.sleep(0.7)
        except:
            await asyncio.sleep(4)

if __name__ == "__main__":
    keep_alive()
    try:
        asyncio.run(poll_messages())
    except KeyboardInterrupt:
        print("Shutdown.")
    
