import logging
import re
import os
import asyncio
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    WebAppInfo, 
    ReplyKeyboardRemove
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340" 

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (HEALTH CHECK) ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running 24/7")

    def log_message(self, format, *args):
        return # Отключаем лишние логи сервера в консоли

def run_health_server():
    port = int(os.environ.get("PORT", 10000)) # Render передает порт в переменной PORT
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logger.info(f"Health check server started on port {port}")
    server.serve_forever()

# --- СОСТОЯНИЯ ДИАЛОГА ---
(LINK_NAME, DESCRIPTION, ICON, TITLE, CATEGORY, PRICE, VERSION) = range(7)

# --- ТЕКСТЫ ---
SUPPORT_INFO = """
Tevs.service
────────────────────
📍 Омск, Россия
📞 (+7) (951) 402-40-88
📅 2026
"""

RULES_TEXT = """
📜 **Правила Zoro Game Store:**
1. Заголовок: 2-25 символов.
2. Цена: от 3 до 50 000 ₽.
3. Версия: цифры и точки.
"""

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 Mini App", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("📝 Загрузить игру", callback_data="start_survey")],
        [InlineKeyboardButton("📋 Правила", callback_data="show_rules")]
    ]
    text = f"🎮 **Zoro Game Store Bot**\n{SUPPORT_INFO}"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.reply_text("1️⃣ Введите название для ссылки:")
    return LINK_NAME

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 2 or len(val) > 25:
        await update.message.reply_text("❌ Ошибка! Нужно 2-25 символов.")
        return TITLE
    context.user_data['title'] = val
    await update.message.reply_text("5️⃣ Введите категорию:")
    return CATEGORY

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", ""))
        if 3 <= price <= 50000:
            context.user_data['price'] = price
            await update.message.reply_text("7️⃣ Введите версию:")
            return VERSION
    except:
        pass
    await update.message.reply_text("❌ Введите число от 3 до 50 000:")
    return PRICE

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    v = update.message.text
    context.user_data['version'] = v
    
    report = (
        f"📩 **НОВАЯ ЗАЯВКА**\n"
        f"🎮 Игра: {context.user_data.get('title')}\n"
        f"💰 Цена: {context.user_data.get('price')} ₽\n"
        f"👤 От: @{update.effective_user.username}"
    )
    
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=report, parse_mode="Markdown")
    await update.message.reply_text("✅ Отправлено модераторам!")
    return ConversationHandler.END

def main():
    # 1. Запускаем "обманку" для Render в отдельном потоке
    threading.Thread(target=run_health_server, daemon=True).start()

    # 2. Инициализируем бота
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: (u.message.reply_text("2️⃣ Описание:"), DESCRIPTION)[1])],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: (u.message.reply_text("3️⃣ Иконка:"), ICON)[1])],
            ICON: [MessageHandler(filters.ALL & ~filters.COMMAND, lambda u,c: (u.message.reply_text("4️⃣ Заголовок:"), TITLE)[1])],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u,c: (u.message.reply_text("6️⃣ Цена:"), PRICE)[1])],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    logger.info("Бот запускается...")
    
    # drop_pending_updates=True критически важен для Render, 
    # чтобы убить старые запросы при перезапуске
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
