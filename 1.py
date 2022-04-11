import telebot

bot = telebot.TeleBot('5173892002:AAEXXEpJsRRjIUeRdTqLLTwdBLLvpMXo4Mo')


@bot.message_handler(commands=['start'])
def start(message):
  bot.send_message(message.chat.id, 'Привет, я твой ассистент! Расскажи мне свое расписание и задания, а я помогу тебе с правильным распределением времемни')
  bot.send_message(message.chat.id,f'Имя : {message.from_user.first_name}\nФамилия: {message.from_user.last_name}\nПсевдоним: {message.from_user.username}')

bot.polling()
