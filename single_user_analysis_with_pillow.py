import logging
from pyrogram import Client
from datetime import timedelta, datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import pandas as pd
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

async def analyze_chat(chat_id):
    message_count = {}
    first_message_count = {}
    media_count = {}
    messages_per_day = {}

    last_message_time = {}

    offset_id = 0
    while True:
        # Получаем историю чата как асинхронный генератор
        history = app.get_chat_history(chat_id, offset_id=offset_id, limit=100)

        messages = []
        async for message in history:
            messages.append(message)

        if not messages:
            print("История пуста, завершаем анализ.")
            break

        for message in messages:
            user_id = message.from_user.id if message.from_user else None

            if user_id:
                if user_id not in message_count:
                    message_count[user_id] = 0
                message_count[user_id] += 1

                if message.media:
                    if user_id not in media_count:
                        media_count[user_id] = 0
                    media_count[user_id] += 1

                if user_id not in last_message_time or last_message_time[user_id] - message.date > timedelta(minutes=30):
                    if user_id not in first_message_count:
                        first_message_count[user_id] = 0
                    first_message_count[user_id] += 1

                last_message_time[user_id] = message.date

                date_key = message.date.date()
                if user_id not in messages_per_day:
                    messages_per_day[user_id] = {}
                if date_key not in messages_per_day[user_id]:
                    messages_per_day[user_id][date_key] = 0
                messages_per_day[user_id][date_key] += 1
        
        offset_id = messages[-1].id
        print(f"Обработано {len(messages)} сообщений, продолжаем...")

    return {
        "message_count": message_count,
        "first_message_count": first_message_count,
        "media_count": media_count,
        "messages_per_day": messages_per_day,
    }

def plot_messages_per_week(messages_per_day):
    plt.figure(figsize=(12, 8))
    
    for user_id, daily_counts in messages_per_day.items():
        df = pd.DataFrame(list(daily_counts.items()), columns=['Date', 'Count'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        weekly_counts = df.resample('W').sum()
        
        plt.bar(weekly_counts.index, weekly_counts['Count'], label=f'User {user_id}')
    
    plt.xlabel('Week')
    plt.ylabel('Number of Messages')
    plt.title('Messages per Week')
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.xticks(rotation=45)
    plt.savefig(f'messages_per_week_{target_username}.png')
    plt.show()

async def main():
    print("Запускаем клиента...")
    await app.start()
    print("Клиент запущен успешно.")
    print(f"Ищем пользователя {target_username}...")
    target_chat = await app.get_chat(target_username)
    chat_id = target_chat.id
    print(f"Начинаем анализ чата с {target_username} (ID: {chat_id})...")
    chat_data = await analyze_chat(chat_id)
    plot_messages_per_week(chat_data["messages_per_day"])

try:
    app.run(main())
except Exception as e:
    print(f"An error occurred: {e}")
