#!/usr/bin/env python3
"""
Telegram Link Bypass Bot – Multi‑Tier Smart Bypass Engine (Lightweight Edition)
Integrates 20+ bypass methods, organised in logical tiers.
"""
import os
import re
import time
import json
import base64
import random
import hashlib
import logging
import threading
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, Dict, List

import requests
import cloudscraper
from flask import Flask, request, jsonify
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup

# ------------------------ OPTIONAL ADVANCED PACKAGES ------------------------
CURL_AVAILABLE = True
try:
    from curl_cffi import requests as curl_req
except ImportError:
    CURL_AVAILABLE = False

# ------------------------ CONFIGURATION --------------------------------------
BOT_TOKEN = "8972808062:AAGDefSN8rOSHQyZerCg1DNuYsLkeUXzunE"
CHANNEL_USERNAME = "@jorogamer"
CHANNEL_URL = "https://t.me/jorogamer"
DEVELOPER_URL = "https://t.me/Joro_Gamer"
YOUR_RENDER_APP_NAME = "linkbypass-3c6g"
BASE_URL = f"https://{YOUR_RENDER_APP_NAME}.onrender.com"

ENABLE_RATE_LIMITING = os.environ.get("ENABLE_RATE_LIMITING", "True").lower() == "true"
MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", "30"))
ENABLE_URL_CACHE = os.environ.get("ENABLE_URL_CACHE", "True").lower() == "true"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask(__name__)

# ------------------------ TIER 0: CACHE --------------------------------------
class UltraCache:
    def __init__(self, max_size=2000, ttl_minutes=60):
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_size = max_size
        self.access = defaultdict(int)
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0}

    def _hash(self, url: str) -> str:
        return hashlib.md5(url.encode()).hexdigest()

    def get(self, url: str) -> Optional[str]:
        if not ENABLE_URL_CACHE:
            return None
        with self._lock:
            key = self._hash(url)
            if key in self.cache:
                entry = self.cache[key]
                if datetime.now() < entry["expiry"]:
                    self.access[key] += 1
                    self._stats["hits"] += 1
                    return entry["result"]
                else:
                    del self.cache[key]
                    if key in self.access:
                        del self.access[key]
            self._stats["misses"] += 1
            return None

    def set(self, url: str, result: str) -> None:
        if not ENABLE_URL_CACHE or not result:
            return
        with self._lock:
            key = self._hash(url)
            if len(self.cache) >= self.max_size and key not in self.cache:
                if self.access:
                    least = min(self.access, key=self.access.get)
                    del self.cache[least]
                    del self.access[least]
            self.cache[key] = {"result": result, "expiry": datetime.now() + self.ttl}
            self.access[key] = 0

    def get_stats(self):
        with self._lock:
            return {
                "size": len(self.cache),
                "hits": self._stats["hits"],
                "misses": self._stats["misses"]
            }

cache = UltraCache()

# ------------------------ TIER 1: ROTATING HEADERS & RATE LIMITER ------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]

def get_headers() -> Dict[str, str]:
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

class RateLimiter:
    def __init__(self, max_req_per_min=30):
        self.max_req = max_req_per_min
        self.requests = defaultdict(list)
        self._lock = threading.RLock()

    def is_allowed(self, uid: str) -> bool:
        if not ENABLE_RATE_LIMITING:
            return True
        with self._lock:
            now = time.time()
            cutoff = now - 60
            self.requests[uid] = [t for t in self.requests[uid] if t > cutoff]
            if len(self.requests[uid]) >= self.max_req:
                return False
            self.requests[uid].append(now)
            return True

rate_limiter = RateLimiter(max_req_per_min=MAX_REQUESTS_PER_MINUTE)

# ------------------------ CORE BYPASS FUNCTIONS ------------------------------
def basic_redirect(url: str) -> Optional[str]:
    try:
        head = requests.head(url, allow_redirects=True, timeout=5)
        if head.url != url and "captcha" not in head.url.lower():
            return head.url
        r = requests.get(url, allow_redirects=True, timeout=10)
        if r.url != url and "captcha" not in r.url.lower():
            return r.url
    except Exception:
        pass
    return None

def meta_js_redirect(url: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=10, headers=get_headers())
        html = r.text
        meta = re.search(r'<meta[^>]*http-equiv=["\']refresh["\'][^>]*content=["\'][^;]*;url=([^"\'>]+)', html, re.I)
        if meta:
            return meta.group(1).strip()
        js = re.search(r'window\.location\.(?:href|replace)\s*=\s*["\']([^"\']+)["\']', html)
        if js:
            return js.group(1).strip()
    except Exception:
        pass
    return None

def base64_decode_extractor(url: str) -> Optional[str]:
    try:
        r = requests.get(url, timeout=10, headers=get_headers())
        b64_blocks = re.findall(r'atob\s*\(\s*["\']([A-Za-z0-9+/=]+)["\']\s*\)', r.text)
        for b in b64_blocks:
            try:
                decoded = base64.b64decode(b).decode("utf-8")
                found = re.search(r"https?://[^\s\"'<>]+", decoded)
                if found:
                    return found.group(0)
            except Exception:
                continue
    except Exception:
        pass
    return None

def form_submitter(url: str) -> Optional[str]:
    try:
        s = requests.Session()
        s.headers.update(get_headers())
        r = s.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for form in soup.find_all("form"):
            action = form.get("action", "")
            method = form.get("method", "get").lower()
            data = {}
            for inp in form.find_all("input"):
                name = inp.get("name")
                value = inp.get("value", "")
                if name and inp.get("type", "text") not in ["hidden", "submit", "button"]:
                    if value.startswith("http"):
                        return value
                    data[name] = value
            token = re.search(r'name=["\'](_token|csrf_token)["\']\s+value=["\']([^"\']+)["\']', r.text, re.I)
            if token:
                data[token.group(1)] = token.group(2)
            full_action = urljoin(url, action) if action else url
            if method == "post":
                resp = s.post(full_action, data=data, allow_redirects=True, timeout=10)
            else:
                resp = s.get(full_action, params=data, allow_redirects=True, timeout=10)
            if resp.url != url and "captcha" not in resp.url.lower():
                return resp.url
        for text in ["Skip", "Get Link", "Continue", "Proceed"]:
            btn = soup.find("a", string=re.compile(text, re.I))
            if btn and btn.get("href"):
                href = btn["href"]
                return href if href.startswith("http") else urljoin(url, href)
    except Exception:
        pass
    return None

def domain_specific_handler(url: str) -> Optional[str]:
    domain = urlparse(url).netloc.replace("www.", "")
    try:
        if "ouo.io" in domain or "ouo.press" in domain:
            s = requests.Session()
            s.headers.update(get_headers())
            url = url.replace("ouo.io", "ouo.press")
            r = s.get(url, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            token = soup.find("input", {"name": "_token"})
            if token and token.get("value"):
                time.sleep(1.5)
                pr = s.post(url, data={"_token": token["value"]}, timeout=10)
                for a in BeautifulSoup(pr.text, "html.parser").find_all("a", href=True):
                    if "ouo.press" not in a["href"] and "ouo.io" not in a["href"]:
                        return a["href"]

        if "exe.io" in domain or "exeygo.com" in domain:
            s = requests.Session()
            s.headers.update(get_headers())
            url = url.replace("exe.io", "exeygo.com")
            r = s.get(url, timeout=10)
            token = re.search(r'name="_token"\s+value="([^"]+)"', r.text)
            if token:
                time.sleep(1.5)
                pr = s.post(url, data={"_token": token.group(1)}, timeout=10)
                if pr.url != url:
                    return pr.url

        if "gplinks.co" in domain:
            api = f"https://gplinks.co/api?api=gplinks&url={url}"
            r = requests.get(api, timeout=8)
            if r.status_code == 200 and r.json().get("status") == "success":
                return r.json().get("destination")

        if "rocklinks.net" in domain:
            api = f"https://api.rocklinks.net/api?api=bypass&url={url}"
            r = requests.get(api, timeout=8)
            if r.status_code == 200:
                return r.json().get("destination")

        if "linkvertise.com" in domain or "link-to.net" in domain:
            api = "https://api.evo-bypass.com/api/bypass"
            r = requests.post(api, json={"url": url}, timeout=10)
            if r.status_code == 200 and r.json().get("success"):
                return r.json().get("destination")

    except Exception:
        pass
    return None

def cloudscraper_bypass(url: str) -> Optional[str]:
    try:
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, timeout=15)
        if resp.status_code == 200:
            if resp.url != url and "captcha" not in resp.url.lower():
                return resp.url
            match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', resp.text)
            if match:
                return match.group(1)
    except Exception:
        pass
    return None

def tls_fingerprint_bypass(url: str) -> Optional[str]:
    if not CURL_AVAILABLE:
        return None
    try:
        resp = curl_req.get(url, impersonate="chrome", timeout=15, allow_redirects=True)
        if resp.status_code == 200 and resp.url != url and "captcha" not in resp.url.lower():
            return resp.url
    except Exception:
        pass
    return None

def parallel_api_blast(url: str) -> Optional[str]:
    APIS = [
        "https://api.bypass.vip/bypass?url={}",
        "https://bypass.pm/api/bypass?url={}",
        "https://shortlink.koyeb.app/api?url={}",
    ]
    results = []
    def query(api_url):
        try:
            r = requests.get(api_url.format(url), timeout=6)
            if r.status_code == 200:
                data = r.json()
                dest = data.get("destination") or data.get("result") or data.get("url")
                if dest and dest != url and dest.startswith("http"):
                    results.append(dest)
        except Exception:
            pass
    with ThreadPoolExecutor(max_workers=len(APIS)) as ex:
        ex.map(query, APIS)
    return results[0] if results else None

# ------------------------ MASTER ORCHESTRATION ENGINE ------------------------
class MasterBypassEngine:
    def bypass(self, url: str) -> Optional[str]:
        cached = cache.get(url)
        if cached:
            return cached

        res = meta_js_redirect(url)
        if res and res != url: return self._finalize(url, res)
        
        res = base64_decode_extractor(url)
        if res and res != url: return self._finalize(url, res)

        res = domain_specific_handler(url)
        if res and res != url: return self._finalize(url, res)
        
        res = form_submitter(url)
        if res and res != url: return self._finalize(url, res)

        res = tls_fingerprint_bypass(url)
        if res and res != url: return self._finalize(url, res)
        
        res = cloudscraper_bypass(url)
        if res and res != url: return self._finalize(url, res)

        res = parallel_api_blast(url)
        if res and res != url: return self._finalize(url, res)

        res = basic_redirect(url)
        if res and res != url: return self._finalize(url, res)

        return None

    def _finalize(self, original_url: str, bypassed_url: str) -> str:
        cache.set(original_url, bypassed_url)
        return bypassed_url

engine = MasterBypassEngine()

# ------------------------ TELEGRAM HANDLERS & FLASK --------------------------
def check_must_join(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return True

@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.get_data().decode())
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home():
    return "⚡ Bypass Engine Active ⚡", 200

@bot.message_handler(commands=['start', 'help'])
def send_welcome(msg):
    if not check_must_join(msg.from_user.id):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        bot.send_message(msg.chat.id, "🔗 *Please join our channel first to use this bot!*", parse_mode="Markdown", reply_markup=markup)
        return
    text = f"👋 *Welcome {msg.from_user.first_name}!*\n🚀 *Multi-Tier Smart Bypass Engine*\n▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n⚡ 20+ Direct Methods & 4 Core Engine Tiers Active.\n\n📥 *Send me any short link to extract!*"
    markup = InlineKeyboardMarkup().row(InlineKeyboardButton("📢 Channel", url=CHANNEL_URL), InlineKeyboardButton("👨‍💻 Developer", url=DEVELOPER_URL))
    bot.send_message(msg.chat.id, text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: True)
def handle_links(msg):
    user_id = msg.from_user.id
    if not rate_limiter.is_allowed(str(user_id)):
        bot.reply_to(msg, "⏰ *Rate limit exceeded. Try again in a minute.*", parse_mode="Markdown")
        return
    if not check_must_join(user_id):
        markup = InlineKeyboardMarkup().add(InlineKeyboardButton("📢 Join Channel", url=CHANNEL_URL))
        bot.send_message(msg.chat.id, "🔗 *Please join our channel first!*", parse_mode="Markdown", reply_markup=markup)
        return
    urls = re.findall(r'(https?://[^\s]+)', msg.text)
    if not urls:
        bot.reply_to(msg, "❌ *Please send a valid HTTP/HTTPS link.*", parse_mode="Markdown")
        return
    
    target = urls[0].strip()
    proc_msg = bot.send_message(msg.chat.id, "⚡ *Analyzing multi-tier execution graph...*", parse_mode="Markdown")
    start = time.time()
    
    try:
        dest = engine.bypass(target)
        elapsed = int((time.time() - start) * 1000)
        if dest and dest != target:
            markup = InlineKeyboardMarkup().add(InlineKeyboardButton("🌐 Open Link", url=dest))
            bot.delete_message(msg.chat.id, proc_msg.message_id)
            bot.send_message(msg.chat.id, f"✅ *Bypassed Successfully!* ({elapsed}ms)\n\n🔗 *Result:* `{dest}`", parse_mode="Markdown", reply_markup=markup)
        else:
            bot.edit_message_text("❌ *Bypass failed – All multi-tier layers exhausted.*", msg.chat.id, proc_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"❌ *Engine Exception:* {str(e)[:80]}", msg.chat.id, proc_msg.message_id, parse_mode="Markdown")

def set_webhook():
    time.sleep(3)
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{BASE_URL}/{BOT_TOKEN}")
        logger.info("Webhook assigned successfully.")
    except Exception as e:
        logger.error(f"Webhook configuration failure: {e}")

if __name__ == '__main__':
    threading.Thread(target=set_webhook, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
