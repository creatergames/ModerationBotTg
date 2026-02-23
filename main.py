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
WEB_APP_URL = "https://zoro-game.store/"

# 19 States + Support
(S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, SUPPORT_MODE) = range(20)

logging.basicConfig(level=logging.INFO)

class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine Ready")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- UI ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ ZGS MINI APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def survey_menu(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ВЕРНУТЬСЯ В МЕНЮ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- HANDLERS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 *Zoro Game Store Engine*\nБот активирован и готов к работе.", 
                                   reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def show_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = (
        "Приложение должно не нарушать конституцию РФ\n"
        "9. Плакат\nЗагрузите изображение w164px h256px. Это изображение будет представлено на странице вашей игры.\n"
        "Не должна содержать авторский контент\nНе должно изображать: порнографию, ссылки или изображения и текст запрещённый конструкции РФ\n"
        "10. Цена\nЦена не должна превышать 50 000 ₽\nЦена не должна быть ниже 3 ₽\n"
        "11. Название ссылок\nНе должно иметь заблуждающие пользователя\n"
        "12. Ссылки\nНе должно вести на несуществующие источники. Не должны вести на экстремистские сайты такие как платформы Meta*.\n"
        "Не должно вести на страницу которая нарушает законы РФ. За то что находится на странице мы не несём ответственность\n\n"
        "Дополнительные файлы\nЭто может быть любой формат файлов. Размер файла не должен превышать 100 гигабайт.\n"
        "не должны содержать вирусов, вредоносного ПО. Рекомендуется предоставить отчет о тестировании.\n"
        "Приложение должно не нарушать конституцию РФ\n\n"
        "Следуйте этим правилам, чтобы обеспечить успешное размещение.\n*принадлежит запрещенной в РФ Meta"
    )
    await update.message.reply_text(rules)

async def engine(u, c, key, next_s, txt, skip=True):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": 
        await start(u, c)
        return ConversationHandler.END
    
    # Принимаем всё: текст, фото, файлы
    if u.message.text == "⏩ ПРОПУСТИТЬ":
        c.user_data[key] = "—"
    else:
        c.user_data[key] = u.message.text if u.message.text else "📎 Приложен медиафайл"

    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

# Анкета
async def st_start(u,c): 
    await u.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu())
    return S1

async def s1(u,c): return await engine(u,c,'q1', S2, "2️⃣ *Описание:*")
async def s2(u,c): return await engine(u,c,'q2', S3, "3️⃣ *Иконка (URL/Файл):*")
async def s3(u,c): return await engine(u,c,'q3', S4, "4️⃣ *ЗАГОЛОВОК* (ОБЯЗАТЕЛЬНО):", False)
async def s4(u,c): return await engine(u,c,'q4', S5, "5️⃣ *Категория:*")
async def s5(u,c): return await engine(u,c,'q5', S6, "6️⃣ *Цена (3 - 50 000 ₽):*")
async def s6(u,c): return await engine(u,c,'q6', S7, "7️⃣ *Версия:*")
async def s7(u,c): return await engine(u,c,'q7', S8, "8️⃣ *Ссылка 1:*")
async def s8(u,c): return await engine(u,c,'q8', S9, "9️⃣ *Ссылка 2:*")
async def s9(u,c): return await engine(u,c,'q9', S10, "🔟 *Ссылка 3:*")
async def s10(u,c): return await engine(u,c,'q10', S11, "1️⃣1️⃣ *Ссылка 4:*")
async def s11(u,c): return await engine(u,c,'q11', S12, "1️⃣2️⃣ *Примечание:*")
async def s12(u,c): return await engine(u,c,'q12', S13, "1️⃣3️⃣ *Комментарии:*")
async def s13(u,c): return await engine(u,c,'q13', S14, "1️⃣4️⃣ *Фоновое изображение:*")
async def s14(u,c): return await engine(u,c,'q14', S15, "1️⃣5️⃣ *Лог изменений:*")
async def s15(u,c): return await engine(u,c,'q15', S16, "1️⃣6️⃣ *Файл игры:*")
async def s16(u,c): return await engine(u,c,'q16', S17, "1️⃣7️⃣ *Иконка игры:*")
async def s17(u,c): return await engine(u,c,'q17', S18, "1️⃣8️⃣ *Скриншоты:*")
async def s18(u,c): return await engine(u,c,'q18', S19, "1️⃣9️⃣ *Доп. файлы и названия:*")

async def final(u,c):
    c.user_data['q19'] = u.message.text if u.message.text else "📎 Файл"
    d = c.user_data
    report = (
        f"📩 **НОВАЯ ЗАЯВКА (19 ПУНКТОВ)**\n━━━━━━━━━━━━━━\n"
        f"👤 От: @{u.effective_user.username}\n🕹 Проект: {d.get('q4')}\n"
        f"1. ID: {d.get('q1')}\n2. Описание: {d.get('q2')}\n3. Превью: {d.get('q3')}\n"
        f"5. Кат: {d.get('q5')}\n6. Цена: {d.get('q6')}\n7. Вер: {d.get('q7')}\n"
        f"🌐 Ссылки: {d.get('q8')}, {d.get('q9')}, {d.get('q10')}, {d.get('q11')}\n"
        f"💬 Комм: {d.get('q13')}\n🖼 Фон: {d.get('q14')}\n🆙 Лог: {d.get('q15')}\n"
        f"📦 Файл: {d.get('q16')}\n🔘 Иконка: {d.get('q17')}\n📸 Скрины: {d.get('q18')}\n"
        f"📂 Доп: {d.get('q19')}\n⚠️ Прим: {d.get('q12')}\n━━━━━━━━━━━━━━"
    )
    await c.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    await u.message.reply_text("🚀 *Заявка отправлена модераторам!*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_support(u,c):
    await u.message.reply_text("👨‍💻 *Напишите сообщение модератору:*", reply_markup=survey_menu(False))
    return SUPPORT_MODE

async def send_to_moders(u,c):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u,c)
    await c.bot.send_message(ADMIN_CHAT_ID, f"🆘 **СВЯЗЬ**\nОт: @{u.effective_user.username}\n{u.message.text}")
    await u.message.reply_text("✅ Отправлено!", reply_markup=main_menu())
    return ConversationHandler.END

# --- RUN ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), st_start),
            MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_support)
        ],
        states={
            S1: [MessageHandler(filters.ALL & ~filters.COMMAND, s1)], S2: [MessageHandler(filters.ALL & ~filters.COMMAND, s2)],
            S3: [MessageHandler(filters.ALL & ~filters.COMMAND, s3)], S4: [MessageHandler(filters.ALL & ~filters.COMMAND, s4)],
            S5: [MessageHandler(filters.ALL & ~filters.COMMAND, s5)], S6: [MessageHandler(filters.ALL & ~filters.COMMAND, s6)],
            S7: [MessageHandler(filters.ALL & ~filters.COMMAND, s7)], S8: [MessageHandler(filters.ALL & ~filters.COMMAND, s8)],
            S9: [MessageHandler(filters.ALL & ~filters.COMMAND, s9)], S10: [MessageHandler(filters.ALL & ~filters.COMMAND, s10)],
            S11: [MessageHandler(filters.ALL & ~filters.COMMAND, s11)], S12: [MessageHandler(filters.ALL & ~filters.COMMAND, s12)],
            S13: [MessageHandler(filters.ALL & ~filters.COMMAND, s13)], S14: [MessageHandler(filters.ALL & ~filters.COMMAND, s14)],
            S15: [MessageHandler(filters.ALL & ~filters.COMMAND, s15)], S16: [MessageHandler(filters.ALL & ~filters.COMMAND, s16)],
            S17: [MessageHandler(filters.ALL & ~filters.COMMAND, s17)], S18: [MessageHandler(filters.ALL & ~filters.COMMAND, s18)],
            S19: [MessageHandler(filters.ALL & ~filters.COMMAND, final)],
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_moders)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 ПРАВИЛА$"), show_rules))
    app.add_handler(conv)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
