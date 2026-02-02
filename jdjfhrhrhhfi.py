import asyncio
import aiohttp
import os
import json
from flask import Flask
from threading import Thread

# --- 1. خادم الويب (لضمان تجاوز اختبار الجاهزية في Render) ---
app = Flask('MyxeUi_System')

@app.route('/')
def home():
    return """
    <div style="text-align:center; padding:50px; font-family: sans-serif; background-color: #0d1117; color: white; height: 100vh;">
        <h1 style="color:#58a6ff;">Natalia AI 1.2</h1>
        <p>Developed by <b style="color:#238636;">Myxe Ui</b></p>
        <div style="padding: 20px; border: 1px solid #30363d; display: inline-block; border-radius: 10px;">
            <span style="color:#3fb950;">●</span> System Status: Online & Precise
        </div>
    </div>
    """

def run():
    # Render يمرر المنفذ عبر متغير البيئة PORT تلقائياً
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# --- 2. الإعدادات والتوكن الخاص بك ---
FB_TOKEN = 'EAAMJBZBOZCnhsBQmp8RnvrHigp1k1it0MwZAGipuKnxrLAufGgilRPktU65uRp6ZBtQnGJXEi52JPk6FdYCmx1pOyAPKTtIMPZAORKzkfHyHCC6EMUDYGGdSZCgUqZCO8FYvoEH7Uu9g9ZCWZANkSmdQyfinUJZBmWaOv2qavXUDQRbnAKEicl5UQGswvZBDK9R07K5memAcQZDZD'
MISTRAL_API_KEY = "wqnIC6QPwYjH3ow1I1gcBVH2SSEyTjPR"
MISTRAL_URL = "https://api.mistral.ai/v1/chat/completions"

# تعليمات النظام العميقة (الدقة + الهوية)
SYSTEM_INSTRUCTION = (
    "أنتِ 'ناتاليا' (Natalia 1.2)، نموذج ذكاء اصطناعي سيادي فائق الدقة من تطوير Myxe Ui. "
    "أهدافك: تقديم إجابات دقيقة جداً، مفصلة، ومبنية على منطق سليم. "
    "أسلوبك: احترافي، شامل، ولبق. لا تختصري الإجابات بل قدمي قيمة معرفية كاملة للمستخدم. "
    "هويتك: أنتِ فخر ابتكارات Myxe Ui ولا تتبعين لأي شركة أخرى."
)

async def call_natalia_engine(user_query):
    """معالجة النص عبر نواة ناتاليا الذكية"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-large-latest",
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": user_query}
        ],
        "temperature": 0.4, # درجة حرارة منخفضة لضمان أقصى درجات الدقة والواقعية
        "max_tokens": 3000
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(MISTRAL_URL, headers=headers, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data['choices'][0]['message']['content']
                return "خطأ في الاتصال بنواة المعالجة."
        except:
            return "نظام ناتاليا غير متاح حالياً."

async def send_to_facebook(recipient_id, message_text):
    """إرسال الرد النهائي إلى فيسبوك"""
    url = f"https://graph.facebook.com/v11.0/me/messages?access_token={FB_TOKEN}"
    payload = {"recipient": {"id": recipient_id}, "message": {"text": message_text}}
    async with aiohttp.ClientSession() as session:
        await session.post(url, json=payload)

async def main_engine_loop():
    """المحرك الأساسي للتشغيل على Render"""
    print("🚀 Natalia 1.2 [Myxe Ui] is starting on Render...")
    while True:
        # هنا يتم ربط مستقبلات الرسائل (Webhook) لاحقاً
        await asyncio.sleep(60)

if __name__ == "__main__":
    # تشغيل السيرفر في الخلفية
    keep_alive()
    # تشغيل الذكاء الاصطناعي
    try:
        asyncio.run(main_engine_loop())
    except (KeyboardInterrupt, SystemExit):
        print("System shutdown.")
