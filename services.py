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
    return "Привет, я  - твой ассистент! Расскажи мне свое расписание и задания, " \
           "а я помогу тебе с правильным распределением времени"


def get_input_error_text():
    """
    Получение текста о неправильно введённых данных
    :return: str
    """
    return "Извините, вы ввели данные в неправильном формате. Пожалуйста, попробуйте ещё раз"


def get_thanks_text():
    """
    Получение благодарственного текста
    :return: str
    """
    return "Спасибо, что использовали нашего бота!"


def get_text_no_tasks_until_deadline():
    """
    Получение текста о том, что нет заданий до дедлайна
    :return: str
    """
    return "Нет заданий до указанного дедлайна!"


def get_text_successfully_adding_task():
    """
    Получение текста о том, что задание добавлено
    :return: str
    """
    return "Задание успешно добавлено!"


def get_text_successfully_deletion_task():
    """
    Получение текста о том, что задание удалено
    :return: str
    """
    return "Задание успешно удалено!"


def get_test_no_tasks():
    """
    Получение текста о том, что у пользователя нет заданий
    :return: str
    """
    return "У вас нет заданий!"


def request_enter_deadline_date_for_tasks():
    """
    Получение текста с просьбой ввести дату, до которой нужно вывести задания
    :return: str
    """
    return "Введите дату, до какого дня вывести задания.\nДД.ММ.ГГГГ"


def request_enter_task_and_deadline():
    """
    Получение текста с просьбой ввести задание и его дедлайн
    :return: str
    """
    return "Введите задание и его дедлайн.\nЗадание - ДД.ММ.ГГГГ"


def request_enter_number_task():
    """
    Получение текста с просьбой ввести номер удаляемого задания
    :return: str
    """
    return "Введите номер удаляемого задания"


def request_enter_date_to_view_schedule():
    """
    Получения текста с просьбой ввести дату, на которую нужно вывести расписание
    :return: str
    """
    return "Введите дату, на какой день хотите посмотреть расписание.\nДД.ММ.ГГГГ"


def request_enter_date_to_add_event():
    """
    Получение текста с просьбой ввести дату, на которую нужно добавить событие
    :return: str
    """
    return "Введите дату, на какой день хотите добавить событие.\nДД.ММ.ГГГГ"


def request_enter_date_to_delete_event():
    """
    Получение текста с просьбой ввести дату, с которой нужно удалить событие
    :return: str
    """
    return "Введите дату, на какой день хотите удалить событие.\nДД.ММ.ГГГГ"


def user_registration(message):
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


def create_counter():
    """
    Функция, при вызове которой создаётся независимый счётчик
    :return: function
    """
    i = 0

    def foo():
        """
        Функция, которая увеличивает значение i на единицу
        :return: int
        """
        nonlocal i
        i += 1
        return i

    return foo
