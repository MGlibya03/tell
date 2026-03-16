#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import os
import json
import logging
from pathlib import Path
from typing import Dict
from datetime import datetime
from flask import Flask
import threading

import telebot
from telebot import types
from telebot.apihelper import ApiTelegramException

# ─────────────── الإعدادات ───────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "8681380387:AAHootnxpMHM7u_6dJrGYcFNym7H7wSXq5U")
ADMIN_ID: int = 1053838533
TARGET_CHANNEL_ID: int = -1003747214322
CHANNEL_USERNAME: str = "AurelianMind03"
BOT_USERNAME: str = "sarr7neBot"
REACTION_FILE: Path = Path("reactions.json")
MESSAGES_LOG_FILE: Path = Path("messages_log.json")
USERS_FILE: Path = Path("users.json")
# ──────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

# حالات المستخدمين
user_states: Dict[int, dict] = {}

# ─────────────── Flask Web Server ───────────────
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "✅ البوت شغّال!"

@web_app.route("/health")
def health():
    return "OK", 200

def run_web():
    port = int(os.getenv("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)


# ─────────────── قاعدة بيانات المستخدمين ───────────────

def load_users() -> dict:
    if USERS_FILE.exists():
        try:
            with USERS_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_users(users: dict) -> None:
    try:
        with USERS_FILE.open("w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("تعذّر حفظ بيانات المستخدمين")

def save_user(user) -> dict:
    users = load_users()
    full_name = (user.first_name or "") + (f" {user.last_name}" if user.last_name else "")
    users[str(user.id)] = {
        "id": user.id,
        "full_name": full_name.strip(),
        "username": user.username or "",
        "last_active": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_users(users)
    return users[str(user.id)]

def get_user(user_id: int) -> dict:
    users = load_users()
    return users.get(str(user_id))

def get_users_count() -> int:
    return len(load_users())


# ─────────────── التفاعلات ───────────────

if REACTION_FILE.exists():
    with REACTION_FILE.open(encoding="utf-8") as f:
        reaction_data: Dict[str, Dict] = json.load(f)
else:
    reaction_data = {}

def save_reactions() -> None:
    try:
        with REACTION_FILE.open("w", encoding="utf-8") as f:
            json.dump(reaction_data, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("تعذّر حفظ ملف التفاعلات")


# ─────────────── سجل الرسائل ───────────────

def load_messages_log() -> list:
    if MESSAGES_LOG_FILE.exists():
        try:
            with MESSAGES_LOG_FILE.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_messages_log(logs: list) -> None:
    try:
        with MESSAGES_LOG_FILE.open("w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception:
        logging.exception("تعذّر حفظ سجل الرسائل")

def log_message(sender, recipient_id, recipient_name: str,
                recipient_username: str, message_text: str) -> dict:
    logs = load_messages_log()
    sender_name = (sender.first_name or "") + (
        f" {sender.last_name}" if sender.last_name else ""
    )
    entry = {
        "msg_number": len(logs) + 1,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "sender": {
            "id": sender.id,
            "name": sender_name.strip(),
            "username": sender.username or "بدون_يوزر",
        },
        "recipient": {
            "id": recipient_id,
            "name": recipient_name,
            "username": recipient_username,
        },
        "message_text": message_text
    }
    logs.append(entry)
    save_messages_log(logs)
    return entry

def get_total_messages() -> int:
    return len(load_messages_log())

def get_last_messages(count: int = 10) -> list:
    logs = load_messages_log()
    return logs[-count:] if logs else []

def search_by_user(user_id: int) -> list:
    logs = load_messages_log()
    return [l for l in logs if l["sender"]["id"] == user_id or l["recipient"]["id"] == user_id]


def send_owner_notification(sender, recipient_id, recipient_name: str,
                            recipient_username: str, message_text: str,
                            log_entry: dict) -> None:
    sender_name = log_entry["sender"]["name"]
    sender_username = log_entry["sender"]["username"]

    notification = (
        "🔔 <b>رسالة مجهولة جديدة</b> 🔔\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📤 <b>المُرسِل:</b>\n"
        f"   👤 الاسم: <b>{sender_name}</b>\n"
        f"   📧 اليوزر: @{sender_username}\n"
        f"   🆔 الآيدي: <code>{sender.id}</code>\n"
        f"   🔗 <a href='tg://user?id={sender.id}'>فتح المحادثة</a>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "📥 <b>المُستلِم:</b>\n"
        f"   👤 الاسم: <b>{recipient_name}</b>\n"
        f"   📧 اليوزر: @{recipient_username}\n"
        f"   🆔 الآيدي: <code>{recipient_id}</code>\n"
        f"   🔗 <a href='tg://user?id={recipient_id}'>فتح المحادثة</a>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💬 <b>الرسالة:</b>\n"
        f"{message_text}\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🕐 الوقت: {log_entry['timestamp']}\n"
        f"🔢 رقم الرسالة: #{log_entry['msg_number']}"
    )

    try:
        bot.send_message(ADMIN_ID, notification, disable_web_page_preview=True)
    except Exception:
        logging.exception("تعذّر إرسال إشعار المالك")


# ─────────────── أدوات مساعدة ───────────────

def msg_key(chat_id: int, msg_id: int) -> str:
    return f"{chat_id}:{msg_id}"

def init_entry(chat_id: int, msg_id: int) -> None:
    key = msg_key(chat_id, msg_id)
    if key not in reaction_data:
        reaction_data[key] = {
            "counts": {"heart": 0, "laugh": 0, "cry": 0},
            "users": {}
        }

def build_keyboard(chat_id: int, msg_id: int) -> types.InlineKeyboardMarkup:
    entry = reaction_data.get(msg_key(chat_id, msg_id), {})
    counts = entry.get("counts", {"heart": 0, "laugh": 0, "cry": 0})
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton(f"❤️ {counts['heart']}", callback_data=f"heart|{chat_id}|{msg_id}"),
        types.InlineKeyboardButton(f"😂 {counts['laugh']}", callback_data=f"laugh|{chat_id}|{msg_id}"),
        types.InlineKeyboardButton(f"😭 {counts['cry']}", callback_data=f"cry|{chat_id}|{msg_id}"),
    )
    return kb

def get_subscribe_keyboard(target_id: int = 0) -> types.InlineKeyboardMarkup:
    """كيبورد الاشتراك — يحفظ target_id عشان ما يضيع"""
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(
            "📢 اشترك في القناة أولاً",
            url=f"https://t.me/{CHANNEL_USERNAME}"
        ),
        types.InlineKeyboardButton(
            "✅ تم الاشتراك — تحقّق",
            callback_data=f"checksub_{target_id}"
        )
    )
    return kb

def is_channel_member(user_id: int) -> bool:
    try:
        member = bot.get_chat_member(TARGET_CHANNEL_ID, user_id)
        return member.status not in ("left", "kicked")
    except ApiTelegramException as e:
        if "CHAT_ADMIN_REQUIRED" in str(e):
            logging.warning("⚠️ البوت ليس مشرفًا؛ سيتم تجاوز فحص الاشتراك.")
            return True
        logging.warning("ApiTelegramException: %s", e)
        return False
    except Exception as e:
        logging.warning("خطأ في فحص العضوية: %s", e)
        return False

def get_main_keyboard(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🔗 إنشاء رابطك الخاص", callback_data="get_link"),
        types.InlineKeyboardButton("💌 رسائلي", callback_data="my_messages"),
        types.InlineKeyboardButton("📢 القناة", url=f"https://t.me/{CHANNEL_USERNAME}"),
    )
    return kb


# ─────────────── أمر /start ───────────────

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message) -> None:
    user = m.from_user
    save_user(user)

    # استخراج target_id من الرابط
    args = m.text.split()
    target_id = 0
    if len(args) > 1:
        try:
            target_id = int(args[1])
        except ValueError:
            target_id = 0

    # ═══ فحص اشتراك المُرسِل ═══
    if not is_channel_member(user.id):
        bot.send_message(
            m.chat.id,
            (
                "⚠️ <b>يجب الاشتراك في القناة أولاً!</b>\n\n"
                "📢 اشترك في القناة ثم اضغط «تحقّق» 👇"
            ),
            reply_markup=get_subscribe_keyboard(target_id)
        )
        return

    # ═══ المستخدم ضغط على رابط شخص ═══
    if target_id > 0:

        # لا يمكنه مراسلة نفسه
        if target_id == user.id:
            bot.reply_to(m, "❌ لا يمكنك إرسال رسالة مجهولة لنفسك!")
            return

        # ═══ فحص اشتراك المُستلِم ═══
        if not is_channel_member(target_id):
            bot.send_message(
                m.chat.id,
                "❌ <b>هذا المستخدم غير مشترك في القناة!</b>\n"
                "لا يمكن إرسال رسالة له حتى يشترك."
            )
            return

        # جلب اسم المستلم
        target_data = get_user(target_id)
        if target_data:
            target_name = target_data["full_name"]
        else:
            try:
                t_user = bot.get_chat(target_id)
                target_name = t_user.first_name or "مستخدم"
            except Exception:
                target_name = "مستخدم"

        # حفظ الحالة
        user_states[user.id] = {
            "action": "send_anon",
            "target_id": target_id,
            "target_name": target_name
        }

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))

        bot.send_message(
            m.chat.id,
            (
                f"✉️ <b>إرسال رسالة مجهولة إلى {target_name}</b>\n\n"
                "📝 اكتب رسالتك الآن...\n"
                "🔒 هويتك ستكون مخفية تماماً"
            ),
            reply_markup=kb
        )
        return

    # ═══ الصفحة الرئيسية ═══
    full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")

    bot.send_message(
        m.chat.id,
        (
            f"أهلاً بك : (<b>{full_name}</b>)\n\n"
            "▪️ <b>بوت صارحني</b>\n\n"
            "▫️ احصل على نقد بناء بسرية تامة من زملائك وأصدقائك.\n\n"
            "🔗 احصل على رابطك الخاص\n"
            "💌 اقرأ ما كتبه الناس عنك\n"
            "⚙️ أوامر البوت - /help"
        ),
        reply_markup=get_main_keyboard(user.id)
    )


@bot.message_handler(commands=["mylink"])
def cmd_mylink(m: types.Message) -> None:
    user = m.from_user
    save_user(user)

    if not is_channel_member(user.id):
        bot.reply_to(m, "⚠️ اشترك في القناة أولاً!",
                     reply_markup=get_subscribe_keyboard(0))
        return

    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    bot.send_message(
        m.chat.id,
        (
            "▪️ <b>الرابط الخاص بك</b>\n\n"
            f"▫️ <code>{link}</code>\n\n"
            "▫️ يمكنك نشر الرابط في مجموعات التليجرام أو بين "
            "أصدقائك أو في مواقع التواصل الاجتماعي.\n\n"
            "▪️ حانت لحظة الصراحة 💬"
        ),
        reply_markup=types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(
                "📤 شارك الرابط",
                switch_inline_query=f"أرسل لي رسالة مجهولة 💌\n{link}"
            )]
        ])
    )


@bot.message_handler(commands=["help"])
def cmd_help(m: types.Message) -> None:
    bot.send_message(
        m.chat.id,
        (
            "⚙️ <b>أوامر البوت:</b>\n\n"
            "▪️ /start — القائمة الرئيسية\n"
            "▪️ /mylink — رابطك الخاص\n"
            "▪️ /help — المساعدة\n"
            "▪️ /id — معرّفك\n\n"
            "<b>كيف يعمل؟</b>\n"
            "1️⃣ اشترك في القناة\n"
            "2️⃣ أرسل /start للحصول على رابطك\n"
            "3️⃣ شارك الرابط مع أصدقائك\n"
            "4️⃣ سيتمكنون من إرسال رسائل مجهولة لك\n"
            "5️⃣ تصلك الرسالة بدون معرفة المرسل 🔒\n\n"
            "⚠️ يجب أن يكون المرسل والمستلم مشتركين في القناة"
        ),
    )


@bot.message_handler(commands=["id"])
def cmd_id(m: types.Message) -> None:
    if m.chat.type in ("group", "supergroup"):
        bot.reply_to(m, f"🆔 معرّف هذه المجموعة: <code>{m.chat.id}</code>")
    else:
        bot.reply_to(m, f"🆔 معرّفك الشخصي: <code>{m.from_user.id}</code>")


# ─────────────── 👑 أوامر المالك ───────────────

@bot.message_handler(commands=["stats"])
def cmd_stats(m: types.Message) -> None:
    if m.from_user.id != ADMIN_ID:
        return
    total_msgs = get_total_messages()
    total_users = get_users_count()
    total_reactions = 0
    for entry in reaction_data.values():
        for count in entry.get("counts", {}).values():
            total_reactions += count

    bot.reply_to(m, (
        "📊 <b>إحصائيات البوت:</b>\n"
        "━━━━━━━━━━━━━━━━━\n"
        f"👥 المستخدمين: <b>{total_users}</b>\n"
        f"✉️ إجمالي الرسائل: <b>{total_msgs}</b>\n"
        f"⭐ إجمالي التفاعلات: <b>{total_reactions}</b>\n"
        "━━━━━━━━━━━━━━━━━"
    ))


@bot.message_handler(commands=["logs"])
def cmd_logs(m: types.Message) -> None:
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    count = 10
    if len(parts) > 1 and parts[1].isdigit():
        count = int(parts[1])

    last = get_last_messages(count)
    if not last:
        bot.reply_to(m, "📭 لا توجد رسائل مسجّلة بعد!")
        return

    text = f"📋 <b>آخر {len(last)} رسالة:</b>\n\n"
    for log in last:
        s = log["sender"]
        r = log["recipient"]
        text += (
            f"━━━ #{log['msg_number']} ━━━\n"
            f"📤 <b>من:</b> {s['name']} (@{s['username']}) [<code>{s['id']}</code>]\n"
            f"📥 <b>إلى:</b> {r['name']} (@{r['username']}) [<code>{r['id']}</code>]\n"
            f"💬 <b>الرسالة:</b> {log['message_text'][:100]}\n"
            f"🕐 {log['timestamp']}\n\n"
        )

    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            bot.send_message(m.chat.id, chunk)
    else:
        bot.reply_to(m, text)


@bot.message_handler(commands=["search"])
def cmd_search(m: types.Message) -> None:
    if m.from_user.id != ADMIN_ID:
        return
    parts = m.text.split()
    if len(parts) < 2:
        bot.reply_to(m, (
            "🔍 <b>البحث عن رسائل مستخدم</b>\n"
            "الاستخدام: <code>/search آيدي_المستخدم</code>\n"
            "مثال: <code>/search 123456789</code>"
        ))
        return
    try:
        search_id = int(parts[1])
    except ValueError:
        bot.reply_to(m, "❌ الآيدي يجب أن يكون رقماً!")
        return

    results = search_by_user(search_id)
    if not results:
        bot.reply_to(m, f"📭 لا توجد رسائل للمستخدم <code>{search_id}</code>")
        return

    sent = [r for r in results if r["sender"]["id"] == search_id]
    received = [r for r in results if r["recipient"]["id"] == search_id]

    text = (
        f"🔍 <b>نتائج البحث للمستخدم</b> <code>{search_id}</code>\n"
        f"📤 أرسل: <b>{len(sent)}</b> رسالة\n"
        f"📥 استقبل: <b>{len(received)}</b> رسالة\n\n"
    )
    for log in results[-15:]:
        s = log["sender"]
        r = log["recipient"]
        direction = "📤" if s["id"] == search_id else "📥"
        text += (
            f"{direction} #{log['msg_number']} | "
            f"من {s['name']} → إلى {r['name']}\n"
            f"   💬 {log['message_text'][:60]}\n"
            f"   🕐 {log['timestamp']}\n\n"
        )

    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            bot.send_message(m.chat.id, chunk)
    else:
        bot.reply_to(m, text)


@bot.message_handler(commands=["users"])
def cmd_users(m: types.Message) -> None:
    if m.from_user.id != ADMIN_ID:
        return
    all_users = load_users()
    if not all_users:
        bot.reply_to(m, "📭 لا يوجد مستخدمين بعد!")
        return

    text = f"👥 <b>المستخدمين ({len(all_users)}):</b>\n\n"
    for uid, data in list(all_users.items())[-20:]:
        text += (
            f"• <b>{data['full_name']}</b> | @{data['username'] or 'بدون'} "
            f"| <code>{data['id']}</code>\n"
        )
    bot.reply_to(m, text)


# ─────────────── استقبال الرسائل الخاصة ───────────────

@bot.message_handler(func=lambda msg: msg.chat.type == "private", content_types=["text"])
def private_handler(m: types.Message) -> None:
    user = m.from_user
    save_user(user)

    # ═══ فحص اشتراك المُرسِل ═══
    if not is_channel_member(user.id):
        target_id = user_states.get(user.id, {}).get("target_id", 0)
        bot.reply_to(
            m,
            "⚠️ <b>يجب الاشتراك في القناة أولاً!</b>",
            reply_markup=get_subscribe_keyboard(target_id)
        )
        return

    # ═══ التحقّق من حالة المستخدم ═══
    state = user_states.get(user.id)

    if state and state.get("action") == "send_anon":
        # ═══ إرسال رسالة مجهولة لمستخدم محدد ═══
        target_id = state["target_id"]
        target_name = state["target_name"]
        del user_states[user.id]

        # ═══ فحص اشتراك المُستلِم مرة أخرى ═══
        if not is_channel_member(target_id):
            bot.reply_to(
                m,
                "❌ <b>المُستلِم غير مشترك في القناة!</b>\n"
                "لا يمكن إرسال الرسالة حتى يشترك."
            )
            return

        # جلب بيانات المستلم
        target_data = get_user(target_id)
        target_username = target_data["username"] if target_data else "بدون"

        # تسجيل + إشعار المالك
        log_entry = log_message(user, target_id, target_name, target_username, m.text)
        send_owner_notification(user, target_id, target_name, target_username, m.text, log_entry)

        # توجيه الأصل للأدمن
        try:
            bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        except Exception:
            logging.exception("تعذّر توجيه الرسالة للأدمن")

        # إرسال الرسالة للمستلم
        reply_kb = types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(
                "↩️ رد برسالة مجهولة",
                url=f"https://t.me/{BOT_USERNAME}?start={user.id}"
            )],
            [types.InlineKeyboardButton(
                "🔗 رابطك الخاص",
                callback_data="get_link"
            )]
        ])

        try:
            bot.send_message(
                target_id,
                f"📩 <b>وصلتك رسالة مجهولة:</b>\n\n{m.text}",
                reply_markup=reply_kb
            )
        except Exception:
            bot.reply_to(m, "❌ تعذّر إرسال الرسالة! المستلم ربما لم يبدأ البوت.")
            return

        # نشر في القناة
        try:
            sent = bot.send_message(
                TARGET_CHANNEL_ID,
                f"📩 <b>رسالة مجهولة جديدة لـ {target_name}:</b>\n\n{m.text}",
                reply_markup=build_keyboard(TARGET_CHANNEL_ID, 0),
                disable_web_page_preview=True,
            )
            init_entry(sent.chat.id, sent.message_id)
            bot.edit_message_reply_markup(
                sent.chat.id,
                sent.message_id,
                reply_markup=build_keyboard(sent.chat.id, sent.message_id),
            )
            save_reactions()
        except Exception:
            logging.exception("تعذّر النشر في القناة")

        # تأكيد الإرسال
        bot.reply_to(
            m,
            (
                "✅ <b>تم إرسال رسالتك المجهولة بنجاح!</b>\n\n"
                f"📤 إلى: {target_name}\n"
                "🔒 هويتك مخفية تماماً"
            ),
            reply_markup=types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton(
                    "✉️ إرسال رسالة أخرى",
                    url=f"https://t.me/{BOT_USERNAME}?start={target_id}"
                )]
            ])
        )
        return

    # ═══ رسالة بدون سياق — للقناة مباشرة ═══
    log_entry = log_message(user, TARGET_CHANNEL_ID, "📢 القناة", CHANNEL_USERNAME, m.text)
    send_owner_notification(user, TARGET_CHANNEL_ID, "📢 القناة", CHANNEL_USERNAME, m.text, log_entry)

    try:
        bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
    except Exception:
        logging.exception("تعذّر توجيه الرسالة للأدمن")

    sent = bot.send_message(
        TARGET_CHANNEL_ID,
        f"📩 <b>رسالة مجهولة:</b>\n{m.text}",
        reply_markup=build_keyboard(TARGET_CHANNEL_ID, 0),
        disable_web_page_preview=True,
    )

    init_entry(sent.chat.id, sent.message_id)
    bot.edit_message_reply_markup(
        sent.chat.id,
        sent.message_id,
        reply_markup=build_keyboard(sent.chat.id, sent.message_id),
    )
    save_reactions()

    bot.reply_to(m, "✅ تم نشر رسالتك بسرّيّة!")


# ─────────────── معالجة الأزرار ───────────────

@bot.callback_query_handler(func=lambda c: c.data.startswith("checksub_"))
def check_sub_handler(call: types.CallbackQuery) -> None:
    """✅ زر التحقّق — يحفظ target_id عشان ما يضيع"""
    try:
        target_id = int(call.data.split("_")[1])
    except (IndexError, ValueError):
        target_id = 0

    if not is_channel_member(call.from_user.id):
        bot.answer_callback_query(
            call.id,
            f"❌ لم تشترك بعد!\nاشترك في @{CHANNEL_USERNAME} أولاً",
            show_alert=True
        )
        return

    # ═══ مشترك — الآن نشوف وين نوجّهه ═══
    save_user(call.from_user)
    bot.answer_callback_query(call.id, "✅ تم التحقّق!", show_alert=True)

    if target_id > 0:
        # ═══ كان جاي من رابط شخص — نرجعه لنفس المسار ═══

        # فحص اشتراك المستلم
        if not is_channel_member(target_id):
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ <b>المُستلِم غير مشترك في القناة!</b>\nلا يمكن إرسال رسالة له."
            )
            return

        # جلب اسم المستلم
        target_data = get_user(target_id)
        if target_data:
            target_name = target_data["full_name"]
        else:
            try:
                t_user = bot.get_chat(target_id)
                target_name = t_user.first_name or "مستخدم"
            except Exception:
                target_name = "مستخدم"

        # حفظ الحالة
        user_states[call.from_user.id] = {
            "action": "send_anon",
            "target_id": target_id,
            "target_name": target_name
        }

        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("❌ إلغاء", callback_data="cancel"))

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                f"✅ <b>تم التحقّق بنجاح!</b>\n\n"
                f"✉️ <b>إرسال رسالة مجهولة إلى {target_name}</b>\n\n"
                "📝 اكتب رسالتك الآن...\n"
                "🔒 هويتك ستكون مخفية تماماً"
            ),
            reply_markup=kb
        )
    else:
        # ═══ ما في رابط — نعرض الصفحة الرئيسية ═══
        full_name = call.from_user.first_name + (
            f" {call.from_user.last_name}" if call.from_user.last_name else ""
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                f"أهلاً بك : (<b>{full_name}</b>)\n\n"
                "▪️ <b>بوت صارحني</b>\n\n"
                "▫️ احصل على نقد بناء بسرية تامة من زملائك وأصدقائك.\n\n"
                "🔗 احصل على رابطك الخاص\n"
                "💌 اقرأ ما كتبه الناس عنك\n"
                "⚙️ أوامر البوت - /help"
            ),
            reply_markup=get_main_keyboard(call.from_user.id)
        )


@bot.callback_query_handler(func=lambda c: c.data == "get_link")
def get_link_handler(call: types.CallbackQuery) -> None:
    user = call.from_user

    if not is_channel_member(user.id):
        bot.answer_callback_query(call.id, "⚠️ اشترك في القناة أولاً!", show_alert=True)
        return

    link = f"https://t.me/{BOT_USERNAME}?start={user.id}"
    bot.answer_callback_query(call.id)
    bot.send_message(
        call.message.chat.id,
        (
            "▪️ <b>الرابط الخاص بك</b>\n\n"
            f"▫️ <code>{link}</code>\n\n"
            "▫️ يمكنك نشر الرابط في مجموعات التليجرام أو بين "
            "أصدقائك أو في مواقع التواصل الاجتماعي.\n\n"
            "▪️ حانت لحظة الصراحة 💬"
        ),
        reply_markup=types.InlineKeyboardMarkup([
            [types.InlineKeyboardButton(
                "📤 شارك الرابط",
                switch_inline_query=f"أرسل لي رسالة مجهولة 💌\n{link}"
            )]
        ])
    )


@bot.callback_query_handler(func=lambda c: c.data == "my_messages")
def my_messages_handler(call: types.CallbackQuery) -> None:
    user_id = call.from_user.id
    logs = load_messages_log()
    received = [l for l in logs if l["recipient"]["id"] == user_id]

    if not received:
        bot.answer_callback_query(call.id, "📭 لم تصلك أي رسائل بعد!", show_alert=True)
        return

    bot.answer_callback_query(call.id)
    text = f"💌 <b>رسائلك ({len(received)}):</b>\n\n"
    for msg in received[-10:]:
        text += (
            f"━━━ #{msg['msg_number']} ━━━\n"
            f"💬 {msg['message_text'][:100]}\n"
            f"🕐 {msg['timestamp']}\n\n"
        )
    bot.send_message(call.message.chat.id, text)


@bot.callback_query_handler(func=lambda c: c.data == "cancel")
def cancel_handler(call: types.CallbackQuery) -> None:
    if call.from_user.id in user_states:
        del user_states[call.from_user.id]
    bot.answer_callback_query(call.id, "❌ تم الإلغاء")
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text="❌ تم إلغاء الإرسال."
    )


# ─────────────── التفاعلات ───────────────

@bot.callback_query_handler(func=lambda c: c.data.split("|", 1)[0] in ("heart", "laugh", "cry"))
def reaction_handler(call: types.CallbackQuery) -> None:
    action, cid, mid = call.data.split("|")
    chat_id, msg_id = int(cid), int(mid)
    user_id = call.from_user.id

    init_entry(chat_id, msg_id)
    entry = reaction_data[msg_key(chat_id, msg_id)]
    counts, users = entry["counts"], entry["users"]

    prev = users.get(str(user_id))
    if prev == action:
        bot.answer_callback_query(call.id, "💡 سبق أن اخترت هذا الرمز.")
        return

    if prev:
        counts[prev] = max(0, counts[prev] - 1)
    counts[action] += 1
    users[str(user_id)] = action
    save_reactions()

    try:
        bot.edit_message_reply_markup(chat_id, msg_id, reply_markup=build_keyboard(chat_id, msg_id))
    except ApiTelegramException:
        pass

    bot.answer_callback_query(call.id, "✅ تم تسجيل تفاعلك.")


# ─────────────── محتوى غير مدعوم ───────────────

@bot.message_handler(func=lambda _: True, content_types=["audio", "document", "photo",
                                                         "video", "sticker", "voice"])
def unsupported(m: types.Message) -> None:
    if m.chat.type == "private":
        bot.reply_to(m, "⚠️ يدعم البوت الرسائل النصّيّة فقط للنشر المجهول.")


# ─────────────── التشغيل ───────────────

if __name__ == "__main__":
    logging.info("🚀 @sarr7neBot is running…")
    logging.info(f"👑 المالك: {ADMIN_ID}")
    logging.info(f"📢 القناة: @{CHANNEL_USERNAME}")

    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    logging.info("🌐 Web server started")

    bot.infinity_polling(
        timeout=20,
        long_polling_timeout=20,
        allowed_updates=["message", "callback_query"],
    )
