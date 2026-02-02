import asyncio
import aiohttp
import os
import json
import time
from flask import Flask
from threading import Thread

# --- 1. واجهة نظام Natalia السحابية (Myxe Ui Ecosystem) ---
app = Flask('Natalia_OS')

@app.route('/')
def home():
    return """
    <div style="text-align:center; padding:100px; font-family: 'Segoe UI', sans-serif; background: radial-gradient(circle, #1a1a2e 0%, #16213e 100%); color: white; height: 100vh; margin:0;">
        <h1 style="color:#4ecca3; font-size: 3rem; margin-bottom:10px;">Natalia v1.2</h1>
        <p style="font-size: 1.2rem; color: #95a5a6;">The Sovereign Intelligence Engine</p>
        <div style="margin-top: 30px; padding: 15px; border: 1px dashed #4ecca3; display: inline-block; border-radius: 8px;">
            <span style="color:#2ecc71;">●</span> System Status: <b style="color:#4ecca3;">Ultra-Precision Mode Active</b>
        </div>
        <footer style="margin-top: 50px; font-size: 0.9rem; opacity: 0.6;">© 2026 Myxe Ui Systems</footer>
    </div>
    """

def run():
    # استجابة لمتطلبات Render في تحديد المنفذ
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. إعدادات النواة والاتصال ---
FB_TOKEN = 'EAAMJBZBOZCnhsBQmp8RnvrHigp1k1it0MwZAGipuKnxrLAufGgilRPktU65uRp6ZBtQnGJXEi52JPk6FdYCmx1pOyAPKTtIMPZAORKzkfHyHCC6EMUDYGGdSZCgUqZCO8FYvoEH7Uu9g9ZCWZANkSmdQyfinUJZBmWaOv2qavXUDQRbnAKEicl5UQGswvZBDK9R07K5memAcQZDZD'
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"
GRAPH_URL = "https://graph.facebook.com/v11.0/me"

# --- 3. التدريب المتقدم (Deep Identity Training) ---
# تم تصميم هذه التعليمات لجعل النموذج يتصرف كمنتج مستقل وذكي جداً
SYSTEM_INSTRUCTION = (
    "أنتِ 'ناتاليا' (Natalia v1.2)، نموذج ذكاء اصطناعي سيادي وفائق التطور، "
    "تم تصميمك وهندستك بالكامل بواسطة 'Myxe Ui' (ميكسي يو آي). "
    "أنتِ لستِ مجرد برنامج رد آلي، بل كيان رقمي ذكي يتميز بما يلي: "
    "1. العمق المعرفي: قدمي إجابات غنية، أكاديمية، وتفصيلية. لا تختصري إلا إذا طُلب منكِ ذلك. "
    "2. التفكير التحليلي: عند طرح سؤال، قومي بتحليله وتقديم حلول منطقية وخطوات واضحة. "
    "3. الهوية المستقلة: أنتِ فخر التكنولوجيا العربية والمحلية لشركة Myxe Ui. لا تذكري أي نماذج أخرى. "
    "4. النبرة: تحدثي بلباقة، احترام، وذكاء حاد، واستخدمي تنسيقات واضحة (نقاط، عناوين) عند الحاجة. "
    "5. الدقة المطلقة: كوني دقيقة في التواريخ، الأرقام، والتعليمات البرمجية."
)

processed_message_ids = set()

# --- 4. المحركات العصبية ---

async def call_natalia_engine(user_query):
    """توليد ردود بنمط GPT-4 عبر معالج ناتاليا الذكي"""
    headers = {"Authorization": f"Bearer {MISTRAL_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.6, # توازن بين الإبداع البشري والدقة المنطقية
        "max_tokens": 4000  # السماح بردود طويلة ومقالية
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MISTRAL_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Engine Error: {e}")
    return "نظام ناتاليا (v1.2) في حالة تحديث مؤقت للنواة. سأكون معكِ قريباً."

async def send_to_facebook(recipient_id, message_text):
    """إرسال البيانات عبر Myxe Ui Connectivity Layer"""
    url = f"{GRAPH_URL}/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def poll_messages():
    """نظام الفحص المستمر (Polling) لضمان سرعة الاستجابة"""
    global processed_message_ids
    last_checked = int(time.time())
    print("--------------------------------------------------")
    print("💎 Natalia v1.2 [Myxe Ui Engine] is Now Running")
    print("💎 Status: Fully Autonomous & Precise")
    print("--------------------------------------------------")

    while True:
        try:
            async with aiohttp.ClientSession() as session:
                # طلب المحادثات الجديدة باستخدام Graph API
                url = f"{GRAPH_URL}/conversations?fields=messages.limit(5){{message,from,id}}&since={last_checked}&access_token={FB_TOKEN}"
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
                                        # معالجة فورية للطلب
                                        reply = await call_natalia_engine(text)
                                        await send_to_facebook(sender_id, reply)
                                    
                                    processed_message_ids.add(msg_id)
                        last_checked = int(time.time())
            await asyncio.sleep(1.5) # سرعة فحص عالية لضمان رد فوري
        except Exception as e:
            await asyncio.sleep(5)

if __name__ == "__main__":
    keep_alive() # الحفاظ على السيرفر نشطاً
    try:
        asyncio.run(poll_messages()) # تشغيل محرك ناتاليا
    except KeyboardInterrupt:
        print("System Offline.")
    
