import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# --- ДАННЫЕ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"

# Состояния анкеты
(L_LINK, L_DESC, L_ICON, L_TITLE, L_CAT, L_PRICE, L_VER, 
 L_URL1, L_URL2, L_URL3, L_URL4, L_NOTE, L_COMM, L_BG, L_CHNG, 
 L_FILE, L_GAME_ICON, L_SCRINS, L_ADDF, L_ADDF_NAME) = range(20)

logging.basicConfig(level=logging.INFO)

# --- SERVER FOR RENDER (FAST) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine v3.0: Flying")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- ПРАВИЛА ---
RULES_TEXT = """
*Tevs.service*
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📍 Омск, Россия | 📞 (+7) (951) 402-40-88
📧 zorogamestoresup@gmail.com

*Краткие правила ZGS:*
• Название: 2-25 символов.
• Цена: 3 - 50 000 ₽.
• Запрещены: Meta*, шок-контент, вирусы.
• Файлы: до 100 Гб (APK, EXE, HTML).
"""

# --- КЛАВИАТУРЫ ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ZORO STORE", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("🚀 ОПУБЛИКОВАТЬ ИГРУ", callback_data="start_survey")],
        [InlineKeyboardButton("📋 ПРАВИЛА", callback_data="show_rules"), InlineKeyboardButton("👨‍💻 ПОДДЕРЖКА", callback_data="contact_mod")]
    ])

def survey_kb(can_skip=True):
    btns = []
    if can_skip: btns.append(InlineKeyboardButton("⏩ ПРОПУСТИТЬ", callback_data="skip"))
    btns.append(InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel"))
    return InlineKeyboardMarkup([btns])

# --- ОБРАБОТЧИКИ ШАГОВ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "🎮 *Zoro Game Store*\n\nЗаполните анкету для публикации вашего проекта. Поля со звездочкой (*) обязательны."
    if update.message: await update.message.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("1️⃣ *Название для ссылки:*", reply_markup=survey_kb(), parse_mode="Markdown")
    return L_LINK

# Функция для циклической обработки шагов
async def next_step(update, context, current_key, next_state, text, can_skip=True):
    val = "Не указано"
    if update.message:
        val = update.message.text if update.message.text else "Файл/Медиа"
    context.user_data[current_key] = val
    
    msg_func = update.message.reply_text if update.message else update.callback_query.message.edit_text
    await msg_func(text, reply_markup=survey_kb(can_skip), parse_mode="Markdown")
    return next_state

# Последовательность шагов
async def step_1(u, c): return await next_step(u, c, 'link', L_DESC, "2️⃣ *Описание:*")
async def step_2(u, c): return await next_step(u, c, 'desc', L_ICON, "3️⃣ *Иконку (URL или файл):*")
async def step_3(u, c): return await next_step(u, c, 'icon', L_TITLE, "4️⃣ *Заголовок*: (Обязательно!)", False)
async def step_4(u, c): 
    if not u.message or not u.message.text: return L_TITLE
    return await next_step(u, c, 'title', L_CAT, "5️⃣ *Категория:*")
async def step_5(u, c): return await next_step(u, c, 'cat', L_PRICE, "6️⃣ *Цена:*")
async def step_6(u, c): return await next_step(u, c, 'price', L_VER, "7️⃣ *Версия:*")
async def step_7(u, c): return await next_step(u, c, 'ver', L_URL1, "8️⃣ *Ссылка 1* (название = ссылка):")
async def step_8(u, c): return await next_step(u, c, 'url1', L_URL2, "9️⃣ *Ссылка 2* (название = ссылка):")
async def step_9(u, c): return await next_step(u, c, 'url2', L_URL3, "🔟 *Ссылка 3* (название = ссылка):")
async def step_10(u, c): return await next_step(u, c, 'url3', L_URL4, "1️⃣1️⃣ *Ссылка 4* (название = ссылка):")
async def step_11(u, c): return await next_step(u, c, 'url4', L_NOTE, "1️⃣2️⃣ *Примечание к игре:*")
async def step_12(u, c): return await next_step(u, c, 'note', L_COMM, "1️⃣3️⃣ *Комментарии* (ТГ ссылка или запрос на создание):")
async def step_13(u, c): return await next_step(u, c, 'comm', L_BG, "1️⃣4️⃣ *Фоновое изображение* (URL или файл):")
async def step_14(u, c): return await next_step(u, c, 'bg', L_CHNG, "1️⃣5️⃣ *Описание последних изменений:*")
async def step_15(u, c): return await next_step(u, c, 'chng', L_FILE, "1️⃣6️⃣ *Файл игры* (до 100 Гб):")
async def step_16(u, c): return await next_step(u, c, 'file', L_GAME_ICON, "1️⃣7️⃣ *Иконка игры:*")
async def step_17(u, c): return await next_step(u, c, 'g_icon', L_SCRINS, "1️⃣8️⃣ *Скриншоты* (до 8 шт):")
async def step_18(u, c): return await next_step(u, c, 'scrins', L_ADDF, "1️⃣9️⃣ *Доп. файлы и их названия* (до 8 шт):")

async def final_step(update, context):
    context.user_data['add_f'] = update.message.text if update.message else "Нет"
    
    # Сборка полной заявки
    d = context.user_data
    report = (
        f"📩 **ПОЛНАЯ ЗАЯВКА ZGS**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🕹 **Заголовок:** {d.get('title')}\n"
        f"🔗 **ID ссылки:** {d.get('link')}\n"
        f"📝 **Описание:** {d.get('desc')}\n"
        f"💰 **Цена:** {d.get('price')} ₽ | 📊 **Версия:** {d.get('ver')}\n"
        f"🗂 **Категория:** {d.get('cat')}\n"
        f"🌐 **Ссылки:** {d.get('url1')}, {d.get('url2')}\n"
        f"💬 **Комменты:** {d.get('comm')}\n"
        f"⚠️ **Примечание:** {d.get('note')}\n"
        f"🆙 **Изменения:** {d.get('chng')}\n"
        f"━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** @{update.effective_user.username}"
    )
    
    await context.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    msg = update.message.reply_text if update.message else update.callback_query.message.edit_text
    await msg("🚀 **Заявка «улетела» модераторам!** Ожидайте ответа.", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            L_LINK: [MessageHandler(filters.ALL, step_1), CallbackQueryHandler(step_1, pattern="^skip$")],
            L_DESC: [MessageHandler(filters.ALL, step_2), CallbackQueryHandler(step_2, pattern="^skip$")],
            L_ICON: [MessageHandler(filters.ALL, step_3), CallbackQueryHandler(step_3, pattern="^skip$")],
            L_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_4)], # Без пропуска
            L_CAT: [MessageHandler(filters.ALL, step_5), CallbackQueryHandler(step_5, pattern="^skip$")],
            L_PRICE: [MessageHandler(filters.ALL, step_6), CallbackQueryHandler(step_6, pattern="^skip$")],
            L_VER: [MessageHandler(filters.ALL, step_7), CallbackQueryHandler(step_7, pattern="^skip$")],
            L_URL1: [MessageHandler(filters.ALL, step_8), CallbackQueryHandler(step_8, pattern="^skip$")],
            L_URL2: [MessageHandler(filters.ALL, step_9), CallbackQueryHandler(step_9, pattern="^skip$")],
            L_URL3: [MessageHandler(filters.ALL, step_10), CallbackQueryHandler(step_10, pattern="^skip$")],
            L_URL4: [MessageHandler(filters.ALL, step_11), CallbackQueryHandler(step_11, pattern="^skip$")],
            L_NOTE: [MessageHandler(filters.ALL, step_12), CallbackQueryHandler(step_12, pattern="^skip$")],
            L_COMM: [MessageHandler(filters.ALL, step_13), CallbackQueryHandler(step_13, pattern="^skip$")],
            L_BG: [MessageHandler(filters.ALL, step_14), CallbackQueryHandler(step_14, pattern="^skip$")],
            L_CHNG: [MessageHandler(filters.ALL, step_15), CallbackQueryHandler(step_15, pattern="^skip$")],
            L_FILE: [MessageHandler(filters.ALL, step_16), CallbackQueryHandler(step_16, pattern="^skip$")],
            L_GAME_ICON: [MessageHandler(filters.ALL, step_17), CallbackQueryHandler(step_17, pattern="^skip$")],
            L_SCRINS: [MessageHandler(filters.ALL, step_18), CallbackQueryHandler(step_18, pattern="^skip$")],
            L_ADDF: [MessageHandler(filters.ALL, final_step), CallbackQueryHandler(final_step, pattern="^skip$")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^cancel$")]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^cancel$"))
    app.add_handler(conv)

    print("🚀 ZGS FAST ENGINE STARTING...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
