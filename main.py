import os
import threading
import re
import requests
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🤖 आपका नया बॉट टोकन
BOT_TOKEN = "8972808062:AAGDefSN8rOSHQyZerCg1DNuYsLkeUXzunE"

# 📢 चैनल और डेवलपर डिटेल्स
CHANNEL_USERNAME = "@jorogamer"
CHANNEL_URL = "https://t.me/jorogamer"
DEVELOPER_URL = "https://t.me/Joro_Gamer"

# आपकी Render ऐप का नाम (अगर आपने Render पर नई ऐप बनाई है, तो उसका नाम यहाँ डालें)
YOUR_RENDER_APP_NAME = "file2linklite" 
BASE_URL = f"https://{YOUR_RENDER_APP_NAME}.onrender.com"

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# 🔒 Force Join Check Function
def check_must_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return True

# 📢 Join Request Message
def send_join_request(chat_id):
    join_text = (
        "🔗 *To use Link Bypass Bot, you must join our channel!*\n\n"
        "Pehle neeche diye gaye button par click karke channel join karein, "
        "uske baad dubara `/start` dabayein."
    )
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
    bot.send_message(chat_id, join_text, parse_mode="Markdown", reply_markup=markup)

# 🚀 LINK BYPASS LOGIC (Multi-Bypass Engine)
def bypass_link(url):
    # साफ़ लिंक निकालने के लिए क्लीनअप
    url = url.strip()
    
    # अगर डायरेक्ट मेगा या कोई नॉर्मल लिंक है
    if "mega.nz" in url or "google.com" in url:
        return url

    try:
        # इन शार्टनर्स के लिए एक सिक्योर यूनिवर्सल बायपास API का इस्तेमाल
        # यह arolinks, short4cash, vplink, speedy-links, get2short सबको हैंडल करने की कोशिश करता है
        api_url = f"https://wb-bypass-api.vercel.app/api/bypass?url={url}"
        response = requests.get(api_url, timeout=10)
        res_json = response.json()
        
        if res_json.get("status") == "success" or "bypassed_url" in res_json:
            return res_json.get("bypassed_url") or res_json.get("destination")
            
        # बैकअप API (अगर पहली काम न करे)
        backup_api = f"https://api.dualects.com/bypass?url={url}"
        backup_res = requests.get(backup_api, timeout=10).json()
        if backup_res.get("bypassed"):
            return backup_res.get("bypassed_url")
            
    except Exception as e:
        print(f"Bypass Error: {str(e)}")
    
    return None


# 🌐 Webhook Route
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

# 🏠 होम रूट
@app.route('/')
def home():
    return "⚡ Joro Link Bypass Bot Is Running Alive ⚡", 200


# --- TELEGRAM BOT LOGIC ---

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    if not check_must_join(message.from_user.id):
        send_join_request(message.chat.id)
        return

    user_name = message.from_user.first_name
    welcome_text = (
        f"👋 *Welcome, {user_name}!*\n\n"
        "🤖 *FAST LINK BYPASS BOT*\n"
        "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
        "⚡ *Supported Links:*\n"
        "├ GPlinks, Arolinks, Short4cash\n"
        "├ Vplink, Speedy-links, Get2short\n"
        "└ Sub2Unlock & All Ad-Shortners!\n\n"
        "📥 *Kaise Use Karein?*\n"
        "Aap koi bhi shortener link is chat me send karein. Bot bina kisi ad ya timer ke aapko direct original link nikal kar dega!"
    )
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("📢 Channel", url=CHANNEL_URL),
        InlineKeyboardButton("👨‍💻 Developer", url=DEVELOPER_URL)
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_links(message):
    if not check_must_join(message.from_user.id):
        send_join_request(message.chat.id)
        return

    text = message.text
    # लिंक ढूंढने के लिए Regex
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if not urls:
        bot.reply_to(message, "❌ *Kripya ek valid URL/Link send karein!*", parse_mode="Markdown")
        return
        
    target_url = urls[0]
    
    processing_msg = bot.send_message(
        message.chat.id, 
        "⏳ *Bypassing your link... Please wait...*", 
        parse_mode="Markdown"
    )
    
    # बायपास फंक्शन को कॉल करना
    bypassed_result = bypass_link(target_url)
    
    if bypassed_result:
        success_text = (
            "✅ *Link Successfully Bypassed!*\n"
            "▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
            "🔗 *Original Destination Link Below:* \n"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🌐 Open Direct Link", url=bypassed_result))
        
        bot.delete_message(message.chat.id, processing_msg.message_id)
        bot.send_message(message.chat.id, success_text, parse_mode="Markdown", reply_markup=markup)
    else:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            text="❌ *Bypass Failed!* Ye link active nahi hai ya ye network abhi supported nahi hai.",
            parse_mode="Markdown"
        )


# 🛠️ AUTOMATIC WEBHOOK SETUP
def set_webhook():
    import time
    time.sleep(2)
    bot.remove_webhook()
    webhook_url = f"{BASE_URL}/{BOT_TOKEN}"
    bot.set_webhook(url=webhook_url)

if __name__ == '__main__':
    webhook_thread = threading.Thread(target=set_webhook)
    webhook_thread.daemon = True
    webhook_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    