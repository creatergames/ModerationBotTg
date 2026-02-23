import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, WebAppInfo, KeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters
)

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"

# 19 состояний анкеты
(L_LINK, L_DESC, L_ICON, L_TITLE, L_CAT, L_PRICE, L_VER, 
 L_URL1, L_URL2, L_URL3, L_URL4, L_NOTE, L_COMM, L_BG, L_CHNG, 
 L_FILE, L_GAME_ICON, L_SCRINS, L_ADDF) = range(19)

logging.basicConfig(level=logging.INFO)

# --- HEALTH CHECK SERVER (Для Render) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine: Flying")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- КЛАВИАТУРЫ (Командные) ---
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ MINI APP", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def get_survey_keyboard(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ОТМЕНИТЬ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "🎮 *ZORO GAME STORE*\n\nБот готов к работе 24/7. Используйте кнопки меню ниже."
    await update.message.reply_text(txt, reply_markup=get_main_keyboard(), parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = """*Tevs.service*
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
Омск, Россия | (+7) (951) 402-40-88
zorogamestoresup@gmail.com

*Критерии:* Название (2-25 симв), Цена (3-50к), Версия (A, B, Release). 
Файлы до 100 Гб. Запрещены вирусы и экстремизм."""
    await update.message.reply_text(rules, parse_mode="Markdown")

# --- ЛОГИКА АНКЕТЫ ---

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=get_survey_keyboard(), parse_mode="Markdown")
    return L_LINK

async def flow_control(update, context, key, next_st, text, can_skip=True):
    msg_text = update.message.text
    if msg_text == "❌ ОТМЕНИТЬ":
        await update.message.reply_text("🛑 Заполнение прервано.", reply_markup=get_main_keyboard())
        return ConversationHandler.END
    
    # Сохраняем данные (если не пропущено)
    context.user_data[key] = "Пропущено" if msg_text == "⏩ ПРОПУСТИТЬ" else msg_text
    
    await update.message.reply_text(text, reply_markup=get_survey_keyboard(can_skip), parse_mode="Markdown")
    return next_st

# Цепочка из 19 вопросов
async def q1(u,c): return await flow_control(u,c,'link', L_DESC, "2️⃣ *Описание:*")
async def q2(u,c): return await flow_control(u,c,'desc', L_ICON, "3️⃣ *Иконка (URL):*")
async def q3(u,c): return await flow_control(u,c,'icon', L_TITLE, "4️⃣ *Заголовок (ОБЯЗАТЕЛЬНО)*:", False)
async def q4(u,c): return await flow_control(u,c,'title', L_CAT, "5️⃣ *Категория:*")
async def q5(u,c): return await flow_control(u,c,'cat', L_PRICE, "6️⃣ *Цена:*")
async def q6(u,c): return await flow_control(u,c,'price', L_VER, "7️⃣ *Версия:*")
async def q7(u,c): return await flow_control(u,c,'ver', L_URL1, "8️⃣ *Ссылка 1 (название = ссылка):*")
async def q8(u,c): return await flow_control(u,c,'u1', L_URL2, "9️⃣ *Ссылка 2:*")
async def q9(u,c): return await flow_control(u,c,'u2', L_URL3, "🔟 *Ссылка 3:*")
async def q10(u,c): return await flow_control(u,c,'u3', L_URL4, "1️⃣1️⃣ *Ссылка 4:*")
async def q11(u,c): return await flow_control(u,c,'u4', L_NOTE, "1️⃣2️⃣ *Примечание к игре:*")
async def q12(u,c): return await flow_control(u,c,'note', L_COMM, "1️⃣3️⃣ *Комментарии (ссылка):*")
async def q13(u,c): return await flow_control(u,c,'comm', L_BG, "1️⃣4️⃣ *Фоновое изображение (URL):*")
async def q14(u,c): return await flow_control(u,c,'bg', L_CHNG, "1️⃣5️⃣ *Описание изменений:*")
async def q15(u,c): return await flow_control(u,c,'chng', L_FILE, "1️⃣6️⃣ *Файл игры:*")
async def q16(u,c): return await flow_control(u,c,'file', L_GAME_ICON, "1️⃣7️⃣ *Иконка игры:*")
async def q17(u,c): return await flow_control(u,c,'g_ico', L_SCRINS, "1️⃣8️⃣ *Скриншоты (до 8 шт):*")
async def q18(u,c): return await flow_control(u,c,'scrs', L_ADDF, "1️⃣9️⃣ *Доп. файлы и названия:*")

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['add_f'] = update.message.text
    d = context.user_data
    report = (
        f"📩 **НОВАЯ ЗАЯВКА ZGS**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🕹 **Игра:** {d.get('title')}\n"
        f"💰 **Цена:** {d.get('price')} ₽ | **Версия:** {d.get('ver')}\n"
        f"👤 **Автор:** @{update.effective_user.username}\n"
        f"━━━━━━━━━━━━━━"
    )
    await context.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    await update.message.reply_text("🚀 *Заявка отправлена!*", reply_markup=get_main_keyboard(), parse_mode="Markdown")
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), start_survey)],
        states={
            L_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, q1)],
            L_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, q2)],
            L_ICON: [MessageHandler(filters.TEXT & ~filters.COMMAND, q3)],
            L_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, q4)],
            L_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, q5)],
            L_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, q6)],
            L_VER: [MessageHandler(filters.TEXT & ~filters.COMMAND, q7)],
            L_URL1: [MessageHandler(filters.TEXT & ~filters.COMMAND, q8)],
            L_URL2: [MessageHandler(filters.TEXT & ~filters.COMMAND, q9)],
            L_URL3: [MessageHandler(filters.TEXT & ~filters.COMMAND, q10)],
            L_URL4: [MessageHandler(filters.TEXT & ~filters.COMMAND, q11)],
            L_NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, q12)],
            L_COMM: [MessageHandler(filters.TEXT & ~filters.COMMAND, q13)],
            L_BG: [MessageHandler(filters.TEXT & ~filters.COMMAND, q14)],
            L_CHNG: [MessageHandler(filters.TEXT & ~filters.COMMAND, q15)],
            L_FILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, q16)],
            L_GAME_ICON: [MessageHandler(filters.TEXT & ~filters.COMMAND, q17)],
            L_SCRINS: [MessageHandler(filters.TEXT & ~filters.COMMAND, q18)],
            L_ADDF: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ОТМЕНИТЬ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 ПРАВИЛА$"), show_rules))
    app.add_handler(MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), lambda u,c: u.message.reply_text("Support: @zorogamestoresup")))
    app.add_handler(conv)

    print("🚀 ZGS BOOTED")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
