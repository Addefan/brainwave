from os import environ
import sqlite3
import datetime
import telebot
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = environ.get("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)


def get_greeting_text():
    """
    Получение приветственного текста
    :return: str
    """
    return 'Привет, я  - твой ассистент! Расскажи мне свое расписание и задания, ' \
           'а я помогу тебе с правильным распределением времени'


def get_input_error_text():
    """
    Получение текста о неправильно введённых данных
    :return: str
    """
    return "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз"


def user_registation(message):
    """
    Регистрация пользователя: создание таблицы с пользователями (если не существовала),
    добавление в неё пользователя (если не был добавлен ранее), приветственное сообщение
    :param message: Message - вся информация о полученном сообщении
    :return: None
    """
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
        bot.send_message(message.chat.id, get_greeting_text())
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрированы!")
    cursor.close()


def date_to_datetime(date):
    """
    Функция, преобразовывающая дату, введённую пользователем в объект datetime.datetime
    :param date: str - дата, введённая пользователем
    :return: datetime.datetime - дата в виде экземпляра класса
    """
    return datetime.datetime.strptime(date, '%d.%m.%Y')


def date_to_timestamp(date):
    """
    Функция, преобразовывающая дату, введённую пользователем в секунды от 01.01.1970
    :param date: str - дата, введённая пользователем
    :return: float - время в секундах
    """
    date = date_to_datetime(date)
    return date.timestamp()


def date_view(date_timestamp):
    """
    Функция, возвращающая дату, конвертированную в формат ДД.ММ.ГГГГ
    :param date_timestamp: float - дата в виде количества секунд от 01.01.1970
    :return: str - дата в формате ДД.ММ.ГГГГ
    """
    return datetime.datetime.fromtimestamp(date_timestamp).strftime("%d.%m.%Y")


def date_validation(date):
    """
    Валидация даты, введённой пользователем
    :param date: str - дата, введённая пользователем
    :return: bool - валидна дата или нет
    """
    try:
        date_to_datetime(date)
    except ValueError:
        return False
    return True


def number_validation(number):
    """
    Валидация номера, введёного пользователем
    :param number: str - номер, введённый пользователем
    :return: bool - валиден номер или нет
    """
    try:
        number = int(number)
    except ValueError:
        return False
    if number < 1:
        return False
    return True
