from os import environ
import sqlite3
import telebot
from telebot import types
from dotenv import load_dotenv
from services import user_registation, date_to_timestamp, date_view, \
    date_validation, number_validation, get_input_error_text

load_dotenv()

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    user_registation(message)
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    timetable = types.KeyboardButton(text='Расписание')
    task = types.KeyboardButton(text='Задания')
    startKBoart.add(timetable, task)
    bot.send_message(message.chat.id, 'Что вы хотите сделать?', reply_markup=startKBoart)


@bot.message_handler(func=lambda message: message.text == "Расписание")
def display_schedule_buttons(message):
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    removal = types.KeyboardButton(text='Удалить событие из рaсписания')
    adding = types.KeyboardButton(text='Добавить событие в расписание')
    view = types.KeyboardButton(text='Посмотреть расписание')
    startKBoart.add(removal, adding, view)
    bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)


@bot.message_handler(regexp="Удалить событие из рaсписания")
def remove_event(message):
    sent = bot.reply_to(message, 'Введите дату, на какой день хотите удалить событие.\nДД.ММ.ГГГГ')
    bot.register_next_step_handler(sent, remove_event_helper)


def remove_event_helper(message):
    message_to_save = message.text


@bot.message_handler(regexp="Добавить событие в расписание")
def add_event(message):
    sent = bot.reply_to(message, 'Введите дату, на какой день хотите добавить событие.\nДД.ММ.ГГГГ')
    bot.register_next_step_handler(sent, add_event_helper)


def add_event_helper(message):
    message_to_save = message.text


@bot.message_handler(regexp="Посмотреть расписание")
def view_schedule(message):
    sent = bot.reply_to(message, 'Введите дату, на какой день хотите посмотреть расписание.\nДД.ММ.ГГГГ')
    bot.register_next_step_handler(sent, view_schedule_helper)


def view_schedule_helper(message):
    message_to_save = message.text


@bot.message_handler(func=lambda message: message.text == "Задания")
def display_tasks_buttons(message):
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    removal = types.KeyboardButton(text='Удалить задание')
    adding = types.KeyboardButton(text='Добавить задание')
    view = types.KeyboardButton(text='Посмотреть задания')
    startKBoart.add(removal, adding, view)
    bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)


@bot.message_handler(regexp="Удалить задание")
def remove_task(message):
    sent = bot.reply_to(message, 'Введите номер удаляемого задания')
    bot.register_next_step_handler(sent, remove_task_helper)


def remove_task_helper(message):
    number = message.text

    # Валидация введённых данных
    if not number_validation(number):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    cursor.execute(f"DELETE FROM tasks WHERE id = {number}")
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, "Задание успешно удалено!")


@bot.message_handler(regexp="Добавить задание")
def add_task(message):
    sent = bot.reply_to(message, 'Введите задание и его дедлайн.\nЗадание - ДД.ММ.ГГГГ')
    bot.register_next_step_handler(sent, add_task_helper)


def add_task_helper(message):
    message_to_save = message.text
    description, deadline = message_to_save[:-11], message_to_save[-10:]

    # Валидация введённых данных
    if not date_validation(deadline):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    # Соединение с db и создание таблицы tasks
    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            deadline TIMESTAMP,
            userid INTEGER
        )""")
    connect.commit()

    # Добавление задания в db
    task = description, date_to_timestamp(deadline), message.chat.id
    cursor.execute("INSERT INTO tasks VALUES(null, ?, ?, ?);", task)
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, "Задание успешно добавлено!")


@bot.message_handler(regexp="Посмотреть задания")
def view_tasks(message):
    sent = bot.reply_to(message, 'Введите дату, до какого дня вывести задания.\nДД.ММ.ГГГГ')
    bot.register_next_step_handler(sent, view_tasks_helper)


def view_tasks_helper(message):
    message_to_save = message.text
    description, deadline = message_to_save[:-11], message_to_save[-10:]

    # Валидация введённых данных
    if not date_validation(deadline):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    date = date_to_timestamp(deadline)

    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    user_id = message.chat.id
    cursor.execute(f"SELECT * FROM tasks WHERE userid = {user_id};")
    tasks = cursor.fetchall()
    out = ''
    for task in tasks:
        if int(date) >= task[2]:
            out += f'{task[0]}. {task[1]} (до {date_view(task[2])})\n'
    if out == '':
        bot.send_message(message.chat.id, "Нет заданий до указанного дедлайна!")
    else:
        bot.send_message(message.chat.id, out)
    cursor.close()


@bot.message_handler(commands=['delete'])
def delete(message):
    # "Удаление" пользователя: удаление id пользователя из списка
    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    user_id = message.chat.id
    cursor.execute(f"DELETE FROM users WHERE userid = {user_id}")
    cursor.execute(f"DELETE FROM tasks WHERE userid = {user_id}")
    connect.commit()
    bot.send_message(message.chat.id, "Спасибо, что использовали нашего бота!")
    cursor.close()


print('Bot started working...')
bot.polling()
