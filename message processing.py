import telebot
import sqlite3
from telebot import types

bot = telebot.TeleBot('5173892002:AAEXXEpJsRRjIUeRdTqLLTwdBLLvpMXo4Mo')


@bot.message_handler(commands=['start'])
def start(message):
    # Подключение (создание) к db и создание таблицы users
    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS users(
        userid INTEGER PRIMARY KEY 
    )""")
    connect.commit()

    # "Регистрация" пользователя: добавление id в db, если он не был добавлен ранее,
    # приветственное сообщение
    user_id = message.chat.id
    cursor.execute(f"SELECT userid FROM users WHERE userid = {user_id}")
    data = cursor.fetchone()
    if data is None:
        user_id = (user_id,)
        cursor.execute("INSERT INTO users VALUES(?);", user_id)
        connect.commit()
        bot.send_message(message.chat.id,
                         'Привет, я твой ассистент! Расскажи мне свое расписание и задания, а я помогу тебе с правильным распределением времемни')
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы!")
    cursor.close()

    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    timetable = types.KeyboardButton(text='Расписание')
    task = types.KeyboardButton(text='Задания')
    startKBoart.add(timetable, task)
    bot.send_message(message.chat.id, 'Что вы хотите сделать?', reply_markup=startKBoart)


'''Timetable'''


@bot.message_handler(regexp="Расписание")
def plan(message):
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    removal = types.KeyboardButton(text='Удалить событие из расписания')
    adding = types.KeyboardButton(text='Добавить событие в расписание')
    view = types.KeyboardButton(text='Посмотреть расписание')
    startKBoart.add(removal, adding, view)
    bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)


@bot.message_handler(regexp="Удалить событие из расписания")
def remove_event(message):
    sent = bot.reply_to(message, 'Введите дату, в какой день хотите удалить событие. \n ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, remove_timetable)


def remove_timetable(message):
    message_to_save = message.text


@bot.message_handler(regexp="Добавить событие в расписание")
def add_event(message):
    sent = bot.reply_to(message, 'Введите дату, в какой день хотите добавить событие. \n ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, add_timetable)


def add_timetable(message):
    message_to_save = message.text


@bot.message_handler(regexp="Посмотреть расписание")
def view_plan(message):
    sent = bot.reply_to(message, 'Введите дату, на какой день хотите посмотреть расписание. \n ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, view_timetable)


def view_timetable(message):
    message_to_save = message.text


'''Tssks'''


@bot.message_handler(regexp="Задания")
def plan(message):
    startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    removal = types.KeyboardButton(text='Удалить задание')
    adding = types.KeyboardButton(text='Добавить задание')
    view = types.KeyboardButton(text='Посмотреть задания')
    startKBoart.add(removal, adding, view)
    bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)


@bot.message_handler(regexp="Удалить задание")
def remove_task(message):
    sent = bot.reply_to(message, 'Введите номер удаляемого задания')
    bot.register_next_step_handler(sent, remove)


def remove(message):
    message_to_save = message.text

    # Валидация введённых данных
    try:
        message_to_save = int(message_to_save)
    except ValueError:
        bot.send_message(message.chat.id,
                         "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз")

    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    cursor.execute(f"DELETE FROM tasks WHERE counter = {message_to_save}")
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, "Задание успешно удалено!")


@bot.message_handler(regexp="Добавить задание")
def add_task(message):
    sent = bot.reply_to(message, 'Введите задание и его дедлайн. \n Задание - ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, add)


def add(message):
    message_to_save = message.text
    description, deadline = message_to_save[:-9], message_to_save[-8:]
    day_month_year = deadline.split('.')

    # Валидация введёных данных
    if not (isinstance(description, str) and all(len(x) == 2 for x in day_month_year) and len(day_month_year) == 3):
        bot.send_message(message.chat.id,
                         "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз")
        return
    try:
        day_month_year = map(int, day_month_year)
    except ValueError:
        bot.send_message(message.chat.id,
                         "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз")
        return

    # Соединение с db и создание таблицы tasks
    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS tasks(
            counter INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            deadline TEXT,
            userid INTEGER
        )""")
    connect.commit()

    # Добавление задания в db
    task = (description, deadline, message.chat.id)
    cursor.execute("INSERT INTO tasks VALUES(null, ?, ?, ?);", task)
    connect.commit()
    connect.close()

    bot.send_message(message.chat.id, "Задание успешно добавлено!")


@bot.message_handler(regexp="Посмотреть задания")
def view_plan(message):
    sent = bot.reply_to(message, 'Введите дату, до какого дня вывести задания. \n ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, view)


def date_to_days(date):
    if isinstance(date, str):
        date = list(map(int, date.split('.')))
    return 365 * date[2] + 30 * date[1] + date[0]


def view(message):
    message_to_save = message.text
    date = message_to_save.split('.')

    # Валидация введённых данных
    if not (all(len(x) == 2 for x in date) and len(date) == 3):
        bot.send_message(message.chat.id,
                         "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз")
    try:
        date = list(map(int, date))
    except ValueError:
        bot.send_message(message.chat.id,
                         "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз")

    date = date_to_days(date)

    connect = sqlite3.connect('project.db')
    cursor = connect.cursor()
    user_id = message.chat.id
    cursor.execute(f"SELECT * FROM tasks WHERE userid = {user_id};")
    tasks = cursor.fetchall()
    out = ''
    for task in tasks:
        if date >= date_to_days(task[2]):
            out += f'{task[0]}. {task[1]} (до {task[2]})\n'
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
    connect.commit()
    bot.send_message(message.chat.id, "Спасибо, что использовали нашего бота!")
    cursor.close()


bot.polling()
