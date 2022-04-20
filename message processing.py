import telebot
from telebot import types
bot = telebot.TeleBot('5173892002:AAEXXEpJsRRjIUeRdTqLLTwdBLLvpMXo4Mo')


@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.chat.id, 'Привет, я твой ассистент! Расскажи мне свое расписание и задания, а я помогу тебе с правильным распределением времемни')
  startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
  timetable = types.KeyboardButton(text='Расписание')
  task = types.KeyboardButton(text='Задания')
  startKBoart.add(timetable, task)
  bot.send_message(message.chat.id, 'Что вы хотите сделать', reply_markup=startKBoart)

'''Timetable'''

@bot.message_handler(regexp = "Расписание")
def plan(message):
  startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
  removal = types.KeyboardButton(text='Удалить событие из расписания')
  adding = types.KeyboardButton(text='Добавить событие из расписания')
  view = types.KeyboardButton(text='Посмотреть расписание')
  startKBoart.add(removal, adding, view)
  bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)

@bot.message_handler(regexp ="Удалить событие из расписания")
def remove_event(message):
  sent = bot.reply_to(message.chat.id, 'Введите дату, в какой день хотите удалить событие. \n ДД.ММ.ГГ')
  bot.register_next_step_handler(sent, remove_timetable)

def remove_timetable(message):
  message_to_save = message.text

@bot.message_handler(regexp ="Добавить событие из расписания")
def add_event(message):
  sent = bot.reply_to(message.chat.id, 'Введите дату, в какой день хотите добавить событие. \n ДД.ММ.ГГ')
  bot.register_next_step_handler(sent, add_timetable)

def add_timetable(message):
  message_to_save = message.text

@bot.message_handler(regexp="Посмотреть расписание")
def view_plan(message):
    sent = bot.reply_to(message.chat.id, 'Введите дату, в какой день хотите посмотреть расписание. \n ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, view_timetable)

def view_timetable(message):
  message_to_save = message.text

'''Tssks'''

@bot.message_handler(regexp = "Задания")
def plan(message):
  startKBoart = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
  removal = types.KeyboardButton(text='Удалить задание')
  adding = types.KeyboardButton(text='Добавить задание')
  view = types.KeyboardButton(text='Посмотреть задания')
  startKBoart.add(removal, adding, view)
  bot.send_message(message.chat.id, 'Каков будет следующий шаг?)', reply_markup=startKBoart)

@bot.message_handler(regexp ="Удалить задани")
def remove_task(message):
  sent = bot.reply_to(message.chat.id, 'Введите номер удаляемого задания')
  bot.register_next_step_handler(sent, remove)

def remove(message):
  message_to_save = message.text

@bot.message_handler(regexp ="Добавить задание")
def add_task(message):
  sent = bot.reply_to(message.chat.id, 'Введите название события и его дедлайн. \n Название задание - ДД.ММ.ГГ')
  bot.register_next_step_handler(sent, add)

def add(message):
  message_to_save = message.text

@bot.message_handler(regexp="Посмотреть задания")
def view_plan(message):
    sent = bot.reply_to(message.chat.id, 'Введите дату, до какого дня вывести задания. \n ДД.ММ.ГГ')
    bot.register_next_step_handler(sent, view)

def view(message):
  message_to_save = message.text

bot.polling()
