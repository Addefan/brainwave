from os import environ
from datetime import timedelta
import sqlite3
import telebot
from dotenv import load_dotenv
import services

load_dotenv()

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


@bot.message_handler(commands=['start'])
def start(message):
    services.user_registration(message)
    bot.send_message(message.chat.id, 'Что вы хотите сделать?',
                     reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(func=lambda message: message.text == "Расписание")
def display_schedule_buttons(message):
    bot.send_message(message.chat.id, 'Каков будет следующий шаг?)',
                     reply_markup=services.display_del_add_view_event())


@bot.message_handler(regexp="Удалить событие из расписания")
def remove_event(message):
    sent = bot.reply_to(message, services.request_enter_date_to_delete_event())
    bot.register_next_step_handler(sent, first_remove_event_helper)


def first_remove_event_helper(message):
    date = message.text
    if view_schedule_helper(message) == 0:
        return
    sent = bot.reply_to(message, services.request_enter_number_event())
    bot.register_next_step_handler(sent, second_remove_event_helper, date)


def second_remove_event_helper(message, date):
    number = message.text
    user_id = message.chat.id

    # Валидация введённых данных
    if not services.number_validation(number):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return

    with services.working_with_db("project.db") as cursor:
        begin_day = services.date_to_timestamp(services.date_to_datetime(date))
        day_in_seconds = 86400
        end_day = begin_day + day_in_seconds - 1
        cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND "
                       f"start_date BETWEEN {begin_day} AND {end_day} ORDER BY start_date;")
        for _ in range(int(number)):
            event = cursor.fetchone()
        if event[4] is None:
            cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
            bot.send_message(user_id, services.get_text_successfully_deletion_event(),
                             reply_markup=services.display_schedule_tasks_buttons())
        else:
            sent = bot.reply_to(message, services.request_enter_deletion_type())
            bot.register_next_step_handler(sent, third_remove_event_helper, event)


def third_remove_event_helper(message, prev_event):
    deletion_type = message.text
    user_id = message.chat.id

    # Валидация введённых данных
    if not services.event_and_deletion_type_validation(deletion_type):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return

    services.create_events_table("project.db")

    with services.working_with_db("project.db") as cursor:
        if deletion_type == 'е':
            cursor.execute(f"DELETE FROM events WHERE id = {prev_event[0]};")
            bot.send_message(user_id, services.get_text_successfully_deletion_event(),
                             reply_markup=services.display_schedule_tasks_buttons())
        else:
            diff = 0
            event = prev_event
            while event is not None:
                cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
                diff += event[4]
                cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND "
                               f"description = '{event[1]}' AND start_date = {prev_event[2] + diff} "
                               f"AND end_date = {prev_event[3] + diff} AND period = {event[4]}")
                event = cursor.fetchone()

            event = tuple(list(prev_event)[1:])
            cursor.execute("INSERT INTO events VALUES(null, ?, ?, ?, ?, ?);", event)
            cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND "
                           f"description = '{event[0]}'  AND start_date = {event[1]} "
                           f"AND end_date = {event[2]} AND period = {event[3]}")
            event = cursor.fetchone()
            diff = 0
            while event is not None:
                cursor.execute(f"DELETE FROM events WHERE id = {event[0]};")
                diff += event[4]
                cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND "
                               f"description = '{event[1]}' AND start_date = {prev_event[2] - diff} "
                               f"AND end_date = {prev_event[3] - diff} AND period = {event[4]}")
                event = cursor.fetchone()
            bot.send_message(user_id, services.get_text_successfully_deletion_events(),
                             reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(regexp="Добавить событие в расписание")
def add_event(message):
    sent = bot.reply_to(message, services.request_enter_event_and_date_to_add())
    bot.register_next_step_handler(sent, first_add_event_helper)


def first_add_event_helper(message):
    message_to_save = message.text
    user_id = message.chat.id
    description, start_date, end_date = message_to_save[:-23], message_to_save[-22:-6], \
                                        message_to_save[-22:-11] + message_to_save[-5:]

    # Валидация введённых данных
    if not services.date_validation(start_date):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return
    if not services.date_validation(end_date):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return

    sent = bot.reply_to(message, services.request_enter_type_and_period())
    bot.register_next_step_handler(sent, second_add_event_helper, description, start_date, end_date)


def second_add_event_helper(message, description, start_date, end_date):
    message_to_save = message.text
    user_id = message.chat.id
    event_type = message_to_save[:1]
    if event_type == 'п':
        period = message_to_save[2:]

    # Валидация введённых данных
    if not services.event_and_deletion_type_validation(event_type):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return
    if event_type == 'п':
        if not services.number_validation(period):
            bot.send_message(user_id, services.get_input_error_text(),
                             reply_markup=services.display_schedule_tasks_buttons())
            return

    services.create_events_table("project.db")

    start_date = services.date_to_datetime(start_date)
    end_date = services.date_to_datetime(end_date)
    if event_type == "п":
        period = timedelta(int(period)).total_seconds()

    # Добавление события в db
    with services.working_with_db("project.db") as cursor:
        if event_type == 'п':
            diff = 0
            limit = start_date + timedelta(days=7)
            while start_date + timedelta(seconds=diff) < limit:
                event = description, services.date_to_timestamp(start_date + timedelta(seconds=diff)), \
                        services.date_to_timestamp(end_date + timedelta(seconds=diff)), \
                        period, user_id
                cursor.execute("INSERT INTO events VALUES(null, ?, ?, ?, ?, ?);", event)
                diff += period
        else:
            event = description, services.date_to_timestamp(start_date), \
                    services.date_to_timestamp(end_date), user_id
            cursor.execute("INSERT INTO events VALUES(null, ?, ?, ?, null, ?);", event)

    bot.send_message(user_id, services.get_text_successfully_adding_event(),
                     reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(regexp="Посмотреть расписание")
def view_schedule(message):
    sent = bot.reply_to(message, services.request_enter_date_to_view_schedule())
    bot.register_next_step_handler(sent, view_schedule_helper)


def view_schedule_helper(message):
    date = message.text
    user_id = message.chat.id

    # Валидация введённых данных
    if not services.date_validation(date):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return
    if not services.schedule_date_limitation(date):
        bot.send_message(user_id, services.get_text_limit_exceeded(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return 0

    services.create_events_table("project.db")

    with services.working_with_db("project.db") as cursor:
        begin_day = services.date_to_timestamp(services.date_to_datetime(date))
        day_in_seconds = 86400
        end_day = begin_day + day_in_seconds - 1
        cursor.execute(f"SELECT * FROM events WHERE user_id = {user_id} AND start_date >= {begin_day} "
                       f"AND start_date <= {end_day} ORDER BY start_date;")
        events = cursor.fetchall()
        counter = services.create_counter()
        out = ""
        for event in events:
            out += f"{counter()}) {services.date_view(event[2], 'time')}-" \
                   f"{services.date_view(event[3], 'time')} {event[1]}\n"
        if out == "":
            bot.send_message(user_id, services.get_text_no_events_on_this_day(),
                             reply_markup=services.display_schedule_tasks_buttons())
            return 0
        out = f"📜 *Расписание на {services.date_view(events[0][2], 'date')}:*\n" + out
        bot.send_message(user_id, out, parse_mode="Markdown",
                         reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(func=lambda message: message.text == "Задания")
def display_tasks_buttons(message):
    bot.send_message(message.chat.id, "Каков будет следующий шаг?)",
                     reply_markup=services.display_del_add_view_task())


@bot.message_handler(regexp="Удалить задание")
def remove_task(message):
    user_id = message.chat.id

    services.create_tasks_table("project.db")

    with services.working_with_db("project.db") as cursor:
        cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} ORDER BY deadline;")
        tasks = cursor.fetchall()
        counter = services.create_counter()
        out = ""
        for task in tasks:
            out += f"{counter()}. {task[1]} (до {services.date_view(task[2], 'date')})\n"
        if out == "":
            bot.send_message(user_id, services.get_text_no_tasks(),
                             reply_markup=services.display_schedule_tasks_buttons())
            return
        else:
            bot.send_message(user_id, out)

    sent = bot.reply_to(message, services.request_enter_number_task())
    bot.register_next_step_handler(sent, remove_task_helper)


def remove_task_helper(message):
    number = message.text
    user_id = message.chat.id

    # Валидация введённых данных
    if not services.number_validation(number):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return

    with services.working_with_db("project.db") as cursor:
        cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} ORDER BY deadline;")
        for _ in range(int(number)):
            task = cursor.fetchone()
        cursor.execute(f"DELETE FROM tasks WHERE id = {task[0]};")

    bot.send_message(user_id, services.get_text_successfully_deletion_task(),
                     reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(regexp="Добавить задание")
def add_task(message):
    sent = bot.reply_to(message, services.request_enter_task_and_deadline())
    bot.register_next_step_handler(sent, add_task_helper)


def add_task_helper(message):
    message_to_save = message.text
    user_id = message.chat.id
    description, deadline = message_to_save[:-11], message_to_save[-10:]

    # Валидация введённых данных
    if not services.date_validation(deadline):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return

    services.create_tasks_table("project.db")

    # Добавление задания в db
    with services.working_with_db("project.db") as cursor:
        task = description, services.date_to_timestamp(services.date_to_datetime(deadline)), user_id
        cursor.execute("INSERT INTO tasks VALUES(null, ?, ?, ?);", task)

    bot.send_message(user_id, services.get_text_successfully_adding_task(),
                     reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(regexp="Посмотреть задания")
def view_tasks(message):
    sent = bot.reply_to(message, services.request_enter_deadline_date_for_tasks())
    bot.register_next_step_handler(sent, view_tasks_helper)


def view_tasks_helper(message):
    deadline = message.text
    user_id = message.chat.id

    # Валидация введённых данных
    if not services.date_validation(deadline):
        bot.send_message(user_id, services.get_input_error_text(),
                         reply_markup=services.display_schedule_tasks_buttons())
        return

    services.create_tasks_table("project.db")

    date = services.date_to_timestamp(services.date_to_datetime(deadline))

    with services.working_with_db("project.db") as cursor:
        cursor.execute(f"SELECT * FROM tasks WHERE user_id = {user_id} ORDER BY deadline;")
        tasks = cursor.fetchall()
        counter = services.create_counter()
        out = ""
        for task in tasks:
            if int(date) >= task[2]:
                out += f"{counter()}. {task[1]} (до {services.date_view(task[2], 'date')})\n"
        if out == "":
            bot.send_message(user_id, services.get_text_no_tasks_until_deadline(),
                             reply_markup=services.display_schedule_tasks_buttons())
        else:
            bot.send_message(user_id, out, reply_markup=services.display_schedule_tasks_buttons())


@bot.message_handler(commands=["delete"])
def delete(message):
    # "Удаление" пользователя: удаление всех данных, связанных с id пользователя
    user_id = message.chat.id

    with services.working_with_db("project.db") as cursor:
        cursor.execute(f"DELETE FROM users WHERE user_id = {user_id}")
        try:
            cursor.execute(f"DELETE FROM tasks WHERE user_id = {user_id}")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute(f"DELETE FROM events WHERE user_id = {user_id}")
        except sqlite3.OperationalError:
            pass

    bot.send_message(user_id, services.get_thanks_text())


if __name__ == "__main__":
    print("Bot started working...")
    bot.infinity_polling()
