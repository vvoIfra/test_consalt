import telebot

#Константы
token='5312367779:AAGIaVZ12JwDu36FGtrXInYSrfeTkIv7NoI'
bot=telebot.TeleBot(token)

#Приветсвенное сообщение
@bot.message_handler(commands=['start'])
def start_message(message):
  bot.send_message(message.chat.id,"""Вас приветсвует бот для оповещения о сроках поставок Для начала работы наберите /start_test""")

#Запуск системы информирования
@bot.message_handler(commands=['start_test'])
def start_test(message):
  with open("test_chat.txt",'a') as file:
    file.write(str(message.chat.id))
  bot.send_message(message.chat.id,"Система информирования запущена")

#Ожидание сообщения
bot.infinity_polling()
