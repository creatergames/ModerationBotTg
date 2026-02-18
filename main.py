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

# --- ВЕБ-СЕРВЕР ДЛЯ RENDER (Health Check) ---
def run_health_server():
    port = int(os.environ.get("PORT", 10000))
    server_address = ('', port)
    httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)
    print(f"Health check server started on port {port}")
    httpd.serve_forever()

# --- ЛОГИКА БОТА ---
STATES = [
    "LINK_NAME", "DESC", "ICON", "TITLE", "CATEGORY", "PRICE", "VERSION",
    "L1", "L2", "L3", "L4", "NOTE", "COMMENTS", "BG", "CHANGELOG",
    "GAME_FILE", "GAME_ICON", "SCREENSHOTS", "EXTRA_FILES", "EXTRA_NAMES", "CONFIRM"
]

user_states = {}
user_data = {}

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

def set_commands():
    bot_api("setMyCommands", {"commands": [
        {"command": "start", "description": "Начать заполнение"},
        {"command": "cancel", "description": "Отменить"}
    ]})

def send_msg(chat_id, text):
    return bot_api("sendMessage", {"chat_id": chat_id, "text": text, "parse_mode": "HTML"})

def handle_update(update):
    if "message" not in update: return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    
    file_id = None
    if "document" in msg: file_id = msg["document"]["file_id"]
    elif "photo" in msg: file_id = msg["photo"][-1]["file_id"]

    if msg["chat"]["type"] != "private" and not text.startswith("/"):
        return

    if text == "/cancel":
        if chat_id in user_states and user_states[chat_id] is not None:
            user_states[chat_id] = None
            user_data[chat_id] = {}
            send_msg(chat_id, "❌ <b>Заполнение отменено.</b>")
        else:
            send_msg(chat_id, "Нет активного процесса.")
        return

    if text == "/start":
        user_states[chat_id] = STATES[0]
        user_data[chat_id] = {"screenshots": [], "extra_files": []}
        send_msg(chat_id, "🚀 <b>Zoro Store</b>\nШаг 1: Введите <b>Название для ссылки</b>:")
        return

    if chat_id not in user_states or user_states[chat_id] is None:
        return

    state = user_states[chat_id]
    idx = STATES.index(state)
    current_val = text if text else file_id
    
    if state == "SCREENSHOTS":
        if text and text.lower() == "готово": pass
        else:
            if file_id: user_data[chat_id]["screenshots"].append(file_id)
            send_msg(chat_id, f"Скриншот получен ({len(user_data[chat_id]['screenshots'])}/8). Напишите 'готово'.")
            return
    elif state == "EXTRA_FILES":
        if text and text.lower() == "готово": pass
        else:
            if file_id: user_data[chat_id]["extra_files"].append(file_id)
            send_msg(chat_id, f"Доп. файл получен. Напишите 'готово'.")
            return
    else:
        user_data[chat_id][state] = current_val

    if idx + 1 < len(STATES):
        next_state = STATES[idx + 1]
        user_states[chat_id] = next_state
        prompts = {
            "DESC": "Введите <b>Описание</b>:",
            "ICON": "Отправьте <b>Иконку</b> (URL или файл):",
            "TITLE": "Введите <b>Заголовок*</b>:",
            "CATEGORY": "Введите <b>Категорию</b>:",
            "PRICE": "Введите <b>Цену</b>:",
            "VERSION": "Введите <b>Версию</b>:",
            "L1": "Ссылка 1 (название = ссылка):",
            "L2": "Ссылка 2 (название = ссылка):",
            "L3": "Ссылка 3 (название = ссылка):",
            "L4": "Ссылка 4 (название = ссылка):",
            "NOTE": "Введите <b>Примечание к игре</b>:",
            "COMMENTS": "<b>Комментарии:</b> Ссылка на ТГ или Zoro Store:",
            "BG": "Отправьте <b>Фоновое изображение</b> (URL или файл):",
            "CHANGELOG": "Описание последних изменений:",
            "GAME_FILE": "Загрузите <b>Файл игры</b>:",
            "GAME_ICON": "Загрузите <b>Иконку игры</b>:",
            "SCREENSHOTS": "Отправьте <b>Скриншоты</b> (до 8). Пишите 'готово'.",
            "EXTRA_FILES": "Доп. файлы (до 8). Пишите 'готово'.",
            "EXTRA_NAMES": "Введите названия для доп. файлов:",
            "CONFIRM": "Все готово. Напишите <b>ДА</b> для отправки."
        }
        send_msg(chat_id, prompts.get(next_state, "Продолжаем..."))
    else:
        # ФОРМИРОВАНИЕ ПОЛНОГО ОТЧЕТА
        d = user_data[chat_id]
        report = (
            f"<b>📥 НОВАЯ ЗАЯВКА @{msg['from'].get('username', 'н/д')}</b>\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>🔹 Основное:</b>\n"
            f"Заголовок*: {d.get('TITLE')}\n"
            f"Название ссылки: {d.get('LINK_NAME')}\n"
            f"Категория: {d.get('CATEGORY')}\n"
            f"Цена: {d.get('PRICE')}\n"
            f"Версия: {d.get('VERSION')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>🔹 Описание и изменения:</b>\n"
            f"Описание: {d.get('DESC')}\n"
            f"Changes: {d.get('CHANGELOG')}\n"
            f"Примечание: {d.get('NOTE')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>🔹 Ссылки:</b>\n"
            f"1: {d.get('L1')}\n2: {d.get('L2')}\n3: {d.get('L3')}\n4: {d.get('L4')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"<b>🔹 Дополнительно:</b>\n"
            f"Комментарии: {d.get('COMMENTS')}\n"
            f"Иконка (URL/ID): {d.get('ICON')}\n"
            f"Фон (URL/ID): {d.get('BG')}\n"
            f"Названия доп. файлов: {d.get('EXTRA_NAMES')}\n"
            f"━━━━━━━━━━━━━━━━━━"
        )
        
        # Отправка текста
        send_msg(GROUP_ID, report)
        
        # Отправка медиа
        if d.get("GAME_FILE"):
            bot_api("sendDocument", {"chat_id": GROUP_ID, "document": d["GAME_FILE"], "caption": "📦 Файл игры"})
        if d.get("GAME_ICON"):
            bot_api("sendPhoto", {"chat_id": GROUP_ID, "photo": d["GAME_ICON"], "caption": "🖼 Иконка игры"})
        
        # Скриншоты (альбомом по 8)
        if d.get("screenshots"):
            media_group = []
            for fid in d["screenshots"]:
                media_group.append({"type": "photo", "media": fid})
            bot_api("sendMediaGroup", {"chat_id": GROUP_ID, "media": media_group})

        send_msg(chat_id, "✅ <b>Успешно!</b> Вся информация передана в группу модерации.")
        user_states[chat_id] = None

def main():
    threading.Thread(target=run_health_server, daemon=True).start()
    set_commands()
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
