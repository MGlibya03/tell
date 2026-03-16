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
# ──────────────────────────────────────────

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)

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

def log_message(sender, message_text: str) -> dict:
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
    return [l for l in logs if l["sender"]["id"] == user_id]


def send_owner_notification(sender, message_text: str, log_entry: dict) -> None:
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


# ─────────────── أوامر البوت ───────────────

@bot.message_handler(commands=["start"])
def cmd_start(m: types.Message) -> None:
    if not is_channel_member(m.from_user.id):
        bot.send_message(
            m.chat.id,
            (
                "⚠️ <b>يجب الاشتراك في القناة أولاً!</b>\n\n"
                "📢 اشترك في القناة ثم اضغط «تحقّق» 👇"
            ),
            reply_markup=get_subscribe_keyboard()
        )
        return

    bot.send_message(
        m.chat.id,
        (
            "👋 أهلاً ومرحبًا بك!\n"
            "• أرسل رسالتك هنا، وسننشرها في القناة بسرّيّة تامّة.\n"
            "✨ استمتع بحريّة التعبير!"
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
    total_reactions = 0
    for entry in reaction_data.values():
        for count in entry.get("counts", {}).values():
            total_reactions += count

    bot.reply_to(m, (
        "📊 <b>إحصائيات البوت:</b>\n"
        "━━━━━━━━━━━━━━━━━\n"
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
        text += (
            f"━━━ #{log['msg_number']} ━━━\n"
            f"📤 <b>من:</b> {s['name']} (@{s['username']}) [<code>{s['id']}</code>]\n"
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
        bot.reply_to(m, f"📭 لا توجد رسائل من المستخدم <code>{search_id}</code>")
        return

    text = (
        f"🔍 <b>رسائل المستخدم</b> <code>{search_id}</code>\n"
        f"👤 الاسم: <b>{results[0]['sender']['name']}</b>\n"
        f"📧 اليوزر: @{results[0]['sender']['username']}\n"
        f"📊 عدد الرسائل: <b>{len(results)}</b>\n\n"
    )
    for log in results[-15:]:
        text += (
            f"━━━ #{log['msg_number']} ━━━\n"
            f"💬 {log['message_text'][:80]}\n"
            f"🕐 {log['timestamp']}\n\n"
        )

    if len(text) > 4000:
        chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
        for chunk in chunks:
            bot.send_message(m.chat.id, chunk)
    else:
        bot.reply_to(m, text)


# ─────────────── استقبال الرسائل الخاصة ───────────────

@bot.message_handler(func=lambda msg: msg.chat.type == "private", content_types=["text"])
def private_handler(m: types.Message) -> None:
    if not is_channel_member(m.from_user.id):
        bot.reply_to(
            m,
            (
                "⚠️ <b>يجب الاشتراك في القناة أولاً!</b>\n\n"
                f"📢 اشترك في @{CHANNEL_USERNAME} ثم أرسل رسالتك مرة أخرى 👇"
            ),
            reply_markup=get_subscribe_keyboard()
        )
        return

    log_entry = log_message(m.from_user, m.text)
    send_owner_notification(m.from_user, m.text, log_entry)

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


# ─────────────── زر التحقّق من الاشتراك ───────────────

@bot.callback_query_handler(func=lambda c: c.data == "check_sub")
def check_sub_handler(call: types.CallbackQuery) -> None:
    if is_channel_member(call.from_user.id):
        bot.answer_callback_query(call.id, "✅ تم التحقّق! أنت مشترك الآن", show_alert=True)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=(
                "✅ <b>تم التحقّق بنجاح!</b>\n\n"
                "👋 أهلاً ومرحبًا بك!\n"
                "• أرسل رسالتك هنا، وسننشرها في القناة بسرّيّة تامّة.\n"
                "✨ استمتع بحريّة التعبير!"
            )
        )
    else:
        bot.answer_callback_query(
            call.id,
            f"❌ لم تشترك بعد!\nاشترك في @{CHANNEL_USERNAME} أولاً",
            show_alert=True
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

    # تشغيل سيرفر الويب أولاً
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    logging.info("🌐 Web server started")

    # تشغيل البوت
    bot.infinity_polling(
        timeout=20,
        long_polling_timeout=20,
        allowed_updates=["message", "callback_query"],
    )
