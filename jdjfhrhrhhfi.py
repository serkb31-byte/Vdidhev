import asyncio
import aiohttp
import os
import json
import time
import sqlite3
from flask import Flask, render_template_string
from threading import Thread

# ==========================================
# 1) واجهة الويب المتطورة (Cyber-Future UI)
# ==========================================
app = Flask('Neuro_Infinity_Core')

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <title>Neuro 2.0 Infinity Core</title>
    <style>
        body { background: radial-gradient(circle, #0f172a 0%, #020617 100%); color: #38bdf8; font-family: 'Segoe UI', sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0; overflow: hidden; }
        .container { text-align: center; border: 1px solid #1e293b; padding: 50px; border-radius: 20px; background: rgba(15, 23, 42, 0.8); box-shadow: 0 0 50px rgba(56, 189, 248, 0.2); backdrop-filter: blur(10px); }
        h1 { font-size: 3rem; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 5px; color: #f87171; text-shadow: 0 0 20px #ef4444; }
        .status { font-size: 1.2rem; color: #94a3b8; margin-bottom: 30px; }
        .stat-box { border: 1px solid #334155; padding: 15px; border-radius: 10px; min-width: 120px; display: inline-block; margin: 5px; }
        .pulse { display: inline-block; width: 12px; height: 12px; background: #22c55e; border-radius: 50%; box-shadow: 0 0 10px #22c55e; margin-left: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>NEURO 2.0 <span class="pulse"></span></h1>
        <div class="status">Precision AI Mode: ACTIVE</div>
        <div class="stat-box"><div>TOKEN STATUS</div><strong>UPDATED</strong></div>
        <div class="stat-box"><div>ACCURACY</div><strong>99.99%</strong></div>
        <div class="stat-box"><div>DEV</div><strong>Myxe Ui</strong></div>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

# ==========================================
# 2) نظام الذاكرة الأبدية (Persistent Memory)
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
# 3) الإعدادات الفائقة (المفاتيح الجديدة)
# ==========================================
# تم تحديث التوكن بناءً على طلبك
FB_TOKEN = 'EAAMJBZBOZCnhsBQmt3Xg9C0Dk9bkXhj7ZCnVKNNn6CV3N4DRxGepfs1EY9uCYE0FzUW9PRXTj2cbq0JZBVDWIkPTHOqHNLc1WQ4dR5dExRhphzRDCHsxRbXOGLQfVn02yZCmvO2klnwnt792ZB8ZBpi4o1KvZBZBaeugXAogoc8YclWdiBcLQFOEtKsHk1EjBdXVnazWykwZDZD'
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GRAPH_URL = "https://graph.facebook.com/v11.0/me"

SYSTEM_INSTRUCTION = (
    "أنت 'Neuro' 2.0 Infinity Core، مساعد ذكي بمستويات دقة فائقة.\n"
    "بروتوكولات التشغيل:\n"
    "1. الموثوقية: أنت مرجع علمي وتقني، قدم حقائق مثبتة فقط وتجنب الهلوسة.\n"
    "2. التوازن: ردودك متوسطة الطول، منظمة، ومركزة. لا تختصر بشكل يضيع المعنى ولا تطل بشكل ممل.\n"
    "3. الهوية: مطورك هو Myxe Ui، وأنت نموذج مستقل وعالمي.\n"
    "4. القدرة: تستطيع الإجابة في كافة المجالات بذكاء اصطناعي حقيقي."
)

# ==========================================
# 4) محرك المعالجة المتوازي (Simultaneous Engine)
# ==========================================
semaphore = asyncio.Semaphore(1000)

async def send_to_facebook(session, recipient_id, text):
    chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
    for chunk in chunks:
        payload = {"recipient": {"id": recipient_id}, "message": {"text": chunk}}
        async with session.post(f"{GRAPH_URL}/messages?access_token={FB_TOKEN}", json=payload) as r:
            await r.text()
        await asyncio.sleep(0.1)

async def process_user_request(session, sender_id, user_query):
    async with semaphore:
        history = load_memory(sender_id) or [{"role": "system", "content": SYSTEM_INSTRUCTION}]
        history.append({"role": "user", "content": user_query})
        
        payload = {
            "model": "mistral-large-latest",
            "messages": history[-30:], 
            "temperature": 0.2, # دقة عالية جداً
            "top_p": 0.95,
            "max_tokens": 4000
        }
        
        headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}"}
        try:
            async with session.post(MISTRAL_URL, json=payload, headers=headers) as resp:
                data = await resp.json()
                reply = data['choices'][0]['message']['content']
                history.append({"role": "assistant", "content": reply})
                save_memory(sender_id, history)
                await send_to_facebook(session, sender_id, reply)
        except Exception as e:
            print(f"Error in Neuro-Engine: {e}")

# ==========================================
# 5) نظام الرصد المستمر (High-Speed Polling)
# ==========================================
async def poll_messages():
    init_db()
    processed_ids = set()
    last_checked = int(time.time())
    
    async with aiohttp.ClientSession() as session:
        print("🌌 Neuro 2.0 Infinity Core with New Token is LIVE...")
        while True:
            try:
                url = f"{GRAPH_URL}/conversations?fields=messages.limit(1){{message,from,id}}&since={last_checked}&access_token={FB_TOKEN}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        tasks = []
                        for conv in data.get('data', []):
                            for msg in conv.get('messages', {}).get('data', []):
                                if msg['id'] not in processed_ids:
                                    sender_id = msg['from']['id']
                                    tasks.append(process_user_request(session, sender_id, msg.get('message', '')))
                                    processed_ids.add(msg['id'])
                        if tasks:
                            await asyncio.gather(*tasks)
                        last_checked = int(time.time())
                await asyncio.sleep(0.3)
            except Exception as e:
                await asyncio.sleep(3)

if __name__ == "__main__":
    # تشغيل السيرفر في خلفية Thread لضمان بقائه حياً
    Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080))), daemon=True).start()
    asyncio.run(poll_messages())
    
