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

# --- SERVER ---
class HealthServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.end_headers()
        self.wfile.write(b"ZGS Ultimate Engine Active")
    def log_message(self, *args): pass

def run_server():
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(('0.0.0.0', port), HealthServer).serve_forever()

# --- ПРАВИЛА (ОБНОВЛЕННЫЕ) ---
RULES_FULL = """

Tevs.service

Горизонтальная линия

Омск, Россия

(+7) (951) 402-40-88

zorogamestoresup@gmail.com

 20 янв. 2026 г.

Уважаемый пользователь!

Вот основные критерии для выкладывания игр на Zoro Game Store (ZGS)

Вам потребуется:

Название игры - лёгкое для восприятия и памяти слова или группа из слов.
Теги - слова которые как либо связаны с вашей игрой.
Студия - Как вы именуете себя или свою команду разработчиков.
Обложка - большое изображение которое будет давать больше возможностей в кастомизации страницы игры.
Скриншоты - изображения которая должна показывать игру визуально.
Описание - объясните про что ваша игра словесно
Привлечение внимания к описанию «легендарная игра … в новых красках» «добро пожаловать в мир облаков»
Лор если он есть «Давным давно две расы правили землёй: люди и монстры»
Какие испытания ждут в игре «В этой игре вас ожидает безумно веселая и забавная атмосфера с приключениями милой пушистой кошки.
Основные механики игры «Управляя кошкой, ваша задача – подпрыгивать на платформы, поднимаясь все выше и выше. Однако, не все так просто, как может показаться! Вас ждут опасные препятствия, ловушки и веселые сюрпризы, которые придется преодолевать по пути вверх.»


1. Название игры
Укажите полное название игры, без сокращений.
Не должно быть слов не культурной речи
должно иметь русский, немецкий, английский язык для удобного и более понятного интерфейса и избежания ошибок на самом сайте
Не должно содержать ссылок на любой контент
Должно иметь не больше 25 символов
Должно иметь больше 2 символов
В начале текста не должен быть whitespace, enter или других не видимых символов
Не должно пропагандировать организаций запрещённые на территории РФ
Не должна содержать авторский контент

2. Теги
Добавьте соответствующие теги, которые описывают жанр и особенности игры.

3. Имя разработчика или студии разработки
Укажите имя разработчика или название компании, ответственной за создание игры.
Название студии подтверждать не требуется
При отказе предоставления этих данных мы будем использовать ваш GreatSupportID или ZOid предоставленный ботом персик

4. обложка
Загрузите аватарку формата 16:9. Это изображение будет представлено на странице вашей игры.
Не должна содержать авторский контент
Не должно изображать: порнографию, ссылки или изображения и текст запрещённый конструкции РФ


5. Скриншоты
Необходимо предоставить 3 основных скриншота, а также можно добавить бесконечное количество дополнительных.
Не должна содержать авторский контент
Не должно изображать: шокирующий контекст, ссылки или изображения, текст запрещённые конструкции РФ
Должны соответствовать содержанию игры

6. Описание игры
Напишите подробное описание игры, включая основные особенности и уникальные элементы.
Не должна содержать копипаст
Не может содержать ссылки на какие либо сайты
Не должно содержать ненавистный характер или пропагандировать организаций запрещённые на территории Российской федерации
7. Версия игры
Укажите актуальную версию игры, которую вы выкладываете.
В версии может содержатся символы: все числа от 1 до 9; «A»; «B»; «C»; «V»; «.»; «_»; «-»; а также слова: «beta» «Alpha» «Release»
8. Файл игры
Приложения должны быть представлены в формате APK для Android или exe для windows, HTML для браузера.
Размер файла не должен превышать 100 гигабайт.
Приложения должны соответствовать последним версиям операционных систем.
Приложения не должны содержать вирусов, вредоносного ПО или шпионского программного обеспечения.
Все разрешения, запрашиваемые приложением, должны быть необходимыми для его работы.
Приложения не должны содержать оскорбительного контента, шокирующий контент или темы, которые могут быть расценены как дискриминационные.
Приложения должны быть протестированы на наличие ошибок и стабильность работы.
Рекомендуется предоставить отчет о тестировании с указанием найденных ошибок и исправлений.
Приложение должно не нарушать конституцию РФ
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

# --- ЛОГИКА ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💎 *Zoro Game Store v7.0*\nВсе системы активны.", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def mini_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = context.user_data.get('click_score', 0)
    context.user_data['click_score'] = score + 1
    await update.message.reply_text(f"🎯 **ZORO CLICKER**\n\nВы кликнули: {score + 1} раз(а)!\nЖмите еще раз на кнопку в меню, чтобы играть.", parse_mode="Markdown")

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
            c.user_data[key] = "📎 [Файл прикреплен]"

    await u.message.reply_text(txt, reply_markup=survey_menu(skip), parse_mode="Markdown")
    return next_s

async def st_start(u,c): 
    c.user_data.clear()
    c.user_data['media'] = []
    await u.message.reply_text("1️⃣ *Название для ссылки:*", reply_markup=survey_menu())
    return S1

async def s1(u,c): return await engine(u,c,'q1', S2, "2️⃣ *Описание:*")
async def s2(u,c): return await engine(u,c,'q2', S3, "3️⃣ *Иконка (URL/Файл):*")
async def s3(u,c): return await engine(u,c,'q3', S4, "4️⃣ *ЗАГОЛОВОК*:", False)
async def s4(u,c): return await engine(u,c,'q4', S5, "5️⃣ *Категория:*")
async def s5(u,c): return await engine(u,c,'q5', S6, "6️⃣ *Цена:*")
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
async def s18(u,c): return await engine(u,c,'q18', S19, "1️⃣9️⃣ *Дополнительные файлы:*")

async def final(u,c):
    if not u.message.text: c.user_data['media'].append(u.message.message_id)
    c.user_data['q19'] = u.message.text if u.message.text else "📎 [Файл]"
    d = c.user_data
    report = f"📩 **ЗАЯВКА (19/19)**\nАвтор: @{u.effective_user.username}\nПроект: {d.get('q4')}\n\n"
    for i in range(1, 20): report += f"{i}. {d.get(f'q{i}')}\n"
    
    await c.bot.send_message(ADMIN_CHAT_ID, report)
    for mid in d.get('media', []):
        try: await c.bot.forward_message(ADMIN_CHAT_ID, u.message.chat_id, mid)
        except: pass
    
    await u.message.reply_text("🚀 *Заявка и файлы отправлены!*", reply_markup=main_menu(), parse_mode="Markdown")
    return ConversationHandler.END

async def start_sup(u,c):
    await u.message.reply_text("👨‍💻 Напишите ваш вопрос:", reply_markup=survey_menu(False))
    return SUPPORT_MODE

async def send_sup(u,c):
    if u.message.text == "❌ ВЕРНУТЬСЯ В МЕНЮ": return await start(u,c)
    await c.bot.send_message(ADMIN_CHAT_ID, f"🆘 **SUPPORT**\n@{u.effective_user.username}: {u.message.text}")
    await u.message.reply_text("✅ Отправлено!", reply_markup=main_menu())
    return ConversationHandler.END

def main():
    threading.Thread(target=run_server, daemon=True).start()
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^🚀 ОПУБЛИКОВАТЬ ПРОЕКТ$"), st_start), MessageHandler(filters.Regex("^👨‍💻 ПОДДЕРЖКА$"), start_sup)],
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

if __name__ == "__main__": main()
