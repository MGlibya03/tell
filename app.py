#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
══════════════════════════════════════════════════════════════════
🇱🇾 إمبراطورية أركان الليبية (ARKAN LIBYA EMPIRE RPG) - النسخة الشاملة الذكية
برمجة خاصة ومتكاملة للمطور الأساسي: MG (1053838533)
تدعم الكتابة السريعة بدون همزات وبدون تاء مربوطة (ه = ة) لجميع الأعضاء 100%
══════════════════════════════════════════════════════════════════
طريقة التركيب في GitHub:
1. الصق (القسم الأول) في بداية الملف.
2. الصق (القسم الثاني) تحته مباشرة.
3. الصق (القسم الثالث) في النهاية.
══════════════════════════════════════════════════════════════════
"""

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
DB_FILE: Path = Path("arkan_libya_v3.db")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

if not BOT_TOKEN:
    raise ValueError("❌ خطأ: BOT_TOKEN غير موجود في Environment Variables!")

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ══════════════════════════════════════════════════════════════════
# 🔤 محرك توحيد الحروف العربية للكتابة السريعة (ه = ة ، ا = أ/إ/آ ، ي = ى)
# ══════════════════════════════════════════════════════════════════
def norm_ar(text: str) -> str:
    """توحيد الحروف العربية لكي تعمل الأوامر حتى لو كُتبت بسرعة بدون تاء مربوطة أو همزات"""
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"[أإآ]", "ا", t)
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")
    t = re.sub(r"\s+", " ", t)
    return t

def match_dict_key(mapping: dict, query: str) -> str | None:
    """البحث الذكي في القواميس بدون حساسية للتاء المربوطة أو الهمزات أو حالة الأحرف"""
    q_norm = norm_ar(query).lower()
    if not q_norm:
        return None
    for k in mapping.keys():
        if norm_ar(k).lower() == q_norm:
            return k
    for k in mapping.keys():
        if q_norm in norm_ar(k).lower() or norm_ar(k).lower() in q_norm:
            return k
    return None

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
                bank_name TEXT DEFAULT 'بدون مصرف',
                bank_branch TEXT DEFAULT 'الفرع الرئيسي - طرابلس',
                cash INTEGER DEFAULT 0,
                home_cash INTEGER DEFAULT 0,
                bank_balance INTEGER DEFAULT 0,
                loan INTEGER DEFAULT 0,
                job TEXT DEFAULT 'عاطل',
                job_level INTEGER DEFAULT 1,
                job_xp INTEGER DEFAULT 0,
                hp INTEGER DEFAULT 100,
                xp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                jail_until INTEGER DEFAULT 0,
                wanted INTEGER DEFAULT 0,
                house TEXT DEFAULT 'بدون سكن',
                house_sec_level INTEGER DEFAULT 0,
                car TEXT DEFAULT 'بدون سيارة',
                car_cond INTEGER DEFAULT 100,
                stocks TEXT DEFAULT '{}',
                tools TEXT DEFAULT '{}',
                married_to INTEGER DEFAULT 0,
                dowry INTEGER DEFAULT 0,
                steal_success INTEGER DEFAULT 0,
                msg_count INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                last_salary INTEGER DEFAULT 0,
                last_rob INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0,
                firewall_until INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS businesses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                owner_name TEXT,
                biz_type TEXT,
                custom_name TEXT,
                city TEXT DEFAULT 'طرابلس',
                stock INTEGER DEFAULT 0,
                vault INTEGER DEFAULT 0,
                security INTEGER DEFAULT 15,
                marketing INTEGER DEFAULT 1,
                ecommerce INTEGER DEFAULT 0,
                is_open INTEGER DEFAULT 1,
                total_sales INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS business_partners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                biz_id INTEGER,
                user_id INTEGER,
                user_name TEXT,
                share_pct INTEGER DEFAULT 10,
                UNIQUE(biz_id, user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS business_staff (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                biz_id INTEGER,
                user_id INTEGER,
                user_name TEXT,
                pay_mode TEXT DEFAULT 'نسبة',
                pay_val INTEGER DEFAULT 10,
                UNIQUE(biz_id, user_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS custom_banks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER,
                owner_name TEXT,
                bank_name TEXT UNIQUE,
                fee_pct REAL DEFAULT 1.5,
                security INTEGER DEFAULT 60,
                vault INTEGER DEFAULT 100000
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
                punishment TEXT DEFAULT 'بالتقييد',
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
# 🇱🇾 القوائم والبيانات الواقعية (مدن، مصارف، سيارات حقيقية، عقارات، متاجر)
# ══════════════════════════════════════════════════════════════════

CITY_LIST = [
    ("طرابلس", 120, "العاصمة والمركز المالي والتجاري"),
    ("بنغازي", 200, "عاصمة الشرق والأسواق الكبرى"),
    ("مصراتة", 150, "مدينة التجارة الحرة والشركات"),
    ("سبها", 250, "عاصمة الجنوب وتجارة الصحراء"),
    ("الزاوية", 90, "مدينة المصافي والساحل الغربي"),
    ("زليتن", 110, "مدينة الأسواق النشطة والعقارات"),
    ("البيضاء", 220, "عروس الجبل الأخضر والسياحة"),
    ("غريان", 100, "بوابة الجبل الغربي"),
    ("طبرق", 300, "أقصى الشرق والتجارة الحدودية"),
    ("زوارة", 110, "مدينة البحر والتجارة الساحلية"),
]
CITIES = {name: {"ticket": t, "desc": d, "idx": i} for i, (name, t, d) in enumerate(CITY_LIST)}

BANK_LIST = [
    ("مصرف الجمهورية", 1.5, 75, ["فرع ميدان الشهداء طرابلس", "فرع بنغازي المركز", "فرع مصراتة المركزي", "فرع سبها"]),
    ("المصرف التجاري الوطني", 1.5, 80, ["فرع ذات العماد طرابلس", "فرع بنغازي الرئيسي", "فرع البيضاء", "فرع الزاوية"]),
    ("مصرف الصحارى", 1.0, 70, ["فرع اول سبتمبر طرابلس", "فرع فينيسيا بنغازي", "فرع مصراتة"]),
    ("مصرف الوحدة", 1.2, 72, ["فرع بنغازي الرئيسي", "فرع طرابلس المركز", "فرع طبرق"]),
    ("مصرف التجارة والتنمية", 2.0, 88, ["فرع البرج طرابلس", "فرع بنغازي النموذجي", "فرع مصراتة"]),
    ("مصرف الأمان", 2.0, 90, ["فرع قرقارش طرابلس", "فرع بنغازي", "فرع زليتن"]),
    ("مصرف شمال أفريقيا", 1.5, 82, ["فرع طرابلس الرئيسي", "فرع غريان", "فرع مصراتة"]),
]
OFFICIAL_BANKS = {name: {"fee": f, "security": s, "branches": br, "idx": i} for i, (name, f, s, br) in enumerate(BANK_LIST)}

JOB_LIST = ["مبرمج", "دكتور", "شرطي", "مهندس", "صيدلي", "ميكانيكي", "قاضي", "تاجر"]
JOBS = {
    "مبرمج": {
        "desc": "تطوير الأنظمة، اختراق الصرافات، وحماية الحسابات بجدار ناري",
        "levels": {
            1: {"title": "مبرمج مبتدئ", "salary": 1200, "req_xp": 0},
            2: {"title": "مطور مواقع وتطبيقات", "salary": 2400, "req_xp": 10},
            3: {"title": "مهندس أمن سيبراني", "salary": 4500, "req_xp": 25},
            4: {"title": "كبير مهندسي البرمجيات CTO", "salary": 8500, "req_xp": 50},
        }
    },
    "دكتور": {
        "desc": "علاج المرضى والمصابين في المجموعة (أمر: علاج بالرد)",
        "levels": {
            1: {"title": "طبيب امتياز", "salary": 1300, "req_xp": 0},
            2: {"title": "طبيب أخصائي", "salary": 2600, "req_xp": 10},
            3: {"title": "جراح استشاري", "salary": 5000, "req_xp": 25},
            4: {"title": "بروفيسور ومدير طبي", "salary": 9000, "req_xp": 50},
        }
    },
    "شرطي": {
        "desc": "مطاردة الحرامية والقبض على المطلوبين بمكافأة (أمر: قبض بالرد)",
        "levels": {
            1: {"title": "شرطي دورية", "salary": 1100, "req_xp": 0},
            2: {"title": "ملازم مباحث", "salary": 2200, "req_xp": 10},
            3: {"title": "رائد قوة خاصة", "salary": 4200, "req_xp": 25},
            4: {"title": "عميد مدير أمن", "salary": 8000, "req_xp": 50},
        }
    },
    "مهندس": {
        "desc": "الإشراف الهندسي وتطوير العقارات والمشاريع الكبرى",
        "levels": {
            1: {"title": "مهندس موقع", "salary": 1250, "req_xp": 0},
            2: {"title": "مهندس مشاريع", "salary": 2500, "req_xp": 10},
            3: {"title": "مهندس استشاري", "salary": 4800, "req_xp": 25},
            4: {"title": "مدير عام إعمار", "salary": 8800, "req_xp": 50},
        }
    },
    "صيدلي": {
        "desc": "تركيب وصرف الأدوية للمواطنين (أمر: بيع دواء بالرد)",
        "levels": {
            1: {"title": "مساعد صيدلي", "salary": 1000, "req_xp": 0},
            2: {"title": "صيدلي قانوني", "salary": 2100, "req_xp": 10},
            3: {"title": "خبير دوائي", "salary": 4000, "req_xp": 25},
            4: {"title": "نقيب صيادلة", "salary": 7500, "req_xp": 50},
        }
    },
    "ميكانيكي": {
        "desc": "صيانة وتعديل السيارات الرياضية والعادية (أمر: تصليح بالرد)",
        "levels": {
            1: {"title": "فني ورشة", "salary": 950, "req_xp": 0},
            2: {"title": "أسطى ميكانيكي", "salary": 1900, "req_xp": 10},
            3: {"title": "خبير محركات تيربو", "salary": 3800, "req_xp": 25},
            4: {"title": "مدير مركز صيانة عالمي", "salary": 7200, "req_xp": 50},
        }
    },
    "قاضي": {
        "desc": "الفصل في القضايا وإصدار أحكام المحكمة العليا",
        "levels": {
            1: {"title": "وكيل نيابة", "salary": 1500, "req_xp": 0},
            2: {"title": "قاضي محكمة", "salary": 3000, "req_xp": 10},
            3: {"title": "مستشار استئناف", "salary": 5800, "req_xp": 25},
            4: {"title": "رئيس المحكمة العليا", "salary": 10500, "req_xp": 50},
        }
    },
    "تاجر": {
        "desc": "احتراف الاستيراد والتصدير وإدارة الأسهم والمولات",
        "levels": {
            1: {"title": "تاجر تجزئة", "salary": 1100, "req_xp": 0},
            2: {"title": "تاجر جملة", "salary": 2300, "req_xp": 10},
            3: {"title": "مستورد دولي", "salary": 4600, "req_xp": 25},
            4: {"title": "رجل أعمال ملياردير", "salary": 9200, "req_xp": 50},
        }
    }
}

CARS = {
    "Hyundai Grand i10 2023": {"price": 18000, "speed": 165, "maint": 150, "ar": "هيونداي اي 10"},
    "Kia Pegas 2024": {"price": 24000, "speed": 175, "maint": 180, "ar": "كيا بيجاس"},
    "Toyota Corolla 1.8 2024": {"price": 38000, "speed": 195, "maint": 250, "ar": "تويوتا كورولا"},
    "Hyundai Elantra N-Line 2024": {"price": 46000, "speed": 215, "maint": 300, "ar": "هيونداي النترا"},
    "Kia K5 GT-Line 2025": {"price": 58000, "speed": 230, "maint": 380, "ar": "كيا اوبتيما k5"},
    "Toyota Camry Grande V6 2025": {"price": 75000, "speed": 240, "maint": 450, "ar": "تويوتا كامري"},
    "Hyundai Sonata Turbo 2025": {"price": 72000, "speed": 245, "maint": 450, "ar": "هيونداي سوناتا"},
    "Toyota Hilux Adventure 2024": {"price": 88000, "speed": 190, "maint": 500, "ar": "تويوتا هايلوكس"},
    "Chevrolet Tahoe Z71 2025": {"price": 135000, "speed": 210, "maint": 750, "ar": "شيفروليه تاهو"},
    "Ford Mustang Dark Horse 5.0 2025": {"price": 165000, "speed": 275, "maint": 950, "ar": "فورد موستنج"},
    "Dodge Charger SRT Hellcat Redeye 2024": {"price": 220000, "speed": 326, "maint": 1300, "ar": "دودج تشارجر هيلكات"},
    "Toyota Land Cruiser 300 Twin-Turbo 2025": {"price": 260000, "speed": 230, "maint": 1200, "ar": "تويوتا لاندكروزر"},
    "BMW M5 CS 2025": {"price": 310000, "speed": 305, "maint": 1600, "ar": "بي ام دبليو ام 5"},
    "Mercedes-Benz S580 Maybach 2025": {"price": 390000, "speed": 260, "maint": 2000, "ar": "مرسيدس مايباخ"},
    "Mercedes-AMG G63 V8 Biturbo 2025": {"price": 480000, "speed": 250, "maint": 2400, "ar": "مرسيدس جي كلاس"},
    "Porsche 911 Turbo S 2025": {"price": 560000, "speed": 330, "maint": 2800, "ar": "بورش 911"},
    "Lamborghini Revuelto V12 2025": {"price": 950000, "speed": 350, "maint": 4500, "ar": "لامبورغيني"},
    "Bugatti Chiron Super Sport 300+": {"price": 2200000, "speed": 440, "maint": 9000, "ar": "بوغاتي شيرون"},
}

def find_car_name(query: str) -> str | None:
    q = norm_ar(query).lower()
    if not q:
        return None
    for ck, ci in CARS.items():
        if q == ck.lower() or q == norm_ar(ci["ar"]).lower():
            return ck
    for ck, ci in CARS.items():
        if q in ck.lower() or q in norm_ar(ci["ar"]).lower():
            return ck
    return None

HOUSES = {
    "شقة عزابية صغيرة": {"price": 20000, "defense": 15, "safe_cap": 30000},
    "شقة سكنية في السراج": {"price": 45000, "defense": 25, "safe_cap": 80000},
    "حوش عائلي في سوق الجمعة": {"price": 75000, "defense": 35, "safe_cap": 150000},
    "دوبلكس راقي في حي الأندلس": {"price": 140000, "defense": 48, "safe_cap": 350000},
    "فيلا حديثة في الهواري": {"price": 240000, "defense": 60, "safe_cap": 700000},
    "فيلا ملكية مع مسبح في جنزور": {"price": 380000, "defense": 72, "safe_cap": 1500000},
    "مزرعة واستراحة فخمة في عين زارة": {"price": 520000, "defense": 68, "safe_cap": 2500000},
    "عمارة استثمارية 6 طوابق": {"price": 850000, "defense": 80, "safe_cap": 5000000},
    "برج تجاري سكني 12 طابق": {"price": 1600000, "defense": 88, "safe_cap": 12000000},
    "قصر رئاسي محصن في فينيسيا": {"price": 3000000, "defense": 95, "safe_cap": 50000000},
}

SECURITY_SYSTEMS = {
    "كاميرات مراقبة": {"price": 4000, "boost": 10},
    "ابواب مصفحة": {"price": 9000, "boost": 18},
    "جهاز انذار ليلي": {"price": 16000, "boost": 28},
    "حراسة مسلحة": {"price": 35000, "boost": 42},
}

BUSINESS_CATALOG = {
    "قهوة": {"price": 35000, "product": "بن إيطالي ومشروبات وحلويات", "unit_cost": 40, "unit_sell": 95, "npc_rate": 14},
    "مطعم": {"price": 65000, "product": "لحوم وطواجن ومواد غذائية", "unit_cost": 80, "unit_sell": 185, "npc_rate": 16},
    "صيدلية": {"price": 95000, "product": "أدوية ومضادات ومستلزمات طبية", "unit_cost": 120, "unit_sell": 280, "npc_rate": 18},
    "متجر ملابس": {"price": 120000, "product": "ملابس تركية وإيطالية وأحذية", "unit_cost": 150, "unit_sell": 350, "npc_rate": 18},
    "سوبرماركت": {"price": 160000, "product": "سلع غذائية وتموينية شاملة", "unit_cost": 110, "unit_sell": 250, "npc_rate": 24},
    "شركة برمجيات": {"price": 250000, "product": "أنظمة محاسبية وسيرفرات وتطبيقات", "unit_cost": 300, "unit_sell": 720, "npc_rate": 15},
    "مستشفى خاص": {"price": 550000, "product": "أدوية تخصصية ومعدات عمليات", "unit_cost": 500, "unit_sell": 1200, "npc_rate": 20},
    "مول تجاري": {"price": 1200000, "product": "بضائع عالمية وإلكترونيات وماركات", "unit_cost": 800, "unit_sell": 1950, "npc_rate": 30},
}

BLACK_MARKET = {
    "مفك اقفال": {"price": 2500, "power": 12, "desc": "يساعد في كسر أقفال البيوت والمتاجر العادية"},
    "مشوش كاميرات": {"price": 7500, "power": 25, "desc": "يعطل كاميرات المراقبة أثناء سرقة البيوت والمتاجر"},
    "قنبلة دخان": {"price": 15000, "power": 38, "desc": "تغطية سريعة للهروب عند السطو على المتاجر والمصارف"},
    "حقيبة تهكير": {"price": 45000, "power": 65, "desc": "جهاز فك شيفرات الخزائن المصرفية الكبرى"},
    "جواز مزور": {"price": 20000, "power": 0, "desc": "يمسح اسمك من قائمة المطلوبين للشرطة فوراً"},
}

STOCKS = {
    "المدار": 160,
    "ليبيانا": 190,
    "البريقة_للنفط": 350,
    "الخطوط_الليبية": 240,
    "ليبيا_للاتصالات": 280,
    "مصرف_التجارة": 420,
    "حديد_مصراتة": 310,
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

LOCK_LIST = [
    ("الكل", "🛡️ الكل"), ("الدخول", "🚪 الدخول"), ("الروابط", "🔗 الروابط"), ("اليوزر", "📧 اليوزر"),
    ("التاك", "🏷️ التاك"), ("الشارحه", "➗ الشارحه"), ("التعديل", "✏️ التعديل"), ("تعديل الميديا", "🖼️ تعديل الميديا"),
    ("المتحركه", "🎞️ المتحركه"), ("الملفات", "📁 الملفات"), ("الصور", "📸 الصور"), ("الفيديو", "🎥 الفيديو"),
    ("الماركداون", "🔣 الماركداون"), ("البوتات", "🤖 البوتات"), ("التكرار", "🔁 التكرار"), ("الكلايش", "📜 الكلايش"),
    ("السيلفي", "🤳 السيلفي"), ("الملصقات", "🎭 الملصقات"), ("الانلاين", "📲 الانلاين"), ("الدردشه", "💬 الدردشه"),
    ("الهمسه", "🤫 الهمسه"), ("التوجيه", "↪️ التوجيه"), ("الاغاني", "🎵 الاغاني"), ("الصوت", "🎙️ الصوت"),
    ("الجهات", "👤 الجهات"), ("الاشعارات", "🔔 الاشعارات"), ("التثبيت", "📌 التثبيت"), ("الوسائط", "🎞️ الوسائط"),
    ("التفليش", "💣 التفليش"), ("الفشار", "🤬 الفشار"), ("القنوات", "📢 القنوات"), ("الموقع", "📍 الموقع"),
    ("الانكليزيه", "🔤 الانكليزيه"), ("الفارسيه", "🈵 الفارسيه"),
]
LOCK_TYPES = {k: v for k, v in LOCK_LIST}

SETTING_LIST = [
    ("الترحيب", "👋 الترحيب"),
    ("الردود", "💬 الردود"),
    ("الالعاب", "🎮 الألعاب والبنك"),
    ("الرادار", "🚓 رادار المرور"),
]
SETTING_TYPES = {k: v for k, v in SETTING_LIST}

BAD_WORDS = ["كلب", "حمار", "حيوان", "تافه", "غبي", "صايع", "منيك", "قحبة", "شرموط", "عرص", "زبي", "طيز", "كس", "نيك"]
FUN_TITLES = ["ملك", "ملكه", "شيخ", "عمدة", "عسل", "صقر", "ذيب", "زاحف", "طلي", "طامس", "فالح", "سند"]

BOT_CALL_REPLIES = [
    "▽ : عيون {name} يا غالي، تفضل شن تبي؟ 😎🇱🇾",
    "▽ : نعم يا مدير، {name} في الخدمة! اكتب <code>الاوامر</code> وشوف الفخامة 🔥",
    "▽ : ها يا غالي تنادي فيا؟ كان تبي فلوس امشي اخدم بكتابة <code>شغل</code> ما فيش شي ببلاش 😂🏦",
    "▽ : لبيه! {name} حاضر وناظر، شن الجو عندكم؟ ✨",
    "▽ : يا مرحبتين! ناديت {name} ولقيته قدامك، آمرني يا غالي 👑"
]

BEAUTY_COMPLIMENTS = [
    "ما شاء الله، وجهك ينور القروب حتى لو الضي هارب! 😍⚡",
    "فخامة وهيبة ليبية أصيلة، خمسة وخميسة عليك! 🔥👑",
    "جمال رباني يفتح النفس، ربي يحفظك يا غالي ✨🌸",
    "صورة عالمية، تستاهل تنحط في لوحة شرف القروب! 😎💎",
    "نور على نور، هالصورة ترد الروح والله! ❤️🇱🇾"
]

SONGS_LIST = [
    "🎵 <i>يا غالي لو تبي ترحل، خذ قلبي معاك...</i> 🎶",
    "🎵 <i>طرابلس يا عروس البحر، فيك الزين وفيك السهر...</i> 🇱🇾🎶",
    "🎵 <i>بنغازي يا مربى العز، قلبي لغيرك ما يهتز...</i> 🇱🇾🎶",
    "🎵 <i>مصراتة يا بلاد الخير، فيك التجارة وفيك الطير...</i> 🇱🇾🎶"
]

POEMS_LIST = [
    "📜 <b>شعر شعبي ليبي :</b>\nيا صاحبي الدنيا امتحانات .. وفيها الصبر مفتاح الفرج\nواللي معاه الله في الأزمات .. يطلع من الضيقة بلا حرج",
    "📜 <b>شعر ليبي أصيل :</b>\nعز الرفيق اللي يبان نهار الضيق .. أما الرخا واجد تلاقي خوت\nوزن الذهب يفرق على التلفيق .. والمرجلة موقف قبل ما تموت"
]

JOKES_LIST = [
    "😂 واحد ليبي قال لصاحبه: عيني توجع فيا من أمس! قاله صاحبه: والله أمس سنوني وجعتني خلعتها ارتحت.. كان تبي نصيحتي اخلعها! 🤣",
    "😂 واحد مشى للدكتور قاله: يا دكتور كل ما نشرب طاسة شاهي عيني تضربني! قاله الدكتور: حول الكاشيك من الطاسة يا فالح! 🤣",
    "😂 سألوا واحد بخيل: لو الدنيا صقع قارس، شن تدير؟ قال: نقرب من الدفاية. قالوله: ولو زاد الصقع بكل؟ قال: نولع الدفاية! 🤣"
]

ADHKAR_LIST = [
    "📿 <b>ذكر الله :</b> «سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ»",
    "📿 <b>ذكر الله :</b> «لَا إِلَهَ إِلَّا أَنْتَ سُبْحَانَكَ إِنِّي كُنْتُ مِنَ الظَّالِمِينَ»",
    "📿 <b>ذكر الله :</b> «أَسْتَغْفِرُ اللَّهَ الْعَظِيمَ وَأَتُوبُ إِلَيْهِ»"
]

LAW_KHAYAROUK_LIST = [
    "🤔 <b>لو خيروك :</b> تاخذ 100 ألف دينار كاش توا، ولا تفتح مول تجاري بالشراكة مع صاحبك؟",
    "🤔 <b>لو خيروك :</b> تاكل بازين كل يوم لمدة شهر، ولا ما تاكلش مكرونة مبكبكة لمدة سنة؟"
]

SARAHA_QUESTIONS = [
    "💬 <b>سؤال صراحة :</b> شن أكثر شيء ندمت عليه في حياتك؟",
    "💬 <b>سؤال صراحة :</b> من هو أكثر شخص في هذا القروب تثق فيه وتدخله معاك شريك في متجر؟"
]

OPINIONS_LIST = [
    "عسل القروب هذا، الله يحفظه ويخليه لينا 😍🍯",
    "شخصية فخمة وهيبة، كلامه كله موزون 👑✨",
    "تاجر شاطر بس ديروا بالكم على متاجركم منه في الليل 😂🦹‍♂️"
]

ROASTS_LIST = [
    "يا راجل وجهك يجيب هروب الضي في عز القايلة 😂⚡",
    "أنت لو تفتح مصرف خاص، أول واحد يسرقه هو العساس متاعك 😂🏦"
]

GIFTS_LIST = [
    "🎁 ساعـة رولكس فخمة ⌚✨",
    "🎁 صحن مبكبكة سخون باللحم الوطني 🍲🔥",
    "🎁 آيفون 16 برو ماكس ذهبي 📱😍",
    "🎁 طاسة شاهي باللوز مع كعك مالح ☕🥨"
]

QUESTIONS_BANK = {
    "اسئله": [
        ("ما هي عاصمة ليبيا؟", "طرابلس"),
        ("ما هي العملة الرسمية في ليبيا؟", "الدينار"),
        ("في أي مدينة ليبية تقع آثار لبدة الكبرى؟", "الخمس"),
        ("ما هو اللقب الشهير لمدينة بنغازي؟", "العصية"),
        ("ما هي أكبر مدينة في الجنوب الليبي؟", "سبها"),
    ],
    "لغز": [
        ("شيء يمشي بلا رجلين ويبكي بلا عينين، شنو هو؟", "السحاب"),
        ("له أسنان كثيرة ولا يعض، شنو هو؟", "المشط"),
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
        ("فكك كلمة: (مصراتة)", "م ص ر ا ت ة"),
    ],
    "عكس": [
        ("اعكس كلمة: (سحاب)", "باحس"),
        ("اعكس كلمة: (قمر)", "رمق"),
        ("اعكس كلمة: (مصرف)", "فرصم"),
    ],
    "معاني": [
        ("ما معنى الكلمة الليبية: (كاشيك) بالفصحى؟", "ملعقة"),
        ("ما معنى الكلمة الليبية: (طاسة)؟", "كوب"),
        ("ما معنى الكلمة الليبية: (قعمز)؟", "اجلس"),
        ("ما معنى الكلمة الليبية: (هلبة)؟", "كثير"),
    ],
    "امثله": [
        ("أكمل المثل الليبي: دير الخير وانساه، ودير الشر و...", "توقاه"),
        ("أكمل المثل الليبي: اللي ما يطول العنب يقول عليه...", "حامض"),
    ]
}

active_games = {}
active_airdrops = {}
group_msg_counter = {}
pending_whispers = {}
pending_bank_creation = {}  # user_id -> timestamp (لفتح مصرف خاص خطوة بخطوة)
active_duels = {}
last_radar_time = {}


# ══════════════════════════════════════════════════════════════════
# 🤖 محرك الزبائن الوهميين (NPCs) التلقائي للمتاجر والمولات والصيدليات
# ══════════════════════════════════════════════════════════════════

def npc_customers_engine():
    while True:
        try:
            time.sleep(180)
            with db_lock:
                conn = get_db()
                c = conn.cursor()
                stores = c.execute("SELECT * FROM businesses WHERE stock > 0 AND is_open = 1").fetchall()
                for st in stores:
                    b_type = st["biz_type"]
                    if b_type not in BUSINESS_CATALOG:
                        continue
                    cat = BUSINESS_CATALOG[b_type]
                    mult = st["marketing"] + (2 if st["ecommerce"] else 0)
                    sold_units = min(st["stock"], random.randint(2, cat["npc_rate"]) * mult)
                    if sold_units <= 0:
                        continue
                    gross = sold_units * cat["unit_sell"]

                    staff_rows = c.execute("SELECT * FROM business_staff WHERE biz_id = ?", (st["id"],)).fetchall()
                    staff_cut_total = 0
                    for emp in staff_rows:
                        if norm_ar(emp["pay_mode"]) == "نسبه":
                            cut = int(gross * (emp["pay_val"] / 100.0))
                        else:
                            cut = min(emp["pay_val"], int(gross * 0.20))
                        if cut > 0:
                            staff_cut_total += cut
                            c.execute("UPDATE users SET bank_balance = bank_balance + ? WHERE user_id = ?", (cut, emp["user_id"]))

                    net_profit = max(0, gross - staff_cut_total)
                    c.execute(
                        "UPDATE businesses SET stock = stock - ?, vault = vault + ?, total_sales = total_sales + ? WHERE id = ?",
                        (sold_units, net_profit, sold_units, st["id"])
                    )
                conn.commit()
                conn.close()
        except Exception as e:
            logging.error("خطأ في محرك الزبائن الوهميين: %s", e)

threading.Thread(target=npc_customers_engine, daemon=True).start()


# ══════════════════════════════════════════════════════════════════
# 📋 القوائم الموحدة والمنظمة + النوافذ السريعة
# ══════════════════════════════════════════════════════════════════

MENU_TEXTS = {
    "main": (
        "▽ : اوامر البوت الرئيسية :\n"
        "------------------\n"
        "▽ : م1 ~ الحمايه\n"
        "▽ : م2 ~ الادمنيه\n"
        "▽ : م3 ~ المدراء\n"
        "▽ : م4 ~ المنشئين\n"
        "▽ : م5 ~ المالكين\n"
        "▽ : م6 ~ التحشيش\n"
        "▽ : م7 ~ التسليه\n"
        "▽ : م8 ~ البنك\n"
        "▽ : م9 ~ التنظيف\n"
        "------------------\n"
        "▽ : قناة السورس والتحديثات : @{channel}"
    ),
    "menu_1": (
        "▽ : اوامر الحمايه كالاتي ...\n"
        "------------------\n"
        "▽ : قفل ، فتح ← الامر\n"
        "▽ : تستطيع قفل حمايه كما يلي ...\n"
        "▽ : ← { بالتقييد ، بالطرد ، بالكتم }\n"
        "------------------\n"
        "▽ : الكل ~ الدخول\n"
        "▽ : الروابط ~ اليوزر\n"
        "▽ : التاك ~ الشارحه\n"
        "▽ : التعديل ~ تعديل الميديا\n"
        "▽ : المتحركه ~ الملفات\n"
        "▽ : الصور ~ الفيديو\n"
        "------------------\n"
        "▽ : الماركداون ~ البوتات\n"
        "▽ : التكرار ~ الكلايش\n"
        "▽ : السيلفي ~ الملصقات\n"
        "▽ : الانلاين ~ الدردشه\n"
        "▽ : الهمسه\n"
        "------------------\n"
        "▽ : التوجيه ~ الاغاني\n"
        "▽ : الصوت ~ الجهات\n"
        "▽ : الاشعارات ~ التثبيت\n"
        "▽ : الوسائط ~ التفليش\n"
        "▽ : الفشار ~ القنوات\n"
        "▽ : الموقع ~ الانكليزيه\n"
        "▽ : الفارسيه\n"
        "------------------"
    ),
    "menu_2": (
        "▽ : اوامر الادمنيه كالاتي ...\n"
        "------------------\n"
        "▽ : حظر ~ الغاء حظر\n"
        "▽ : طرد ~ كتم ~ الغاء كتم\n"
        "▽ : انذار ~ حذف الانذارات\n"
        "▽ : تثبيت ~ الغاء تثبيت\n"
        "▽ : كشف ~ ايدي ~ صورتي\n"
        "▽ : رتبتي ~ لقبي\n"
        "▽ : رفع مميز ~ تنزيل مميز\n"
        "------------------"
    ),
    "menu_3": (
        "▽ : اوامر المدراء كالاتي ...\n"
        "------------------\n"
        "▽ : رفع ادمن ~ تنزيل ادمن\n"
        "▽ : اضف رد الكلمه=الجواب\n"
        "▽ : مسح رد الكلمه ~ الردود\n"
        "▽ : اضف اختصار الحرف=الامر\n"
        "▽ : مسح اختصار الحرف ~ الاختصارات\n"
        "▽ : ضع ترحيب ~ ضع قوانين ~ القوانين\n"
        "------------------"
    ),
    "menu_4": (
        "▽ : اوامر المنشئين كالاتي ...\n"
        "------------------\n"
        "▽ : رفع مدير ~ تنزيل مدير\n"
        "▽ : المدراء ~ المنشئين\n"
        "▽ : الادمنيه ~ المميزين\n"
        "▽ : تنزيل الكل\n"
        "------------------"
    ),
    "menu_5": (
        "▽ : اوامر المالكين كالاتي ...\n"
        "------------------\n"
        "▽ : تفعيل ~ رفع نفسي مالك\n"
        "▽ : رفع مالك ~ تنزيل مالك\n"
        "▽ : رفع منشئ ~ تنزيل منشئ\n"
        "▽ : ضع لقب + اللقب بالرد\n"
        "▽ : المالكين\n"
        "------------------"
    ),
    "menu_6": (
        "▽ : اوامر التحشيش الليبي (لجميع الأعضاء) ...\n"
        "------------------\n"
        "▽ : رفع ملك ~ رفع ملكه ~ رفع شيخ\n"
        "▽ : رفع عسل ~ رفع صقر ~ رفع ذيب\n"
        "▽ : رفع طلي ~ رفع زاحف ~ رفع فالح\n"
        "▽ : نسبه الحب ~ نسبه الذكاء ~ نسبه الجمال\n"
        "▽ : شنو رايك بهذا ~ رزله ~ انطي هديه\n"
        "▽ : ص ~ صورتي\n"
        "------------------"
    ),
    "menu_7": (
        "▽ : اوامر التسليه والزواج (لجميع الأعضاء) ...\n"
        "------------------\n"
        "▽ : همسه ~ همسة (بالرد)\n"
        "▽ : زواج + المهر (بالرد)\n"
        "▽ : طلاق ~ خلع ~ زواجي\n"
        "▽ : غنيلي ~ شعر ~ نكته\n"
        "▽ : اذكار ~ لو خيروك ~ صراحه\n"
        "------------------"
    ),
    "menu_8": (
        "▽ : اوامر البنك والحياة الواقعية (لجميع الأعضاء) ...\n"
        "------------------\n"
        "▽ : انشاء حساب ~ انشاء حساب بنكي\n"
        "▽ : تغيير البنك ~ الفروع ~ حسابي ~ فلوسي\n"
        "▽ : ايداع ~ سحب ~ تحويل (من اي فرع)\n"
        "▽ : فتح مصرف خاص + الاسم ~ مصرفي\n"
        "------------------\n"
        "▽ : المدن ~ اختيار مدينتي ~ سفر + المدينه\n"
        "▽ : الوظائف ~ وظيفه + المهنه ~ وظيفتي\n"
        "▽ : شغل ~ عمل ~ راتب ~ ترقيه\n"
        "▽ : علاج ~ تصليح ~ قبض ~ اختراق صراف\n"
        "------------------\n"
        "▽ : السيارات ~ شراء سياره + الاسم\n"
        "▽ : بيع سياره ~ صيانه سيارتي ~ سباق\n"
        "▽ : العقارات ~ شراء عقار + الاسم\n"
        "▽ : خزنه البيت ~ ايداع بالبيت ~ سحب من البيت\n"
        "▽ : تطوير الحمايه + النوع\n"
        "------------------\n"
        "▽ : المتاجر ~ فتح متجر النوع=الاسم\n"
        "▽ : متجري ~ شراء بضاعه + العدد\n"
        "▽ : تسويق متجري ~ تفعيل بيع الكتروني\n"
        "▽ : فتح المتجر ~ قفل المتجر ~ سحب ارباح المتجر\n"
        "▽ : تعيين موظف نسبه 15 (بالرد)\n"
        "▽ : تعيين موظف راتب 1000 (بالرد)\n"
        "▽ : فصل موظف (بالرد) ~ اضافه شريك 30 (بالرد)\n"
        "------------------\n"
        "▽ : البورصه ~ شراء اسهم ~ بيع اسهم\n"
        "▽ : السوق الحر ~ عرض سياره للبيع ~ عرض عقار للبيع\n"
        "▽ : السوق السوداء ~ شراء اداه + الاسم\n"
        "▽ : سرقه جيبه ~ سرقه بيته ~ سرقه متجره (بالرد)\n"
        "▽ : سرقه مصرف + اسم المصرف\n"
        "▽ : دفع كفاله ~ رشوه العساس ~ تهريب\n"
        "------------------"
    ),
    "menu_9": (
        "▽ : اوامر التنظيف كالاتي ...\n"
        "------------------\n"
        "▽ : مسح (بالرد)\n"
        "▽ : مسح + العدد\n"
        "▽ : اطردني\n"
        "------------------"
    ),
    "menu_games": (
        "▽ : اوامر الالعاب والمسابقات (لجميع الأعضاء) ...\n"
        "------------------\n"
        "▽ : اسئله ~ لغز ~ عواصم ~ فكك\n"
        "▽ : عكس ~ معاني ~ امثله ~ رياضيات\n"
        "▽ : حجره ~ ورقه ~ مقص\n"
        "▽ : تحدي + المبلغ (بالرد)\n"
        "▽ : حظ ~ مضاربه ~ استثمار ~ اكشط\n"
        "------------------"
    ),
    "menu_dev": (
        "▽ : اوامر المطور الاساسي (MG) السرية ...\n"
        "------------------\n"
        "▽ : تعمل بالرد او باليوزر/الايدي في القروب او الخاص :\n"
        "▽ : اضف فلوس ~ خصم فلوس ~ تصفير فلوسه\n"
        "▽ : منح سياره ~ سحب سياره\n"
        "▽ : منح عقار ~ سحب عقار\n"
        "▽ : منح متجر ~ سحب متجر\n"
        "▽ : منح مصرف ~ سحب مصرف\n"
        "▽ : تعيين مهنه ~ فصل من العمل\n"
        "▽ : اطلاق سراح ~ عفو\n"
        "------------------\n"
        "▽ : تغيير اسم البوت + الاسم\n"
        "▽ : صنع اكشطها ~ قائمه اكشطها\n"
        "▽ : الهمسات ~ الاحصائيات ~ اذاعه\n"
        "▽ : نسخه احتياطيه ~ استعاده\n"
        "------------------"
    )
}

POPUP_ALERT_MENUS = {
    "menu_1": "▽ م1 الحمايه:\nقفل / فتح + (الكل، الدخول، الروابط، اليوزر، التاك، التعديل، المتحركه، الملفات، الصور، الفيديو، البوتات، الكلايش، الملصقات، الدردشه، الهمسه، التوجيه، الفشار)\n(اكتب م1 للتفاصيل)",
    "menu_2": "▽ م2 الادمنيه:\nحظر ~ الغاء حظر ~ طرد\nكتم ~ الغاء كتم ~ انذار\nتثبيت ~ الغاء تثبيت\nكشف ~ ايدي ~ صورتي ~ رتبتي\nرفع مميز ~ تنزيل مميز\n(اكتب م2 للتفاصيل)",
    "menu_3": "▽ م3 المدراء:\nرفع ادمن ~ تنزيل ادمن\nاضف رد الكلمه=الجواب ~ مسح رد\nالردود ~ اضف اختصار الحرف=الامر\nضع ترحيب ~ ضع قوانين ~ القوانين",
    "menu_4": "▽ م4 المنشئين:\nرفع مدير ~ تنزيل مدير\nالمدراء ~ المنشئين\nالادمنيه ~ المميزين\nتنزيل الكل",
    "menu_5": "▽ م5 المالكين:\nتفعيل ~ رفع نفسي مالك\nرفع مالك ~ تنزيل مالك\nرفع منشئ ~ تنزيل منشئ\nضع لقب + اللقب بالرد ~ المالكين",
    "menu_6": "▽ م6 التحشيش (للجميع):\nرفع (ملك/ملكه/شيخ/عسل/صقر/ذيب/طلي/زاحف)\nنسبه (الحب/الذكاء/الجمال)\nشنو رايك بهذا ~ رزله ~ انطي هديه\nص ~ صورتي",
    "menu_7": "▽ م7 التسليه والزواج (للجميع):\nهمسه (بالرد)\nزواج + المهر ~ طلاق ~ خلع ~ زواجي\nغنيلي ~ شعر ~ نكته ~ اذكار\nلو خيروك ~ صراحه",
    "menu_8": "▽ م8 البنك والحياة الواقعية (للجميع):\nانشاء حساب ~ حسابي ~ الفروع ~ فتح مصرف خاص\nالمدن ~ سفر ~ الوظائف ~ وظيفتي ~ شغل ~ ترقيه\nالسيارات ~ العقارات ~ المتاجر ~ متجري ~ سرقه\n(اكتب م8 للشرح الكامل)",
    "menu_9": "▽ م9 التنظيف:\nمسح (بالرد لحذف رسالة)\nمسح + العدد (مثال: مسح 20)\nاطردني",
    "menu_games": "▽ الالعاب والمسابقات (للجميع):\nاسئله ~ لغز ~ عواصم ~ فكك\nعكس ~ معاني ~ امثله ~ رياضيات\nحجره ~ ورقه ~ مقص ~ تحدي + المبلغ\nحظ ~ مضاربه ~ استثمار ~ اكشط",
    "menu_dev": "⚡ لوحة المطور MG:\nاضف فلوس ~ خصم فلوس ~ تصفير فلوسه\nمنح/سحب (سياره، عقار، متجر، مصرف)\nتعيين مهنه ~ فصل من العمل ~ عفو\nالهمسات ~ الاحصائيات ~ اذاعه"
}
# ══════════════════════════════════════════════════════════════════
# 🛠️ دوال المساعدة وإدارة البيانات والبحث الذكي (رد / يوزر / آيدي)
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
    base_p = STOCKS.get(s_name, 160)
    factor = (int(time.time()) // 600) % 9
    return max(40, base_p + (factor * 18) - 60)

def ensure_user(user: types.User) -> dict:
    full_name = (user.first_name or "") + (f" {user.last_name}" if user.last_name else "")
    full_name = full_name.strip() or "مواطن ليبي"
    username = (user.username or "").lstrip("@")
    with db_lock:
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ?", (user.id,))
        row = c.fetchone()
        if not row:
            c.execute(
                "INSERT INTO users (user_id, name, username, cash, bank_balance, msg_count, points) VALUES (?, ?, ?, 0, 0, 1, 1)",
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
            u = get_user_by_username(p)
            if u:
                return u
        elif p.isdigit() and len(p) >= 6:
            u = get_user_by_id(int(p))
            if u:
                return u
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

def get_user_businesses(user_id: int) -> list[dict]:
    with db_lock:
        conn = get_db()
        rows = conn.execute("SELECT * FROM businesses WHERE owner_id = ?", (user_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

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
    if lock_name == "الكل":
        for k in LOCK_TYPES.keys():
            locks[k] = state
    else:
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
# 📢 فحص الاشتراك الإجباري
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
# 🎨 بناء لوحات الأزرار بأكواد قصيرة جداً (< 25 بايت) لتعمل 100% بدون أخطاء
# ══════════════════════════════════════════════════════════════════

def render_menu(key: str) -> str:
    return MENU_TEXTS[key].replace("{bot_name}", esc(get_bot_name())).replace("{channel}", CHANNEL_USERNAME)

def get_private_start_kb(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("قناه البوت", url=f"https://t.me/{CHANNEL_USERNAME}"),
        types.InlineKeyboardButton("اضفني لمجموعتك ➕", url=f"https://t.me/{BOT_USERNAME}?startgroup=true"),
    )
    kb.row(
        types.InlineKeyboardButton("📍 اختيار مدينتي", callback_data=f"pc_m:{user_id}"),
        types.InlineKeyboardButton("🏦 فتح / تغيير المصرف", callback_data=f"pb_m:{user_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("المطور", url=f"tg://user?id={ADMIN_ID}"),
        types.InlineKeyboardButton("اوامر الاعضاء", callback_data=f"pm_c:{user_id}"),
    )
    if user_id == ADMIN_ID:
        kb.row(
            types.InlineKeyboardButton("⚡ لوحة المطور الأساسي MG", callback_data=f"menu_dev:{user_id}"),
        )
    kb.row(
        types.InlineKeyboardButton("ARKAN SOURCE ™ ®", url=f"https://t.me/{CHANNEL_USERNAME}"),
    )
    return kb

def get_commands_kb(owner_id: int = 0) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("م1", callback_data=f"menu_1:{owner_id}"),
        types.InlineKeyboardButton("م2", callback_data=f"menu_2:{owner_id}"),
        types.InlineKeyboardButton("م3", callback_data=f"menu_3:{owner_id}"),
        types.InlineKeyboardButton("م4", callback_data=f"menu_4:{owner_id}"),
        types.InlineKeyboardButton("م5", callback_data=f"menu_5:{owner_id}"),
        types.InlineKeyboardButton("م6", callback_data=f"menu_6:{owner_id}"),
        types.InlineKeyboardButton("م7", callback_data=f"menu_7:{owner_id}"),
        types.InlineKeyboardButton("م8", callback_data=f"menu_8:{owner_id}"),
        types.InlineKeyboardButton("م9", callback_data=f"menu_9:{owner_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("الالعاب", callback_data=f"menu_games:{owner_id}"),
        types.InlineKeyboardButton("م المطور", callback_data=f"menu_dev:{owner_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("القفل / الفتح", callback_data=f"locks_p:{owner_id}"),
        types.InlineKeyboardButton("التفعيل/ التعطيل", callback_data=f"sets_p:{owner_id}"),
    )
    kb.row(
        types.InlineKeyboardButton("ARKAN SOURCE ™ ®", url=f"https://t.me/{CHANNEL_USERNAME}")
    )
    return kb

def build_bank_secret_kb(owner_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.row(
        types.InlineKeyboardButton("💳 كشف رصيد المصرف السري", callback_data=f"sbank_{owner_id}"),
        types.InlineKeyboardButton("📩 إرسال التقرير للخاص", callback_data=f"dbank_{owner_id}")
    )
    kb.row(
        types.InlineKeyboardButton("🏦 فتح / تغيير المصرف", callback_data=f"pb_m:{owner_id}"),
        types.InlineKeyboardButton("📍 تغيير الفرع / المدينة", callback_data=f"pc_m:{owner_id}")
    )
    return kb

def build_city_kb(owner_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for idx, (c_name, ticket, _) in enumerate(CITY_LIST):
        btns.append(types.InlineKeyboardButton(f"📍 {c_name} ({ticket} د.ل)", callback_data=f"sc:{owner_id}:{idx}"))
    kb.add(*btns)
    return kb

def build_banks_kb(owner_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    for idx, (b_name, fee, sec, _) in enumerate(BANK_LIST):
        kb.add(types.InlineKeyboardButton(
            f"🏛️ {b_name} (نسبة: {fee}% | حماية: {sec}%)",
            callback_data=f"sb:{owner_id}:o:{idx}"
        ))
    with db_lock:
        conn = get_db()
        custom_rows = conn.execute("SELECT id, bank_name, fee_pct, security FROM custom_banks").fetchall()
        conn.close()
    for cr in custom_rows:
        kb.add(types.InlineKeyboardButton(
            f"🏦 مصرف خاص: {cr['bank_name']} (نسبة: {cr['fee_pct']}% | حماية: {cr['security']}%)",
            callback_data=f"sb:{owner_id}:c:{cr['id']}"
        ))
    return kb

def build_branches_kb(owner_id: int, bank_idx: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    if 0 <= bank_idx < len(BANK_LIST):
        branches = BANK_LIST[bank_idx][3]
    else:
        branches = ["الفرع الرئيسي - طرابلس", "فرع بنغازي", "فرع مصراتة"]
        bank_idx = 0
    for br_idx, br_name in enumerate(branches):
        kb.add(types.InlineKeyboardButton(f"🏢 {br_name}", callback_data=f"sbr:{owner_id}:{bank_idx}:{br_idx}"))
    return kb

def build_jobs_kb(owner_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for idx, j_name in enumerate(JOB_LIST):
        sal = JOBS[j_name]["levels"][1]["salary"]
        btns.append(types.InlineKeyboardButton(f"💼 {j_name} ({sal} د.ل)", callback_data=f"sj:{owner_id}:{idx}"))
    kb.add(*btns)
    return kb

def build_locks_kb(chat_id: int, owner_id: int = 0) -> types.InlineKeyboardMarkup:
    locks = get_group_locks(chat_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for idx, (key, label) in enumerate(LOCK_LIST):
        status = "🔒" if locks.get(key, False) else "🔓"
        buttons.append(
            types.InlineKeyboardButton(f"{label} : {status}", callback_data=f"tl:{owner_id}:{idx}")
        )
    kb.add(*buttons)
    kb.row(types.InlineKeyboardButton("🔙 رجوع للأوامر الرئيسية", callback_data=f"m_main:{owner_id}"))
    return kb

def build_settings_kb(chat_id: int, owner_id: int = 0) -> types.InlineKeyboardMarkup:
    settings = get_group_settings(chat_id)
    kb = types.InlineKeyboardMarkup(row_width=2)
    buttons = []
    for idx, (key, label) in enumerate(SETTING_LIST):
        status = "✅ مفعل" if settings.get(key, True) else "❌ معطل"
        buttons.append(
            types.InlineKeyboardButton(f"{label} : {status}", callback_data=f"ts:{owner_id}:{idx}")
        )
    kb.add(*buttons)
    kb.row(types.InlineKeyboardButton("🔙 رجوع للأوامر الرئيسية", callback_data=f"m_main:{owner_id}"))
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
                sender_id = m.from_user.id if m.from_user else 0
                bot.send_message(
                    m.chat.id,
                    (
                        f"▽ : تم إضافة البوت ({esc(b_name)}) بنجاح 🇱🇾\n"
                        f"------------------\n"
                        f"▽ : ارفع البوت مشرفاً ثم ارسل <code>تفعيل</code>\n"
                        f"▽ : لعرض الأوامر ارسل <code>الاوامر</code>"
                    ),
                    reply_markup=get_commands_kb(sender_id)
                )
            elif (locks.get("البوتات", False) or locks.get("الكل", False)) and get_rank(m.chat.id, m.from_user.id) < 2:
                try:
                    bot.ban_chat_member(m.chat.id, new_user.id)
                except Exception:
                    pass
        else:
            if locks.get("الدخول", False) or locks.get("الكل", False):
                try:
                    bot.ban_chat_member(m.chat.id, new_user.id)
                    bot.unban_chat_member(m.chat.id, new_user.id)
                except Exception:
                    pass
                continue
            ensure_user(new_user)
            if settings.get("الترحيب", True) and grp.get("welcome_enabled", 1):
                w_text = grp.get("welcome_text") or "مرحبتين بيك يا غالي نورت القروب 🇱🇾"
                bot.reply_to(
                    m,
                    f"▽ : أهلاً بك يا <a href='tg://user?id={new_user.id}'>{esc(new_user.first_name)}</a>\n"
                    f"▽ : {esc(w_text)}\n"
                    f"▽ : افتح حسابك المصرفي بكتابة <code>انشاء حساب</code>"
                )

@bot.edited_message_handler(func=lambda m: m.chat.type in ("group", "supergroup"))
def on_message_edited(m: types.Message):
    if get_rank(m.chat.id, m.from_user.id) >= 1:
        return
    locks = get_group_locks(m.chat.id)
    if locks.get("التعديل", False) or locks.get("تعديل الميديا", False) or locks.get("الكل", False):
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except Exception:
            pass

@bot.message_handler(content_types=["photo", "video", "sticker", "animation", "document", "voice", "audio", "video_note", "contact", "location"])
def media_handler(m: types.Message):
    if m.chat.type not in ("group", "supergroup"):
        return
    if m.from_user and m.from_user.id == ADMIN_ID:
        return
    if get_rank(m.chat.id, m.from_user.id) >= 1:
        return
    locks = get_group_locks(m.chat.id)
    del_msg = False
    if locks.get("الكل") or locks.get("الدردشه") or locks.get("الوسائط"):
        del_msg = True
    elif (m.forward_from or m.forward_from_chat) and (locks.get("التوجيه") or locks.get("القنوات")):
        del_msg = True
    elif m.content_type == "photo" and locks.get("الصور"):
        del_msg = True
    elif m.content_type == "video" and locks.get("الفيديو"):
        del_msg = True
    elif m.content_type == "sticker" and locks.get("الملصقات"):
        del_msg = True
    elif m.content_type == "animation" and locks.get("المتحركه"):
        del_msg = True
    elif m.content_type == "document" and locks.get("الملفات"):
        del_msg = True
    elif m.content_type == "voice" and locks.get("الصوت"):
        del_msg = True
    elif m.content_type == "audio" and locks.get("الاغاني"):
        del_msg = True
    elif m.content_type == "video_note" and locks.get("السيلفي"):
        del_msg = True
    elif m.content_type == "contact" and locks.get("الجهات"):
        del_msg = True
    elif m.content_type == "location" and locks.get("الموقع"):
        del_msg = True
    if del_msg:
        try:
            bot.delete_message(m.chat.id, m.message_id)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════
# ✨ واجهة الخاص (/start) ونظام الهمسة السرية
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

    if m.chat.type == "private":
        caption = (
            f"▽ : أهلا بك في بوت {esc(b_name)} 🇱🇾\n"
            f"------------------\n"
            f"▽ : مدينتك الحالية ← {{ {esc(u['city'])} }}\n"
            f"▽ : مصرفك الحالي ← {{ {esc(u['bank_name'])} }}\n"
            f"▽ : فرع المصرف ← {{ {esc(u['bank_branch'])} }}\n"
            f"------------------\n"
            f"▽ : اضف البوت وارفعه مشرف في مجموعتك\n"
            f"▽ : ارسل {{ تفعيل }} ليتم تفعيل المجموعه\n"
            f"▽ : يوزر البوت ← {{@{BOT_USERNAME}}}"
        )
        if user.id == ADMIN_ID:
            caption += "\n------------------\n⚡ <b>مرحباً بك يا مطور البوت (MG)! جميع أوامرك السيادية تعمل هنا في الخاص وفي المجموعات.</b>"
        send_with_user_photo(
            m.chat.id,
            user.id,
            caption,
            reply_to_message_id=m.message_id,
            reply_markup=get_private_start_kb(user.id)
        )
        return

    bot.reply_to(
        m,
        render_menu("main"),
        reply_markup=get_commands_kb(user.id)
    )


# ══════════════════════════════════════════════════════════════════
# 👮‍♂️ دالة معالجة أوامر الإدارة والحماية (م1-م5 و م9) والبطاقة الشخصية
# ══════════════════════════════════════════════════════════════════

def handle_admin_and_info_cmds(m: types.Message, text: str, u_data: dict, grp_data: dict, user_rank: int, locks: dict, now: int) -> bool:
    user = m.from_user
    chat_id = m.chat.id
    b_name = get_bot_name()
    ntext = norm_ar(text)

    # القوائم متاحة لجميع الأعضاء
    if ntext in ("الاوامر", "اوامر", "قائمه الاوامر"):
        bot.reply_to(m, render_menu("main"), reply_markup=get_commands_kb(user.id))
        return True

    if ntext in ("م المطور", "اوامر المطور"):
        if user.id != ADMIN_ID:
            bot.reply_to(m, "▽ : 🚫 هذا القسم خاص بالمطور الأساسي (MG) فقط!")
            return True
        bot.reply_to(m, render_menu("menu_dev"), reply_markup=get_commands_kb(user.id))
        return True

    for i in range(1, 10):
        if ntext == f"م{i}" or ntext == f"م {i}":
            bot.reply_to(m, render_menu(f"menu_{i}"), reply_markup=get_commands_kb(user.id))
            return True

    if ntext in ("الالعاب", "العاب"):
        bot.reply_to(m, render_menu("menu_games"), reply_markup=get_commands_kb(user.id))
        return True

    if ntext in ("الحمايه", "لوحه الحمايه"):
        if user_rank < 2:
            bot.reply_to(m, "▽ : ❌ لوحة قفل وفتح الحماية مخصصة للادمنية فما فوق فقط!")
            return True
        bot.reply_to(m, f"▽ : لوحة القفل والفتح لبوت ({esc(b_name)}) :", reply_markup=build_locks_kb(chat_id, user.id))
        return True

    if ntext in ("الاعدادات", "التفعيل والتعطيل"):
        if user_rank < 3:
            bot.reply_to(m, "▽ : ❌ لوحة الإعدادات مخصصة للمدراء فما فوق فقط!")
            return True
        bot.reply_to(m, f"▽ : لوحة التفعيل والتعطيل لبوت ({esc(b_name)}) :", reply_markup=build_settings_kb(chat_id, user.id))
        return True

    # الهمسة السرية متاحة لجميع الأعضاء
    if ntext == "همسه":
        if locks.get("الهمسه", False) and user_rank < 2:
            return True
        if not m.reply_to_message or not m.reply_to_message.from_user:
            bot.reply_to(m, "▽ : قم بالرد على رسالة الشخص الذي تريد إرسال همسة له واكتب <code>همسه</code>")
            return True
        target = m.reply_to_message.from_user
        if target.is_bot:
            bot.reply_to(m, "▽ : لا يمكنك إرسال همسة إلى بوت!")
            return True
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
        return True

    # البطاقة الشخصية وتقييم الصورة والكشف متاحة لجميع الأعضاء
    if ntext in ("ايدي", "معلوماتي", "رتبتي", "لقبي", "بطاقتي"):
        c_title = get_custom_title(chat_id, user.id)
        u_biz = get_user_businesses(user.id)
        biz_names = "، ".join([b["custom_name"] for b in u_biz]) if u_biz else "بدون متجر"
        job_lvl_title = JOBS.get(u_data["job"], {}).get("levels", {}).get(u_data["job_level"], {}).get("title", u_data["job"])
        caption = (
            f"▽ : البطاقة الشخصية للمواطن 🇱🇾\n"
            f"------------------\n"
            f"▽ : الاسم ← {esc(u_data['name'])}\n"
            f"▽ : الايدي ← <code>{user.id}</code>\n"
            f"▽ : المدينة ← {esc(u_data['city'])}\n"
            f"▽ : الرتبة ← {RANK_NAMES.get(user_rank, 'عضو 🙍‍♂️')}\n"
            f"▽ : اللقب ← {esc(c_title)}\n"
            f"▽ : المهنة ← {esc(job_lvl_title)} (مستوى {u_data['job_level']})\n"
            f"▽ : الكاش في الجيب ← {u_data['cash']} د.ل 💵\n"
            f"▽ : كاش المنزل ← {u_data['home_cash']} د.ل 🏠\n"
            f"▽ : رصيد المصرف ← 🔒 مشفر (سري)\n"
            f"▽ : السكن ← {esc(u_data['house'])}\n"
            f"▽ : السيارة ← {esc(u_data['car'])}\n"
            f"▽ : المتاجر ← {esc(biz_names)}\n"
            f"------------------"
        )
        send_with_user_photo(chat_id, user.id, caption, reply_to_message_id=m.message_id, reply_markup=build_bank_secret_kb(user.id))
        return True

    if ntext == "صورتي":
        pct = 100 if user.id == ADMIN_ID else random.randint(68, 100)
        comp = random.choice(BEAUTY_COMPLIMENTS)
        caption = (
            f"▽ : فحص جمال الصورة الشخصية 📸\n"
            f"------------------\n"
            f"▽ : العضو ← {esc(u_data['name'])}\n"
            f"▽ : نسبة الجمال ← {pct}% 🔥\n"
            f"▽ : التقييم ← {comp}"
        )
        send_with_user_photo(chat_id, user.id, caption, reply_to_message_id=m.message_id)
        return True

    if ntext == "كشف" or ntext.startswith("كشف "):
        t_u = resolve_target_user(m, text) or u_data
        t_rank = get_rank(chat_id, t_u["user_id"])
        t_biz = get_user_businesses(t_u["user_id"])
        biz_summary = "، ".join([f"{b['custom_name']} ({b['biz_type']})" for b in t_biz]) if t_biz else "لا يملك متجراً"
        job_lvl_title = JOBS.get(t_u["job"], {}).get("levels", {}).get(t_u["job_level"], {}).get("title", t_u["job"])
        base_def = HOUSES.get(t_u["house"], {"defense": 0})["defense"] + t_u["house_sec_level"]
        bot.reply_to(
            m,
            f"▽ : كشف السجل المدني والممتلكات 🇱🇾\n"
            f"------------------\n"
            f"▽ : المواطن ← <b>{esc(t_u['name'])}</b> (<code>{t_u['user_id']}</code>)\n"
            f"▽ : المدينة ← <b>{esc(t_u['city'])}</b>\n"
            f"▽ : الرتبة ← <b>{RANK_NAMES.get(t_rank, 'عضو')}</b>\n"
            f"▽ : المهنة ← <b>{esc(job_lvl_title)}</b>\n"
            f"▽ : الكاش في الجيب ← <b>{t_u['cash']} د.ل</b> 💵\n"
            f"▽ : الكاش في المنزل ← <b>{t_u['home_cash']} د.ل</b> 🏠\n"
            f"▽ : رصيد المصرف ({esc(t_u['bank_name'])}) ← <b>🔒 سري لا يراه أحد</b>\n"
            f"▽ : العقار ← <b>{esc(t_u['house'])}</b> (حماية: {base_def}%)\n"
            f"▽ : السيارة ← <b>{esc(t_u['car'])}</b> (حالة المحرك: {t_u['car_cond']}%)\n"
            f"▽ : المتاجر والشركات ← <b>{esc(biz_summary)}</b>\n"
            f"▽ : الحالة الجنائية ← <b>{'🚨 مطلوب للعدالة' if t_u['wanted'] else '✅ سجل نظيف'}</b>\n"
            f"------------------"
        )
        return True

    # أوامر التفعيل والرتب والحماية (للإدارة فقط)
    if ntext in ("تفعيل", "رفع نفسي مالك", "ترقيه نفسي", "تفعيل البوت", "ارفعني مالك"):
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
        return True

    if ntext in ("بالتقييد", "بالطرد", "بالكتم") and user_rank >= 2:
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE groups SET punishment = ? WHERE chat_id = ?", (ntext, chat_id))
            conn.commit()
            conn.close()
        bot.reply_to(m, f"▽ : ✅ تم ضبط عقوبة مخالفة الحماية إلى ← {{ <b>{ntext}</b> }}")
        return True

    if ntext.startswith("قفل ") or ntext.startswith("فتح "):
        act = ntext.split()[0]
        t_lock = ntext[len(act):].strip()
        # السماح لأمر قفل/فتح المتجر أو الحساب بالمرور لقسم الاقتصاد لجميع الأعضاء
        if t_lock in ("المتجر", "متجري") or t_lock.startswith(("حساب", "مصرف", "بنك", "متجر", "مشروع")):
            return False
        matched_lock = match_dict_key(LOCK_TYPES, t_lock)
        if matched_lock:
            if user_rank < 2:
                bot.reply_to(m, "▽ : ❌ قفل وفتح الحماية للادمنية فما فوق فقط!")
                return True
            set_group_lock(chat_id, matched_lock, act == "قفل")
            bot.reply_to(m, f"▽ : تم {'قفل 🔒' if act == 'قفل' else 'فتح 🔓'} ← {{ <b>{matched_lock}</b> }} بنجاح!")
            return True

    RANK_CMDS = {
        "رفع مالك": (7, 6, "مالك 👑"), "تنزيل مالك": (7, 0, "عضو 🙍‍♂️"),
        "رفع منشئ اساسي": (6, 5, "منشئ اساسي 🏅"), "تنزيل منشئ اساسي": (6, 0, "عضو 🙍‍♂️"),
        "رفع منشئ": (5, 4, "منشئ 🎖️"), "تنزيل منشئ": (5, 0, "عضو 🙍‍♂️"),
        "رفع مدير": (4, 3, "مدير 💼"), "تنزيل مدير": (4, 0, "عضو 🙍‍♂️"),
        "رفع ادمن": (3, 2, "ادمن 👮‍♂️"), "تنزيل ادمن": (3, 0, "عضو 🙍‍♂️"),
        "رفع مميز": (2, 1, "مميز 🌟"), "تنزيل مميز": (2, 0, "عضو 🙍‍♂️"),
    }
    for r_cmd, (req_r, new_l, r_t) in RANK_CMDS.items():
        if ntext == r_cmd or ntext.startswith(r_cmd + " "):
            if user_rank < req_r:
                bot.reply_to(m, "▽ : ❌ رتبتك لا تسمح لك بهذا الإجراء!")
                return True
            t_u = resolve_target_user(m, text)
            if not t_u:
                bot.reply_to(m, "▽ : 💡 قم بالرد على رسالة العضو أو اكتب يوزره بعد الأمر!")
                return True
            if t_u["user_id"] == ADMIN_ID:
                bot.reply_to(m, "▽ : ⚡ لا يمكن تعديل رتبة المطور الأساسي MG!")
                return True
            set_rank(chat_id, t_u["user_id"], new_l)
            bot.reply_to(m, f"▽ : تم تحديث رتبة <b>{esc(t_u['name'])}</b> إلى ← <b>{r_t}</b>")
            return True

    if ntext in ("تنزيل الكل", "تصفير الرتب") and user_rank >= 6:
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE ranks SET rank_level = 0 WHERE chat_id = ? AND rank_level < 6", (chat_id,))
            conn.commit()
            conn.close()
        bot.reply_to(m, "▽ : ✅ تم تنزيل جميع الرتب الفرعية في المجموعة بنجاح.")
        return True

    RANK_LIST_CMDS = {
        "المالكين": (6, "👑 قائمة المالكين"),
        "المنشئين": (4, "🎖️ قائمة المنشئين"),
        "المدراء": (3, "💼 قائمة المدراء"),
        "الادمنيه": (2, "👮‍♂️ قائمة الادمنية"),
        "المميزين": (1, "🌟 قائمة المميزين"),
    }
    if ntext in RANK_LIST_CMDS:
        lvl, hdr = RANK_LIST_CMDS[ntext]
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
            txt = f"▽ : {hdr} :\n------------------\n"
            for idx, r in enumerate(rows, 1):
                txt += f"{idx}. <b>{esc(r['name'] or 'مواطن')}</b> (<code>{r['user_id']}</code>)\n"
            bot.reply_to(m, txt)
        return True

    if ntext.startswith("ضع لقب ") and m.reply_to_message and user_rank >= 3:
        new_title = text.split(maxsplit=2)[2].strip()
        target = m.reply_to_message.from_user
        set_custom_title(chat_id, target.id, new_title)
        bot.reply_to(m, f"▽ : تم تعيين اللقب « <b>{esc(new_title)}</b> » للعضو بنجاح!")
        return True

    if ntext.startswith("اضف رد ") and "=" in text and user_rank >= 3:
        raw = text.split(maxsplit=2)[2].strip()
        k, v = [x.strip() for x in raw.split("=", 1)]
        if k and v:
            reps = get_group_json(chat_id, "replies", {})
            reps[k] = v
            set_group_json(chat_id, "replies", reps)
            bot.reply_to(m, f"▽ : تم حفظ الرد بنجاح!\n▽ : الكلمة ← « {esc(k)} »\n▽ : الجواب ← « {esc(v)} »")
        return True

    if ntext.startswith("مسح رد ") and user_rank >= 3:
        k = text.split(maxsplit=2)[2].strip()
        reps = get_group_json(chat_id, "replies", {})
        if k in reps:
            del reps[k]
            set_group_json(chat_id, "replies", reps)
            bot.reply_to(m, f"▽ : تم حذف الرد « {esc(k)} » بنجاح.")
        return True

    if ntext == "الردود":
        reps = get_group_json(chat_id, "replies", {})
        if not reps:
            bot.reply_to(m, "▽ : لا توجد ردود مضافة في المجموعة حالياً.")
        else:
            txt = "▽ : قائمة ردود المجموعة :\n------------------\n"
            for k, v in reps.items():
                txt += f"▽ : <code>{esc(k)}</code> ~ {esc(v)}\n"
            bot.reply_to(m, txt)
        return True

    if ntext == "مسح الردود" and user_rank >= 3:
        set_group_json(chat_id, "replies", {})
        bot.reply_to(m, "▽ : تم مسح جميع ردود المجموعة بنجاح.")
        return True

    if ntext.startswith("اضف اختصار ") and "=" in text and user_rank >= 3:
        raw = text.split(maxsplit=2)[2].strip()
        k, v = [x.strip() for x in raw.split("=", 1)]
        if k and v:
            scs = get_group_json(chat_id, "shortcuts", {})
            scs[k] = v
            set_group_json(chat_id, "shortcuts", scs)
            bot.reply_to(m, f"▽ : تم إضافة الاختصار ← <code>{esc(k)}</code> ~ <code>{esc(v)}</code>")
        return True

    if ntext.startswith("مسح اختصار ") and user_rank >= 3:
        k = text.split(maxsplit=2)[2].strip()
        scs = get_group_json(chat_id, "shortcuts", {})
        if k in scs:
            del scs[k]
            set_group_json(chat_id, "shortcuts", scs)
            bot.reply_to(m, f"▽ : تم مسح الاختصار « {esc(k)} » بنجاح.")
        return True

    if ntext == "الاختصارات":
        scs = get_group_json(chat_id, "shortcuts", {})
        txt = "▽ : الاختصارات المفعلة :\n------------------\n▽ : ا ~ ايدي\n▽ : ص ~ صورتي\n"
        for k, v in scs.items():
            txt += f"▽ : <code>{esc(k)}</code> ~ {esc(v)}\n"
        bot.reply_to(m, txt)
        return True

    if ntext.startswith("ضع ترحيب ") and user_rank >= 3:
        w_t = text.split(maxsplit=2)[2].strip()
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE groups SET welcome_text = ? WHERE chat_id = ?", (w_t, chat_id))
            conn.commit()
            conn.close()
        bot.reply_to(m, "▽ : ✅ تم تحديث رسالة الترحيب للمجموعة بنجاح!")
        return True

    if ntext.startswith("ضع قوانين ") and user_rank >= 3:
        r_t = text.split(maxsplit=2)[2].strip()
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE groups SET rules_text = ? WHERE chat_id = ?", (r_t, chat_id))
            conn.commit()
            conn.close()
        bot.reply_to(m, "▽ : ✅ تم حفظ قوانين المجموعة بنجاح!")
        return True

    if ntext == "القوانين":
        bot.reply_to(m, f"▽ : قوانين المجموعة :\n------------------\n{esc(grp_data.get('rules_text', ''))}")
        return True

    # الكتم والحظر والطرد والإنذار للادمنية فقط
    if ntext in ("حظر", "الغاء حظر", "طرد", "كتم", "الغاء كتم", "انذار", "حذف الانذارات") and m.reply_to_message:
        if user_rank < 2:
            bot.reply_to(m, "▽ : ❌ أوامر الحظر والكتم والطرد مخصصة للادمنية فما فوق فقط!")
            return True
        target = m.reply_to_message.from_user
        if get_rank(chat_id, target.id) >= user_rank and user.id != ADMIN_ID:
            bot.reply_to(m, "▽ : ❌ لا يمكنك تطبيق العقوبة على رتبة مساوية أو أعلى منك!")
            return True
        try:
            if ntext == "حظر":
                bot.ban_chat_member(chat_id, target.id)
                bot.reply_to(m, f"▽ : 🚫 تم حظر <b>{esc(target.first_name)}</b> من المجموعة!")
            elif ntext == "الغاء حظر":
                bot.unban_chat_member(chat_id, target.id)
                bot.reply_to(m, f"▽ : ✅ تم إلغاء حظر <b>{esc(target.first_name)}</b>!")
            elif ntext == "طرد":
                bot.ban_chat_member(chat_id, target.id)
                bot.unban_chat_member(chat_id, target.id)
                bot.reply_to(m, f"▽ : 👞 تم طرد <b>{esc(target.first_name)}</b> من المجموعة!")
            elif ntext == "كتم":
                bot.restrict_chat_member(chat_id, target.id, can_send_messages=False)
                bot.reply_to(m, f"▽ : 🔇 تم كتم <b>{esc(target.first_name)}</b>!")
            elif ntext == "الغاء كتم":
                bot.restrict_chat_member(chat_id, target.id, can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
                bot.reply_to(m, f"▽ : 🔊 تم إلغاء كتم <b>{esc(target.first_name)}</b>!")
            elif ntext == "انذار":
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
            elif ntext == "حذف الانذارات":
                with db_lock:
                    conn = get_db()
                    conn.execute("DELETE FROM warnings WHERE chat_id=? AND user_id=?", (chat_id, target.id))
                    conn.commit()
                    conn.close()
                bot.reply_to(m, f"▽ : ✅ تم مسح جميع إنذارات <b>{esc(target.first_name)}</b>!")
        except Exception:
            bot.reply_to(m, "▽ : ⚠️ تأكد من منح البوت صلاحيات المشرف الكاملة!")
        return True

    if ntext in ("تثبيت", "الغاء تثبيت") and m.reply_to_message and user_rank >= 2:
        try:
            if ntext == "تثبيت":
                bot.pin_chat_message(chat_id, m.reply_to_message.message_id)
                bot.reply_to(m, "▽ : 📌 تم تثبيت الرسالة بنجاح!")
            else:
                bot.unpin_chat_message(chat_id, m.reply_to_message.message_id)
                bot.reply_to(m, "▽ : 📌 تم إلغاء تثبيت الرسالة!")
        except Exception:
            pass
        return True

    if ntext == "اطردني" and user_rank < 2:
        try:
            bot.ban_chat_member(chat_id, user.id)
            bot.unban_chat_member(chat_id, user.id)
        except Exception:
            pass
        return True

    if ntext.startswith("مسح") and not ntext.startswith(("مسح رد", "مسح اختصار")):
        if user_rank < 2:
            bot.reply_to(m, "▽ : ❌ مسح الرسائل مخصص للادمنية فما فوق فقط!")
            return True
        if m.reply_to_message and ntext == "مسح":
            try:
                bot.delete_message(chat_id, m.reply_to_message.message_id)
                bot.delete_message(chat_id, m.message_id)
            except Exception:
                pass
            return True
        parts = ntext.split()
        if len(parts) == 2 and parts[1].isdigit():
            cnt = min(int(parts[1]), 50)
            for mid in range(m.message_id, m.message_id - cnt - 1, -1):
                try:
                    bot.delete_message(chat_id, mid)
                except Exception:
                    pass
            return True

    return False
