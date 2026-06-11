import os
import re
import time
import threading
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🤖 आपका बॉट टोकन
BOT_TOKEN = "8972808062:AAGDefSN8rOSHQyZerCg1DNuYsLkeUXzunE"

# 📢 चैनल और डेवलपर डिटेल्स
CHANNEL_USERNAME = "@jorogamer"
CHANNEL_URL = "https://t.me/jorogamer"
DEVELOPER_URL = "https://t.me/Joro_Gamer"

# Render ऐप नाम (Webhook के लिए)
YOUR_RENDER_APP_NAME = "linkbypass-3c6g" 
BASE_URL = f"https://{YOUR_RENDER_APP_NAME}.onrender.com"

# 🔑 Premium API Key (Render Environment Variables से उठाएगा)
BYPASS_API_KEY = os.environ.get("BYPASS_API_KEY", "")

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 🔒 Force Join Check
def check_must_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

def send_join_request(chat_id):
    join_text = (
        "🔗 *To use Link Bypass Bot, you must join our channel!*\n\n"
        "Pehle neeche diye gaye button par click karke channel join karein, "
        "uske baad dubara `/start` dabayein."
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
    bot.send_message(chat_id, join_text, parse_mode="Markdown", reply_markup=markup)

# 🚀 UNIVERSAL MULTI-ROUTING ENGINE
def universal_bypass(url):
    url = url.strip()
    
    # -------- ROUTE 1: PREMIUM BYPASSTOOLS SDK --------
    if BYPASS_API_KEY and BYPASS_API_KEY.startswith("bt_"):
        headers = {"x-api-key": BYPASS_API_KEY, "Content-Type": "application/json"}
        try:
            res = requests.post("https://api.bypass.tools/api/v1/bypass/direct", json={"url": url, "refresh": False}, headers=headers, timeout=12).json()
            if "resultUrl" in res: return res["resultUrl"]
            if "result" in res: return res["result"]
        except Exception:
            pass

    # -------- ROUTE 2: ADVANCED FREE HYBRID PUBLIC API ROSTER --------
    api_endpoints = [
        f"https://api.bypass.vip/bypass?url={url}",
        f"https://id.bypass.vip/api/bypass?url={url}",
        f"https://api.g9bypasser.xyz/bypass?url={url}",
        f"https://pub.bypasser.atest.workers.dev/api?url={url}",
        f"https://unbypassed.vercel.app/api/bypass?url={url}"
    ]
    
    for api in api_endpoints:
        try:
            response = requests.get(api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                dest = data.get("destination") or data.get("bypassed_url") or data.get("bypassed") or data.get("bypassed_link")
                if dest and dest != url and not dest.startswith("Error") and "captcha" not in dest.lower():
                    return dest
        except Exception:
            continue
            
    return None

# 🌐 Webhook Setup
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home():
    return "⚡ Joro Hybrid Multi-Bypass Is Live ⚡", 200

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not check_must_join(message.from_user.id):
        send_join_request(message.chat.id)
        return

    welcome_text = (
        f"👋 *Welcome, {message.from_user.first_name}!*\n\n"
        "🤖 *UNIVERSAL BYPASS ENGINE (Fast v4)*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "📥 *Kaise Use Karein?*\n"
        "Aap kisi bhi shortener ka link send karein। Bot multi-servers का इस्तेमाल करके डायरेक्ट लिंक निकाल देगा!"
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Channel", url=CHANNEL_URL), InlineKeyboardButton("👨‍💻 Developer", url=DEVELOPER_URL))
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    chat_id = message.chat.id
    if not check_must_join(message.from_user.id):
        send_join_request(chat_id)
        return

    urls = re.findall(r'(https?://[^\s]+)', message.text)
    if not urls:
        bot.reply_to(message, "❌ *Kripya ek valid URL/Link send karein!*", parse_mode="Markdown")
        return
        
    target_url = urls[0].strip()
    processing_msg = bot.send_message(chat_id, "⏳ *Bypassing your link... Please wait...*", parse_mode="Markdown")
    
    try:
        bypassed_result = universal_bypass(target_url)
        
        if bypassed_result and bypassed_result != target_url:
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🌐 Open Direct Link", url=bypassed_result))
            bot.delete_message(chat_id, processing_msg.message_id)
            bot.send_message(chat_id, "✅ *Link Successfully Bypassed!*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id, text="❌ *Bypass Failed!* Yeh link abhi supported nahi hai ya active nahi hai।")
            
    except Exception as error:
        bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id, text="❌ *An error occurred while breaking the link.*")

def set_webhook():
    time.sleep(2)
    bot.remove_webhook()
    bot.set_webhook(url=f"{BASE_URL}/{BOT_TOKEN}")

if __name__ == '__main__':
    threading.Thread(target=set_webhook, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
