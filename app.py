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

# ─────────────── الإعدادات الأساسية ───────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID: int = 1053838533  # المطور الأساسي MG
TARGET_CHANNEL_ID: int = -1003747214322
CHANNEL_USERNAME: str = "AurelianMind03"
BOT_USERNAME: str = "ArkanLyBot"
BOT_DEFAULT_NAME: str = "أركان"
DB_FILE: Path = Path("arkan_libya.db")
# ──────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN غير موجود في Environment Variables")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ─────────────── Flask Web Server ───────────────
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "✅ البوت أركان الليبي شغّال بكامل الميزات!", 200

@web_app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


# ─────────────── قاعدة البيانات الشاملة ───────────────
db_lock = threading.Lock()

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

        # جدول السوق الحر (بيع السيارات والبيوت بين اللاعبين)
        c.execute("""
            CREATE TABLE IF NOT EXISTS marketplace (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                seller_name TEXT,
                item_type TEXT, -- 'house' or 'car'
                item_name TEXT,
                price INTEGER
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                locks TEXT DEFAULT '{}',
                welcome_enabled INTEGER DEFAULT 1,
                welcome_text TEXT DEFAULT 'مرحبتين بيك يا غالي في لمّتنا الليبية 🇱🇾 نورت القروب!',
                rules_text TEXT DEFAULT 'احترام الجميع وعدم نشر الروابط أو الشتائم.',
                replies TEXT DEFAULT '{}',
                fun_lists TEXT DEFAULT '{}'
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


# ─────────────── ردود ومحتوى التسلية ───────────────

BOT_CALL_REPLIES = [
    "عيون {name} يا غالي، تفضل شن تبي؟ 😎🇱🇾",
    "نعم يا برو، {name} في الخدمة! اكتب <code>الاوامر</code> وشوف العجب 🔥",
    "ها يا غالي تنادي فيا؟ كان تبي سلف راهو المصرف مسكر 😂🏦",
    "لبيه! {name} حاضر وناظر، شن الجو عندكم؟ ✨",
    "تفضل يا مدير، {name} يسمع فيك 🫡",
    "نعم يا ودي! تبي تسرق ولا تبي تشتغل؟ اكتب <code>م8</code> وشوف عالم ليبيا الواقعي 😂💸",
    "يا مرحبتين! ناديت {name} ولقيته قدامك، آمرني يا غالي 👑"
]

SONGS_LIST = [
    "🎵 <i>يا غالي لو تبي ترحل، خذ قلبي معاك...</i> 🎶",
    "🎵 <i>طرابلس يا عروس البحر، فيك الزين وفيك السهر...</i> 🇱🇾🎶",
    "🎵 <i>بنغازي يا مربى العز، قلبي لغيرك ما يهتز...</i> 🇱🇾🎶",
    "🎵 <i>اللي باعنا خسر دلعنا، واللي شرانا فوق الراس وضعنا!</i> 🎶",
    "🎵 <i>وينك يا غالي طولت الغيبة، خليت القلب في حيرة وريبة...</i> 🎶"
]

POEMS_LIST = [
    "📜 <b>شعر شعبي ليبي :</b>\nيا صاحبي الدنياامتحانات .. وفيها الصبر مفتاح الفرج\nواللي معاه الله في الأزمات .. يطلع من الضيقة بلا حرج",
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


# ─────────────── الثوابت ───────────────

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
    "صيدلي": {"salary": 2000, "desc": "يبيع الأدوية والإسعافات للمصابين (أمر: بيع دواء بالرد)"},
    "ميكانيكي": {"salary": 1800, "desc": "يصلح ويعدل السيارات ويكسب أتعاب (أمر: تصليح بالرد)"},
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
    "الكلايش": "📜 الكلايش الطويلة",
    "البوتات": "🤖 البوتات",
    "الفشار": "🤬 الفشار والشتائم",
    "الدردشة": "💬 الدردشة",
}

BAD_WORDS = [
    "كلب", "حمار", "حيوان", "تافه", "غبي", "صايع", "منيك", "قحبة", "شرموط", "عرص", "زبي", "طيز", "كس", "نيك"
]

FUN_TITLES = [
    "ملك", "ملكه", "طلي", "طامس", "عسل", "كيك", "زاحف", "غبي", "بقره", "صخل", "لوكي"
]

active_games = {}


# ─────────────── دوال المساعدة ───────────────

def esc(text: str) -> str:
    return html.escape(str(text or ""))

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
                "INSERT INTO users (user_id, name, username, msg_count) VALUES (?, ?, ?, 1)",
                (user.id, full_name, username)
            )
            conn.commit()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
            row = c.fetchone()
        else:
            # 🆕 نظام نقاط التفاعل التلقائي وترقية المستويات
            new_msgs = row["msg_count"] + 1
            new_pts = row["points"] + 1
            new_lvl = row["level"]
            if new_pts >= new_lvl * 50:  # كل 50 نقطة يرتفع مستوى المواطن
                new_lvl += 1
            c.execute(
                "UPDATE users SET name = ?, username = ?, msg_count = ?, points = ?, level = ? WHERE user_id = ?",
                (full_name, username, new_msgs, new_pts, new_lvl, user.id)
            )
            conn.commit()
        data = dict(row)
        conn.close()
        return data

def get_user_by_id(user_id: int) -> dict | None:
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

def get_user_by_username(username: str) -> dict | None:
    username = username.lstrip("@").lower()
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE LOWER(username) = ?", (username,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

def resolve_target_user(m: types.Message, text: str) -> dict | None:
    if m.reply_to_message and m.reply_to_message.from_user:
        return ensure_user(m.reply_to_message.from_user)
    parts = text.split()
    for p in parts:
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
            c.execute(
                "INSERT INTO groups (chat_id, title, locks) VALUES (?, ?, ?)",
                (chat.id, chat.title or "مجموعة", json.dumps({"الفشار": True}))
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

def get_group_locks(chat_id: int) -> dict:
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT locks FROM groups WHERE chat_id = ?", (chat_id,))
        row = c.fetchone()
        conn.close()
        if row and row["locks"]:
            try:
                return json.loads(row["locks"])
            except Exception:
                return {}
        return {}

def set_group_lock(chat_id: int, lock_name: str, state: bool):
    locks = get_group_locks(chat_id)
    locks[lock_name] = state
    with db_lock:
        conn = get_db()
        conn.execute("UPDATE groups SET locks = ? WHERE chat_id = ?", (json.dumps(locks), chat_id))
        conn.commit()
        conn.close()

def get_rank(chat_id: int, user_id: int) -> int:
    if user_id == ADMIN_ID:
        return 99
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT rank_level FROM ranks WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
        row = c.fetchone()
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


# ─────────────── فحص الاشتراك الإجباري ───────────────

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
            f"📢 اشترك في قناة المطور @{CHANNEL_USERNAME}",
            url=f"https://t.me/{CHANNEL_USERNAME}"
        ),
        types.InlineKeyboardButton(
            "✅ تم الاشتراك — تحقّق الآن",
            callback_data="check_sub"
        )
    )
    return kb


# ─────────────── القوائم والأزرار التفاعلية ───────────────

def get_commands_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("م1 الحماية", callback_data="menu_1"),
        types.InlineKeyboardButton("م2 الادمنية", callback_data="menu_2"),
        types.InlineKeyboardButton("م3 المدراء", callback_data="menu_3"),
        types.InlineKeyboardButton("م4 المنشئين", callback_data="menu_4"),
        types.InlineKeyboardButton("م5 المالكين", callback_data="menu_5"),
        types.InlineKeyboardButton("م6 التحشيش", callback_data="menu_6"),
        types.InlineKeyboardButton("م7 التسلية", callback_data="menu_7"),
        types.InlineKeyboardButton("م8 البنك الليبي", callback_data="menu_8"),
        types.InlineKeyboardButton("م9 التنظيف", callback_data="menu_9"),
    )
    kb.row(
        types.InlineKeyboardButton("🎮 الالعاب", callback_data="menu_games"),
        types.InlineKeyboardButton("⚡ م المطور", callback_data="menu_dev"),
    )
    kb.row(
        types.InlineKeyboardButton("🔒 لوحة القفل والفتح", callback_data="locks_panel"),
    )
    kb.row(
        types.InlineKeyboardButton(f"📢 قناة السورس @{CHANNEL_USERNAME}", url=f"https://t.me/{CHANNEL_USERNAME}")
    )
    return kb

MENU_TEXTS = {
    "main": (
        "🇱🇾 <b>أوامر البوت ({bot_name}) الرئيسية :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "∇ : <b>م1</b> ~ الحماية والأقفال\n"
        "∇ : <b>م2</b> ~ أوامر الادمنية\n"
        "∇ : <b>م3</b> ~ أوامر المدراء والردود\n"
        "∇ : <b>م4</b> ~ أوامر المنشئين\n"
        "∇ : <b>م5</b> ~ أوامر المالكين\n"
        "∇ : <b>م6</b> ~ أوامر التحشيش والالقاب\n"
        "∇ : <b>م7</b> ~ أوامر التسلية والهمسة\n"
        "∇ : <b>م8</b> ~ البنك والحياة الواقعية الليبية + <b>السوق الحر</b>\n"
        "∇ : <b>م9</b> ~ أوامر التنظيف والمسح\n"
        "━━━━━━━━━━━━━━━\n"
        "💡 <i>نادِ البوت باسمه (<b>{bot_name}</b>) أو اكتب الأوامر مباشرة بدون ( / )</i>"
    ),
    "menu_1": (
        "🛡️ <b>م1 ~ أوامر الحماية :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "∇ : <code>قفل</code> ، <code>فتح</code> + الأمر :\n"
        "• الروابط ~ اليوزرات ~ التوجيه ~ التعديل ~ الصور ~ الفيديو ~ الملصقات ~ المتحركة ~ الكلايش ~ البوتات ~ الفشار ~ الدردشة\n"
        "━━━━━━━━━━━━━━━\n"
        "∇ : <code>الحماية</code> ← لوحة الأزرار"
    ),
    "menu_2": (
        "👮‍♂️ <b>م2 ~ أوامر ادمنية المجموعة :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>حظر</code> ~ <code>الغاء حظر</code> ~ <code>طرد</code>\n"
        "• <code>كتم</code> ~ <code>الغاء كتم</code> ~ <code>انذار</code> ~ <code>حذف الانذارات</code>\n"
        "• <code>تثبيت</code> ~ <code>الغاء تثبيت</code> ~ <code>كشف</code> ~ <code>ايدي</code>\n"
        "• <code>رتبتي</code> ~ <code>لقبي</code> ~ <code>رفع مميز</code>"
    ),
    "menu_3": (
        "💼 <b>م3 ~ أوامر المدراء والردود :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>رفع ادمن</code> ~ <code>تنزيل ادمن</code> (بالرد)\n"
        "• <code>اضف رد</code> (مثال: اضف رد السلام=وعليكم السلام)\n"
        "• <code>مسح رد</code> + الكلمة ~ <code>الردود</code> ~ <code>مسح الردود</code>\n"
        "• <code>ضع ترحيب</code> ~ <code>تفعيل الترحيب</code> ~ <code>تعطيل الترحيب</code>"
    ),
    "menu_4": (
        "🎖️ <b>م4 ~ أوامر المنشئين :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>رفع مدير</code> ~ <code>تنزيل مدير</code> (بالرد)\n"
        "• <code>المدراء</code> ~ <code>المنشئين</code> ~ <code>تنزيل الكل</code>"
    ),
    "menu_5": (
        "👑 <b>م5 ~ أوامر مالك المجموعة :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>رفع نفسي مالك</code> (لصاحب المجموعة الأصلي)\n"
        "• <code>رفع مالك</code> ~ <code>تنزيل مالك</code> ~ <code>ضع لقب</code> ~ <code>المالكين</code>"
    ),
    "menu_6": (
        "😂 <b>م6 ~ أوامر التحشيش والألقاب :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>رفع ملك</code> ~ <code>رفع طلي</code> ~ <code>رفع عسل</code> ~ <code>رفع زاحف</code>\n"
        "• <code>نسبة الحب</code> ~ <code>نسبة الذكاء</code> ~ <code>شنو رايك بهذا</code> ~ <code>رزله</code>"
    ),
    "menu_7": (
        "🎉 <b>م7 ~ أوامر التسلية والزواج والهمسة :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>همسة</code> + الكلام ~ <code>زواج</code> ~ <code>طلاق</code> ~ <code>زواجي</code>\n"
        "• <code>غنيلي</code> ~ <code>شعر</code> ~ <code>نكتة</code> ~ <code>اذكار</code> ~ <code>لو خيروك</code> ~ <code>صراحة</code>"
    ),
    "menu_8": (
        "🏦 <b>م8 ~ البنك، الحياة الواقعية، و⚡ السوق الحر :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>انشاء حساب</code> ~ <code>حسابي</code> ~ <code>ايداع</code> ~ <code>سحب</code> ~ <code>تحويل</code> ~ <code>قرض</code>\n"
        "• <code>الوظائف</code> ~ <code>وظيفة دكتور/مبرمج/شرطي/صيدلي/ميكانيكي/تاجر</code>\n"
        "• <code>راتب</code> ~ <code>علاج</code> ~ <code>تصليح</code> ~ <code>قبض</code> ~ <code>اختراق صراف</code>\n"
        "• <code>المدن</code> ~ <code>سفر بنغازي</code> ~ <code>تهريب بضاعة</code>\n"
        "• <code>العقارات</code> ~ <code>شراء بيت</code> ~ <code>بيع بيت</code>\n"
        "• <code>السيارات</code> ~ <code>شراء سيارة</code> ~ <code>بيع سيارة</code> ~ <code>سباق</code>\n"
        "• <code>البورصة</code> ~ <code>شراء اسهم المدار 10</code> ~ <code>بيع اسهم المدار</code>\n"
        "• <code>السوق الحر</code> ~ <code>عرض بيت للبيع 45000</code> ~ <code>عرض سيارة للبيع 12000</code> ~ <code>شراء معروض 1</code>\n"
        "• <code>سرقة</code> ~ <code>سرقة المصرف</code> ~ <code>دفع كفالة</code>"
    ),
    "menu_9": (
        "🧹 <b>م9 ~ التنظيف والمسح :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>مسح</code> (بالرد) ~ <code>مسح 20</code> ~ <code>اطردني</code>"
    ),
    "menu_games": (
        "🎮 <b>ألعاب البوت :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>اسئلة</code> ~ <code>لغز</code> ~ <code>عواصم</code> ~ <code>فكك</code> ~ <code>عكس</code> ~ <code>معاني</code> ~ <code>رياضيات</code>\n"
        "• <code>حجرة ورقة مقص</code> ~ <code>حظ 500</code> ~ <code>اكشط CODE</code>"
    ),
    "menu_dev": (
        "⚡ <b>أوامر المطور (MG) :</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "• <code>تغيير اسم البوت</code> ~ <code>اضف فلوس</code> ~ <code>تصفير فلوسه</code> ~ <code>اطلاق سراح</code>\n"
        "• <code>صنع اكشطها</code> ~ <code>الهمسات</code> ~ <code>اذاعة</code> ~ <code>نسخة احتياطية</code> ~ <code>استعادة</code>"
    )
}

def render_menu(key: str) -> str:
    return MENU_TEXTS[key].replace("{bot_name}", esc(get_bot_name()))

def build_locks_kb(chat_id: int) -> types.InlineKeyboardMarkup:
    locks = get_group_locks(chat_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for key, label in LOCK_TYPES.items():
        status = "✅" if locks.get(key, False) else "❌"
        buttons.append(
            types.InlineKeyboardButton(f"{label} : {status}", callback_data=f"togglelock_{key}")
        )
    kb.add(*buttons)
    kb.row(types.InlineKeyboardButton("🔙 رجوع للأوامر", callback_data="menu_main"))
    return kb


# ─────────────── بنك الأسئلة والألعاب ───────────────

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


# ─────────────── أحداث الأعضاء والرسائل ───────────────

@bot.message_handler(content_types=["new_chat_members"])
def on_new_member(m: types.Message):
    if m.chat.type not in ("group", "supergroup"):
        return
    grp = ensure_group(m.chat)
    locks = get_group_locks(m.chat.id)
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
                        f"🇱🇾 <b>تم تفعيل البوت ({esc(b_name)}) للحماية والحياة الواقعية بنجاح!</b>\n\n"
                        "👑 لكي يتحكم صاحب المجموعة بالبوت، ارفع البوت مشرفاً ثم اكتب:\n"
                        "<code>رفع نفسي مالك</code>\n\n"
                        f"🗣️ نادِ البوت بكتابة: <code>{esc(b_name)}</code> أو <code>بوت</code>\n"
                        "📖 ولعرض الأوامر اكتب: <code>الاوامر</code>"
                    ),
                    reply_markup=get_commands_kb()
                )
            elif locks.get("البوتات", False):
                try:
                    bot.ban_chat_member(m.chat.id, new_user.id)
                except Exception:
                    pass
        else:
            ensure_user(new_user)
            if grp.get("welcome_enabled", 1):
                w_text = grp.get("welcome_text") or "مرحبتين بيك يا غالي نورت القروب 🇱🇾"
                bot.reply_to(m, f"👋 أهلاً بك يا <a href='tg://user?id={new_user.id}'>{esc(new_user.first_name)}</a>\n💬 {esc(w_text)}")


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
    if locks.get("الدردشة") or (m.forward_from and locks.get("التوجيه")) or (m.content_type == "photo" and locks.get("الصور")) or (m.content_type == "video" and locks.get("الفيديو")) or (m.content_type == "sticker" and locks.get("الملصقات")):
        del_msg = True
    if del_msg:
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except Exception:
            pass


@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message):
    u = ensure_user(m.from_user)
    b_name = get_bot_name()
    if not is_channel_member(m.from_user.id):
        bot.reply_to(m, f"⚠️ اشترك في قناة المطور @{CHANNEL_USERNAME} أولاً لتشغيل البوت!", reply_markup=get_subscribe_kb())
        return
    bot.reply_to(m, f"🇱🇾 مرحبتين بيك يا {esc(u['name'])} في إمبراطورية أركان الليبية! اكتب <code>الاوامر</code> للبدء.", reply_markup=get_commands_kb())


# ─────────────── الموجه الرئيسي للأوامر ───────────────

@bot.message_handler(content_types=["text"])
def main_text_router(m: types.Message):
    try:
        _process_text(m)
    except Exception as e:
        logging.error("خطأ: %s", e)

def _process_text(m: types.Message):
    user = m.from_user
    text = m.text.strip()
    chat_id = m.chat.id
    is_group = m.chat.type in ("group", "supergroup")
    b_name = get_bot_name()
    b_name_no_hamza = b_name.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")

    u_data = ensure_user(user)
    grp_data = ensure_group(m.chat) if is_group else {}

    if is_group:
        rank = get_rank(chat_id, user.id)
        locks = get_group_locks(chat_id)

        if rank == 0:
            del_r = None
            if locks.get("الدردشة") or ((m.forward_from or m.forward_from_chat) and locks.get("التوجيه")) or (locks.get("الروابط") and re.search(r"(https?://|t\.me/|telegram\.me/|www\.)", text, re.I)) or (locks.get("اليوزرات") and "@" in text) or (locks.get("الفشار") and any(bw in text.split() for bw in BAD_WORDS)):
                del_r = True
            if del_r:
                try:
                    bot.delete_message(chat_id, m.message_id)
                except Exception:
                    pass
                return

        if chat_id in active_games:
            game = active_games[chat_id]
            if text == game["answer"]:
                reward = game["reward"]
                del active_games[chat_id]
                new_cash = u_data["cash"] + reward
                update_user_field(user.id, cash=new_cash, points=u_data["points"] + 5)
                bot.reply_to(m, f"🎉 صح لسانك يا {esc(u_data['name'])}! ربحت <b>{reward} د.ل</b> كاش + 5 نقاط!")
                return

    # مناداة البوت
    if text in ("بوت", "يا بوت", "يابوت", b_name, f"يا {b_name}", f"يا{b_name}", b_name_no_hamza, f"يا {b_name_no_hamza}"):
        bot.reply_to(m, random.choice(BOT_CALL_REPLIES).format(name=esc(b_name)))
        return

    for prefix in (b_name + " ", b_name_no_hamza + " ", "بوت "):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    COMMAND_TRIGGERS = (
        "الاوامر", "أوامر", "اوامر", "م1", "م2", "م3", "م4", "م5", "م6", "م7", "م8", "م9",
        "الحماية", "الالعاب", "انشاء حساب", "حسابي", "فلوسي", "البنك", "راتب", "خدمة", "بخشيش",
        "ايداع", "سحب", "تحويل", "قرض", "تسديد القرض", "الوظائف", "وظيفة", "علاج", "بيع دواء", "قبض",
        "تصليح", "اختراق صراف", "حماية حساب", "المدن", "سفر", "تهريب بضاعة", "العقارات", "شراء بيت", "بيع بيت",
        "السيارات", "شراء سيارة", "بيع سيارة", "سباق", "المشاريع", "فتح مشروع", "تحصيل ارباح", "البورصة",
        "شراء اسهم", "بيع اسهم", "اسهمي", "السوق الحر", "عرض بيت للبيع", "عرض سيارة للبيع", "شراء معروض",
        "سرقة", "سرقة المصرف", "دفع كفالة", "رشوة العساس", "تهريب",
        "همسة", "رفع", "تنزيل", "قفل", "فتح", "حظر", "الغاء حظر", "طرد", "اطردني", "كتم", "الغاء كتم", "انذار", "حذف الانذارات",
        "مسح", "تثبيت", "الغاء تثبيت", "كشف", "ايدي", "رتبتي", "لقبي", "ضع لقب", "تصفير الرتب",
        "المالكين", "المنشئين", "المدراء", "الادمنية", "المميزين", "الردود", "مسح الردود", "اضف رد", "مسح رد",
        "ضع ترحيب", "تفعيل الترحيب", "تعطيل الترحيب", "ضع قوانين", "القوانين",
        "زواج", "طلاق", "خلع", "زواجي", "غنيلي", "شعر", "نكتة", "نكته", "اذكار", "لو خيروك", "صراحة",
        "حجرة", "ورقة", "مقص", "شنو رايك بهذا", "رزله", "انطي هدية", "نسبة",
        "اسئلة", "لغز", "عواصم", "فكك", "عكس", "معاني", "امثلة", "رياضيات", "حظ", "مضاربة", "استثمار", "اكشط", "قائمة اكشطها",
        "توب", "اضف فلوس", "تصفير فلوسه", "الهمسات", "اذاعة", "نسخة احتياطية", "استعادة", "الاحصائيات", "اطلاق سراح", "تغيير اسم البوت"
    )

    is_cmd = any(text == trig or text.startswith(trig + " ") for trig in COMMAND_TRIGGERS)
    if is_cmd and not is_channel_member(user.id):
        bot.reply_to(m, f"⚠️ اشترك في قناة @{CHANNEL_USERNAME} أولاً لتشغيل الأوامر!", reply_markup=get_subscribe_kb())
        return

    if text in ("الاوامر", "اوامر", "أوامر", "م المطور"):
        bot.reply_to(m, render_menu("main"), reply_markup=get_commands_kb())
        return

    for i in range(1, 10):
        if text == f"م{i}":
            bot.reply_to(m, render_menu(f"menu_{i}"), reply_markup=get_commands_kb())
            return

    if text == "الالعاب":
        bot.reply_to(m, render_menu("menu_games"), reply_markup=get_commands_kb())
        return

    if text == "الحماية" and is_group:
        if get_rank(chat_id, user.id) < 2:
            bot.reply_to(m, "❌ للادمنية فقط!")
            return
        bot.reply_to(m, f"🔒 لوحة أقفال ({esc(b_name)}) :", reply_markup=build_locks_kb(chat_id))
        return

    if is_group:
        user_rank = get_rank(chat_id, user.id)

        if text in ("رفع نفسي مالك", "ترقية نفسي", "تفعيل البوت", "ارفعني مالك", "تفعيل"):
            try:
                member = bot.get_chat_member(chat_id, user.id)
                if member.status == "creator" or user.id == ADMIN_ID:
                    set_rank(chat_id, user.id, 7)
                    bot.reply_to(m, f"💎 تم رفعك إلى رتبة (مالك أساسي) بنجاح!")
                else:
                    bot.reply_to(m, "❌ لمنشئ المجموعة الأصلي فقط!")
            except Exception:
                bot.reply_to(m, "⚠️ ارفع البوت مشرفاً أولاً!")
            return

        if text.startswith("قفل ") or text.startswith("فتح "):
            if user_rank < 2:
                return
            act, t_lock = text.split()[0], text[len(text.split()[0]):].strip()
            if t_lock in LOCK_TYPES:
                set_group_lock(chat_id, t_lock, act == "قفل")
                bot.reply_to(m, f"{'🔒 تم قفل' if act=='قفل' else '🔓 تم فتح'} <b>{t_lock}</b>")
            return

        RANK_CMDS = {
            "رفع مالك": (7, 6, "مالك 👑"), "تنزيل مالك": (7, 0, "عضو"),
            "رفع منشئ": (6, 4, "منشئ 🎖️"), "تنزيل منشئ": (6, 0, "عضو"),
            "رفع مدير": (4, 3, "مدير 💼"), "تنزيل مدير": (4, 0, "عضو"),
            "رفع ادمن": (3, 2, "ادمن 👮‍♂️"), "تنزيل ادمن": (3, 0, "عضو"),
            "رفع مميز": (2, 1, "مميز 🌟"), "تنزيل مميز": (2, 0, "عضو"),
            "تنزيل الكل": (5, 0, "عضو"),
        }
        for r_cmd, (req_r, new_l, r_t) in RANK_CMDS.items():
            if text == r_cmd or text.startswith(r_cmd + " @"):
                if user_rank < req_r:
                    bot.reply_to(m, "❌ رتبتك لا تسمح!")
                    return
                t_u = resolve_target_user(m, text)
                if not t_u:
                    bot.reply_to(m, "💡 رد على رسالة الشخص أو اكتب يوزره!")
                    return
                set_rank(chat_id, t_u["user_id"], new_l)
                bot.reply_to(m, f"✅ تم تحديث رتبة <b>{esc(t_u['name'])}</b> إلى: <b>{r_t}</b>")
                return

        RANK_LIST_CMDS = {
            "المالكين": (6, "👑 قائمة المالكين"), "المنشئين": (4, "🎖️ قائمة المنشئين"),
            "المدراء": (3, "💼 قائمة المدراء"), "الادمنية": (2, "👮‍♂️ قائمة الادمنية"), "المميزين": (1, "🌟 قائمة المميزين"),
        }
        if text in RANK_LIST_CMDS:
            lvl, hdr = RANK_LIST_CMDS[text]
            with db_lock:
                conn = get_db()
                rows = conn.execute("SELECT r.user_id, u.name FROM ranks r LEFT JOIN users u ON r.user_id=u.user_id WHERE r.chat_id=? AND r.rank_level=?", (chat_id, lvl)).fetchall()
                conn.close()
            if not rows:
                bot.reply_to(m, f"📭 لا يوجد أعضاء في {hdr}.")
            else:
                txt = f"<b>{hdr} :</b>\n"
                for idx, r in enumerate(rows, 1):
                    txt += f"{idx}. <b>{esc(r['name'] or 'مستخدم')}</b> (<code>{r['user_id']}</code>)\n"
                bot.reply_to(m, txt)
            return

        if text.startswith("ضع لقب ") and m.reply_to_message and user_rank >= 3:
            set_custom_title(chat_id, m.reply_to_message.from_user.id, text[len("ضع لقب "):].strip())
            bot.reply_to(m, "🏷️ تم تعيين اللقب بنجاح!")
            return

        if text in ("حظر", "طرد", "كتم", "الغاء كتم", "انذار", "حذف الانذارات") and m.reply_to_message and user_rank >= 2:
            target = m.reply_to_message.from_user
            try:
                if text == "حظر": bot.ban_chat_member(chat_id, target.id); bot.reply_to(m, "🚫 تم الحظر!")
                elif text == "طرد": bot.ban_chat_member(chat_id, target.id); bot.unban_chat_member(chat_id, target.id); bot.reply_to(m, "👞 تم الطرد!")
                elif text == "كتم": bot.restrict_chat_member(chat_id, target.id, can_send_messages=False); bot.reply_to(m, "🔇 تم الكتم!")
                elif text == "الغاء كتم": bot.restrict_chat_member(chat_id, target.id, can_send_messages=True, can_send_media_messages=True); bot.reply_to(m, "🔊 تم إلغاء الكتم!")
                elif text == "انذار":
                    with db_lock:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("SELECT count FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, target.id))
                        cnt = (c.fetchone()["count"] if c.fetchone() else 0) + 1
                        conn.execute("INSERT INTO warnings (chat_id, user_id, count) VALUES (?,?,?) ON CONFLICT(chat_id,user_id) DO UPDATE SET count=?", (chat_id, target.id, cnt, cnt))
                        conn.commit()
                        conn.close()
                    bot.reply_to(m, f"⚠️ إنذار ({cnt}/3)")
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
                try: bot.delete_message(chat_id, m.reply_to_message.message_id); bot.delete_message(chat_id, m.message_id)
                except Exception: pass
                return
            parts = text.split()
            if len(parts) == 2 and parts[1].isdigit():
                cnt = min(int(parts[1]), 50)
                for mid in range(m.message_id, m.message_id - cnt - 1, -1):
                    try: bot.delete_message(chat_id, mid)
                    except Exception: pass
                return

    # الهمسة
    if text.startswith("همسة ") and m.reply_to_message:
        s_msg = text[len("همسة "):].strip()
        target = m.reply_to_message.from_user
        try: bot.delete_message(chat_id, m.message_id)
        except Exception: pass
        with db_lock:
            conn = get_db()
            c = conn.cursor()
            c.execute("INSERT INTO whispers (chat_id, sender_id, sender_name, target_id, target_name, text, timestamp) VALUES (?,?,?,?,?,?,?)",
                      (chat_id, user.id, u_data["name"], target.id, target.first_name, s_msg, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            w_id = c.lastrowid
            conn.commit()
            conn.close()
        try:
            bot.send_message(ADMIN_ID, f"🕵️‍♂️ همسة جديدة #{w_id}\nمن: {u_data['name']} ⬅️ {target.first_name}\nالنص: {s_msg}")
        except Exception:
            pass
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔒 عرض الهمسة السرية", callback_data=f"whisper_{w_id}"))
        bot.send_message(chat_id, f"💌 همسة سرية من <b>{esc(u_data['name'])}</b> إلى <b>{esc(target.first_name)}</b>\n🔒 للمستلم فقط!", reply_markup=kb)
        return

    if text in ("ايدي", "معلوماتي", "رتبتي", "لقبي"):
        r_lvl = get_rank(chat_id, user.id) if is_group else 0
        c_title = get_custom_title(chat_id, user.id) if is_group else "بدون لقب"
        bot.reply_to(m, f"🪪 <b>البطاقة الشخصية :</b>\n👤 الاسم: {esc(u_data['name'])}\n🆔 الآيدي: <code>{user.id}</code>\n🎖️ الرتبة: {RANK_NAMES.get(r_lvl, 'عضو')} | 🏷️ اللقب: {esc(c_title)}\n💵 الكاش: {u_data['cash']} د.ل | 🏦 المصرف: {u_data['bank_balance']} د.ل\n⭐ المستوى: {u_data['level']} (نقاط: {u_data['points']})")
        return

    if text == "كشف" or text.startswith("كشف @"):
        t_u = resolve_target_user(m, text) or u_data
        bot.reply_to(m, f"🔍 <b>كشف السجل :</b>\n👤 المواطن: {esc(t_u['name'])}\n📍 المدينة: {t_u['city']} | 💼 المهنة: {t_u['job']}\n❤️ الصحة: {t_u['hp']}% | 💵 الكاش: {t_u['cash']} د.ل\n🏦 المصرف: {t_u['bank_balance']} د.ل\n🏠 البيت: {t_u['house']} | 🚗 السيارة: {t_u['car']}")
        return

    # الحبس
    now = int(time.time())
    if u_data["jail_until"] > now:
        rem = max(1, (u_data["jail_until"] - now) // 60)
        if text == "دفع كفالة":
            if u_data["cash"] >= 1500:
                update_user_field(user.id, cash=u_data["cash"]-1500, jail_until=0, wanted=0)
                bot.reply_to(m, "⚖️ دفعت 1500 كفالة وطلعت براءة!")
            elif u_data["bank_balance"] >= 1500:
                update_user_field(user.id, bank_balance=u_data["bank_balance"]-1500, jail_until=0, wanted=0)
                bot.reply_to(m, "⚖️ خصموا الكفالة من مصرفك وطلعت!")
            else:
                bot.reply_to(m, "❌ ما عندكش 1500 كفالة!")
            return
        if is_cmd and text not in ("حسابي", "فلوسي"):
            bot.reply_to(m, f"⛓️ أنت محبوس! باقي {rem} دقيقة. اكتب <code>دفع كفالة</code> للخروج.")
            return

    # المصارف والأموال
    if text in ("انشاء حساب", "فتح حساب"):
        if u_data["bank_name"] != "بدون مصرف":
            bot.reply_to(m, f"🏦 عندك حساب في {u_data['bank_name']} مسبقاً!")
            return
        kb = types.InlineKeyboardMarkup(row_width=1)
        for b_t in BANKS: kb.add(types.InlineKeyboardButton(f"🏦 {b_t}", callback_data=f"openbank_{b_t}"))
        bot.reply_to(m, "🇱🇾 اختر المصرف الليبي لفتح حسابك:", reply_markup=kb)
        return

    if text in ("حسابي", "فلوسي", "البنك"):
        bot.reply_to(m, f"🏦 <b>حسابك المصرفي :</b>\n🏛️ المصرف: {u_data['bank_name']}\n💵 كاش في الجيب: {u_data['cash']} د.ل\n💳 رصيد المصرف الآمن: {u_data['bank_balance']} د.ل\n📉 القروض: {u_data['loan']} د.ل")
        return

    if text.startswith("ايداع "):
        arg = text.split()[1]
        amt = u_data["cash"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt > 0 and amt <= u_data["cash"]:
            update_user_field(user.id, cash=u_data["cash"]-amt, bank_balance=u_data["bank_balance"]+amt)
            bot.reply_to(m, f"✅ تم إيداع {amt} د.ل في المصرف بنجاح!")
        return

    if text.startswith("سحب "):
        arg = text.split()[1]
        amt = u_data["bank_balance"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt > 0 and amt <= u_data["bank_balance"]:
            update_user_field(user.id, cash=u_data["cash"]+amt, bank_balance=u_data["bank_balance"]-amt)
            bot.reply_to(m, f"💵 سحبت {amt} د.ل كاش!")
        return

    # الوظائف
    if text == "الوظائف":
        txt = "💼 <b>المهن المتاحة :</b>\n"
        for j, inf in JOBS.items(): txt += f"• <b>{j}</b> — راتب: {inf['salary']} د.ل\n"
        bot.reply_to(m, txt + "\nللتسجيل: <code>وظيفة دكتور</code> أو <code>وظيفة مبرمج</code>...")
        return

    if text.startswith("وظيفة "):
        j_c = text[len("وظيفة "):].strip()
        if j_c in JOBS:
            update_user_field(user.id, job=j_c)
            bot.reply_to(m, f"🎉 مبروك تعيينك في وظيفة <b>{j_c}</b>! اكتب <code>راتب</code> لاستلام يوميتك.")
        return

    if text in ("راتب", "خدمة", "بخشيش"):
        if now - u_data["last_salary"] < 600:
            bot.reply_to(m, "⏳ ارجع بعد قليل لاستلام راتبك القادم.")
            return
        sal = JOBS.get(u_data["job"], {"salary": 700})["salary"]
        update_user_field(user.id, cash=u_data["cash"]+sal, last_salary=now)
        bot.reply_to(m, f"💵 استلمت راتب مهنتك ({u_data['job']}) وقدره <b>{sal} د.ل</b> كاش!")
        return

    if text == "تصليح" and m.reply_to_message:
        if u_data["job"] != "ميكانيكي": bot.reply_to(m, "❌ للميكانيكي فقط!"); return
        cli = ensure_user(m.reply_to_message.from_user)
        if cli["car"] == "بدون سيارة": bot.reply_to(m, "😂 ما عنده سيارة!"); return
        update_user_field(user.id, cash=u_data["cash"]+800)
        bot.reply_to(m, f"🔧 صلحت سيارة {cli['name']} وكسبت 800 د.ل!")
        return

    # السفر والتهريب
    if text == "المدن":
        txt = "🗺️ <b>المدن الليبية :</b>\n"
        for cn, ci in CITIES.items(): txt += f"📍 {cn} — التذكرة: {ci['ticket']} د.ل\n"
        bot.reply_to(m, txt + "\nللسفر: <code>سفر بنغازي</code>")
        return

    if text.startswith("سفر "):
        dest = text[len("سفر "):].strip()
        if dest in CITIES and u_data["cash"] >= CITIES[dest]["ticket"]:
            update_user_field(user.id, city=dest, cash=u_data["cash"]-CITIES[dest]["ticket"])
            bot.reply_to(m, f"✈️ وصلت بسلام إلى مدينة <b>{dest}</b>!")
        return

    if text == "تهريب بضاعة":
        if u_data["cash"] < 1500: bot.reply_to(m, "❌ تحتاج 1500 د.ل رأس مال!"); return
        if random.randint(1, 100) > 30:
            prof = random.randint(3000, 6000)
            update_user_field(user.id, cash=u_data["cash"]-1500+prof)
            bot.reply_to(m, f"🚚💨 نجحت صفقة التهريب وكسبت مكسب {prof} د.ل!")
        else:
            update_user_field(user.id, cash=u_data["cash"]-1500, jail_until=now+1200)
            bot.reply_to(m, "🚨 طاحوا بيك الجمارك وحطوك في الحبس 20 دقيقة!")
        return

    # العقارات والسيارات والسوق الحر
    if text == "العقارات":
        txt = "🏡 <b>العقارات :</b>\n"
        for hn, hi in HOUSES.items(): txt += f"• {hn} — {hi['price']} د.ل\n"
        bot.reply_to(m, txt + "\nللشراء: <code>شراء بيت شقة في الفلاح</code>\nللبيع: <code>بيع بيت</code>")
        return

    if text.startswith("شراء بيت "):
        hn = text[len("شراء بيت "):].strip()
        if hn in HOUSES and u_data["bank_balance"] >= HOUSES[hn]["price"]:
            update_user_field(user.id, bank_balance=u_data["bank_balance"]-HOUSES[hn]["price"], house=hn)
            bot.reply_to(m, f"🔑 مبروك اشتريت <b>{hn}</b>!")
        return

    if text == "بيع بيت":
        if u_data["house"] != "بدون سكن":
            p = int(HOUSES[u_data["house"]]["price"] * 0.8)
            update_user_field(user.id, bank_balance=u_data["bank_balance"]+p, house="بدون سكن")
            bot.reply_to(m, f"🏠 بعت بيتك واسترديت {p} د.ل في المصرف!")
        return

    if text == "السيارات":
        txt = "🚗 <b>السيارات :</b>\n"
        for cn, ci in CARS.items(): txt += f"• {cn} — {ci['price']} د.ل\n"
        bot.reply_to(m, txt + "\nللشراء: <code>شراء سيارة تويتا دبدوبة</code>\nللبيع: <code>بيع سيارة</code>")
        return

    if text.startswith("شراء سيارة "):
        cn = text[len("شراء سيارة "):].strip()
        if cn in CARS and u_data["bank_balance"] >= CARS[cn]["price"]:
            update_user_field(user.id, bank_balance=u_data["bank_balance"]-CARS[cn]["price"], car=cn)
            bot.reply_to(m, f"🏎️ مبروك سيارتك الجديدة ({cn})!")
        return

    if text == "بيع سيارة":
        if u_data["car"] != "بدون سيارة":
            p = int(CARS[u_data["car"]]["price"] * 0.8)
            update_user_field(user.id, bank_balance=u_data["bank_balance"]+p, car="بدون سيارة")
            bot.reply_to(m, f"🚗 بعت سيارتك واسترديت {p} د.ل!")
        return

    # ⚡ نظام السوق الحر (بيع وشراء بين اللاعبين)
    if text == "السوق الحر":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM marketplace").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "🏪 السوق الحر فارغ حالياً! لا توجد عروض بيع.")
        else:
            txt = "🏪 <b>عروض السوق الحر بين اللاعبين :</b>\n"
            for r in rows:
                txt += f"🆔 #{r['id']} | البائع: {esc(r['seller_name'])} | المعروض: <b>{r['item_name']}</b> | السعر: <b>{r['price']} د.ل</b>\n"
            bot.reply_to(m, txt + "\nلشراء أي سلعة اكتب: <code>شراء معروض رقم_السلعة</code>")
        return

    if text.startswith("عرض بيت للبيع "):
        pr = text[len("عرض بيت للبيع "):].strip()
        if u_data["house"] == "بدون سكن": bot.reply_to(m, "❌ ما عندكش بيت تعرضه للبيع!"); return
        if pr.isdigit():
            with db_lock:
                conn = get_db()
                conn.execute("INSERT INTO marketplace (seller_id, seller_name, item_type, item_name, price) VALUES (?,?,?,?,?)",
                             (user.id, u_data["name"], "house", u_data["house"], int(pr)))
                conn.commit()
                conn.close()
            update_user_field(user.id, house="بدون سكن")
            bot.reply_to(m, f"🏪 تم عرض بيتك ({u_data['house']}) للبيع في السوق الحر بسعر {pr} د.ل!")
        return

    if text.startswith("عرض سيارة للبيع "):
        pr = text[len("عرض سيارة للبيع "):].strip()
        if u_data["car"] == "بدون سيارة": bot.reply_to(m, "❌ ما عندكش سيارة تعرضها!"); return
        if pr.isdigit():
            with db_lock:
                conn = get_db()
                conn.execute("INSERT INTO marketplace (seller_id, seller_name, item_type, item_name, price) VALUES (?,?,?,?,?)",
                             (user.id, u_data["name"], "car", u_data["car"], int(pr)))
                conn.commit()
                conn.close()
            update_user_field(user.id, car="بدون سيارة")
            bot.reply_to(m, f"🏪 تم عرض سيارتك ({u_data['car']}) للبيع في السوق الحر بسعر {pr} د.ل!")
        return

    if text.startswith("شراء معروض "):
        parts = text.split()
        if len(parts) == 3 and parts[2].isdigit():
            m_id = int(parts[2])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM marketplace WHERE id = ?", (m_id,)).fetchone()
                conn.close()
            if not row: bot.reply_to(m, "❌ المعروض غير موجود أو تم بيعه!"); return
            if row["seller_id"] == user.id: bot.reply_to(m, "😂 تبي تشترى سلعتاك روحك؟"); return
            if u_data["bank_balance"] < row["price"]: bot.reply_to(m, "❌ رصيدك في المصرف لا يكفي!"); return

            with db_lock:
                conn = get_db()
                conn.execute("DELETE FROM marketplace WHERE id = ?", (m_id,))
                conn.commit()
                conn.close()

            update_user_field(user.id, bank_balance=u_data["bank_balance"]-row["price"],
                              house=(row["item_name"] if row["item_type"]=="house" else u_data["house"]),
                              car=(row["item_name"] if row["item_type"]=="car" else u_data["car"]))
            
            # تحويل الثمن للبائع
            seller = get_user_by_id(row["seller_id"])
            if seller:
                update_user_field(seller["user_id"], bank_balance=seller["bank_balance"]+row["price"])

            bot.reply_to(m, f"🎉 مبروك! اشتريت <b>{row['item_name']}</b> من السوق الحر بسعر {row['price']} د.ل!")
        return

    # البورصة والأسهم
    if text in ("البورصة", "اسهمي"):
        u_stk = json.loads(u_data.get("stocks") or "{}")
        txt = "📈 <b>البورصة الليبية :</b>\n"
        for sn in STOCKS.keys():
            txt += f"• {sn} — السعر: {get_current_stock_price(sn)} د.ل (تمتلك: {u_stk.get(sn, 0)})\n"
        bot.reply_to(m, txt + "\nللشراء: <code>شراء اسهم المدار 10</code>\nللبيع: <code>بيع اسهم المدار</code>")
        return

    if text.startswith("شراء اسهم "):
        parts = text.split()
        if len(parts) == 4 and parts[3].isdigit():
            sn, qty = parts[2], int(parts[3])
            cost = get_current_stock_price(sn) * qty
            if u_data["bank_balance"] >= cost:
                u_stk = json.loads(u_data.get("stocks") or "{}")
                u_stk[sn] = u_stk.get(sn, 0) + qty
                update_user_field(user.id, bank_balance=u_data["bank_balance"]-cost, stocks=json.dumps(u_stk))
                bot.reply_to(m, f"📈 اشتريت {qty} سهم في {sn} بمبلغ {cost} د.ل!")
        return

    if text.startswith("بيع اسهم "):
        sn = text[len("بيع اسهم "):].strip()
        u_stk = json.loads(u_data.get("stocks") or "{}")
        qty = u_stk.get(sn, 0)
        if qty > 0:
            val = get_current_stock_price(sn) * qty
            u_stk[sn] = 0
            update_user_field(user.id, bank_balance=u_data["bank_balance"]+val, stocks=json.dumps(u_stk))
            bot.reply_to(m, f"💰 بعت أسهم {sn} واسترديت {val} د.ل في المصرف!")
        return

    # السرقة
    if text == "سرقة" and m.reply_to_message:
        vic = ensure_user(m.reply_to_message.from_user)
        if vic["user_id"] == user.id or vic["cash"] < 200: bot.reply_to(m, "❌ لا يمكن سرقته!"); return
        if random.randint(1, 100) <= 50:
            stn = int(vic["cash"] * 0.4)
            update_user_field(vic["user_id"], cash=vic["cash"]-stn)
            update_user_field(user.id, cash=u_data["cash"]+stn, steal_success=u_data["steal_success"]+1, wanted=1)
            bot.reply_to(m, f"🦹‍♂️ سرقت من جيب {vic['name']} مبلغ {stn} د.ل وهربت!")
        else:
            update_user_field(user.id, hp=max(10, u_data["hp"]-30), jail_until=now+900)
            bot.reply_to(m, "🚨 مسكك صاحب الجيب وعطاكا طريحة وحطوك في الحبس 15 دقيقة!")
        return

    if text == "سرقة المصرف":
        if now - u_data["last_rob"] < 1200: bot.reply_to(m, "⏳ المصرف مشدد الحراسة حالياً!"); return
        if random.randint(1, 100) <= 25:
            loot = random.randint(10000, 20000)
            update_user_field(user.id, cash=u_data["cash"]+loot, last_rob=now, wanted=1)
            bot.reply_to(m, f"💣🏦 عملية سطو ناجحة! سرقت {loot} د.ل كاش من الخزنة!")
        else:
            update_user_field(user.id, jail_until=now+2400, last_rob=now)
            bot.reply_to(m, "🚓 كبّست عليك قوة الردع وحطوك في الحبس 40 دقيقة!")
        return

    # الألعاب والترفيه
    if text in QUESTIONS_BANK:
        q, ans = random.choice(QUESTIONS_BANK[text])
        reward = 500
        active_games[chat_id] = {"answer": ans, "reward": reward}
        bot.reply_to(m, f"🎲 <b>مسابقة ({text}) :</b>\n❓ {q}\n💰 الجائزة: {reward} د.ل لأول إجابة صحيحة!")
        return

    if text == "رياضيات":
        a, b = random.randint(10, 50), random.randint(10, 50)
        active_games[chat_id] = {"answer": str(a+b), "reward": 400}
        bot.reply_to(m, f"🧮 كم ناتج: {a} + {b} ؟")
        return

    if text == "غنيلي": bot.reply_to(m, random.choice(SONGS_LIST)); return
    if text in ("شعر", "قصيدة"): bot.reply_to(m, random.choice(POEMS_LIST)); return
    if text in ("نكتة", "نكته"): bot.reply_to(m, random.choice(JOKES_LIST)); return
    if text == "اذكار": bot.reply_to(m, random.choice(ADHKAR_LIST)); return
    if text == "لو خيروك": bot.reply_to(m, random.choice(LAW_KHAYAROUK_LIST)); return
    if text == "صراحة": bot.reply_to(m, random.choice(SARAHA_QUESTIONS)); return

    if text.startswith(("حظ ", "مضاربة ", "استثمار ")):
        parts = text.split()
        if len(parts) == 2 and parts[1].isdigit():
            amt = int(parts[1])
            if amt > 0 and amt <= u_data["cash"]:
                if random.choice([True, False]):
                    prof = int(amt * 0.8)
                    update_user_field(user.id, cash=u_data["cash"]+prof)
                    bot.reply_to(m, f"📈 ربحت في السوق {prof} د.ل 🎉")
                else:
                    update_user_field(user.id, cash=u_data["cash"]-amt)
                    bot.reply_to(m, f"📉 خسرت {amt} د.ل 😢")
        return

    # أوامر المطور MG
    if user.id == ADMIN_ID:
        if text == "استعادة" and m.reply_to_message and m.reply_to_message.document:
            try:
                fi = bot.get_file(m.reply_to_message.document.file_id)
                dw = bot.download_file(fi.file_path)
                with db_lock:
                    with open(DB_FILE, "wb") as f: f.write(dw)
                init_db()
                bot.reply_to(m, "✅ تمت استعادة قاعدة البيانات بنجاح!")
            except Exception as e:
                bot.reply_to(m, f"❌ خطأ: {e}")
            return

        if text.startswith("تغيير اسم البوت "):
            set_bot_name(text[len("تغيير اسم البوت "):].strip())
            bot.reply_to(m, "⚡ تم تغيير اسم البوت بنجاح!")
            return

        if text.startswith("اضف فلوس ") and m.reply_to_message:
            amt = int(text.split()[-1])
            t_u = ensure_user(m.reply_to_message.from_user)
            update_user_field(t_u["user_id"], bank_balance=t_u["bank_balance"]+amt)
            bot.reply_to(m, f"⚡ تمت إضافة {amt} د.ل لحساب العضو!")
            return

        if text == "نسخة احتياطية" and DB_FILE.exists():
            with open(DB_FILE, "rb") as f:
                bot.send_document(ADMIN_ID, f, caption="📦 نسخة احتياطية لقاعدة البيانات\nرد عليها بـ `استعادة` للرجوع إليها في أي وقت.")
            return

        if text.startswith("اذاعة "):
            b_msg = text[len("اذاعة "):].strip()
            with db_lock:
                conn = get_db()
                g_rows = conn.execute("SELECT chat_id FROM groups").fetchall()
                conn.close()
            for r in g_rows:
                try: bot.send_message(r["chat_id"], f"📢 <b>إذاعة من المطور :</b>\n\n{esc(b_msg)}")
                except Exception: pass
            bot.reply_to(m, "✅ تمت الإذاعة في المجموعات!")
            return


# ─────────────── معالجة الأزرار ───────────────

@bot.callback_query_handler(func=lambda c: True)
def on_callback(call: types.CallbackQuery):
    try:
        data, user, chat_id = call.data, call.from_user, call.message.chat.id
        b_name = get_bot_name()

        if data == "check_sub":
            if is_channel_member(user.id):
                bot.answer_callback_query(call.id, "✅ تم التحقق!", show_alert=True)
                bot.edit_message_text(render_menu("main"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_commands_kb())
            else:
                bot.answer_callback_query(call.id, f"❌ لم تشترك في @{CHANNEL_USERNAME}!", show_alert=True)
            return

        if data == "menu_main":
            bot.edit_message_text(render_menu("main"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_commands_kb())
            return

        if data in MENU_TEXTS:
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="menu_main"))
            bot.edit_message_text(render_menu(data), chat_id=chat_id, message_id=call.message.message_id, reply_markup=kb)
            return

        if data == "locks_panel":
            if get_rank(chat_id, user.id) < 2: return
            bot.edit_message_text(f"🔒 لوحة أقفال ({esc(b_name)}) :", chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_locks_kb(chat_id))
            return

        if data.startswith("togglelock_"):
            if get_rank(chat_id, user.id) < 2: return
            lk = data.split("_", 1)[1]
            st = not get_group_locks(chat_id).get(lk, False)
            set_group_lock(chat_id, lk, st)
            bot.answer_callback_query(call.id, f"تم {'قفل' if st else 'فتح'} {lk}")
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_locks_kb(chat_id))
            return

        if data.startswith("openbank_"):
            b_t = data.split("_", 1)[1]
            u = ensure_user(user)
            if u["bank_name"] == "بدون مصرف":
                update_user_field(user.id, bank_name=b_t, bank_balance=u["bank_balance"]+1000)
                bot.answer_callback_query(call.id, "🎉 مبروك فتح الحساب و1000 د.ل هدية!", show_alert=True)
                bot.edit_message_text(f"🏦 تم فتح حسابك في ({b_t}) وإضافة 1000 د.ل هدية لرصيدك!", chat_id=chat_id, message_id=call.message.message_id)
            return

        if data.startswith("whisper_"):
            w_id = int(data.split("_")[1])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM whispers WHERE id = ?", (w_id,)).fetchone()
                conn.close()
            if row and user.id in (row["sender_id"], row["target_id"], ADMIN_ID):
                bot.answer_callback_query(call.id, f"💬 الهمسة:\n{row['text']}", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "🚫 الهمسة ليس لك!", show_alert=True)
            return
    except Exception as e:
        logging.error("CB error: %s", e)


# ─────────────── التشغيل ───────────────

if __name__ == "__main__":
    try:
        me = bot.get_me()
        if me.username: BOT_USERNAME = me.username
    except Exception:
        pass

    try:
        bot.delete_webhook(drop_pending_updates=True)
        time.sleep(1)
    except Exception:
        pass

    threading.Thread(target=run_web, daemon=True).start()

    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=20, skip_pending=True, allowed_updates=["message", "edited_message", "callback_query", "chat_member"])
        except Exception as err:
            logging.error("Polling error: %s", err)
            time.sleep(3)
