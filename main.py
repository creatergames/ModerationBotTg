import logging
import re
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    WebAppInfo
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- СЕРВЕР ДЛЯ СТАБИЛЬНОСТИ НА RENDER ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Zoro Store Bot is Flying!")
    def log_message(self, format, *args): return

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

# --- СОСТОЯНИЯ ---
(LINK_NAME, DESCRIPTION, ICON, TITLE, CATEGORY, PRICE, VERSION) = range(7)

# --- ГЛАВНОЕ МЕНЮ ---
def get_main_menu():
    keyboard = [
        [InlineKeyboardButton("🌐 Открыть Web App", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("📝 Загрузить игру (Бот)", callback_data="start_survey")],
        [InlineKeyboardButton("📜 Читать правила", callback_data="show_rules")]
    ]
    return InlineKeyboardMarkup(keyboard)

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎮 **Zoro Game Store Bot**\n\nДобро пожаловать! Здесь вы можете опубликовать свою игру или воспользоваться нашим Mini App."
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    text = "📜 **Правила Zoro Game Store:**\n\n1. Название: 2-25 символов.\n2. Цена: от 3 до 50 000 ₽.\n3. Версия: цифры, точки, Alpha/beta.\n\nГотовы продолжить?"
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]]
    await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    # Удаляем меню и начинаем опрос
    await update.callback_query.message.delete()
    await context.bot.send_message(update.effective_chat.id, "1️⃣ **Введите название для ссылки:**")
    return LINK_NAME

async def get_link_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['link_name'] = update.message.text
    await update.message.reply_text("2️⃣ **Введите описание игры:**")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("3️⃣ **Отправьте иконку (ссылку или текст):**")
    return ICON

async def get_icon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['icon'] = update.message.text
    await update.message.reply_text("4️⃣ **Введите заголовок (2-25 симв):**")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 2 or len(val) > 25:
        await update.message.reply_text("❌ Ошибка! Нужно 2-25 символов. Попробуйте снова:")
        return TITLE
    context.user_data['title'] = val
    await update.message.reply_text("5️⃣ **Введите категорию:**")
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text("6️⃣ **Введите цену (число):**")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", ""))
        if 3 <= price <= 50000:
            context.user_data['price'] = price
            await update.message.reply_text("7️⃣ **Введите версию (например 1.0.1):**")
            return VERSION
    except: pass
    await update.message.reply_text("❌ Введите число от 3 до 50 000:")
    return PRICE

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['version'] = update.message.text
    
    # Отчет в группу
    report = (
        f"📩 **НОВАЯ ЗАЯВКА**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎮 Игра: {context.user_data.get('title')}\n"
        f"📊 Версия: {context.user_data.get('version')}\n"
        f"💰 Цена: {context.user_data.get('price')} ₽\n"
        f"👤 От: @{update.effective_user.username}\n"
        f"🔗 Ссылка: {context.user_data.get('link_name')}"
    )
    
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=report, parse_mode="Markdown")
    await update.message.reply_text("✅ **Заявка отправлена!** Ожидайте модерации.", reply_markup=get_main_menu())
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    # Запускаем сервер для Render в фоне
    threading.Thread(target=run_health_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            ICON: [MessageHandler(filters.ALL & ~filters.COMMAND, get_icon)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(show_rules, pattern="^show_rules$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_to_start$"))
    app.add_handler(conv_handler)

    print("🚀 Бот летит на Render...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
