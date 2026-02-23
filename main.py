import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters
)

# --- НАСТРОЙКИ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"
# Проверь эту ссылку! Если Vercel выдает 404, значит проект нужно передеплоить или сменить URL.
WEB_APP_URL = "https://zoro-game.store/" 

# Состояния
(S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, SUPPORT_MODE) = range(20)

logging.basicConfig(level=logging.INFO)

# --- СЕРВЕР ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine: Running")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- ПОЛНЫЙ ТЕКСТ ПРАВИЛ ---
RULES_TEXT = """
9. Плакат
Загрузите изображение w164px h256px. Это изображение будет представлено на странице вашей игры.
Не должна содержать авторский контент
Не должно изображать: порнографию, ссылки или изображения и текст запрещённый конструкции РФ

10. Цена
Цена не должна превышать 50 000 ₽
Цена не должна быть ниже 3 ₽

11. Название ссылок
Не должно иметь заблуждающие пользователя

12. Ссылки
Не должно ввести на несуществующие источники.
Не должны вести на экстремистские сайты такие как платформы Meta*.
Не должно вести на страницу которая нарушает законы РФ.
За то что находится на странице мы не несём ответственность

Дополнительные файлы
Это может быть любой формат файлов
Размер файла не должен превышать 100 гигабайт.
не должны содержать вирусов, вредоносного ПО или шпионского программного обеспечения.
не должны содержать оскорбительного контента, шокирующий контент или темы, которые могут быть расценены как дискриминационные.
Рекомендуется предоставить отчет о тестировании с указанием найденных ошибок и исправлений.
Приложение должно не нарушать конституцию РФ

Следуйте этим правилам, чтобы обеспечить успешное размещение вашего приложения в магазине.

*принадлежит запрещенной в РФ Meta
"""

# --- МЕНЮ ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ MINI APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def survey_menu(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ВЕРНУТЬСЯ В МЕНЮ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 *Zoro Game Store*\nМеню открыто. Бот готов к работе.", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)

async def start_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Напишите ваше сообщение модератору:", reply_markup=survey_menu(False))
    return SUPPORT_MODE

async def send_to_moders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(update, context)
    msg = f"📩 **ПОДДЕРЖКА**\nОт: @{update.effective_user.username}\nТекст: {update.message.text}"
    await context.bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")
    await update.message.reply_text("✅ Отправлено!", reply_markup=main_menu())
    return ConversationHandler.END

# --- ЦЕПОЧКА АНКЕТЫ ---
async def engine(u, c, key, next_s, txt, skip=True):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u, c)
    c.user_data[key] = u.message.text if u.message.text != "⏩ ПРОПУСТИТЬ" else "—"
    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

async def st_start(u,c): 
    await u.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu())
    return S1

async def s1(u,c): return await engine(u,c,'link', S2, "2️⃣ *Описание:*")
async def s2(u,c): return await engine(u,c,'desc', S3, "3️⃣ *Иконка:*")
async def s3(u,c): return await engine(u,c,'icon', S4, "4️⃣ *Заголовок* (ОБЯЗАТЕЛЬНО):", False)
async def s4(u,c): return await engine(u,c,'title', S5, "5️⃣ *Категория:*")
async def s5(u,c): return await engine(u,c,'cat', S6, "6️⃣ *Цена:*")
async def s6(u,c): return await engine(u,c,'price', S7, "7️⃣ *Версия:*")
async def s7(u,c): return await engine(u,c,'ver', S8, "8️⃣ *Ссылка 1:*")
async def s8(u,c): return await engine(u,c,'u1', S9, "9️⃣ *Ссылка 2:*")
async def s9(u,c): return await engine(u,c,'u2', S10, "🔟 *Ссылка 3:*")
async def s10(u,c): return await engine(u,c,'u3', S11, "1️⃣1️⃣ *Ссылка 4:*")
async def s11(u,c): return await engine(u,c,'u4', S12, "1️⃣2️⃣ *Примечание:*")
async def s12(u,c): return await engine(u,c,'note', S13, "1️⃣3️⃣ *Комментарии:*")
async def s13(u,c): return await engine(u,c,'comm', S14, "1️⃣4️⃣ *Фон (URL):*")
async def s14(u,c): return await engine(u,c,'bg', S15, "1️⃣5️⃣ *Лог изменений:*")
async def s15(u,c): return await engine(u,c,'chng', S16, "1️⃣6️⃣ *Файл игры:*")
async def s16(u,c): return await engine(u,c,'file', S17, "1️⃣7️⃣ *Иконка игры:*")
async def s17(u,c): return await engine(u,c,'gico', S18, "1️⃣8️⃣ *Скриншоты:*")
async def s18(u,c): return await engine(u,c,'scrs', S19, "1️⃣9️⃣ *Доп. файлы:*")

async def final(u,c):
    c.user_data['addf'] = u.message.text
    d = c.user_data
    res = f"🎁 **ЗАЯВКА**\nИмя: {d.get('title')}\nЦена: {d.get('price')}\nВерсия: {d.get('ver')}\nАвтор: @{u.effective_user.username}"
    await c.bot.send_message(ADMIN_CHAT_ID, res)
    await u.message.reply_text("✅ Заявка отправлена!", reply_markup=main_menu())
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), st_start),
            MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_support)
        ],
        states={
            S1: [MessageHandler(filters.TEXT & ~filters.COMMAND, s1)], S2: [MessageHandler(filters.TEXT & ~filters.COMMAND, s2)],
            S3: [MessageHandler(filters.TEXT & ~filters.COMMAND, s3)], S4: [MessageHandler(filters.TEXT & ~filters.COMMAND, s4)],
            S5: [MessageHandler(filters.TEXT & ~filters.COMMAND, s5)], S6: [MessageHandler(filters.TEXT & ~filters.COMMAND, s6)],
            S7: [MessageHandler(filters.TEXT & ~filters.COMMAND, s7)], S8: [MessageHandler(filters.TEXT & ~filters.COMMAND, s8)],
            S9: [MessageHandler(filters.TEXT & ~filters.COMMAND, s9)], S10: [MessageHandler(filters.TEXT & ~filters.COMMAND, s10)],
            S11: [MessageHandler(filters.TEXT & ~filters.COMMAND, s11)], S12: [MessageHandler(filters.TEXT & ~filters.COMMAND, s12)],
            S13: [MessageHandler(filters.TEXT & ~filters.COMMAND, s13)], S14: [MessageHandler(filters.TEXT & ~filters.COMMAND, s14)],
            S15: [MessageHandler(filters.TEXT & ~filters.COMMAND, s15)], S16: [MessageHandler(filters.TEXT & ~filters.COMMAND, s16)],
            S17: [MessageHandler(filters.TEXT & ~filters.COMMAND, s17)], S18: [MessageHandler(filters.TEXT & ~filters.COMMAND, s18)],
            S19: [MessageHandler(filters.TEXT & ~filters.COMMAND, final)],
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_moders)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 ПРАВИЛА$"), show_rules))
    app.add_handler(conv)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
