from os import environ
from datetime import timedelta
import sqlite3
import telebot
from telebot import types
from dotenv import load_dotenv
from services import user_registration, date_to_timestamp, date_view, \
    date_validation, number_validation, get_input_error_text, get_thanks_text, \
    request_enter_deadline_date_for_tasks, get_text_no_tasks_until_deadline, \
    get_text_successfully_adding_task, get_text_successfully_deletion_task, \
    request_enter_task_and_deadline, request_enter_number_task, request_enter_date_to_view_schedule, \
    request_enter_event_and_date_to_add, request_enter_date_to_delete_event, create_counter, \
    get_text_no_tasks, request_enter_type_and_period, event_and_deletion_type_validation, \
    get_text_successfully_adding_event, get_text_no_events_on_this_day, schedule_date_limitation, \
    get_text_limit_exceeded, date_to_datetime, request_enter_number_event, request_enter_deletion_type, \
    get_text_successfully_deletion_event, get_text_successfully_deletion_events, create_tasks_table, \
    create_events_table

load_dotenv()

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    user_registration(message)
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    timetable = types.KeyboardButton(text='Расписание')
    task = types.KeyboardButton(text='Задания')
    startKBoart.add(timetable, task)
    bot.send_message(message.chat.id, 'Что вы хотите сделать?', reply_markup=startKBoart)


@bot.message_handler(func=lambda message: message.text == "Расписание")
def display_schedule_buttons(message):
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    removal = types.KeyboardButton(text='Удалить событие из расписания')
    adding = types.KeyboardButton(text='Добавить событие в расписание')
    view = types.KeyboardButton(text='Посмотреть расписание')
    startKBoart.add(removal, adding, view)
    bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)


@bot.message_handler(regexp="Удалить событие из расписания")
def remove_event(message):
    sent = bot.reply_to(message, request_enter_date_to_delete_event())
    bot.register_next_step_handler(sent, first_remove_event_helper)


def first_remove_event_helper(message):
    date = message.text
    if view_schedule_helper(message) == 0:
        return
    sent = bot.reply_to(message, request_enter_number_event())
    bot.register_next_step_handler(sent, second_remove_event_helper, date)


def second_remove_event_helper(message, date):
    number = message.text

    # Валидация введённых данных
    if not number_validation(number):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    begin_day = date_to_timestamp(date_to_datetime(date))
    day_in_seconds = 86400
    end_day = begin_day + day_in_seconds - 1
    cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND start_date >= {begin_day} "
                   f"AND start_date <= {end_day} ORDER BY start_date;")
    for _ in range(int(number)):
        event = cursor.fetchone()
    if event[4] is None:
        cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
        connect.commit()
        cursor.close()
        bot.send_message(message.chat.id, get_text_successfully_deletion_event())
    else:
        cursor.close()
        sent = bot.reply_to(message, request_enter_deletion_type())
        bot.register_next_step_handler(sent, third_remove_event_helper, event)


def third_remove_event_helper(message, prev_event):
    deletion_type = message.text

    # Валидация введённых данных
    if not (event_and_deletion_type_validation(deletion_type)):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    create_events_table()

    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    if deletion_type == 'е':
        cursor.execute(f"DELETE FROM events WHERE id = {prev_event[0]};")
        connect.commit()
        bot.send_message(message.chat.id, get_text_successfully_deletion_event())
    else:
        difference = 0
        event = prev_event
        while event is not None:
            cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
            difference += event[4]
            cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND description = '{event[1]}' "
                           f"AND start_date = {prev_event[2] + difference} "
                           f"AND end_date = {prev_event[3] + difference} AND period = {event[4]}")
            event = cursor.fetchone()

        event = tuple(list(prev_event)[1:])
        cursor.execute("INSERT INTO events VALUES(null, ?, ?, ?, ?, ?);", event)
        cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND description = '{event[0]}' "
                       f"AND start_date = {event[1]} AND end_date = {event[2]} AND period = {event[3]}")
        event = cursor.fetchone()
        difference = 0
        while event is not None:
            cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
            difference += event[4]
            cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND description = '{event[1]}' "
                           f"AND start_date = {prev_event[2] - difference} "
                           f"AND end_date = {prev_event[3] - difference} AND period = {event[4]}")
            event = cursor.fetchone()
        connect.commit()
        bot.send_message(message.chat.id, get_text_successfully_deletion_events())
    cursor.close()


@bot.message_handler(regexp="Добавить событие в расписание")
def add_event(message):
    sent = bot.reply_to(message, request_enter_event_and_date_to_add())
    bot.register_next_step_handler(sent, first_add_event_helper)


def first_add_event_helper(message):
    message_to_save = message.text
    description, start_date, end_date = message_to_save[:-23], message_to_save[-22:-6], \
                                        message_to_save[-22:-11] + message_to_save[-5:]

    # Валидация введённых данных
    if not date_validation(start_date):
        bot.send_message(message.chat.id, get_input_error_text())
        return
    if not date_validation(end_date):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    sent = bot.reply_to(message, request_enter_type_and_period())
    bot.register_next_step_handler(sent, second_add_event_helper, description, start_date, end_date)


def second_add_event_helper(message, description, start_date, end_date):
    message_to_save = message.text
    event_type = message_to_save[:1]
    if event_type == 'п':
        period = message_to_save[2:]

    # Валидация введённых данных
    if not event_and_deletion_type_validation(event_type):
        bot.send_message(message.chat.id, get_input_error_text())
        return
    if event_type == 'п':
        if not number_validation(period):
            bot.send_message(message.chat.id, get_input_error_text())
            return

    create_events_table()

    start_date = date_to_datetime(start_date)
    end_date = date_to_datetime(end_date)
    period = timedelta(int(period)).total_seconds()

    # Добавление события в db
    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    if event_type == 'п':
        difference = 0
        limit = start_date + timedelta(days=7)
        while start_date + timedelta(seconds=difference) < limit:
            event = description, date_to_timestamp(start_date + timedelta(seconds=difference)), \
                    date_to_timestamp(end_date + timedelta(seconds=difference)), period, message.chat.id
            cursor.execute("INSERT INTO events VALUES(null, ?, ?, ?, ?, ?);", event)
            difference += period
    else:
        event = description, date_to_timestamp(start_date), date_to_timestamp(end_date), message.chat.id
        cursor.execute("INSERT INTO events VALUES(null, ?, ?, ?, null, ?);", event)
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, get_text_successfully_adding_event())


@bot.message_handler(regexp="Посмотреть расписание")
def view_schedule(message):
    sent = bot.reply_to(message, request_enter_date_to_view_schedule())
    bot.register_next_step_handler(sent, view_schedule_helper)


def view_schedule_helper(message):
    date = message.text

    # Валидация введённых данных
    if not date_validation(date):
        bot.send_message(message.chat.id, get_input_error_text())
        return
    if not schedule_date_limitation(date):
        bot.send_message(message.chat.id, get_text_limit_exceeded())
        return 0

    create_events_table()

    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    begin_day = date_to_timestamp(date_to_datetime(date))
    day_in_seconds = 86400
    end_day = begin_day + day_in_seconds - 1
    cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND start_date >= {begin_day} "
                   f"AND start_date <= {end_day} ORDER BY start_date;")
    events = cursor.fetchall()
    counter = create_counter()
    out = ""
    for event in events:
        out += f"{counter()}) {date_view(event[2], 'time')}-{date_view(event[3], 'time')} {event[1]}\n"
    if out == "":
        bot.send_message(message.chat.id, get_text_no_events_on_this_day())
    else:
        bot.send_message(message.chat.id, out)
    cursor.close()


@bot.message_handler(func=lambda message: message.text == "Задания")
def display_tasks_buttons(message):
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    removal = types.KeyboardButton(text="Удалить задание")
    adding = types.KeyboardButton(text="Добавить задание")
    view = types.KeyboardButton(text="Посмотреть задания")
    startKBoart.add(removal, adding, view)
    bot.send_message(message.chat.id, "Каков будет следующий шаг?)", reply_markup=startKBoart)


@bot.message_handler(regexp="Удалить задание")
def remove_task(message):
    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    create_tasks_table()
    cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} ORDER BY deadline;")
    tasks = cursor.fetchall()
    counter = create_counter()
    out = ""
    for task in tasks:
        out += f"{counter()}. {task[1]} (до {date_view(task[2], 'date')})\n"
    if out == "":
        bot.send_message(message.chat.id, get_text_no_tasks())
        return
    else:
        bot.send_message(message.chat.id, out)
    cursor.close()

    sent = bot.reply_to(message, request_enter_number_task())
    bot.register_next_step_handler(sent, remove_task_helper)


def remove_task_helper(message):
    number = message.text

    # Валидация введённых данных
    if not number_validation(number):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} ORDER BY deadline;")
    for _ in range(int(number)):
        task = cursor.fetchone()
    cursor.execute(f"DELETE FROM tasks WHERE id = {task[0]};")
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, get_text_successfully_deletion_task())


@bot.message_handler(regexp="Добавить задание")
def add_task(message):
    sent = bot.reply_to(message, request_enter_task_and_deadline())
    bot.register_next_step_handler(sent, add_task_helper)


def add_task_helper(message):
    message_to_save = message.text
    description, deadline = message_to_save[:-11], message_to_save[-10:]

    # Валидация введённых данных
    if not date_validation(deadline):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    create_tasks_table()

    # Добавление задания в db
    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    task = description, date_to_timestamp(date_to_datetime(deadline)), message.chat.id
    cursor.execute("INSERT INTO tasks VALUES(null, ?, ?, ?);", task)
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, get_text_successfully_adding_task())


@bot.message_handler(regexp="Посмотреть задания")
def view_tasks(message):
    sent = bot.reply_to(message, request_enter_deadline_date_for_tasks())
    bot.register_next_step_handler(sent, view_tasks_helper)


def view_tasks_helper(message):
    deadline = message.text

    # Валидация введённых данных
    if not date_validation(deadline):
        bot.send_message(message.chat.id, get_input_error_text())
        return

    create_tasks_table()

    date = date_to_timestamp(date_to_datetime(deadline))

    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} ORDER BY deadline;")
    tasks = cursor.fetchall()
    counter = create_counter()
    out = ""
    for task in tasks:
        if int(date) >= task[2]:
            out += f"{counter()}. {task[1]} (до {date_view(task[2], 'date')})\n"
    if out == "":
        bot.send_message(message.chat.id, get_text_no_tasks_until_deadline())
    else:
        bot.send_message(message.chat.id, out)
    cursor.close()


@bot.message_handler(commands=["delete"])
def delete(message):
    # "Удаление" пользователя: удаление всех данных, связанных с id пользователя
    connect = sqlite3.connect("project.db")
    cursor = connect.cursor()
    user_id = message.chat.id
    cursor.execute(f"DELETE FROM users WHERE user_id = {user_id}")
    try:
        cursor.execute(f"DELETE FROM tasks WHERE user_id = {user_id}")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute(f"DELETE FROM events WHERE user_id = {user_id}")
    except sqlite3.OperationalError:
        pass
    connect.commit()
    bot.send_message(message.chat.id, get_thanks_text())
    cursor.close()


print("Bot started working...")
bot.polling()
