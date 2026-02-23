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

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Константы состояний
(
    START_ORDER, RULES_AGREE, LINK_NAME, DESCRIPTION, ICON, TITLE, 
    CATEGORY, PRICE, VERSION, LINKS_BLOCK, NOTE, COMMENTS, 
    BACKGROUND, CHANGELOG, GAME_FILE, GAME_ICON, SCREENSHOTS, EXTRA_FILES
) = range(18)

# Контакты и инфо
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

1. **Название:** 2-25 символов, без ссылок, без мата.
2. **Обложка:** Формат 16:9, без порнографии и АП.
3. **Скриншоты:** 3 основных обязательно, далее - безлимит.
4. **Версия:** Числа, A, B, C, V, '.', '_', '-', "beta", "Alpha", "Release".
5. **Файлы:** APK, EXE, HTML до 100 Гб. Без вирусов.
6. **Цена:** от 3 ₽ до 50 000 ₽.
7. **Запреты:** Контент Meta*, пропаганда запрещенных орг. РФ, нарушение Конституции РФ.

Полный список доступен в меню. Согласны продолжить?
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌐 Mini App (Загрузить игру)", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("📝 Начать загрузку в боте", callback_data="start_survey")],
        [InlineKeyboardButton("📋 Правила и Поддержка", callback_data="show_rules")],
        [InlineKeyboardButton("👨‍💻 Связь с модером", callback_data="contact_mod")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"🎮 **Zoro Game Store Bot**\n\n{SUPPORT_INFO}\nПривет! Выберите действие:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    return START_ORDER

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    keyboard = [[InlineKeyboardButton("✅ Я ознакомлен, начать", callback_data="start_survey")]]
    await query.edit_message_text(RULES_TEXT, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("1️⃣ Введите **Название для ссылки** (для внутреннего использования):")
    return LINK_NAME

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text.strip()
    # Валидация по правилам ZGS
    if len(val) < 2 or len(val) > 25:
        await update.message.reply_text("❌ Ошибка! Название должно быть от 2 до 25 символов.")
        return TITLE
    if re.search(r'http[s]?://', val):
        await update.message.reply_text("❌ Название не должно содержать ссылок.")
        return TITLE

    context.user_data['title'] = val
    await update.message.reply_text("5️⃣ Введите **Категорию** (жанр игры):")
    return CATEGORY

async def get_version(update: Update, context: ContextTypes.DEFAULT_TYPE):
    val = update.message.text
    pattern = r'^[0-9ABCV._\-betaAlphaRelease ]+$'
    if not re.match(pattern, val):
        await update.message.reply_text("❌ Неверный формат версии! Разрешены цифры, точки, дефисы и слова beta/Alpha/Release.")
        return VERSION
    
    context.user_data['version'] = val
    await update.message.reply_text("➕ Введите ссылки (до 4-х) в формате: `имя = ссылка`.\nНапишите 'Далее' для перехода.")
    return LINKS_BLOCK

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.replace(" ", ""))
        if price < 3 or price > 50000:
            raise ValueError
        context.user_data['price'] = price
        await update.message.reply_text("7️⃣ Введите **Версию игры**:")
        return VERSION
    except:
        await update.message.reply_text("❌ Цена должна быть числом от 3 ₽ до 50 000 ₽.")
        return PRICE

# --- Вспомогательные функции связи ---
async def contact_mod(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("📧 Напишите ваше обращение. Модераторы Zoro Store ответят вам в ближайшее время.")
    context.user_data['waiting_mod'] = True

async def handle_mod_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('waiting_mod'):
        # Здесь отправка сообщения админу (логика пересылки)
        await update.message.reply_text("✅ Ваше сообщение передано в службу поддержки.")
        context.user_data['waiting_mod'] = False
        return

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Заполнение отменено.", reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END

def main():
    # Замени на свой ТОКЕН
    app = Application.builder().token("YOUR_TOKEN").build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_survey, pattern="^start_survey$"),
            CallbackQueryHandler(show_rules, pattern="^show_rules$"),
            CallbackQueryHandler(contact_mod, pattern="^contact_mod$")
        ],
        states={
            LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: (c.user_data.update({'l_name': u.message.text}), u.message.reply_text("2️⃣ Введите **Описание**:"), DESCRIPTION)[2])],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: (c.user_data.update({'desc': u.message.text}), u.message.reply_text("3️⃣ Отправьте **Иконку** (ссылка/файл):"), ICON)[2])],
            ICON: [MessageHandler(filters.ALL & ~filters.COMMAND, lambda u, c: (u.message.reply_text("4️⃣ Введите **Заголовок*** (2-25 симв):"), TITLE)[1])],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)],
            CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, lambda u, c: (c.user_data.update({'cat': u.message.text}), u.message.reply_text("6️⃣ Введите **Цену** (3-50000 ₽):"), PRICE)[2])],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price)],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_version)],
            # ... остальные состояния аналогично ...
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mod_reply))
    
    print("🚀 Бот Zoro Store запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
