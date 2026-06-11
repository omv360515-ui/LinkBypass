import os
import re
import time
import threading
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
import datetime

# 🤖 आपका बॉट टोकन
BOT_TOKEN = "8972808062:AAGDefSN8rOSHQyZerCg1DNuYsLkeUXzunE"

# 📢 चैनल और डेवलपर डिटेल्स
CHANNEL_USERNAME = "@jorogamer"
CHANNEL_URL = "https://t.me/jorogamer"
DEVELOPER_URL = "https://t.me/Joro_Gamer"

# 👑 एडमिन टेलीग्राम आईडी
ADMIN_ID = "7056647424"

# Render ऐप नाम (Webhook के लिए)
YOUR_RENDER_APP_NAME = "linkbypass-3c6g" 
BASE_URL = f"https://{YOUR_RENDER_APP_NAME}.onrender.com"

# 🔑 API Keys और डेटाबेस
MONGO_URI = os.environ.get("MONGO_URI", "your_mongodb_atlas_link_here")
BYPASS_API_KEY = os.environ.get("BYPASS_API_KEY", "your_bypass_tools_key_here")

# 🗄️ DATABASE SETUP (MongoDB)
try:
    client = MongoClient(MONGO_URI)
    db = client['JoroBypassBot']
    users_col = db['Users']
    cache_col = db['Cache']
    cache_col.create_index("createdAt", expireAfterSeconds=86400) # 24 घंटे का कैशे एक्सपायरी
    print("Database connected successfully!")
except Exception as e:
    print(f"Database connection error: {e}")

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


# 🚀 UNIVERSAL MULTI-ROUTING BYPASS ENGINE
def universal_bypass(url):
    url = url.strip()
    
    # -------- ROUTE 1: PREMIUM BYPASSTOOLS SDK (FOR LINKVERTISE, LOOTLABS, ETC.) --------
    if BYPASS_API_KEY and BYPASS_API_KEY.startswith("bt_"):
        headers = {"x-api-key": BYPASS_API_KEY, "Content-Type": "application/json"}
        try:
            # Sync Method
            res = requests.post("https://api.bypass.tools/api/v1/bypass/direct", json={"url": url, "refresh": False}, headers=headers, timeout=12).json()
            if "resultUrl" in res or "result" in res:
                return res.get("resultUrl") or res.get("result")
        except Exception:
            pass

        try:
            # Async Task Method
            task_res = requests.post("https://api.bypass.tools/api/v1/bypass/createTask", json={"url": url}, headers=headers, timeout=10).json()
            if "taskId" in task_res:
                task_id = task_res["taskId"]
                for _ in range(6):
                    time.sleep(1.5)
                    status_res = requests.get(f"https://api.bypass.tools/api/v1/bypass/getTaskResult/{task_id}", headers=headers, timeout=8).json()
                    if status_res.get("status") in ["completed", "success"]:
                        return status_res.get("resultUrl") or status_res.get("result")
                    if status_res.get("status") == "failed":
                        break
        except Exception:
            pass

    # -------- ROUTE 2: ADVANCED MULTI-API FALLBACKS (FOR ALL OTHER SHORTENERS) --------
    api_endpoints = [
        f"https://api.bypass.vip/bypass?url={url}",
        f"https://id.bypass.vip/api/bypass?url={url}",
        f"https://api.g9bypasser.xyz/bypass?url={url}",
        f"https://bypasser.atest.workers.dev/api?url={url}"
    ]
    
    for api in api_endpoints:
        try:
            response = requests.get(api, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # अलग-अलग APIs के रिपॉन्स फॉर्मेट्स को संभालना
                dest = data.get("destination") or data.get("bypassed_url") or data.get("bypassed") or data.get("url")
                if dest and dest != url and not dest.startswith("Error"):
                    return dest
        except Exception:
            continue

    # -------- ROUTE 3: GENERIC ADLINKFLY SCRAPER (FOR LOCAL/SMALL SHORTENERS) --------
    try:
        # बहुत से शॉर्टनर्स में डायरेक्ट 'safe' या 'go' पैरामीटर काम कर जाता है
        if "safe" in url or "go" in url:
            session = requests.Session()
            session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
            res = session.get(url, timeout=8, allow_redirects=True)
            if res.url != url and not any(x in res.url for x in ["login", "register", "captcha"]):
                return res.url
    except Exception:
        pass

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
    return "⚡ Joro Universal Hybrid Bypass Bot Is Live ⚡", 200


# --- TELEGRAM BOT LOGIC ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    user_id = str(message.from_user.id)
    
    try:
        users_col.update_one(
            {"userId": user_id},
            {"$set": {"username": message.from_user.username, "firstName": message.from_user.first_name, "joinedAt": datetime.datetime.utcnow()}},
            upsert=True
        )
    except Exception:
        pass

    if not check_must_join(message.from_user.id):
        send_join_request(chat_id)
        return

    welcome_text = (
        f"👋 *Welcome, {message.from_user.first_name}!*\n\n"
        "🤖 *UNIVERSAL BYPASS ENGINE v4*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "📥 *Kaise Use Karein?*\n"
        "Aap kisi bhi shortener ka link send karein (GPlinks, Linkvertise, Shareus, Droplink आदि)। यह बॉट उसे ऑटो-डिटेक्ट करके सीधे ओरिजिनल डेस्टिनेशन लिंक निकाल देगा!"
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Channel", url=CHANNEL_URL), InlineKeyboardButton("👨‍💻 Developer", url=DEVELOPER_URL))
    bot.send_message(chat_id, welcome_text, parse_mode="Markdown", reply_markup=markup)


# 📊 ADMIN COMMANDS
@bot.message_handler(commands=['stats'])
def bot_stats(message):
    if str(message.from_user.id) != ADMIN_ID: return
    total_users = users_col.count_documents({})
    cached_links = cache_col.count_documents({})
    bot.send_message(message.chat.id, f"📊 *Bot Live Stats:*\n\n👥 Users: *{total_users}*\n💾 Cached Links: *{cached_links}*", parse_mode="Markdown")

@bot.message_handler(commands=['broadcast'])
def bot_broadcast(message):
    if str(message.from_user.id) != ADMIN_ID: return
    command_text = message.text.replace("/broadcast", "").strip()
    if not command_text:
        bot.reply_to(message, "❌ Text missing. Example: `/broadcast Offer Live`")
        return
    all_users = list(users_col.find({}, {"userId": 1}))
    bot.send_message(message.chat.id, f"🚀 *Broadcasting to {len(all_users)} users...*")
    
    success = 0
    for u in all_users:
        try:
            bot.send_message(u["userId"], command_text)
            success += 1
            time.sleep(0.04)
        except Exception:
            pass
    bot.send_message(message.chat.id, f"✅ *Broadcast Done!* Sent to: *{success}* users.")


# 📥 मुख्य लिंक रिसीवर
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
    processing_msg = bot.send_message(chat_id, "⏳ *Analyzing and Bypassing your link... Please wait...*", parse_mode="Markdown")
    
    try:
        # 💾 CACHE LAYER: पहले डेटाबेस चेक करो
        cached_data = cache_col.find_one({"originalLink": target_url})
        if cached_data:
            bot.delete_message(chat_id, processing_msg.message_id)
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🌐 Open Direct Link", url=cached_data["bypassedLink"]))
            bot.send_message(chat_id, "✅ *Link Retrieved From Cache (Instant)!*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", parse_mode="Markdown", reply_markup=markup)
            return

        # 🚀 MULTI-ROUTING BYPASS MECHANISM
        bypassed_result = universal_bypass(target_url)
        
        if bypassed_result and bypassed_result != target_url:
            # डेटाबेस में सहेजें
            cache_col.insert_one({"originalLink": target_url, "bypassedLink": bypassed_result, "createdAt": datetime.datetime.utcnow()})
            
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🌐 Open Direct Link", url=bypassed_result))
            bot.delete_message(chat_id, processing_msg.message_id)
            bot.send_message(chat_id, "✅ *Link Successfully Bypassed!*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id, text="❌ *Bypass Failed!* यह लिंक सपोर्टेड नहीं है, एक्टिव नहीं है या इसकी सिक्योरिटी बेहद मजबूत है।")
            
    except Exception as error:
        print(error)
        bot.edit_message_text(chat_id=chat_id, message_id=processing_msg.message_id, text="❌ *An error occurred while breaking the link.*")


def set_webhook():
    time.sleep(2)
    bot.remove_webhook()
    bot.set_webhook(url=f"{BASE_URL}/{BOT_TOKEN}")

if __name__ == '__main__':
    threading.Thread(target=set_webhook, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
