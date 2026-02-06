import asyncio
import aiohttp
import os
import json
import time
import sqlite3
import random
from flask import Flask, render_template_string
from threading import Thread

# ==========================================
# 1) واجهة الويب المتطورة (Turbo UI)
# ==========================================
app = Flask('Neuro_Turbo_Core')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <title>Neuro 2.0 Turbo</title>
    <style>
        body { background: #020617; color: #38bdf8; font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; }
        .container { text-align: center; border: 1px solid #1e293b; padding: 40px; border-radius: 15px; background: #0f172a; box-shadow: 0 0 30px rgba(56, 189, 248, 0.2); }
        .status-light { display: inline-block; width: 12px; height: 12px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 10px #22c55e; margin-right: 10px; }
        h1 { font-size: 2.5rem; margin: 10px 0; color: #f87171; }
        .mode { color: #94a3b8; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="container">
        <div class="status-light"></div>
        <h1>NEURO 2.0 TURBO</h1>
        <div class="mode">Ultra-Low Latency Mode: ACTIVE</div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# ==========================================
# 2) نظام الذاكرة الأبدية
# ==========================================
def init_db():
    conn = sqlite3.connect('neuro_memory.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS memory (user_id TEXT PRIMARY KEY, history TEXT)''')
    conn.commit()
    conn.close()

def save_memory(user_id, history):
    conn = sqlite3.connect('neuro_memory.db')
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO memory VALUES (?, ?)", (user_id, json.dumps(history)))
    conn.commit()
    conn.close()

def load_memory(user_id):
    conn = sqlite3.connect('neuro_memory.db')
    c = conn.cursor()
    c.execute("SELECT history FROM memory WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    return json.loads(data[0]) if data else None

# ==========================================
# 3) الإعدادات
# ==========================================
FB_TOKEN = 'EAAMJBZBOZCnhsBQmt3Xg9C0Dk9bkXhj7ZCnVKNNn6CV3N4DRxGepfs1EY9uCYE0FzUW9PRXTj2cbq0JZBVDWIkPTHOqHNLc1WQ4dR5dExRhphzRDCHsxRbXOGLQfVn02yZCmvO2klnwnt792ZB8ZBpi4o1KvZBZBaeugXAogoc8YclWdiBcLQFOEtKsHk1EjBdXVnazWykwZDZD'
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GRAPH_URL = "https://graph.facebook.com/v14.0/me"

SYSTEM_INSTRUCTION = "أنت Neuro 2.0، ذكاء اصطناعي سيادي. ردودك دقيقة، سريعة، ومتزنة."

# ==========================================
# 4) محرك الاستجابة الفورية (Zero-Latency Engine)
# ==========================================

async def toggle_typing(session, recipient_id, state="typing_on"):
    """مؤشر الكتابة لزيادة الواقعية"""
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "sender_action": state}
    await session.post(url, json=payload)

async def send_to_facebook(session, recipient_id, text):
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    chunks = [text[i:i+1500] for i in range(0, len(text), 1500)]
    for chunk in chunks:
        payload = {"recipient": {"id": recipient_id}, "message": {"text": chunk}}
        async with session.post(url, json=payload) as resp:
            await resp.json()
        await asyncio.sleep(0.2)

async def process_message(session, sender_id, text):
    # تفعيل مؤشر الكتابة فوراً
    await toggle_typing(session, sender_id, "typing_on")
    
    history = load_memory(sender_id) or [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    history.append({"role": "user", "content": text})
    
    payload = {
        "model": "mistral-large-latest",
        "messages": history[-20:],
        "temperature": 0.2,
        "max_tokens": 2000
    }
    
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
    
    try:
        async with session.post(MISTRAL_URL, json=payload, headers=headers) as resp:
            data = await resp.json()
            if 'choices' in data:
                reply = data['choices'][0]['message']['content']
                history.append({"role": "assistant", "content": reply})
                save_memory(sender_id, history)
                
                # إرسال الرد وإطفاء مؤشر الكتابة
                await send_to_facebook(session, sender_id, reply)
                await toggle_typing(session, sender_id, "typing_off")
    except Exception as e:
        print(f"Engine Error: {e}")

# ==========================================
# 5) نظام الرصد المصلح (Fixed Polling)
# ==========================================

async def poll_messages():
    init_db()
    processed_message_ids = set()
    
    # استخدام سعة اتصال أكبر للسرعة
    connector = aiohttp.TCPConnector(limit=200)
    async with aiohttp.ClientSession(connector=connector) as session:
        print("⚡ Neuro 2.0 Turbo Active: Waiting for messages...")
        
        while True:
            try:
                # طلب آخر الرسائل بدون تأخير زمني في الاستعلام
                url = f"{GRAPH_URL}/conversations?fields=messages.limit(2){{message,from,id,created_time}}&access_token={FB_TOKEN}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        tasks = []
                        
                        for conv in data.get('data', []):
                            msgs = conv.get('messages', {}).get('data', [])
                            if not msgs: continue
                            
                            # معالجة أحدث رسالة فقط لضمان عدم حدوث إزاحة
                            latest_msg = msgs[0]
                            m_id = latest_msg['id']
                            
                            if m_id not in processed_message_ids:
                                sender_id = latest_msg['from']['id']
                                text = latest_msg.get('message', '')
                                if text:
                                    # إطلاق مهمة المعالجة في الخلفية فوراً دون انتظار
                                    tasks.append(asyncio.create_task(process_message(session, sender_id, text)))
                                processed_message_ids.add(m_id)
                        
                        # تنظيف ذاكرة المعرفات المجرى معالجتها دورياً
                        if len(processed_message_ids) > 1000:
                            processed_message_ids.clear()

                # فحص سريع جداً كل 0.2 ثانية للاستجابة اللحظية
                await asyncio.sleep(0.2)
            except Exception as e:
                print(f"Polling Alert: {e}")
                await asyncio.sleep(1)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    asyncio.run(poll_messages())
    
