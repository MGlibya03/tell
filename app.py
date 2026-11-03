#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ==================== بداية القسم الأول ====================

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
DB_FILE: Path = Path("arkan_libya_v6.db")

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
    if not text:
        return ""
    t = text.strip()
    t = re.sub(r"[أإآ]", "ا", t)
    t = t.replace("ة", "ه")
    t = t.replace("ى", "ي")
    t = re.sub(r"\s+", " ", t)
    return t

def match_dict_key(mapping: dict, query: str) -> str | None:
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
    return "✅ إمبراطورية أركان الليبية — البوت يعمل باللهجة الليبية بنجاح 24/7!", 200

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
                account_type TEXT DEFAULT 'عادي',
                bank_name TEXT DEFAULT 'بدون مصرف',
                bank_branch TEXT DEFAULT 'الفرع الرئيسي - طرابلس',
                bank_card TEXT DEFAULT 'عادي',
                cash INTEGER DEFAULT 0,
                home_cash INTEGER DEFAULT 0,
                bank_balance INTEGER DEFAULT 0,
                deposit_amount INTEGER DEFAULT 0,
                deposit_until INTEGER DEFAULT 0,
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
                marriage_role TEXT DEFAULT '',
                dowry INTEGER DEFAULT 0,
                steal_success INTEGER DEFAULT 0,
                msg_count INTEGER DEFAULT 0,
                sahkat_count INTEGER DEFAULT 0,
                contacts_count INTEGER DEFAULT 0,
                likes_count INTEGER DEFAULT 0,
                points INTEGER DEFAULT 0,
                created_at TEXT DEFAULT '',
                last_salary INTEGER DEFAULT 0,
                last_rob INTEGER DEFAULT 0,
                last_work INTEGER DEFAULT 0,
                firewall_until INTEGER DEFAULT 0
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS user_likes (
                target_id INTEGER,
                liker_id INTEGER,
                PRIMARY KEY (target_id, liker_id)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS bank_checks (
                check_code TEXT PRIMARY KEY,
                issuer_id INTEGER,
                issuer_name TEXT,
                bank_name TEXT,
                amount INTEGER,
                claimed_by INTEGER DEFAULT 0,
                created_at TEXT
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS bank_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action_text TEXT,
                timestamp TEXT
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
                rules_text TEXT DEFAULT 'احترام الجميع وعدم نشر الروابط أو السب والشتم.',
                replies TEXT DEFAULT '{}',
                multi_replies TEXT DEFAULT '{}',
                shortcuts TEXT DEFAULT '{}',
                banned_cmds TEXT DEFAULT '[]',
                banned_names TEXT DEFAULT '[]',
                tag_words TEXT DEFAULT '[]',
                toheed_text TEXT DEFAULT '',
                toheed_enabled INTEGER DEFAULT 0,
                toheed_mute_count INTEGER DEFAULT 3,
                like_emoji TEXT DEFAULT '🧡',
                id_addon_mode TEXT DEFAULT 'الكل',
                id_header TEXT DEFAULT '',
                freeze_id INTEGER DEFAULT 0,
                night_mode INTEGER DEFAULT 0,
                flood_limit INTEGER DEFAULT 5,
                nidaa_minutes INTEGER DEFAULT 5,
                nidaa_replies TEXT DEFAULT '[]',
                discuss_channel TEXT DEFAULT ''
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
            CREATE TABLE IF NOT EXISTS friends (
                chat_id INTEGER,
                user_id INTEGER,
                user_name TEXT,
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

# ==================== نهاية القسم الأول ====================
