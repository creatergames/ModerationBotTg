import json
import time
import urllib.request
import urllib.parse
import http.server
import threading
import os

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
GROUP_ID = -1003844600340
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    httpd.serve_forever()

# --- ЭТАПЫ ОПРОСА ---
STATES = [
    "LINK_NAME", "DESC", "ICON", "TITLE", "CATEGORY", "PRICE", "VERSION",
    "L1", "L2", "L3", "L4", "NOTE", "COMMENTS", "BG", "CHANGELOG",
    "GAME_FILE", "GAME_ICON", "SCREENSHOTS", "EXTRA_FILES", "EXTRA_NAMES", "CONFIRM"
]

user_states = {}
user_data = {}
# Ожидание комментария от модератора: {chat_id_группы: {"target_user": ID, "action": "approve/reject"}}
moderation_pending = {}

def bot_api(method, data=None):
    url = API_URL + method
    try:
        req_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Ошибка API {method}: {e}")
        return None

def send_msg(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: payload["reply_markup"] = reply_markup
    return bot_api("sendMessage", payload)

def handle_update(update):
    # --- ОБРАБОТКА КНОПОК МОДЕРАЦИИ ---
    if "callback_query" in update:
        cb = update["callback_query"]
        action, target_user_id = cb["data"].split("_")
        
        status = "ОДОБРЕНИЯ" if action == "approve" else "ОТКЛОНЕНИЯ"
        moderation_pending[GROUP_ID] = {"target": target_user_id, "action": action, "msg_id": cb["message"]["message_id"]}
        
        bot_api("answerCallbackQuery", {"callback_query_id": cb["id"], "text": "Жду комментарий в чате..."})
        send_msg(GROUP_ID, f"📝 <b>Модератор @{cb['from'].get('username')}, напишите причину {status}:</b>\n(Просто отправьте сообщение в этот чат)")
        return

    if "message" not in update: return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    # --- ЛОГИКА КОММЕНТАРИЯ В ГРУППЕ ---
    if chat_id == GROUP_ID and chat_id in moderation_pending:
        p = moderation_pending.pop(chat_id)
        final_status = "ОДОБРЕНА" if p["action"] == "approve" else "ОТКЛОНЕНА"
        
        # Уведомляем пользователя
        send_msg(int(p["target"]), f"🔔 <b>Ваша заявка {final_status}!</b>\n\n💬 Комментарий модератора: <i>{text}</i>")
        
        # Обновляем пост в группе
        bot_api("editMessageText", {
            "chat_id": GROUP_ID,
            "message_id": p["msg_id"],
            "text": f"✅ <b>Заявка обработана</b>\nРезультат: {final_status}\nПричина: {text}",
            "parse_mode": "HTML"
        })
        return

    # --- ЛОГИКА ПОЛЬЗОВАТЕЛЯ (ЛС) ---
    if msg["chat"]["type"] == "private":
        if text == "/cancel":
            user_states[chat_id] = None
            send_msg(chat_id, "❌ Заполнение отменено.")
            return

        if text == "/start":
            user_states[chat_id] = STATES[0]
            user_data[chat_id] = {"screenshots": [], "extra_files": []}
            send_msg(chat_id, "🚀 <b>Zoro Store</b>\nВведите <b>Название для ссылки</b>:")
            return

        state = user_states.get(chat_id)
        if not state: return

        idx = STATES.index(state)
        file_id = msg["document"]["file_id"] if "document" in msg else (msg["photo"][-1]["file_id"] if "photo" in msg else None)

        # Сохранение медиа
        if state == "SCREENSHOTS":
            if text and text.lower() == "готово": pass
            else:
                if file_id: user_data[chat_id]["screenshots"].append(file_id)
                send_msg(chat_id, f"Скриншот получен ({len(user_data[chat_id]['screenshots'])}/8). Еще или 'готово'?")
                return
        elif state == "EXTRA_FILES":
            if text and text.lower() == "готово": pass
            else:
                if file_id: user_data[chat_id]["extra_files"].append(file_id)
                send_msg(chat_id, "Файл получен. Еще или 'готово'?")
                return
        else:
            user_data[chat_id][state] = text if text else file_id

        # Переход к следующему шагу
        if idx + 1 < len(STATES):
            next_s = STATES[idx + 1]
            user_states[chat_id] = next_s
            prompts = {
                "DESC": "Введите <b>Описание</b>:",
                "ICON": "Отправьте <b>Иконку</b> (файл или ссылку):",
                "TITLE": "Введите <b>Заголовок*</b> (Обязательно):",
                "CATEGORY": "Введите <b>Категорию</b>:",
                "PRICE": "Введите <b>Цену</b>:",
                "VERSION": "Введите <b>Версию</b>:",
                "L1": "Ссылка 1 (название = ссылка):",
                "L2": "Ссылка 2 (название = ссылка):",
                "L3": "Ссылка 3 (название = ссылка):",
                "L4": "Ссылка 4 (название = ссылка):",
                "NOTE": "Введите <b>Примечание к игре</b>:",
                "COMMENTS": "<b>Комментарии</b> (ссылка или Zoro Store):",
                "BG": "Отправьте <b>Фоновое изображение</b>:",
                "CHANGELOG": "Описание <b>изменений</b>:",
                "GAME_FILE": "Загрузите <b>Файл игры</b>:",
                "GAME_ICON": "Загрузите <b>Иконку игры</b>:",
                "SCREENSHOTS": "Отправьте <b>Скриншоты</b> (до 8). Напишите 'готово' для завершения.",
                "EXTRA_FILES": "Доп. файлы (до 8). Напишите 'готово'.",
                "EXTRA_NAMES": "Введите <b>названия</b> доп. файлов:",
                "CONFIRM": "Все данные введены. Напишите <b>ДА</b> для отправки на модерацию."
            }
            send_msg(chat_id, prompts.get(next_s, "Следующий шаг..."))
        else:
            # ОТПРАВКА ВСЕХ ДАННЫХ В ГРУППУ
            d = user_data[chat_id]
            report = (
                f"<b>📥 НОВАЯ ЗАЯВКА @{msg['from'].get('username', 'н/д')}</b>\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🏷 <b>Название ссылки:</b> {d.get('LINK_NAME')}\n"
                f"📖 <b>Описание:</b> {d.get('DESC')}\n"
                f"🖼 <b>Иконка:</b> {d.get('ICON')}\n"
                f"🔥 <b>Заголовок*:</b> {d.get('TITLE')}\n"
                f"📂 <b>Категория:</b> {d.get('CATEGORY')}\n"
                f"💰 <b>Цена:</b> {d.get('PRICE')}\n"
                f"🆙 <b>Версия:</b> {d.get('VERSION')}\n"
                f"🔗 <b>Ссылки:</b>\n1: {d.get('L1')}\n2: {d.get('L2')}\n3: {d.get('L3')}\n4: {d.get('L4')}\n"
                f"📝 <b>Примечание:</b> {d.get('NOTE')}\n"
                f"💬 <b>Комменты:</b> {d.get('COMMENTS')}\n"
                f"🌌 <b>Фон:</b> {d.get('BG')}\n"
                f"🛠 <b>Changelog:</b> {d.get('CHANGELOG')}\n"
                f"📁 <b>Доп. файлы имена:</b> {d.get('EXTRA_NAMES')}\n"
                f"━━━━━━━━━━━━━━━━━━"
            )
            
            kb = {"inline_keyboard": [[
                {"text": "✅ Одобрить", "callback_data": f"approve_{chat_id}"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{chat_id}"}
            ]]}
            
            send_msg(GROUP_ID, report, reply_markup=kb)
            
            # Пересылка медиа
            if d.get("GAME_FILE"): bot_api("sendDocument", {"chat_id": GROUP_ID, "document": d["GAME_FILE"], "caption": "📦 Файл игры"})
            if d.get("GAME_ICON"): bot_api("sendPhoto", {"chat_id": GROUP_ID, "photo": d["GAME_ICON"], "caption": "🖼 Иконка игры"})
            if d.get("screenshots"):
                bot_api("sendMediaGroup", {"chat_id": GROUP_ID, "media": [{"type":"photo", "media": f} for f in d["screenshots"]]})

            send_msg(chat_id, "✅ Ваша заявка отправлена в @ModerationZ! Ожидайте решения.")
            user_states[chat_id] = None

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    bot_api("setMyCommands", {"commands": [{"command":"start","description":"Начать"},{"command":"cancel","description":"Отмена"}]})
    offset = 0
    while True:
        updates = bot_api("getUpdates", {"offset": offset, "timeout": 20})
        if updates and "result" in updates:
            for up in updates["result"]:
                handle_update(up)
                offset = up["update_id"] + 1
        time.sleep(1)

if __name__ == "__main__":
    main()
