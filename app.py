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
# ══════════════════════════════════════════════════════════════════
# 🛍️ تحديث وتوسيع المتاجر والمشاريع (صيدلية، متجر عطور، مواد منزلية، معرض سيارات...)
# ══════════════════════════════════════════════════════════════════

BUSINESS_CATALOG.update({
    "متجر عطور": {
        "price": 85000,
        "product": "زيوت عطرية فاخرة وزجاجات تشتريها الناس",
        "unit_cost": 95,
        "unit_sell": 230,
        "npc_rate": 18
    },
    "متجر مواد منزلية": {
        "price": 110000,
        "product": "أواني ومفروشات ومستلزمات منزلية",
        "unit_cost": 130,
        "unit_sell": 310,
        "npc_rate": 18
    },
    "معرض سيارات": {
        "price": 420000,
        "product": "قطع غيار أصلية وإكسسوارات سيارات",
        "unit_cost": 400,
        "unit_sell": 980,
        "npc_rate": 16
    }
})

# تحديث قائمة م8 لتشمل الصيغ السريعة الجديدة
MENU_TEXTS["menu_8"] = (
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
    "▽ : المتاجر ~ متجري ~ صيدليتي ~ مشروعي\n"
    "▽ : فتح صيدليه + الاسم\n"
    "▽ : فتح متجر عطور + الاسم\n"
    "▽ : فتح متجر مواد منزليه + الاسم\n"
    "▽ : فتح قهوه ~ فتح مطعم ~ فتح سوبرماركت\n"
    "▽ : فتح شركه ~ فتح مستشفى ~ فتح مول\n"
    "▽ : شراء بضاعه + العدد (او شراء ادويه / عطور)\n"
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
)

BIZ_KEYS_LIST = list(BUSINESS_CATALOG.keys())

def build_biz_kb(owner_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    btns = []
    for idx, b_key in enumerate(BIZ_KEYS_LIST):
        pr = BUSINESS_CATALOG[b_key]["price"]
        btns.append(types.InlineKeyboardButton(f"🏢 {b_key} ({pr} د.ل)", callback_data=f"obiz:{owner_id}:{idx}"))
    kb.add(*btns)
    return kb

def parse_open_business(raw_text: str, default_owner_name: str) -> tuple[str | None, str]:
    """
    يفهم جميع صيغ فتح المشاريع باللهجة الليبية والكتابة السريعة:
    مثل: (فتح صيدليه)، (فتح صيدليه الشفاء)، (فتح متجر عطور التوقيع الذهبي)، (فتح متجر مواد منزليه)، (فتح قهوه)، إلخ.
    """
    nt = norm_ar(raw_text)
    for prefix in ("فتح مشروع ", "فتح متجر ", "فتح محل ", "انشاء متجر ", "انشاء مشروع ", "فتح "):
        if nt.startswith(prefix):
            rest_norm = nt[len(prefix):].strip()
            rest_orig = raw_text.strip()[len(prefix):].strip() if len(raw_text.strip()) >= len(prefix) else rest_norm
            break
    else:
        return None, ""

    # إذا كتب علامة = (مثال: صيدليه=الشفاء)
    if "=" in rest_orig:
        t_part, n_part = [x.strip() for x in rest_orig.split("=", 1)]
        t_norm = norm_ar(t_part)
    else:
        t_norm = rest_norm
        n_part = ""

    aliases = [
        ("متجر عطور", ["متجر عطور", "محل عطور", "عطور", "عطر"]),
        ("متجر مواد منزليه", ["متجر مواد منزليه", "محل مواد منزليه", "مواد منزليه", "مواد منزليه", "منزليه"]),
        ("متجر ملابس", ["متجر ملابس", "محل ملابس", "ملابس"]),
        ("صيدليه", ["صيدليه", "صيدلية"]),
        ("قهوه", ["قهوه", "مقهي", "كافيه", "كافي"]),
        ("مطعم", ["مطعم", "مشاوي"]),
        ("سوبرماركت", ["سوبرماركت", "سوبر ماركت", "اسواق", "غذائيه"]),
        ("شركه برمجيات", ["شركه برمجيات", "شركه تقنيه", "شركه", "برمجيات"]),
        ("مستشفي خاص", ["مستشفي خاص", "مستشفي", "مصحه"]),
        ("مول تجاري", ["مول تجاري", "مول", "مركز تسوق"]),
        ("معرض سيارات", ["معرض سيارات", "معرض"]),
    ]

    matched_catalog_key = None
    custom_name = n_part

    for cat_norm, words in aliases:
        for w in words:
            if t_norm == w or t_norm.startswith(w + " "):
                # إيجاد المفتاح الأصلي في BUSINESS_CATALOG
                for orig_k in BUSINESS_CATALOG.keys():
                    if norm_ar(orig_k) == cat_norm:
                        matched_catalog_key = orig_k
                        break
                if not custom_name and len(t_norm) > len(w):
                    custom_name = rest_orig[len(w):].strip(" =-")
                break
        if matched_catalog_key:
            break

    if not matched_catalog_key:
        return None, ""

    if not custom_name:
        custom_name = f"{matched_catalog_key} {default_owner_name}"

    return matched_catalog_key, custom_name


# ══════════════════════════════════════════════════════════════════
# 💰 دالة الاقتصاد، المصارف، المتاجر، السرقات، والألعاب (متاحة لجميع الأعضاء 100%)
# ══════════════════════════════════════════════════════════════════

def handle_economy_and_games_cmds(m: types.Message, text: str, u_data: dict, now: int) -> bool:
    user = m.from_user
    chat_id = m.chat.id
    ntext = norm_ar(text)

    # ─────────────── 0. استكمال فتح مصرف خاص إذا كان ينتظر الاسم ───────────────
    if user.id in pending_bank_creation:
        exp = pending_bank_creation.pop(user.id)
        if now <= exp and len(text) <= 35:
            ntext = f"فتح مصرف خاص {text}"
            text = f"فتح مصرف خاص {text}"

    # ─────────────── 1. نظام الحبس والهروب والكفالة ───────────────
    if ntext == "تهريب" and m.reply_to_message:
        friend = ensure_user(m.reply_to_message.from_user)
        if friend["user_id"] == user.id:
            bot.reply_to(m, "▽ : 😂 ما تقدرش تهرب روحك! اكتب <code>دفع كفاله</code> أو <code>رشوه العساس</code>.")
            return True
        if friend["jail_until"] <= now:
            bot.reply_to(m, f"▽ : المواطن <b>{esc(friend['name'])}</b> حر طليق ومش محبوس!")
            return True
        if random.randint(1, 100) <= 70:
            update_user_field(friend["user_id"], jail_until=0, wanted=0)
            bot.reply_to(
                m,
                f"🚁🔥 <b>عملية تهريب أسطورية ناجحة!</b>\n"
                f"▽ : قام الذئب <b>{esc(u_data['name'])}</b> بتهريب صاحبه <b>{esc(friend['name'])}</b> من الحبس!"
            )
        else:
            fine = min(200, u_data["cash"])
            update_user_field(user.id, cash=u_data["cash"] - fine)
            bot.reply_to(m, f"🚨 فشلت محاولة التهريب! خالفك العساس بمبلغ {fine} د.ل.")
        return True

    if u_data["jail_until"] > now:
        rem_sec = u_data["jail_until"] - now
        rem_min = max(1, (rem_sec + 59) // 60)

        if ntext in ("دفع كفاله", "كفاله", "طلوع كفاله"):
            bail = 500
            if u_data["cash"] >= bail:
                update_user_field(user.id, cash=u_data["cash"] - bail, jail_until=0, wanted=0)
                bot.reply_to(m, f"▽ : ⚖️ دفعت <b>{bail} د.ل</b> كفالة من جيبك وطلعت براءة فوراً!")
            elif u_data["bank_balance"] >= bail:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - bail, jail_until=0, wanted=0)
                bot.reply_to(m, f"▽ : ⚖️ تم خصم <b>{bail} د.ل</b> كفالة من مصرفك وطلعت براءة فوراً!")
            else:
                bot.reply_to(m, f"▽ : ❌ لا تملك {bail} د.ل لدفع الكفالة! خلي صاحبك يرد عليك بكلمة <code>تهريب</code>.")
            return True

        if ntext in ("رشوه العساس", "رشوه"):
            bribe = 300
            if u_data["cash"] < bribe:
                bot.reply_to(m, f"▽ : ❌ تحتاج <b>{bribe} د.ل</b> كاش لرشوة العساس!")
                return True
            if random.randint(1, 100) <= 65:
                update_user_field(user.id, cash=u_data["cash"] - bribe, jail_until=0, wanted=0)
                bot.reply_to(m, "▽ : 🤫 قبل العساس الرشوة وفتحلك الباب الخلفي.. اهرب بسرعة!")
            else:
                update_user_field(user.id, cash=u_data["cash"] - bribe, jail_until=u_data["jail_until"] + 120)
                bot.reply_to(m, "▽ : 🚨 العساس طلع نزيه وصادر الـ 300 د.ل وزادك دقيقتين!")
            return True

        if ntext not in ("حسابي", "فلوسي", "البنك", "رصيدي", "وظيفتي", "مهنتي"):
            bot.reply_to(
                m,
                f"⛓️ <b>أنت موقوف في المركز حالياً!</b>\n"
                f"------------------\n"
                f"▽ : الوقت المتبقي للخروج ← <b>{rem_min} دقيقة</b>\n"
                f"▽ : للخروج فوراً اكتب: <code>دفع كفاله</code> أو <code>رشوه العساس</code> أو خلي صاحبك يرد عليك بـ <code>تهريب</code>"
            )
            return True

    # ─────────────── 2. المصارف، الفروع، تغيير البنك، والمصارف الخاصة ───────────────
    if ntext in (
        "انشاء حساب", "انشاء حساب بنكي", "فتح حساب", "فتح حساب بنكي",
        "حساب جديد", "تغيير البنك", "تغيير المصرف", "المصارف", "بنك"
    ):
        bot.reply_to(
            m,
            "▽ : اختر المصرف الليبي من الأزرار أدناه لفتح حسابك أو نقل حسابك إليه مجاناً (يمكنك السحب والإيداع من جميع الفروع) :",
            reply_markup=build_banks_kb(user.id)
        )
        return True

    if ntext.startswith(("انشاء حساب ", "فتح حساب ", "تغيير البنك ", "تغيير المصرف ")):
        b_match = match_dict_key(OFFICIAL_BANKS, text)
        if b_match:
            def_br = OFFICIAL_BANKS[b_match]["branches"][0]
            update_user_field(user.id, bank_name=b_match, bank_branch=def_br)
            bot.reply_to(
                m,
                f"▽ : 🏦 تم فتح/نقل حسابك إلى <b>{esc(b_match)}</b> ({esc(def_br)}) بنجاح!\n"
                f"▽ : اكتب <code>الفروع</code> إذا أردت تغيير الفرع، أو اكتب <code>شغل</code> لكسب المال.",
                reply_markup=build_bank_secret_kb(user.id)
            )
            return True

    if ntext in ("الفروع", "فروع المصرف", "تغيير الفرع"):
        if u_data["bank_name"] == "بدون مصرف":
            bot.reply_to(m, "▽ : ❌ افتح حساباً أولاً بكتابة <code>انشاء حساب</code>!", reply_markup=build_banks_kb(user.id))
            return True
        b_idx = OFFICIAL_BANKS.get(u_data["bank_name"], {}).get("idx", 0)
        bot.reply_to(
            m,
            f"▽ : فروع ({esc(u_data['bank_name'])}) المتاحة للسحب والإيداع الفوري :",
            reply_markup=build_branches_kb(user.id, b_idx)
        )
        return True

    if ntext in ("حسابي", "فلوسي", "البنك", "رصيدي", "اموالي"):
        bot.reply_to(
            m,
            f"▽ : البطاقة المصرفية الذكية 🇱🇾\n"
            f"------------------\n"
            f"▽ : العميل ← <b>{esc(u_data['name'])}</b>\n"
            f"▽ : المدينة ← <b>{esc(u_data['city'])}</b>\n"
            f"▽ : المصرف ← <b>{esc(u_data['bank_name'])}</b>\n"
            f"▽ : الفرع ← <b>{esc(u_data['bank_branch'])}</b>\n"
            f"▽ : الكاش في الجيب (ظاهر) ← <b>{u_data['cash']} د.ل</b> 💵\n"
            f"▽ : الكاش في المنزل (ظاهر) ← <b>{u_data['home_cash']} د.ل</b> 🏠\n"
            f"▽ : رصيد المصرف ← <b>🔒 مشفر (خاص بالعميل)</b>\n"
            f"------------------\n"
            f"▽ : اضغط الزر أدناه لكشف رصيدك المصرفي السري (لن يراه أحد غيرك) :",
            reply_markup=build_bank_secret_kb(user.id)
        )
        return True

    if ntext.startswith(("ايداع ", "حط فلوس ")) and not ntext.startswith("ايداع بالبيت"):
        if u_data["bank_name"] == "بدون مصرف":
            bot.reply_to(m, "▽ : ❌ افتح حساباً أولاً بكتابة <code>انشاء حساب</code>!", reply_markup=build_banks_kb(user.id))
            return True
        arg = ntext.split()[-1]
        amt = u_data["cash"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt <= 0 or amt > u_data["cash"]:
            bot.reply_to(m, "▽ : ❌ المبلغ غير صحيح أو الكاش في جيبك لا يكفي!")
            return True
        fee_pct = OFFICIAL_BANKS.get(u_data["bank_name"], {}).get("fee", 1.5)
        with db_lock:
            conn = get_db()
            cb = conn.execute("SELECT * FROM custom_banks WHERE bank_name = ?", (u_data["bank_name"],)).fetchone()
            if cb:
                fee_pct = cb["fee_pct"]
            conn.close()
        fee = max(1, int(amt * (fee_pct / 100.0)))
        net_amt = amt - fee
        update_user_field(user.id, cash=u_data["cash"] - amt, bank_balance=u_data["bank_balance"] + net_amt)
        if cb:
            with db_lock:
                conn = get_db()
                conn.execute("UPDATE custom_banks SET vault = vault + ? WHERE id = ?", (fee, cb["id"]))
                conn.commit()
                conn.close()
        bot.reply_to(
            m,
            f"▽ : ✅ تم إيداع <b>{net_amt} د.ل</b> عبر ({esc(u_data['bank_branch'])})!\n"
            f"▽ : عمولة المصرف ({fee_pct}%) ← <b>{fee} د.ل</b>\n"
            f"▽ : الكاش المتبقي في جيبك ← <b>{u_data['cash'] - amt} د.ل</b>\n"
            f"▽ : رصيد المصرف ← <b>🔒 محفوظ سرياً</b>",
            reply_markup=build_bank_secret_kb(user.id)
        )
        return True

    if ntext.startswith(("سحب ", "طلع فلوس ")) and not ntext.startswith(("سحب من البيت", "سحب ارباح", "سحب سياره", "سحب عقار", "سحب متجر", "سحب مصرف")):
        if u_data["bank_name"] == "بدون مصرف":
            bot.reply_to(m, "▽ : ❌ افتح حساباً أولاً بكتابة <code>انشاء حساب</code>!", reply_markup=build_banks_kb(user.id))
            return True
        arg = ntext.split()[-1]
        amt = u_data["bank_balance"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt <= 0 or amt > u_data["bank_balance"]:
            bot.reply_to(m, "▽ : ❌ رصيدك في المصرف لا يكفي لإتمام السحب!")
            return True
        new_cash = u_data["cash"] + amt
        new_bank = u_data["bank_balance"] - amt
        update_user_field(user.id, cash=new_cash, bank_balance=new_bank)
        bot.reply_to(
            m,
            f"▽ : 💵 تم سحب <b>{amt} د.ل</b> من فرع ({esc(u_data['bank_branch'])}) إلى جيبك!\n"
            f"▽ : الكاش الحالي في جيبك ← <b>{new_cash} د.ل</b> (احذر من الحرامية!)",
            reply_markup=build_bank_secret_kb(user.id)
        )
        return True

    if ntext.startswith("تحويل ") and m.reply_to_message:
        parts = ntext.split()
        if len(parts) == 2 and parts[1].isdigit():
            amt = int(parts[1])
            target = ensure_user(m.reply_to_message.from_user)
            if target["user_id"] == user.id or amt <= 0:
                return True
            if u_data["bank_balance"] < amt:
                bot.reply_to(m, "▽ : ❌ رصيدك في المصرف لا يكفي للتحويل!")
                return True
            fee = max(1, int(amt * 0.01))
            net = amt - fee
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - amt)
            update_user_field(target["user_id"], bank_balance=target["bank_balance"] + net)
            bot.reply_to(
                m,
                f"▽ : 💸 تمت الحوالة المصرفية بنجاح!\n"
                f"▽ : من ← <b>{esc(u_data['name'])}</b>\n"
                f"▽ : إلى ← <b>{esc(target['name'])}</b>\n"
                f"▽ : الصافي المحول ← <b>{net} د.ل</b> (العمولة: {fee} د.ل)"
            )
        return True

    if ntext.startswith("قرض"):
        parts = ntext.split()
        amt = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 5000
        amt = min(amt, 15000)
        if u_data["loan"] > 0:
            bot.reply_to(m, f"▽ : ❌ عليك قرض سابق بقيمة {u_data['loan']} د.ل! سدده أولاً بكتابة <code>تسديد القرض</code>.")
            return True
        update_user_field(user.id, bank_balance=u_data["bank_balance"] + amt, loan=amt)
        bot.reply_to(m, f"▽ : 🏦 تم منحك قرضاً مصرفياً بقيمة <b>{amt} د.ل</b> وإضافته لرصيدك السري!")
        return True

    if ntext in ("تسديد القرض", "سداد القرض"):
        if u_data["loan"] <= 0:
            bot.reply_to(m, "▽ : ليس عليك أي قروض مصرفية حالياً!")
            return True
        if u_data["bank_balance"] >= u_data["loan"]:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - u_data["loan"], loan=0)
            bot.reply_to(m, "▽ : ✅ تم تسديد القرض بالكامل من رصيدك المصرفي!")
        elif u_data["cash"] >= u_data["loan"]:
            update_user_field(user.id, cash=u_data["cash"] - u_data["loan"], loan=0)
            bot.reply_to(m, "▽ : ✅ تم تسديد القرض بالكامل من كاش جيبك!")
        else:
            bot.reply_to(m, f"▽ : ❌ لا تملك قيمة القرض ({u_data['loan']} د.ل) لتسديده!")
        return True

    # فتح مصرف خاص لجميع الأعضاء (سواء كتب الاسم معه أو كتبه وحده!)
    if ntext in ("فتح مصرف خاص", "فتح بنك خاص", "انشاء مصرف خاص", "تاسيس مصرف"):
        pending_bank_creation[user.id] = now + 180
        bot.reply_to(
            m,
            "▽ : 🏦 <b>تأسيس مصرف تجاري خاص :</b>\n"
            "------------------\n"
            "▽ : تكلفة التأسيس والترخيص ← <b>500,000 د.ل</b>\n"
            "▽ : أرسل الآن <b>اسم المصرف الجديد</b> في رسالتك القادمة (أو اكتب: <code>فتح مصرف خاص مصرف النور</code>)!"
        )
        return True

    if ntext.startswith(("فتح مصرف خاص ", "فتح بنك خاص ", "انشاء مصرف خاص ")):
        b_custom = text.split(maxsplit=3)[-1].strip(" =")
        cost = 500000
        if u_data["bank_balance"] < cost and u_data["cash"] < cost:
            bot.reply_to(
                m,
                f"▽ : ❌ تأسيس مصرف خاص باسم « <b>{esc(b_custom)}</b> » يتطلب رأس مال قدره <b>{cost} د.ل</b>!\n"
                f"▽ : رصيدك الحالي لا يكفي، اجمع المال من المتاجر والوظائف أولاً."
            )
            return True
        with db_lock:
            conn = get_db()
            ex = conn.execute("SELECT * FROM custom_banks WHERE bank_name = ?", (b_custom,)).fetchone()
            if ex:
                conn.close()
                bot.reply_to(m, "▽ : ❌ هذا الاسم مستخدم لمصرف آخر!")
                return True
            conn.execute(
                "INSERT INTO custom_banks (owner_id, owner_name, bank_name, fee_pct, security, vault) VALUES (?,?,?,1.5,65,150000)",
                (user.id, u_data["name"], b_custom)
            )
            conn.commit()
            conn.close()
        if u_data["bank_balance"] >= cost:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost, bank_name=b_custom)
        else:
            update_user_field(user.id, cash=u_data["cash"] - cost, bank_name=b_custom)
        bot.reply_to(
            m,
            f"🏦👑 <b>حدث اقتصادي ضخم في ليبيا!</b>\n"
            f"------------------\n"
            f"▽ : قام رجل الأعمال <b>{esc(u_data['name'])}</b> بتأسيس مصرف خاص باسم:\n"
            f"▽ : « <b>{esc(b_custom)}</b> »\n"
            f"▽ : يمكن لجميع المواطنين الآن فتح حسابات فيه، وستذهب عمولات الإيداع لخزينة المصرف!"
        )
        return True

    if ntext in ("مصرفي", "بنكي الخاص"):
        with db_lock:
            conn = get_db()
            cb = conn.execute("SELECT * FROM custom_banks WHERE owner_id = ?", (user.id,)).fetchone()
            conn.close()
        if not cb:
            bot.reply_to(m, "▽ : ❌ أنت لا تملك مصرفاً خاصاً حالياً! لتأسيس مصرف اكتب: <code>فتح مصرف خاص</code>.")
            return True
        bot.reply_to(
            m,
            f"▽ : 🏦 <b>إدارة مصرفك الخاص « {esc(cb['bank_name'])} » :</b>\n"
            f"------------------\n"
            f"▽ : المالك ← <b>{esc(u_data['name'])}</b>\n"
            f"▽ : الخزينة والاحتياطي ← <b>{cb['vault']} د.ل</b>\n"
            f"▽ : نسبة العمولة ← <b>{cb['fee_pct']}%</b> | قوة الحماية ← <b>{cb['security']}%</b>\n"
            f"------------------\n"
            f"▽ : لسحب الأرباح الزائدة عن الاحتياطي اكتب: <code>سحب ارباح المصرف</code>"
        )
        return True

    if ntext == "سحب ارباح المصرف":
        with db_lock:
            conn = get_db()
            cb = conn.execute("SELECT * FROM custom_banks WHERE owner_id = ?", (user.id,)).fetchone()
            if not cb:
                conn.close()
                bot.reply_to(m, "▽ : ❌ أنت لا تملك مصرفاً خاصاً!")
                return True
            if cb["vault"] <= 100000:
                conn.close()
                bot.reply_to(m, f"▽ : خزينة مصرفك ({esc(cb['bank_name'])}) فيها الاحتياطي الإجباري فقط ({cb['vault']} د.ل).")
                return True
            prof = cb["vault"] - 100000
            conn.execute("UPDATE custom_banks SET vault = 100000 WHERE id = ?", (cb["id"],))
            conn.commit()
            conn.close()
        update_user_field(user.id, bank_balance=u_data["bank_balance"] + prof)
        bot.reply_to(m, f"▽ : 🏦 تم سحب أرباح عمولات مصرفك (<b>{prof} د.ل</b>) وإيداعها في حسابك السري!")
        return True

    # ─────────────── 3. المدن والسفر، الوظائف (`وظيفتي` و `ترقيه`) ───────────────
    if ntext in ("المدن", "اختيار مدينتي", "تغيير مدينتي", "مدينتي"):
        txt = (
            f"▽ : <b>نظام المدن والسفر في ليبيا 🇱🇾</b>\n"
            f"▽ : مدينتك الحالية ← <b>{esc(u_data['city'])}</b>\n"
            f"------------------\n"
        )
        for cn, ci in CITIES.items():
            txt += f"▽ : <b>{cn}</b> ~ التذكرة: {ci['ticket']} د.ل ({ci['desc']})\n"
        txt += "------------------\n▽ : اختر مدينتك من الأزرار أو اكتب: <code>سفر بنغازي</code>"
        bot.reply_to(m, txt, reply_markup=build_city_kb(user.id))
        return True

    if ntext.startswith("سفر "):
        dest_q = text.split(maxsplit=1)[1].strip()
        dest = match_dict_key(CITIES, dest_q)
        if dest:
            if dest == u_data["city"]:
                bot.reply_to(m, f"▽ : أنت متواجد حالياً في مدينة <b>{dest}</b>!")
                return True
            t_cost = CITIES[dest]["ticket"]
            if u_data["cash"] < t_cost:
                bot.reply_to(m, f"▽ : ❌ تحتاج {t_cost} د.ل كاش في جيبك لشراء تذكرة السفر إلى {dest}!")
                return True
            update_user_field(user.id, city=dest, cash=u_data["cash"] - t_cost)
            bot.reply_to(
                m,
                f"▽ : ✈️ رحلة سعيدة! سافرت من <b>{u_data['city']}</b> ووصلت الآن إلى مدينة <b>{dest}</b>.\n"
                f"▽ : تم خصم سعر التذكرة (<b>{t_cost} د.ل</b>)."
            )
        return True

    if ntext in ("الوظائف", "المهن", "تعيين وظيفه"):
        txt = "▽ : ديوان الوظائف الحكومية والخاصة (نظام المراحل والترقيات) :\n------------------\n"
        for j_name, j_info in JOBS.items():
            l1 = j_info["levels"][1]["salary"]
            l4 = j_info["levels"][4]["salary"]
            txt += f"▽ : <b>{j_name}</b> ~ الراتب يبدأ من {l1} إلى {l4} د.ل\n  └ <i>{j_info['desc']}</i>\n"
        txt += "------------------\n▽ : اختر وظيفتك بالضغط على الأزرار أدناه أو اكتب: <code>وظيفه مبرمج</code>"
        bot.reply_to(m, txt, reply_markup=build_jobs_kb(user.id))
        return True

    # أمر وظيفتي / مهنتي (يعرض تفاصيل وظيفة العضو ومستواه وخبرته)
    if ntext in ("وظيفتي", "مهنتي", "شغلي"):
        if u_data["job"] == "عاطل" or u_data["job"] not in JOBS:
            bot.reply_to(
                m,
                "▽ : ❌ أنت حالياً <b>عاطل عن العمل</b>!\n▽ : اختر وظيفتك الآن من الأزرار أدناه لتبدأ بكسب المال :",
                reply_markup=build_jobs_kb(user.id)
            )
            return True
        j_name = u_data["job"]
        cur_lvl = u_data["job_level"]
        lvl_info = JOBS[j_name]["levels"].get(cur_lvl, JOBS[j_name]["levels"][1])
        nxt_txt = "وصلت لأعلى درجة 👑"
        if cur_lvl < 4:
            nxt = JOBS[j_name]["levels"][cur_lvl + 1]
            nxt_txt = f"{nxt['title']} (تحتاج {nxt['req_xp']} XP)"
        bot.reply_to(
            m,
            f"▽ : 💼 <b>بطاقة العمل الوظيفية :</b>\n"
            f"------------------\n"
            f"▽ : الموظف ← <b>{esc(u_data['name'])}</b>\n"
            f"▽ : المهنة ← <b>{esc(j_name)}</b>\n"
            f"▽ : الدرجة الحالية ← <b>{esc(lvl_info['title'])}</b> (المرحلة {cur_lvl}/4)\n"
            f"▽ : الراتب اليومي ← <b>{lvl_info['salary']} د.ل</b>\n"
            f"▽ : نقاط الخبرة ← <b>{u_data['job_xp']} XP</b>\n"
            f"▽ : الترقية القادمة ← <b>{esc(nxt_txt)}</b>\n"
            f"------------------\n"
            f"▽ : اكتب <code>شغل</code> لاستلام الراتب وزيادة الخبرة، أو <code>ترقيه</code> للترقية!"
        )
        return True

    if ntext.startswith(("وظيفه ", "مهنه ", "تعيين ")):
        j_q = text.split(maxsplit=1)[1].strip()
        j_c = match_dict_key(JOBS, j_q)
        if j_c:
            update_user_field(user.id, job=j_c, job_level=1, job_xp=0)
            lvl_info = JOBS[j_c]["levels"][1]
            bot.reply_to(
                m,
                f"▽ : 🎉 تم تعيينك رسمياً في مهنة <b>{j_c}</b>!\n"
                f"▽ : الدرجة الأولى ← <b>{lvl_info['title']}</b> (اليومية: {lvl_info['salary']} د.ل)\n"
                f"▽ : اكتب <code>شغل</code> أو <code>راتب</code> لاستلام يوميتك وتجميع نقاط الخبرة للترقية!"
            )
            return True

    if ntext in ("شغل", "عمل", "راتب", "خدمه", "يوميه", "بخشيش"):
        if u_data["job"] == "عاطل" or u_data["job"] not in JOBS:
            bot.reply_to(
                m,
                "▽ : ❌ أنت عاطل عن العمل! اختر وظيفتك من الأزرار أدناه أولاً :",
                reply_markup=build_jobs_kb(user.id)
            )
            return True
        if now - u_data["last_salary"] < 480:
            rem = (480 - (now - u_data["last_salary"])) // 60 + 1
            bot.reply_to(m, f"▽ : ⏳ انتهت ورديتك الحالية! ارتح لمدة <b>{rem} دقيقة</b> ثم ارجع للشغل.")
            return True

        j_name = u_data["job"]
        cur_lvl = u_data["job_level"]
        new_xp = u_data["job_xp"] + 2
        lvl_data = JOBS[j_name]["levels"].get(cur_lvl, JOBS[j_name]["levels"][1])
        sal = lvl_data["salary"]

        promo_msg = ""
        if cur_lvl < 4:
            next_lvl_req = JOBS[j_name]["levels"][cur_lvl + 1]["req_xp"]
            if new_xp >= next_lvl_req:
                cur_lvl += 1
                new_title = JOBS[j_name]["levels"][cur_lvl]["title"]
                new_sal = JOBS[j_name]["levels"][cur_lvl]["salary"]
                promo_msg = f"\n🎖️ <b>ترقية مهنية مستحقة!</b> تمت ترقيتك إلى درجة (<b>{new_title}</b>) وارتفع راتبك إلى <b>{new_sal} د.ل</b>!"

        update_user_field(
            user.id,
            cash=u_data["cash"] + sal,
            job_level=cur_lvl,
            job_xp=new_xp,
            last_salary=now
        )
        bot.reply_to(
            m,
            f"▽ : 💼 أتممت عملك اليومي في مدينة <b>{esc(u_data['city'])}</b> بنجاح!\n"
            f"------------------\n"
            f"▽ : المسمى الوظيفي ← <b>{esc(lvl_data['title'])}</b> (المرحلة {cur_lvl}/4)\n"
            f"▽ : اليومية المستلمة ← <b>{sal} د.ل</b> كاش في جيبك 💵\n"
            f"▽ : خبرة المهنة ← <b>{new_xp} XP</b>{promo_msg}\n"
            f"------------------\n"
            f"▽ : 💡 نصيحة: اودع فلوسك في المصرف (<code>ايداع الكل</code>) أو في خزنة بيتك!"
        )
        return True

    # أمر ترقيه / ترقية (يعمل بالهاء والتاء المربوطة، ويرقي بالخبرة أو بدورة تدريبية!)
    if ntext in ("ترقيه", "ترقيتي", "ترقيه وظيفيه"):
        if u_data["job"] not in JOBS:
            bot.reply_to(m, "▽ : ❌ لست موظفاً حالياً! اختر وظيفتك أولاً:", reply_markup=build_jobs_kb(user.id))
            return True
        cur_lvl = u_data["job_level"]
        if cur_lvl >= 4:
            bot.reply_to(m, "▽ : 👑 وصلت إلى أعلى مرحلة وظيفية في مهنتك!")
            return True
        nxt = JOBS[u_data["job"]]["levels"][cur_lvl + 1]
        req_xp = nxt["req_xp"]
        if u_data["job_xp"] >= req_xp:
            update_user_field(user.id, job_level=cur_lvl + 1)
            bot.reply_to(
                m,
                f"🎖️🎉 <b>مبروك الترقية الوظيفية!</b>\n"
                f"▽ : تمت ترقيتك إلى ← <b>{esc(nxt['title'])}</b> (المرحلة {cur_lvl+1}/4)\n"
                f"▽ : راتبك الجديد ← <b>{nxt['salary']} د.ل</b>!"
            )
            return True
        missing_xp = req_xp - u_data["job_xp"]
        course_cost = missing_xp * 400
        bot.reply_to(
            m,
            f"▽ : 📈 <b>سلم الترقيات لمهنة ({u_data['job']}) :</b>\n"
            f"------------------\n"
            f"▽ : درجتك الحالية ← المرحلة {cur_lvl}\n"
            f"▽ : الدرجة القادمة ← <b>{nxt['title']}</b> (الراتب: {nxt['salary']} د.ل)\n"
            f"▽ : الخبرة المطلوبة ← <b>{req_xp} XP</b> (خبرتك الحالية: {u_data['job_xp']} XP)\n"
            f"------------------\n"
            f"▽ : استمر في كتابة <code>شغل</code> لترتقي مجاناً، أو اكتب <code>شراء دوره</code> ({course_cost} د.ل) للترقية الفورية!"
        )
        return True

    if ntext in ("شراء دوره", "دوره تدريبيه"):
        if u_data["job"] not in JOBS or u_data["job_level"] >= 4:
            return True
        cur_lvl = u_data["job_level"]
        nxt = JOBS[u_data["job"]]["levels"][cur_lvl + 1]
        missing_xp = max(1, nxt["req_xp"] - u_data["job_xp"])
        cost = missing_xp * 400
        if u_data["cash"] >= cost:
            update_user_field(user.id, cash=u_data["cash"] - cost, job_level=cur_lvl + 1, job_xp=nxt["req_xp"])
        elif u_data["bank_balance"] >= cost:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost, job_level=cur_lvl + 1, job_xp=nxt["req_xp"])
        else:
            bot.reply_to(m, f"▽ : ❌ تكلفة الدورة التدريبية للترقية الفورية هي <b>{cost} د.ل</b>!")
            return True
        bot.reply_to(
            m,
            f"🎓🎖️ <b>اجتزت الدورة التدريبية بنجاح!</b>\n"
            f"▽ : تمت ترقيتك فوراً إلى درجة ← <b>{esc(nxt['title'])}</b> (الراتب: {nxt['salary']} د.ل)!"
        )
        return True

    if ntext in ("علاج", "بيع دواء") and m.reply_to_message:
        if u_data["job"] not in ("دكتور", "صيدلي"):
            bot.reply_to(m, "▽ : ❌ هذا الأمر مخصص للدكتور أو الصيدلي فقط!")
            return True
        patient = ensure_user(m.reply_to_message.from_user)
        update_user_field(patient["user_id"], hp=100)
        fee = 400 * u_data["job_level"]
        update_user_field(user.id, cash=u_data["cash"] + fee, job_xp=u_data["job_xp"] + 1)
        bot.reply_to(m, f"▽ : 🩺 عالجت <b>{esc(patient['name'])}</b> وحصلت على أتعاب <b>{fee} د.ل</b> كاش!")
        return True

    if ntext == "تصليح" and m.reply_to_message:
        if u_data["job"] != "ميكانيكي":
            bot.reply_to(m, "▽ : ❌ هذا الأمر للميكانيكي فقط!")
            return True
        cli = ensure_user(m.reply_to_message.from_user)
        if cli["car"] == "بدون سيارة":
            bot.reply_to(m, "▽ : 😂 هذا الشخص لا يملك سيارة أصلاً!")
            return True
        fee = 500 * u_data["job_level"]
        update_user_field(cli["user_id"], car_cond=100)
        update_user_field(user.id, cash=u_data["cash"] + fee, job_xp=u_data["job_xp"] + 1)
        bot.reply_to(m, f"▽ : 🔧 قمت بصيانة سيارة <b>{esc(cli['name'])}</b> لـ 100% وكسبت <b>{fee} د.ل</b> كاش!")
        return True

    if ntext == "قبض" and m.reply_to_message:
        if u_data["job"] != "شرطي":
            bot.reply_to(m, "▽ : ❌ هذا الأمر لرجال الشرطة فقط!")
            return True
        crim = ensure_user(m.reply_to_message.from_user)
        if crim["wanted"] == 0:
            bot.reply_to(m, "▽ : ⚖️ هذا المواطن سجله نظيف وغير مطلوب للعدالة!")
            return True
        reward = 1000 * u_data["job_level"]
        update_user_field(crim["user_id"], jail_until=now + 300, wanted=0)
        update_user_field(user.id, cash=u_data["cash"] + reward, job_xp=u_data["job_xp"] + 2)
        bot.reply_to(
            m,
            f"▽ : 🚓 ألقى الشرطي <b>{esc(u_data['name'])}</b> القبض على المطلوب <b>{esc(crim['name'])}</b>!\n"
            f"▽ : المكافأة الأمنية ← <b>{reward} د.ل</b> كاش 🎖️"
        )
        return True

    if ntext == "اختراق صراف":
        if u_data["job"] != "مبرمج":
            bot.reply_to(m, "▽ : ❌ هذا الأمر للمبرمجين فقط!")
            return True
        if now - u_data["last_work"] < 600:
            bot.reply_to(m, "▽ : ⏳ أنظمة الحماية مشددة حالياً، انتظر قليلاً!")
            return True
        chance = 55 + (u_data["job_level"] * 8)
        if random.randint(1, 100) <= chance:
            hack_val = random.randint(1500, 3000) * u_data["job_level"]
            update_user_field(user.id, cash=u_data["cash"] + hack_val, last_work=now, job_xp=u_data["job_xp"] + 2)
            bot.reply_to(m, f"▽ : 💻⚡ اخترقت الصراف الآلي بنجاح وسحبت <b>{hack_val} د.ل</b> كاش!")
        else:
            update_user_field(user.id, jail_until=now + 240, last_work=now)
            bot.reply_to(m, "▽ : 🚨 كشفك النظام الأمني وتم توقيفك لمدة 4 دقائق!")
        return True

    if ntext == "حمايه حساب":
        if u_data["job"] != "مبرمج":
            bot.reply_to(m, "▽ : ❌ هذا الأمر للمبرمجين فقط!")
            return True
        update_user_field(user.id, firewall_until=now + 3600)
        bot.reply_to(m, "▽ : 🛡️ قمت بتفعيل جدار ناري لحماية جيبك وحسابك لمدة ساعة كاملة!")
        return True

    # ─────────────── 4. السيارات الحقيقية، السباق، العقارات، وخزنة وحماية المنزل ───────────────
    if ntext in ("السيارات", "معرض السيارات", "سيارات"):
        txt = "▽ : معرض السيارات العالمية الحقيقية (السيارات محمية ولا تُسرق) :\n------------------\n"
        for cn, ci in CARS.items():
            txt += f"🚗 <b>{cn}</b> ({ci['ar']})\n  └ السعر: {ci['price']} د.ل | السرعة: {ci['speed']} كم/س\n"
        txt += "------------------\n▽ : للشراء اكتب الاسم بالعربي أو الإنجليزي:\n<code>شراء سياره تويوتا كورولا</code> أو <code>شراء سياره مرسيدس</code>\n▽ : للصيانة: <code>صيانه سيارتي</code> | للسباق: <code>سباق</code> بالرد"
        bot.reply_to(m, txt)
        return True

    if ntext.startswith("شراء سياره "):
        cn_query = text.split(maxsplit=2)[2].strip()
        matched_car = find_car_name(cn_query)
        if not matched_car:
            bot.reply_to(m, "▽ : ❌ اسم السيارة غير موجود! اكتب <code>السيارات</code> لرؤية الأسماء.")
            return True
        pr = CARS[matched_car]["price"]
        if u_data["bank_balance"] >= pr:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - pr, car=matched_car, car_cond=100)
            bot.reply_to(m, f"▽ : 🏎️ مبروك! اشتريت السيارة الحقيقية (<b>{matched_car}</b>) بسرعة {CARS[matched_car]['speed']} كم/س من رصيدك المصرفي!")
        elif u_data["cash"] >= pr:
            update_user_field(user.id, cash=u_data["cash"] - pr, car=matched_car, car_cond=100)
            bot.reply_to(m, f"▽ : 🏎️ مبروك! اشتريت السيارة (<b>{matched_car}</b>) بالكاش!")
        else:
            bot.reply_to(m, f"▽ : ❌ ثمن السيارة ({pr} د.ل) غير متوفر لديك!")
        return True

    if ntext in ("صيانه سيارتي", "تصليح سيارتي", "سيارتي"):
        if u_data["car"] not in CARS:
            bot.reply_to(m, "▽ : ❌ لا تملك سيارة حالياً! اكتب <code>السيارات</code>.")
            return True
        m_cost = CARS[u_data["car"]]["maint"]
        if u_data["cash"] < m_cost:
            bot.reply_to(m, f"▽ : ❌ تحتاج {m_cost} د.ل كاش لصيانة سيارتك ({u_data['car']})!")
            return True
        update_user_field(user.id, cash=u_data["cash"] - m_cost, car_cond=100)
        bot.reply_to(m, f"▽ : 🔧 تمت صيانة سيارتك (<b>{u_data['car']}</b>) وعادت كفاءتها إلى 100%!")
        return True

    if ntext == "بيع سياره":
        if u_data["car"] in CARS:
            p = int(CARS[u_data["car"]]["price"] * 0.8)
            old_c = u_data["car"]
            update_user_field(user.id, bank_balance=u_data["bank_balance"] + p, car="بدون سيارة")
            bot.reply_to(m, f"▽ : 🚗 بعت سيارتك (<b>{old_c}</b>) للمعرض وتم إيداع <b>{p} د.ل</b> في مصرفك السري!")
        else:
            bot.reply_to(m, "▽ : ❌ أنت لا تملك سيارة لبيعها!")
        return True

    if ntext == "سباق" and m.reply_to_message:
        opp = ensure_user(m.reply_to_message.from_user)
        if u_data["car"] not in CARS or opp["car"] not in CARS:
            bot.reply_to(m, "▽ : ❌ يجب أن يمتلك الطرفان سيارة حقيقية لخوض السباق!")
            return True
        c1 = CARS[u_data["car"]]
        c2 = CARS[opp["car"]]
        s1 = int(c1["speed"] * (u_data["car_cond"] / 100.0)) + random.randint(1, 35)
        s2 = int(c2["speed"] * (opp["car_cond"] / 100.0)) + random.randint(1, 35)
        prize = 1200
        if s1 >= s2:
            update_user_field(user.id, cash=u_data["cash"] + prize, car_cond=max(30, u_data["car_cond"] - 4))
            bot.reply_to(
                m,
                f"🏁🏎️ <b>سباق سرعة حقيقي!</b>\n"
                f"------------------\n"
                f"▽ : فاز <b>{esc(u_data['name'])}</b> بسيارته (<b>{u_data['car']}</b> - سرعة {c1['speed']} كم/س)\n"
                f"▽ : على <b>{esc(opp['name'])}</b> ({opp['car']})\n"
                f"▽ : الجائزة ← <b>{prize} د.ل</b> كاش!"
            )
        else:
            update_user_field(opp["user_id"], cash=opp["cash"] + prize, car_cond=max(30, opp["car_cond"] - 4))
            bot.reply_to(
                m,
                f"🏁🏎️ <b>سباق سرعة حقيقي!</b>\n"
                f"------------------\n"
                f"▽ : فاز <b>{esc(opp['name'])}</b> بسيارته (<b>{opp['car']}</b> - سرعة {c2['speed']} كم/س)\n"
                f"▽ : على <b>{esc(u_data['name'])}</b> ({u_data['car']})\n"
                f"▽ : الجائزة ← <b>{prize} د.ل</b> كاش!"
            )
        return True

    if ntext in ("العقارات", "البيوت", "بيتي", "عقاري"):
        txt = "▽ : دليل العقارات والشقق والفلل والعمارات الليبية :\n------------------\n"
        for hn, hi in HOUSES.items():
            txt += f"🏠 <b>{hn}</b>\n  └ السعر: {hi['price']} د.ل | حماية أساسية: {hi['defense']}% | سعة الخزنة: {hi['safe_cap']} د.ل\n"
        txt += (
            "------------------\n"
            "▽ : للشراء: <code>شراء عقار شفه سكنيه في السراج</code>\n"
            "▽ : لتقوية الحماية: <code>انظمه الحمايه</code>\n"
            "▽ : لخزنة البيت: <code>ايداع بالبيت المبلغ</code> ~ <code>سحب من البيت المبلغ</code>"
        )
        bot.reply_to(m, txt)
        return True

    if ntext.startswith(("شراء عقار ", "شراء بيت ")):
        hn_q = text.split(maxsplit=2)[2].strip()
        hn = match_dict_key(HOUSES, hn_q)
        if hn:
            pr = HOUSES[hn]["price"]
            if u_data["bank_balance"] >= pr:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - pr, house=hn)
                bot.reply_to(m, f"▽ : 🔑 مبروك العقار الجديد! اشتريت (<b>{hn}</b>) من رصيدك المصرفي.")
            elif u_data["cash"] >= pr:
                update_user_field(user.id, cash=u_data["cash"] - pr, house=hn)
                bot.reply_to(m, f"▽ : 🔑 مبروك العقار الجديد! اشتريت (<b>{hn}</b>) بالكاش.")
            else:
                bot.reply_to(m, f"▽ : ❌ ثمن العقار ({pr} د.ل) غير متوفر لديك!")
        else:
            bot.reply_to(m, "▽ : ❌ اسم العقار غير صحيح! اكتب <code>العقارات</code> لرؤية القائمة.")
        return True

    if ntext in ("بيع بيت", "بيع عقار"):
        if u_data["house"] in HOUSES:
            p = int(HOUSES[u_data["house"]]["price"] * 0.8)
            old_h = u_data["house"]
            update_user_field(user.id, bank_balance=u_data["bank_balance"] + p, house="بدون سكن")
            bot.reply_to(m, f"▽ : 🏠 بعت عقارك (<b>{old_h}</b>) وتم إيداع <b>{p} د.ل</b> في مصرفك السري!")
        else:
            bot.reply_to(m, "▽ : ❌ لا تملك عقاراً لبيعه!")
        return True

    if ntext in ("انظمه الحمايه", "تطوير الحمايه", "خزنه البيت"):
        txt = f"▽ : خزنة وحماية المنزل ({esc(u_data['house'])}) :\n▽ : الكاش المخزن بالبيت ← <b>{u_data['home_cash']} د.ل</b>\n------------------\n"
        for sn, si in SECURITY_SYSTEMS.items():
            txt += f"🛡️ <b>{sn}</b> ~ السعر: {si['price']} د.ل (+{si['boost']}% حماية)\n"
        txt += "------------------\n▽ : للتركيب اكتب: <code>تطوير الحمايه كاميرات مراقبه</code>"
        bot.reply_to(m, txt)
        return True

    if ntext.startswith("تطوير الحمايه "):
        s_q = text.split(maxsplit=2)[2].strip()
        s_name = match_dict_key(SECURITY_SYSTEMS, s_q)
        if s_name:
            cost = SECURITY_SYSTEMS[s_name]["price"]
            boost = SECURITY_SYSTEMS[s_name]["boost"]
            if u_data["cash"] < cost and u_data["bank_balance"] < cost:
                bot.reply_to(m, f"▽ : ❌ تحتاج {cost} د.ل لتركيب ({s_name})!")
                return True
            if u_data["cash"] >= cost:
                update_user_field(user.id, cash=u_data["cash"] - cost, house_sec_level=min(95, u_data["house_sec_level"] + boost))
            else:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost, house_sec_level=min(95, u_data["house_sec_level"] + boost))
            with db_lock:
                conn = get_db()
                conn.execute("UPDATE businesses SET security = MIN(95, security + ?) WHERE owner_id = ?", (boost, user.id))
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : 🛡️ تم تركيب (<b>{s_name}</b>) بنجاح! ارتفعت قوة حماية منزلك ومتجرك بمقدار +{boost}%.")
        return True

    if ntext.startswith("ايداع بالبيت "):
        if u_data["house"] not in HOUSES:
            bot.reply_to(m, "▽ : ❌ يجب أن تشتري عقاراً أولاً لتخزين الكاش في البيت!")
            return True
        arg = ntext.split()[-1]
        amt = u_data["cash"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        cap = HOUSES[u_data["house"]]["safe_cap"]
        if amt <= 0 or amt > u_data["cash"]:
            bot.reply_to(m, "▽ : ❌ المبلغ غير متوفر في جيبك!")
            return True
        if u_data["home_cash"] + amt > cap:
            bot.reply_to(m, f"▽ : ❌ سعة خزنة عقارك القصوى هي {cap} د.ل!")
            return True
        update_user_field(user.id, cash=u_data["cash"] - amt, home_cash=u_data["home_cash"] + amt)
        bot.reply_to(m, f"▽ : 🏠 وضعت <b>{amt} د.ل</b> كاش في خزنة منزلك ({u_data['house']})!")
        return True

    if ntext.startswith("سحب من البيت "):
        arg = ntext.split()[-1]
        amt = u_data["home_cash"] if arg == "الكل" else (int(arg) if arg.isdigit() else 0)
        if amt <= 0 or amt > u_data["home_cash"]:
            bot.reply_to(m, "▽ : ❌ المبلغ غير متوفر في خزنة منزلك!")
            return True
        update_user_field(user.id, cash=u_data["cash"] + amt, home_cash=u_data["home_cash"] - amt)
        bot.reply_to(m, f"▽ : 💵 أخذت <b>{amt} د.ل</b> من خزنة منزلك إلى جيبك!")
        return True

    # ─────────────── 5. المتاجر، الصيدليات، متاجر العطور، المواد المنزلية، المولات، والشركاء ───────────────
    if ntext in ("المتاجر", "المشاريع", "الشركات", "فتح متجر", "فتح مشروع"):
        txt = "▽ : دليل المتاجر والصيدليات والشركات والمولات الخاصة :\n------------------\n"
        for bt, bi in BUSINESS_CATALOG.items():
            txt += (
                f"🏢 <b>{bt}</b> ~ التكلفة: {bi['price']} د.ل\n"
                f"  └ المنتجات: ({bi['product']})\n"
                f"  └ جملة: {bi['unit_cost']} د.ل | بيع للزبائن: {bi['unit_sell']} د.ل\n"
            )
        txt += (
            "------------------\n"
            "▽ : اضغط على الزر أدناه لفتح مشروعك فوراً، أو اكتب مباشرة:\n"
            "• <code>فتح صيدليه الشفاء</code>\n"
            "• <code>فتح متجر عطور التوقيع الذهبي</code>\n"
            "• <code>فتح متجر مواد منزليه</code>\n"
            "• <code>فتح قهوه</code> أو <code>فتح مول</code>"
        )
        bot.reply_to(m, txt, reply_markup=build_biz_kb(user.id))
        return True

    # فتح أي مشروع بكل الصيغ الطبيعية (فتح صيدليه، فتح متجر عطور، فتح متجر مواد منزليه، إلخ)
    if ntext.startswith(("فتح ", "انشاء متجر ", "انشاء مشروع ")) and not ntext.startswith(("فتح المتجر", "فتح حساب", "فتح مصرف", "فتح بنك")):
        b_type, b_name_custom = parse_open_business(text, u_data["name"])
        if b_type:
            cost = BUSINESS_CATALOG[b_type]["price"]
            if u_data["bank_balance"] >= cost:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost)
            elif u_data["cash"] >= cost:
                update_user_field(user.id, cash=u_data["cash"] - cost)
            else:
                bot.reply_to(m, f"▽ : ❌ افتتاح (<b>{b_type}</b>) يتطلب رأس مال قدره <b>{cost} د.ل</b>!")
                return True

            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT INTO businesses (owner_id, owner_name, biz_type, custom_name, city, stock, vault, security, marketing, is_open) VALUES (?,?,?,?,?,20,0,20,1,1)",
                    (user.id, u_data["name"], b_type, b_name_custom, u_data["city"])
                )
                conn.commit()
                conn.close()
            bot.reply_to(
                m,
                f"🏢🎉 <b>افتتاح مشروع جديد في {esc(u_data['city'])}!</b>\n"
                f"------------------\n"
                f"▽ : المالك ← <b>{esc(u_data['name'])}</b>\n"
                f"▽ : النشاط ← <b>{esc(b_type)}</b>\n"
                f"▽ : الاسم ← « <b>{esc(b_name_custom)}</b> »\n"
                f"▽ : مخزون البداية المجاني ← <b>20 وحدة</b>\n"
                f"------------------\n"
                f"▽ : اكتب <code>متجري</code> أو <code>صيدليتي</code> للإدارة، واكتب <code>شراء بضاعه 50</code> لتزويد المخزن!"
            )
            return True

    if ntext in ("متجري", "مشروعي", "شركتي", "صيدليتي", "قهوتي", "مطعمي", "مولي"):
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            bot.reply_to(m, "▽ : ❌ لا تملك أي مشروع حالياً! اختر مشروعك من الأزرار أدناه :", reply_markup=build_biz_kb(user.id))
            return True
        st = my_biz[0]
        cat = BUSINESS_CATALOG.get(st["biz_type"], {})
        with db_lock:
            conn = get_db()
            staff = conn.execute("SELECT * FROM business_staff WHERE biz_id = ?", (st["id"],)).fetchall()
            partners = conn.execute("SELECT * FROM business_partners WHERE biz_id = ?", (st["id"],)).fetchall()
            conn.close()
        staff_txt = "، ".join([f"{s['user_name']} ({s['pay_mode']} {s['pay_val']})" for s in staff]) if staff else "لا يوجد موظفون"
        part_txt = "، ".join([f"{p['user_name']} ({p['share_pct']}%)" for p in partners]) if partners else "لا يوجد شركاء"
        bot.reply_to(
            m,
            f"▽ : لوحة إدارة المشروع التجاري 🏢\n"
            f"------------------\n"
            f"▽ : الاسم ← « <b>{esc(st['custom_name'])}</b> » ({esc(st['biz_type'])})\n"
            f"▽ : المدينة ← <b>{esc(st['city'])}</b> | الحالة ← <b>{'🟢 مفتوح للزبائن' if st['is_open'] else '🔴 مغلق'}</b>\n"
            f"▽ : المخزون ({esc(cat.get('product', ''))}) ← <b>{st['stock']} وحدة متبقية</b> 📦\n"
            f"▽ : إجمالي المبيعات ← <b>{st['total_sales']} عملية بيع</b>\n"
            f"▽ : الكاش في خزينة المشروع ← <b>{st['vault']} د.ل</b> 💰\n"
            f"▽ : قوة الحماية ← <b>{st['security']}%</b> | مستوى التسويق ← <b>{st['marketing']}</b>\n"
            f"▽ : البيع الإلكتروني ← <b>{'✅ مفعل' if st['ecommerce'] else '❌ غير مفعل'}</b>\n"
            f"▽ : الشركاء ← <b>{esc(part_txt)}</b>\n"
            f"▽ : الموظفون ← <b>{esc(staff_txt)}</b>\n"
            f"------------------\n"
            f"▽ : أوامر الإدارة السريعة :\n"
            f"• <code>شراء بضاعه 100</code> (أو <code>شراء ادويه 100</code> / <code>شراء عطور 100</code>)\n"
            f"• <code>سحب ارباح المتجر</code> (توزيع الأرباح لك وللشركاء)\n"
            f"• <code>تسويق متجري</code> | <code>تفعيل بيع الكتروني</code>\n"
            f"• <code>قفل المتجر</code> | <code>فتح المتجر</code>"
        )
        return True

    if ntext.startswith(("شراء بضاعه ", "شراء منتجات ", "شراء ادويه ", "شراء عطور ")):
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            bot.reply_to(m, "▽ : ❌ افتح مشروعاً أولاً! اكتب <code>المتاجر</code>.")
            return True
        parts = ntext.split()
        if len(parts) >= 3 and parts[-1].isdigit():
            qty = int(parts[-1])
            if qty <= 0:
                return True
            st = my_biz[0]
            cat = BUSINESS_CATALOG[st["biz_type"]]
            total_cost = qty * cat["unit_cost"]
            if u_data["cash"] >= total_cost:
                update_user_field(user.id, cash=u_data["cash"] - total_cost)
            elif u_data["bank_balance"] >= total_cost:
                update_user_field(user.id, bank_balance=u_data["bank_balance"] - total_cost)
            else:
                bot.reply_to(m, f"▽ : ❌ شراء {qty} وحدة من ({cat['product']}) يكلف <b>{total_cost} د.ل</b>!")
                return True
            with db_lock:
                conn = get_db()
                conn.execute("UPDATE businesses SET stock = stock + ? WHERE id = ?", (qty, st["id"]))
                conn.commit()
                conn.close()
            bot.reply_to(
                m,
                f"▽ : 📦 تم توريد <b>{qty} وحدة</b> من ({esc(cat['product'])}) إلى « <b>{esc(st['custom_name'])}</b> »!\n"
                f"▽ : التكلفة المدفوعة ← <b>{total_cost} د.ل</b>\n"
                f"▽ : سيقوم الزبائن الوهميون واللاعبون بالشراء منها الآن تلقائياً!"
            )
        return True

    if ntext in ("تسويق متجري", "تسويق مشروعي", "تسويق"):
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            bot.reply_to(m, "▽ : ❌ لا تملك مشروعاً لتسويقه!")
            return True
        st = my_biz[0]
        cost = st["marketing"] * 8000
        if u_data["cash"] < cost and u_data["bank_balance"] < cost:
            bot.reply_to(m, f"▽ : ❌ حملة التسويق والإعلانات تتطلب <b>{cost} د.ل</b>!")
            return True
        if u_data["cash"] >= cost:
            update_user_field(user.id, cash=u_data["cash"] - cost)
        else:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost)
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE businesses SET marketing = marketing + 1 WHERE id = ?", (st["id"],))
            conn.commit()
            conn.close()
        bot.reply_to(m, f"▽ : 📢 نجحت الحملة التسويقية لـ « <b>{esc(st['custom_name'])}</b> » وتضاعف إقبال المشترين!")
        return True

    if ntext in ("تفعيل بيع الكتروني", "بيع الكتروني"):
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            return True
        st = my_biz[0]
        if st["ecommerce"]:
            bot.reply_to(m, "▽ : البيع الإلكتروني مفعل مسبقاً لمشروعك!")
            return True
        cost = 25000
        if u_data["bank_balance"] < cost and u_data["cash"] < cost:
            bot.reply_to(m, f"▽ : ❌ برمجة وتفعيل البيع الإلكتروني والتوصيل تتطلب <b>{cost} د.ل</b>!")
            return True
        if u_data["bank_balance"] >= cost:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost)
        else:
            update_user_field(user.id, cash=u_data["cash"] - cost)
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE businesses SET ecommerce = 1 WHERE id = ?", (st["id"],))
            conn.commit()
            conn.close()
        bot.reply_to(m, f"▽ : 🌐🛒 تم تفعيل منظومة البيع الإلكتروني والتوصيل لـ « <b>{esc(st['custom_name'])}</b> »!")
        return True

    if ntext in ("قفل المتجر", "فتح المتجر", "قفل متجري", "فتح متجري"):
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            return True
        st = my_biz[0]
        new_state = 1 if ntext.startswith("فتح") else 0
        with db_lock:
            conn = get_db()
            conn.execute("UPDATE businesses SET is_open = ? WHERE id = ?", (new_state, st["id"]))
            conn.commit()
            conn.close()
        bot.reply_to(m, f"▽ : تم {'فتح 🟢' if new_state else 'إغلاق 🔴'} « <b>{esc(st['custom_name'])}</b> »!")
        return True

    if ntext in ("سحب ارباح المتجر", "تحصيل ارباح", "سحب ارباحي"):
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            bot.reply_to(m, "▽ : ❌ لا تملك مشروعاً تجارياً!")
            return True
        st = my_biz[0]
        vault = st["vault"]
        if vault <= 0:
            bot.reply_to(m, "▽ : خزينة المشروع فارغة حالياً! تأكد من توفير البضاعة (`شراء بضاعه 50`) وفتح المتجر.")
            return True
        with db_lock:
            conn = get_db()
            partners = conn.execute("SELECT * FROM business_partners WHERE biz_id = ?", (st["id"],)).fetchall()
            conn.execute("UPDATE businesses SET vault = 0 WHERE id = ?", (st["id"],))
            conn.commit()
            conn.close()

        partner_cuts = 0
        for p in partners:
            p_cut = int(vault * (p["share_pct"] / 100.0))
            if p_cut > 0:
                partner_cuts += p_cut
                p_u = get_user_by_id(p["user_id"])
                if p_u:
                    update_user_field(p_u["user_id"], bank_balance=p_u["bank_balance"] + p_cut)

        owner_net = max(0, vault - partner_cuts)
        update_user_field(user.id, cash=u_data["cash"] + owner_net)
        bot.reply_to(
            m,
            f"▽ : 💰 تم تحصيل أرباح مبيعات « <b>{esc(st['custom_name'])}</b> »!\n"
            f"------------------\n"
            f"▽ : إجمالي الخزينة ← <b>{vault} د.ل</b>\n"
            f"▽ : حصة الشركاء المحولة لمصارفهم ← <b>{partner_cuts} د.ل</b>\n"
            f"▽ : صافي حصتك في جيبك ← <b>{owner_net} د.ل</b> كاش!"
        )
        return True

    if ntext.startswith("تعيين موظف") and m.reply_to_message:
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            bot.reply_to(m, "▽ : ❌ يجب أن تملك مشروعاً لتعيين موظفين!")
            return True
        st = my_biz[0]
        emp_u = ensure_user(m.reply_to_message.from_user)
        parts = ntext.split()
        mode = "نسبة"
        val = 10
        if len(parts) >= 4 and parts[2] in ("نسبه", "راتب") and parts[3].isdigit():
            mode = "نسبة" if parts[2] == "نسبه" else "راتب"
            val = int(parts[3])
        elif len(parts) == 3 and parts[2].isdigit():
            val = int(parts[2])
        if mode == "نسبة":
            val = min(40, max(1, val))
        with db_lock:
            conn = get_db()
            conn.execute(
                "INSERT OR REPLACE INTO business_staff (biz_id, user_id, user_name, pay_mode, pay_val) VALUES (?,?,?,?,?)",
                (st["id"], emp_u["user_id"], emp_u["name"], mode, val)
            )
            conn.commit()
            conn.close()
        bot.reply_to(
            m,
            f"▽ : 🤝 تم تعيين <b>{esc(emp_u['name'])}</b> موظفاً في « <b>{esc(st['custom_name'])}</b> »!\n"
            f"▽ : نظام الأجر ← <b>{mode} ({val}{'%' if mode == 'نسبة' else ' د.ل'})</b> من المبيعات تلقائياً."
        )
        return True

    if ntext == "فصل موظف" and m.reply_to_message:
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            return True
        st = my_biz[0]
        emp_u = ensure_user(m.reply_to_message.from_user)
        with db_lock:
            conn = get_db()
            conn.execute("DELETE FROM business_staff WHERE biz_id = ? AND user_id = ?", (st["id"], emp_u["user_id"]))
            conn.commit()
            conn.close()
        bot.reply_to(m, f"▽ : 👞 قام المدير بفصل <b>{esc(emp_u['name'])}</b> من العمل في « <b>{esc(st['custom_name'])}</b> »!")
        return True

    if ntext.startswith(("اضافه شريك", "دخول شريك")) and m.reply_to_message:
        my_biz = get_user_businesses(user.id)
        if not my_biz:
            bot.reply_to(m, "▽ : ❌ يجب أن تملك متجراً أو مولاً لإضافة شريك!")
            return True
        st = my_biz[0]
        part_u = ensure_user(m.reply_to_message.from_user)
        parts = ntext.split()
        pct = int(parts[-1]) if parts[-1].isdigit() else 20
        pct = min(49, max(5, pct))
        with db_lock:
            conn = get_db()
            conn.execute(
                "INSERT OR REPLACE INTO business_partners (biz_id, user_id, user_name, share_pct) VALUES (?,?,?,?)",
                (st["id"], part_u["user_id"], part_u["name"], pct)
            )
            conn.commit()
            conn.close()
        bot.reply_to(
            m,
            f"▽ : 🤝🏢 <b>عقد شراكة رسمي!</b>\n"
            f"▽ : دخل <b>{esc(part_u['name'])}</b> شريكاً بنسبة <b>{pct}%</b> في مشروع « <b>{esc(st['custom_name'])}</b> »!"
        )
        return True

    # ─────────────── 6. السوق السوداء والسرقات الذكية ───────────────
    if ntext in ("السوق السوداء", "سوق سودا", "سوق سوداء"):
        txt = "▽ : 🕶️ <b>السوق السوداء السرية (معدات السطو والتهكير) :</b>\n------------------\n"
        for iname, iinfo in BLACK_MARKET.items():
            txt += f"💣 <b>{iname}</b> ~ السعر: {iinfo['price']} د.ل (+{iinfo['power']}% نجاح)\n  └ <i>{iinfo['desc']}</i>\n"
        txt += "------------------\n▽ : للشراء اكتب: <code>شراء اداه مفك اقفال</code>"
        bot.reply_to(m, txt)
        return True

    if ntext.startswith("شراء اداه "):
        t_q = text.split(maxsplit=2)[2].strip()
        t_name = match_dict_key(BLACK_MARKET, t_q)
        if t_name:
            cost = BLACK_MARKET[t_name]["price"]
            if u_data["cash"] < cost:
                bot.reply_to(m, f"▽ : ❌ السوق السوداء تتعامل بالكاش فقط! تحتاج <b>{cost} د.ل</b> كاش في جيبك.")
                return True
            if t_name == "جواز مزور":
                update_user_field(user.id, cash=u_data["cash"] - cost, wanted=0)
                bot.reply_to(m, "▽ : 🕶️ اشتريت جوازاً مزوراً وتم مسح اسمك من قائمة المطلوبين للشرطة فوراً!")
                return True
            u_tools = json.loads(u_data.get("tools") or "{}")
            u_tools[t_name] = u_tools.get(t_name, 0) + 1
            update_user_field(user.id, cash=u_data["cash"] - cost, tools=json.dumps(u_tools))
            bot.reply_to(m, f"▽ : 🕶️ اشتريت (<b>{t_name}</b>) من السوق السوداء! سيتم استخدامها تلقائياً في عملية السطو القادمة.")
        return True

    def _use_best_tool(u_dict: dict) -> tuple[int, str]:
        u_tools = json.loads(u_dict.get("tools") or "{}")
        best_p = 0
        best_n = "بدون معدات"
        for tn, ti in BLACK_MARKET.items():
            if u_tools.get(tn, 0) > 0 and ti["power"] > best_p:
                best_p = ti["power"]
                best_n = tn
        if best_n != "بدون معدات":
            u_tools[best_n] -= 1
            update_user_field(u_dict["user_id"], tools=json.dumps(u_tools))
        return best_p, best_n

    if ntext in ("سرقه", "سرقه جيبه") and m.reply_to_message:
        vic = ensure_user(m.reply_to_message.from_user)
        if vic["user_id"] == user.id or m.reply_to_message.from_user.is_bot:
            return True
        if vic["firewall_until"] > now:
            bot.reply_to(m, f"▽ : 🛡️ المواطن <b>{esc(vic['name'])}</b> مفعل حماية المبرمج! لا يمكنك سرقته.")
            return True
        if vic["cash"] < 100:
            bot.reply_to(m, f"▽ : 😂 جيب <b>{esc(vic['name'])}</b> فاضي ({vic['cash']} د.ل)! جرب <code>سرقه بيته</code> أو <code>سرقه متجره</code>.")
            return True
        tool_power, _ = _use_best_tool(u_data)
        chance = min(80, 48 + tool_power)
        if random.randint(1, 100) <= chance:
            stolen = max(50, int(vic["cash"] * random.uniform(0.25, 0.45)))
            update_user_field(vic["user_id"], cash=vic["cash"] - stolen)
            update_user_field(user.id, cash=u_data["cash"] + stolen, steal_success=u_data["steal_success"] + 1, wanted=1)
            bot.reply_to(
                m,
                f"🦹‍♂️💨 <b>عملية نشل جيب ناجحة!</b>\n"
                f"▽ : سرق <b>{esc(u_data['name'])}</b> مبلغ <b>{stolen} د.ل</b> كاش من جيب <b>{esc(vic['name'])}</b>!"
            )
        else:
            update_user_field(user.id, jail_until=now + 180)
            bot.reply_to(m, f"🚨🤛 فطنلك <b>{esc(vic['name'])}</b> وسلمك للدورية! تم توقيفك <b>3 دقائق</b>.")
        return True

    if ntext in ("سرقه بيته", "سرقه منزله") and m.reply_to_message:
        vic = ensure_user(m.reply_to_message.from_user)
        if vic["user_id"] == user.id:
            return True
        if vic["home_cash"] < 200:
            bot.reply_to(m, f"▽ : 🏠 خزنة منزل <b>{esc(vic['name'])}</b> فارغة حالياً!")
            return True
        house_def = HOUSES.get(vic["house"], {"defense": 10})["defense"] + vic["house_sec_level"]
        tool_power, tool_name = _use_best_tool(u_data)
        chance = max(15, min(75, 55 + tool_power - (house_def // 2)))
        if random.randint(1, 100) <= chance:
            stolen = int(vic["home_cash"] * random.uniform(0.30, 0.55))
            update_user_field(vic["user_id"], home_cash=vic["home_cash"] - stolen)
            update_user_field(user.id, cash=u_data["cash"] + stolen, steal_success=u_data["steal_success"] + 1, wanted=1)
            bot.reply_to(
                m,
                f"🦹‍♂️🏠 <b>اقتحام منزل ناجح باستخدام ({tool_name})!</b>\n"
                f"▽ : تسلل <b>{esc(u_data['name'])}</b> إلى منزل <b>{esc(vic['name'])}</b> ({vic['house']})\n"
                f"▽ : وسرق من خزنة البيت <b>{stolen} د.ل</b> كاش!"
            )
        else:
            update_user_field(user.id, jail_until=now + 240)
            bot.reply_to(
                m,
                f"🚨🔔 <b>دوت صافرات الإنذار في منزل {esc(vic['name'])} (حماية {house_def}%)!</b>\n"
                f"▽ : فشلت السرقة وتم حبسك لمدة <b>4 دقائق</b>!"
            )
        return True

    if ntext in ("سرقه متجره", "سرقه صيدليته", "سرقه مشروعه") and m.reply_to_message:
        vic = ensure_user(m.reply_to_message.from_user)
        vic_biz = get_user_businesses(vic["user_id"])
        if not vic_biz:
            bot.reply_to(m, f"▽ : ❌ المواطن <b>{esc(vic['name'])}</b> لا يملك متجراً أو صيدلية لسرقتها!")
            return True
        st = vic_biz[0]
        if st["vault"] < 100 and st["stock"] < 3:
            bot.reply_to(m, f"▽ : مشروع « <b>{esc(st['custom_name'])}</b> » خزينته ومخزنه فاضيين!")
            return True
        tool_power, tool_name = _use_best_tool(u_data)
        status_bonus = 15 if st["is_open"] == 0 else -10
        chance = max(15, min(75, 50 + tool_power + status_bonus - (st["security"] // 2)))
        if random.randint(1, 100) <= chance:
            stolen_cash = int(st["vault"] * 0.45)
            stolen_stock = int(st["stock"] * 0.35)
            cat = BUSINESS_CATALOG.get(st["biz_type"], {"unit_cost": 50})
            stock_value = stolen_stock * cat["unit_cost"]
            total_gain = stolen_cash + stock_value
            with db_lock:
                conn = get_db()
                conn.execute(
                    "UPDATE businesses SET vault = vault - ?, stock = stock - ? WHERE id = ?",
                    (stolen_cash, stolen_stock, st["id"])
                )
                conn.commit()
                conn.close()
            update_user_field(user.id, cash=u_data["cash"] + total_gain, steal_success=u_data["steal_success"] + 1, wanted=1)
            bot.reply_to(
                m,
                f"💣🏪 <b>سطو جريء على « {esc(st['custom_name'])} »!</b>\n"
                f"------------------\n"
                f"▽ : المنفذ ← <b>{esc(u_data['name'])}</b> (المعدات: {tool_name})\n"
                f"▽ : حالة المشروع وقت السطو ← <b>{'مغلق 🌙' if st['is_open'] == 0 else 'مفتوح ☀️'}</b>\n"
                f"▽ : الكاش المسروق من الخزينة ← <b>{stolen_cash} د.ل</b>\n"
                f"▽ : البضائع المسروقة ← <b>{stolen_stock} وحدة</b> (بيعت بـ {stock_value} د.ل)!"
            )
        else:
            update_user_field(user.id, jail_until=now + 300)
            bot.reply_to(
                m,
                f"🚓🚨 <b>تصدى حراس وكاميرات « {esc(st['custom_name'])} » للهجوم!</b>\n"
                f"▽ : تم القبض عليك وحبسك لمدة <b>5 دقائق</b>!"
            )
        return True

    if ntext in ("سرقه المصرف", "سرقه البنك") or ntext.startswith(("سرقه مصرف ", "سرقه بنك ")):
        if now - u_data["last_rob"] < 600:
            bot.reply_to(m, "▽ : ⏳ الدوريات محاصرة للمصارف حالياً! انتظر بضع دقائق.")
            return True
        b_q = text.split(maxsplit=2)[2].strip() if len(text.split()) >= 3 else "مصرف الصحارى"
        b_target = match_dict_key(OFFICIAL_BANKS, b_q) or b_q
        sec = OFFICIAL_BANKS.get(b_target, {"security": 75})["security"]
        tool_power, tool_name = _use_best_tool(u_data)
        chance = max(12, min(65, 35 + tool_power - (sec // 3)))
        if random.randint(1, 100) <= chance:
            loot = random.randint(12000, 30000)
            update_user_field(user.id, cash=u_data["cash"] + loot, last_rob=now, wanted=1, steal_success=u_data["steal_success"] + 1)
            bot.reply_to(
                m,
                f"💣🏦 <b>سطو مسلح أسطوري على ({esc(b_target)})!</b>\n"
                f"▽ : استخدمت (<b>{tool_name}</b>) لتجاوز حماية المصرف ({sec}%)\n"
                f"▽ : وهربت بغنيمة كاش قدرها <b>{loot} د.ل</b>! 🔥"
            )
        else:
            update_user_field(user.id, jail_until=now + 360, last_rob=now)
            bot.reply_to(
                m,
                f"🚓🚨 <b>فشل السطو على ({esc(b_target)}) بسبب قوة حمايته ({sec}%)!</b>\n"
                f"▽ : تم توقيفك لمدة <b>6 دقائق</b>."
            )
        return True

    # ─────────────── 7. السوق الحر، البورصة، الزواج، التحشيش، والألعاب ───────────────
    if ntext == "السوق الحر":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM marketplace").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "▽ : 🏪 السوق الحر فارغ حالياً!\n▽ : اعرض سيارتك أو عقارك بكتابة:\n<code>عرض سياره للبيع 40000</code>\n<code>عرض عقار للبيع 60000</code>")
        else:
            txt = "▽ : عروض السوق الحر بين اللاعبين :\n------------------\n"
            for r in rows:
                txt += f"🆔 <b>#{r['id']}</b> | البائع: {esc(r['seller_name'])}\n  └ السلعة: <b>{esc(r['item_name'])}</b> ~ السعر: <b>{r['price']} د.ل</b>\n"
            txt += "------------------\n▽ : للشراء: <code>شراء معروض الرقم</code> | للإلغاء: <code>الغاء عرض الرقم</code>"
            bot.reply_to(m, txt)
        return True

    if ntext.startswith(("عرض بيت للبيع ", "عرض عقار للبيع ")):
        pr = ntext.split()[-1]
        if u_data["house"] == "بدون سكن":
            bot.reply_to(m, "▽ : ❌ لا تملك عقاراً لعرضه للبيع!")
            return True
        if pr.isdigit() and int(pr) > 0:
            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT INTO marketplace (seller_id, seller_name, item_type, item_name, price) VALUES (?,?,?,?,?)",
                    (user.id, u_data["name"], "house", u_data["house"], int(pr))
                )
                conn.commit()
                conn.close()
            old_h = u_data["house"]
            update_user_field(user.id, house="بدون سكن")
            bot.reply_to(m, f"▽ : 🏪 تم عرض عقارك (<b>{old_h}</b>) في السوق الحر بسعر <b>{pr} د.ل</b>!")
        return True

    if ntext.startswith("عرض سياره للبيع "):
        pr = ntext.split()[-1]
        if u_data["car"] == "بدون سيارة":
            bot.reply_to(m, "▽ : ❌ لا تملك سيارة لعرضها للبيع!")
            return True
        if pr.isdigit() and int(pr) > 0:
            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT INTO marketplace (seller_id, seller_name, item_type, item_name, price) VALUES (?,?,?,?,?)",
                    (user.id, u_data["name"], "car", u_data["car"], int(pr))
                )
                conn.commit()
                conn.close()
            old_c = u_data["car"]
            update_user_field(user.id, car="بدون سيارة")
            bot.reply_to(m, f"▽ : 🏪 تم عرض سيارتك (<b>{old_c}</b>) في السوق الحر بسعر <b>{pr} د.ل</b>!")
        return True

    if ntext.startswith("الغاء عرض "):
        parts = ntext.split()
        if len(parts) == 3 and parts[2].isdigit():
            m_id = int(parts[2])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM marketplace WHERE id = ?", (m_id,)).fetchone()
                if not row or row["seller_id"] != user.id:
                    conn.close()
                    bot.reply_to(m, "▽ : ❌ هذا العرض غير موجود أو لا يخصك!")
                    return True
                conn.execute("DELETE FROM marketplace WHERE id = ?", (m_id,))
                conn.commit()
                conn.close()
            if row["item_type"] == "house":
                update_user_field(user.id, house=row["item_name"])
            else:
                update_user_field(user.id, car=row["item_name"])
            bot.reply_to(m, f"▽ : ✅ تم إلغاء العرض واسترجاع (<b>{row['item_name']}</b>)!")
        return True

    if ntext.startswith("شراء معروض "):
        parts = ntext.split()
        if len(parts) == 3 and parts[2].isdigit():
            m_id = int(parts[2])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM marketplace WHERE id = ?", (m_id,)).fetchone()
                if not row:
                    conn.close()
                    bot.reply_to(m, "▽ : ❌ المعروض غير موجود!")
                    return True
                price = row["price"]
                if u_data["bank_balance"] >= price:
                    pay_from = "bank"
                elif u_data["cash"] >= price:
                    pay_from = "cash"
                else:
                    conn.close()
                    bot.reply_to(m, f"▽ : ❌ لا تملك {price} د.ل لشراء هذا المعروض!")
                    return True
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
            bot.reply_to(m, f"▽ : 🎉 اشتريت (<b>{esc(row['item_name'])}</b>) من <b>{esc(row['seller_name'])}</b> بمبلغ <b>{price} د.ل</b>!")
        return True

    if ntext in ("البورصه", "الاسهم", "اسهمي"):
        txt = "▽ : 📈 سوق الأسهم والشركات المساهمة الليبية :\n------------------\n"
        for sn in STOCKS.keys():
            txt += f"▽ : سهم <b>{sn}</b> ~ السعر اللحظي: <b>{get_current_stock_price(sn)} د.ل</b>\n"
        txt += "------------------\n▽ : للشراء: <code>شراء اسهم المدار 10</code> | للبيع: <code>بيع اسهم المدار</code>"
        bot.reply_to(m, txt, reply_markup=build_bank_secret_kb(user.id))
        return True

    if ntext.startswith("شراء اسهم "):
        parts = text.split()
        if len(parts) == 4 and parts[3].isdigit():
            sn = match_dict_key(STOCKS, parts[2])
            qty = int(parts[3])
            if not sn or qty <= 0:
                return True
            cost = get_current_stock_price(sn) * qty
            if u_data["bank_balance"] < cost:
                bot.reply_to(m, f"▽ : ❌ تحتاج {cost} د.ل في مصرفك لشراء هذه الأسهم!")
                return True
            u_stk = json.loads(u_data.get("stocks") or "{}")
            u_stk[sn] = u_stk.get(sn, 0) + qty
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - cost, stocks=json.dumps(u_stk))
            bot.reply_to(m, f"▽ : 📈 اشتريت <b>{qty} سهم</b> في شركة <b>{sn}</b> بمبلغ <b>{cost} د.ل</b>!")
        return True

    if ntext.startswith("بيع اسهم "):
        sn_q = text.split(maxsplit=2)[2].strip()
        sn = match_dict_key(STOCKS, sn_q)
        u_stk = json.loads(u_data.get("stocks") or "{}")
        qty = u_stk.get(sn, 0) if sn else 0
        if qty > 0:
            val = get_current_stock_price(sn) * qty
            u_stk[sn] = 0
            update_user_field(user.id, bank_balance=u_data["bank_balance"] + val, stocks=json.dumps(u_stk))
            bot.reply_to(m, f"▽ : 💰 بعت أسهمك في شركة <b>{sn}</b> وتم إيداع <b>{val} د.ل</b> في رصيدك المصرفي السري!")
        return True

    if ntext.startswith("زواج") and m.reply_to_message:
        partner = ensure_user(m.reply_to_message.from_user)
        if partner["user_id"] == user.id or m.reply_to_message.from_user.is_bot:
            return True
        if u_data["married_to"] != 0 or partner["married_to"] != 0:
            bot.reply_to(m, "▽ : ❌ أحد الطرفين متزوج مسبقاً!")
            return True
        parts = ntext.split()
        dowry = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 2000
        if u_data["cash"] < dowry:
            bot.reply_to(m, f"▽ : ❌ لا تملك قيمة المهر ({dowry} د.ل) كاش في جيبك!")
            return True
        update_user_field(user.id, cash=u_data["cash"] - dowry, married_to=partner["user_id"], dowry=dowry)
        update_user_field(partner["user_id"], cash=partner["cash"] + dowry, married_to=user.id, dowry=dowry)
        bot.reply_to(
            m,
            f"💍🎉 <b>زغروطة ليبية يا بنات! لولولولوليش!</b>\n"
            f"------------------\n"
            f"▽ : تم عقد قران <b>{esc(u_data['name'])}</b> على <b>{esc(partner['name'])}</b>\n"
            f"▽ : المهر المدفوع ← <b>{dowry} د.ل</b> كاش!"
        )
        return True

    if ntext in ("طلاق", "خلع"):
        if u_data["married_to"] == 0:
            bot.reply_to(m, "▽ : أنت أعزب أصلاً!")
            return True
        sp_id = u_data["married_to"]
        update_user_field(user.id, married_to=0, dowry=0)
        update_user_field(sp_id, married_to=0, dowry=0)
        bot.reply_to(m, f"▽ : 💔 تم الـ{ntext} رسمياً في محكمة الأسرة.. كل واحد يمشي في حاله!")
        return True

    if ntext == "زواجي":
        if u_data["married_to"] == 0:
            bot.reply_to(m, "▽ : الحالة الاجتماعية ← أعزب/عزباء 💔")
        else:
            sp = get_user_by_id(u_data["married_to"])
            sp_name = sp["name"] if sp else "شريك الحياة"
            bot.reply_to(m, f"▽ : 💍 متزوج من ← <b>{esc(sp_name)}</b> (المهر: {u_data['dowry']} د.ل)")
        return True

    for f_title in FUN_TITLES:
        nf = norm_ar(f_title)
        if (ntext == f"رفع {nf}" or ntext == f"تنزيل {nf}") and m.reply_to_message:
            t_name = m.reply_to_message.from_user.first_name
            if ntext.startswith("رفع"):
                bot.reply_to(m, f"▽ : 😂 تم رفع <b>{esc(t_name)}</b> إلى لقب (<b>{f_title} القروب</b>)!")
            else:
                bot.reply_to(m, f"▽ : 😂 تم تنزيل <b>{esc(t_name)}</b> من لقب (<b>{f_title} القروب</b>)!")
            return True

    if ntext.startswith("نسبه ") and m.reply_to_message:
        kind = text.split(maxsplit=1)[1].strip()
        t_name = m.reply_to_message.from_user.first_name
        bot.reply_to(m, f"▽ : نسبة <b>{esc(kind)}</b> لـ <b>{esc(t_name)}</b> هي ← <b>{random.randint(1, 100)}%</b> 🔥")
        return True

    if ntext == "شنو رايك بهذا" and m.reply_to_message:
        bot.reply_to(m, f"▽ : رأيي فيه ← {random.choice(OPINIONS_LIST)}")
        return True

    if ntext == "رزله" and m.reply_to_message:
        bot.reply_to(m, f"▽ : {random.choice(ROASTS_LIST)}")
        return True

    if ntext in ("انطي هديه", "اعطي هديه", "هديه") and m.reply_to_message:
        t_name = m.reply_to_message.from_user.first_name
        bot.reply_to(m, f"▽ : أهدى <b>{esc(u_data['name'])}</b> إلى <b>{esc(t_name)}</b> ← {random.choice(GIFTS_LIST)}")
        return True

    if ntext in QUESTIONS_BANK:
        q, ans = random.choice(QUESTIONS_BANK[ntext])
        reward = 400
        active_games[chat_id] = {"answer": ans, "reward": reward}
        bot.reply_to(m, f"🎲 مسابقة ({text}) :\n▽ : {q}\n▽ : الجائزة ← <b>{reward} د.ل</b> لأول إجابة صحيحة!")
        return True

    if ntext == "رياضيات":
        a, b = random.randint(12, 65), random.randint(12, 65)
        active_games[chat_id] = {"answer": str(a + b), "reward": 400}
        bot.reply_to(m, f"🧮 مسابقة الرياضيات :\n▽ : كم ناتج ( <b>{a} + {b}</b> ) ؟\n▽ : الجائزة ← <b>400 د.ل</b>!")
        return True

    if ntext in ("حجره", "ورقه", "مقص"):
        bot_c = random.choice(["حجره", "ورقه", "مقص"])
        if ntext == bot_c:
            bot.reply_to(m, f"▽ : اخترتُ ({bot_c}) وأنت ({ntext}) ← تعادل! 🤝")
        elif (ntext == "حجره" and bot_c == "مقص") or (ntext == "ورقه" and bot_c == "حجره") or (ntext == "مقص" and bot_c == "ورقه"):
            update_user_field(user.id, cash=u_data["cash"] + 200)
            bot.reply_to(m, f"▽ : اخترتُ ({bot_c}) وأنت ({ntext}) ← فزتَ عليّ وربحت <b>200 د.ل</b> كاش! 🎉")
        else:
            bot.reply_to(m, f"▽ : اخترتُ ({bot_c}) وأنت ({ntext}) ← فزتُ عليك! 😎")
        return True

    if ntext == "غنيلي":
        bot.reply_to(m, random.choice(SONGS_LIST))
        return True
    if ntext in ("شعر", "قصيده"):
        bot.reply_to(m, random.choice(POEMS_LIST))
        return True
    if ntext == "نكته":
        bot.reply_to(m, random.choice(JOKES_LIST))
        return True
    if ntext == "اذكار":
        bot.reply_to(m, random.choice(ADHKAR_LIST))
        return True
    if ntext == "لو خيروك":
        bot.reply_to(m, random.choice(LAW_KHAYAROUK_LIST))
        return True
    if ntext == "صراحه":
        bot.reply_to(m, random.choice(SARAHA_QUESTIONS))
        return True

    if ntext.startswith("تحدي ") and m.reply_to_message:
        parts = ntext.split()
        if len(parts) == 2 and parts[1].isdigit():
            bet = int(parts[1])
            opp = ensure_user(m.reply_to_message.from_user)
            if opp["user_id"] == user.id or bet < 100:
                return True
            if u_data["cash"] < bet or opp["cash"] < bet:
                bot.reply_to(m, "▽ : ❌ يجب أن يمتلك الطرفان مبلغ الرهان كاش في الجيب!")
                return True
            duel_id = f"{chat_id}_{now}_{random.randint(10,99)}"
            active_duels[duel_id] = {
                "chat_id": chat_id,
                "p1": user.id, "p1_name": u_data["name"],
                "p2": opp["user_id"], "p2_name": opp["name"],
                "bet": bet
            }
            kb = types.InlineKeyboardMarkup(row_width=2)
            kb.add(
                types.InlineKeyboardButton("⚔️ قبول التحدي", callback_data=f"duel_acc_{duel_id}"),
                types.InlineKeyboardButton("🏳️ انسحاب", callback_data=f"duel_rej_{duel_id}")
            )
            bot.reply_to(
                m,
                f"⚔️🔥 <b>تحدي مباشر!</b>\n▽ : {esc(u_data['name'])} يتحدى {esc(opp['name'])} على مبلغ <b>{bet} د.ل</b>!",
                reply_markup=kb
            )
        return True

    if ntext.startswith(("حظ ", "مضاربه ", "استثمار ")):
        parts = ntext.split()
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
        return True

    if ntext.startswith("اكشط "):
        code = text.split(maxsplit=1)[1].strip().upper()
        with db_lock:
            conn = get_db()
            row = conn.execute("SELECT * FROM scratch_cards WHERE code = ?", (code,)).fetchone()
            if not row or row["claimed_by"] != 0:
                conn.close()
                bot.reply_to(m, "▽ : ❌ كرت اكشطها غير صحيح أو مستخدم!")
                return True
            amt = row["amount"]
            conn.execute("UPDATE scratch_cards SET claimed_by = ? WHERE code = ?", (user.id, code))
            conn.commit()
            conn.close()
        update_user_field(user.id, cash=u_data["cash"] + amt)
        bot.reply_to(m, f"▽ : 🎉 مبروك! كشطت الكرت (<code>{esc(code)}</code>) وربحت <b>{amt} د.ل</b> كاش!")
        return True

    if ntext in ("توب", "توب الفلوس", "توب الاغنياء"):
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT name, cash FROM users ORDER BY cash DESC LIMIT 10").fetchall()
            conn.close()
        txt = "▽ : 🏆 قائمة أصحاب الكاش الظاهر في ليبيا :\n------------------\n"
        for i, r in enumerate(rows, 1):
            txt += f"{i}. <b>{esc(r['name'])}</b> ~ {r['cash']} د.ل كاش 💵\n"
        bot.reply_to(m, txt)
        return True

    if ntext == "توب الحراميه":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT name, steal_success FROM users ORDER BY steal_success DESC LIMIT 10").fetchall()
            conn.close()
        txt = "▽ : 🦹‍♂️ أخطر اللصوص في ليبيا :\n------------------\n"
        for i, r in enumerate(rows, 1):
            txt += f"{i}. <b>{esc(r['name'])}</b> ~ {r['steal_success']} عملية ناجحة\n"
        bot.reply_to(m, txt)
        return True

    if ntext == "توب التفاعل":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT name, points, level FROM users ORDER BY points DESC LIMIT 10").fetchall()
            conn.close()
        txt = "▽ : ⭐ أساطير التفاعل في البوت :\n------------------\n"
        for i, r in enumerate(rows, 1):
            txt += f"{i}. <b>{esc(r['name'])}</b> ~ المستوى {r['level']} ({r['points']} نقطة)\n"
        bot.reply_to(m, txt)
        return True

    return False
# ══════════════════════════════════════════════════════════════════
# 🚀 الموجه الرئيسي للرسائل النصية (في الخاص والمجموعات)
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
    ntext = norm_ar(text)
    chat_id = m.chat.id
    is_group = m.chat.type in ("group", "supergroup")
    b_name = get_bot_name()
    b_name_norm = norm_ar(b_name)

    u_data = ensure_user(user)
    now = int(time.time())

    # ─────────────── 1. المحادثة الخاصة ───────────────
    if not is_group:
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
                        f"▽ : من ← {esc(u_data['name'])} (<code>{user.id}</code>)\n"
                        f"▽ : إلى ← {esc(w_info['target_name'])} (<code>{w_info['target_id']}</code>)\n"
                        f"▽ : النص ← <code>{esc(text)}</code>"
                    )
                except Exception:
                    pass

            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("• عرض الهمسة •", callback_data=f"whisper_{w_id}"))
            group_msg_text = (
                f"هذه همسة سرية لك ← <a href='tg://user?id={w_info['target_id']}'>{esc(w_info['target_name'])}</a>\n"
                f"الهمسة من ← <a href='tg://user?id={user.id}'>{esc(u_data['name'])}</a>"
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

        if user.id == ADMIN_ID:
            if _handle_dev_commands(m, text, u_data):
                return

        if handle_economy_and_games_cmds(m, text, u_data, now):
            return

        caption = (
            f"▽ : أهلا بك في بوت {esc(b_name)} 🇱🇾\n"
            f"------------------\n"
            f"▽ : مدينتك الحالية ← {{ {esc(u_data['city'])} }}\n"
            f"▽ : مصرفك الحالي ← {{ {esc(u_data['bank_name'])} }}\n"
            f"▽ : فرع المصرف ← {{ {esc(u_data['bank_branch'])} }}\n"
            f"------------------\n"
            f"▽ : اضف البوت وارفعه مشرف في مجموعتك\n"
            f"▽ : ارسل {{ تفعيل }} ليتم تفعيل المجموعه"
        )
        send_with_user_photo(
            chat_id,
            user.id,
            caption,
            reply_to_message_id=m.message_id,
            reply_markup=get_private_start_kb(user.id)
        )
        return

    # ─────────────── 2. المجموعات ───────────────
    grp_data = ensure_group(m.chat)
    user_rank = get_rank(chat_id, user.id)
    locks = get_group_locks(chat_id)
    settings = get_group_settings(chat_id)

    if user_rank == 0:
        del_msg = False
        if locks.get("الكل") or locks.get("الدردشه"):
            del_msg = True
        elif (m.forward_from or m.forward_from_chat) and (locks.get("التوجيه") or locks.get("القنوات")):
            del_msg = True
        elif locks.get("الروابط") and re.search(r"(https?://|t\.me/|telegram\.me/|www\.)", text, re.I):
            del_msg = True
        elif (locks.get("اليوزر") or locks.get("التاك")) and "@" in text:
            del_msg = True
        elif locks.get("الشارحه") and "/" in text:
            del_msg = True
        elif locks.get("الكلايش") and len(text) > 400:
            del_msg = True
        elif locks.get("الانكليزيه") and re.search(r"[a-zA-Z]{4,}", text):
            del_msg = True
        elif locks.get("الفشار") and any(bw in ntext.split() for bw in BAD_WORDS):
            del_msg = True

        if del_msg:
            try:
                bot.delete_message(chat_id, m.message_id)
                punish = grp_data.get("punishment", "بالتقييد")
                if punish == "بالطرد":
                    bot.ban_chat_member(chat_id, user.id)
                    bot.unban_chat_member(chat_id, user.id)
                elif punish == "بالكتم":
                    bot.restrict_chat_member(chat_id, user.id, can_send_messages=False)
            except Exception:
                pass
            return

    if ntext == "لحق" and chat_id in active_airdrops:
        bag_amount = active_airdrops.pop(chat_id)
        update_user_field(user.id, cash=u_data["cash"] + bag_amount)
        bot.reply_to(
            m,
            f"🏃‍♂️💨 <b>كفو يا ذيب ({esc(u_data['name'])})!</b>\n"
            f"▽ : سبقت الكل ولحقت على حقيبة الفلوس في الشارع!\n"
            f"▽ : ربحت <b>{bag_amount} د.ل</b> كاش في جيبك 💵🔥"
        )
        return

    if chat_id in active_games:
        game = active_games[chat_id]
        if norm_ar(text) == norm_ar(game["answer"]):
            reward = game["reward"]
            del active_games[chat_id]
            update_user_field(user.id, cash=u_data["cash"] + reward, points=u_data["points"] + 5)
            bot.reply_to(
                m,
                f"🎉 <b>إجابة صحيحة وسريعة يا {esc(u_data['name'])}!</b>\n"
                f"▽ : ربحت <b>{reward} د.ل</b> كاش + 5 نقاط تفاعل ⭐"
            )
            return

    if settings.get("الالعاب", True):
        group_msg_counter[chat_id] = group_msg_counter.get(chat_id, 0) + 1
        if group_msg_counter[chat_id] >= 40 and chat_id not in active_airdrops:
            group_msg_counter[chat_id] = 0
            bag_val = random.choice([1000, 1500, 2000, 2500])
            active_airdrops[chat_id] = bag_val
            try:
                bot.send_message(
                    chat_id,
                    f"🚨💼 <b>حدث طارئ في الشارع العام!</b>\n"
                    f"------------------\n"
                    f"▽ : طاحت حقيبة فلوس فيها <b>{bag_val} د.ل</b> كاش!\n"
                    f"▽ : أول شخص يكتب كلمة ( <code>لحق</code> ) يأخذها كلها فوراً! 🏃‍♂️💨"
                )
            except Exception:
                pass

    if (
        settings.get("الرادار", True)
        and u_data["car"] != "بدون سيارة"
        and u_data["car"] in CARS
        and now - last_radar_time.get(user.id, 0) > 1800
        and random.randint(1, 100) <= 3
    ):
        last_radar_time[user.id] = now
        car_speed = CARS[u_data["car"]]["speed"]
        fine = int(car_speed * 1.2)
        new_cond = max(20, u_data["car_cond"] - 5)
        if u_data["cash"] >= fine:
            update_user_field(user.id, cash=u_data["cash"] - fine, car_cond=new_cond)
            bot.reply_to(
                m,
                f"🚓📸 <b>رادار الطريق الساحلي في {esc(u_data['city'])} صوّرك!</b>\n"
                f"▽ : كنت تجري بسيارتك (<b>{esc(u_data['car'])}</b>) بسرعة <b>{car_speed} كم/س</b>!\n"
                f"▽ : تم خصم مخالفة مرورية بقيمة <b>{fine} د.ل</b> من كاش جيبك 💸"
            )
        elif u_data["bank_balance"] >= fine:
            update_user_field(user.id, bank_balance=u_data["bank_balance"] - fine, car_cond=new_cond)
            bot.reply_to(
                m,
                f"🚓📸 <b>رادار الطريق الساحلي في {esc(u_data['city'])} صوّرك!</b>\n"
                f"▽ : كنت تجري بسيارتك (<b>{esc(u_data['car'])}</b>) بسرعة <b>{car_speed} كم/س</b>!\n"
                f"▽ : تم خصم مخالفة مرورية بقيمة <b>{fine} د.ل</b> من حسابك المصرفي 🏦"
            )

    if ntext in ("بوت", "يا بوت", "يابوت", b_name_norm, f"يا {b_name_norm}", f"يا{b_name_norm}"):
        bot.reply_to(m, random.choice(BOT_CALL_REPLIES).format(name=esc(b_name)))
        return

    for prefix in (b_name + " ", b_name_norm + " ", "بوت "):
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            ntext = norm_ar(text)
            break

    shortcuts = get_group_json(chat_id, "shortcuts", {})
    if text in shortcuts:
        text = shortcuts[text]
        ntext = norm_ar(text)
    elif ntext == "ا":
        text = "ايدي"
    elif ntext in ("ص", "جمال صورتي"):
        text = "صورتي"

    if settings.get("الردود", True):
        custom_replies = get_group_json(chat_id, "replies", {})
        if text in custom_replies:
            bot.reply_to(m, custom_replies[text])
            return

    if user.id == ADMIN_ID:
        if _handle_dev_commands(m, text, u_data):
            return

    if handle_admin_and_info_cmds(m, text, u_data, grp_data, user_rank, locks, now):
        return

    handle_economy_and_games_cmds(m, text, u_data, now)


# ══════════════════════════════════════════════════════════════════
# ⚡ أوامر المطور الأساسي (MG) السرية (تعمل بالكتابة السريعة ه = ة في القروب والخاص)
# ══════════════════════════════════════════════════════════════════

def _handle_dev_commands(m: types.Message, text: str, u_data: dict) -> bool:
    if m.from_user.id != ADMIN_ID:
        return False

    ntext = norm_ar(text)

    if ntext in ("م المطور", "اوامر المطور"):
        bot.reply_to(m, render_menu("menu_dev"), reply_markup=get_commands_kb(ADMIN_ID))
        return True

    if ntext.startswith("تغيير اسم البوت "):
        new_n = text.split(maxsplit=3)[3].strip()
        if new_n:
            set_bot_name(new_n)
            bot.reply_to(m, f"▽ : ⚡ تم تغيير اسم البوت إلى (<b>{esc(new_n)}</b>) بنجاح!")
        return True

    if ntext.startswith("اضف فلوس "):
        t_u = resolve_target_user(m, text)
        nums = [int(x) for x in ntext.split() if x.isdigit() and int(x) != (t_u["user_id"] if t_u else 0)]
        if t_u and nums:
            amt = nums[-1]
            update_user_field(t_u["user_id"], bank_balance=t_u["bank_balance"] + amt)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم إضافة <b>{amt} د.ل</b> لرصيد <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("خصم فلوس "):
        t_u = resolve_target_user(m, text)
        nums = [int(x) for x in ntext.split() if x.isdigit() and int(x) != (t_u["user_id"] if t_u else 0)]
        if t_u and nums:
            amt = nums[-1]
            new_b = max(0, t_u["bank_balance"] - amt)
            new_c = max(0, t_u["cash"] - max(0, amt - t_u["bank_balance"]))
            update_user_field(t_u["user_id"], bank_balance=new_b, cash=new_c)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم خصم <b>{amt} د.ل</b> من <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("تصفير فلوسه"):
        t_u = resolve_target_user(m, text)
        if t_u:
            update_user_field(t_u["user_id"], cash=0, home_cash=0, bank_balance=0)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم تصفير كاش ومصرف وخزنة <b>{esc(t_u['name'])}</b> بالكامل!")
            return True

    if ntext.startswith("منح سياره"):
        t_u = resolve_target_user(m, text)
        if t_u:
            car_name = find_car_name(text) or "Mercedes-AMG G63 V8 Biturbo 2025"
            update_user_field(t_u["user_id"], car=car_name, car_cond=100)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم منح السيارة (<b>{car_name}</b>) إلى <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("سحب سياره"):
        t_u = resolve_target_user(m, text)
        if t_u:
            update_user_field(t_u["user_id"], car="بدون سيارة")
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم سحب السيارة من <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("منح عقار"):
        t_u = resolve_target_user(m, text)
        if t_u:
            h_name = match_dict_key(HOUSES, text) or "قصر رئاسي محصن في فينيسيا"
            update_user_field(t_u["user_id"], house=h_name)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم منح العقار (<b>{h_name}</b>) إلى <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("سحب عقار"):
        t_u = resolve_target_user(m, text)
        if t_u:
            update_user_field(t_u["user_id"], house="بدون سكن", home_cash=0)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم سحب العقار من <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith(("منح متجر", "منح مشروع", "منح صيدليه")):
        t_u = resolve_target_user(m, text)
        if t_u:
            b_type = match_dict_key(BUSINESS_CATALOG, text) or "مول تجاري"
            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT INTO businesses (owner_id, owner_name, biz_type, custom_name, city, stock, vault, security, marketing, is_open) VALUES (?,?,?,?,?,100,0,80,3,1)",
                    (t_u["user_id"], t_u["name"], b_type, f"{b_type} {t_u['name']}", t_u["city"])
                )
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم منح مشروع (<b>{b_type}</b>) مجهز بالكامل إلى <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith(("سحب متجر", "سحب مشروع", "سحب صيدليه")):
        t_u = resolve_target_user(m, text)
        if t_u:
            with db_lock:
                conn = get_db()
                conn.execute("DELETE FROM businesses WHERE owner_id = ?", (t_u["user_id"],))
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم سحب وإغلاق مشاريع <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("منح مصرف"):
        t_u = resolve_target_user(m, text)
        if t_u:
            b_custom = f"مصرف {t_u['name']} الدولي"
            with db_lock:
                conn = get_db()
                conn.execute(
                    "INSERT OR REPLACE INTO custom_banks (owner_id, owner_name, bank_name, fee_pct, security, vault) VALUES (?,?,?,1.5,85,250000)",
                    (t_u["user_id"], t_u["name"], b_custom)
                )
                conn.commit()
                conn.close()
            update_user_field(t_u["user_id"], bank_name=b_custom)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم منح مصرف خاص « <b>{esc(b_custom)}</b> » إلى <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith("سحب مصرف"):
        t_u = resolve_target_user(m, text)
        if t_u:
            with db_lock:
                conn = get_db()
                conn.execute("DELETE FROM custom_banks WHERE owner_id = ?", (t_u["user_id"],))
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم سحب المصرف الخاص من <b>{esc(t_u['name'])}</b>!")
            return True

    if ntext.startswith(("تعيين مهنه", "تعيين وظيفه")):
        t_u = resolve_target_user(m, text)
        if t_u:
            chosen_job = match_dict_key(JOBS, text) or "مبرمج"
            update_user_field(t_u["user_id"], job=chosen_job, job_level=4, job_xp=60)
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم تعيين <b>{esc(t_u['name'])}</b> في مهنة (<b>{chosen_job} - الدرجة الرابعة العليا</b>)!")
            return True

    if ntext.startswith("فصل من العمل"):
        t_u = resolve_target_user(m, text)
        if t_u:
            update_user_field(t_u["user_id"], job="عاطل", job_level=1, job_xp=0)
            with db_lock:
                conn = get_db()
                conn.execute("DELETE FROM business_staff WHERE user_id = ?", (t_u["user_id"],))
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : ⚡ أمر المطور MG: تم فصل <b>{esc(t_u['name'])}</b> من وظيفته ومن جميع المتاجر!")
            return True

    if ntext.startswith(("اطلاق سراح", "عفو")):
        t_u = resolve_target_user(m, text)
        if t_u:
            update_user_field(t_u["user_id"], jail_until=0, wanted=0)
            bot.reply_to(m, f"▽ : ⚡ عفو سيادي من المطور MG! تم إطلاق سراح <b>{esc(t_u['name'])}</b> فوراً.")
            return True

    if ntext.startswith("صنع اكشطها "):
        parts = text.split()
        if len(parts) == 4 and parts[3].isdigit():
            code, amt = parts[2].upper(), int(parts[3])
            with db_lock:
                conn = get_db()
                conn.execute("INSERT OR REPLACE INTO scratch_cards (code, amount, claimed_by) VALUES (?,?,0)", (code, amt))
                conn.commit()
                conn.close()
            bot.reply_to(m, f"▽ : ⚡ تم صنع كرت اكشطها!\n▽ : الكود ← <code>{esc(code)}</code> | القيمة ← <b>{amt} د.ل</b>")
            return True

    if ntext == "قائمه اكشطها":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM scratch_cards WHERE claimed_by = 0").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "▽ : لا توجد كروت غير مستخدمة حالياً.")
        else:
            txt = "▽ : 🎫 كروت اكشطها المتاحة :\n------------------\n"
            for r in rows:
                txt += f"▽ : <code>{esc(r['code'])}</code> ~ {r['amount']} د.ل\n"
            bot.reply_to(m, txt)
        return True

    if ntext == "الهمسات":
        with db_lock:
            conn = get_db()
            rows = conn.execute("SELECT * FROM whispers ORDER BY id DESC LIMIT 15").fetchall()
            conn.close()
        if not rows:
            bot.reply_to(m, "▽ : لا توجد همسات مسجلة بعد.")
        else:
            txt = "🕵️‍♂️ سجل آخر 15 همسة سرية (خاص بالمطور MG) :\n------------------\n"
            for r in rows:
                txt += f"#{r['id']} | <b>{esc(r['sender_name'])}</b> ⬅️ <b>{esc(r['target_name'])}</b>:\n  └ <code>{esc(r['text'])}</code>\n"
            bot.reply_to(m, txt)
        return True

    if ntext == "الاحصائيات":
        with db_lock:
            conn = get_db()
            u_cnt = conn.execute("SELECT COUNT(*) as c FROM users").fetchone()["c"]
            g_cnt = conn.execute("SELECT COUNT(*) as c FROM groups").fetchone()["c"]
            b_cnt = conn.execute("SELECT COUNT(*) as c FROM businesses").fetchone()["c"]
            conn.close()
        bot.reply_to(
            m,
            f"📊 إحصائيات إمبراطورية أركان (خاص بالمطور MG) :\n"
            f"------------------\n"
            f"▽ : عدد المواطنين ← <b>{u_cnt}</b>\n"
            f"▽ : عدد المجموعات ← <b>{g_cnt}</b>\n"
            f"▽ : عدد المتاجر والشركات ← <b>{b_cnt}</b>"
        )
        return True

    if ntext == "نسخه احتياطيه" and DB_FILE.exists():
        with open(DB_FILE, "rb") as f:
            bot.send_document(ADMIN_ID, f, caption="📦 نسخة احتياطية لقاعدة بيانات إمبراطورية أركان")
        return True

    if ntext == "استعاده" and m.reply_to_message and m.reply_to_message.document:
        try:
            fi = bot.get_file(m.reply_to_message.document.file_id)
            dw = bot.download_file(fi.file_path)
            with db_lock:
                with open(DB_FILE, "wb") as f:
                    f.write(dw)
            init_db()
            bot.reply_to(m, "▽ : ✅ تمت استعادة قاعدة البيانات بنجاح!")
        except Exception as e:
            bot.reply_to(m, f"▽ : ❌ خطأ: {e}")
        return True

    if ntext.startswith("اذاعه "):
        b_msg = text.split(maxsplit=1)[1].strip()
        with db_lock:
            conn = get_db()
            g_rows = conn.execute("SELECT chat_id FROM groups").fetchall()
            conn.close()
        sent = 0
        for r in g_rows:
            try:
                bot.send_message(r["chat_id"], f"📢 <b>إذاعة رسمية من إدارة البوت :</b>\n------------------\n{esc(b_msg)}")
                sent += 1
            except Exception:
                pass
        bot.reply_to(m, f"▽ : ✅ تم إرسال الإذاعة إلى <b>{sent}</b> مجموعة!")
        return True

    return False


# ══════════════════════════════════════════════════════════════════
# 🔘 معالج الأزرار الشامل (استجابة فورية + ثبات الشاشة الرئيسية في القروب)
# ══════════════════════════════════════════════════════════════════

@bot.callback_query_handler(func=lambda c: True)
def on_callback(call: types.CallbackQuery):
    try:
        data = call.data or ""
        user = call.from_user
        chat_id = call.message.chat.id
        b_name = get_bot_name()

        if data == "check_sub":
            if is_channel_member(user.id):
                bot.answer_callback_query(call.id, "✅ تم التحقق من اشتراكك بنجاح!", show_alert=True)
            else:
                bot.answer_callback_query(call.id, f"❌ اشترك في القناة @{CHANNEL_USERNAME} أولاً!", show_alert=True)
            return

        # حماية ملكية الأزرار (لا أحد يستطيع الضغط على أزرار غيره!)
        if ":" in data:
            parts = data.split(":")
            action = parts[0]
            owner_id = int(parts[1]) if parts[1].isdigit() else 0
            if owner_id != 0 and user.id != owner_id and user.id != ADMIN_ID:
                bot.answer_callback_query(
                    call.id,
                    "🚫 هذه القائمة خاصة بصاحبها فقط! اكتب (الاوامر) لفتح قائمتك الخاصة.",
                    show_alert=True
                )
                return
        else:
            action = data
            owner_id = user.id

        # 1. عند الضغط على م1 - م9 أو الألعاب أو م المطور:
        if action in POPUP_ALERT_MENUS:
            if action == "menu_dev" and user.id != ADMIN_ID:
                bot.answer_callback_query(call.id, "🚫 هذا القسم سري وخاص بالمطور الأساسي (MG) فقط!", show_alert=True)
                return
            bot.answer_callback_query(call.id, POPUP_ALERT_MENUS[action][:195], show_alert=True)
            if call.message.chat.type == "private":
                kb = types.InlineKeyboardMarkup()
                kb.add(types.InlineKeyboardButton("🔙 رجوع للأوامر الرئيسية", callback_data=f"m_main:{owner_id}"))
                bot.edit_message_text(render_menu(action), chat_id=chat_id, message_id=call.message.message_id, reply_markup=kb)
            else:
                try:
                    bot.send_message(user.id, render_menu(action))
                except Exception:
                    pass
            return

        if action == "m_main":
            bot.edit_message_text(render_menu("main"), chat_id=chat_id, message_id=call.message.message_id, reply_markup=get_commands_kb(owner_id))
            return

        if action == "pm_c":
            bot.answer_callback_query(call.id, POPUP_ALERT_MENUS["menu_8"][:195], show_alert=True)
            if call.message.chat.type == "private":
                bot.send_message(chat_id, render_menu("menu_8"))
            return

        # 2. اختيار المدينة وتحديد المصرف والفرع والوظيفة والمشروع بالأزرار السريعة
        if action == "pc_m":
            bot.send_message(chat_id, "▽ : اختر مدينتك في ليبيا :", reply_markup=build_city_kb(user.id))
            bot.answer_callback_query(call.id)
            return

        if action == "sc":
            c_idx = int(data.split(":")[2])
            if 0 <= c_idx < len(CITY_LIST):
                chosen_city = CITY_LIST[c_idx][0]
                update_user_field(user.id, city=chosen_city)
                bot.answer_callback_query(call.id, f"✅ تم تسجيل مدينتك: ({chosen_city}) بنجاح!", show_alert=True)
            return

        if action == "pb_m":
            bot.send_message(chat_id, "▽ : اختر المصرف لفتح أو نقل حسابك إليه :", reply_markup=build_banks_kb(user.id))
            bot.answer_callback_query(call.id)
            return

        if action == "sb":
            _, _, b_kind, b_id_str = data.split(":")
            if b_kind == "o":
                b_idx = int(b_id_str)
                chosen_bank = BANK_LIST[b_idx][0]
                default_br = BANK_LIST[b_idx][3][0]
                update_user_field(user.id, bank_name=chosen_bank, bank_branch=default_br)
                bot.answer_callback_query(call.id, f"🏦 تم فتح/نقل حسابك في ({chosen_bank}) بنجاح! اختر الفرع الآن.", show_alert=True)
                bot.edit_message_text(
                    f"▽ : ✅ تم تفعيل حسابك في <b>{esc(chosen_bank)}</b>\n▽ : اختر الفرع المصرفي المفضل لديك :",
                    chat_id=chat_id,
                    message_id=call.message.message_id,
                    reply_markup=build_branches_kb(user.id, b_idx)
                )
            else:
                cb_id = int(b_id_str)
                with db_lock:
                    conn = get_db()
                    cb = conn.execute("SELECT bank_name FROM custom_banks WHERE id = ?", (cb_id,)).fetchone()
                    conn.close()
                if cb:
                    chosen_bank = cb["bank_name"]
                    update_user_field(user.id, bank_name=chosen_bank, bank_branch="الفرع الرئيسي")
                    bot.answer_callback_query(call.id, f"🏦 تم فتح حسابك في المصرف الخاص ({chosen_bank})!", show_alert=True)
                    bot.edit_message_text(
                        f"▽ : ✅ تم تفعيل حسابك في المصرف الخاص <b>{esc(chosen_bank)}</b> بنجاح!",
                        chat_id=chat_id,
                        message_id=call.message.message_id,
                        reply_markup=build_bank_secret_kb(user.id)
                    )
            return

        if action == "sbr":
            _, _, b_idx_s, br_idx_s = data.split(":")
            b_idx, br_idx = int(b_idx_s), int(br_idx_s)
            chosen_br = BANK_LIST[b_idx][3][br_idx]
            update_user_field(user.id, bank_branch=chosen_br)
            bot.answer_callback_query(call.id, f"✅ تم اعتماد فرعك المصرفي: ({chosen_br})!", show_alert=True)
            bot.edit_message_text(
                f"▽ : ✅ اكتمل إعداد حسابك المصرفي بنجاح!\n"
                f"▽ : المصرف ← <b>{esc(BANK_LIST[b_idx][0])}</b>\n"
                f"▽ : الفرع المعتمد ← <b>{esc(chosen_br)}</b>\n"
                f"▽ : اكتب <code>الوظائف</code> ثم <code>شغل</code> لكسب المال!",
                chat_id=chat_id,
                message_id=call.message.message_id,
                reply_markup=build_bank_secret_kb(user.id)
            )
            return

        # اختيار الوظيفة بالزر المباشر
        if action == "sj":
            j_idx = int(data.split(":")[2])
            if 0 <= j_idx < len(JOB_LIST):
                chosen_job = JOB_LIST[j_idx]
                update_user_field(user.id, job=chosen_job, job_level=1, job_xp=0)
                lvl_info = JOBS[chosen_job]["levels"][1]
                bot.answer_callback_query(call.id, f"💼 مبروك! تم تعيينك في مهنة ({chosen_job})!", show_alert=True)
                bot.edit_message_text(
                    f"▽ : 🎉 تم تعيينك رسمياً في مهنة <b>{esc(chosen_job)}</b>!\n"
                    f"▽ : الدرجة الأولى ← <b>{esc(lvl_info['title'])}</b> (الراتب: {lvl_info['salary']} د.ل)\n"
                    f"▽ : اكتب الآن <code>شغل</code> لاستلام راتبك، واكتب <code>وظيفتي</code> أو <code>ترقيه</code> لمتابعة درجتك!",
                    chat_id=chat_id,
                    message_id=call.message.message_id
                )
            return

        # فتح مشروع أو صيدلية أو متجر عطور بالزر المباشر
        if action == "obiz":
            b_idx = int(data.split(":")[2])
            if 0 <= b_idx < len(BIZ_KEYS_LIST):
                b_type = BIZ_KEYS_LIST[b_idx]
                cost = BUSINESS_CATALOG[b_type]["price"]
                u = ensure_user(user)
                if u["bank_balance"] >= cost:
                    update_user_field(user.id, bank_balance=u["bank_balance"] - cost)
                elif u["cash"] >= cost:
                    update_user_field(user.id, cash=u["cash"] - cost)
                else:
                    bot.answer_callback_query(call.id, f"❌ تحتاج {cost} د.ل لافتتاح ({b_type})!", show_alert=True)
                    return
                c_name = f"{b_type} {u['name']}"
                with db_lock:
                    conn = get_db()
                    conn.execute(
                        "INSERT INTO businesses (owner_id, owner_name, biz_type, custom_name, city, stock, vault, security, marketing, is_open) VALUES (?,?,?,?,?,20,0,20,1,1)",
                        (user.id, u["name"], b_type, c_name, u["city"])
                    )
                    conn.commit()
                    conn.close()
                bot.answer_callback_query(call.id, f"🎉 مبروك افتتاح ({c_name})!", show_alert=True)
                bot.edit_message_text(
                    f"🏢🎉 <b>تم افتتاح مشروعك بنجاح!</b>\n"
                    f"------------------\n"
                    f"▽ : المشروع ← « <b>{esc(c_name)}</b> »\n"
                    f"▽ : مخزون البداية ← <b>20 وحدة مجانية</b>\n"
                    f"▽ : اكتب <code>متجري</code> أو <code>صيدليتي</code> لإدارته!",
                    chat_id=chat_id,
                    message_id=call.message.message_id
                )
            return

        # 3. لوحة القفل والفتح والإعدادات
        if action == "locks_p":
            if get_rank(chat_id, user.id) < 2:
                bot.answer_callback_query(call.id, "❌ لوحة الحماية للادمنية فما فوق فقط!", show_alert=True)
                return
            bot.edit_message_text(f"▽ : لوحة القفل والفتح لبوت ({esc(b_name)}) :", chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_locks_kb(chat_id, owner_id))
            return

        if action == "tl":
            if get_rank(chat_id, user.id) < 2:
                bot.answer_callback_query(call.id, "❌ للادمنية فقط!", show_alert=True)
                return
            l_idx = int(data.split(":")[2])
            lk = LOCK_LIST[l_idx][0]
            st = not get_group_locks(chat_id).get(lk, False)
            set_group_lock(chat_id, lk, st)
            bot.answer_callback_query(call.id, f"▽ : تم {'قفل 🔒' if st else 'فتح 🔓'} {lk}")
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_locks_kb(chat_id, owner_id))
            return

        if action == "sets_p":
            if get_rank(chat_id, user.id) < 3:
                bot.answer_callback_query(call.id, "❌ لوحة الإعدادات للمدراء فما فوق فقط!", show_alert=True)
                return
            bot.edit_message_text(f"▽ : لوحة التفعيل والتعطيل لبوت ({esc(b_name)}) :", chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_settings_kb(chat_id, owner_id))
            return

        if action == "ts":
            if get_rank(chat_id, user.id) < 3:
                bot.answer_callback_query(call.id, "❌ للمدراء فقط!", show_alert=True)
                return
            s_idx = int(data.split(":")[2])
            sk = SETTING_LIST[s_idx][0]
            st = not get_group_settings(chat_id).get(sk, True)
            set_group_setting(chat_id, sk, st)
            bot.answer_callback_query(call.id, f"▽ : تم {'تفعيل ✅' if st else 'تعطيل ❌'} {sk}")
            bot.edit_message_reply_markup(chat_id=chat_id, message_id=call.message.message_id, reply_markup=build_settings_kb(chat_id, owner_id))
            return

        # 4. كشف رصيد المصرف السري لصاحب الحساب فقط!
        if data.startswith("sbank_"):
            target_owner = int(data.split("_")[1])
            if user.id not in (target_owner, ADMIN_ID):
                bot.answer_callback_query(call.id, "🚫 هذا الحساب المصرفي سري وخاص بصاحبه فقط!", show_alert=True)
                return
            owner = get_user_by_id(target_owner)
            if not owner:
                return
            u_stk = json.loads(owner.get("stocks") or "{}")
            stk_summary = "، ".join([f"{k}: {v}" for k, v in u_stk.items() if v > 0]) or "لا توجد"
            secret_msg = (
                f"🏦 كشف الخزنة المصرفية السري :\n"
                f"🏛️ المصرف : {owner['bank_name']}\n"
                f"💳 رصيد المصرف : {owner['bank_balance']} د.ل\n"
                f"🏠 كاش المنزل : {owner['home_cash']} د.ل\n"
                f"💵 كاش الجيب : {owner['cash']} د.ل\n"
                f"📈 الأسهم : {stk_summary}"
            )
            bot.answer_callback_query(call.id, secret_msg[:195], show_alert=True)
            return

        if data.startswith("dbank_"):
            target_owner = int(data.split("_")[1])
            if user.id != target_owner:
                bot.answer_callback_query(call.id, "🚫 هذا الزر خاص بصاحب الحساب فقط!", show_alert=True)
                return
            owner = get_user_by_id(target_owner)
            if not owner:
                return
            try:
                bot.send_message(
                    user.id,
                    f"🏦 <b>التقرير المالي السري — {esc(owner['bank_name'])}</b>\n"
                    f"------------------\n"
                    f"▽ : الفرع ← <b>{esc(owner['bank_branch'])}</b>\n"
                    f"▽ : رصيد المصرف السري ← <b>{owner['bank_balance']} د.ل</b> 🔒\n"
                    f"▽ : كاش المنزل ← <b>{owner['home_cash']} د.ل</b> 🏠\n"
                    f"▽ : كاش الجيب ← <b>{owner['cash']} د.ل</b> 💵\n"
                    f"▽ : العقار ← <b>{esc(owner['house'])}</b>\n"
                    f"▽ : السيارة ← <b>{esc(owner['car'])}</b>"
                )
                bot.answer_callback_query(call.id, "✅ تم إرسال التقرير السري إلى خاصك!", show_alert=True)
            except Exception:
                bot.answer_callback_query(call.id, "⚠️ افتح محادثة البوت في الخاص واضغط Start أولاً!", show_alert=True)
            return

        # 5. الهمسة السرية والتحديات
        if data.startswith("whisper_"):
            w_id = int(data.split("_")[1])
            with db_lock:
                conn = get_db()
                row = conn.execute("SELECT * FROM whispers WHERE id = ?", (w_id,)).fetchone()
                conn.close()
            if not row:
                bot.answer_callback_query(call.id, "▽ : هذه الهمسة غير موجودة!", show_alert=True)
                return
            if user.id in (row["sender_id"], row["target_id"], ADMIN_ID):
                bot.answer_callback_query(call.id, f"🔒 همسة سرية:\n\n{row['text']}"[:195], show_alert=True)
            else:
                bot.answer_callback_query(call.id, "🔒 هذه الهمسة سرية وليست لك!", show_alert=True)
            return

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
                bot.edit_message_text(f"🏳️ انسحب <b>{esc(duel['p2_name'])}</b> من التحدي!", chat_id=chat_id, message_id=call.message.message_id)
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
                w_n, l_n = p1_u["name"], p2_u["name"]
            else:
                update_user_field(p2_u["user_id"], cash=p2_u["cash"] + bet)
                update_user_field(p1_u["user_id"], cash=p1_u["cash"] - bet)
                w_n, l_n = p2_u["name"], p1_u["name"]
            bot.edit_message_text(
                f"⚔️🔥 فاز البطل <b>{esc(w_n)}</b> على <b>{esc(l_n)}</b> وربح <b>{bet} د.ل</b> كاش!",
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

    threading.Thread(target=run_web, daemon=True).start()

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
                logging.warning("تعارض 409 مؤقت.. الانتظار 5 ثوانٍ...")
                time.sleep(5)
            else:
                logging.error("خطأ تيليجرام: %s", api_err)
                time.sleep(3)
        except Exception as err:
            logging.error("خطأ اتصال عام: %s", err)
            time.sleep(3)
