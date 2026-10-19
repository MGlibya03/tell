#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import re
import html
import json
import time
import random
import sqlite3
import logging
import threading
from pathlib import Path
from datetime import datetime
from flask import Flask

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

# ══════════════════════════════════════════════════════════════════
# ⚙️ الإعدادات الأساسية لبوت أركان الليبي
# ══════════════════════════════════════════════════════════════════
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID: int = 1053838533  # المطور الأساسي MG
TARGET_CHANNEL_ID: int = -1003747214322
CHANNEL_USERNAME: str = "AurelianMind03"
BOT_USERNAME: str = "ArkanLyBot"
BOT_DEFAULT_NAME: str = "أركان"
DB_FILE: Path = Path("arkan_libya.db")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

if not BOT_TOKEN:
    raise ValueError("❌ خطأ: BOT_TOKEN غير موجود في Environment Variables!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════
# 🌐 سيرفر الويب (لإبقاء Render + UptimeRobot شغالاً 24/7)
# ══════════════════════════════════════════════════════════════════
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "✅ إمبراطورية أركان الليبية — البوت يعمل بنجاح 24/7!", 200

@web_app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ══════════════════════════════════════════════════════════════════
# 🗄️ قاعدة البيانات الشاملة والمحمية بـ RLock
# ══════════════════════════════════════════════════════════════════
db_lock = threading.RLock()

def get_db():
    conn = sqlite3.connect(str(DB_FILE), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bot_config (
                key TEXT PRIMARY KEY,
                val TEXT
            )
        """)
        c.execute("INSERT OR IGNORE INTO bot_config (key, val) VALUES ('bot_name', ?)", (BOT_DEFAULT_NAME,))

        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                username TEXT,
                city TEXT DEFAULT 'طرابلس',
                job TEXT DEFAULT 'عاطل',
                cash INTEGER DEFAULT 500,
                bank_balance INTEGER DEFAULT 0,
                bank_name TEXT DEFAULT 'بدون مصرف',
                loan INTEGER DEFAULT 0,
                hp INTEGER DEFAULT 100,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                jail_until INTEGER DEFAULT 0,
                jail_reason TEXT DEFAULT '',
                wanted INTEGER DEFAULT 0,
                house TEXT DEFAULT 'بدون سكن',
                car TEXT DEFAULT 'بدون سيارة',
                business TEXT DEFAULT 'بدون مشروع',
                stocks TEXT DEFAULT '{}',
                married_to INTEGER DEFAULT 0,
                dowry INTEGER DEFAULT 0,
                steal_success INTEGER DEFAULT 0,
                msg_count INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                last_salary INTEGER DEFAULT 0,
                last_rob INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0,
                last_collect INTEGER DEFAULT 0,
                firewall_until INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                seller_name TEXT,
                item_type TEXT,
                item_name TEXT,
                price INTEGER
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                locks TEXT DEFAULT '{}',
                settings TEXT DEFAULT '{}',
                welcome_enabled INTEGER DEFAULT 1,
                welcome_text TEXT DEFAULT 'مرحبتين بيك يا غالي في لمّتنا الليبية 🇱🇾 نورت القروب!',
                rules_text TEXT DEFAULT 'احترام الجميع وعدم نشر الروابط أو الشتائم.',
                replies TEXT DEFAULT '{}',
                shortcuts TEXT DEFAULT '{}'
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS ranks (
                chat_id INTEGER,
                user_id INTEGER,
                rank_level INTEGER DEFAULT 0,
                custom_title TEXT DEFAULT '',
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER,
                user_id INTEGER,
                count INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS whispers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                sender_id INTEGER,
                sender_name TEXT,
                target_id INTEGER,
                target_name TEXT,
                text TEXT,
                timestamp TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS scratch_cards (
                code TEXT PRIMARY KEY,
                amount INTEGER,
                claimed_by INTEGER DEFAULT 0
            )
        """)
        conn.commit()
        conn.close()

init_db()


# ══════════════════════════════════════════════════════════════════
# 📚 الثوابت، القوائم، والمحتوى الليبي
# ══════════════════════════════════════════════════════════════════

BOT_CALL_REPLIES = [
    "▽ : عيون {name} يا غالي، تفضل شن تبي؟ 😎🇱🇾",
    "▽ : نعم يا مدير، {name} في الخدمة! اكتب <code>الاوامر</code> وشوف الفخامة 🔥",
    "▽ : ها يا غالي تنادي فيا؟ كان تبي سلف راهو المصرف مسكر 😂🏦",
    "▽ : لبيه! {name} حاضر وناظر، شن الجو عندكم؟ ✨",
    "▽ : يا مرحبتين! ناديت {name} ولقيته قدامك، آمرني يا غالي 👑"
]

BEAUTY_COMPLIMENTS = [
    "ما شاء الله، وجهك ينور القروب حتى لو الكهرباء هاربة! 😍⚡",
    "فخامة وهيبة ليبية أصيلة، خمسة وخميسة عليك! 🔥👑",
    "جمال رباني يفتح النفس، ربي يحفظك يا غالي ✨🌸",
    "صورة عالمية، تستاهل تنحط في لوحة شرف القروب! 😎💎",
    "نور على نور، هالصورة ترد الروح والله! ❤️🇱🇾"
]

SONGS_LIST = [
    "🎵 <i>يا غالي لو تبي ترحل، خذ قلبي معاك...</i> 🎶",
    "🎵 <i>طرابلس يا عروس البحر، فيك الزين وفيك السهر...</i> 🇱🇾🎶",
    "🎵 <i>بنغازي يا مربى العز، قلبي لغيرك ما يهتز...</i> 🇱🇾🎶",
    "🎵 <i>اللي باعنا خسر دلعنا، واللي شرانا فوق الراس وضعنا!</i> 🎶"
]

POEMS_LIST = [
    "📜 <b>شعر شعبي ليبي :</b>\nيا صاحبي الدنيا امتحانات .. وفيها الصبر مفتاح الفرج\nواللي معاه الله في الأزمات .. يطلع من الضيقة بلا حرج",
    "📜 <b>شعر ليبي :</b>\nعز الرفيق اللي يبان نهار الضيق .. أما الرخا واجد تلاقي خوت\nوزن الذهب يفرق على التلفيق .. والمرجلة موقف قبل ما تموت"
]

JOKES_LIST = [
    "😂 واحد ليبي قال لصاحبه: عيني توجع فيا من أمس! قاله صاحبه: والله أمس سنوني وجعتني خلعتها ارتحت.. كان تبي نصيحتي اخلعها! 🤣",
    "😂 واحد مشى للدكتور قاله: يا دكتور كل ما نشرب شاهي عيني تضربني! قاله الدكتور: حول الكاشيك من الطاسة يا ذكي! 🤣",
    "😂 سألوا واحد بخيل: لو الدنيا صقع قارس، شن تدير؟ قال: نقرب من الدفاية. قالوله: ولو زاد الصقع بكل؟ قال: نولع الدفاية! 🤣"
]

ADHKAR_LIST = [
    "📿 <b>ذكر الله :</b> «سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ»",
    "📿 <b>ذكر الله :</b> «لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ»",
    "📿 <b>ذكر الله :</b> «أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ وَأَتُوبُ إِلَيْهِ»"
]

LAW_KHAYAROUK_LIST = [
    "🤔 <b>لو خيروك :</b> تاخذ 100 ألف دينار كاش توا، ولا تسافر تعيش في سويسرا بدون فلوس؟",
    "🤔 <b>لو خيروك :</b> تاكل بازين كل يوم لمدة شهر، ولا ما تاكلش مكرونة مبكبكة لمدة سنة؟"
]

SARAHA_QUESTIONS = [
    "💬 <b>سؤال صراحة :</b> شن أكثر شيء ندمت عليه في حياتك؟",
    "💬 <b>سؤال صراحة :</b> من هو أكثر شخص في هذا القروب ترتاح له؟"
]

OPINIONS_LIST = [
    "عسل القروب هذا، الله يحفظه ويخليه لينا 😍🍯",
    "شخصية فخمة وهيبة، كلامه كله موزون 👑✨",
    "هذا حرامي المصارف الأول، ديروا بالكم على جيوبكم منه 😂🦹‍♂️"
]

ROASTS_LIST = [
    "يا راجل وجهك يجيب قطع الكهرباء في عز القايلة 😂⚡",
    "أنت لو تشارك في مسابقة أغبى واحد، تطلع الثاني.. لأنك غبي ما عرفتش تفوز بالأول 😂🐸"
]

GIFTS_LIST = [
    "🎁 ساعـة رولكس فخمة ⌚✨",
    "🎁 صحن مبكبكة سخون باللحم الوطني 🍲🔥",
    "🎁 آيفون 16 برو ماكس ذهبي 📱😍"
]

CITIES = {
    "طرابلس": {"ticket": 150, "risk": 25},
    "بنغازي": {"ticket": 250, "risk": 25},
    "مصراتة": {"ticket": 180, "risk": 20},
    "سبها": {"ticket": 300, "risk": 35},
    "الزاوية": {"ticket": 100, "risk": 20},
    "غريان": {"ticket": 120, "risk": 15},
    "طبرق": {"ticket": 350, "risk": 30},
}

BANKS = [
    "مصرف التجارة والتنمية",
    "المصرف التجاري الوطني",
    "مصرف الجمهورية",
    "مصرف الصحارى",
    "مصرف الوحدة"
]

JOBS = {
    "دكتور": {"salary": 2500, "desc": "يعالج المرضى والمصابين (أمر: علاج بالرد)"},
    "مبرمج": {"salary": 2800, "desc": "يخترق الصرافات ويحمي الحسابات (أمر: اختراق صراف / حماية حساب)"},
    "شرطي": {"salary": 2200, "desc": "يقبض على الحرامية والمطلوبين بمكافأة (أمر: قبض بالرد)"},
    "صيدلي": {"salary": 2000, "desc": "يبيع الأدوية للمصابين (أمر: بيع دواء بالرد)"},
    "ميكانيكي": {"salary": 1800, "desc": "يصلح السيارات ويكسب أتعاب (أمر: تصليح بالرد)"},
    "تاجر": {"salary": 3000, "desc": "خبير في التهريب والمشاريع والأسهم"},
}

HOUSES = {
    "شقة في الفلاح": {"price": 25000, "defense": 15},
    "حوش في سوق الجمعة": {"price": 60000, "defense": 30},
    "فيلا في السراج": {"price": 150000, "defense": 50},
    "فيلا في الهواري": {"price": 180000, "defense": 60},
    "قصر في فينيسيا": {"price": 450000, "defense": 85},
}

CARS = {
    "تويوتا دبدوبة": {"price": 8000, "speed": 60},
    "هيونداي سوناتا": {"price": 18000, "speed": 75},
    "كيا اوبتيما": {"price": 22000, "speed": 80},
    "لاندكروزر": {"price": 65000, "speed": 85},
    "مرسيدس قرش": {"price": 95000, "speed": 92},
    "سيارة جارجر": {"price": 120000, "speed": 98},
}

BUSINESSES = {
    "مقهى شعبي": {"price": 30000, "income": 3500},
    "صيدلية الشفاء": {"price": 75000, "income": 8500},
    "محل قطع غيار": {"price": 110000, "income": 13000},
    "شركة برمجيات": {"price": 180000, "income": 22000},
    "معرض سيارات": {"price": 350000, "income": 45000},
}

STOCKS = {
    "المدار": 150,
    "ليبيانا": 180,
    "البريقة": 320,
    "الخطوط_الليبية": 240,
}

RANK_NAMES = {
    0: "عضو 🙍‍♂️",
    1: "مميز 🌟",
    2: "ادمن 👮‍♂️",
    3: "مدير 💼",
    4: "منشئ 🎖️",
    5: "منشئ اساسي 🏅",
    6: "مالك 👑",
    7: "مالك اساسي 💎",
    99: "المطور الاساسي MG ⚡"
}

LOCK_TYPES = {
    "الروابط": "🔗 الروابط",
    "اليوزرات": "📧 اليوزرات",
    "التوجيه": "↪️ التوجيه",
    "التعديل": "✏️ التعديل",
    "الصور": "🖼️ الصور",
    "الفيديو": "🎥 الفيديو",
    "الملصقات": "🎭 الملصقات",
    "المتحركة": "🎞️ المتحركة",
    "الكلايش": "📜 الكلايش",
    "البوتات": "🤖 البوتات",
    "الفشار": "🤬 الفشار",
    "الدردشة": "💬 الدردشة",
}

SETTING_TYPES = {
    "الترحيب": "👋 الترحيب",
    "الردود": "💬 الردود",
    "الالعاب": "🎮 الألعاب والبنك",
    "الرادار": "🚓 رادار المرور",
}

BAD_WORDS = [
    "كلب", "حمار", "حيوان", "تافه", "غبي", "صايع", "منيك", "قحبة", "شرموط", "عرص", "زبي", "طيز", "كس", "نيك"
]

FUN_TITLES = [
    "ملك", "ملكه", "طلي", "طامس", "عسل", "كيك", "زاحف", "غبي", "بقره", "صخل", "لوكي"
]

QUESTIONS_BANK = {
    "اسئلة": [
        ("ما هي عاصمة ليبيا؟", "طرابلس"),
        ("ما هي العملة الرسمية في ليبيا؟", "الدينار"),
        ("في أي مدينة ليبية تقع آثار لبدة الكبرى؟", "الخمس"),
        ("ما هو اللقب الشهير لمدينة بنغازي؟", "العصية"),
        ("ما هي أكبر مدينة في الجنوب الليبي؟", "سبها"),
        ("كم عدد ألوان علم ليبيا؟", "3"),
    ],
    "لغز": [
        ("شيء يمشي بلا رجلين ويبكي بلا عينين، شنو هو؟", "السحاب"),
        ("له أسنان كثيرة ولا يعض، شنو هو؟", "المشط"),
        ("يكسيني ويكسي الناس وهو عريان، شنو هو؟", "الابرة"),
        ("تذبحه وتبكي عليه، شنو هو؟", "البصل"),
    ],
    "عواصم": [
        ("ما هي عاصمة تونس؟", "تونس"),
        ("ما هي عاصمة مصر؟", "القاهرة"),
        ("ما هي عاصمة الجزائر؟", "الجزائر"),
        ("ما هي عاصمة إيطاليا؟", "روما"),
    ],
    "فكك": [
        ("فكك كلمة: (طرابلس)", "ط ر ا ب ل س"),
        ("فكك كلمة: (بنغازي)", "ب ن غ ا ز ي"),
        ("فكك كلمة: (ليبيا)", "ل ي ب ي ا"),
    ],
    "عكس": [
        ("اعكس كلمة: (سحاب)", "باحس"),
        ("اعكس كلمة: (قمر)", "رمق"),
        ("اعكس كلمة: (علم)", "ملع"),
    ],
    "معاني": [
        ("ما معنى الكلمة الليبية: (كاشيك) بالفصحى؟", "ملعقة"),
        ("ما معنى الكلمة الليبية: (طاسة)؟", "كوب"),
        ("ما معنى الكلمة الليبية: (قعمز)؟", "اجلس"),
    ],
    "امثلة": [
        ("أكمل المثل الليبي: دير الخير وانساه، ودير الشر و...", "توقاه"),
        ("أكمل المثل الليبي: اللي ما يطول العنب يقول عليه...", "حامض"),
    ]
}

# الحالات المؤقتة في الذاكرة
active_games = {}           # chat_id -> {"answer": str, "reward": int}
active_airdrops = {}        # chat_id -> int (amount)
group_msg_counter = {}      # chat_id -> int
pending_whispers = {}       # user_id -> {"chat_id": int, "target_id": int, "target_name": str, "reply_id": int, "expires": int}
active_duels = {}           # duel_id -> {"chat_id": int, "p1": int, "p1_name": str, "p2": int, "p2_name": str, "bet": int}
last_radar_time = {}        # user_id -> int


# ══════════════════════════════════════════════════════════════════
# 🛠️ دوال المساعدة وإدارة البيانات
# ══════════════════════════════════════════════════════════════════

def esc(text: str) -> str:
    return html.escape(str(text or ""))

def get_bot_name() -> str:
    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT val FROM bot_config WHERE key = 'bot_name'").fetchone()
        conn.close()
        return row["val"] if row else BOT_DEFAULT_NAME

def set_bot_name(new_name: str):
    with db_lock:
        conn = get_db()
        conn.execute("INSERT OR REPLACE INTO bot_config (key, val) VALUES ('bot_name', ?)", (new_name,))
        conn.commit()
        conn.close()

def get_current_stock_price(s_name: str) -> int:
    base_p = STOCKS.get(s_name, 150)
    factor = (int(time.time()) // 600) % 7
    return max(50, base_p + (factor * 20) - 50)

def ensure_user(user: types.User) -> dict:
    full_name = (user.first_name or "") + (f" {user.last_name}" if user.last_name else "")
    full_name = full_name.strip() or "مواطن ليبي"
    username = user.username or ""
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
        row = c.fetchone()
        if not row:
            c.execute(
                "INSERT INTO users (user_id, name, username, msg_count, points) VALUES (?, ?, ?, 1, 1)",
                (user.id, full_name, username)
            )
            conn.commit()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
            row = c.fetchone()
        else:
            new_msgs = row["msg_count"] + 1
            new_pts = row["points"] + 1
            new_lvl = row["level"]
            if new_pts >= new_lvl * 50:
                new_lvl += 1
            c.execute(
                "UPDATE users SET name = ?, username = ?, msg_count = ?, points = ?, level = ? WHERE user_id = ?",
                (full_name, username, new_msgs, new_pts, new_lvl, user.id)
            )
            conn.commit()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
            row = c.fetchone()
        data = dict(row)
        conn.close()
        return data

def get_user_by_id(user_id: int) -> dict | None:
    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
        conn.close()
        return dict(row) if row else None

def get_user_by_username(username: str) -> dict | None:
    username = username.lstrip("@").lower()
    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,)).fetchone()
        conn.close()
        return dict(row) if row else None

def resolve_target_user(m: types.Message, text: str) -> dict | None:
    if m.reply_to_message and m.reply_to_message.from_user:
        return ensure_user(m.reply_to_message.from_user)
    for p in text.split():
        if p.startswith("@") and len(p) > 2:
            return get_user_by_username(p)
    return None

def update_user_field(user_id: int, **kwargs):
    if not kwargs:
        return
    cols = ", ".join([f"{k} = ?" for k in kwargs.keys()])
    vals = list(kwargs.values()) + [user_id]
    with db_lock:
        conn = get_db()
        conn.execute(f"UPDATE users SET {cols} WHERE user_id = ?", vals)
        conn.commit()
        conn.close()

def ensure_group(chat: types.Chat) -> dict:
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM groups WHERE chat_id = ?", (chat.id,))
        row = c.fetchone()
        if not row:
            default_settings = {"الترحيب": True, "الردود": True, "الالعاب": True, "الرادار": True}
            c.execute(
                "INSERT INTO groups (chat_id, title, locks, settings) VALUES (?, ?, ?, ?)",
                (chat.id, chat.title or "مجموعة", json.dumps({"الفشار": True}), json.dumps(default_settings))
            )
            conn.commit()
            c.execute("SELECT * FROM groups WHERE chat_id = ?", (chat.id,))
            row = c.fetchone()
        else:
            if chat.title and chat.title != row["title"]:
                c.execute("UPDATE groups SET title = ? WHERE chat_id = ?", (chat.title, chat.id))
                conn.commit()
        data = dict(row)
        conn.close()
        return data

def get_group_json(chat_id: int, col: str, default_val: dict) -> dict:
    with db_lock:
        conn = get_db()
        row = conn.execute(f"SELECT {col} FROM groups WHERE chat_id = ?", (chat_id,)).fetchone()
        conn.close()
        if row and row[col]:
            try:
                return json.loads(row[col])
            except Exception:
                return dict(default_val)
        return dict(default_val)

def set_group_json(chat_id: int, col: str, data: dict):
    with db_lock:
        conn = get_db()
        conn.execute(f"UPDATE groups SET {col} = ? WHERE chat_id = ?", (json.dumps(data), chat_id))
        conn.commit()
        conn.close()

def get_group_locks(chat_id: int) -> dict:
    return get_group_json(chat_id, "locks", {})

def set_group_lock(chat_id: int, lock_name: str, state: bool):
    locks = get_group_locks(chat_id)
    locks[lock_name] = state
    set_group_json(chat_id, "locks", locks)

def get_group_settings(chat_id: int) -> dict:
    return get_group_json(chat_id, "settings", {"الترحيب": True, "الردود": True, "الالعاب": True, "الرادار": True})

def set_group_setting(chat_id: int, s_name: str, state: bool):
    settings = get_group_settings(chat_id)
    settings[s_name] = state
    set_group_json(chat_id, "settings", settings)

def get_rank(chat_id: int, user_id: int) -> int:
    if user_id == ADMIN_ID:
        return 99
    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT rank_level FROM ranks WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)).fetchone()
        conn.close()
        if row and row["rank_level"] > 0:
            return row["rank_level"]
    try:
        member = bot.get_chat_member(chat_id, user_id)
        if member.status == "creator":
            set_rank(chat_id, user_id, 7)
            return 7
        elif member.status == "administrator":
            return 2
    except Exception:
        pass
    return 0

def set_rank(chat_id: int, user_id: int, level: int):
    with db_lock:
        conn = get_db()
        conn.execute(
            "INSERT INTO ranks (chat_id, user_id, rank_level) VALUES (?, ?, ?) "
            "ON CONFLICT(chat_id, user_id) DO UPDATE SET rank_level = ?",
            (chat_id, user_id, level, level)
        )
        conn.commit()
        conn.close()

def get_custom_title(chat_id: int, user_id: int) -> str:
    with db_lock:
        conn = get_db()
        row = conn.execute("SELECT custom_title FROM ranks WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)).fetchone()
        conn.close()
        return row["custom_title"] if row and row["custom_title"] else "بدون لقب"

def set_custom_title(chat_id: int, user_id: int, title: str):
    cur_rank = get_rank(chat_id, user_id)
    if cur_rank == 99:
        cur_rank = 7
    with db_lock:
        conn = get_db()
        conn.execute(
            "INSERT INTO ranks (chat_id, user_id, rank_level, custom_title) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(chat_id, user_id) DO UPDATE SET custom_title = ?",
            (chat_id, user_id, cur_rank, title, title)
        )
        conn.commit()
        conn.close()

def send_with_user_photo(chat_id: int, user_id: int, caption: str, reply_to_message_id: int = None, reply_markup=None):
    try:
        photos = bot.get_user_profile_photos(user_id, limit=1)
        if photos and photos.total_count > 0:
            file_id = photos.photos[0][-1].file_id
            bot.send_photo(chat_id, file_id, caption=caption, reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)
            return
    except Exception:
        pass
    bot.send_message(chat_id, caption, reply_to_message_id=reply_to_message_id, reply_markup=reply_markup)


# ══════════════════════════════════════════════════════════════════
# 📢 فحص الاشتراك الإجباري الصارم
# ══════════════════════════════════════════════════════════════════

def is_channel_member(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    try:
        member = bot.get_chat_member(TARGET_CHANNEL_ID, user_id)
        return member.status not in ("left", "kicked")
    except ApiTelegramException as e:
        if "CHAT_ADMIN_REQUIRED" in str(e) or "chat not found" in str(e).lower():
            return True
        return False
    except Exception:
        return True

def get_subscribe_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(
            f"📢 اشترك في قناة البوت @{CHANNEL_USERNAME}",
            url=f"https://t.me/{CHANNEL_USERNAME}"
        ),
        types.InlineKeyboardButton(
            "✅ تم الاشتراك — تحقّق الآن",
            callback_data="check_sub"
        )
    )
    return kb


# ══════════════════════════════════════════════════════════════════
# 🎨 الواجهات الفخمة والأزرار التفاعلية (مطابقة للصور)
# ══════════════════════════════════════════════════════════════════

def get_private_start_kb(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("قناه البوت", url=f"https://t.me/{CHANNEL_USERNAME}"),
        types.InlineKeyboardButton("اضفني لمجموعتك ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"),
    )
    kb.row(
        types.InlineKeyboardButton("المطور", url=f"tg://user?id={ADMIN_ID}"),
        types.InlineKeyboardButton("لتنصيب بوت", callback_data="install_bot_info"),
    )
    kb.row(
        types.InlineKeyboardButton("اوامر الاعضاء", callback_data="private_member_cmds"),
    )
    if user_id == ADMIN_ID:
        kb.row(
            types.InlineKeyboardButton("⚡ لوحة المطور الأساسي MG", callback_data="menu_dev"),
        )
    kb.row(
        types.InlineKeyboardButton("ARKAN SOURCE ™ ® 🇱🇾", url=f"https://t.me/{CHANNEL_USERNAME}"),
    )
    return kb

def get_commands_kb(user_id: int = 0) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("م1", callback_data="menu_1"),
        types.InlineKeyboardButton("م2", callback_data="menu_2"),
        types.InlineKeyboardButton("م3", callback_data="menu_3"),
        types.InlineKeyboardButton("م4", callback_data="menu_4"),
        types.InlineKeyboardButton("م5", callback_data="menu_5"),
        types.InlineKeyboardButton("م6", callback_data="menu_6"),
        types.InlineKeyboardButton("م7", callback_data="menu_7"),
        types.InlineKeyboardButton("م8", callback_data="menu_8"),
        types.InlineKeyboardButton("م9", callback_data="menu_9"),
    )
    if user_id == ADMIN_ID:
        kb.row(
            types.InlineKeyboardButton("الالعاب", callback_data="menu_games"),
            types.InlineKeyboardButton("م المطور", callback_data="menu_dev"),
        )
    else:
        kb.row(
            types.InlineKeyboardButton("الالعاب", callback_data="menu_games"),
        )
    kb.row(
        types.InlineKeyboardButton("القفل / الفتح", callback_data="locks_panel"),
        types.InlineKeyboardButton("التفعيل/ التعطيل", callback_data="settings_panel"),
    )
    kb.row(
        types.InlineKeyboardButton("ARKAN SOURCE ™ ® 🇱🇾", url=f"https://t.me/{CHANNEL_USERNAME}")
    )
    return kb

def build_bank_secret_kb(owner_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("💳 كشف رصيد المصرف السري (فوري)", callback_data=f"secretbank_{owner_id}"),
        types.InlineKeyboardButton("📩 إرسال كشف الحساب المفصل للخاص", callback_data=f"dmbank_{owner_id}")
    )
    return kb

MENU_TEXTS = {
    "main": (
        "▽ : <b>أوامر البوت ({bot_name}) الرئيسية :</b>\n"
        "──────────────\n"
        "▽ : <b>م1</b> ↞ أوامر الحماية والقفل والفتح\n"
        "▽ : <b>م2</b> ↞ أوامر ادمنية المجموعة\n"
        "▽ : <b>م3</b> ↞ أوامر المدراء والردود والاختصارات\n"
        "▽ : <b>م4</b> ↞ أوامر المنشئين\n"
        "▽ : <b>م5</b> ↞ أوامر المالكين\n"
        "▽ : <b>م6</b> ↞ أوامر التحشيش والألقاب\n"
        "▽ : <b>م7</b> ↞ أوامر التسلية والهمسة والزواج\n"
        "▽ : <b>م8</b> ↞ البنك الليبي والحياة الواقعية والسوق الحر\n"
        "▽ : <b>م9</b> ↞ أوامر التنظيف والمسح\n"
        "──────────────\n"
        "▽ : نادِ البوت باسمه (<b>{bot_name}</b>) أو تصفح بالأزرار أدناه :"
    ),
    "menu_1": (
        "▽ : <b>م1 ↞ أوامر الحماية (القفل والفتح) :</b>\n"
        "──────────────\n"
        "▽ : <code>قفل</code> ، <code>فتح</code> + الأمر :\n"
        "▽ : الروابط • اليوزرات • التوجيه • التعديل\n"
        "▽ : الصور • الفيديو • الملصقات • المتحركة\n"
        "▽ : الكلايش • البوتات • الفشار • الدردشة\n"
        "──────────────\n"
        "▽ : ارسل <code>الحماية</code> لفتح لوحة القفل والفتح بالأزرار"
    ),
    "menu_2": (
        "▽ : <b>م2 ↞ أوامر ادمنية المجموعة :</b>\n"
        "──────────────\n"
        "▽ : <code>حظر</code> • <code>الغاء حظر</code> • <code>طرد</code> (بالرد)\n"
        "▽ : <code>كتم</code> • <code>الغاء كتم</code> • <code>انذار</code> • <code>حذف الانذارات</code>\n"
        "▽ : <code>تثبيت</code> • <code>الغاء تثبيت</code> (بالرد)\n"
        "▽ : <code>كشف</code> • <code>ايدي</code> (أو <code>ا</code>) • <code>صورتي</code> (أو <code>ص</code>)\n"
        "▽ : <code>رتبتي</code> • <code>لقبي</code> • <code>رفع مميز</code> • <code>تنزيل مميز</code>"
    ),
    "menu_3": (
        "▽ : <b>م3 ↞ أوامر المدراء والردود والاختصارات :</b>\n"
        "──────────────\n"
        "▽ : <code>رفع ادمن</code> • <code>تنزيل ادمن</code> (بالرد)\n"
        "▽ : <code>اضف رد الكلمة=الجواب</code> • <code>مسح رد الكلمة</code>\n"
        "▽ : <code>الردود</code> • <code>مسح الردود</code>\n"
        "▽ : <code>اضف اختصار الحرف=الامر</code> • <code>مسح اختصار الحرف</code> • <code>الاختصارات</code>\n"
        "▽ : <code>ضع ترحيب</code> + النص • <code>ضع قوانين</code> + النص • <code>القوانين</code>"
    ),
    "menu_4": (
        "▽ : <b>م4 ↞ أوامر المنشئين :</b>\n"
        "──────────────\n"
        "▽ : <code>رفع مدير</code> • <code>تنزيل مدير</code> (بالرد)\n"
        "▽ : <code>المدراء</code> • <code>المنشئين</code> • <code>الادمنية</code> • <code>المميزين</code>\n"
        "▽ : <code>تنزيل الكل</code>"
    ),
    "menu_5": (
        "▽ : <b>م5 ↞ أوامر المالكين :</b>\n"
        "──────────────\n"
        "▽ : <code>تفعيل</code> أو <code>رفع نفسي مالك</code> (لمنشئ المجموعة)\n"
        "▽ : <code>رفع مالك</code> • <code>تنزيل مالك</code>\n"
        "▽ : <code>رفع منشئ</code> • <code>تنزيل منشئ</code>\n"
        "▽ : <code>ضع لقب</code> + اللقب (بالرد) • <code>المالكين</code>"
    ),
    "menu_6": (
        "▽ : <b>م6 ↞ أوامر التحشيش والألقاب :</b>\n"
        "──────────────\n"
        "▽ : <code>رفع ملك</code> • <code>رفع ملكه</code> • <code>رفع عسل</code> • <code>رفع طلي</code> • <code>رفع زاحف</code>\n"
        "▽ : <code>نسبة الحب</code> • <code>نسبة الذكاء</code> • <code>نسبة الجمال</code> (بالرد)\n"
        "▽ : <code>شنو رايك بهذا</code> • <code>رزله</code> • <code>انطي هدية</code> (بالرد)\n"
        "▽ : <code>ص</code> أو <code>صورتي</code> ↞ تقييم جمال صورتك الشخصية"
    ),
    "menu_7": (
        "▽ : <b>م7 ↞ أوامر التسلية والهمسة والزواج :</b>\n"
        "──────────────\n"
        "▽ : <code>همسه</code> أو <code>همسة</code> (بالرد) ↞ همسة سرية بزر خاص\n"
        "▽ : <code>زواج</code> + المهر (بالرد) • <code>طلاق</code> • <code>خلع</code> • <code>زواجي</code>\n"
        "▽ : <code>غنيلي</code> • <code>شعر</code> • <code>نكتة</code> • <code>اذكار</code> • <code>لو خيروك</code> • <code>صراحة</code>"
    ),
    "menu_8": (
        "▽ : <b>م8 ↞ البنك الليبي والحياة الواقعية والسوق الحر :</b>\n"
        "──────────────\n"
        "▽ : <code>انشاء حساب</code> • <code>حسابي</code> • <code>فلوسي</code> (الكاش عام والمصرف سري 🔒)\n"
        "▽ : <code>ايداع</code> + المبلغ/الكل • <code>سحب</code> + المبلغ/الكل • <code>تحويل</code> + المبلغ (بالرد)\n"
        "▽ : <code>قرض</code> • <code>تسديد القرض</code>\n"
        "▽ : <code>الوظائف</code> • <code>وظيفة</code> + المهنة • <code>راتب</code>\n"
        "▽ : <code>علاج</code> • <code>تصليح</code> • <code>قبض</code> • <code>اختراق صراف</code> • <code>حماية حساب</code>\n"
        "▽ : <code>المدن</code> • <code>سفر</code> + المدينة • <code>تهريب بضاعة</code>\n"
        "▽ : <code>العقارات</code> • <code>شراء بيت</code> + الاسم • <code>بيع بيت</code>\n"
        "▽ : <code>السيارات</code> • <code>شراء سيارة</code> + الاسم • <code>بيع سيارة</code> • <code>سباق</code> (بالرد)\n"
        "▽ : <code>المشاريع</code> • <code>فتح مشروع</code> + الاسم • <code>تحصيل ارباح</code>\n"
        "▽ : <code>البورصة</code> • <code>شراء اسهم</code> + الشركة والعدد • <code>بيع اسهم</code> + الشركة\n"
        "▽ : <code>السوق الحر</code> • <code>عرض بيت للبيع</code> + السعر • <code>عرض سيارة للبيع</code> + السعر\n"
        "▽ : <code>شراء معروض</code> + الرقم • <code>الغاء عرض</code> + الرقم\n"
        "▽ : <code>سرقة</code> (بالرد) • <code>سرقة المصرف</code> • <code>تحدي</code> + المبلغ (بالرد)\n"
        "▽ : <code>دفع كفالة</code> • <code>رشوة العساس</code> • <code>تهريب</code> (بالرد لإنقاذ صديقك)\n"
        "▽ : <code>توب الفلوس</code> • <code>توب الحرامية</code> • <code>توب التفاعل</code>"
    ),
    "menu_9": (
        "▽ : <b>م9 ↞ أوامر التنظيف والمسح :</b>\n"
        "──────────────\n"
        "▽ : <code>مسح</code> (بالرد لحذف رسالة)\n"
        "▽ : <code>مسح</code> + العدد (مثال: <code>مسح 20</code>)\n"
        "▽ : <code>اطردني</code>"
    ),
    "menu_games": (
        "▽ : <b>أوامر الألعاب والمسابقات :</b>\n"
        "──────────────\n"
        "▽ : <code>اسئلة</code> • <code>لغز</code> • <code>عواصم</code> • <code>فكك</code> • <code>عكس</code> • <code>معاني</code> • <code>امثلة</code> • <code>رياضيات</code>\n"
        "▽ : <code>حجرة</code> / <code>ورقة</code> / <code>مقص</code>\n"
        "▽ : <code>حظ</code> + المبلغ • <code>مضاربة</code> + المبلغ • <code>استثمار</code> + المبلغ\n"
        "▽ : <code>اكشط</code> + الكود"
    ),
    "menu_dev": (
        "⚡ <b>لوحة المطور الأساسي (MG) السرية :</b>\n"
        "──────────────\n"
        "▽ : <code>تغيير اسم البوت</code> + الاسم الجديد\n"
        "▽ : <code>اضف فلوس</code> + المبلغ (بالرد)\n"
        "▽ : <code>تصفير فلوسه</code> (بالرد)\n"
        "▽ : <code>اطلاق سراح</code> (بالرد)\n"
        "▽ : <code>صنع اكشطها</code> + الكود + المبلغ • <code>قائمة اكشطها</code>\n"
        "▽ : <code>الهمسات</code> (عرض آخر الهمسات السرية)\n"
        "▽ : <code>الاحصائيات</code> • <code>اذاعة</code> + النص\n"
        "▽ : <code>نسخة احتياطية</code> • <code>استعادة</code> (بالرد على ملف قاعدة البيانات)"
    )
}

def render_menu(key: str) -> str:
    return MENU_TEXTS[key].replace("{bot_name}", esc(get_bot_name()))

def build_locks_kb(chat_id: int, user_id: int = 0) -> types.InlineKeyboardMarkup:
    locks = get_group_locks(chat_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, label in LOCK_TYPES.items():
        status = "🔒" if locks.get(key, False) else "🔓"
        buttons.append(
            types.InlineKeyboardButton(f"{label} : {status}", callback_data=f"togglelock_{key}")
        )
    kb.add(*buttons)
    kb.row(types.InlineKeyboardButton("🔙 رجوع للأوامر", callback_data="menu_main"))
    return kb

def build_settings_kb(chat_id: int) -> types.InlineKeyboardMarkup:
    settings = get_group_settings(chat_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, label in SETTING_TYPES.items():
        status = "✅ مفعل" if settings.get(key, True) else "❌ معطل"
        buttons.append(
            types.InlineKeyboardButton(f"{label} : {status}", callback_data=f"toggleset_{key}")
        )
    kb.add(*buttons)
    kb.row(types.InlineKeyboardButton("🔙 رجوع للأوامر", callback_data="menu_main"))
    return kb


# ══════════════════════════════════════════════════════════════════
# 🛡️ أحداث دخول الأعضاء، التعديل، والميديا
# ══════════════════════════════════════════════════════════════════

@bot.message_handler(content_types=["new_chat_members"])
def on_new_member(m: types.Message):
    if m.chat.type not in ("group", "supergroup"):
        return
    grp = ensure_group(m.chat)
    locks = get_group_locks(m.chat.id)
    settings = get_group_settings(m.chat.id)
    b_name = get_bot_name()

    for new_user in m.new_chat_members:
        if new_user.is_bot:
            try:
                me_id = bot.get_me().id
            except Exception:
                me_id = 0
            if new_user.id == me_id:
                bot.send_message(
                    m.chat.id,
                    (
                        f"▽ : <b>تم إضافة البوت ({esc(b_name)}) بنجاح 🇱🇾</b>\n"
                        f"▽ : ارفع البوت مشرفاً ثم ارسل <code>تفعيل</code> أو <code>رفع نفسي مالك</code>\n"
                        f"▽ : لعرض الأوامر ارسل <code>الاوامر</code>"
                    ),
                    reply_markup=get_commands_kb(m.from_user.id if m.from_user else 0)
                )
            elif locks.get("البوتات", False) and get_rank(m.chat.id, m.from_user.id) < 2:
                try:
                    bot.ban_chat_member(m.chat.id, new_user.id)
                except Exception:
                    pass
        else:
            ensure_user(new_user)
            if settings.get("الترحيب", True) and grp.get("welcome_enabled", 1):
                w_text = grp.get("welcome_text") or "مرحبتين بيك يا غالي نورت القروب 🇱🇾"
                bot.reply_to(
                    m,
                    f"▽ : أهلاً بك يا <a href='tg://user?id={new_user.id}'>{esc(new_user.first_name)}</a>\n"
                    f"▽ : {esc(w_text)}"
                )

@bot.edited_message_handler(func=lambda m: m.chat.type in ("group", "supergroup"))
def on_message_edited(m: types.Message):
    if get_rank(m.chat.id, m.from_user.id) >= 1:
        return
    locks = get_group_locks(m.chat.id)
    if locks.get("التعديل", False):
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except Exception:
            pass

@bot.message_handler(content_types=["photo", "video", "sticker", "animation", "document", "voice", "audio"])
def media_handler(m: types.Message):
    if m.chat.type not in ("group", "supergroup"):
        return
    if get_rank(m.chat.id, m.from_user.id) >= 1:
        return
    locks = get_group_locks(m.chat.id)
    del_msg = False
    if locks.get("الدردشة"):
        del_msg = True
    elif (m.forward_from or m.forward_from_chat) and locks.get("التوجيه"):
        del_msg = True
    elif m.content_type == "photo" and locks.get("الصور"):
        del_msg = True
    elif m.content_type == "video" and locks.get("الفيديو"):
        del_msg = True
    elif m.content_type == "sticker" and locks.get("الملصقات"):
        del_msg = True
    elif m.content_type == "animation" and locks.get("المتحركة"):
        del_msg = True
    if del_msg:
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
# ✨ واجهة الخاص الفخمة (/start) ونظام الهمسة السرية بالخاص
# ══════════════════════════════════════════════════════════════════

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message):
    user = m.from_user
    u = ensure_user(user)
    b_name = get_bot_name()
    parts = (m.text or "").split(maxsplit=1)

    if not is_channel_member(user.id):
        bot.reply_to(
            m,
            f"▽ : عذراً يا <b>{esc(u['name'])}</b>!\n"
            f"▽ : يجب عليك الاشتراك في قناة البوت الرسمية @{CHANNEL_USERNAME} أولاً لتتمكن من استخدام البوت.",
            reply_markup=get_subscribe_kb()
        )
        return

    # فحص ما إذا كان الدخول للخاص من أجل كتابة همسة سرية (نفس الصور بالضبط)
    if m.chat.type == "private" and len(parts) > 1 and parts[1].startswith("whisper_"):
        try:
            _, c_id_s, s_id_s, t_id_s, r_id_s = parts[1].split("_")
            c_id, s_id, t_id, r_id = int(c_id_s), int(s_id_s), int(t_id_s), int(r_id_s)
        except Exception:
            bot.reply_to(m, "▽ : عذرا، انتهت صلاحية الهمسة")
            return

        if user.id != s_id:
            bot.reply_to(m, "▽ : عذرا، هذه الهمسة ليست مخصصة لك!")
            return

        target_u = get_user_by_id(t_id)
        t_name = target_u["name"] if target_u else "العضو"
        pending_whispers[user.id] = {
            "chat_id": c_id,
            "target_id": t_id,
            "target_name": t_name,
            "reply_id": r_id,
            "expires": int(time.time()) + 300
        }
        bot.reply_to(m, "▽ : حسناً، ارسل الهمسة الان")
        return

    # في المحادثة الخاصة: عرض الواجهة الفخمة المطابقة للصورة
    if m.chat.type == "private":
        caption = (
            f"▽ : أهلا بك في بوت {esc(b_name)} 🇱🇾\n"
            f"▽ : لحماية المجموعات من التفليش والحياة الواقعية\n"
            f"▽ : يمكنك تفعيل البوت كالاتي :\n"
            f"▽ : اضف البوت وارفعه مشرف في مجموعتك\n"
            f"▽ : ارسل {{ تفعيل }} ليتم تفعيل المجموعه\n"
            f"▽ : يوزر البوت ← {{@{BOT_USERNAME}}}"
        )
        send_with_user_photo(
            m.chat.id,
            user.id,
            caption,
            reply_to_message_id=m.message_id,
            reply_markup=get_private_start_kb(user.id)
        )
        return

    # في المجموعات
    bot.reply_to(
        m,
        render_menu("main"),
        reply_markup=get_commands_kb(user.id)
    )


# ══════════════════════════════════════════════════════════════════
# 🚀 الموجه الرئيسي للرسائل والأوامر
# ══════════════════════════════════════════════════════════════════

@bot.message_handler(content_types=["text"])
def main_text_router(m: types.Message):
    try:
        _process_text(m)
    except Exception as e:
        logging.error("خطأ غير متوقع في معالجة الرسالة: %s", e)

def _process_text(m: types.Message):
    user = m.from_user
    if not user:
        return
    text = (m.text or "").strip()
    chat_id = m.chat.id
    is_group = m.chat.type in ("group", "supergroup")
    b_name = get_bot_name()
    b_name_no_hamza = b_name.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")

    u_data = ensure_user(user)
    now = int(time.time())

    # ─────────────── 1. معالجة المحادثة الخاصة (الذاتية) ───────────────
    if not is_group:
        # إذا كان العضو يكتب همسة سرية حالياً
        if user.id in pending_whispers:
            w_info = pending_whispers.pop(user.id)
            if now > w_info["expires"]:
                bot.reply_to(m, "▽ : عذرا، انتهت صلاحية الهمسة")
                return
            with db_lock:
                conn = get_db()
                c = conn.cursor()
                c.execute(
                    "INSERT INTO whispers (chat_id, sender_id, sender_name, target_id, target_name, text, timestamp) VALUES (?,?,?,?,?,?,?)",
                    (w_info["chat_id"], user.id, u_data["name"], w_info["target_id"], w_info["target_name"], text, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                )
                w_id = c.lastrowid
                conn.commit()
                conn.close()

            if user.id != ADMIN_ID:
                try:
                    bot.send_message(
                        ADMIN_ID,
                        f"🕵️‍♂️ <b>همسة سرية جديدة #{w_id} :</b>\n"
                        f"▽ : من ↞ {esc(u_data['name'])} (<code>{user.id}</code>)\n"
                        f"▽ : إلى ↞ {esc(w_info['target_name'])} (<code>{w_info['target_id']}</code>)\n"
                        f"▽ : النص ↞ <code>{esc(text)}</code>"
                    )
                except Exception:
                    pass

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("• عرض الهمسة •", callback_data=f"whisper_{w_id}"))
            group_msg_text = (
                f"هذه همسة سرية لك ↞ <a href='tg://user?id={w_info['target_id']}'>{esc(w_info['target_name'])}</a>\n"
                f"الهمسة من ↞ <a href='tg://user?id={user.id}'>{esc(u_data['name'])}</a>"
            )
            try:
                bot.send_message(
                    w_info["chat_id"],
                    group_msg_text,
                    reply_to_message_id=w_info["reply_id"] if w_info["reply_id"] else None,
                    reply_markup=kb
                )
            except Exception:
                bot.send_message(w_info["chat_id"], group_msg_text, reply_markup=kb)

            bot.reply_to(m, "▽ : تم ارسالها بنجاح بالمجموعة")
            return

        # أوامر المطور الأساسي مسموحة في الخاص أيضاً
        if user.id == ADMIN_ID and (
            text in ("م المطور", "الهمسات", "الاحصائيات", "نسخة احتياطية", "قائمة اكشطها", "استعادة")
            or text.startswith(("تغيير اسم البوت ", "صنع اكشطها ", "اذاعة "))
        ):
            _handle_dev_commands(m, text, u_data)
            return

        # أي رسالة أخرى في الخاص تعرض الواجهة الفخمة فقط (ممنوع اللعب في الخاص)
        if not is_channel_member(user.id):
            bot.reply_to(
                m,
                f"▽ : اشترك في قناة البوت @{CHANNEL_USERNAME} أولاً لتتمكن من استخدام البوت!",
                reply_markup=get_subscribe_kb()
            )
            return

        caption = (
            f"▽ : أهلا بك في بوت {esc(b_name)} 🇱🇾\n"
            f"▽ : لحماية المجموعات من التفليش والحياة الواقعية\n"
            f"▽ : يمكنك تفعيل البوت كالاتي :\n"
            f"▽ : اضف البوت وارفعه مشرف في مجموعتك\n"
            f"▽ : ارسل {{ تفعيل }} ليتم تفعيل المجموعه\n"
            f"▽ : يوزر البوت ← {{@{BOT_USERNAME}}}"
        )
        send_with_user_photo(
            chat_id,
            user.id,
            caption,
            reply_to_message_id=m.message_id,
            reply_markup=get_private_start_kb(user.id)
        )
        return

    # ─────────────── 2. معالجة المجموعات (الحماية والأحداث) ───────────────
    grp_data = ensure_group(m.chat)
    user_rank = get_rank(chat_id, user.id)
    locks = get_group_locks(chat_id)
    settings = get_group_settings(chat_id)

    # تطبيق أقفال الحماية الصامتة على الأعضاء العاديين
    if user_rank == 0:
        del_msg = False
        if locks.get("الدردشة"):
            del_msg = True
        elif (m.forward_from or m.forward_from_chat) and locks.get("التوجيه"):
            del_msg = True
        elif locks.get("الروابط") and re.search(r"(https?://|t\.me/|telegram\.me/|www\.)", text, re.I):
            del_msg = True
        elif locks.get("اليوزرات") and "@" in text:
            del_msg = True
        elif locks.get("الكلايش") and len(text) > 450:
            del_msg = True
        elif locks.get("الفشار") and any(bw in text.split() for bw in BAD_WORDS):
            del_msg = True

        if del_msg:
            try:
                bot.delete_message(chat_id, m.message_id)
            except Exception:
                pass
            return

    # التقاط حقيبة الفلوس العشوائية في الشارع (لحق)
    if text == "لحق" and chat_id in active_airdrops:
        bag_amount = active_airdrops.pop(chat_id)
        update_user_field(user.id, cash=u_data["cash"] + bag_amount)
        bot.reply_to(
            m,
            f"🏃‍♂️💨 <b>كفو يا ذيب ({esc(u_data['name'])})!</b>\n"
            f"▽ : سبقت الكل ولحقت على حقيبة الفلوس في الشارع!\n"
            f"▽ : ربحت <b>{bag_amount} د.ل</b> كاش في جيبك 💵🔥"
        )
        return

    # التقاط إجابات المسابقات الفورية
    if chat_id in active_games:
        game = active_games[chat_id]
        if text == game["answer"]:
            reward = game["reward"]
            del active_games[chat_id]
            update_user_field(user.id, cash=u_data["cash"] + reward, points=u_data["points"] + 5)
            bot.reply_to(
                m,
                f"🎉 <b>إجابة صحيحة وسريعة يا {esc(u_data['name'])}!</b>\n"
                f"▽ : ربحت <b>{reward} د.ل</b> كاش + 5 نقاط تفاعل ⭐"
            )
            return

    # عداد رسائل المجموعة لرمي حقيبة فلوس عشوائية (AirDrop) + رادار المرور
    if settings.get("الالعاب", True):
        group_msg_counter[chat_id] = group_msg_counter.get(chat_id, 0) + 1
        if group_msg_counter[chat_id] >= 40 and chat_id not in active_airdrops:
            group_msg_counter[chat_id] = 0
            bag_val = random.choice([1000, 1500, 2000, 2500, 3000])
            active_airdrops[chat_id] = bag_val
            try:
                bot.send_message(
                    chat_id,
                    f"🚨💼 <b>حدث طارئ في الشارع العام!</b>\n"
                    f"──────────────\n"
                    f"▽ : طاحت حقيبة فلوس فيها <b>{bag_val} د.ل</b> كاش!\n"
                    f"▽ : أول شخص يكتب كلمة ( <code>لحق</code> ) يأخذها كلها فوراً! 🏃‍♂️💨"
                )
            except Exception:
                pass

    # رادار المرور العشوائي لأصحاب السيارات (غير مزعج وبفترة تباعد)
    if (
        settings.get("الرادار", True)
        and u_data["car"] != "بدون سيارة"
        and now - last_radar_time.get(user.id, 0) > 1800
        and random.randint(1, 100) <= 3
    ):
        last_radar_time[user.id] = now
        fine = random.choice([150, 200, 250, 300])
        if u_data["cash"] >= fine:
            u_data["cash"] -= fine
            update_user_field(user.id, cash=u_data["cash"])
            bot.reply_to(
                m,
                f"🚓📸 <b>رادار الطريق الساحلي صوّرك!</b>\n"
                f"▽ : كنت تجري بسيارتك (<b>{esc(u_data['car'])}</b>) بسرعة جنونية!\n"
                f"▽ : تم خصم مخالفة مرورية بقيمة <b>{fine} د.ل</b> من كاش جيبك 💸"
            )
        elif u_data["bank_balance"] >= fine:
            u_data["bank_balance"] -= fine
            update_user_field(user.id, bank_balance=u_data["bank_balance"])
            bot.reply_to(
                m,
                f"🚓📸 <b>رادار الطريق الساحلي صوّرك!</b>\n"
                f"▽ : كنت تجري بسيارتك (<b>{esc(u_data['car'])}</b>) بسرعة جنونية!\n"
                f"▽ : تم خصم مخالفة مرورية بقيمة <b>{fine} د.ل</b> من حسابك المصرفي 🏦"
            )

    # مناداة البوت باسمه
    if text in ("بوت", "يا بوت", "يابوت", b_name, f"يا {b_name}", f"يا{b_name}", b_name_no_hamza, f"يا {b_name_no_hamza}"):
        bot.reply_to(m, random.choice(BOT_CALL_REPLIES).format(name=esc(b_name)))
        return

    # إزالة بادئة اسم البوت لو نادى البوت مع الأمر (مثال: أركان حسابي)
    for prefix in (b_name + " ", b_name_no_hamza + " ", "بوت "):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    # تحويل الاختصارات المخصصة للمجموعة والاختصارات الثابتة (ا، ص)
    shortcuts = get_group_json(chat_id, "shortcuts", {})
    if text in shortcuts:
        text = shortcuts[text]
    elif text == "ا":
        text = "ايدي"
    elif text in ("ص", "جمال صورتي"):
        text = "صورتي"

    # الردود المخصصة للمجموعة
    if settings.get("الردود", True):
        custom_replies = get_group_json(chat_id, "replies", {})
        if text in custom_replies:
            bot.reply_to(m, custom_replies[text])
            return

    # قائمة الكلمات المفتاحية للأوامر لفحص الاشتراك الإجباري
    COMMAND_TRIGGERS = (
        "الاوامر", "أوامر", "اوامر", "م1", "م2", "م3", "م4", "م5", "م6", "م7", "م8", "م9", "م المطور",
        "الحماية", "الاعدادات", "الالعاب", "انشاء حساب", "فتح حساب", "حسابي", "فلوسي", "البنك", "راتب", "خدمة", "بخشيش",
        "ايداع", "سحب", "تحويل", "قرض", "تسديد القرض", "الوظائف", "وظيفة", "علاج", "بيع دواء", "قبض",
        "تصليح", "اختراق صراف", "حماية حساب", "المدن", "سفر", "تهريب بضاعة", "العقارات", "شراء بيت", "بيع بيت",
        "السيارات", "شراء سيارة", "بيع سيارة", "سباق", "المشاريع", "فتح مشروع", "تحصيل ارباح", "البورصة",
        "شراء اسهم", "بيع اسهم", "اسهمي", "السوق الحر", "عرض بيت للبيع", "عرض سيارة للبيع", "شراء معروض", "الغاء عرض",
        "سرقة", "سرقة المصرف", "دفع كفالة", "رشوة العساس", "تهريب", "تحدي",
        "همسة", "همسه", "رفع", "تنزيل", "قفل", "فتح", "حظر", "الغاء حظر", "طرد", "اطردني", "كتم", "الغاء كتم", "انذار", "حذف الانذارات",
        "مسح", "تثبيت", "الغاء تثبيت", "كشف", "ايدي", "صورتي", "رتبتي", "لقبي", "ضع لقب", "تصفير الرتب",
        "المالكين", "المنشئين", "المدراء", "الادمنية", "المميزين", "الردود", "مسح الردود", "اضف رد", "مسح رد",
        "اضف اختصار", "مسح اختصار", "الاختصارات", "تفعيل",
        "ضع ترحيب", "تفعيل الترحيب", "تعطيل الترحيب", "ضع قوانين", "القوانين",
        "زواج", "طلاق", "خلع", "زواجي", "غنيلي", "شعر", "قصيدة", "نكتة", "نكته", "اذكار", "لو خيروك", "صراحة",
        "حجرة", "ورقة", "مقص", "شنو رايك بهذا", "رزله", "انطي هدية", "نسبة",
        "اسئلة", "لغز", "عواصم", "فكك", "عكس", "معاني", "امثلة", "رياضيات", "حظ", "مضاربة", "استثمار", "اكشط", "قائمة اكشطها",
        "توب", "اضف فلوس", "تصفير فلوسه", "الهمسات", "اذاعة", "نسخة احتياطية", "استعادة", "الاحصائيات", "اطلاق سراح", "تغيير اسم البوت", "صنع اكشطها"
    )

    is_cmd = any(text == trig or text.startswith(trig + " ") for trig in COMMAND_TRIGGERS)
    if is_cmd and not is_channel_member(user.id):
        bot.reply_to(
            m,
            f"▽ : عذراً يا <b>{esc(u_data['name'])}</b>!\n"
            f"▽ : اشترك في قناة البوت @{CHANNEL_USERNAME} أولاً لتشغيل الأوامر.",
            reply_markup=get_subscribe_kb()
        )
        return

    # ─────────────── 3. أوامر القوائم، الأيدي بالصورة، والهمسة ───────────────

    if text in ("الاوامر", "اوامر", "أوامر"):
        bot.reply_to(m, render_menu("main"), reply_markup=get_commands_kb(user.id))
        return

    if text == "م المطور":
        if user.id != ADMIN_ID:
            bot.reply_to(m, "▽ : 🚫 هذا القسم خاص بالمطور الأساسي (MG) فقط ولا يمكنك رؤيته!")
            return
        bot.reply_to(m, render_menu("menu_dev"), reply_markup=get_commands_kb(user.id))
        return

    for i in range(1, 10):
        if text == f"م{i}":
            bot.reply_to(m, render_menu(f"menu_{i}"), reply_markup=get_commands_kb(user.id))
            return

    if text == "الالعاب":
        bot.reply_to(m, render_menu("menu_games"), reply_markup=get_commands_kb(user.id))
        return

    if text == "الحماية":
        if user_rank < 2:
            bot.reply_to(m, "▽ : ❌ هذا الأمر مخصص للادمنية فما فوق!")
            return
        bot.reply_to(m, f"▽ : لوحة القفل والفتح لبوت ({esc(b_name)}) :", reply_markup=build_locks_kb(chat_id, user.id))
        return

    if text == "الاعدادات":
        if user_rank < 3:
            bot.reply_to(m, "▽ : ❌ هذا الأمر مخصص للمدراء فما فوق!")
            return
        bot.reply_to(m, f"▽ : لوحة التفعيل والتعطيل لبوت ({esc(b_name)}) :", reply_markup=build_settings_kb(chat_id))
        return

    # الهمسة المطابقة للصور 100% (عند الرد بكلمة همسه / همسة)
    if text in ("همسه", "همسة"):
        if not m.reply_to_message or not m.reply_to_message.from_user:
            bot.reply_to(m, "▽ : قم بالرد على رسالة الشخص الذي تريد إرسال همسة له واكتب <code>همسه</code>")
            return
        target = m.reply_to_message.from_user
        if target.is_bot:
            bot.reply_to(m, "▽ : لا يمكنك إرسال همسة إلى بوت!")
            return
        ensure_user(target)
        deep_url = f"https://t.me/{BOT_USERNAME}?start=whisper_{chat_id}_{user.id}_{target.id}_{m.reply_to_message.message_id}"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("• اضغط هنا لكتابة الهمسة •", url=deep_url))
        bot.reply_to(
            m,
            f"▽ : تم تحديد الهمسه الى « <a href='tg://user?id={target.id}'>{esc(target.first_name)}</a> »\n\n"
            f"▽ : اضغط على الزر لكتابه الهمسه",
            reply_markup=kb
        )
        return

    # دعم الهمسة السريعة مع النص (همسة + كلام بالرد)
    if (text.startswith("همسة ") or text.startswith("همسه ")) and m.reply_to_message:
        s_msg = text.split(maxsplit=1)[1].strip()
        target = m.reply_to_message.from_user
        try:
            bot.delete_message(chat_id, m.message_id)
        except Exception:
            pass
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute(
                "INSERT INTO whispers (chat_id, sender_id, sender_name, target_id, target_name, text, timestamp) VALUES (?,?,?,?,?,?,?)",
                (chat_id, user.id, u_data["name"], target.id, target.first_name, s_msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            w_id = c.lastrowid
            conn.commit()
            conn.close()
        if user.id != ADMIN_ID:
            try:
                bot.send_message(ADMIN_ID, f"🕵️‍♂️ همسة #{w_id}\nمن: {u_data['name']} ⬅️ {target.first_name}\nالنص: {s_msg}")
            except Exception:
                pass
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("• عرض الهمسة •", callback_data=f"whisper_{w_id}"))
        bot.send_message(
            chat_id,
            f"هذه همسة سرية لك ↞ <a href='tg://user?id={target.id}'>{esc(target.first_name)}</a>\n"
            f"الهمسة من ↞ <a href='tg://user?id={user.id}'>{esc(u_data['name'])}</a>",
            reply_to_message_id=m.reply_to_message.message_id,
            reply_markup=kb
        )
        return

    # أمر الأيدي بالصورة (ايدي / ا)
    if text in ("ايدي", "معلوماتي", "رتبتي", "لقبي"):
        c_title = get_custom_title(chat_id, user.id)
        caption = (
            f"▽ : <b>البطاقة الشخصية للمواطن 🇱🇾</b>\n"
            f"──────────────\n"
            f"▽ : الاسم ↞ <b>{esc(u_data['name'])}</b>\n"
            f"▽ : الايدي ↞ <code>{user.id}</code>\n"
            f"▽ : الرتبة ↞ <b>{RANK_NAMES.get(user_rank, 'عضو 🙍‍♂️')}</b>\n"
            f"▽ : اللقب ↞ <b>{esc(c_title)}</b>\n"
            f"▽ : الكاش في الجيب ↞ <b>{u_data['cash']} د.ل</b> 💵\n"
            f"▽ : رصيد المصرف ↞ <b>🔒 مشفر (سري)</b>\n"
            f"▽ : المستوى ↞ <b>{u_data['level']}</b> (نقاط التفاعل: {u_data['points']})\n"
            f"▽ : الرسائل ↞ <b>{u_data['msg_count']}</b> رسالة"
        )
        send_with_user_photo(chat_id, user.id, caption, reply_to_message_id=m.message_id, reply_markup=build_bank_secret_kb(user.id))
        return

    # أمر تقييم جمال الصورة الشخصية (ص / صورتي)
    if text == "صورتي":
        pct = 100 if user.id == ADMIN_ID else random.randint(68, 100)
        comp = random.choice(BEAUTY_COMPLIMENTS)
        caption = (
            f"▽ : <b>فحص جمال الصورة الشخصية 📸✨</b>\n"
            f"──────────────\n"
            f"▽ : العضو ↞ <b>{esc(u_data['name'])}</b>\n"
            f"▽ : نسبة الجمال ↞ <b>{pct}%</b> 🔥\n"
            f"▽ : التقييم ↞ {comp}"
        )
        send_with_user_photo(chat_id, user.id, caption, reply_to_message_id=m.message_id)
        return

    # أمر كشف (يعرض الكاش والأملاك في العام، ويبقي رصيد المصرف سرياً)
    if text == "كشف" or text.startswith("كشف @"):
        t_u = resolve_target_user(m, text) or u_data
        t_rank = get_rank(chat_id, t_u["user_id"])
        bot.reply_to(
            m,
            f"▽ : <b>كشف السجل المدني 🇱🇾</b>\n"
            f"──────────────\n"
            f"▽ : المواطن ↞ <b>{esc(t_u['name'])}</b> (<code>{t_u['user_id']}</code>)\n"
            f"▽ : الرتبة ↞ <b>{RANK_NAMES.get(t_rank, 'عضو')}</b>\n"
            f"▽ : المدينة ↞ <b>{t_u['city']}</b> | المهنة ↞ <b>{t_u['job']}</b>\n"
            f"▽ : الصحة ↞ <b>{t_u['hp']}%</b> ❤️ | المستوى ↞ <b>{t_u['level']}</b>\n"
            f"▽ : الكاش في الجيب ↞ <b>{t_u['cash']} د.ل</b> 💵\n"
            f"▽ : رصيد المصرف ↞ <b>🔒 سري خاص بالعميل</b>\n"
            f"▽ : السكن ↞ <b>{t_u['house']}</b>\n"
            f"▽ : السيارة ↞ <b>{t_u['car']}</b>\n"
            f"▽ : المشروع ↞ <b>{t_u['business']}</b>"
        )
        return

    # ─────────────── 4. أوامر الإدارة والرتب والردود والاختصارات ───────────────

    if text in ("تفعيل", "رفع نفسي مالك", "ترقية نفسي", "تفعيل البوت", "ارفعني مالك"):
        try:
            member = bot.get_chat_member(chat_id, user.id)
            if member.status == "creator" or user.id == ADMIN_ID:
                set_rank(chat_id, user.id, 7)
                bot.reply_to(
                    m,
                    f"▽ : تم تفعيل المجموعة بنجاح 🇱🇾\n"
                    f"▽ : تم رفعك إلى رتبة <b>مالك اساسي 💎</b> يا {esc(u_data['name'])}"
                )
            else:
                bot.reply_to(m, "▽ : ❌ هذا الأمر مخصص لمنشئ المجموعة الأصلي فقط!")
        except Exception:
            bot.reply_to(m, "▽ : ⚠️ ارفع البوت مشرفاً في المجموعة أولاً!")
        return

    if text.startswith("قفل ") or text.startswith("فتح "):
        if user_rank < 2:
            bot.reply_to(m, "▽ : ❌ هذا الأمر للادمنية فما فوق!")
            return
        act = text.split()[0]
        t_lock = text[len(act):].strip()
        if t_lock in LOCK_TYPES:
            set_group_lock(chat_id, t_lock, act == "قفل")
            bot.reply_to(m, f"▽ : تم {'قفل 🔒' if act == 'قفل' else 'فتح 🔓'} <b>{t_lock}</b> بنجاح!")
        return

    RANK_CMDS = {
        "رفع مالك": (7, 6, "مالك 👑"), "تنزيل مالك": (7, 0, "عضو 🙍‍♂️"),
        "رفع منشئ اساسي": (6, 5, "منشئ اساسي 🏅"), "تنزيل منشئ اساسي": (6, 0, "عضو 🙍‍♂️"),
        "رفع منشئ": (5, 4, "منشئ 🎖️"), "تنزيل منشئ": (5, 0, "عضو 🙍‍♂️"),
        "رفع مدير": (4, 3, "مدير 💼"), "تنزيل مدير": (4, 0, "عضو 🙍‍♂️"),
        "رفع ادمن": (3, 2, "ادمن 👮‍♂️"), "تنزيل ادمن": (3, 0, "عضو 🙍‍♂️"),
        "رفع مميز": (2, 1, "مميز 🌟"), "تنزيل مميز": (2, 0, "عضو 🙍‍♂️"),
    }
    for r_cmd, (req_r, new_l, r_t) in RANK_CMDS.items():
        if text == r_cmd or text.startswith(r_cmd + " @"):
            if user_rank < req_r:
                bot.reply_to(m, "▽ : ❌ رتبتك لا تسمح لك بهذا الإجراء!")
                return
            t_u = resolve_target_user(m, text)
            if not t_u:
                bot.reply_to(m, "▽ : 💡 قم بالرد على رسالة العضو أو اكتب يوزره بعد الأمر!")
                return
            if t_u["user_id"] == ADMIN_ID:
                bot.reply_to(m, "▽ : ⚡ لا يمكن تعديل رتبة المطور الأساسي MG!")
                return
            set_rank(chat_id, t_u["user_id"], new_l)
            bot.reply_to(m, f"▽ : تم تحديث رتبة <b>{esc(t_u['name'])}</b> إلى ↞ <b>{r_t}</b>")
            return

    if text in ("تنزيل الكل", "تصفير الرتب") and user_rank >= 6:
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE ranks SET rank_level = 0 WHERE chat_id = ? AND rank_level < 6", (chat_id,))
            conn.commit()
            conn.close()
        bot.reply_to(m, "▽ : ✅ تم تنزيل جميع الرتب الفرعية في المجموعة بنجاح.")
        return

    RANK_LIST_CMDS = {
        "المالكين": (6, "👑 قائمة المالكين"),
        "المنشئين": (4, "🎖️ قائمة المنشئين"),
        "المدراء": (3, "💼 قائمة المدراء"),
        "الادمنية": (2, "👮‍♂️ قائمة الادمنية"),
        "المميزين": (1, "🌟 قائمة المميزين"),
    }
    if text in RANK_LIST_CMDS:
        lvl, hdr = RANK_LIST_CMDS[text]
        with db_lock:
            conn = get_db()
            rows = conn.execute(
                "SELECT r.user_id, u.name FROM ranks r LEFT JOIN users u ON r.user_id = u.user_id WHERE r.chat_id = ? AND r.rank_level = ?",
                (chat_id, lvl)
            ).fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, f"▽ : لا يوجد أعضاء في {hdr} حالياً.")
        else:
            txt = f"▽ : <b>{hdr} :</b>\n──────────────\n"
            for idx, r in enumerate(rows, 1):
                txt += f"{idx}. <b>{esc(r['name'] or 'مواطن')}</b> (<code>{r['user_id']}</code>)\n"
            bot.reply_to(m, txt)
        return

    if text.startswith("ضع لقب ") and m.reply_to_message and user_rank >= 3:
        new_title = text[len("ضع لقب "):].strip()
        target = m.reply_to_message.from_user
        set_custom_title(chat_id, target.id, new_title)
        bot.reply_to(m, f"▽ : تم تعيين اللقب « <b>{esc(new_title)}</b> » للعضو بنجاح!")
        return

    # الردود المخصصة للمجموعة
    if text.startswith("اضف رد ") and "=" in text and user_rank >= 3:
        raw = text[len("اضف رد "):].strip()
        k, v = [x.strip() for x in raw.split("=", 1)]
        if k and v:
            reps = get_group_json(chat_id, "replies", {})
            reps[k] = v
            set_group_json(chat_id, "replies", reps)
            bot.reply_to(m, f"▽ : تم حفظ الرد بنجاح!\n▽ : الكلمة ↞ « {esc(k)} »\n▽ : الجواب ↞ « {esc(v)} »")
        return

    if text.startswith("مسح رد ") and user_rank >= 3:
        k = text[len("مسح رد "):].strip()
        reps = get_group_json(chat_id, "replies", {})
        if k in reps:
            del reps[k]
            set_group_json(chat_id, "replies", reps)
            bot.reply_to(m, f"▽ : تم حذف الرد « {esc(k)} » بنجاح.")
        else:
            bot.reply_to(m, "▽ : هذا الرد غير موجود!")
        return

    if text == "الردود":
        reps = get_group_json(chat_id, "replies", {})
        if not reps:
            bot.reply_to(m, "▽ : لا توجد ردود مضافة في المجموعة حالياً.")
        else:
            txt = "▽ : <b>قائمة ردود المجموعة :</b>\n──────────────\n"
            for k, v in reps.items():
                txt += f"• <code>{esc(k)}</code> ↞ {esc(v)}\n"
            bot.reply_to(m, txt)
        return

    if text == "مسح الردود" and user_rank >= 3:
        set_group_json(chat_id, "replies", {})
        bot.reply_to(m, "▽ : تم مسح جميع ردود المجموعة بنجاح.")
        return

    # الاختصارات المخصصة للمجموعة (مثال: اضف اختصار ح=حسابي)
    if text.startswith("اضف اختصار ") and "=" in text and user_rank >= 3:
        raw = text[len("اضف اختصار "):].strip()
        k, v = [x.strip() for x in raw.split("=", 1)]
        if k and v:
            scs = get_group_json(chat_id, "shortcuts", {})
            scs[k] = v
            set_group_json(chat_id, "shortcuts", scs)
            bot.reply_to(m, f"▽ : تم إضافة الاختصار بنجاح!\n▽ : عند كتابة « <code>{esc(k)}</code> » سينفذ أمر « <code>{esc(v)}</code> »")
        return

    if text.startswith("مسح اختصار ") and user_rank >= 3:
        k = text[len("مسح اختصار "):].strip()
        scs = get_group_json(chat_id, "shortcuts", {})
        if k in scs:
            del scs[k]
            set_group_json(chat_id, "shortcuts", scs)
            bot.reply_to(m, f"▽ : تم مسح الاختصار « {esc(k)} » بنجاح.")
        return

    if text == "الاختصارات":
        scs = get_group_json(chat_id, "shortcuts", {})
        txt = (
            "▽ : <b>الاختصارات الأساسية والمضافة :</b>\n"
            "──────────────\n"
            "• <code>ا</code> ↞ ايدي بالصورة\n"
            "• <code>ص</code> ↞ صورتي ونسبة جمالها\n"
        )
        for k, v in scs.items():
            txt += f"• <code>{esc(k)}</code> ↞ {esc(v)}\n"
        bot.reply_to(m, txt)
        return

    # الترحيب والقوانين
    if text.startswith("ضع ترحيب ") and user_rank >= 3:
        w_t = text[len("ضع ترحيب "):].strip()
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE groups SET welcome_text = ? WHERE chat_id = ?", (w_t, chat_id))
            conn.commit()
            conn.close()
        bot.reply_to(m, "▽ : ✅ تم تحديث رسالة الترحيب للمجموعة بنجاح!")
        return

    if text in ("تفعيل الترحيب", "تعطيل الترحيب") and user_rank >= 3:
        st = text == "تفعيل الترحيب"
        set_group_setting(chat_id, "الترحيب", st)
        bot.reply_to(m, f"▽ : تم {'تفعيل ✅' if st else 'تعطيل ❌'} الترحيب بنجاح.")
        return

    if text.startswith("ضع قوانين ") and user_rank >= 3:
        r_t = text[len("ضع قوانين "):].strip()
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE groups SET rules_text = ? WHERE chat_id = ?", (r_t, chat_id))
            conn.commit()
            conn.close()
        bot.reply_to(m, "▽ : ✅ تم حفظ قوانين المجموعة بنجاح!")
        return

    if text == "القوانين":
        bot.reply_to(m, f"▽ : <b>قوانين المجموعة :</b>\n──────────────\n{esc(grp_data.get('rules_text', ''))}")
        return

    # الحظر، الطرد، الكتم، الإنذار، التثبيت، المسح
    if text in ("حظر", "الغاء حظر", "طرد", "كتم", "الغاء كتم", "انذار", "حذف الانذارات") and m.reply_to_message and user_rank >= 2:
        target = m.reply_to_message.from_user
        if get_rank(chat_id, target.id) >= user_rank and user.id != ADMIN_ID:
            bot.reply_to(m, "▽ : ❌ لا يمكنك تطبيق العقوبة على رتبة مساوية أو أعلى منك!")
            return
        try:
            if text == "حظر":
                bot.ban_chat_member(chat_id, target.id)
                bot.reply_to(m, f"▽ : 🚫 تم حظر <b>{esc(target.first_name)}</b> من المجموعة!")
            elif text == "الغاء حظر":
                bot.unban_chat_member(chat_id, target.id)
                bot.reply_to(m, f"▽ : ✅ تم إلغاء حظر <b>{esc(target.first_name)}</b>!")
            elif text == "طرد":
                bot.ban_chat_member(chat_id, target.id)
                bot.unban_chat_member(chat_id, target.id)
                bot.reply_to(m, f"▽ : 👞 تم طرد <b>{esc(target.first_name)}</b> من المجموعة!")
            elif text == "كتم":
                bot.restrict_chat_member(chat_id, target.id, can_send_messages=False)
                bot.reply_to(m, f"▽ : 🔇 تم كتم <b>{esc(target.first_name)}</b>!")
            elif text == "الغاء كتم":
                bot.restrict_chat_member(chat_id, target.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
                bot.reply_to(m, f"▽ : 🔊 تم إلغاء كتم <b>{esc(target.first_name)}</b>!")
            elif text == "انذار":
                with db_lock:
                    conn = get_db()
                    row = conn.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, target.id)).fetchone()
                    cnt = (row["count"] if row else 0) + 1
                    conn.execute(
                        "INSERT INTO warnings (chat_id, user_id, count) VALUES (?,?,?) ON CONFLICT(chat_id,user_id) DO UPDATE SET count=?",
                        (chat_id, target.id, cnt, cnt)
                    )
                    conn.commit()
                    conn.close()
                if cnt >= 3:
                    bot.restrict_chat_member(chat_id, target.id, can_send_messages=False)
                    bot.reply_to(m, f"▽ : ⚠️ وصل <b>{esc(target.first_name)}</b> إلى (3/3) إنذارات وتم كتمه تلقائياً!")
                else:
                    bot.reply_to(m, f"▽ : ⚠️ تم توجيه إنذار إلى <b>{esc(target.first_name)}</b> ({cnt}/3)!")
            elif text == "حذف الانذارات":
                with db_lock:
                    conn = get_db()
                    conn.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, target.id))
                    conn.commit()
                    conn.close()
                bot.reply_to(m, f"▽ : ✅ تم مسح جميع إنذارات <b>{esc(target.first_name)}</b>!")
        except Exception:
            bot.reply_to(m, "▽ : ⚠️ تأكد من منح البوت صلاحيات المشرف الكاملة!")
        return

    if text in ("تثبيت", "الغاء تثبيت") and m.reply_to_message and user_rank >= 2:
        try:
            if text == "تثبيت":
                bot.pin_chat_message(chat_id, m.reply_to_message.message_id)
                bot.reply_to(m, "▽ : 📌 تم تثبيت الرسالة بنجاح!")
            else:
                bot.unpin_chat_message(chat_id, m.reply_to_message.message_id)
                bot.reply_to(m, "▽ : 📌 تم إلغاء تثبيت الرسالة!")
        except Exception:
            pass
        return

    if text == "اطردني" and user_rank < 2:
        try:
            bot.ban_chat_member(chat_id, user.id)
            bot.unban_chat_member(chat_id, user.id)
        except Exception:
            pass
        return

    if text.startswith("مسح") and user_rank >= 2:
        if m.reply_to_message and text == "مسح":
            try:
                bot.delete_message(chat_id, m.reply_to_message.message_id)
                bot.delete_message(chat_id, m.message_id)
            except Exception:
                pass
            return
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            cnt = min(int(parts[1]), 50)
            for mid in range(m.message_id, m.message_id - cnt - 1, -1):
                try:
                    bot.delete_message(chat_id, mid)
                except Exception:
                    pass
            return

    # ─────────────── 5. نظام الحبس القصير والهروب (3 إلى 10 دقائق فقط) ───────────────

    # أمر تهريب صديق محبوس بالرد عليه
    if text == "تهريب" and m.reply_to_message:
        friend = ensure_user(m.reply_to_message.from_user)
        if friend["user_id"] == user.id:
            bot.reply_to(m, "▽ : 😂 ما تقدرش تهرب روحك! خلي صاحبك يرد عليك بـ <code>تهريب</code> أو اكتب <code>دفع كفالة</code> أو <code>رشوة العساس</code>.")
            return
        if friend["jail_until"] <= now:
            bot.reply_to(m, f"▽ : المواطن <b>{esc(friend['name'])}</b> حر طليق ومش محبوس!")
            return
        if random.randint(1, 100) <= 70:
            update_user_field(friend["user_id"], jail_until=0, wanted=0)
            bot.reply_to(
                m,
                f"🚁🔥 <b>عملية تهريب أسطورية ناجحة!</b>\n"
                f"▽ : قام الذئب <b>{esc(u_data['name'])}</b> بتهريب صاحبه <b>{esc(friend['name'])}</b> من الحبس بنجاح!"
            )
        else:
            fine = min(200, u_data["cash"])
            update_user_field(user.id, cash=u_data["cash"] - fine)
            bot.reply_to(
                m,
                f"🚨 <b>فشلت محاولة التهريب!</b>\n"
                f"▽ : انتبه العساس وخالفك بمبلغ <b>{fine} د.ل</b>!"
            )
        return

    # التحقق مما إذا كان اللاعب نفسه محبوساً
    if u_data["jail_until"] > now:
        rem_sec = u_data["jail_until"] - now
        rem_min = max(1, (rem_sec + 59) // 60)

        if text == "دفع كفالة":
            bail = 500
            if u_data["cash"] >= bail:
                update_user_field(user.id, cash=u_data["cash"] - bail, jail_until=0, wanted=0)
                bot.reply_to(m, f"▽ : ⚖️ دفعت <b>{bail} د.ل</b> كفالة من كاش جيبك وطلعت براءة فوراً!")
            elif u_data["bank_balance"] >= bail:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - bail, jail_until=0, wanted=0)
                bot.reply_to(m, f"▽ : ⚖️ تم خصم <b>{bail} د.ل</b> كفالة من مصرفك وطلعت براءة فوراً!")
            else:
                bot.reply_to(m, f"▽ : ❌ لا تملك {bail} د.ل لدفع الكفالة! اطلب من صديقك الرد عليك بكلمة <code>تهريب</code>.")
            return

        if text == "رشوة العساس":
            bribe = 300
            if u_data["cash"] < bribe:
                bot.reply_to(m, f"▽ : ❌ تحتاج <b>{bribe} د.ل</b> كاش لرشوة العساس!")
                return
            if random.randint(1, 100) <= 65:
                update_user_field(user.id, cash=u_data["cash"] - bribe, jail_until=0, wanted=0)
                bot.reply_to(m, "▽ : 🤫 قبل العساس الرشوة وفتحلك الباب الخلفي.. اهرب بسرعة!")
            else:
                new_jail = u_data["jail_until"] + 120  # زيادة دقيقتين فقط
                update_user_field(user.id, cash=u_data["cash"] - bribe, jail_until=new_jail)
                bot.reply_to(m, "▽ : 🚨 العساس طلع نزيه وصادر الـ 300 د.ل وزادك دقيقتين في الحبس!")
            return

        if is_cmd and text not in ("حسابي", "فلوسي", "البنك"):
            bot.reply_to(
                m,
                f"⛓️ <b>أنت موقوف في المركز حالياً!</b>\n"
                f"──────────────\n"
                f"▽ : الوقت المتبقي للخروج ↞ <b>{rem_min} دقيقة فقط</b>\n"
                f"▽ : للخروج فوراً اختر إحدى الطرق :\n"
                f"1️⃣ ارسل <code>دفع كفالة</code> (500 د.ل)\n"
                f"2️⃣ ارسل <code>رشوة العساس</code> (300 د.ل)\n"
                f"3️⃣ اطلب من صديقك الرد على رسالتك بكلمة <code>تهريب</code>"
            )
            return

    # ─────────────── 6. البنك الليبي (الكاش عام والرصيد المصرفي سري) ───────────────

    if text in ("انشاء حساب", "فتح حساب"):
        if u_data["bank_name"] != "بدون مصرف":
            bot.reply_to(m, f"▽ : لديك حساب مفعل مسبقاً في <b>{esc(u_data['bank_name'])}</b>!")
            return
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b_t in BANKS:
            kb.add(types.InlineKeyboardButton(f"🏦 {b_t}", callback_data=f"openbank_{b_t}"))
        bot.reply_to(m, "▽ : اختر المصرف الليبي لفتح حسابك واستلام 1000 د.ل هدية افتتاح :", reply_markup=kb)
        return

    if text in ("حسابي", "فلوسي", "البنك"):
        bot.reply_to(
            m,
            f"🏦 <b>البطاقة المصرفية الذكية 🇱🇾</b>\n"
            f"──────────────\n"
            f"▽ : العميل ↞ <b>{esc(u_data['name'])}</b>\n"
            f"▽ : المصرف ↞ <b>{esc(u_data['bank_name'])}</b>\n"
            f"▽ : الكاش في الجيب (عام) ↞ <b>{u_data['cash']} د.ل</b> 💵\n"
            f"▽ : رصيد الخزنة المصرفية ↞ <b>🔒 مشفر (خاص بالعميل)</b>\n"
            f"▽ : القروض والأسهم ↞ <b>🔒 مشفر (خاص بالعميل)</b>\n"
            f"──────────────\n"
            f"💡 <i>اضغط على الزر أدناه لكشف رصيدك المصرفي السري دون أن يراه أحد في المجموعة :</i>",
            reply_markup=build_bank_secret_kb(user.id)
        )
        return

    if text.startswith("ايداع "):
        if u_data["bank_name"] == "بدون مصرف":
            bot.reply_to(m, "▽ : ❌ افتح حساباً أولاً بكتابة <code>انشاء حساب</code>!")
            return
        arg = text.split()[1]
        amt = u_data["cash"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt <= 0 or amt > u_data["cash"]:
            bot.reply_to(m, "▽ : ❌ المبلغ غير صحيح أو الكاش في جيبك لا يكفي!")
            return
        new_cash = u_data["cash"] - amt
        new_bank = u_data["bank_balance"] + amt
        update_user_field(user.id, cash=new_cash, bank_balance=new_bank)
        bot.reply_to(
            m,
            f"▽ : ✅ تم إيداع <b>{amt} د.ل</b> في خزنتك المصرفية بأمان!\n"
            f"▽ : الكاش المتبقي في جيبك ↞ <b>{new_cash} د.ل</b>\n"
            f"▽ : رصيد المصرف الإجمالي ↞ <b>🔒 محفوظ سرياً</b>",
            reply_markup=build_bank_secret_kb(user.id)
        )
        return

    if text.startswith("سحب "):
        arg = text.split()[1]
        amt = u_data["bank_balance"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt <= 0 or amt > u_data["bank_balance"]:
            bot.reply_to(m, "▽ : ❌ رصيدك في المصرف لا يكفي لإتمام عملية السحب!")
            return
        new_cash = u_data["cash"] + amt
        new_bank = u_data["bank_balance"] - amt
        update_user_field(user.id, cash=new_cash, bank_balance=new_bank)
        bot.reply_to(
            m,
            f"▽ : 💵 تم سحب <b>{amt} د.ل</b> من المصرف إلى جيبك!\n"
            f"▽ : الكاش الحالي في جيبك ↞ <b>{new_cash} د.ل</b> (احذر من الحرامية! 🦹‍♂️)",
            reply_markup=build_bank_secret_kb(user.id)
        )
        return

    if text.startswith("تحويل ") and m.reply_to_message:
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            amt = int(parts[1])
            target = ensure_user(m.reply_to_message.from_user)
            if target["user_id"] == user.id or amt <= 0:
                return
            if u_data["bank_balance"] < amt:
                bot.reply_to(m, "▽ : ❌ رصيدك في المصرف لا يكفي للتحويل!")
                return
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - amt)
            update_user_field(target["user_id"], bank_balance=target["bank_balance"] + amt)
            bot.reply_to(
                m,
                f"▽ : 💸 تمت الحوالة المصرفية بنجاح!\n"
                f"▽ : من ↞ <b>{esc(u_data['name'])}</b>\n"
                f"▽ : إلى ↞ <b>{esc(target['name'])}</b>\n"
                f"▽ : القيمة المحولة ↞ <b>{amt} د.ل</b>"
            )
        return

    if text.startswith("قرض"):
        parts = text.split()
        amt = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5000
        amt = min(amt, 15000)
        if u_data["loan"] > 0:
            bot.reply_to(m, f"▽ : ❌ عليك قرض سابق بقيمة {u_data['loan']} د.ل! سدده أولاً بكتابة <code>تسديد القرض</code>.")
            return
        update_user_field(user.id, bank_balance=u_data["bank_balance"] + amt, loan=amt)
        bot.reply_to(m, f"▽ : 🏦 تم منحك قرضاً مصرفياً بقيمة <b>{amt} د.ل</b> وإضافته لرصيدك السري!")
        return

    if text == "تسديد القرض":
        if u_data["loan"] <= 0:
            bot.reply_to(m, "▽ : ليس عليك أي قروض مصرفية حالياً!")
            return
        if u_data["bank_balance"] >= u_data["loan"]:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - u_data["loan"], loan=0)
            bot.reply_to(m, "▽ : ✅ تم تسديد القرض بالكامل من رصيدك المصرفي!")
        elif u_data["cash"] >= u_data["loan"]:
            update_user_field(user.id, cash=u_data["cash"] - u_data["loan"], loan=0)
            bot.reply_to(m, "▽ : ✅ تم تسديد القرض بالكامل من كاش جيبك!")
        else:
            bot.reply_to(m, f"▽ : ❌ لا تملك قيمة القرض ({u_data['loan']} د.ل) لتسديده!")
        return

    # ─────────────── 7. الوظائف، المدن، العقارات، السيارات، السوق الحر ───────────────

    if text == "الوظائف":
        txt = "▽ : <b>ديوان الوظائف والمهن الليبية :</b>\n──────────────\n"
        for j, inf in JOBS.items():
            txt += f"• <b>{j}</b> ↞ الراتب: {inf['salary']} د.ل\n  └ <i>{inf['desc']}</i>\n"
        txt += "──────────────\n▽ : للتعيين اكتب: <code>وظيفة دكتور</code> أو <code>وظيفة مبرمج</code>..."
        bot.reply_to(m, txt)
        return

    if text.startswith("وظيفة "):
        j_c = text[len("وظيفة "):].strip()
        if j_c in JOBS:
            update_user_field(user.id, job=j_c)
            bot.reply_to(m, f"▽ : 🎉 مبروك تعيينك في مهنة <b>{j_c}</b>! اكتب <code>راتب</code> لاستلام يوميتك.")
        return

    if text in ("راتب", "خدمة", "بخشيش"):
        if now - u_data["last_salary"] < 600:
            rem = (600 - (now - u_data["last_salary"])) // 60 + 1
            bot.reply_to(m, f"▽ : ⏳ استلمت راتبك منذ قليل! انتظر {rem} دقيقة للراتب القادم.")
            return
        sal = JOBS.get(u_data["job"], {"salary": 700})["salary"]
        update_user_field(user.id, cash=u_data["cash"] + sal, last_salary=now)
        bot.reply_to(
            m,
            f"▽ : 💵 استلمت راتب مهنتك (<b>{u_data['job']}</b>) وقدره <b>{sal} د.ل</b> كاش في جيبك!\n"
            f"▽ : 💡 سارع بإيداعه في المصرف (<code>ايداع الكل</code>) قبل أن يسرقك الحرامية!"
        )
        return

    if text in ("علاج", "بيع دواء") and m.reply_to_message:
        if u_data["job"] not in ("دكتور", "صيدلي"):
            bot.reply_to(m, "▽ : ❌ هذا الأمر مخصص للدكتور أو الصيدلي فقط!")
            return
        patient = ensure_user(m.reply_to_message.from_user)
        update_user_field(patient["user_id"], hp=100)
        update_user_field(user.id, cash=u_data["cash"] + 600)
        bot.reply_to(m, f"▽ : 🩺 قمت بعلاج <b>{esc(patient['name'])}</b> لـ 100% وكسبت مكافأة <b>600 د.ل</b> كاش!")
        return

    if text == "تصليح" and m.reply_to_message:
        if u_data["job"] != "ميكانيكي":
            bot.reply_to(m, "▽ : ❌ هذا الأمر للميكانيكي فقط!")
            return
        cli = ensure_user(m.reply_to_message.from_user)
        if cli["car"] == "بدون سيارة":
            bot.reply_to(m, "▽ : 😂 هذا الشخص لا يملك سيارة أصلاً!")
            return
        update_user_field(user.id, cash=u_data["cash"] + 800)
        bot.reply_to(m, f"▽ : 🔧 صلحت سيارة <b>{esc(cli['name'])}</b> وكسبت أتعاب <b>800 د.ل</b> كاش!")
        return

    if text == "قبض" and m.reply_to_message:
        if u_data["job"] != "شرطي":
            bot.reply_to(m, "▽ : ❌ هذا الأمر لرجال الشرطة فقط!")
            return
        crim = ensure_user(m.reply_to_message.from_user)
        if crim["wanted"] == 0:
            bot.reply_to(m, "▽ : ⚖️ هذا المواطن سجله نظيف وغير مطلوب للعدالة!")
            return
        # حبس قصير 5 دقائق فقط
        update_user_field(crim["user_id"], jail_until=now + 300, wanted=0)
        update_user_field(user.id, cash=u_data["cash"] + 1200)
        bot.reply_to(
            m,
            f"▽ : 🚓 تم إلقاء القبض على المطلوب <b>{esc(crim['name'])}</b> وحبسه لمدة 5 دقائق!\n"
            f"▽ : استلم الشرطي مكافأة <b>1200 د.ل</b> كاش 🎖️"
        )
        return

    if text == "اختراق صراف":
        if u_data["job"] != "مبرمج":
            bot.reply_to(m, "▽ : ❌ هذا الأمر للمبرمجين فقط!")
            return
        if now - u_data["last_work"] < 600:
            bot.reply_to(m, "▽ : ⏳ أنظمة الحماية مشددة حالياً، انتظر قليلاً!")
            return
        if random.randint(1, 100) <= 65:
            hack_val = random.randint(1500, 3500)
            update_user_field(user.id, cash=u_data["cash"] + hack_val, last_work=now)
            bot.reply_to(m, f"▽ : 💻⚡ اخترقت الصراف الآلي بنجاح وسحبت <b>{hack_val} د.ل</b> كاش!")
        else:
            update_user_field(user.id, jail_until=now + 240, last_work=now)  # 4 دقائق فقط
            bot.reply_to(m, "▽ : 🚨 كشفك النظام الأمني وتم توقيفك لمدة 4 دقائق!")
        return

    if text == "حماية حساب":
        if u_data["job"] != "مبرمج":
            bot.reply_to(m, "▽ : ❌ هذا الأمر للمبرمجين فقط!")
            return
        update_user_field(user.id, firewall_until=now + 3600)
        bot.reply_to(m, "▽ : 🛡️ قمت بتفعيل جدار ناري لحماية جيبك وحسابك لمدة ساعة كاملة!")
        return

    # المدن والسفر والتهريب
    if text == "المدن":
        txt = "▽ : <b>المدن الليبية المتاحة للسفر والتجارة :</b>\n──────────────\n"
        for cn, ci in CITIES.items():
            txt += f"📍 <b>{cn}</b> ↞ التذكرة: {ci['ticket']} د.ل\n"
        txt += "──────────────\n▽ : للسفر اكتب: <code>سفر بنغازي</code>"
        bot.reply_to(m, txt)
        return

    if text.startswith("سفر "):
        dest = text[len("سفر "):].strip()
        if dest in CITIES:
            t_cost = CITIES[dest]["ticket"]
            if u_data["cash"] < t_cost:
                bot.reply_to(m, f"▽ : ❌ تحتاج {t_cost} د.ل كاش لشراء تذكرة السفر!")
                return
            update_user_field(user.id, city=dest, cash=u_data["cash"] - t_cost)
            bot.reply_to(m, f"▽ : ✈️ الحمد لله على السلامة! وصلت إلى مدينة <b>{dest}</b>.")
        return

    if text == "تهريب بضاعة":
        if u_data["cash"] < 1500:
            bot.reply_to(m, "▽ : ❌ تحتاج 1500 د.ل كاش رأس مال لشراء البضاعة!")
            return
        if random.randint(1, 100) <= 65:
            prof = random.randint(2500, 5000)
            update_user_field(user.id, cash=u_data["cash"] - 1500 + prof)
            bot.reply_to(m, f"▽ : 🚚💨 نجحت صفقة التهريب عبر مدينة {u_data['city']} وربحت صافي <b>{prof} د.ل</b> كاش!")
        else:
            # حبس قصير 5 دقائق فقط
            update_user_field(user.id, cash=u_data["cash"] - 1500, jail_until=now + 300)
            bot.reply_to(m, "▽ : 🚨 مسكتك دورية الجمارك وصادرت البضاعة وتم توقيفك لمدة 5 دقائق فقط!")
        return

    # العقارات والسيارات والسباق والمشاريع
    if text == "العقارات":
        txt = "▽ : <b>معرض العقارات الليبية :</b>\n──────────────\n"
        for hn, hi in HOUSES.items():
            txt += f"🏠 <b>{hn}</b> ↞ السعر: {hi['price']} د.ل (حماية +{hi['defense']}%)\n"
        txt += "──────────────\n▽ : للشراء: <code>شراء بيت شقة في الفلاح</code>\n▽ : للبيع: <code>بيع بيت</code> أو <code>عرض بيت للبيع السعر</code>"
        bot.reply_to(m, txt)
        return

    if text.startswith("شراء بيت "):
        hn = text[len("شراء بيت "):].strip()
        if hn in HOUSES:
            pr = HOUSES[hn]["price"]
            if u_data["bank_balance"] >= pr:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - pr, house=hn)
                bot.reply_to(m, f"▽ : 🔑 مبروك العتبة الجديدة! اشتريت <b>{hn}</b> من رصيدك المصرفي.")
            elif u_data["cash"] >= pr:
                update_user_field(user.id, cash=u_data["cash"] - pr, house=hn)
                bot.reply_to(m, f"▽ : 🔑 مبروك العتبة الجديدة! اشتريت <b>{hn}</b> بالكاش.")
            else:
                bot.reply_to(m, f"▽ : ❌ ثمن العقار ({pr} د.ل) غير متوفر في حسابك!")
        return

    if text == "بيع بيت":
        if u_data["house"] != "بدون سكن" and u_data["house"] in HOUSES:
            p = int(HOUSES[u_data["house"]]["price"] * 0.8)
            update_user_field(user.id, bank_balance=u_data["bank_balance"] + p, house="بدون سكن")
            bot.reply_to(m, f"▽ : 🏠 بعت عقارك للمكتب العقاري وتم إيداع <b>{p} د.ل</b> في مصرفك السري!")
        return

    if text == "السيارات":
        txt = "▽ : <b>معرض السيارات الليبية :</b>\n──────────────\n"
        for cn, ci in CARS.items():
            txt += f"🚗 <b>{cn}</b> ↞ السعر: {ci['price']} د.ل (السرعة: {ci['speed']})\n"
        txt += "──────────────\n▽ : للشراء: <code>شراء سيارة تويوتا دبدوبة</code>\n▽ : للبيع: <code>بيع سيارة</code> أو <code>عرض سيارة للبيع السعر</code>"
        bot.reply_to(m, txt)
        return

    if text.startswith("شراء سيارة "):
        cn = text[len("شراء سيارة "):].strip()
        if cn in CARS:
            pr = CARS[cn]["price"]
            if u_data["bank_balance"] >= pr:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - pr, car=cn)
                bot.reply_to(m, f"▽ : 🏎️ مبروك عليك السيارة الجديدة (<b>{cn}</b>)! دير بالك من الرادارات 😂")
            elif u_data["cash"] >= pr:
                update_user_field(user.id, cash=u_data["cash"] - pr, car=cn)
                bot.reply_to(m, f"▽ : 🏎️ مبروك عليك السيارة الجديدة (<b>{cn}</b>) بالكاش!")
            else:
                bot.reply_to(m, f"▽ : ❌ ثمن السيارة ({pr} د.ل) غير متوفر لديك!")
        return

    if text == "بيع سيارة":
        if u_data["car"] != "بدون سيارة" and u_data["car"] in CARS:
            p = int(CARS[u_data["car"]]["price"] * 0.8)
            update_user_field(user.id, bank_balance=u_data["bank_balance"] + p, car="بدون سيارة")
            bot.reply_to(m, f"▽ : 🚗 بعت سيارتك للمعرض وتم إيداع <b>{p} د.ل</b> في مصرفك السري!")
        return

    if text == "سباق" and m.reply_to_message:
        opp = ensure_user(m.reply_to_message.from_user)
        if u_data["car"] == "بدون سيارة" or opp["car"] == "بدون سيارة":
            bot.reply_to(m, "▽ : ❌ يجب أن يمتلك الطرفان سيارة لخوض السباق!")
            return
        s1 = CARS.get(u_data["car"], {"speed": 50})["speed"] + random.randint(1, 35)
        s2 = CARS.get(opp["car"], {"speed": 50})["speed"] + random.randint(1, 35)
        prize = 1000
        if s1 >= s2:
            update_user_field(user.id, cash=u_data["cash"] + prize)
            bot.reply_to(m, f"🏁🏎️ <b>سباق ناري في طريق الشط!</b>\n▽ : فاز <b>{esc(u_data['name'])}</b> بسيارته ({u_data['car']}) على <b>{esc(opp['name'])}</b> وربح جائزة <b>{prize} د.ل</b> كاش!")
        else:
            update_user_field(opp["user_id"], cash=opp["cash"] + prize)
            bot.reply_to(m, f"🏁🏎️ <b>سباق ناري في طريق الشط!</b>\n▽ : فاز <b>{esc(opp['name'])}</b> بسيارته ({opp['car']}) على <b>{esc(u_data['name'])}</b> وربح جائزة <b>{prize} د.ل</b> كاش!")
        return

    if text == "المشاريع":
        txt = "▽ : <b>المشاريع التجارية المتاحة :</b>\n──────────────\n"
        for bn, bi in BUSINESSES.items():
            txt += f"🏢 <b>{bn}</b> ↞ السعر: {bi['price']} د.ل (العائد: {bi['income']} د.ل)\n"
        txt += "──────────────\n▽ : للبدء: <code>فتح مشروع مقهى شعبي</code>\n▽ : لجني الأرباح: <code>تحصيل ارباح</code>"
        bot.reply_to(m, txt)
        return

    if text.startswith("فتح مشروع "):
        bn = text[len("فتح مشروع "):].strip()
        if bn in BUSINESSES:
            pr = BUSINESSES[bn]["price"]
            if u_data["bank_balance"] >= pr:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - pr, business=bn, last_collect=now)
                bot.reply_to(m, f"▽ : 🏢 مبروك افتتاح مشروعك التجاري (<b>{bn}</b>)!")
            else:
                bot.reply_to(m, f"▽ : ❌ تحتاج {pr} د.ل في مصرفك لافتتاح هذا المشروع!")
        return

    if text == "تحصيل ارباح":
        if u_data["business"] == "بدون مشروع" or u_data["business"] not in BUSINESSES:
            bot.reply_to(m, "▽ : ❌ لا تملك مشروعاً تجارياً حالياً! اكتب <code>المشاريع</code>.")
            return
        if now - u_data["last_collect"] < 900:
            bot.reply_to(m, "▽ : ⏳ لم تتجمع الأرباح بعد، انتظر بضع دقائق!")
            return
        inc = BUSINESSES[u_data["business"]]["income"]
        update_user_field(user.id, cash=u_data["cash"] + inc, last_collect=now)
        bot.reply_to(m, f"▽ : 💰 استلمت أرباح مشروعك ({u_data['business']}) بقيمة <b>{inc} د.ل</b> كاش!")
        return

    # ─────────────── 8. السوق الحر بين اللاعبين + البورصة ───────────────

    if text == "السوق الحر":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM marketplace").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "▽ : 🏪 السوق الحر فارغ حالياً! اعرض عقارك أو سيارتك بكتابة:\n<code>عرض سيارة للبيع 15000</code> أو <code>عرض بيت للبيع 30000</code>")
        else:
            txt = "▽ : <b>🏪 عروض السوق الحر بين اللاعبين :</b>\n──────────────\n"
            for r in rows:
                txt += f"🆔 <b>#{r['id']}</b> | البائع: {esc(r['seller_name'])}\n  └ السلعة: <b>{esc(r['item_name'])}</b> ↞ السعر: <b>{r['price']} د.ل</b>\n"
            txt += "──────────────\n▽ : للشراء: <code>شراء معروض الرقم</code>\n▽ : لإلغاء عرضك: <code>الغاء عرض الرقم</code>"
            bot.reply_to(m, txt)
        return

    if text.startswith("عرض بيت للبيع "):
        pr = text[len("عرض بيت للبيع "):].strip()
        if u_data["house"] == "بدون سكن":
            bot.reply_to(m, "▽ : ❌ لا تملك بيتاً لعرضه للبيع!")
            return
        if pr.isdigit() and int(pr) > 0:
            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT INTO marketplace (seller_id, seller_name, item_type, item_name, price) VALUES (?,?,?,?,?)",
                    (user.id, u_data["name"], "house", u_data["house"], int(pr))
                )
                conn.commit()
                conn.close()
            update_user_field(user.id, house="بدون سكن")
            bot.reply_to(m, f"▽ : 🏪 تم عرض عقارك (<b>{u_data['house']}</b>) في السوق الحر بسعر <b>{pr} د.ل</b>!")
        return

    if text.startswith("عرض سيارة للبيع "):
        pr = text[len("عرض سيارة للبيع "):].strip()
        if u_data["car"] == "بدون سيارة":
            bot.reply_to(m, "▽ : ❌ لا تملك سيارة لعرضها للبيع!")
            return
        if pr.isdigit() and int(pr) > 0:
            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT INTO marketplace (seller_id, seller_name, item_type, item_name, price) VALUES (?,?,?,?,?)",
                    (user.id, u_data["name"], "car", u_data["car"], int(pr))
                )
                conn.commit()
                conn.close()
            update_user_field(user.id, car="بدون سيارة")
            bot.reply_to(m, f"▽ : 🏪 تم عرض سيارتك (<b>{u_data['car']}</b>) في السوق الحر بسعر <b>{pr} د.ل</b>!")
        return

    if text.startswith("الغاء عرض "):
        parts = text.split()
        if len(parts) == 3 and parts[2].isdigit():
            m_id = int(parts[2])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM marketplace WHERE id = ?", (m_id,)).fetchone()
                if not row or row["seller_id"] != user.id:
                    conn.close()
                    bot.reply_to(m, "▽ : ❌ هذا العرض غير موجود أو لا يخصك!")
                    return
                conn.execute("DELETE FROM marketplace WHERE id = ?", (m_id,))
                conn.commit()
                conn.close()
            if row["item_type"] == "house":
                update_user_field(user.id, house=row["item_name"])
            else:
                update_user_field(user.id, car=row["item_name"])
            bot.reply_to(m, f"▽ : ✅ تم إلغاء العرض واسترجاع (<b>{row['item_name']}</b>) إلى ممتلكاتك!")
        return

    if text.startswith("شراء معروض "):
        parts = text.split()
        if len(parts) == 3 and parts[2].isdigit():
            m_id = int(parts[2])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM marketplace WHERE id = ?", (m_id,)).fetchone()
                conn.close()
            if not row:
                bot.reply_to(m, "▽ : ❌ المعروض غير موجود أو تم بيعه!")
                return
            if row["seller_id"] == user.id:
                bot.reply_to(m, "▽ : 💡 لاسترجاع سلعتك اكتب <code>الغاء عرض الرقم</code>.")
                return
            price = row["price"]
            if u_data["bank_balance"] >= price:
                pay_from = "bank"
            elif u_data["cash"] >= price:
                pay_from = "cash"
            else:
                bot.reply_to(m, f"▽ : ❌ لا تملك {price} د.ل لشراء هذا المعروض!")
                return

            with db_lock:
                conn = get_db()
                conn.execute("DELETE FROM marketplace WHERE id = ?", (m_id,))
                conn.commit()
                conn.close()

            if pay_from == "bank":
                update_user_field(
                    user.id,
                    bank_balance=u_data["bank_balance"] - price,
                    house=(row["item_name"] if row["item_type"] == "house" else u_data["house"]),
                    car=(row["item_name"] if row["item_type"] == "car" else u_data["car"])
                )
            else:
                update_user_field(
                    user.id,
                    cash=u_data["cash"] - price,
                    house=(row["item_name"] if row["item_type"] == "house" else u_data["house"]),
                    car=(row["item_name"] if row["item_type"] == "car" else u_data["car"])
                )

            seller = get_user_by_id(row["seller_id"])
            if seller:
                update_user_field(seller["user_id"], bank_balance=seller["bank_balance"] + price)
            bot.reply_to(
                m,
                f"▽ : 🎉 صفقة ناجحة في السوق الحر!\n"
                f"▽ : اشترى <b>{esc(u_data['name'])}</b> السلعة (<b>{esc(row['item_name'])}</b>) من <b>{esc(row['seller_name'])}</b> بمبلغ <b>{price} د.ل</b>!"
            )
        return

    # البورصة والأسهم
    if text in ("البورصة", "اسهمي"):
        txt = "▽ : <b>📈 أسعار أسهم الشركات الليبية الآن :</b>\n──────────────\n"
        for sn in STOCKS.keys():
            txt += f"• شركة <b>{sn}</b> ↞ السعر الحالي: <b>{get_current_stock_price(sn)} د.ل</b> للسهم\n"
        txt += (
            "──────────────\n"
            "▽ : محفظة أسهمك الخاصة مشفرة لحمايتك (اضغط الزر أدناه لكشفها)\n"
            "▽ : للشراء: <code>شراء اسهم المدار 10</code> | للبيع: <code>بيع اسهم المدار</code>"
        )
        bot.reply_to(m, txt, reply_markup=build_bank_secret_kb(user.id))
        return

    if text.startswith("شراء اسهم "):
        parts = text.split()
        if len(parts) == 4 and parts[3].isdigit():
            sn, qty = parts[2], int(parts[3])
            if sn not in STOCKS or qty <= 0:
                return
            cost = get_current_stock_price(sn) * qty
            if u_data["bank_balance"] < cost:
                bot.reply_to(m, f"▽ : ❌ تحتاج {cost} د.ل في مصرفك لشراء هذه الأسهم!")
                return
            u_stk = json.loads(u_data.get("stocks") or "{}")
            u_stk[sn] = u_stk.get(sn, 0) + qty
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost, stocks=json.dumps(u_stk))
            bot.reply_to(m, f"▽ : 📈 اشتريت <b>{qty} سهم</b> في شركة <b>{sn}</b> بمبلغ <b>{cost} د.ل</b> وتم حفظها في محفظتك السرية!")
        return

    if text.startswith("بيع اسهم "):
        sn = text[len("بيع اسهم "):].strip()
        u_stk = json.loads(u_data.get("stocks") or "{}")
        qty = u_stk.get(sn, 0)
        if qty > 0:
            val = get_current_stock_price(sn) * qty
            u_stk[sn] = 0
            update_user_field(user.id, bank_balance=u_data["bank_balance"] + val, stocks=json.dumps(u_stk))
            bot.reply_to(m, f"▽ : 💰 بعت أسهمك في شركة <b>{sn}</b> وتم إيداع <b>{val} د.ل</b> في رصيدك المصرفي السري!")
        else:
            bot.reply_to(m, f"▽ : ❌ لا تملك أسهماً في شركة {esc(sn)}!")
        return

    # ─────────────── 9. السرقة، التحدي والمبارزة، والتوب ───────────────

    if text == "سرقة" and m.reply_to_message:
        vic = ensure_user(m.reply_to_message.from_user)
        if vic["user_id"] == user.id or m.reply_to_message.from_user.is_bot:
            return
        if vic["firewall_until"] > now:
            bot.reply_to(m, f"▽ : 🛡️ المواطن <b>{esc(vic['name'])}</b> مفعل حماية المبرمج! لا يمكنك سرقته حالياً.")
            return
        if vic["cash"] < 150:
            bot.reply_to(m, f"▽ : 😂 جيب <b>{esc(vic['name'])}</b> فاضي ما فيه غير الفكة ({vic['cash']} د.ل)، فلوسه داسهم في المصرف!")
            return
        defense = HOUSES.get(vic["house"], {"defense": 0})["defense"]
        chance = max(25, 65 - (defense // 2))
        if random.randint(1, 100) <= chance:
            stolen = max(50, int(vic["cash"] * random.uniform(0.25, 0.45)))
            update_user_field(vic["user_id"], cash=vic["cash"] - stolen)
            update_user_field(user.id, cash=u_data["cash"] + stolen, steal_success=u_data["steal_success"] + 1, wanted=1)
            bot.reply_to(
                m,
                f"🦹‍♂️💨 <b>عملية نشل سريعة!</b>\n"
                f"▽ : غفّل <b>{esc(u_data['name'])}</b> الضحية <b>{esc(vic['name'])}</b> وسرق من كاش جيبه <b>{stolen} د.ل</b>!\n"
                f"▽ : 💡 (نصيحة للضحية: دير <code>ايداع الكل</code> في المصرف لحماية فلوسك!)"
            )
        else:
            # حبس قصير 3 دقائق فقط!
            update_user_field(user.id, hp=max(10, u_data["hp"] - 20), jail_until=now + 180)
            bot.reply_to(
                m,
                f"🚨🤛 <b>انكشفت السرقة!</b>\n"
                f"▽ : فطنلك <b>{esc(vic['name'])}</b> وعطاك طريحة وسلمك للدورية!\n"
                f"▽ : تم توقيفك لمدة <b>3 دقائق فقط</b> (اكتب <code>دفع كفالة</code> أو خلي صاحبك يرد بـ <code>تهريب</code>)."
            )
        return

    if text == "سرقة المصرف":
        if now - u_data["last_rob"] < 900:
            bot.reply_to(m, "▽ : ⏳ المصرف تحت الحراسة المشددة حالياً! انتظر قليلاً.")
            return
        if random.randint(1, 100) <= 35:
            loot = random.randint(8000, 18000)
            update_user_field(user.id, cash=u_data["cash"] + loot, last_rob=now, wanted=1)
            bot.reply_to(m, f"💣🏦 <b>سطو مسلح أسطوري ناجح!</b>\n▽ : كسرت الخزنة وهربت بمبلغ <b>{loot} د.ل</b> كاش!")
        else:
            # حبس قصير 7 دقائق فقط!
            update_user_field(user.id, jail_until=now + 420, last_rob=now)
            bot.reply_to(m, "🚓🚨 <b>كبست عليك القوة الخاصة!</b>\n▽ : فشلت سرقة المصرف وتم حبسك لمدة <b>7 دقائق فقط</b>!")
        return

    # أمر تحدي الشارع بالرهان بين عضوين
    if text.startswith("تحدي ") and m.reply_to_message:
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            bet = int(parts[1])
            opp = ensure_user(m.reply_to_message.from_user)
            if opp["user_id"] == user.id or bet < 100:
                bot.reply_to(m, "▽ : ❌ أقل مبلغ للتحدي هو 100 د.ل مع عضو آخر!")
                return
            if u_data["cash"] < bet or opp["cash"] < bet:
                bot.reply_to(m, "▽ : ❌ يجب أن يمتلك الطرفان مبلغ الرهان كاش في الجيب!")
                return
            duel_id = f"{chat_id}_{now}_{random.randint(10,99)}"
            active_duels[duel_id] = {
                "chat_id": chat_id,
                "p1": user.id,
                "p1_name": u_data["name"],
                "p2": opp["user_id"],
                "p2_name": opp["name"],
                "bet": bet
            }
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                types.InlineKeyboardButton("⚔️ قبول التحدي", callback_data=f"duel_acc_{duel_id}"),
                types.InlineKeyboardButton("🏳️ انسحاب", callback_data=f"duel_rej_{duel_id}")
            )
            bot.reply_to(
                m,
                f"⚔️🔥 <b>تحدي مباشر في الساحة!</b>\n"
                f"──────────────\n"
                f"▽ : المتحدي ↞ <b>{esc(u_data['name'])}</b>\n"
                f"▽ : الخصم ↞ <a href='tg://user?id={opp['user_id']}'>{esc(opp['name'])}</a>\n"
                f"▽ : قيمة الرهان ↞ <b>{bet} د.ل</b> كاش (الفائز يأخذ {bet*2} د.ل!)",
                reply_markup=kb
            )
        return

    if text in ("توب", "توب الفلوس", "توب الاغنياء"):
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT name, cash FROM users ORDER BY cash DESC LIMIT 10").fetchall()
            conn.close()
        txt = "▽ : <b>🏆 قائمة أصحاب الكاش الظاهر في ليبيا :</b>\n──────────────\n"
        for i, r in enumerate(rows, 1):
            txt += f"{i}. <b>{esc(r['name'])}</b> ↞ {r['cash']} د.ل كاش 💵\n"
        txt += "──────────────\n💡 <i>(الأرصدة المصرفية سرية ولا تظهر في العام 🔒)</i>"
        bot.reply_to(m, txt)
        return

    if text == "توب الحرامية":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT name, steal_success FROM users ORDER BY steal_success DESC LIMIT 10").fetchall()
            conn.close()
        txt = "▽ : <b>🦹‍♂️ أخطر حرامية الجيوب في ليبيا :</b>\n──────────────\n"
        for i, r in enumerate(rows, 1):
            txt += f"{i}. <b>{esc(r['name'])}</b> ↞ {r['steal_success']} عملية ناجحة\n"
        bot.reply_to(m, txt)
        return

    if text == "توب التفاعل":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT name, points, level FROM users ORDER BY points DESC LIMIT 10").fetchall()
            conn.close()
        txt = "▽ : <b>⭐ أساطير التفاعل في البوت :</b>\n──────────────\n"
        for i, r in enumerate(rows, 1):
            txt += f"{i}. <b>{esc(r['name'])}</b> ↞ المستوى {r['level']} ({r['points']} نقطة)\n"
        bot.reply_to(m, txt)
        return

    # ─────────────── 10. التحشيش، الزواج، التسلية، والألعاب ───────────────

    for f_title in FUN_TITLES:
        if (text == f"رفع {f_title}" or text == f"تنزيل {f_title}") and m.reply_to_message:
            t_name = m.reply_to_message.from_user.first_name
            if text.startswith("رفع"):
                bot.reply_to(m, f"▽ : 😂 تم رفع <b>{esc(t_name)}</b> إلى رتبة (<b>{f_title} القروب</b>) بنجاح!")
            else:
                bot.reply_to(m, f"▽ : 😂 تم تنزيل <b>{esc(t_name)}</b> من رتبة (<b>{f_title} القروب</b>)!")
            return

    if text.startswith("نسبة ") and m.reply_to_message:
        kind = text[len("نسبة "):].strip()
        t_name = m.reply_to_message.from_user.first_name
        bot.reply_to(m, f"▽ : نسبة <b>{esc(kind)}</b> لـ <b>{esc(t_name)}</b> هي ↞ <b>{random.randint(1, 100)}%</b> 🔥")
        return

    if text == "شنو رايك بهذا" and m.reply_to_message:
        bot.reply_to(m, f"▽ : رأيي فيه ↞ {random.choice(OPINIONS_LIST)}")
        return

    if text == "رزله" and m.reply_to_message:
        bot.reply_to(m, f"▽ : {random.choice(ROASTS_LIST)}")
        return

    if text == "انطي هدية" and m.reply_to_message:
        t_name = m.reply_to_message.from_user.first_name
        bot.reply_to(m, f"▽ : أهدى <b>{esc(u_data['name'])}</b> إلى <b>{esc(t_name)}</b> ↞ {random.choice(GIFTS_LIST)}")
        return

    # الزواج والطلاق
    if text.startswith("زواج") and m.reply_to_message:
        partner = ensure_user(m.reply_to_message.from_user)
        if partner["user_id"] == user.id or m.reply_to_message.from_user.is_bot:
            return
        if u_data["married_to"] != 0 or partner["married_to"] != 0:
            bot.reply_to(m, "▽ : ❌ أحد الطرفين متزوج مسبقاً!")
            return
        parts = text.split()
        dowry = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2000
        if u_data["cash"] < dowry:
            bot.reply_to(m, f"▽ : ❌ لا تملك قيمة المهر ({dowry} د.ل) كاش في جيبك!")
            return
        update_user_field(user.id, cash=u_data["cash"] - dowry, married_to=partner["user_id"], dowry=dowry)
        update_user_field(partner["user_id"], cash=partner["cash"] + dowry, married_to=user.id, dowry=dowry)
        bot.reply_to(
            m,
            f"💍🎉 <b>زغروطة ليبية يا بنات! لولولولوليش!</b>\n"
            f"──────────────\n"
            f"▽ : تم عقد قران <b>{esc(u_data['name'])}</b> على <b>{esc(partner['name'])}</b>\n"
            f"▽ : قيمة المهر المدفوع ↞ <b>{dowry} د.ل</b> كاش!"
        )
        return

    if text in ("طلاق", "خلع"):
        if u_data["married_to"] == 0:
            bot.reply_to(m, "▽ : أنت أعزب أصلاً!")
            return
        sp_id = u_data["married_to"]
        update_user_field(user.id, married_to=0, dowry=0)
        update_user_field(sp_id, married_to=0, dowry=0)
        bot.reply_to(m, "▽ : 💔 تم الانفصال رسمياً في محكمة الأسرة.. كل واحد يمشي في حاله!")
        return

    if text == "زواجي":
        if u_data["married_to"] == 0:
            bot.reply_to(m, "▽ : الحالة الاجتماعية ↞ أعزب/عزباء 💔")
        else:
            sp = get_user_by_id(u_data["married_to"])
            sp_name = sp["name"] if sp else "شريك الحياة"
            bot.reply_to(m, f"▽ : 💍 متزوج من ↞ <b>{esc(sp_name)}</b> (المهر: {u_data['dowry']} د.ل)")
        return

    # التسلية والألعاب
    if text in QUESTIONS_BANK:
        q, ans = random.choice(QUESTIONS_BANK[text])
        reward = 500
        active_games[chat_id] = {"answer": ans, "reward": reward}
        bot.reply_to(m, f"🎲 <b>مسابقة ({text}) السريعة :</b>\n▽ : {q}\n▽ : الجائزة ↞ <b>{reward} د.ل</b> لأول إجابة صحيحة!")
        return

    if text == "رياضيات":
        a, b = random.randint(12, 65), random.randint(12, 65)
        active_games[chat_id] = {"answer": str(a + b), "reward": 450}
        bot.reply_to(m, f"🧮 <b>مسابقة الرياضيات :</b>\n▽ : كم ناتج ( <b>{a} + {b}</b> ) ؟\n▽ : الجائزة ↞ <b>450 د.ل</b>!")
        return

    if text in ("حجرة", "ورقة", "مقص"):
        bot_c = random.choice(["حجرة", "ورقة", "مقص"])
        if text == bot_c:
            bot.reply_to(m, f"▽ : اخترتُ ({bot_c}) وأنت ({text}) ↞ تعادل! 🤝")
        elif (text == "حجرة" and bot_c == "مقص") or (text == "ورقة" and bot_c == "حجرة") or (text == "مقص" and bot_c == "ورقة"):
            update_user_field(user.id, cash=u_data["cash"] + 250)
            bot.reply_to(m, f"▽ : اخترتُ ({bot_c}) وأنت ({text}) ↞ فزتَ عليّ وربحت <b>250 د.ل</b> كاش! 🎉")
        else:
            bot.reply_to(m, f"▽ : اخترتُ ({bot_c}) وأنت ({text}) ↞ فزتُ عليك! 😎")
        return

    if text == "غنيلي":
        bot.reply_to(m, random.choice(SONGS_LIST))
        return
    if text in ("شعر", "قصيدة"):
        bot.reply_to(m, random.choice(POEMS_LIST))
        return
    if text in ("نكتة", "نكته"):
        bot.reply_to(m, random.choice(JOKES_LIST))
        return
    if text == "اذكار":
        bot.reply_to(m, random.choice(ADHKAR_LIST))
        return
    if text == "لو خيروك":
        bot.reply_to(m, random.choice(LAW_KHAYAROUK_LIST))
        return
    if text == "صراحة":
        bot.reply_to(m, random.choice(SARAHA_QUESTIONS))
        return

    if text.startswith(("حظ ", "مضاربة ", "استثمار ")):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            amt = int(parts[1])
            if 0 < amt <= u_data["cash"]:
                if random.choice([True, False]):
                    prof = int(amt * 0.8)
                    update_user_field(user.id, cash=u_data["cash"] + prof)
                    bot.reply_to(m, f"▽ : 📈 صفقة رابحة! كسبت <b>{prof} د.ل</b> كاش إضافي 🎉")
                else:
                    update_user_field(user.id, cash=u_data["cash"] - amt)
                    bot.reply_to(m, f"▽ : 📉 للأسف خسرت الرهان (<b>{amt} د.ل</b>) 😢")
        return

    if text.startswith("اكشط "):
        code = text[len("اكشط "):].strip().upper()
        with db_lock:
            conn = get_db()
            row = conn.execute("SELECT * FROM scratch_cards WHERE code = ?", (code,)).fetchone()
            if not row or row["claimed_by"] != 0:
                conn.close()
                bot.reply_to(m, "▽ : ❌ كرت اكشطها غير صحيح أو تم استخدامه مسبقاً!")
                return
            amt = row["amount"]
            conn.execute("UPDATE scratch_cards SET claimed_by = ? WHERE code = ?", (user.id, code))
            conn.commit()
            conn.close()
        update_user_field(user.id, cash=u_data["cash"] + amt)
        bot.reply_to(m, f"▽ : 🎉 مبروك! كشطت الكرت (<code>{esc(code)}</code>) وربحت <b>{amt} د.ل</b> كاش!")
        return

    # ─────────────── 11. أوامر المطور الأساسي (MG) السرية ───────────────
    if user.id == ADMIN_ID:
        _handle_dev_commands(m, text, u_data)


def _handle_dev_commands(m: types.Message, text: str, u_data: dict):
    if m.from_user.id != ADMIN_ID:
        return

    if text == "م المطور":
        bot.reply_to(m, render_menu("menu_dev"), reply_markup=get_commands_kb(ADMIN_ID))
        return

    if text.startswith("تغيير اسم البوت "):
        new_n = text[len("تغيير اسم البوت "):].strip()
        if new_n:
            set_bot_name(new_n)
            bot.reply_to(m, f"▽ : ⚡ تم تغيير اسم البوت إلى (<b>{esc(new_n)}</b>) بنجاح!")
        return

    if text.startswith("اضف فلوس ") and m.reply_to_message:
        parts = text.split()
        if parts[-1].isdigit():
            amt = int(parts[-1])
            t_u = ensure_user(m.reply_to_message.from_user)
            update_user_field(t_u["user_id"], bank_balance=t_u["bank_balance"] + amt)
            bot.reply_to(m, f"▽ : ⚡ تم إيداع <b>{amt} د.ل</b> في المصرف السري للعضو <b>{esc(t_u['name'])}</b>!")
        return

    if text == "تصفير فلوسه" and m.reply_to_message:
        t_u = ensure_user(m.reply_to_message.from_user)
        update_user_field(t_u["user_id"], cash=0, bank_balance=0)
        bot.reply_to(m, f"▽ : ⚡ تم تصفير كاش ومصرف <b>{esc(t_u['name'])}</b> بالكامل!")
        return

    if text == "اطلاق سراح" and m.reply_to_message:
        t_u = ensure_user(m.reply_to_message.from_user)
        update_user_field(t_u["user_id"], jail_until=0, wanted=0)
        bot.reply_to(m, f"▽ : ⚡ عفو رئاسي من المطور MG! تم إطلاق سراح <b>{esc(t_u['name'])}</b> فوراً.")
        return

    if text.startswith("صنع اكشطها "):
        parts = text.split()
        if len(parts) == 4 and parts[3].isdigit():
            code, amt = parts[2].upper(), int(parts[3])
            with db_lock:
                conn = get_db()
                conn.execute("INSERT OR REPLACE INTO scratch_cards (code, amount, claimed_by) VALUES (?,?,0)", (code, amt))
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : ⚡ تم صنع كرت اكشطها!\n▽ : الكود ↞ <code>{esc(code)}</code> | القيمة ↞ <b>{amt} د.ل</b>")
        return

    if text == "قائمة اكشطها":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM scratch_cards WHERE claimed_by = 0").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "▽ : لا توجد كروت غير مستخدمة حالياً.")
        else:
            txt = "▽ : <b>🎫 كروت اكشطها المتاحة :</b>\n──────────────\n"
            for r in rows:
                txt += f"• الكود: <code>{esc(r['code'])}</code> ↞ {r['amount']} د.ل\n"
            bot.reply_to(m, txt)
        return

    if text == "الهمسات":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM whispers ORDER BY id DESC LIMIT 15").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "▽ : لا توجد همسات مسجلة بعد.")
        else:
            txt = "🕵️‍♂️ <b>سجل آخر 15 همسة سرية (خاص بالمطور MG) :</b>\n──────────────\n"
            for r in rows:
                txt += f"#{r['id']} | <b>{esc(r['sender_name'])}</b> ⬅️ <b>{esc(r['target_name'])}</b>:\n  └ <code>{esc(r['text'])}</code>\n"
            bot.reply_to(m, txt)
        return

    if text == "الاحصائيات":
        with db_lock:
            conn = get_db()
            u_cnt = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            g_cnt = conn.execute("SELECT COUNT(*) as c FROM groups").fetchone()["c"]
            w_cnt = conn.execute("SELECT COUNT(*) as c FROM whispers").fetchone()["c"]
            conn.close()
        bot.reply_to(
            m,
            f"📊 <b>إحصائيات البوت (خاص بالمطور MG) :</b>\n"
            f"──────────────\n"
            f"▽ : عدد المواطنين المسجلين ↞ <b>{u_cnt}</b>\n"
            f"▽ : عدد المجموعات المفعلة ↞ <b>{g_cnt}</b>\n"
            f"▽ : عدد الهمسات المرسلة ↞ <b>{w_cnt}</b>"
        )
        return

    if text == "نسخة احتياطية" and DB_FILE.exists():
        with open(DB_FILE, "rb") as f:
            bot.send_document(
                ADMIN_ID,
                f,
                caption="📦 نسخة احتياطية كاملة لقاعدة بيانات أركان\n▽ : رد على هذا الملف بكلمة <code>استعادة</code> لاسترجاعها في أي وقت."
            )
        return

    if text == "استعادة" and m.reply_to_message and m.reply_to_message.document:
        try:
            fi = bot.get_file(m.reply_to_message.document.file_id)
            dw = bot.download_file(fi.file_path)
            with db_lock:
                with open(DB_FILE, "wb") as f:
                    f.write(dw)
            init_db()
            bot.reply_to(m, "▽ : ✅ تمت استعادة قاعدة البيانات بنجاح!")
        except Exception as e:
            bot.reply_to(m, f"▽ : ❌ خطأ أثناء الاستعادة: {e}")
        return

    if text.startswith("اذاعة "):
        b_msg = text[len("اذاعة "):].strip()
        with db_lock:
            conn = get_db()
            g_rows = conn.execute("SELECT chat_id FROM groups").fetchall()
            conn.close()
        sent = 0
        for r in g_rows:
            try:
                bot.send_message(r["chat_id"], f"📢 <b>إذاعة رسمية من إدارة البوت :</b>\n──────────────\n{esc(b_msg)}")
                sent += 1
            except Exception:
                pass
        bot.reply_to(m, f"▽ : ✅ تم إرسال الإذاعة إلى <b>{sent}</b> مجموعة بنجاح!")
        return


# ══════════════════════════════════════════════════════════════════
# 🔘 معالج الأزرار الشفافة والهمسات والكشف المصرفي السري
# ══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def on_callback(call: types.CallbackQuery):
    try:
        data = call.data or ""
        user = call.from_user
        chat_id = call.message.chat.id
        b_name = get_bot_name()

        # فحص زر تحقق الاشتراك الإجباري
        if data == "check_sub":
            if is_channel_member(user.id):
                bot.answer_callback_query(call.id, "✅ تم التحقق من اشتراكك بنجاح! يمكنك استخدام البوت الآن.", show_alert=True)
                if call.message.chat.type == "private":
                    bot.send_message(chat_id, "▽ : أهلاً بك! أضف البوت لمجموعتك واستمتع بالأوامر.", reply_markup=get_private_start_kb(user.id))
                else:
                    bot.edit_message_text(render_menu("main"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_commands_kb(user.id))
            else:
                bot.answer_callback_query(call.id, f"❌ لم تشترك في القناة @{CHANNEL_USERNAME} بعد! اشترك ثم اضغط تحقق.", show_alert=True)
            return

        # أزرار واجهة الخاص
        if data == "install_bot_info":
            bot.answer_callback_query(
                call.id,
                f"⚙️ لتنصيب بوت أو الاستفسار تواصل مع المطور الأساسي MG عبر زر (المطور) أو قناة السورس @{CHANNEL_USERNAME}",
                show_alert=True
            )
            return

        if data == "private_member_cmds":
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("اضفني لمجموعتك لتشغيل الأوامر ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"))
            bot.send_message(
                chat_id,
                render_menu("main") + "\n\n⚠️ <b>ملاحظة:</b> جميع الأوامر والألعاب تشتغل داخل المجموعات فقط!",
                reply_markup=kb
            )
            bot.answer_callback_query(call.id)
            return

        # حماية صارمة لزر لوحة المطور الأساسي MG
        if data == "menu_dev":
            if user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "🚫 هذا القسم سري وخاص بالمطور الأساسي (MG) فقط!", show_alert=True)
                return
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="menu_main"))
            bot.edit_message_text(render_menu("menu_dev"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=kb)
            return

        if data == "menu_main":
            bot.edit_message_text(render_menu("main"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_commands_kb(user.id))
            return

        if data in MENU_TEXTS:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 رجوع للأوامر الرئيسية", callback_data="menu_main"))
            bot.edit_message_text(render_menu(data), chat_id=chat_id, message_id=call.message.message_id, reply_markup=kb)
            return

        # لوحة القفل والفتح
        if data == "locks_panel":
            if get_rank(chat_id, user.id) < 2:
                bot.answer_callback_query(call.id, "❌ هذه اللوحة مخصصة للادمنية فما فوق فقط!", show_alert=True)
                return
            bot.edit_message_text(f"▽ : لوحة القفل والفتح لبوت ({esc(b_name)}) :", chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_locks_kb(chat_id, user.id))
            return

        if data.startswith("togglelock_"):
            if get_rank(chat_id, user.id) < 2:
                bot.answer_callback_query(call.id, "❌ للادمنية فقط!", show_alert=True)
                return
            lk = data.split("_", 1)[1]
            st = not get_group_locks(chat_id).get(lk, False)
            set_group_lock(chat_id, lk, st)
            bot.answer_callback_query(call.id, f"▽ : تم {'قفل 🔒' if st else 'فتح 🔓'} {lk}")
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_locks_kb(chat_id, user.id))
            return

        # لوحة التفعيل والتعطيل
        if data == "settings_panel":
            if get_rank(chat_id, user.id) < 3:
                bot.answer_callback_query(call.id, "❌ هذه اللوحة مخصصة للمدراء فما فوق فقط!", show_alert=True)
                return
            bot.edit_message_text(f"▽ : لوحة التفعيل والتعطيل لبوت ({esc(b_name)}) :", chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_settings_kb(chat_id))
            return

        if data.startswith("toggleset_"):
            if get_rank(chat_id, user.id) < 3:
                bot.answer_callback_query(call.id, "❌ للمدراء فما فوق فقط!", show_alert=True)
                return
            sk = data.split("_", 1)[1]
            st = not get_group_settings(chat_id).get(sk, True)
            set_group_setting(chat_id, sk, st)
            bot.answer_callback_query(call.id, f"▽ : تم {'تفعيل ✅' if st else 'تعطيل ❌'} {sk}")
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_settings_kb(chat_id))
            return

        # فتح حساب مصرفي
        if data.startswith("openbank_"):
            b_t = data.split("_", 1)[1]
            u = ensure_user(user)
            if u["bank_name"] == "بدون مصرف":
                update_user_field(user.id, bank_name=b_t, bank_balance=u["bank_balance"] + 1000)
                bot.answer_callback_query(call.id, f"🎉 مبروك! تم فتح حسابك في ({b_t}) وإيداع 1000 د.ل هدية سرياً!", show_alert=True)
                bot.edit_message_text(
                    f"▽ : 🏦 تم فتح حساب مصرفي للعميل <b>{esc(u['name'])}</b> في (<b>{esc(b_t)}</b>) بنجاح!\n"
                    f"▽ : تمت إضافة <b>1000 د.ل</b> هدية في رصيدك المصرفي السري 🔒",
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=build_bank_secret_kb(user.id)
                )
            else:
                bot.answer_callback_query(call.id, "لديك حساب مصرفي مسبقاً!", show_alert=True)
            return

        # 🔒 كشف رصيد المصرف السري في نافذة منبثقة لصاحب الحساب فقط!
        if data.startswith("secretbank_"):
            owner_id = int(data.split("_")[1])
            if user.id not in (owner_id, ADMIN_ID):
                bot.answer_callback_query(call.id, "🚫 بطاقة الصراف هذه سرية وخاصة بصاحب الحساب فقط!", show_alert=True)
                return
            owner = get_user_by_id(owner_id)
            if not owner:
                return
            u_stk = json.loads(owner.get("stocks") or "{}")
            stk_summary = "، ".join([f"{k}: {v}" for k, v in u_stk.items() if v > 0]) or "لا توجد أسهم"
            secret_msg = (
                f"🏦 كشف الخزنة المصرفية السري :\n"
                f"━━━━━━━━━━━━━━\n"
                f"🏛️ المصرف : {owner['bank_name']}\n"
                f"💳 رصيد المصرف الآمن : {owner['bank_balance']} د.ل\n"
                f"💵 الكاش في الجيب : {owner['cash']} د.ل\n"
                f"📉 القروض : {owner['loan']} د.ل\n"
                f"📈 الأسهم : {stk_summary}"
            )
            bot.answer_callback_query(call.id, secret_msg, show_alert=True)
            return

        # 📩 إرسال كشف الحساب المفصل لخاص العميل
        if data.startswith("dmbank_"):
            owner_id = int(data.split("_")[1])
            if user.id != owner_id:
                bot.answer_callback_query(call.id, "🚫 هذا الزر خاص بصاحب الحساب فقط!", show_alert=True)
                return
            owner = get_user_by_id(owner_id)
            if not owner:
                return
            u_stk = json.loads(owner.get("stocks") or "{}")
            stk_summary = "، ".join([f"{k} ({v} سهم)" for k, v in u_stk.items() if v > 0]) or "لا توجد أسهم"
            try:
                bot.send_message(
                    user.id,
                    f"🏦 <b>التقرير المالي السري المفصل — {esc(owner['bank_name'])}</b>\n"
                    f"──────────────\n"
                    f"▽ : العميل ↞ <b>{esc(owner['name'])}</b>\n"
                    f"▽ : رصيد المصرف السري ↞ <b>{owner['bank_balance']} د.ل</b> 🔒\n"
                    f"▽ : الكاش في الجيب ↞ <b>{owner['cash']} د.ل</b> 💵\n"
                    f"▽ : القروض المستحقة ↞ <b>{owner['loan']} د.ل</b>\n"
                    f"▽ : محفظة الأسهم ↞ <b>{esc(stk_summary)}</b>\n"
                    f"▽ : العقار ↞ <b>{esc(owner['house'])}</b>\n"
                    f"▽ : السيارة ↞ <b>{esc(owner['car'])}</b>\n"
                    f"▽ : المشروع ↞ <b>{esc(owner['business'])}</b>"
                )
                bot.answer_callback_query(call.id, "✅ تم إرسال كشف حسابك السري إلى خاصك بنجاح!", show_alert=True)
            except Exception:
                bot.answer_callback_query(call.id, "⚠️ افتح محادثة البوت في الخاص واضغط Start أولاً ليتمكن من مراسلتك!", show_alert=True)
            return

        # عرض الهمسة السرية (نفس الصورة رقم 2 بالضبط)
        if data.startswith("whisper_"):
            w_id = int(data.split("_")[1])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM whispers WHERE id = ?", (w_id,)).fetchone()
                conn.close()
            if not row:
                bot.answer_callback_query(call.id, "▽ : عذراً، هذه الهمسة غير موجودة!", show_alert=True)
                return
            if user.id in (row["sender_id"], row["target_id"], ADMIN_ID):
                bot.answer_callback_query(call.id, f"{row['target_name']}\n\n{row['text']}", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "🔒 هذه الهمسة سرية وليست مخصصة لك!", show_alert=True)
            return

        # قبول أو رفض التحدي والمبارزة
        if data.startswith(("duel_acc_", "duel_rej_")):
            duel_id = data.split("_", 2)[2]
            duel = active_duels.get(duel_id)
            if not duel:
                bot.answer_callback_query(call.id, "انتهى هذا التحدي!", show_alert=True)
                return
            if user.id != duel["p2"]:
                bot.answer_callback_query(call.id, "🚫 هذا القرار خاص بالشخص المتحدى فقط!", show_alert=True)
                return
            del active_duels[duel_id]
            if data.startswith("duel_rej_"):
                bot.edit_message_text(
                    f"🏳️ انسحب <b>{esc(duel['p2_name'])}</b> من مواجهة <b>{esc(duel['p1_name'])}</b>!",
                    chat_id=chat_id,
                    message_id=call.message.message_id
                )
                return
            p1_u = get_user_by_id(duel["p1"])
            p2_u = get_user_by_id(duel["p2"])
            bet = duel["bet"]
            if not p1_u or not p2_u or p1_u["cash"] < bet or p2_u["cash"] < bet:
                bot.edit_message_text("❌ أحد الطرفين لم يعد يملك مبلغ الرهان كاش!", chat_id=chat_id, message_id=call.message.message_id)
                return
            if random.choice([True, False]):
                update_user_field(p1_u["user_id"], cash=p1_u["cash"] + bet)
                update_user_field(p2_u["user_id"], cash=p2_u["cash"] - bet)
                winner_name, loser_name = p1_u["name"], p2_u["name"]
            else:
                update_user_field(p2_u["user_id"], cash=p2_u["cash"] + bet)
                update_user_field(p1_u["user_id"], cash=p1_u["cash"] - bet)
                winner_name, loser_name = p2_u["name"], p1_u["name"]
            bot.edit_message_text(
                f"⚔️🔥 <b>نتيجة المبارزة الحاسمة!</b>\n"
                f"──────────────\n"
                f"▽ : اكتسح البطل <b>{esc(winner_name)}</b> خصمه <b>{esc(loser_name)}</b>!\n"
                f"▽ : وانتزع جائزة الرهان <b>{bet} د.ل</b> كاش! 💵🏆",
                chat_id=chat_id,
                message_id=call.message.message_id
            )
            return

    except Exception as e:
        logging.error("خطأ في معالجة الزر: %s", e)


# ══════════════════════════════════════════════════════════════════
# 🚀 نقطة التشغيل الرئيسية (مع منع تعارض 409)
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        me = bot.get_me()
        if me.username:
            BOT_USERNAME = me.username
        logging.info("تم الاتصال بالبوت بنجاح: @%s", BOT_USERNAME)
    except Exception as e:
        logging.warning("تعذر جلب يوزر البوت تلقائياً: %s", e)

    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception:
        pass

    # تشغيل سيرفر الويب في الخلفية لـ Render و UptimeRobot
    threading.Thread(target=run_web, daemon=True).start()

    # تشغيل البوت مع حماية ضد التوقف
    while True:
        try:
            bot.infinity_polling(
                timeout=20,
                long_polling_timeout=20,
                skip_pending=True,
                allowed_updates=["message", "edited_message", "callback_query", "chat_member"]
            )
        except ApiTelegramException as api_err:
            if api_err.error_code == 409:
                logging.warning("تعارض 409 مؤقت أثناء تحديث السيرفر.. الانتظار 5 ثوانٍ لإغلاق النسخة القديمة...")
                time.sleep(5)
            else:
                logging.error("خطأ تيليجرام: %s", api_err)
                time.sleep(3)
        except Exception as err:
            logging.error("خطأ اتصال عام: %s", err)
            time.sleep(3)
