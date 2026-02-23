import logging
import os
import threading
import random
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
(S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, SUPPORT_MODE) = range(20)

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

1. *Закон и этика:*
• Приложение не должно нарушать Конституцию РФ.
• Запрещены: порнография, вирусы, вредоносное ПО, шок-контент и дискриминация.
• *Запрет Meta:* Ссылки на Instagram/Facebook запрещены.

2. *Плакат (изображение):*
• Строго 164px h256px. Без чужого авторского контента.

3. *Цена и ссылки:*
• Цена: от 3 ₽ до 50 000 ₽.
• Ссылки только рабочие и легальные. Названия не должны вводить в заблуждение.
• Магазин не несет ответственности за внешние страницы.

4. *Технические данные:*
• Файлы любого формата до 100 ГБ.
• Рекомендуется отчет о тестировании и список исправлений.

*Нарушение любого пункта приведет к отказу.*
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
*Meta признана экстремистской организацией и запрещена в РФ.
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

# --- АДМИН ПАНЕЛЬ ---
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("|")
    action = data[0]
    user_id = data[1]
    project_name = data[2]

    if action == "approve":
        await context.bot.send_message(user_id, f"✅ Ваша заявка по проекту *{project_name}* одобрена!", parse_mode="Markdown")
        await query.edit_message_text(f"✅ Проект {project_name} ОДОБРЕН админом {update.effective_user.name}")
    elif action == "reject":
        await query.edit_message_text(f"❌ Проект {project_name} ОТКЛОНЕН. Введите причину отказа в ответ на этот пост.")
        context.user_data['reject_user_id'] = user_id

# Ответ админа на поддержку (просто ответьте на сообщение юзера в админ-чате)
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(update.effective_chat.id) == ADMIN_CHAT_ID and update.message.reply_to_message:
        reply_text = update.message.reply_to_message.text
        if "ID:" in reply_text:
            try:
                target_user_id = reply_text.split("ID:")[1].split("\n")[0].strip()
                await context.bot.send_message(target_user_id, f"👨‍💻 *Ответ поддержки:*\n\n{update.message.text}", parse_mode="Markdown")
                await update.message.reply_text("✅ Ответ отправлен пользователю.")
            except: pass

# --- ЛОГИКА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 *Zoro Game Store v7.0*\nВсе системы активны.", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_FULL, reply_markup=main_menu(), parse_mode="Markdown")

async def mini_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data.get('click_score', 0)
    context.user_data['click_score'] = score + 1
    await update.message.reply_text(f"🎯 **ZORO CLICKER**\n\nВы кликнули: {score + 1} раз(а)!", parse_mode="Markdown")

async def engine(u, c, key, next_s, txt, skip=True):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u, c)
    if 'media' not in c.user_data: c.user_data['media'] = []
    if u.message.text == "⏩ ПРОПУСТИТЬ":
        c.user_data[key] = "—"
    else:
        if u.message.text: c.user_data[key] = u.message.text
        else:
            c.user_data['media'].append(u.message.message_id)
            c.user_data[key] = "📎 [Файл прикреплен]"
    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

async def st_start(u,c): 
    c.user_data.clear()
    c.user_data['media'] = []
    await u.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu())
    return S1

async def s1(u,c): return await engine(u,c,'q1', S2, "2️⃣ *Описание:*")
async def s2(u,c): return await engine(u,c,'q2', S3, "3️⃣ *Иконка (URL/Файл):*")
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
    if not u.message.text: c.user_data['media'].append(u.message.message_id)
    c.user_data['q19'] = u.message.text if u.message.text else "📎 [Файл]"
    d = c.user_data
    uid = u.effective_user.id
    name = d.get('q4', 'Project')
    
    report = f"📩 **ЗАЯВКА (19/19)**\nАвтор: @{u.effective_user.username}\nID: `{uid}`\nПроект: {name}\n\n"
    for i in range(1, 20): report += f"{i}. {d.get(f'q{i}')}\n"
    
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Одобрить", callback_data=f"approve|{uid}|{name}"),
         InlineKeyboardButton("❌ Отклонить", callback_data=f"reject|{uid}|{name}")]
    ])
    
    await c.bot.send_message(ADMIN_CHAT_ID, report, reply_markup=kb)
    for mid in d.get('media', []):
        try: await c.bot.forward_message(ADMIN_CHAT_ID, u.message.chat_id, mid)
        except: pass
    
    await u.message.reply_text("🚀 *Заявка и файлы отправлены!*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_sup(u,c):
    await u.message.reply_text("👨‍💻 Напишите ваш вопрос:", reply_markup=survey_menu(False))
    return SUPPORT_MODE

async def send_sup(u,c):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u,c)
    msg = f"🆘 **SUPPORT**\nID: `{u.effective_user.id}`\nАвтор: @{u.effective_user.username}\n\n{u.message.text}"
    await c.bot.send_message(ADMIN_CHAT_ID, msg)
    await u.message.reply_text("✅ Отправлено! Ожидайте ответа.", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), st_start), 
                      MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_sup)],
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
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sup)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 ПРАВИЛА$"), show_rules))
    app.add_handler(MessageHandler(filters.Regex("^🎮 МИНИ-ИГРА$"), mini_game))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_reply)) # Ответ админа
    app.add_handler(CallbackQueryHandler(admin_decision)) # Кнопки Одобрить/Отказ
    app.add_handler(conv)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
