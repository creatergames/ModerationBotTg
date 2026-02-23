import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters
)

# --- CONFIG ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"

# 19 Состояний
(STEP1, STEP2, STEP3, STEP4, STEP5, STEP6, STEP7, STEP8, STEP9, STEP10,
 STEP11, STEP12, STEP13, STEP14, STEP15, STEP16, STEP17, STEP18, STEP19) = range(19)

logging.basicConfig(level=logging.INFO)

# --- SERVER FOR RENDER ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Full Engine: Active")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- KEYBOARDS ---
def main_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ ZGS MINI APP", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def survey_kb(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ОТМЕНИТЬ ЗАПОЛНЕНИЕ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- SURVEY LOGIC ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 *Zoro Game Store v6.0*\nВсе 19 вопросов анкеты готовы.", reply_markup=main_kb(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_kb(), parse_mode="Markdown")
    return STEP1

async def flow(update, context, key, next_step, text, can_skip=True):
    val = update.message.text
    if val == "❌ ОТМЕНИТЬ ЗАПОЛНЕНИЕ":
        await update.message.reply_text("🛑 Заполнение отменено.", reply_markup=main_kb())
        return ConversationHandler.END
    context.user_data[key] = "—" if val == "⏩ ПРОПУСТИТЬ" else val
    await update.message.reply_text(text, reply_markup=survey_kb(can_skip), parse_mode="Markdown")
    return next_step

# Регистрация всех шагов
async def s1(u,c): return await flow(u,c, 'l_link', STEP2, "2️⃣ *Описание:*")
async def s2(u,c): return await flow(u,c, 'l_desc', STEP3, "3️⃣ *Иконка (URL):*")
async def s3(u,c): return await flow(u,c, 'l_icon', STEP4, "4️⃣ *Заголовок* (ОБЯЗАТЕЛЬНО)*:", False)
async def s4(u,c): return await flow(u,c, 'l_title', STEP5, "5️⃣ *Категория:*")
async def s5(u,c): return await flow(u,c, 'l_cat', STEP6, "6️⃣ *Цена:*")
async def s6(u,c): return await flow(u,c, 'l_price', STEP7, "7️⃣ *Версия:*")
async def s7(u,c): return await flow(u,c, 'l_ver', STEP8, "8️⃣ *Ссылка 1 (название = ссылка):*")
async def s8(u,c): return await flow(u,c, 'l_u1', STEP9, "9️⃣ *Ссылка 2:*")
async def s9(u,c): return await flow(u,c, 'l_u2', STEP10, "🔟 *Ссылка 3:*")
async def s10(u,c): return await flow(u,c, 'l_u3', STEP11, "1️⃣1️⃣ *Ссылка 4:*")
async def s11(u,c): return await flow(u,c, 'l_u4', STEP12, "1️⃣2️⃣ *Примечание к игре:*")
async def s12(u,c): return await flow(u,c, 'l_note', STEP13, "1️⃣3️⃣ *Комментарии (ТГ ссылка или запрос):*")
async def s13(u,c): return await flow(u,c, 'l_comm', STEP14, "1️⃣4️⃣ *Фоновое изображение (URL):*")
async def s14(u,c): return await flow(u,c, 'l_bg', STEP15, "1️⃣5️⃣ *Описание последних изменений:*")
async def s15(u,c): return await flow(u,c, 'l_chng', STEP16, "1️⃣6️⃣ *Файл игры:*")
async def s16(u,c): return await flow(u,c, 'l_file', STEP17, "1️⃣7️⃣ *Иконка игры:*")
async def s17(u,c): return await flow(u,c, 'l_g_ico', STEP18, "1️⃣8️⃣ *Скриншоты (до 8 шт):*")
async def s18(u,c): return await flow(u,c, 'l_scrs', STEP19, "1️⃣9️⃣ *Дополнительные файлы и их названия (до 8 шт):*")

async def finish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['l_addf'] = update.message.text
    d = context.user_data
    
    # Формируем полный отчет для модерации
    full_report = (
        f"🎁 **НОВАЯ ЗАЯВКА ZGS (19/19)**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🕹 **Игра:** {d.get('l_title')}\n"
        f"🔗 **ID Ссылки:** {d.get('l_link')}\n"
        f"📝 **Описание:** {d.get('l_desc')}\n"
        f"📂 **Категория:** {d.get('l_cat')}\n"
        f"💰 **Цена:** {d.get('l_price')} ₽\n"
        f"📊 **Версия:** {d.get('l_ver')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **Ссылки:**\n1: {d.get('l_u1')}\n2: {d.get('l_u2')}\n3: {d.get('l_u3')}\n4: {d.get('l_u4')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 **Комменты:** {d.get('l_comm')}\n"
        f"🖼 **Фон:** {d.get('l_bg')}\n"
        f"🆙 **Патч-ноут:** {d.get('l_chng')}\n"
        f"📦 **Файл:** {d.get('l_file')}\n"
        f"🖼 **Иконка:** {d.get('l_g_ico')}\n"
        f"📸 **Скрины:** {d.get('l_scrs')}\n"
        f"📁 **Доп. файлы:** {d.get('l_addf')}\n"
        f"⚠️ **Примечание:** {d.get('l_note')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** @{update.effective_user.username}"
    )
    
    await context.bot.send_message(ADMIN_CHAT_ID, full_report, parse_mode="Markdown")
    await update.message.reply_text("🚀 *Заявка укомплектована и отправлена модераторам!*", reply_markup=main_kb(), parse_mode="Markdown")
    return ConversationHandler.END

# --- MAIN ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), start_survey)],
        states={
            STEP1: [MessageHandler(filters.TEXT & ~filters.COMMAND, s1)],
            STEP2: [MessageHandler(filters.TEXT & ~filters.COMMAND, s2)],
            STEP3: [MessageHandler(filters.TEXT & ~filters.COMMAND, s3)],
            STEP4: [MessageHandler(filters.TEXT & ~filters.COMMAND, s4)],
            STEP5: [MessageHandler(filters.TEXT & ~filters.COMMAND, s5)],
            STEP6: [MessageHandler(filters.TEXT & ~filters.COMMAND, s6)],
            STEP7: [MessageHandler(filters.TEXT & ~filters.COMMAND, s7)],
            STEP8: [MessageHandler(filters.TEXT & ~filters.COMMAND, s8)],
            STEP9: [MessageHandler(filters.TEXT & ~filters.COMMAND, s9)],
            STEP10: [MessageHandler(filters.TEXT & ~filters.COMMAND, s10)],
            STEP11: [MessageHandler(filters.TEXT & ~filters.COMMAND, s11)],
            STEP12: [MessageHandler(filters.TEXT & ~filters.COMMAND, s12)],
            STEP13: [MessageHandler(filters.TEXT & ~filters.COMMAND, s13)],
            STEP14: [MessageHandler(filters.TEXT & ~filters.COMMAND, s14)],
            STEP15: [MessageHandler(filters.TEXT & ~filters.COMMAND, s15)],
            STEP16: [MessageHandler(filters.TEXT & ~filters.COMMAND, s16)],
            STEP17: [MessageHandler(filters.TEXT & ~filters.COMMAND, s17)],
            STEP18: [MessageHandler(filters.TEXT & ~filters.COMMAND, s18)],
            STEP19: [MessageHandler(filters.TEXT & ~filters.COMMAND, finish)],
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ОТМЕНИТЬ ЗАПОЛНЕНИЕ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("🚀 ZGS ENGINE V6 STARTED")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
