import logging
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pyrogram import Client
import asyncio
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
    messages_per_day = {}
    
    async for message in app.get_chat_history(chat_id):
        if message.date:
            date_str = message.date.strftime('%Y-%m-%d')
            user_id = message.from_user.id if message.from_user else 'unknown'
            
            if user_id not in messages_per_day:
                messages_per_day[user_id] = {}
            
            if date_str not in messages_per_day[user_id]:
                messages_per_day[user_id][date_str] = 0
            
            messages_per_day[user_id][date_str] += 1
    
    return {"messages_per_day": messages_per_day}

def plot_messages_histogram(messages_per_day):
    plt.figure(figsize=(12, 8))
    
    for user_id, daily_counts in messages_per_day.items():
        df = pd.DataFrame(list(daily_counts.items()), columns=['Date', 'Count'])
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        weekly_counts = df.resample('W').sum()

        # Подготовка данных для гистограммы
        weeks = weekly_counts.index.to_pydatetime()
        counts = weekly_counts['Count'].values

        # Построение гистограммы
        plt.hist(weeks, bins=len(weeks), weights=counts, alpha=0.5, label=f'User {user_id}', edgecolor='black')
    
    plt.xlabel('Week')
    plt.ylabel('Number of Messages')
    plt.title('Messages Distribution per Week')
    plt.legend()
    plt.grid(True)
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.WeekdayLocator())
    plt.xticks(rotation=45)
    plt.savefig(f'messages_histogram_{target_username}.png')
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
    
    plot_messages_histogram(chat_data["messages_per_day"])

if __name__ == '__main__':
    asyncio.run(main())