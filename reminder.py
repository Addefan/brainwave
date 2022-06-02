from os import environ
from time import time, sleep
from math import ceil
import telebot
from dotenv import load_dotenv
from services import working_with_db, create_events_table

load_dotenv()

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def reminder():
    """
    Функция, которая шлёт сообщение-напоминание о событии, если до него осталось 5 минут
    После этого убирает событие с текущего дня и переносит на период вперёд
    :return: None
    """
    create_events_table("project.db")
    with working_with_db("project.db") as cursor:
        current_time = int(time())
        cursor.execute(f"SELECT * FROM events WHERE start_date - {current_time} "
                       f"BETWEEN 0 AND 300;")
        events = cursor.fetchall()
        if events is None:
            return
        for event in events:
            bot.send_message(event[5], send_reminder(event[1]), parse_mode="Markdown")
            cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
            if event[4] is not None:
                new_event = list(event)[1:]
                day_in_seconds = 86400
                events_per_week = ceil(7 / (new_event[3] // day_in_seconds)) - 1
                new_event[1] += (events_per_week + 1) * new_event[3]
                new_event[2] += (events_per_week + 1) * new_event[3]
                new_event = tuple(new_event)
                cursor.execute(f"INSERT INTO events VALUES(null, ?, ?, ?, ?, ?);", new_event)


def send_reminder(description):
    """
    Получение текста-напоминания о событии
    :param description: str - событие
    :return: str
    """
    return f"До события ▶ *{description}* ◀ осталось 5 минут❕"


if __name__ == "__main__":
    print("Напоминатель событий включен...")
    while True:
        reminder()
        sleep(1)
