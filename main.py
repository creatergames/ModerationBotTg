import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"

(LINK_NAME, DESCRIPTION, ICON, TITLE, CATEGORY, PRICE, VERSION) = range(7)

logging.basicConfig(level=logging.INFO)

# --- SERVER FOR RENDER ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine Active")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- КЛАВИАТУРЫ ---
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ZORO STORE (WEB)", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("🚀 ОПУБЛИКОВАТЬ ПРОЕКТ", callback_data="start_survey")],
        [InlineKeyboardButton("📜 ПРАВИЛА", callback_data="show_rules"), InlineKeyboardButton("💡 ИДЕИ СЕРВИСА", callback_data="show_ideas")],
        [InlineKeyboardButton("👨‍💻 ПОДДЕРЖКА", callback_data="contact_mod")]
    ])

def get_survey_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➡️ ПРОПУСТИТЬ", callback_data="skip")],
        [InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel_conv")]
    ])

# --- ОБРАБОТЧИКИ МОДЕРАЦИИ ---

async def handle_moderation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    action, user_id, game_name = query.data.split("|")
    await query.answer()

    if action == "approve":
        text = f"✅ **ОДОБРЕНО**\nПроект: {game_name}\nМодератор: @{query.from_user.username}"
        await context.bot.send_message(user_id, f"🎉 **Поздравляем!** Твой проект *{game_name}* прошел модерацию и опубликован!")
    else:
        text = f"❌ **ОТКЛОНЕНО**\nПроект: {game_name}\nМодератор: @{query.from_user.username}"
        await context.bot.send_message(user_id, f"⚠️ **Увы!** Проект *{game_name}* отклонен. Проверь правила и попробуй снова.")

    await query.message.edit_text(text, parse_mode="Markdown")

# --- ОСНОВНАЯ ЛОГИКА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💎 **ZORO GAME STORE**\n\nМесто, где инди-легенды обретают жизнь. Публикуй, играй, создавай.\n\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯"
    if update.message:
        await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("1️⃣ **ID (Ссылка):**\nНапиши латиницей название для URL.", reply_markup=get_survey_kb(), parse_mode="Markdown")
    return LINK_NAME

async def get_link_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['link_name'] = update.message.text if update.message else "game-id"
    await update.effective_message.reply_text("2️⃣ **ОПИСАНИЕ:**\nСуть твоей игры?", reply_markup=get_survey_kb(), parse_mode="Markdown")
    return DESCRIPTION

async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['description'] = update.message.text if update.message else "N/A"
    await update.effective_message.reply_text("4️⃣ **ЗАГОЛОВОК:**\nКрасивое название проекта.", reply_markup=get_survey_kb(), parse_mode="Markdown")
    return TITLE

async def get_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['title'] = update.message.text if update.message else "Unnamed"
    await update.effective_message.reply_text("6️⃣ **ЦЕНА:**\nЧисло в рублях или 0.", reply_markup=get_survey_kb(), parse_mode="Markdown")
    return PRICE

async def get_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['price'] = update.message.text if update.message else "0"
    await update.effective_message.reply_text("7️⃣ **ВЕРСИЯ:**\nПример: 1.0.0", reply_markup=get_survey_kb(), parse_mode="Markdown")
    return VERSION

async def finish_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['version'] = update.message.text if update.message else "1.0"
    user = update.effective_user
    game = context.user_data.get('title')

    # Клавиатура модерации для админ-группы
    mod_kb = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Одобрить", callback_data=f"approve|{user.id}|{game}"),
            InlineKeyboardButton("❌ Отклонить", callback_data="reject|{user.id}|{game}")
        ]
    ])

    report = (
        f"📩 **ЗАЯВКА НА ПУБЛИКАЦИЮ**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎮 **Игра:** {game}\n"
        f"💰 **Цена:** {context.user_data.get('price')} ₽\n"
        f"📊 **Версия:** {context.user_data.get('version')}\n"
        f"👤 **Автор:** @{user.username} (ID: `{user.id}`)\n"
        f"━━━━━━━━━━━━━━"
    )

    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=report, reply_markup=mod_kb, parse_mode="Markdown")
    await update.effective_message.reply_text("✅ **Заявка на рассмотрении!**\nМы сообщим результат в течение 24 часов.", reply_markup=get_main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("🛑 **ОТМЕНЕНО**", reply_markup=get_main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link_name), CallbackQueryHandler(get_link_name, pattern="^skip$")],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description), CallbackQueryHandler(get_description, pattern="^skip$")],
            TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title), CallbackQueryHandler(get_title, pattern="^skip$")],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price), CallbackQueryHandler(get_price, pattern="^skip$")],
            VERSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish_survey), CallbackQueryHandler(finish_survey, pattern="^skip$")],
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel_conv$")],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^back_to_start$"))
    app.add_handler(CallbackQueryHandler(handle_moderation, pattern="^(approve|reject)\|"))
    app.add_handler(conv_handler)

    print("🚀 Zoro Engine Flying...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
