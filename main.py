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

    if text == "/cancel":
        user_states[chat_id] = None
        send_msg(chat_id, "❌ Отменено. Напишите /start для новой заявки.")
        return

    if text == "/start" or chat_id not in user_states or user_states[chat_id] is None:
        user_states[chat_id] = STATES[0]
        user_data[chat_id] = {"screenshots": [], "extra_files": []}
        send_msg(chat_id, "🚀 <b>Zoro Store</b>\nШаг 1: Введите <b>Название для ссылки</b>:")
        return

    state = user_states[chat_id]
    idx = STATES.index(state)
    current_val = text if text else file_id
    
    if state == "SCREENSHOTS":
        if text and text.lower() == "готово": pass
        else:
            if file_id: user_data[chat_id]["screenshots"].append(file_id)
            send_msg(chat_id, f"Скриншот получен ({len(user_data[chat_id]['screenshots'])}/8). Отправьте еще или 'готово'.")
            return
    elif state == "EXTRA_FILES":
        if text and text.lower() == "готово": pass
        else:
            if file_id: user_data[chat_id]["extra_files"].append(file_id)
            send_msg(chat_id, f"Доп. файл получен. Отправьте еще или 'готово'.")
            return
    else:
        user_data[chat_id][state] = current_val

    if idx + 1 < len(STATES):
        next_state = STATES[idx + 1]
        user_states[chat_id] = next_state
        prompts = {
            "DESC": "Введите <b>Описание</b>:",
            "ICON": "Отправьте <b>Иконку</b> (URL или файл):",
            "TITLE": "Введите <b>Заголовок*</b> (Обязательно!):",
            "CATEGORY": "Введите <b>Категорию</b>:",
            "PRICE": "Введите <b>Цену</b>:",
            "VERSION": "Введите <b>Версию</b>:",
            "L1": "Ссылка 1 (название = ссылка):",
            "L2": "Ссылка 2 (название = ссылка):",
            "L3": "Ссылка 3 (название = ссылка):",
            "L4": "Ссылка 4 (название = ссылка):",
            "NOTE": "Введите <b>Примечание к игре</b>:",
            "COMMENTS": "<b>Комментарии:</b> Ссылка на ТГ или Zoro Store:",
            "BG": "Отправьте <b>Фоновое изображение</b>:",
            "CHANGELOG": "Описание последних изменений:",
            "GAME_FILE": "Загрузите <b>Файл игры</b>:",
            "GAME_ICON": "Загрузите <b>Иконку игры</b>:",
            "SCREENSHOTS": "Отправьте <b>Скриншоты</b> (до 8). Пишите 'готово'.",
            "EXTRA_FILES": "Доп. файлы (до 8). Пишите 'готово'.",
            "EXTRA_NAMES": "Введите названия для доп. файлов:",
            "CONFIRM": "Напишите <b>ДА</b> для отправки."
        }
        send_msg(chat_id, prompts.get(next_state, "Продолжаем..."))
    else:
        d = user_data[chat_id]
        report = (
            f"<b>🆕 ЗАЯВКА @{msg['from'].get('username', 'н/д')}</b>\n"
            f"━━━━━━━━━━━━━\n"
            f"<b>Заголовок*:</b> {d.get('TITLE')}\n"
            f"<b>Цена:</b> {d.get('PRICE')}\n"
            f"<b>Версия:</b> {d.get('VERSION')}\n"
            f"<b>Ссылки:</b> {d.get('L1')}, {d.get('L2')}\n"
            f"━━━━━━━━━━━━━\n"
        )
        send_msg(GROUP_ID, report)
        if d.get("GAME_FILE"): bot_api("sendDocument", {"chat_id": GROUP_ID, "document": d["GAME_FILE"], "caption": "📦 Файл игры"})
        send_msg(chat_id, "✅ Отправлено в группу модерации.")
        user_states[chat_id] = None

def main():
    # Запускаем веб-сервер в отдельном потоке
    threading.Thread(target=run_health_server, daemon=True).start()
    
    print("Бот запущен...")
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
