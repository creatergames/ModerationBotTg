import logging
import os
import threading
import random
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    ConversationHandler, ContextTypes, filters
)

# --- НАСТРОЙКИ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
ADMIN_CHAT_ID = "-1003844600340"
WEB_APP_URL = "https://zoro-game.store/"

# Состояния
(S1, S2, S3, S4, S5, S6, S7, S8, S9, S10, S11, S12, S13, S14, S15, S16, S17, S18, S19, SUPPORT_MODE) = range(20)

logging.basicConfig(level=logging.INFO)

# --- SERVER FOR HEALTH CHECKS ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Ultimate Engine Active")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- ПРАВИЛА ---
RULES_FULL = """
*ZORO GAME STORE - ПРАВИЛА*
⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯
1. Название: 2-25 символов.
2. Теги: Соответствующие жанру.
3. Студия: Имя разработчика/команды.
4. Обложка: 16:9, без запрещенки.
5. Скриншоты: Минимум 3 шт.
6. Описание: Уникальный текст.
7. Версия: Формат 1.0.0 или Beta.
8. Файл: До 100 ГБ, без вирусов.
9. Плакат: 164x256px.
10. Цена: 3 ₽ — 50 000 ₽.
11. Ссылки: Без Meta* и нарушений закона.

*Приложение не должно нарушать конституцию РФ.*
"""

# --- UI ---
def main_menu():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🌐 ОТКРЫТЬ ZGS MINI APP", web_app=WebAppInfo(url=WEB_APP_URL))],
        ["🚀 ОПУБЛИКОВАТЬ ПРОЕКТ"],
        ["📋 ПРАВИЛА", "🎮 МИНИ-ИГРА"],
        ["👨‍💻 ПОДДЕРЖКА"]
    ], resize_keyboard=True)

def survey_menu(can_skip=True):
    btns = []
    if can_skip: btns.append("⏩ ПРОПУСТИТЬ")
    btns.append("❌ ВЕРНУТЬСЯ В МЕНЮ")
    return ReplyKeyboardMarkup([btns], resize_keyboard=True)

# --- ЛОГИКА АНКЕТЫ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 *Zoro Game Store v7.0*\nВыберите действие в меню:", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def mini_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data.get('click_score', 0)
    context.user_data['click_score'] = score + 1
    await update.message.reply_text(f"🎯 **ZORO CLICKER**\nВы кликнули: {score + 1} раз(а)!", parse_mode="Markdown")

async def engine(u, c, key, next_s, txt, skip=True):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u, c)
    
    if 'media' not in c.user_data: c.user_data['media'] = []

    if u.message.text == "⏩ ПРОПУСТИТЬ":
        c.user_data[key] = "—"
    else:
        if u.message.text:
            c.user_data[key] = u.message.text
        else:
            c.user_data['media'].append(u.message.message_id)
            c.user_data[key] = "📎 [Медиа-файл]"

    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

async def st_start(u,c): 
    c.user_data.clear() # Полная очистка перед новой анкетой
    c.user_data['media'] = []
    await u.message.reply_text("1️⃣ *Название для ссылки (URL ID):*", reply_markup=survey_menu())
    return S1

# Регистрация шагов
async def s1(u,c): return await engine(u,c,'q1', S2, "2️⃣ *Описание проекта:*")
async def s2(u,c): return await engine(u,c,'q2', S3, "3️⃣ *Иконка (URL или Файл):*")
async def s3(u,c): return await engine(u,c,'q3', S4, "4️⃣ *ЗАГОЛОВОК (Название игры):*", False)
async def s4(u,c): return await engine(u,c,'q4', S5, "5️⃣ *Категория:*")
async def s5(u,c): return await engine(u,c,'q5', S6, "6️⃣ *Цена (в рублях):*")
async def s6(u,c): return await engine(u,c,'q6', S7, "7️⃣ *Версия проекта:*")
async def s7(u,c): return await engine(u,c,'q7', S8, "8️⃣ *Ссылка №1:*")
async def s8(u,c): return await engine(u,c,'q8', S9, "9️⃣ *Ссылка №2:*")
async def s9(u,c): return await engine(u,c,'q9', S10, "🔟 *Ссылка №3:*")
async def s10(u,c): return await engine(u,c,'q10', S11, "1️⃣1️⃣ *Ссылка №4:*")
async def s11(u,c): return await engine(u,c,'q11', S12, "1️⃣2️⃣ *Примечание к игре:*")
async def s12(u,c): return await engine(u,c,'q12', S13, "1️⃣3️⃣ *Комментарии разработчика:*")
async def s13(u,c): return await engine(u,c,'q13', S14, "1️⃣4️⃣ *Фоновое изображение (URL/Файл):*")
async def s14(u,c): return await engine(u,c,'q14', S15, "1️⃣5️⃣ *Список изменений (Changelog):*")
async def s15(u,c): return await engine(u,c,'q15', S16, "1️⃣6️⃣ *Файл игры (APK/EXE/Документ):*")
async def s16(u,c): return await engine(u,c,'q16', S17, "1️⃣7️⃣ *Иконка игры (прозрачная):*")
async def s17(u,c): return await engine(u,c,'q17', S18, "1️⃣8️⃣ *Скриншоты (одним сообщением или файлом):*")
async def s18(u,c): return await engine(u,c,'q18', S19, "1️⃣9️⃣ *Дополнительные файлы и их названия:*")

async def final(u,c):
    if not u.message.text: c.user_data['media'].append(u.message.message_id)
    c.user_data['q19'] = u.message.text if u.message.text else "📎 [Файл]"
    
    d = c.user_data
    # ФОРМИРОВАНИЕ ПОЛНОГО ОТЧЕТА ИЗ 19 ПУНКТОВ
    report = (
        f"📩 **НОВАЯ ЗАЯВКА НА МОДЕРАЦИЮ (19/19)**\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"👤 **Отправитель:** @{u.effective_user.username} (ID: `{u.effective_user.id}`)\n\n"
        f"1. **URL ID:** {d.get('q1')}\n"
        f"2. **Описание:** {d.get('q2')}\n"
        f"3. **Иконка (превью):** {d.get('q3')}\n"
        f"4. **ЗАГОЛОВОК:** {d.get('q4')}\n"
        f"5. **Категория:** {d.get('q5')}\n"
        f"6. **Цена:** {d.get('q6')}\n"
        f"7. **Версия:** {d.get('q7')}\n"
        f"8. **Ссылка 1:** {d.get('q8')}\n"
        f"9. **Ссылка 2:** {d.get('q9')}\n"
        f"10. **Ссылка 3:** {d.get('q10')}\n"
        f"11. **Ссылка 4:** {d.get('q11')}\n"
        f"12. **Примечание:** {d.get('q12')}\n"
        f"13. **Комментарии:** {d.get('q13')}\n"
        f"14. **Фон:** {d.get('q14')}\n"
        f"15. **Лог изменений:** {d.get('q15')}\n"
        f"16. **Файл игры:** {d.get('q16')}\n"
        f"17. **Иконка (файл):** {d.get('q17')}\n"
        f"18. **Скриншоты:** {d.get('q18')}\n"
        f"19. **Доп. файлы:** {d.get('q19')}\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"📦 *Все прикрепленные медиа-файлы будут пересланы ниже.*"
    )
    
    # Отправка текстового отчета
    await c.bot.send_message(ADMIN_CHAT_ID, report, parse_mode="Markdown")
    
    # Пересылка файлов
    for mid in d.get('media', []):
        try:
            await c.bot.forward_message(ADMIN_CHAT_ID, u.message.chat_id, mid)
        except: pass
    
    await u.message.reply_text("🚀 *Ваша заявка полностью укомплектована и отправлена!*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

# Поддержка
async def start_sup(u,c):
    await u.message.reply_text("👨‍💻 Напишите ваш вопрос модератору:", reply_markup=survey_menu(False))
    return SUPPORT_MODE

async def send_sup(u,c):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u,c)
    await c.bot.send_message(ADMIN_CHAT_ID, f"🆘 **SUPPORT**\nОт @{u.effective_user.username}: {u.message.text}")
    await u.message.reply_text("✅ Сообщение отправлено!", reply_markup=main_menu())
    return ConversationHandler.END

# --- RUN ---
def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), st_start),
            MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_sup)
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
            SUPPORT_MODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, send_sup)]
        },
        fallbacks=[MessageHandler(filters.Regex("^❌ ВЕРНУТЬСЯ В МЕНЮ$"), start)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 ПРАВИЛА$"), lambda u,c: u.message.reply_text(RULES_FULL, parse_mode="Markdown")))
    app.add_handler(MessageHandler(filters.Regex("^🎮 МИНИ-ИГРА$"), mini_game))
    app.add_handler(conv)

    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
