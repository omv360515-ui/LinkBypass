import os
import threading
import re
import requests
from bs4 import BeautifulSoup
from flask import Flask, request
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# 🤖 आपका बॉट टोकन
BOT_TOKEN = "8972808062:AAGDefSN8rOSHQyZerCg1DNuYsLkeUXzunE"

# 📢 चैनल और डेवलपर डिटेल्स
CHANNEL_USERNAME = "@jorogamer"
CHANNEL_URL = "https://t.me/jorogamer"
DEVELOPER_URL = "https://t.me/Joro_Gamer"

# सही Render ऐप नाम
YOUR_RENDER_APP_NAME = "linkbypass-3c6g" 
BASE_URL = f"https://{YOUR_RENDER_APP_NAME}.onrender.com"

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


# 🚀 NEW CUSTOM SCRAPER ENGINE (Direct Token Bypasser)
def custom_bypass(url):
    url = url.strip()
    session = requests.Session()
    
    # ब्राउज़र जैसा दिखने के लिए Headers
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Connection': 'keep-alive'
    })
    
    try:
        # Step 1: शॉर्टनर के पहले पेज पर जाना
        res = session.get(url, timeout=15, allow_redirects=True)
        final_url = res.url
        
        # अगर सीधे ओरिजिनल लिंक पर ही रीडायरेक्ट हो गया हो
        if "arolinks.com" not in final_url and "get2short.com" not in final_url and "short4cash.com" not in final_url and "vplink.in" not in final_url:
            return final_url
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Step 2: फॉर्म इनपुट्स और हिडन टोकन्स ढूंढना
        inputs = soup.find_all('input')
        data = {}
        for i in inputs:
            if i.get('name'):
                data[i.get('name')] = i.get('value', '')
                
        # बहुत से स्क्रिप्ट्स में 'id' या 'g-recaptcha-response' की ज़रूरत होती है
        # हम बैकएंड पर रीडायरेक्शन फॉर्म को मिमिक (नकल) कर रहे हैं
        form = soup.find('form')
        if form and form.get('action'):
            action_url = form.get('action')
            if not action_url.startswith('http'):
                # रिलेटिव URL को पूरा करना
                from urlparse import urljoin # Python 2/3 compatibility safety
                try:
                    from urllib.parse import urljoin
                except ImportError:
                    pass
                
                # बेस डोमेन निकालना
                domain = re.match(r'(https?://[^/]+)', final_url).group(1)
                action_url = urljoin(domain, action_url)
                
            # फॉर्म सबमिट करना बैकएंड पर
            res2 = session.post(action_url, data=data, timeout=15, allow_redirects=True)
            
            # अगर फाइनल डेस्टिनेशन मिल गया
            if res2.status_code == 200:
                # कुछ क्लोन स्क्रिप्ट्स सीधे 'location' स्क्रिप्ट टैग में लिंक देती हैं
                script_links = re.findall(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', res2.text)
                if script_links:
                    return script_links[0]
                
                # अगर रिस्पॉन्स में कोई डायरेक्ट लिंक बटन है
                soup2 = BeautifulSoup(res2.text, 'html.parser')
                for a in soup2.find_all('a', href=True):
                    if 'get link' in a.text.lower() or 'download' in a.text.lower():
                        if "arolinks" not in a['href'] and "get2short" not in a['href']:
                            return a['href']
                            
                return res2.url

    except Exception as e:
        print(f"Scraper Error: {str(e)}")
        
    # --- MULTI-API BACKUP FALLBACK ---
    try:
        # अगर स्क्रैपर अटके, तो एडवांस यूनिवर्सल अल्टरनेटिव API ट्रिगर करना
        alt_api = f"https://api.pepebypass.workers.dev/bypass?url={url}"
        r = requests.get(alt_api, timeout=10).json()
        if r.get("status") == "success" and r.get("bypassed_url"):
            return r.get("bypassed_url")
    except Exception:
        pass
        
    return None


# 🌐 Webhook & Home Routes
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

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
        "🤖 *FAST LINK BYPASS BOT v2.0*\n"
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
    urls = re.findall(r'(https?://[^\s]+)', text)
    
    if not urls:
        bot.reply_to(message, "❌ *Kripya ek valid URL/Link send karein!*", parse_mode="Markdown")
        return
        
    target_url = urls[0]
    processing_msg = bot.send_message(message.chat.id, "⏳ *Bypassing your link with Engine v2... Please wait...*", parse_mode="Markdown")
    
    # कॉल न्यू स्क्रैपर + बैकअप कम्बो
    bypassed_result = custom_bypass(target_url)
    
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
            text="❌ *Bypass Failed!* Ye link active nahi hai ya ye network abhi supported nahi hai.\n\n*Tip:* Ek baar check karein ki link open ho rahi hai ya nahi.",
            parse_mode="Markdown"
        )

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
    
