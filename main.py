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
ADMIN_CHAT_ID = "-1003844600340"  # Группа модерации

# Состояния: 19 шагов анкеты + Режим поддержки
(S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, SUPPORT_MODE) = range(20)

logging.basicConfig(level=logging.INFO)

# --- SERVER FOR RENDER (Мгновенный старт) ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Engine Running")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- КЛАВИАТУРЫ (Для скорости выбраны Reply-кнопки) ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ MINI APP", web_app=WebAppInfo(url="https://zoro-game-store.vercel.app"))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def survey_menu(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ВЕРНУТЬСЯ В МЕНЮ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- ПРЯМАЯ СВЯЗЬ С МОДЕРАТОРАМИ ---
async def start_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📝 *Режим связи с модератором*\nНапишите ваше сообщение ниже, и оно будет передано в группу поддержки.",
        reply_markup=survey_menu(False), parse_mode="Markdown"
    )
    return SUPPORT_MODE

async def send_to_moders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    if text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(update, context)
    
    msg = (f"📩 **СООБЩЕНИЕ В ПОДДЕРЖКУ**\n"
           f"━━━━━━━━━━━━━━\n"
           f"👤 От: {user.first_name} (@{user.username})\n"
           f"🆔 ID: `{user.id}`\n"
           f"💬 Сообщение: {text}")
    
    await context.bot.send_message(ADMIN_CHAT_ID, msg, parse_mode="Markdown")
    await update.message.reply_text("✅ Сообщение отправлено! Модератор скоро ответит вам.", reply_markup=main_menu())
    return ConversationHandler.END

# --- ЛОГИКА АНКЕТЫ (19 ШАГОВ) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎮 *Zoro Game Store*\nВыберите действие:", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_survey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu(), parse_mode="Markdown")
    return S1

async def engine(u, c, key, next_s, txt, skip=True):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u, c)
    c.user_data[key] = "—" if u.message.text == "⏩ ПРОПУСТИТЬ" else u.message.text
    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

# Цепочка мгновенных переходов
async def st1(u,c): return await engine(u,c,'link', S2, "2️⃣ *Описание:*")
async def st2(u,c): return await engine(u,c,'desc', S3, "3️⃣ *Иконка (URL):*")
async def st3(u,c): return await engine(u,c,'icon', S4, "4️⃣ *Заголовок* (Обязательно!):", False)
async def st4(u,c): return await engine(u,c,'title', S5, "5️⃣ *Категория:*")
async def st5(u,c): return await engine(u,c,'cat', S6, "6️⃣ *Цена:*")
async def st6(u,c): return await engine(u,c,'price', S7, "7️⃣ *Версия:*")
async def st7(u,c): return await engine(u,c,'ver', S8, "8️⃣ *Ссылка 1 (название=ссылка):*")
async def st8(u,c): return await engine(u,c,'u1', S9, "9️⃣ *Ссылка 2:*")
async def st9(u,c): return await engine(u,c,'u2', S10, "🔟 *Ссылка 3:*")
async def st10(u,c): return await engine(u,c,'u3', S11, "1️⃣1️⃣ *Ссылка 4:*")
async def st11(u,c): return await engine(u,c,'u4', S12, "1️⃣2️⃣ *Примечание к игре:*")
async def st12(u,c): return await engine(u,c,'note', S13, "1️⃣3️⃣ *Комментарии (ссылка):*")
async def st13(u,c): return await engine(u,c,'comm', S14, "1️⃣4️⃣ *Фоновое изображение (URL):*")
async def st14(u,c): return await engine(u,c,'bg', S15, "1️⃣5️⃣ *Описание изменений:*")
async def st15(u,c): return await engine(u,c,'chng', S16, "1️⃣6️⃣ *Файл игры:*")
async def st16(u,c): return await engine(u,c,'file', S17, "1️⃣7️⃣ *Иконка игры:*")
async def st17(u,c): return await engine(u,c,'g_ico', S18, "1️⃣8️⃣ *Скриншоты (до 8 шт):*")
async def st18(u,c): return await engine(u,c,'scrs', S19, "1️⃣9️⃣ *Доп. файлы и названия:*")

async def final(update, context):
    context.user_data['addf'] = update.message.text
    d = context.user_data
    report = (f"🎁 **ЗАЯВКА (19 ШАГОВ)**\n━━━━━━━━━━━━━━\n"
              f"🕹 **Игра:** {d.get('title')}\n📝 **Описание:** {d.get('desc')}\n"
              f"💰 **Цена:** {d.get('price')} | **Версия:** {d.get('ver')}\n"
              f"📂 **Категория:** {d.get('cat')}\n🌐 **ID:** {d.get('link')}\n"
              f"💬 **Связь:** {d.get('comm')}\n🖼 **Фон:** {d.get('bg')}\n"
              f"📦 **Файл:** {d.get('file')}\n━━━━━━━━━━━━━━\n"
              f"👤 От: @{update.effective_user.username}")
    
    await context.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    await update.message.reply_text("🚀 *Заявка улетела!*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# --- ЗАПУСК ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), start_survey),
            MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_support)
        ],
        states={
            S1: [MessageHandler(filters.TEXT & ~filters.COMMAND, st1)], S2: [MessageHandler(filters.TEXT & ~filters.COMMAND, st2)],
            S3: [MessageHandler(filters.TEXT & ~filters.COMMAND, st3)], S4: [MessageHandler(filters.TEXT & ~filters.COMMAND, st4)],
            S5: [MessageHandler(filters.TEXT & ~filters.COMMAND, st5)], S6: [MessageHandler(filters.TEXT & ~filters.COMMAND, st6)],
            S7: [MessageHandler(filters.TEXT & ~filters.COMMAND, st7)], S8: [MessageHandler(filters.TEXT & ~filters.COMMAND, st8)],
            S9: [MessageHandler(filters.TEXT & ~filters.COMMAND, st9)], S10: [MessageHandler(filters.TEXT & ~filters.COMMAND, st10)],
            S11: [MessageHandler(filters.TEXT & ~filters.COMMAND, st11)], S12: [MessageHandler(filters.TEXT & ~filters.COMMAND, st12)],
            S13: [MessageHandler(filters.TEXT & ~filters.COMMAND, st13)], S14: [MessageHandler(filters.TEXT & ~filters.COMMAND, st14)],
            S15: [MessageHandler(filters.TEXT & ~filters.COMMAND, st15)], S16: [MessageHandler(filters.TEXT & ~filters.COMMAND, st16)],
            S17: [MessageHandler(filters.TEXT & ~filters.COMMAND, st17)], S18: [MessageHandler(filters.TEXT & ~filters.COMMAND, st18)],
            S19: [MessageHandler(filters.TEXT & ~filters.COMMAND, final)],
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_to_moders)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    print("🚀 ENGINE SUPERSONIC START")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__": main()
