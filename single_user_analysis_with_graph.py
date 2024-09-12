import logging
from pyrogram import Client
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os

# Настройки логирования для отладки
logging.basicConfig(
    filename='pyrogram.log',  # Имя файла для логов
    filemode='w',             # Режим записи ('w' для перезаписи файла каждый раз)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Формат логов
    level=logging.DEBUG       # Уровень логирования
)

# Конфигурация Pyrogram

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")


# Запрашиваем у пользователя ввод имени пользователя
target_username = input("Введите имя пользователя: ")

# Теперь переменная target_username содержит значение, введенное пользователем
print(f"Вы ввели имя пользователя: {target_username}")

app = Client("my_account", api_id=api_id, api_hash=api_hash)

def analyze_chat(chat_id):
    message_count = {}
    first_message_count = {}
    media_count = {}
    messages_per_day = {}

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

                # Считаем количество сообщений по дням
                date_key = message.date.date()
                if user_id not in messages_per_day:
                    messages_per_day[user_id] = {}
                if date_key not in messages_per_day[user_id]:
                    messages_per_day[user_id][date_key] = 0
                messages_per_day[user_id][date_key] += 1
        
        offset_id = history[-1].id  # Изменено с message_id на id
        print(f"Обработано {len(history)} сообщений, продолжаем...")

    return {
        "message_count": message_count,
        "first_message_count": first_message_count,
        "media_count": media_count,
        "messages_per_day": messages_per_day,
    }

def plot_messages_per_day(messages_per_day):
    plt.figure(figsize=(10, 6))
    
    for user_id, daily_counts in messages_per_day.items():
        dates = sorted(daily_counts.keys())
        counts = [daily_counts[date] for date in dates]
        
        plt.plot(dates, counts, label=f'User {user_id}')
    
    plt.xlabel('Date')
    plt.ylabel('Number of Messages')
    plt.title('Messages per Day')
    plt.legend()
    plt.grid(True)
    
    # Formatting the date on x-axis
    plt.gcf().autofmt_xdate()
    myFmt = mdates.DateFormatter('%Y-%m-%d')
    plt.gca().xaxis.set_major_formatter(myFmt)
    
    plt.savefig(f'messages_per_day_{target_username}.png')
    plt.show()

try:
    print("Запускаем клиента...")
    app.start()

    print("Клиент запущен успешно.")

    print(f"Ищем пользователя {target_username}...")
    target_chat = app.get_chat(target_username)
    chat_id = target_chat.id

    print(f"Начинаем анализ чата с {target_username} (ID: {chat_id})...")
    chat_data = analyze_chat(chat_id)

    with open(f'result_{target_username}.txt', 'w', encoding='utf-8') as f:
        f.write(f"Чат с {target_username}\n")
        f.write("Количество сообщений:\n")
        for user_id, count in chat_data['message_count'].items():
            f.write(f"  Пользователь {user_id}: {count}\n")
        
        f.write("Количество первых сообщений:\n")
        for user_id, count in chat_data['first_message_count'].items():
            f.write(f"  Пользователь {user_id}: {count}\n")

        f.write("Количество мультимедиа:\n")
        for user_id, count in chat_data['media_count'].items():
            f.write(f"  Пользователь {user_id}: {count}\n")
    
    print(f"Данные успешно записаны в файл 'result_{target_username}.txt'.")
    
    print("Строим график сообщений по дням...")
    plot_messages_per_day(chat_data['messages_per_day'])

except Exception as e:
    logging.error("Произошла ошибка при работе с клиентом Pyrogram", exc_info=True)
finally:
    print("Завершаем работу клиента...")
    app.stop()
