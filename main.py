import logging
import os
import threading
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
)

# --- CONFIGURATION ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"

# States 1-19
(L_LINK, L_DESC, L_ICON, L_TITLE, L_CAT, L_PRICE, L_VER, 
 L_URL1, L_URL2, L_URL3, L_URL4, L_NOTE, L_COMM, L_BG, L_CHNG, 
 L_FILE, L_GAME_ICON, L_SCRINS, L_ADDF) = range(19)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- ULTRA-FAST HEALTH SERVER ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"ZGS Engine v4.0: Super-Sonic")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthServer)
    server.serve_forever()

# --- UI COMPONENTS ---
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ZORO STORE (WEB)", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        [InlineKeyboardButton("🚀 ОПУБЛИКОВАТЬ ПРОЕКТ", callback_data="start_survey")],
        [InlineKeyboardButton("📋 ПОЛНЫЕ ПРАВИЛА", callback_data="show_rules")],
        [InlineKeyboardButton("👨‍💻 ТЕХ. ПОДДЕРЖКА", callback_data="contact_mod")]
    ])

def get_survey_kb(can_skip=True):
    btns = []
    if can_skip: btns.append(InlineKeyboardButton("⏩ ПРОПУСТИТЬ", callback_data="skip"))
    btns.append(InlineKeyboardButton("❌ ОТМЕНА", callback_data="cancel"))
    return InlineKeyboardMarkup([btns])

# --- LOGIC & STEPS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎮 *Zoro Game Store*\n\nБот работает в режиме 24/7. Начните заполнение анкеты (19 вопросов)."
    if update.message: await update.message.reply_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    else: await update.callback_query.message.edit_text(text, reply_markup=get_main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer()
    await update.callback_query.message.edit_text("1️⃣ *Название для ссылки:*", reply_markup=get_survey_kb(), parse_mode="Markdown")
    return L_LINK

# Универсальный контроллер переходов
async def flow(update, context, key, next_st, next_txt, can_skip=True):
    val = update.message.text if (update.message and update.message.text) else "Пропущено/Файл"
    context.user_data[key] = val
    msg = update.message.reply_text if update.message else update.callback_query.message.edit_text
    await msg(next_txt, reply_markup=get_survey_kb(can_skip), parse_mode="Markdown")
    return next_st

# Цепочка вопросов
async def st1(u,c): return await flow(u,c,'link', L_DESC, "2️⃣ *Описание:*")
async def st2(u,c): return await flow(u,c,'desc', L_ICON, "3️⃣ *Иконку (URL):*")
async def st3(u,c): return await flow(u,c,'icon', L_TITLE, "4️⃣ *Заголовок* (ОБЯЗАТЕЛЬНО)*:", False)
async def st4(u,c): 
    if not u.message or not u.message.text: return L_TITLE
    return await flow(u,c,'title', L_CAT, "5️⃣ *Категория:*")
async def st5(u,c): return await flow(u,c,'cat', L_PRICE, "6️⃣ *Цена:*")
async def st6(u,c): return await flow(u,c,'price', L_VER, "7️⃣ *Версия:*")
async def st7(u,c): return await flow(u,c,'ver', L_URL1, "8️⃣ *Ссылка 1* (название = ссылка):")
async def st8(u,c): return await flow(u,c,'u1', L_URL2, "9️⃣ *Ссылка 2* (название = ссылка):")
async def st9(u,c): return await flow(u,c,'u2', L_URL3, "🔟 *Ссылка 3* (название = ссылка):")
async def st10(u,c): return await flow(u,c,'u3', L_URL4, "1️⃣1️⃣ *Ссылка 4* (название = ссылка):")
async def st11(u,c): return await flow(u,c,'u4', L_NOTE, "1️⃣2️⃣ *Примечание к игре:*")
async def st12(u,c): return await flow(u,c,'note', L_COMM, "1️⃣3️⃣ *Комментарии* (Ссылка или запрос):")
async def st13(u,c): return await flow(u,c,'comm', L_BG, "1️⃣4️⃣ *Фоновое изображение* (URL):")
async def st14(u,c): return await flow(u,c,'bg', L_CHNG, "1️⃣5️⃣ *Описание последних изменений:*")
async def st15(u,c): return await flow(u,c,'chng', L_FILE, "1️⃣6️⃣ *Файл игры* (APK/EXE/HTML):")
async def st16(u,c): return await flow(u,c,'file', L_GAME_ICON, "1️⃣7️⃣ *Иконка игры:*")
async def st17(u,c): return await flow(u,c,'g_ico', L_SCRINS, "1️⃣8️⃣ *Скриншоты* (до 8 шт):")
async def st18(u,c): return await flow(u,c,'scrs', L_ADDF, "1️⃣9️⃣ *Доп. файлы и их названия:*")

async def finish(update, context):
    context.user_data['addf'] = update.message.text if update.message else "Нет"
    d = context.user_data
    report = (
        f"📩 **ПОЛНАЯ ЗАЯВКА ZGS**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🕹 **Игра:** {d.get('title')}\n"
        f"📝 **Описание:** {d.get('desc')}\n"
        f"💰 **Цена:** {d.get('price')} ₽ | 📊 **Версия:** {d.get('ver')}\n"
        f"🌐 **ID:** {d.get('link')}\n"
        f"👤 **Автор:** @{update.effective_user.username}\n"
        f"━━━━━━━━━━━━━━"
    )
    await context.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    m = update.message.reply_text if update.message else update.callback_query.message.edit_text
    await m("🚀 *Готово! Заявка отправлена.*", reply_markup=get_main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# --- APP RUNNER ---
def main():
    # Запуск сервера для Render
    threading.Thread(target=run_server, daemon=True).start()

    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_survey, pattern="^start_survey$")],
        states={
            L_LINK: [MessageHandler(filters.ALL, st1), CallbackQueryHandler(st1, pattern="^skip$")],
            L_DESC: [MessageHandler(filters.ALL, st2), CallbackQueryHandler(st2, pattern="^skip$")],
            L_ICON: [MessageHandler(filters.ALL, st3), CallbackQueryHandler(st3, pattern="^skip$")],
            L_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, st4)],
            L_CAT: [MessageHandler(filters.ALL, st5), CallbackQueryHandler(st5, pattern="^skip$")],
            L_PRICE: [MessageHandler(filters.ALL, st6), CallbackQueryHandler(st6, pattern="^skip$")],
            L_VER: [MessageHandler(filters.ALL, st7), CallbackQueryHandler(st7, pattern="^skip$")],
            L_URL1: [MessageHandler(filters.ALL, st8), CallbackQueryHandler(st8, pattern="^skip$")],
            L_URL2: [MessageHandler(filters.ALL, st9), CallbackQueryHandler(st9, pattern="^skip$")],
            L_URL3: [MessageHandler(filters.ALL, st10), CallbackQueryHandler(st10, pattern="^skip$")],
            L_URL4: [MessageHandler(filters.ALL, st11), CallbackQueryHandler(st11, pattern="^skip$")],
            L_NOTE: [MessageHandler(filters.ALL, st12), CallbackQueryHandler(st12, pattern="^skip$")],
            L_COMM: [MessageHandler(filters.ALL, st13), CallbackQueryHandler(st13, pattern="^skip$")],
            L_BG: [MessageHandler(filters.ALL, st14), CallbackQueryHandler(st14, pattern="^skip$")],
            L_CHNG: [MessageHandler(filters.ALL, st15), CallbackQueryHandler(st15, pattern="^skip$")],
            L_FILE: [MessageHandler(filters.ALL, st16), CallbackQueryHandler(st16, pattern="^skip$")],
            L_GAME_ICON: [MessageHandler(filters.ALL, st17), CallbackQueryHandler(st17, pattern="^skip$")],
            L_SCRINS: [MessageHandler(filters.ALL, st18), CallbackQueryHandler(st18, pattern="^skip$")],
            L_ADDF: [MessageHandler(filters.ALL, finish), CallbackQueryHandler(finish, pattern="^skip$")],
        },
        fallbacks=[CallbackQueryHandler(start, pattern="^cancel$")]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(start, pattern="^cancel$"))
    app.add_handler(conv)

    print("🚀 ZGS BOOTED")
    # drop_pending_updates=True ЛЕЧИТ ОШИБКУ CONFLICT ПРИ ПЕРЕЗАПУСКЕ
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
