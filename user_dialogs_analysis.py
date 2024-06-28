import logging
from pyrogram import Client
from datetime import timedelta
import os
import re

# Настройки логирования для отладки
logging.basicConfig(
    filename='pyrogram.log',  # Имя файла для логов
    filemode='w',             # Режим записи ('w' для перезаписи файла каждый раз)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат логов
    level=logging.DEBUG       # Уровень логирования
)

api_id = 12345678
api_hash = ""

print("Создаём клиент...")
app = Client("my_account", api_id=api_id, api_hash=api_hash)

def clean_filename(filename):
    """
    Функция для удаления недопустимых символов из имени файла.
    """
    return re.sub(r'[\\\\/*?:"<>|]', "", filename)

def analyze_chat(chat_id):
    message_count = {}
    first_message_count = {}
    media_count = {}

    last_message_time = {}

    offset_id = 0
    while True:
        history = list(app.get_chat_history(chat_id, offset_id=offset_id, limit=100))
        if not history:
            print("История пуста, завершаем анализ.")
            break

        for message in history:
            user_id = message.from_user.id if message.from_user else None

            if user_id:
                # Считаем количество сообщений
                if user_id not in message_count:
                    message_count[user_id] = 0
                message_count[user_id] += 1

                # Считаем мультимедиа сообщения
                if message.media:
                    if user_id not in media_count:
                        media_count[user_id] = 0
                    media_count[user_id] += 1

                # Считаем "первое написание"
                if user_id not in last_message_time or last_message_time[
                    user_id
                ] - message.date > timedelta(minutes=30):
                    if user_id not in first_message_count:
                        first_message_count[user_id] = 0
                    first_message_count[user_id] += 1
                
                # Обновляем время последнего сообщения
                last_message_time[user_id] = message.date
        
        offset_id = history[-1].id  # Изменено с message_id на id
        print(f"Обработано {len(history)} сообщений, продолжаем...")

    return {
        "message_count": message_count,
        "first_message_count": first_message_count,
        "media_count": media_count,
    }

try:
    print("Запускаем клиента...")
    app.start()

    print("Клиент запущен успешно.")

    print("Получаем список всех чатов...")
    dialogs = app.get_dialogs()

    for dialog in dialogs:
        chat = dialog.chat
        chat_id = chat.id
        chat_title = chat.title or chat.username or f"chat_{chat_id}"
        
        # Очистка имени файла от недопустимых символов
        clean_chat_title = clean_filename(chat_title)
        
        # Проверяем наличие файла перед анализом чата
        result_filename = f'result_{clean_chat_title}.txt'
        if os.path.exists(result_filename):
            print(f"Файл {result_filename} уже существует. Пропускаем анализ чата {chat_title}.")
            continue
        
        print(f"Начинаем анализ чата {chat_title} (ID: {chat_id})...")
        chat_data = analyze_chat(chat_id)

        with open(result_filename, 'w', encoding='utf-8') as f:
            f.write(f"Чат с {chat_title}\n")
            f.write("Количество сообщений:\n")
            for user_id, count in chat_data['message_count'].items():
                user = app.get_users(user_id)
                username = user.username or f"user_{user_id}"
                f.write(f"  Пользователь {username}: {count}\n")
            
            f.write("Количество первых сообщений:\n")
            for user_id, count in chat_data['first_message_count'].items():
                user = app.get_users(user_id)
                username = user.username or f"user_{user_id}"
                f.write(f"  Пользователь {username}: {count}\n")

            f.write("Количество мультимедиа:\n")
            for user_id, count in chat_data['media_count'].items():
                user = app.get_users(user_id)
                username = user.username or f"user_{user_id}"
                f.write(f"  Пользователь {username}: {count}\n")
        
        print(f"Данные успешно записаны в файл '{result_filename}'.")

except Exception as e:
    logging.error("Произошла ошибка при работе с клиентом Pyrogram", exc_info=True)
finally:
    print("Завершаем работу клиента...")
    app.stop()