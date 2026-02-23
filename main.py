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

# Состояния анкеты (расширенные)
(L_LINK, L_DESC, L_ICON, L_TITLE, L_CAT, L_PRICE, L_VER, 
 L_URL1, L_URL2, L_URL3, L_URL4, L_NOTE, L_COMM, L_BG, L_CHNG, L_FILE, L_GAME_ICON, L_SCRINS, L_ADDF) = range(19)

logging.basicConfig(level=logging.INFO)

# --- SERVER FOR RENDER (FAST) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine Running")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- ТЕКСТЫ ---
RULES_TEXT = """
*Tevs.service*
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
📍 Омск, Россия
📞 (+7) (951) 402-40-88
📧 zorogamestoresup@gmail.com
📅 20 янв. 2026 г.

*ОСНОВНЫЕ КРИТЕРИИ ZGS:*
1. **Название:** 2-25 символов, без мата, ссылок и спецсимволов в начале.
2. **Разработчик:** Имя студии или ваш ZOid.
3. **Медиа:** Обложка 16:9, Плакат 164x256px, до 8 скриншотов. Без авторского контента и шок-контента.
4. **Версия:** Числа, точки, и слова: beta, Alpha, Release.
5. **Файлы:** APK, EXE, HTML до 100 ГБ. Без вирусов!
6. **Цена:** От 3 ₽ до 50 000 ₽.
7. **Ссылки:** Запрещены ссылки на Meta (Instagram/FB), экстремистские и несуществующие ресурсы.

*Полный список правил доступен при заполнении заявки.*
"""

# --- КЛАВИАТУРЫ ---
def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ZORO STORE", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("🚀 ОПУБЛИКОВАТЬ ИГРУ", callback_data="start_survey")],
        [InlineKeyboardButton("📋 ПРАВИЛА", callback_data="show_rules"), InlineKeyboardButton("👨‍💻 ПОДДЕРЖКА", callback_data="contact_mod")]
    ])

def survey_kb(can_skip=True):
    buttons = []
    if can_skip: buttons.append(InlineKeyboardButton("⏩ ПРОПУСТИТЬ", callback_data="skip"))
    buttons.append(InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel"))
    return InlineKeyboardMarkup([buttons])

# --- ЛОГИКА ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = "🎮 *Zoro Game Store*\n\nДобро пожаловать! Опубликуйте свою игру, следуя строгим критериям качества."
    if update.message: await update.message.reply_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(txt, reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("1️⃣ *Название для ссылки:*", reply_markup=survey_kb(), parse_mode="Markdown")
    return L_LINK

# Универсальный обработчик шагов для экономии места и скорости
async def ask_step(update: Update, context: ContextTypes.DEFAULT_TYPE, next_state, text, can_skip=True):
    key = update.message.text if update.message else "Пропущено"
    state_map = {L_LINK: 'link', L_DESC: 'desc', L_ICON: 'icon', L_TITLE: 'title', L_CAT: 'cat', L_PRICE: 'price', L_VER: 'ver'}
    # (Здесь логика сохранения данных)
    if update.message:
        await update.message.reply_text(text, reply_markup=survey_kb(can_skip), parse_mode="Markdown")
    else:
        await update.callback_query.message.edit_text(text, reply_markup=survey_kb(can_skip), parse_mode="Markdown")
    return next_state

# Примеры конкретных шагов (Заголовок нельзя пропустить по твоему запросу)
async def get_link(update, context): context.user_data['l_link'] = update.message.text; return await ask_step(update, context, L_DESC, "2️⃣ *Описание:*")
async def get_desc(update, context): context.user_data['l_desc'] = update.message.text; return await ask_step(update, context, L_ICON, "3️⃣ *Иконку (URL):*")
async def get_icon(update, context): context.user_data['l_icon'] = update.message.text; return await ask_step(update, context, L_TITLE, "4️⃣ *Заголовок (ОБЯЗАТЕЛЬНО):*", False)
async def get_title(update, context): 
    if not update.message or len(update.message.text) < 2: 
        await update.message.reply_text("❌ Заголовок слишком короткий!"); return L_TITLE
    context.user_data['l_title'] = update.message.text
    return await ask_step(update, context, L_CAT, "5️⃣ *Категория:*")

async def get_cat(update, context): context.user_data['l_cat'] = update.message.text; return await ask_step(update, context, L_PRICE, "6️⃣ *Цена:*")
async def get_price(update, context): context.user_data['l_price'] = update.message.text; return await ask_step(update, context, L_VER, "7️⃣ *Версия:*")

async def finish(update, context):
    context.user_data['l_ver'] = update.message.text if update.message else "1.0"
    res = (f"🎁 *НОВАЯ ЗАЯВКА*\n\n"
           f"🎮 Имя: {context.user_data.get('l_title')}\n"
           f"🔗 ID: {context.user_data.get('l_link')}\n"
           f"💰 Цена: {context.user_data.get('l_price')} ₽\n"
           f"👤 Автор: @{update.effective_user.username}")
    
    await context.bot.send_message(ADMIN_CHAT_ID, res, parse_mode="Markdown")
    await (update.message.reply_text if update.message else update.callback_query.message.edit_text)("✅ *Заявка отправлена!*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            L_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link), CallbackQueryHandler(get_link, pattern="^skip$")],
            L_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_desc), CallbackQueryHandler(get_desc, pattern="^skip$")],
            L_ICON: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_icon), CallbackQueryHandler(get_icon, pattern="^skip$")],
            L_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_title)], # Без пропуска
            L_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_cat), CallbackQueryHandler(get_cat, pattern="^skip$")],
            L_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price), CallbackQueryHandler(get_price, pattern="^skip$")],
            L_VER: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish), CallbackQueryHandler(finish, pattern="^skip$")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^cancel$")]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(lambda u,c: u.callback_query.message.edit_text(RULES_TEXT, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="cancel")]]), parse_mode="Markdown"), pattern="^show_rules$"))
    app.add_handler(conv)

    print("🚀 ZGS FLIES ON RENDER...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
