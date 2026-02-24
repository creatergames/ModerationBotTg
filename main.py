import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters, CallbackQueryHandler
)

# --- НАСТРОЙКИ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"
WEB_APP_URL = "https://zoro-game.store/"

# Состояния
(S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, SUPPORT_MODE, ADMIN_REPLY) = range(21)

logging.basicConfig(level=logging.INFO)

# --- SERVER ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Ultimate Engine Active")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- ПРАВИЛА ---
RULES_FULL = """
📋 *ПРАВИЛА РАЗМЕЩЕНИЯ ZGS*
... (ваш текст правил) ...
"""

# --- UI ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ ZGS MINI APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "🎮 МИНИ-ИГРА"],
        ["👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def survey_menu(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ВЕРНУТЬСЯ В МЕНЮ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- АДМИН-ЛОГИКА (ОДОБРЕНИЕ / ОТКЛОНЕНИЕ) ---
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action, user_id, type_msg = query.data.split("|")
    context.user_data['target_user'] = user_id

    if action == "approve":
        await context.bot.send_message(user_id, "✅ Ваша заявка одобрена модератором!")
        await query.edit_message_text(f"{query.message.text}\n\n📢 **СТАТУС: ОДОБРЕНО**")
    elif action == "reject":
        await query.edit_message_text(f"{query.message.text}\n\n📢 **СТАТУС: ОЖИДАЕТСЯ ПРИЧИНА ОТКАЗА...**")
        return ADMIN_REPLY

# Обработка комментария админа
async def admin_send_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('target_user')
    comment = update.message.text
    if user_id:
        await context.bot.send_message(user_id, f"❌ Ваша заявка/обращение отклонено.\n💬 **Комментарий модератора:** {comment}")
        await update.message.reply_text("✅ Комментарий отправлен пользователю.")
    return ConversationHandler.END

# --- ОСНОВНАЯ ЛОГИКА ---
async def start(u, c):
    await u.message.reply_text("💎 *Zoro Game Store v7.0*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(u, c):
    await u.message.reply_text(RULES_FULL, parse_mode="Markdown")

async def mini_game(u, c):
    score = c.user_data.get('click_score', 0) + 1
    c.user_data['click_score'] = score
    await u.message.reply_text(f"🎯 **ZORO CLICKER**\nКликов: {score}")

async def engine(u, c, key, next_s, txt, skip=True):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u, c)
    if 'media' not in c.user_data: c.user_data['media'] = []
    if u.message.text == "⏩ ПРОПУСТИТЬ":
        c.user_data[key] = "—"
    else:
        if u.message.text: c.user_data[key] = u.message.text
        else:
            c.user_data['media'].append(u.message.message_id)
            c.user_data[key] = "📎 [Файл]"
    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

# Шаги
async def st_start(u,c): 
    c.user_data.clear()
    c.user_data['media'] = []
    await u.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu())
    return S1

# ... (промежуточные шаги s1-s18 остаются без изменений) ...
async def s1(u,c): return await engine(u,c,'q1', S2, "2️⃣ *Описание:*")
async def s2(u,c): return await engine(u,c,'q2', S3, "3️⃣ *Иконка:*")
async def s3(u,c): return await engine(u,c,'q3', S4, "4️⃣ *ЗАГОЛОВОК*:", False)
async def s4(u,c): return await engine(u,c,'q4', S5, "5️⃣ *Категория:*")
async def s5(u,c): return await engine(u,c,'q5', S6, "6️⃣ *Цена:*")
async def s6(u,c): return await engine(u,c,'q6', S7, "7️⃣ *Версия:*")
async def s7(u,c): return await engine(u,c,'q7', S8, "8️⃣ *Ссылка 1:*")
async def s8(u,c): return await engine(u,c,'q8', S9, "9️⃣ *Ссылка 2:*")
async def s9(u,c): return await engine(u,c,'q9', S10, "🔟 *Ссылка 3:*")
async def s10(u,c): return await engine(u,c,'q10', S11, "1️⃣1️⃣ *Ссылка 4:*")
async def s11(u,c): return await engine(u,c,'q11', S12, "1️⃣2️⃣ *Примечание:*")
async def s12(u,c): return await engine(u,c,'q12', S13, "1️⃣3️⃣ *Комментарии:*")
async def s13(u,c): return await engine(u,c,'q13', S14, "1️⃣4️⃣ *Фоновое изображение:*")
async def s14(u,c): return await engine(u,c,'q14', S15, "1️⃣5️⃣ *Лог изменений:*")
async def s15(u,c): return await engine(u,c,'q15', S16, "1️⃣6️⃣ *Файл игры:*")
async def s16(u,c): return await engine(u,c,'q16', S17, "1️⃣7️⃣ *Иконка игры:*")
async def s17(u,c): return await engine(u,c,'q17', S18, "1️⃣8️⃣ *Скриншоты:*")
async def s18(u,c): return await engine(u,c,'q18', S19, "1️⃣9️⃣ *Дополнительные файлы:*")

async def final(u,c):
    c.user_data['q19'] = u.message.text if u.message.text else "📎"
    d = c.user_data
    uid = u.effective_user.id
    report = f"📩 **ЗАЯВКА ОТ @{u.effective_user.username}**\n"
    for i in range(1, 20): report += f"{i}. {d.get(f'q{i}')}\n"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve|{uid}|app"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject|{uid}|app")]
    ])
    
    await c.bot.send_message(ADMIN_CHAT_ID, report, reply_markup=kb)
    for mid in d.get('media', []):
        try: await c.bot.forward_message(ADMIN_CHAT_ID, u.message.chat_id, mid)
        except: pass
    await u.message.reply_text("🚀 Отправлено!", reply_markup=main_menu())
    return ConversationHandler.END

async def start_sup(u,c):
    await u.message.reply_text("💬 Напишите вопрос:", reply_markup=survey_menu(False))
    return SUPPORT_MODE

async def send_sup(u,c):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u,c)
    uid = u.effective_user.id
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Одобрить", callback_data=f"approve|{uid}|sup"), InlineKeyboardButton("❌ Отклонить", callback_data=f"reject|{uid}|sup")]])
    await c.bot.send_message(ADMIN_CHAT_ID, f"🆘 **ПОДДЕРЖКА**\nОт: @{u.effective_user.username}\nТекст: {u.message.text}", reply_markup=kb)
    await u.message.reply_text("✅ Отправлено!", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    # ВАЖНО: Обработчики кнопок меню вынесены ДО ConversationHandler, чтобы они работали всегда
    app.add_handler(MessageHandler(filters.Regex("^📋 ПРАВИЛА$"), show_rules))
    app.add_handler(MessageHandler(filters.Regex("^🎮 МИНИ-ИГРА$"), mini_game))
    app.add_handler(CommandHandler("start", start))
    
    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), st_start),
            MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_sup),
            CallbackQueryHandler(admin_callback) # Ловим кнопки админа
        ],
        states={
            S1: [MessageHandler(filters.ALL & ~filters.COMMAND, s1)], S2: [MessageHandler(filters.ALL & ~filters.COMMAND, s2)],
            S3: [MessageHandler(filters.ALL & ~filters.COMMAND, s3)], S4: [MessageHandler(filters.ALL & ~filters.COMMAND, s4)],
            S5: [MessageHandler(filters.ALL & ~filters.COMMAND, s5)], S6: [MessageHandler(filters.ALL & ~filters.COMMAND, s6)],
            S7: [MessageHandler(filters.ALL & ~filters.COMMAND, s7)], S8: [MessageHandler(filters.ALL & ~filters.COMMAND, s8)],
            S9: [MessageHandler(filters.ALL & ~filters.COMMAND, s9)], S10: [MessageHandler(filters.ALL & ~filters.COMMAND, s10)],
            S11: [MessageHandler(filters.ALL & ~filters.COMMAND, s11)], S12: [MessageHandler(filters.ALL & ~filters.COMMAND, s12)],
            S13: [MessageHandler(filters.ALL & ~filters.COMMAND, s13)], S14: [MessageHandler(filters.ALL & ~filters.COMMAND, s14)],
            S15: [MessageHandler(filters.ALL & ~filters.COMMAND, s15)], S16: [MessageHandler(filters.ALL & ~filters.COMMAND, s16)],
            S17: [MessageHandler(filters.ALL & ~filters.COMMAND, s17)], S18: [MessageHandler(filters.ALL & ~filters.COMMAND, s18)],
            S19: [MessageHandler(filters.ALL & ~filters.COMMAND, final)],
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sup)],
            ADMIN_REPLY: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_send_comment)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
        allow_reentry=True
    )
    
    app.add_handler(conv)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
