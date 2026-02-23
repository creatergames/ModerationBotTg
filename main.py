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
        self.wfile.write(b"ZGS Ultra Engine Active")
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

# --- LOGIC ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 *Zoro Game Store Engine*\nДобро пожаловать! Бот готов к приему заявок.", 
                                   reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def engine(u, c, key, next_s, txt, skip=True):
    # Если нажата кнопка отмены
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": 
        await start(u, c)
        return ConversationHandler.END
    
    # Сохраняем любое входящее сообщение (текст или описание файла)
    if u.message.text == "⏩ ПРОПУСТИТЬ":
        c.user_data[key] = "—"
    else:
        # Принимаем текст, либо помечаем наличие медиафайла
        c.user_data[key] = u.message.text if u.message.text else f"📎 Файл: {u.message.effective_attachment}"

    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

# Шаги
async def st_start(u,c): 
    await u.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu())
    return S1

async def s1(u,c): return await engine(u,c,'q1', S2, "2️⃣ *Описание:*")
async def s2(u,c): return await engine(u,c,'q2', S3, "3️⃣ *Иконка (URL или файл):*")
async def s3(u,c): return await engine(u,c,'q3', S4, "4️⃣ *ЗАГОЛОВОК* (Обязательно):", False)
async def s4(u,c): return await engine(u,c,'q4', S5, "5️⃣ *Категория:*")
async def s5(u,c): return await engine(u,c,'q5', S6, "6️⃣ *Цена (3 - 50 000 ₽):*")
async def s6(u,c): return await engine(u,c,'q6', S7, "7️⃣ *Версия:*")
async def s7(u,c): return await engine(u,c,'q7', S8, "8️⃣ *Ссылка 1 (название = ссылка):*")
async def s8(u,c): return await engine(u,c,'q8', S9, "9️⃣ *Ссылка 2:*")
async def s9(u,c): return await engine(u,c,'q9', S10, "🔟 *Ссылка 3:*")
async def s10(u,c): return await engine(u,c,'q10', S11, "1️⃣1️⃣ *Ссылка 4:*")
async def s11(u,c): return await engine(u,c,'q11', S12, "1️⃣2️⃣ *Примечание к игре:*")
async def s12(u,c): return await engine(u,c,'q12', S13, "1️⃣3️⃣ *Комментарии (TG ссылка/запрос):*")
async def s13(u,c): return await engine(u,c,'q13', S14, "1️⃣4️⃣ *Фоновое изображение (URL/файл):*")
async def s14(u,c): return await engine(u,c,'q14', S15, "1️⃣5️⃣ *Лог последних изменений:*")
async def s15(u,c): return await engine(u,c,'q15', S16, "1️⃣6️⃣ *Файл игры (APK/EXE/Link):*")
async def s16(u,c): return await engine(u,c,'q16', S17, "1️⃣7️⃣ *Иконка игры:*")
async def s17(u,c): return await engine(u,c,'q17', S18, "1️⃣8️⃣ *Скриншоты (до 8 шт):*")
async def s18(u,c): return await engine(u,c,'q18', S19, "1️⃣9️⃣ *Дополнительные файлы и названия:*")

async def final(u,c):
    c.user_data['q19'] = u.message.text if u.message.text else "📎 Приложен файл"
    d = c.user_data
    user = u.effective_user
    
    # КРАСИВЫЙ ОТЧЕТ ИЗ ВСЕХ 19 ПУНКТОВ
    report = (
        f"📩 **ПОЛНАЯ ЗАЯВКА НА МОДЕРАЦИЮ**\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Автор:** @{user.username} (ID: `{user.id}`)\n"
        f"🕹 **Проект:** {d.get('q4')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"1. ID Ссылки: `{d.get('q1')}`\n"
        f"2. Описание: {d.get('q2')}\n"
        f"3. Превью иконка: {d.get('q3')}\n"
        f"5. Категория: {d.get('q5')}\n"
        f"6. Цена: {d.get('q6')} ₽\n"
        f"7. Версия: {d.get('q7')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **Ссылки:**\n"
        f"🔗 Ссылка 1: {d.get('q8')}\n"
        f"🔗 Ссылка 2: {d.get('q9')}\n"
        f"🔗 Ссылка 3: {d.get('q10')}\n"
        f"🔗 Ссылка 4: {d.get('q11')}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💬 Комменты: {d.get('q13')}\n"
        f"🖼 Фон: {d.get('q14')}\n"
        f"🆙 Патч-ноут: {d.get('q15')}\n"
        f"📦 Файл игры: {d.get('q16')}\n"
        f"🔘 Иконка игры: {d.get('q17')}\n"
        f"📸 Скриншоты: {d.get('q18')}\n"
        f"📂 Доп. файлы: {d.get('q19')}\n"
        f"⚠️ Примечание: {d.get('q12')}\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )
    
    await c.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    await u.message.reply_text("🚀 *Ваша заявка из 19 пунктов успешно отправлена!*", 
                               reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# --- SUPPORT ---
async def start_support(u,c):
    await u.message.reply_text("👨‍💻 *Связь с модератором*\nНапишите ваш вопрос ниже:", 
                               reply_markup=survey_menu(False), parse_mode="Markdown")
    return SUPPORT_MODE

async def send_to_moders(u,c):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u,c)
    msg = f"🆘 **ВОПРОС В ПОДДЕРЖКУ**\nОт: @{u.effective_user.username}\nТекст: {u.message.text}"
    await c.bot.send_message(ADMIN_CHAT_ID, msg)
    await u.message.reply_text("✅ Сообщение передано!", reply_markup=main_menu())
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
            S1: [MessageHandler(filters.ALL & ~filters.COMMAND, s1)],
            S2: [MessageHandler(filters.ALL & ~filters.COMMAND, s2)],
            S3: [MessageHandler(filters.ALL & ~filters.COMMAND, s3)],
            S4: [MessageHandler(filters.ALL & ~filters.COMMAND, s4)],
            S5: [MessageHandler(filters.ALL & ~filters.COMMAND, s5)],
            S6: [MessageHandler(filters.ALL & ~filters.COMMAND, s6)],
            S7: [MessageHandler(filters.ALL & ~filters.COMMAND, s7)],
            S8: [MessageHandler(filters.ALL & ~filters.COMMAND, s8)],
            S9: [MessageHandler(filters.ALL & ~filters.COMMAND, s9)],
            S10: [MessageHandler(filters.ALL & ~filters.COMMAND, s10)],
            S11: [MessageHandler(filters.ALL & ~filters.COMMAND, s11)],
            S12: [MessageHandler(filters.ALL & ~filters.COMMAND, s12)],
            S13: [MessageHandler(filters.ALL & ~filters.COMMAND, s13)],
            S14: [MessageHandler(filters.ALL & ~filters.COMMAND, s14)],
            S15: [MessageHandler(filters.ALL & ~filters.COMMAND, s15)],
            S16: [MessageHandler(filters.ALL & ~filters.COMMAND, s16)],
            S17: [MessageHandler(filters.ALL & ~filters.COMMAND, s17)],
            S18: [MessageHandler(filters.ALL & ~filters.COMMAND, s18)],
            S19: [MessageHandler(filters.ALL & ~filters.COMMAND, final)],
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_moders)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
