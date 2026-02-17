import json
import time
import urllib.request
import urllib.parse

# --- КОНФИГУРАЦИЯ ---
TOKEN = "8346418130:AAF7u1diMBBTzDdfaoA9nBua4xJNfuSPY5A"
GROUP_ID = -1003844600340
API_URL = f"https://api.telegram.org/bot{TOKEN}/"

# Состояния и данные
user_states = {}
user_data = {}

def bot_api(method, data=None):
    url = API_URL + method
    try:
        req_data = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=req_data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Ошибка API ({method}): {e}")
        return None

def set_commands():
    """Установка списка команд для отображения через '/'"""
    commands = {
        "commands": [
            {"command": "start", "description": "Начать заполнение заявки"},
            {"command": "cancel", "description": "Отменить текущую заявку"},
            {"command": "help", "description": "Инструкция"}
        ]
    }
    bot_api("setMyCommands", commands)

def send_msg(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return bot_api("sendMessage", payload)

def handle_update(update):
    if "message" not in update: return
    msg = update["message"]
    chat_id = msg["chat"]["id"]
    user = msg["from"]
    text = msg.get("text", "")

    # Команда отмены
    if text == "/cancel":
        user_states[chat_id] = "START"
        send_msg(chat_id, "❌ Заполнение отменено. Напишите /start для новой попытки.")
        return

    # Команда старт / Приветствие
    if text == "/start":
        user_states[chat_id] = "STEP_TITLE"
        user_data[chat_id] = {}
        welcome = (
            f"👋 Привет, <b>{user.get('first_name', 'пользователь')}</b>!\n\n"
            "Я бот модерации <b>Zoro Store</b>. Давайте оформим вашу игру.\n\n"
            "Шаг 1: Введите <b>Заголовок*</b> игры (обязательно):"
        )
        send_msg(chat_id, welcome)
        return

    state = user_states.get(chat_id, "START")

    # --- ЦЕПОЧКА ОПРОСА ---
    if state == "STEP_TITLE":
        user_data[chat_id]['title'] = text
        user_states[chat_id] = "STEP_DESC"
        send_msg(chat_id, "Шаг 2: Введите <b>Описание</b> игры:")

    elif state == "STEP_DESC":
        user_data[chat_id]['desc'] = text
        user_states[chat_id] = "STEP_PRICE"
        send_msg(chat_id, "Шаг 3: Укажите <b>Цену</b> (или напишите 'Бесплатно'):")

    elif state == "STEP_PRICE":
        user_data[chat_id]['price'] = text
        user_states[chat_id] = "STEP_LINKS"
        send_msg(chat_id, "Шаг 4: Введите <b>Ссылки</b> (название = ссылка). Можно несколько штук.")

    elif state == "STEP_LINKS":
        user_data[chat_id]['links'] = text
        user_states[chat_id] = "FINISH_CONFIRM"
        send_msg(chat_id, "✅ Все данные собраны! Отправить на модерацию?\nНапишите <b>ДА</b> для подтверждения.")

    elif state == "FINISH_CONFIRM":
        if text.upper() == "ДА":
            d = user_data[chat_id]
            report = (
                "<b>🆕 НОВАЯ ЗАЯВКА НА МОДЕРАЦИЮ</b>\n"
                "----------------------------------\n"
                f"👤 <b>Отправитель:</b> @{user.get('username', 'н/д')}\n"
                f"🎮 <b>Игра:</b> {d['title']}\n"
                f"📝 <b>Описание:</b> {d['desc']}\n"
                f"💰 <b>Цена:</b> {d['price']}\n"
                f"🔗 <b>Ссылки:</b>\n{d['links']}\n"
                "----------------------------------"
            )
            # Отправка в твою группу
            send_msg(GROUP_ID, report)
            # Ответ пользователю
            send_msg(chat_id, "🚀 Заявка успешно отправлена в группу @ModerationZ!")
        else:
            send_msg(chat_id, "Отправка отменена. Используйте /start чтобы начать заново.")
        
        user_states[chat_id] = "START"

def main():
    print("Бот активирован...")
    set_commands() # Регистрируем команды в меню Telegram
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
