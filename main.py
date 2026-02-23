import logging
import re
import os
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
# Ваш токен (уже прописан из ваших логов)
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
# ID группы модерации (замените на ваш ID группы, начинается с -100)
ADMIN_CHAT_ID = "-1003844600340" 

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Состояния диалога
(
    LINK_NAME, DESCRIPTION, ICON, TITLE, 
    CATEGORY, PRICE, VERSION, LINKS_BLOCK
) = range(8)

# --- КОНТЕНТ ---
SUPPORT_INFO = """
Tevs.service
────────────────────
📍 Омск, Россия
📞 (+7) (951) 402-40-88
📧 zorogamestoresup@gmail.com
📅 20 янв. 2026 г.
"""

RULES_TEXT = """
📜 **Критерии Zoro Game Store (ZGS):**

1. **Заголовок:** 2-25 символов, без ссылок.
2. **Версия:** Только цифры, точки, Alpha, beta, Release.
3. **Цена:** От 3 ₽ до 50 000 ₽.
4. **Файлы:** APK, EXE, HTML до 100 Гб. Без вирусов.
5. **Запреты:** Контент Meta*, пропаганда запрещенных организаций.

Нажимая «Начать», вы соглашаетесь с условиями.
"""

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 Mini App (Загрузить)", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("📝 Начать загрузку в боте", callback_data="start_survey")],
        [InlineKeyboardButton("📋 Правила", callback_data="show_rules")],
        [InlineKeyboardButton("👨‍💻 Связь с модером", callback_data="contact_mod")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"🎮 **Zoro Game Store Bot**\n\n{SUPPORT_INFO}\nВыберите действие:"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]]
    await query.edit_message_text(RULES_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("1️⃣ Введите **Название для ссылки** (короткое имя ID):")
    return LINK_NAME

async def get_link_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['link_name'] = update.message.text
    await update.message.reply_text("2️⃣ Введите **Описание игры**:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("3️⃣ Отправьте **Иконку** (ссылкой или файлом):")
    return ICON

async def get_icon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['icon'] = update.message.text or "Файл получен"
    await update.message.reply_text("4️⃣ Введите **Заголовок*** (2-25 символов, без ссылок):")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 2 or len(val) > 25 or "http" in val:
        await update.message.reply_text("❌ Ошибка! Название должно быть от 2 до 25 символов и без ссылок.")
        return TITLE
    context.user_data['title'] = val
    await update.message.reply_text("5️⃣ Введите **Категорию**:")
    return CATEGORY

async def get_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['category'] = update.message.text
    await update.message.reply_text("6️⃣ Введите **Цену** (от 3 до 50 000 ₽):")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", ""))
        if 3 <= price <= 50000:
            context.user_data['price'] = price
            await update.message.reply_text("7️⃣ Введите **Версию** (цифры, точки, Alpha/beta/Release):")
            return VERSION
        raise ValueError
    except:
        await update.message.reply_text("❌ Введите число от 3 до 50 000:")
        return PRICE

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if not re.match(r'^[0-9ABCV._\-betaAlphaRelease ]+$', val):
        await update.message.reply_text("❌ Неверный формат версии. Используйте цифры и разрешенные слова.")
        return VERSION
    context.user_data['version'] = val
    
    # ФИНАЛЬНАЯ ОТПРАВКА В ГРУППУ
    report = (
        f"📩 **НОВАЯ ЗАЯВКА ZGS**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎮 **Игра:** {context.user_data.get('title')}\n"
        f"📊 **Версия:** {context.user_data.get('version')}\n"
        f"💰 **Цена:** {context.user_data.get('price')} ₽\n"
        f"📂 **Категория:** {context.user_data.get('category')}\n"
        f"📝 **Описание:** {context.user_data.get('description')[:200]}\n"
        f"🔗 **Link Name:** {context.user_data.get('link_name')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Отправитель:** @{update.effective_user.username}\n"
        f"🆔 **ID:** `{update.effective_user.id}`"
    )
    
    try:
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=report, parse_mode="Markdown")
        await update.message.reply_text("✅ Успешно! Заявка отправлена модераторам в группу.")
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        await update.message.reply_text("❌ Ошибка отправки в группу. Проверьте, что бот там есть.")
        
    return ConversationHandler.END

async def contact_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💬 Напишите сообщение модератору, я передам его в группу.")
    return ConversationHandler.END # Можно расширить до пересылки сообщений

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(start_survey, pattern="^start_survey$"),
            CommandHandler("start", start)
        ],
        states={
            LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            ICON: [MessageHandler(filters.ALL & ~filters.COMMAND, get_icon)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(show_rules, pattern="^show_rules$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(contact_mod, pattern="^contact_mod$"))

    print("🚀 Бот ZGS активен. Ожидание заявок...")
    # Очистка старых обновлений для предотвращения Conflict
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
