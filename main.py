import logging
import re
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
TOKEN = "7547192801:AAH8rS5FOn-j8OAn9K0yE1p0G1G6G1G6G1G" # Твой токен от BotFather
ADMIN_CHAT_ID = "6434444555" # Твой ID для получения заявок

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Состояния
(
    START_ORDER, LINK_NAME, DESCRIPTION, ICON, TITLE, 
    CATEGORY, PRICE, VERSION, LINKS_BLOCK, NOTE, COMMENTS, 
    BACKGROUND, CHANGELOG, GAME_FILE, GAME_ICON, SCREENSHOTS, EXTRA_FILES
) = range(17)

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

1. **Название:** 2-25 символов, без ссылок и мата.
2. **Обложка:** 16:9, без АП.
3. **Версия:** Числа, A, B, C, V, '.', '_', '-', "beta", "Alpha", "Release".
4. **Файлы:** APK, EXE, HTML до 100 Гб. Без вирусов.
5. **Цена:** от 3 ₽ до 50 000 ₽.
6. **Запреты:** Контент Meta*, пропаганда запрещенных орг. РФ.

Нажимая кнопку ниже, вы соглашаетесь с правилами.
"""

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
    return START_ORDER

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    keyboard = [[InlineKeyboardButton("⬅️ Назад", callback_data="back_to_start")]]
    await query.edit_message_text(RULES_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("1️⃣ Введите **Название для ссылки**:")
    return LINK_NAME

async def get_link_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['link_name'] = update.message.text
    await update.message.reply_text("2️⃣ Введите **Описание**:")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text
    await update.message.reply_text("3️⃣ Отправьте **Иконку** (URL или файл):")
    return ICON

async def get_icon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['icon'] = update.message.text or (update.message.document.file_id if update.message.document else "Файл")
    await update.message.reply_text("4️⃣ Введите **Заголовок*** (от 2 до 25 символов):")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    if len(val) < 2 or len(val) > 25 or "http" in val:
        await update.message.reply_text("❌ Ошибка! Название должно быть 2-25 символов и без ссылок. Попробуйте еще раз:")
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
            await update.message.reply_text("7️⃣ Введите **Версию** (цифры, точки, beta/Alpha/Release):")
            return VERSION
        raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Введите число от 3 до 50 000:")
        return PRICE

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    if not re.match(r'^[0-9ABCV._\-betaAlphaRelease ]+$', val):
        await update.message.reply_text("❌ Неверный формат версии. Используйте цифры, точки или слова Alpha/beta.")
        return VERSION
    context.user_data['version'] = val
    await update.message.reply_text("8️⃣ Введите ссылки (до 4) в формате `название = ссылка`. Когда закончите, напишите 'Далее'.")
    return LINKS_BLOCK

async def get_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text.lower() == 'далее':
        await update.message.reply_text("9️⃣ Введите **Примечание к игре**:")
        return NOTE
    if 'links' not in context.user_data: context.user_data['links'] = []
    context.user_data['links'].append(text)
    await update.message.reply_text(f"Добавлено ({len(context.user_data['links'])}/4). Еще одну или 'Далее'?")
    return LINKS_BLOCK

async def finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Финальная сборка данных (упрощено для краткости)
    await update.message.reply_text("✅ Заявка успешно сформирована и отправлена модераторам Zoro Store!")
    
    # Отправка админу
    summary = f"🆕 **Новая игра на модерацию!**\n\nЗаголовок: {context.user_data.get('title')}\nВерсия: {context.user_data.get('version')}\nЦена: {context.user_data.get('price')} ₽"
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary, parse_mode="Markdown")
    return ConversationHandler.END

async def contact_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("💬 Напишите ваше сообщение модератору. Я его передам.")
    context.user_data['waiting_mod'] = True
    return START_ORDER

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_survey, pattern="^start_survey$"),
            CallbackQueryHandler(show_rules, pattern="^show_rules$"),
            CallbackQueryHandler(start, pattern="^back_to_start$"),
            CallbackQueryHandler(contact_mod, pattern="^contact_mod$")
        ],
        states={
            LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_name)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            ICON: [MessageHandler(filters.ALL & ~filters.COMMAND, get_icon)],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_category)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
            LINKS_BLOCK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_links)],
            NOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_survey)], # Упростил для примера
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    
    print("🚀 Бот Zoro Store запущен на Render...")
    app.run_polling()

if __name__ == "__main__":
    main()
