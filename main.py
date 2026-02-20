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

# --- ЛОГИКА БОТА ---
STATES = [
    "LINK_NAME", "DESC", "ICON", "TITLE", "CATEGORY", "PRICE", "VERSION",
    "L1", "L2", "L3", "L4", "NOTE", "COMMENTS", "BG", "CHANGELOG",
    "GAME_FILE", "GAME_ICON", "SCREENSHOTS", "EXTRA_FILES", "EXTRA_NAMES", "CONFIRM"
]

user_states = {}
user_data = {}
# Для хранения связи: ID сообщения в группе -> ID пользователя
moderation_map = {}

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
    # --- ОБРАБОТКА КНОПОК (CALLBACK) ---
    if "callback_query" in update:
        cb = update["callback_query"]
        admin_user = cb["from"]["username"]
        data = cb["data"] # "approve_USERID" или "reject_USERID"
        action, target_user_id = data.split("_")
        msg_id = cb["message"]["message_id"]

        status_text = "✅ ОДОБРЕНО" if action == "approve" else "❌ ОТКЛОНЕНО"
        
        # Обновляем сообщение в группе (убираем кнопки)
        bot_api("editMessageText", {
            "chat_id": GROUP_ID,
            "message_id": msg_id,
            "text": cb["message"]["text"] + f"\n\n<b>Статус: {status_text}</b>\nМодератор: @{admin_user}",
            "parse_mode": "HTML"
        })

        # Запрашиваем комментарий у админа в ЛС
        user_states[cb["from"]["id"]] = f"WAIT_COMMENT_{action}_{target_user_id}"
        send_msg(cb["from"]["id"], f"Введите комментарий для пользователя по заявке {status_text}:")
        return

    if "message" not in update: return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    
    # --- ЛОГИКА КОММЕНТАРИЯ МОДЕРАТОРА ---
    current_state = user_states.get(chat_id, "")
    if isinstance(current_state, str) and current_state.startswith("WAIT_COMMENT_"):
        _, _, action, target_id = current_state.split("_")
        final_status = "ОДОБРЕНА" if action == "approve" else "ОТКЛОНЕНА"
        
        # Отправляем вердикт пользователю
        send_msg(int(target_id), f"🔔 <b>Ваша заявка {final_status}!</b>\n\n💬 Комментарий модератора: <i>{text}</i>")
        send_msg(chat_id, "✅ Комментарий отправлен пользователю.")
        user_states[chat_id] = None
        return

    # Стандартные команды
    if text == "/cancel":
        user_states[chat_id] = None
        send_msg(chat_id, "❌ Отменено.")
        return

    if text == "/start":
        user_states[chat_id] = STATES[0]
        user_data[chat_id] = {"screenshots": [], "extra_files": []}
        send_msg(chat_id, "🚀 <b>Zoro Store</b>\nШаг 1: Введите <b>Название для ссылки</b>:")
        return

    if chat_id not in user_states or user_states[chat_id] is None: return

    # Цепочка опроса (упрощенно для краткости, логика та же)
    state = user_states[chat_id]
    if state not in STATES: return
    
    idx = STATES.index(state)
    file_id = msg["document"]["file_id"] if "document" in msg else (msg["photo"][-1]["file_id"] if "photo" in msg else None)
    user_data[chat_id][state] = text if text else file_id

    # Обработка SCREENSHOTS / EXTRA_FILES (аналогично предыдущему коду)
    if state in ["SCREENSHOTS", "EXTRA_FILES"] and text.lower() != "готово":
        if file_id: user_data[chat_id][state if state == "EXTRA_FILES" else "screenshots"].append(file_id)
        return

    if idx + 1 < len(STATES):
        next_state = STATES[idx + 1]
        user_states[chat_id] = next_state
        # Тут твои промпты из предыдущего кода...
        send_msg(chat_id, f"Следующий шаг: {next_state} (Введите данные)")
    else:
        # ФИНАЛ: Отправка в группу с КНОПКАМИ
        d = user_data[chat_id]
        report = f"<b>📥 НОВАЯ ЗАЯВКА @{msg['from'].get('username', 'н/д')}</b>\nЗаголовок: {d.get('TITLE')}\nЦена: {d.get('PRICE')}"
        
        buttons = {
            "inline_keyboard": [[
                {"text": "✅ Одобрить", "callback_data": f"approve_{chat_id}"},
                {"text": "❌ Отклонить", "callback_data": f"reject_{chat_id}"}
            ]]
        }
        
        send_msg(GROUP_ID, report, reply_markup=buttons)
        send_msg(chat_id, "✅ Заявка отправлена. Ожидайте решения модератора.")
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
