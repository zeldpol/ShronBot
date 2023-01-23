import os
import telebot as tb

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = tb.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start', 'hello'])
def send_welcome(message):
    bot.reply_to(message, "Howdy, how are you doing?")


@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, message.text)

@bot.message_handler(content_types=["sticker"])
def echo_sticker(message):
    bot.send_sticker(message.chat.id, message.sticker.file_id)

#message.from_user.id
bot.infinity_polling()

