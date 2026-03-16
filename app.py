#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
بوت صارحني – @sarr7neBot
كل مستخدم يحصل على رابط خاص به لاستقبال رسائل مجهولة
"""

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

# حالات المستخدمين (لتتبع من يرسل لمن)
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


# ─────────────── إدارة المستخدمين ───────────────

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
        logging.exception("تعذّر حفظ المستخدمين")

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

def get_user(user_id: int) -> dict | None:
    users = load_users()
    return users.get(str(user_id))

def get_users_count() -> int:
    return len(load_users())


# ─────────────── تحميل التفاعلات ───────────────

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

def log_message(sender, recipient_id: int, recipient_name: str, message_text: str) -> dict:
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


def send_owner_notification(sender, recipient_id: int, recipient_name: str,
                            recipient_username: str, message_text: str, log_entry: dict) -> None:
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

def get_subscribe_keyboard() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(
            "📢 اشترك في القناة أولاً",
            url=f"https://t.me/{CHANNEL_USERNAME}"
        ),
        types.InlineKeyboardButton(
            "✅ تم الاشتراك — تحقّق",
            callback_data="check_sub"
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

def get_user_link(user_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start={user_id}"


# ─────────────── أمر /start ───────────────

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message) -> None:
    user = m.from_user
    save_user(user)

    # التحقّق من الاشتراك
    if not is_channel_member(user.id):
        bot.send_message(
            m.chat.id,
            (
                "⚠️ <b>يجب الاشتراك في القناة أولاً!</b>\n\n"
                "📢 اشترك في القناة ثم اضغط «تحقّق» 👇"
            ),
            reply_markup=get_subscribe_keyboard()
        )
        return

    # التحقق من وجود بارامتر (رابط شخص آخر)
    args = m.text.split()

    if len(args) > 1:
        try:
            target_id = int(args[1])
        except ValueError:
            bot.reply_to(m, "❌ رابط غير صالح!")
            return

        # لا يمكن إرسال رسالة لنفسك
        if target_id == user.id:
            bot.reply_to(m, "❌ لا يمكنك إرسال رسالة مجهولة لنفسك!")
            return

        # جلب بيانات المستلم
        target_data = get_user(target_id)
        if target_data:
            target_name = target_data["full_name"]
        else:
            try:
                t_user = bot.get_chat(target_id)
                target_name = t_user.first_name or "مستخدم"
            except Exception:
                target_name = "مستخدم"

        # حفظ حالة المستخدم
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
                "🔒 هويتك ستكون مخفية تماماً\n\n"
                "▪️ <i>حانت لحظة الصراحة</i>"
            ),
            reply_markup=kb
        )
        return

    # الصفحة الرئيسية (بدون بارامتر)
    full_name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    link = get_user_link(user.id)

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🌐 إنشاء رابط خاص بي", callback_data="get_link"),
        types.InlineKeyboardButton("📢 القناة", url=f"https://t.me/{CHANNEL_USERNAME}"),
        types.InlineKeyboardButton("⚙️ المساعدة", callback_data="help"),
    )

    bot.send_message(
        m.chat.id,
        (
            f"أهلاً بك : (<b>{full_name}</b>)\n\n"
            "▪️ <b>بوت صارحني</b>\n\n"
            "▫️ احصل على نقد بناء بسرية تامة من زملائك وأصدقائك.\n\n"
            "🌐 احصل على رابطك الخاص\n"
            "💌 اقرأ ما كتبه الناس عنك\n"
            "⚙️ أوامر البوت - /help\n"
            "─"
        ),
        reply_markup=kb
    )


# ─────────────── أمر /mylink ───────────────

@bot.message_handler(commands=["mylink"])
def cmd_mylink(m: types.Message) -> None:
    save_user(m.from_user)
    link = get_user_link(m.from_user.id)

    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(
            "📤 شارك الرابط",
            switch_inline_query=f"أرسل لي رسالة مجهولة 💌\n{link}"
        )
    )

    bot.send_message(
        m.chat.id,
        (
            "▪️ <b>الرابط الخاص بك</b>\n\n"
            f"▫️ <code>{link}</code>\n\n"
            "▫️ يمكنك نشر الرابط في مجموعات التليجرام أو بين أصدقائك "
            "أو في مواقع التواصل الاجتماعي.\n\n"
            "▪️ <i>حانت لحظة الصراحة</i>\n"
            "─"
        ),
        reply_markup=kb
    )


# ─────────────── أمر /help ───────────────

@bot.message_handler(commands=["help"])
def cmd_help(m: types.Message) -> None:
    bot.send_message(
        m.chat.id,
        (
            "⚙️ <b>أوامر البوت:</b>\n\n"
            "▫️ /start — القائمة الرئيسية\n"
            "▫️ /mylink — رابطك الشخصي\n"
            "▫️ /help — المساعدة\n"
            "▫️ /id — معرّفك الشخصي\n\n"
            "<b>كيف يعمل البوت؟</b>\n"
            "1️⃣ أرسل /start أو اضغط «إنشاء رابط»\n"
            "2️⃣ شارك الرابط مع أصدقائك\n"
            "3️⃣ يرسلون لك رسائل مجهولة\n"
            "4️⃣ تصلك الرسالة بدون معرفة المرسل\n\n"
            "⚠️ يجب الاشتراك في القناة لاستخدام البوت"
        )
    )


# ─────────────── أمر /id ───────────────

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
            f"📥 <b>إلى:</b> {r['name']} [<code>{r['id']}</code>]\n"
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

    text = f"🔍 <b>رسائل المستخدم</b> <code>{search_id}</code>\n"
    text += f"📊 عدد الرسائل: <b>{len(results)}</b>\n\n"

    for log in results[-15:]:
        s = log["sender"]
        r = log["recipient"]
        if s["id"] == search_id:
            direction = "📤 أرسل"
        else:
            direction = "📥 استقبل"
        text += (
            f"━━━ #{log['msg_number']} ━━━\n"
            f"{direction}\n"
            f"📤 من: {s['name']} [<code>{s['id']}</code>]\n"
            f"📥 إلى: {r['name']} [<code>{r['id']}</code>]\n"
            f"💬 {log['message_text'][:80]}\n"
            f"🕐 {log['timestamp']}\n\n"
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
            f"• <b>{data['full_name']}</b> | "
            f"@{data['username'] or 'بدون'} | "
            f"<code>{data['id']}</code>\n"
        )

    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            bot.send_message(m.chat.id, chunk)
    else:
        bot.reply_to(m, text)


# ─────────────── استقبال الرسائل النصية ───────────────

@bot.message_handler(func=lambda msg: msg.chat.type == "private", content_types=["text"])
def private_handler(m: types.Message) -> None:
    user = m.from_user
    save_user(user)

    # التحقّق من الاشتراك
    if not is_channel_member(user.id):
        bot.reply_to(
            m,
            (
                "⚠️ <b>يجب الاشتراك في القناة أولاً!</b>\n\n"
                f"📢 اشترك في @{CHANNEL_USERNAME} ثم أرسل رسالتك مرة أخرى 👇"
            ),
            reply_markup=get_subscribe_keyboard()
        )
        return

    # التحقق من حالة المستخدم
    state = user_states.get(user.id)

    if state and state.get("action") == "send_anon":
        # ═══ إرسال رسالة مجهولة لمستخدم محدد ═══
        target_id = state["target_id"]
        target_name = state["target_name"]
        del user_states[user.id]

        # جلب بيانات المستلم
        target_data = get_user(target_id)
        target_username = target_data["username"] if target_data else "بدون"

        # تسجيل الرسالة + إشعار المالك
        log_entry = log_message(user, target_id, target_name, m.text)
        send_owner_notification(
            user, target_id, target_name, target_username, m.text, log_entry
        )

        # توجيه الأصل للأدمن
        try:
            bot.forward_message(ADMIN_ID, m.chat.id, m.message_id)
        except Exception:
            logging.exception("تعذّر توجيه الرسالة للأدمن")

        # إرسال الرسالة المجهولة للمستلم
        recipient_kb = types.InlineKeyboardMarkup(row_width=1)
        recipient_kb.add(
            types.InlineKeyboardButton(
                "↩️ رد برسالة مجهولة",
                url=f"https://t.me/{BOT_USERNAME}?start={user.id}"
            )
        )

        try:
            bot.send_message(
                target_id,
                (
                    "📩 <b>وصلتك رسالة مجهولة:</b>\n\n"
                    f"{m.text}\n\n"
                    "─\n"
                    "🔒 <i>هوية المرسل مخفية</i>"
                ),
                reply_markup=recipient_kb
            )
        except ApiTelegramException:
            bot.reply_to(m, "❌ المستخدم لم يبدأ محادثة مع البوت بعد!")
            return
        except Exception as e:
            bot.reply_to(m, "❌ حدث خطأ في الإرسال!")
            logging.exception("خطأ في الإرسال: %s", e)
            return

        # نشر في القناة
        try:
            sent = bot.send_message(
                TARGET_CHANNEL_ID,
                (
                    f"📩 <b>رسالة مجهولة جديدة لـ {target_name}:</b>\n\n"
                    f"{m.text}"
                ),
                reply_markup=build_keyboard(TARGET_CHANNEL_ID, 0),
                disable_web_page_preview=True,
            )
            init_entry(sent.chat.id, sent.message_id)
            bot.edit_message_reply_markup(
                sent.chat.id, sent.message_id,
                reply_markup=build_keyboard(sent.chat.id, sent.message_id),
            )
            save_reactions()
        except Exception:
            logging.exception("خطأ في النشر بالقناة")

        # تأكيد الإرسال
        bot.reply_to(
            m,
            (
                "✅ <b>تم إرسال رسالتك المجهولة بنجاح!</b>\n\n"
                f"📤 إلى: {target_name}\n"
                "🔒 هويتك مخفية تماماً عن المستلم"
            )
        )

    else:
        # ═══ رسالة بدون هدف — أرشد المستخدم ═══
        link = get_user_link(user.id)
        bot.reply_to(
            m,
            (
      
